"""
Rule-based extraction of explicit section/clause references from clause text.
No LLM; pure regex over clause snippets. Used as a post-step after structure extraction.
"""
import re
from typing import List, Optional

from app.schemas.contract import Clause, CrossReference


def _section_number_to_clause_id(clause: Clause) -> Optional[str]:
    """Get normalized section number (e.g. '1.1', '4.2') for mapping. Returns None if not derivable."""
    # Prefer section_id: "Section 1.1" -> "1.1"
    if clause.section_id:
        m = re.match(r"(?i)^Section\s+(.+)$", clause.section_id.strip())
        if m:
            return m.group(1).strip()
        if re.match(r"^\d+(?:\.\d+)*$", clause.section_id.strip()):
            return clause.section_id.strip()
    # Fallback: id "section_1_1" -> "1.1"
    if clause.id and clause.id.startswith("section_"):
        num = clause.id.replace("section_", "", 1).replace("_", ".")
        if re.match(r"^\d+(?:\.\d+)*$", num):
            return num
    return None


def _build_section_map(clauses: List[Clause]) -> dict[str, str]:
    """Map section number (e.g. '1.1') -> clause id (e.g. 'section_1_1')."""
    m: dict[str, str] = {}
    for c in clauses:
        num = _section_number_to_clause_id(c)
        if num:
            m[num] = c.id
    return m


# Single reference: "Section 4.2", "Clause 7.3", "Section 10.1"
_SINGLE = re.compile(
    r"\b(?:Section|Clause)\s+(\d+(?:\.\d+)*)\b",
    re.IGNORECASE,
)

# Plural: "Sections 5.1 and 5.2", "Sections 3.1, 3.2 and 3.3"
_PLURAL = re.compile(
    r"\bSections?\s+([\d.]+(?:\s*,\s*[\d.]+)*(?:\s+and\s+[\d.]+)?)\b",
    re.IGNORECASE,
)


def _parse_plural_refs(s: str) -> List[str]:
    """Parse '5.1, 5.2 and 5.3' or '3.1, 3.2 and 3.3' into ['5.1','5.2','5.3']."""
    s = s.strip()
    parts = re.split(r"\s+and\s+|\s*,\s*", s, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip() and re.match(r"^\d+(?:\.\d+)*$", p.strip())]


def extract_cross_references(clauses: List[Clause]) -> List[CrossReference]:
    """
    Extract explicit section/clause references from clause text. Rule-based only.
    Returns deduplicated list of CrossReference; unknown section numbers are skipped.
    """
    if not clauses:
        return []

    section_map = _build_section_map(clauses)
    seen: set[tuple[str, str, str]] = set()
    out: List[CrossReference] = []

    for clause in clauses:
        if not (clause.text or "").strip():
            continue
        from_id = clause.id
        text = clause.text

        # Single refs
        for m in _SINGLE.finditer(text):
            num = m.group(1)
            to_id = section_map.get(num)
            if not to_id or to_id == from_id:
                continue
            ref_text = m.group(0)
            key = (from_id, to_id, ref_text)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                CrossReference(
                    from_clause_id=from_id,
                    to_clause_id=to_id,
                    ref_text=ref_text,
                )
            )

        # Plural refs: "Sections 5.1 and 5.2" etc.
        for m in _PLURAL.finditer(text):
            ref_text = m.group(0)
            nums_str = m.group(1)
            for num in _parse_plural_refs(nums_str):
                to_id = section_map.get(num)
                if not to_id or to_id == from_id:
                    continue
                key = (from_id, to_id, ref_text)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    CrossReference(
                        from_clause_id=from_id,
                        to_clause_id=to_id,
                        ref_text=ref_text,
                    )
                )

    return out
