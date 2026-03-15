"""
Shared structural pipeline: parse PDF (path or bytes) -> segment clauses -> extract contract
-> overwrite clauses/cross-refs when rule-based segmenter found clauses -> ingest to Neo4j.

Used by scripts/run_structural_pipeline.py and the contracts API (upload + demo).
The rule-based segmenter is tuned for "Section X.Y" numbering; other PDFs still run
but may get fewer clauses (LLM-only clauses when segmenter finds no matches).
"""
from pathlib import Path
from typing import Any, Dict, Optional, Union

from app.parsing import parse_pdf
from app.extraction import extract_contract, extract_cross_references, segment_clauses
from app.graph import ingest_contract
from app.schemas.contract import Contract


def run_structural_pipeline(
    path_or_bytes: Union[str, Path, bytes],
    contract_id: str,
) -> tuple[Contract, Optional[Dict[str, Any]]]:
    """
    Run full pipeline: parse -> segment -> extract -> (overwrite clauses if any) -> ingest.

    Args:
        path_or_bytes: PDF file path or raw bytes.
        contract_id: Id for the contract (e.g. filename stem or "EX-10.4(a)").

    Returns:
        (contract, ingest_stats). ingest_stats is None if ingest was skipped (e.g. Neo4j not configured).
    """
    full_text, _blocks = parse_pdf(path_or_bytes)
    clauses, _seg_stats = segment_clauses(full_text)
    contract = extract_contract(full_text, contract_id=contract_id)
    if clauses:
        contract.clauses = clauses
        contract.cross_references = extract_cross_references(contract.clauses)

    ingest_stats: Optional[Dict[str, Any]] = None
    try:
        ingest_stats = ingest_contract(contract)
    except ValueError:
        # Neo4j not configured or connection failed
        pass
    return contract, ingest_stats
