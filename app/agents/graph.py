"""
LangGraph multi-agent orchestration (Task 12): Scanner → Critic → Evaluator per clause.
Input: contract_id, optional clause_ids, Playbook. Output: StructuredRiskMemo.
"""
import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas.risk_memo import RiskMemoItem, StructuredRiskMemo
from app.schemas.playbook import Rule


class ReviewState(TypedDict):
    contract_id: str
    clause_ids: List[str]
    rules_list: List[Dict[str, Any]]  # serializable Rule-like dicts
    items: Annotated[List[Dict[str, Any]], operator.add]
    current_index: int
    current_ctx: Optional[Dict[str, Any]]
    current_findings: List[Dict[str, Any]]
    current_finding_index: int


def _get_clause_ids(contract_id: str) -> List[str]:
    from app.graph.client import get_driver
    driver = get_driver()
    with driver.session() as session:
        r = session.run(
            "MATCH (c:Clause {contract_id: $contract_id}) RETURN c.id AS id ORDER BY c.id",
            contract_id=contract_id,
        )
        return [rec["id"] for rec in r if rec.get("id")]


def _process_node(state: ReviewState) -> Dict[str, Any]:
    """One step: either load next clause and scan, or run Critic+Evaluator on next finding."""
    from app.retrieval import get_context_for_clause
    from app.agents import scan_clause, evaluate_finding, evaluate_escalation

    contract_id = state["contract_id"]
    clause_ids = state["clause_ids"]
    rules_list = state["rules_list"]
    current_index = state["current_index"]
    current_ctx = state.get("current_ctx")
    current_findings = state.get("current_findings") or []
    current_finding_index = state.get("current_finding_index") or 0

    rules = [Rule.model_validate(r) for r in rules_list]
    rule_by_id = {r.rule_id: r for r in rules}

    # No more clauses
    if current_index >= len(clause_ids):
        return {"current_index": current_index}

    # Need to load next clause and run Scanner
    if current_ctx is None:
        clause_id = clause_ids[current_index]
        ctx = get_context_for_clause(contract_id, clause_id)
        clause_text = (ctx.get("clause_text") or "").strip()
        graph_context = ctx.get("graph_context") or ""
        clause_ref = ctx.get("section_id") or clause_id
        findings = scan_clause(
            clause_text=ctx.get("clause_text") or "",
            clause_ref=clause_ref,
            rules=rules,
            graph_context=graph_context,
        )
        if not findings:
            return {
                "current_index": current_index + 1,
                "current_ctx": None,
                "current_findings": [],
                "current_finding_index": 0,
            }
        return {
            "current_ctx": ctx,
            "current_findings": findings,
            "current_finding_index": 0,
        }

    # Process next finding: Critic → Evaluator → append item
    if current_finding_index < len(current_findings):
        f = current_findings[current_finding_index]
        rule = rule_by_id.get(f.get("rule_triggered"))
        rule_desc = (rule.description or "") + (" " + (rule.criteria or "") if rule and rule.criteria else "") if rule else ""
        risk_level = rule.risk_level.value if rule else "Medium"
        clause_text = (current_ctx.get("clause_text") or "").strip()
        graph_context = current_ctx.get("graph_context") or ""

        critic_result = evaluate_finding(
            finding=f,
            clause_text=clause_text,
            graph_context=graph_context,
            rule_description=rule_desc or f"Rule {f.get('rule_triggered')}",
        )
        eval_result = evaluate_escalation(
            finding=f,
            critic_result=critic_result,
            risk_level=risk_level,
            clause_text=clause_text,
        )

        clause_ref = current_ctx.get("section_id") or current_ctx.get("clause_id") or ""
        item = {
            "clause": (clause_text or "")[:500],
            "clause_ref": clause_ref,
            "risk_level": risk_level,
            "rule_triggered": f.get("rule_triggered", ""),
            "reason": eval_result.get("reason", ""),
            "fallback_language": eval_result.get("fallback_language"),
            "escalation": eval_result.get("escalation", ""),
            "citation": {"section": clause_ref, "page": None},
            "evidence_summary": f.get("evidence_summary"),
            "justified": critic_result.get("justified"),
            "confidence": critic_result.get("confidence"),
        }
        return {
            "items": [item],
            "current_finding_index": current_finding_index + 1,
        }

    # Done with findings for this clause; move to next clause
    return {
        "current_index": current_index + 1,
        "current_ctx": None,
        "current_findings": [],
        "current_finding_index": 0,
    }


def _route_after_process(state: ReviewState) -> Literal["process", "__end__"]:
    """Continue to process if there is more work; else END."""
    current_index = state.get("current_index") or 0
    clause_ids = state.get("clause_ids") or []
    if current_index >= len(clause_ids):
        return "__end__"
    current_ctx = state.get("current_ctx")
    current_findings = state.get("current_findings") or []
    current_finding_index = state.get("current_finding_index") or 0
    # More findings to process on current clause
    if current_ctx is not None and current_finding_index < len(current_findings):
        return "process"
    # More clauses to process (current_ctx will be None after update, or we just advanced index)
    if current_index < len(clause_ids):
        return "process"
    return "__end__"


def build_review_graph():
    """Build the Scanner → Critic → Evaluator LangGraph."""
    builder = StateGraph(ReviewState)
    builder.add_node("process", _process_node)
    builder.add_edge(START, "process")
    builder.add_conditional_edges("process", _route_after_process, {"process": "process", "__end__": END})
    return builder.compile()


def run_review(
    contract_id: str,
    clause_ids: Optional[List[str]] = None,
    rules: Optional[List[Rule]] = None,
    playbook_path: Optional[str] = None,
) -> StructuredRiskMemo:
    """
    Run the full review pipeline (Scanner → Critic → Evaluator) on the given contract
    and optional clause list. Returns StructuredRiskMemo for API/frontend.

    contract_id: contract id in Neo4j.
    clause_ids: if None, all clauses for the contract are used.
    rules: if None, playbook_path must be provided to load rules.
    playbook_path: path to playbook YAML (used if rules is None).
    """
    from pathlib import Path
    from app.agents.playbook_loader import load_playbook

    if rules is None:
        if not playbook_path:
            playbook_path = str(Path(__file__).resolve().parent.parent.parent / "data" / "playbooks" / "default.yaml")
        rules = load_playbook(playbook_path)
    if clause_ids is None:
        clause_ids = _get_clause_ids(contract_id)
    if not clause_ids:
        return StructuredRiskMemo(contract_id=contract_id, items=[])

    rules_list = [r.model_dump() for r in rules]
    initial: ReviewState = {
        "contract_id": contract_id,
        "clause_ids": clause_ids,
        "rules_list": rules_list,
        "items": [],
        "current_index": 0,
        "current_ctx": None,
        "current_findings": [],
        "current_finding_index": 0,
    }
    graph = build_review_graph()
    final = graph.invoke(initial)
    items = [RiskMemoItem.model_validate(i) for i in (final.get("items") or [])]
    return StructuredRiskMemo(contract_id=contract_id, items=items)
