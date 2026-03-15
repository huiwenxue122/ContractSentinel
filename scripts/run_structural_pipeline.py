r"""
Test PDF -> parse -> extract -> Contract (no Neo4j yet).
Usage (from project root):
  python scripts/run_structural_pipeline.py "data/sample_contracts/EX-10.4(a).pdf"
  or
  python scripts/run_structural_pipeline.py
"""
import sys
from pathlib import Path

# Allow importing app when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing import parse_pdf
from app.extraction import extract_contract, extract_cross_references, segment_clauses
from app.graph import ingest_contract


def main() -> None:
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path(__file__).resolve().parent.parent / "data" / "sample_contracts" / "EX-10.4(a).pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        print("Usage: python scripts/run_structural_pipeline.py [path/to/contract.pdf]")
        sys.exit(1)

    print(f"Parsing: {pdf_path}")
    full_text, blocks = parse_pdf(pdf_path)
    print(f"  -> {len(full_text)} chars, {len(blocks)} pages")

    # 1) Rule-based clause segmentation (stable count; no LLM)
    clauses, seg_stats = segment_clauses(full_text)
    print(f"  -> rule-based clause segmentation raw matches: {seg_stats['raw_matches']}")
    print(f"  -> rule-based clauses after dedup/filter: {seg_stats['after_dedup_filter']}")
    if not clauses:
        print("  (warning: rule-based segmenter found no subsections, using LLM clauses)")

    # 2) LLM extraction for definitions / parties / obligations (clauses from step 1 overwrite LLM clauses)
    print("Extracting (LLM)...")
    contract = extract_contract(full_text, contract_id=pdf_path.stem)
    if clauses:
        contract.clauses = clauses
        contract.cross_references = extract_cross_references(contract.clauses)

    print(f"  -> {len(contract.clauses)} clauses, {len(contract.definitions)} definitions, "
          f"{len(contract.cross_references)} cross-refs, {len(contract.parties)} parties")

    # 3) Ingest into Neo4j (optional; skip if NEO4J_PASSWORD not set)
    try:
        stats = ingest_contract(contract)
        print(f"  -> Neo4j ingest: {stats['node_counts']} nodes, {stats['relationship_counts']} relationships")
    except ValueError as e:
        print(f"  -> Neo4j ingest skipped: {e}")

    # Show first 2 clauses
    for i, c in enumerate(contract.clauses[:2]):
        print(f"\nClause {i+1}: id={c.id} section_id={c.section_id}")
        print(f"  text: {c.text[:200]}...")


if __name__ == "__main__":
    main()
