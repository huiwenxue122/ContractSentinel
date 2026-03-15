"""
API dependencies: Neo4j driver, health checks for Neo4j and LLM.
Used by health and contract routes.
"""
from typing import Any, Dict

from app.config import get_settings
from app.graph.client import get_driver


def check_neo4j() -> Dict[str, Any]:
    """
    Check Neo4j connectivity. Returns {"ok": bool, "error": str | None}.
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("RETURN 1")
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_llm() -> Dict[str, Any]:
    """
    Check LLM (OpenAI) availability: API key set and optionally reachable.
    Returns {"ok": bool, "error": str | None}. We only check key presence to avoid extra latency.
    """
    try:
        s = get_settings()
        if not (s.openai_api_key or "").strip():
            return {"ok": False, "error": "OPENAI_API_KEY is not set"}
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}
