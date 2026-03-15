"""
PDF parsing with PyMuPDF (fitz).
Output: full text or list of page-wise text blocks for extraction.
"""
from pathlib import Path
from typing import Union

import fitz  # PyMuPDF

from app.parsing.blocks import TextBlock


def parse_pdf(path_or_bytes: Union[str, Path, bytes]) -> tuple[str, list[TextBlock]]:
    """
    Parse a contract PDF into full text and optional page-wise blocks.

    Args:
        path_or_bytes: File path (str or Path) or raw PDF bytes.

    Returns:
        (full_text, blocks) where full_text is the entire document text
        and blocks is a list of TextBlock with optional page numbers.
    """
    if isinstance(path_or_bytes, (str, Path)):
        doc = fitz.open(path_or_bytes)
    else:
        doc = fitz.open(stream=path_or_bytes, filetype="pdf")

    blocks: list[TextBlock] = []
    full_parts: list[str] = []

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            full_parts.append(page_text)
            if page_text.strip():
                blocks.append(TextBlock(text=page_text.strip(), page=page_num + 1))
    finally:
        doc.close()

    full_text = "\n\n".join(full_parts)
    return full_text, blocks


def strip_repeated_headers_footers(
    full_text: str, blocks: list[TextBlock], page_threshold_ratio: float = 0.35
) -> str:
    """
    Remove short lines that appear on many pages (likely headers/footers) to reduce noise.
    Only strips lines with length <= 100 that appear on more than page_threshold_ratio of pages.
    """
    if not blocks:
        return full_text
    from collections import Counter
    short_lines_per_page: list[set[str]] = []
    seen_pages: set[int] = set()
    for b in blocks:
        if b.page is None:
            continue
        if b.page not in seen_pages:
            seen_pages.add(b.page)
            lines = [ln.strip() for ln in b.text.splitlines() if ln.strip() and len(ln.strip()) <= 100]
            short_lines_per_page.append(set(lines))
    if len(short_lines_per_page) < 2:
        return full_text
    threshold = max(2, int(len(short_lines_per_page) * page_threshold_ratio))
    line_counts: Counter[str] = Counter()
    for s in short_lines_per_page:
        for ln in s:
            line_counts[ln] += 1
    repeated = {ln for ln, c in line_counts.items() if c >= threshold}
    if not repeated:
        return full_text
    out_lines = [
        ln for ln in full_text.splitlines()
        if ln.strip() not in repeated or len(ln.strip()) > 100
    ]
    return "\n".join(out_lines)
