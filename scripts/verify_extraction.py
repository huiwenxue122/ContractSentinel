"""
Verify extraction: save Contract to JSON and print a short report.
Run from project root:
  python scripts/verify_extraction.py "data/sample_contracts/EX-10.4(a).pdf"
Output: out/contract_<stem>.json + summary to stdout.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing import parse_pdf
from app.extraction import extract_contract


def main() -> None:
    if len(sys.argv) < 2:
        pdf_path = Path(__file__).resolve().parent.parent / "data" / "sample_contracts" / "EX-10.4(a).pdf"
    else:
        pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"Parsing: {pdf_path}")
    full_text, blocks = parse_pdf(pdf_path)
    print(f"  -> {len(full_text)} chars, {len(blocks)} pages")

    print("Extracting (LLM)...")
    contract = extract_contract(full_text, contract_id=pdf_path.stem)

    # Summary
    print("\n--- 抽取结果摘要 ---")
    print(f"条款(clauses):     {len(contract.clauses)} 条")
    print(f"定义(definitions): {len(contract.definitions)} 条")
    print(f"交叉引用:         {len(contract.cross_references)} 条")
    print(f"当事方(parties):   {len(contract.parties)} 条")
    print(f"义务(obligations): {len(contract.obligations)} 条")

    if contract.parties:
        print("\n当事方:")
        for p in contract.parties:
            print(f"  - {p.name}" + (f"  ({p.description})" if p.description else ""))

    if contract.definitions:
        print("\n定义 (前 5 个):")
        for d in contract.definitions[:5]:
            print(f"  - {d.term}: {d.definition[:80]}...")

    print("\n条款列表 (section_id):")
    for c in contract.clauses[:15]:
        print(f"  - {c.section_id or c.id}: {c.text[:60].replace(chr(10), ' ')}...")
    if len(contract.clauses) > 15:
        print(f"  ... 共 {len(contract.clauses)} 条")

    # Save JSON for manual inspection
    out_dir = Path(__file__).resolve().parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"contract_{pdf_path.stem}.json"
    # Pydantic model_dump for JSON-serializable dict
    data = contract.model_dump()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到: {out_file}")
    print("  -> 打开该 JSON 可逐条对照 PDF 检查条款、定义是否一致。")


if __name__ == "__main__":
    main()
