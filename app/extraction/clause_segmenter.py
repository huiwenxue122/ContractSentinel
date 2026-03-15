"""
Rule-based clause segmenter: split contract full text into subsection-level Clause list.
No LLM; stable numbering (e.g. 1.1, 1.2, 2.1). Dedup by subsection number; filter TOC/weak hits.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.contract import Clause


# Match subsection header at line start: optional "Section ", then digits.digits, then whitespace.
_SUBSECTION_HEADER = re.compile(
    r"(?m)^\s*(?:Section\s+)?(\d+\.\d+)\s+",
)

# Minimum clause body length (chars) to count as real subsection, not TOC or ref line
MIN_CLAUSE_CHARS = 100
# First line (to newline) longer than this suggests real body; shorter may be TOC line
MIN_FIRST_LINE_CHARS = 40
# Only consider subsection starts in the first fraction of doc (main body; exhibits often reuse 1.1, 2.1 later)
MAIN_BODY_FRACTION = 0.55


def _first_line(s: str) -> str:
    """First line of text, stripped."""
    idx = s.find("\n")
    return (s[:idx] if idx >= 0 else s).strip()


def is_plausible_subsection_start(
    text: str,
    start: int,
    end: int,
    prev_start: Optional[int],
) -> bool:
    """
    Heuristic: reject TOC lines, ref-only lines, and too-short fragments.
    - Clause text must be at least MIN_CLAUSE_CHARS.
    - First line not too short (avoids "1.1  Title" / "1.1 ........ 5" TOC lines).
    - Optional: if distance from prev match is tiny and text short, skip (dense TOC block).
    """
    if not text or len(text) < MIN_CLAUSE_CHARS:
        return False
    first = _first_line(text)
    if len(first) < MIN_FIRST_LINE_CHARS:
        return False
    # Dense TOC: very close to previous match and still short
    if prev_start is not None and (start - prev_start) < 100 and len(text) < 200:
        return False
    return True


def segment_clauses(full_text: str) -> Tuple[List[Clause], Dict[str, Any]]:
    """
    Split full contract text into subsection-level clauses. Dedup by subsection number
    (keep one candidate per number, preferring longer text). Filter implausible/TOC hits.
    Returns (clauses, stats) with stats["raw_matches"] and stats["after_dedup_filter"].
    """
    stats: Dict[str, Any] = {"raw_matches": 0, "after_dedup_filter": 0}

    if not (full_text or "").strip():
        return [], stats

    matches = list(_SUBSECTION_HEADER.finditer(full_text))
    stats["raw_matches"] = len(matches)
    if not matches:
        return [], stats

    positions = [m.start() for m in matches]
    numbers = [m.group(1) for m in matches]

    # Build candidates: (num, start, end, text); skip starts beyond main body (exhibits reuse numbers)
    main_body_end = int(len(full_text) * MAIN_BODY_FRACTION)
    candidates: List[Tuple[str, int, int, str]] = []
    prev_start: Optional[int] = None
    for i in range(len(positions)):
        start = positions[i]
        if start > main_body_end:
            continue
        end = positions[i + 1] if i + 1 < len(positions) else len(full_text)
        text = full_text[start:end].strip()
        num = numbers[i]
        if not is_plausible_subsection_start(text, start, end, prev_start):
            continue
        candidates.append((num, start, end, text))
        prev_start = start

    # One clause per subsection number: keep candidate with longest text
    by_num: Dict[str, Tuple[int, int, int, str]] = {}
    for (num, start, end, text) in candidates:
        if num not in by_num or len(text) > len(by_num[num][3]):
            by_num[num] = (start, end, end - start, text)

    # Sort by start to preserve document order; build Clause list
    chosen = sorted(by_num.items(), key=lambda x: x[1][0])
    clauses: List[Clause] = []
    for num, (start, _end, _len, text) in chosen:
        clause_id = "section_" + num.replace(".", "_")
        section_id = "Section " + num
        clauses.append(
            Clause(
                id=clause_id,
                section_id=section_id,
                text=text,
                page=None,
            )
        )

    stats["after_dedup_filter"] = len(clauses)
    return clauses, stats
