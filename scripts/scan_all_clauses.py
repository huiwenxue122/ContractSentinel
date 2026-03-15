"""
扫完整合同：对图中所有 clause 跑 Scanner，汇总并保存结果。

逻辑：
  for clause in graph:
      findings = scan_clause(...)
      save results

输出：
  - 终端：表头 Clause | Rule | Risk Level，每行一条 finding
  - 文件：out/scan_<contract_id>.tsv（Clause, Rule, Risk Level, Evidence）
  - Neo4j：Clause -[:TRIGGERS {evidence?}]-> Rule，便于 Critic Agent 直接读取

用法（项目根、已激活 .venv，需 Neo4j + OPENAI_API_KEY）：
  python scripts/scan_all_clauses.py
  python scripts/scan_all_clauses.py "EX-10.4(a)"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Max evidence length stored on TRIGGERS edge
MAX_EVIDENCE_ON_EDGE = 1000


def _get_clause_ids_in_graph(contract_id: str):
    from app.graph.client import get_driver
    driver = get_driver()
    with driver.session() as session:
        r = session.run(
            "MATCH (c:Clause {contract_id: $contract_id}) RETURN c.id AS id ORDER BY c.id",
            contract_id=contract_id,
        )
        return [rec["id"] for rec in r if rec.get("id")]


def main():
    contract_id = sys.argv[1] if len(sys.argv) > 1 else "EX-10.4(a)"
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "out"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"scan_{contract_id}.tsv"

    from app.retrieval import get_context_for_clause
    from app.agents import load_playbook, scan_clause

    rules = load_playbook(root / "data" / "playbooks" / "default.yaml")
    rule_id_to_level = {r.rule_id: r.risk_level.value for r in rules}
    ids = _get_clause_ids_in_graph(contract_id)
    if not ids:
        print(f"No clauses in graph for {contract_id}. Run run_structural_pipeline.py first.")
        sys.exit(1)

    rows = []  # (clause_id, rule_id, risk_level, evidence)
    skipped_empty = 0

    print(f"Scanning {len(ids)} clauses for contract {contract_id} ...\n")
    for i, clause_id in enumerate(ids, 1):
        ctx = get_context_for_clause(contract_id, clause_id)
        clause_text = (ctx.get("clause_text") or "").strip()
        if not clause_text:
            skipped_empty += 1
            continue
        findings = scan_clause(
            clause_text=ctx["clause_text"],
            clause_ref=ctx.get("section_id") or clause_id,
            rules=rules,
            graph_context=ctx.get("graph_context") or "",
        )
        for f in findings:
            rule_id = f.get("rule_triggered", "")
            risk_level = rule_id_to_level.get(rule_id, "")
            evidence = (f.get("evidence_summary") or "").replace("\t", " ").replace("\n", " ")
            rows.append((clause_id, rule_id, risk_level, evidence))

    # Print table: Clause | Rule | Risk Level
    print("Clause              | Rule   | Risk Level")
    print("-" * 50)
    for clause_id, rule_id, risk_level, _ in rows:
        print(f"{clause_id:20} | {rule_id:6} | {risk_level}")
    if not rows:
        print("(no findings)")
    print()
    if skipped_empty:
        print(f"Skipped {skipped_empty} clauses with empty text.")
    print(f"Total findings: {len(rows)}")

    # Save TSV: Clause, Rule, Risk Level, Evidence
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Clause\tRule\tRisk Level\tEvidence\n")
        for clause_id, rule_id, risk_level, evidence in rows:
            f.write(f"{clause_id}\t{rule_id}\t{risk_level}\t{evidence}\n")
    print(f"Results saved to {out_path}")

    # Write findings back to Neo4j: Clause -[:TRIGGERS]-> Rule (Critic can read)
    if rows:
        from app.graph.client import get_driver
        from app.graph.models import LABEL_CLAUSE, LABEL_RULE, REL_TRIGGERS

        driver = get_driver()
        with driver.session() as session:
            # Ensure Rule nodes exist (MERGE from playbook)
            for r in rules:
                session.run(
                    """
                    MERGE (rule:Rule {id: $rule_id})
                    SET rule.risk_level = $risk_level, rule.description = $description
                    """,
                    rule_id=r.rule_id,
                    risk_level=r.risk_level.value,
                    description=(r.description or "")[:500],
                )
            # Remove existing TRIGGERS from this contract's clauses so re-run replaces
            session.run(
                """
                MATCH (c:Clause {contract_id: $contract_id})-[rel:TRIGGERS]->()
                DELETE rel
                """,
                contract_id=contract_id,
            )
            # Create Clause -[:TRIGGERS {evidence?}]-> Rule
            for clause_id, rule_id, risk_level, evidence in rows:
                evidence_short = (evidence or "")[:MAX_EVIDENCE_ON_EDGE]
                session.run(
                    """
                    MATCH (c:Clause {contract_id: $contract_id, id: $clause_id})
                    MATCH (r:Rule {id: $rule_id})
                    MERGE (c)-[rel:TRIGGERS]->(r)
                    SET rel.evidence = $evidence
                    """,
                    contract_id=contract_id,
                    clause_id=clause_id,
                    rule_id=rule_id,
                    evidence=evidence_short,
                )
        print(f"Neo4j: {len(rows)} TRIGGERS edges written (Clause -[:TRIGGERS]-> Rule).")
    else:
        print("Neo4j: no findings, no TRIGGERS written.")


if __name__ == "__main__":
    main()
