"""
Query Neo4j for clause neighborhood: related clauses (REFERENCES), definitions (DEFINES), obligations (HAS_OBLIGATION).
Returns structured context for review/agents.
"""
from typing import Any, Dict, List, Optional

from app.graph.client import get_driver


def get_clause_neighborhood(
    contract_id: str,
    clause_id: str,
    max_refs: int = 20,
) -> Dict[str, Any]:
    """
    Get neighborhood of a clause: its text, outgoing/incoming REFERENCES, definitions it DEFINES, obligations it HAS.
    Returns dict with clause_text, references_out, references_in, definitions, obligations.
    """
    driver = get_driver()
    result: Dict[str, Any] = {
        "contract_id": contract_id,
        "clause_id": clause_id,
        "clause_text": "",
        "section_id": "",
        "references_out": [],
        "references_in": [],
        "definitions": [],
        "obligations": [],
    }

    with driver.session() as session:
        # Clause text
        r = session.run(
            """
            MATCH (c:Clause {contract_id: $contract_id, id: $clause_id})
            RETURN c.text AS text, c.section_id AS section_id
            """,
            contract_id=contract_id,
            clause_id=clause_id,
        )
        rec = r.single()
        if rec:
            result["clause_text"] = rec["text"] or ""
            result["section_id"] = rec["section_id"] or ""

        # Outgoing REFERENCES
        r = session.run(
            """
            MATCH (from:Clause {contract_id: $contract_id, id: $clause_id})-[rel:REFERENCES]->(to:Clause)
            RETURN to.id AS to_id, to.section_id AS to_section_id, rel.ref_text AS ref_text
            LIMIT $max_refs
            """,
            contract_id=contract_id,
            clause_id=clause_id,
            max_refs=max_refs,
        )
        result["references_out"] = [
            {"to_clause_id": rec["to_id"], "to_section_id": rec["to_section_id"] or "", "ref_text": rec["ref_text"] or ""}
            for rec in r
        ]

        # Incoming REFERENCES
        r = session.run(
            """
            MATCH (from:Clause)-[rel:REFERENCES]->(to:Clause {contract_id: $contract_id, id: $clause_id})
            RETURN from.id AS from_id, from.section_id AS from_section_id, rel.ref_text AS ref_text
            LIMIT $max_refs
            """,
            contract_id=contract_id,
            clause_id=clause_id,
            max_refs=max_refs,
        )
        result["references_in"] = [
            {"from_clause_id": rec["from_id"], "from_section_id": rec["from_section_id"] or "", "ref_text": rec["ref_text"] or ""}
            for rec in r
        ]

        # Definitions this clause DEFINES
        r = session.run(
            """
            MATCH (c:Clause {contract_id: $contract_id, id: $clause_id})-[:DEFINES]->(d:Definition)
            RETURN d.term AS term, d.definition AS definition
            """,
            contract_id=contract_id,
            clause_id=clause_id,
        )
        result["definitions"] = [{"term": rec["term"], "definition": rec["definition"] or ""} for rec in r]

        # Obligations this clause HAS_OBLIGATION
        r = session.run(
            """
            MATCH (c:Clause {contract_id: $contract_id, id: $clause_id})-[:HAS_OBLIGATION]->(o:Obligation)
            RETURN o.description AS description
            """,
            contract_id=contract_id,
            clause_id=clause_id,
        )
        result["obligations"] = [{"description": rec["description"] or ""} for rec in r]

    return result


def get_contract_summary(contract_id: str) -> Dict[str, Any]:
    """Return counts of clauses, definitions, parties, obligations for a contract."""
    driver = get_driver()
    with driver.session() as session:
        r = session.run(
            """
            MATCH (contract:Contract {id: $contract_id})
            OPTIONAL MATCH (contract)-[:HAS_CLAUSE]->(c:Clause)
            OPTIONAL MATCH (contract)-[:HAS_PARTY]->(p:Party)
            OPTIONAL MATCH (contract)-[:HAS_CLAUSE]->(cl:Clause)-[:DEFINES]->(d:Definition)
            OPTIONAL MATCH (contract)-[:HAS_CLAUSE]->(cl2:Clause)-[:HAS_OBLIGATION]->(o:Obligation)
            RETURN count(DISTINCT c) AS clauses,
                   count(DISTINCT p) AS parties,
                   count(DISTINCT d) AS definitions,
                   count(DISTINCT o) AS obligations
            """,
            contract_id=contract_id,
        )
        rec = r.single()
        if not rec:
            return {"contract_id": contract_id, "clauses": 0, "parties": 0, "definitions": 0, "obligations": 0}
        return {
            "contract_id": contract_id,
            "clauses": rec["clauses"] or 0,
            "parties": rec["parties"] or 0,
            "definitions": rec["definitions"] or 0,
            "obligations": rec["obligations"] or 0,
        }
