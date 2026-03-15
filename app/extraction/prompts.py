"""
Single-call extraction: clauses (by section), definitions, parties, cross_references, obligations.
Placeholder: {text} for contract body. Literal braces in prompt are {{ }} for Python .format(text=...).
"""
EXTRACT_SYSTEM = """You extract structured contract information from long legal text.

Return exactly one valid JSON object and nothing else.

The JSON must contain these top-level keys exactly:
"clauses", "definitions", "parties", "cross_references", "obligations".

Output must be valid JSON parsable by json.loads(...). Use double-quoted property names, no trailing commas, and properly escaped strings.

Do not output markdown, code fences, commentary, or explanations."""

EXTRACT_USER_TEMPLATE = """Extract structured information from the following contract text.

Return exactly one valid JSON object with these top-level keys:
"clauses", "definitions", "parties", "cross_references", "obligations"

1. Clauses
- Split the contract at subsection level: every visible numbered subsection (e.g. 1.1, 1.2, 2.1, 2.2) must be a separate clause. Do not merge subsections.
- For each clause: "id" use underscore form (e.g. section_1_1, section_1_2); "section_id" use display form (e.g. "Section 1.1", "Section 1.2"); "text" is a short identifying snippet only (opening sentence or first ~500 chars of that subsection), not the full section text; "page" if known else null.
- Goal: complete clause coverage by subsection; keep "text" as a snippet so output stays compact.

2. Definitions
- Extract explicit definitions (e.g. "X" means ..., "X" shall mean ..., is defined as ...).
- For each: "term", "definition", "source_clause_id" (or null).

3. Parties
- Identify the contract parties (from preamble, signature, or context).
- For each: "name", "description" (role if known, else null).

4. Cross references
- If clearly present, extract; otherwise return []. For each: "from_clause_id", "to_clause_id", "ref_text" (or null).

5. Obligations
- If clearly present, extract; otherwise return []. For each: "description", "clause_id" (or null).

Return only valid JSON. No markdown. No code fences. Double-quoted keys. No trailing commas.

Example shape:
{{
  "clauses": [
    {{ "id": "section_1_1", "section_id": "Section 1.1", "text": "Supplier shall provide the services (the \\"Services\\") described in reasonable detail...", "page": null }},
    {{ "id": "section_1_2", "section_id": "Section 1.2", "text": "Supplier acknowledges that Company is entering into this Agreement...", "page": null }}
  ],
  "definitions": [
    {{ "term": "Services", "definition": "definition text", "source_clause_id": "1.1" }}
  ],
  "parties": [
    {{ "name": "Acme Inc.", "description": "Customer" }}
  ],
  "cross_references": [],
  "obligations": []
}}

Contract text:
{text}"""
