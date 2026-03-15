"""
Graph model: node labels and relationship types aligned with schemas.contract.
Used by ingest and query.
"""
# Node labels
LABEL_CONTRACT = "Contract"
LABEL_CLAUSE = "Clause"
LABEL_DEFINITION = "Definition"
LABEL_PARTY = "Party"
LABEL_OBLIGATION = "Obligation"

# Relationship types
REL_REFERENCES = "REFERENCES"       # (Clause)-[:REFERENCES {ref_text}]->(Clause)
REL_DEFINES = "DEFINES"             # (Clause)-[:DEFINES]->(Definition)
REL_HAS_OBLIGATION = "HAS_OBLIGATION"  # (Clause)-[:HAS_OBLIGATION]->(Obligation)
REL_HAS_PARTY = "HAS_PARTY"         # (Contract)-[:HAS_PARTY]->(Party)
REL_HAS_CLAUSE = "HAS_CLAUSE"       # (Contract)-[:HAS_CLAUSE]->(Clause)
