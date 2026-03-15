"""
Health check: Neo4j and LLM availability.
GET /health -> { "status": "ok" | "degraded", "neo4j": bool, "llm": bool }
Returns 200 if status is ok, 503 if degraded.
"""
from fastapi import APIRouter, Response, status

from app.api.deps import check_llm, check_neo4j

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response):
    neo4j_result = check_neo4j()
    llm_result = check_llm()
    neo4j_ok = neo4j_result["ok"]
    llm_ok = llm_result["ok"]
    status_val = "ok" if (neo4j_ok and llm_ok) else "degraded"
    response.status_code = status.HTTP_200_OK if status_val == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": status_val,
        "neo4j": neo4j_ok,
        "llm": llm_ok,
        "neo4j_error": neo4j_result.get("error"),
        "llm_error": llm_result.get("error"),
    }
