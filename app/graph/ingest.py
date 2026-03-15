"""
Ingest extraction result (Contract) into Neo4j: nodes Clause, Definition, Party, Obligation;
edges REFERENCES, DEFINES, HAS_OBLIGATION, HAS_PARTY, HAS_CLAUSE.
"""
from typing import Any, Dict

from app.schemas.contract import Contract
from app.graph.client import get_driver
from app.graph.models import (
    LABEL_CLAUSE,
    LABEL_CONTRACT,
    LABEL_DEFINITION,
    LABEL_OBLIGATION,
    LABEL_PARTY,
    REL_DEFINES,
    REL_HAS_CLAUSE,
    REL_HAS_OBLIGATION,
    REL_HAS_PARTY,
    REL_REFERENCES,
)


def ingest_contract(contract: Contract) -> Dict[str, Any]:
    """
    Write Contract to Neo4j. Uses contract_id (or "unknown") to scope nodes.
    Clears existing nodes for this contract_id then creates fresh nodes and edges.
    Returns dict with node_counts and relationship_counts.
    """
    contract_id = contract.contract_id or "unknown"
    driver = get_driver()
    stats: Dict[str, Any] = {"node_counts": {}, "relationship_counts": {}}

    with driver.session() as session:
        # Clear existing subgraph for this contract
        session.run(
            "MATCH (n) WHERE n.contract_id = $contract_id OR (n:Contract AND n.id = $contract_id) DETACH DELETE n",
            contract_id=contract_id,
        )

        # Create Contract node
        session.run(
            "CREATE (c:Contract {id: $contract_id}) SET c.contract_id = $contract_id",
            contract_id=contract_id,
        )
        stats["node_counts"]["Contract"] = 1

        # Clauses
        for clause in contract.clauses:
            session.run(
                """
                MATCH (contract:Contract {id: $contract_id})
                MERGE (c:Clause {contract_id: $contract_id, id: $clause_id})
                SET c.section_id = $section_id, c.text = $text, c.page = $page
                MERGE (contract)-[:HAS_CLAUSE]->(c)
                """,
                contract_id=contract_id,
                clause_id=clause.id,
                section_id=clause.section_id or "",
                text=(clause.text or "")[:10000],
                page=clause.page,
            )
        stats["node_counts"]["Clause"] = len(contract.clauses)
        stats["relationship_counts"]["HAS_CLAUSE"] = len(contract.clauses)

        # Definitions + DEFINES from source clause (link only when clause exists)
        for d in contract.definitions:
            session.run(
                """
                CREATE (def:Definition {contract_id: $contract_id, term: $term, definition: $definition, source_clause_id: $source_clause_id})
                WITH def
                OPTIONAL MATCH (c:Clause {contract_id: $contract_id, id: $source_clause_id})
                WITH def, c WHERE c IS NOT NULL
                CREATE (c)-[:DEFINES]->(def)
                """,
                contract_id=contract_id,
                term=d.term,
                definition=(d.definition or "")[:5000],
                source_clause_id=d.source_clause_id or "",
            )
        stats["node_counts"]["Definition"] = len(contract.definitions)
        stats["relationship_counts"]["DEFINES"] = len(contract.definitions)

        # Parties
        for p in contract.parties:
            session.run(
                """
                MATCH (contract:Contract {id: $contract_id})
                CREATE (party:Party {contract_id: $contract_id, name: $name, description: $description})
                CREATE (contract)-[:HAS_PARTY]->(party)
                """,
                contract_id=contract_id,
                name=p.name,
                description=p.description or "",
            )
        stats["node_counts"]["Party"] = len(contract.parties)
        stats["relationship_counts"]["HAS_PARTY"] = len(contract.parties)

        # Obligations + HAS_OBLIGATION from clause (link only when clause exists)
        for o in contract.obligations:
            session.run(
                """
                CREATE (obl:Obligation {contract_id: $contract_id, description: $description, clause_id: $clause_id})
                WITH obl
                OPTIONAL MATCH (c:Clause {contract_id: $contract_id, id: $clause_id})
                WITH obl, c WHERE c IS NOT NULL
                CREATE (c)-[:HAS_OBLIGATION]->(obl)
                """,
                contract_id=contract_id,
                description=(o.description or "")[:2000],
                clause_id=o.clause_id or "",
            )
        stats["node_counts"]["Obligation"] = len(contract.obligations)
        stats["relationship_counts"]["HAS_OBLIGATION"] = len(contract.obligations)

        # Cross-references: (from_clause)-[:REFERENCES {ref_text}]->(to_clause)
        for ref in contract.cross_references:
            session.run(
                """
                MATCH (from:Clause {contract_id: $contract_id, id: $from_id})
                MATCH (to:Clause {contract_id: $contract_id, id: $to_id})
                MERGE (from)-[r:REFERENCES]->(to) SET r.ref_text = $ref_text
                """,
                contract_id=contract_id,
                from_id=ref.from_clause_id,
                to_id=ref.to_clause_id,
                ref_text=ref.ref_text or "",
            )
        stats["relationship_counts"]["REFERENCES"] = len(contract.cross_references)

    return stats
