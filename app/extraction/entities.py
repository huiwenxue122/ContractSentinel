"""
Single-call LLM extraction: contract text -> Contract (clauses, definitions, parties, cross_refs, obligations).
"""
import json
import re
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.schemas.contract import (
    Contract,
    Clause,
    Definition,
    CrossReference,
    Party,
    Obligation,
)
from app.extraction.prompts import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE


def _extract_json_from_response(content: str) -> dict:
    """Parse JSON from LLM response. Strip markdown, then parse with fallback repair."""
    text = content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    first = text.find("{")
    if first >= 0:
        depth = 0
        for i in range(first, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    text = text[first : i + 1]
                    break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    repaired = re.sub(r",\s*}(?=\s*[\]}])", "}", text)
    repaired = re.sub(r",\s*](?=\s*[\]}])", "]", repaired)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass
    try:
        from json_repair import repair_json
        return json.loads(repair_json(text))
    except ImportError:
        pass
    except Exception:
        pass
    raise ValueError(
        "LLM returned invalid JSON (e.g. unescaped quote or trailing comma). Try running again."
    )


def extract_contract(text: str, contract_id: Optional[str] = None) -> Contract:
    """
    Single LLM call to extract clauses, definitions, parties, cross_references, obligations.
    Merges into one Contract.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=settings.openai_api_key, timeout=180.0)
    capped = text[:settings.openai_max_input_chars]

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": EXTRACT_USER_TEMPLATE.format(text=capped)},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_tokens=settings.openai_max_output_tokens,
    )
    content = response.choices[0].message.content or "{}"
    data = _extract_json_from_response(content)

    clauses = [
        Clause(
            id=str(item.get("id", f"clause_{i}")),
            section_id=item.get("section_id") or None,
            text=item.get("text", ""),
            page=item.get("page"),
        )
        for i, item in enumerate(data.get("clauses", []))
    ]
    definitions = [
        Definition(
            term=d.get("term", ""),
            definition=d.get("definition", ""),
            source_clause_id=d.get("source_clause_id"),
        )
        for d in data.get("definitions", [])
    ]
    cross_references = [
        CrossReference(
            from_clause_id=str(ref.get("from_clause_id", "")),
            to_clause_id=str(ref.get("to_clause_id", "")),
            ref_text=ref.get("ref_text"),
        )
        for ref in data.get("cross_references", [])
    ]
    parties = [
        Party(name=p.get("name", ""), description=p.get("description"))
        for p in data.get("parties", [])
    ]
    obligations = [
        Obligation(
            description=o.get("description", ""),
            clause_id=o.get("clause_id"),
        )
        for o in data.get("obligations", [])
    ]

    return Contract(
        contract_id=contract_id,
        raw_text=text,
        clauses=clauses,
        definitions=definitions,
        cross_references=cross_references,
        parties=parties,
        obligations=obligations,
    )
