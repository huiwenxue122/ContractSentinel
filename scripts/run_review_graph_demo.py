"""
Demo: run full review pipeline via LangGraph (Scanner → Critic → Evaluator) on a contract.
  python scripts/run_review_graph_demo.py "EX-10.4(a)"
  python scripts/run_review_graph_demo.py "EX-10.4(a)" --clauses section_5_1 section_7_2
Output: StructuredRiskMemo (contract_id + items with clause, risk_level, rule_triggered, escalation, etc.).
Requires Neo4j + OPENAI_API_KEY.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Run LangGraph review pipeline")
    parser.add_argument("contract_id", nargs="?", default="EX-10.4(a)", help="Contract ID in Neo4j")
    parser.add_argument("--clauses", nargs="*", help="Optional clause IDs; if omitted, all clauses")
    parser.add_argument("--playbook", default=None, help="Path to playbook YAML (default: data/playbooks/default.yaml)")
    args = parser.parse_args()

    from app.agents import run_review

    playbook_path = args.playbook or str(Path(__file__).resolve().parent.parent / "data" / "playbooks" / "default.yaml")
    memo = run_review(
        contract_id=args.contract_id,
        clause_ids=args.clauses if args.clauses else None,
        playbook_path=playbook_path,
    )
    print(f"Contract: {memo.contract_id}")
    print(f"Items: {len(memo.items)}\n")
    for i, item in enumerate(memo.items, 1):
        print(f"  {i}. [{item.rule_triggered}] {item.clause_ref or '?'} — {item.risk_level}")
        print(f"     Escalation: {item.escalation}")
        print(f"     Reason: {item.reason[:100]}{'...' if len(item.reason) > 100 else ''}")
        if item.fallback_language:
            print(f"     Fallback: {item.fallback_language[:80]}...")
        print()
    print("JSON (first 2000 chars):")
    print(json.dumps(memo.model_dump(), indent=2, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    main()
