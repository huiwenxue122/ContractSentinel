"""
Risk memo schema: output of the review pipeline (Scanner → Critic → Evaluator).
Aligns with README example and API/frontend display.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Source location for a finding."""
    section: Optional[str] = Field(None, description="e.g. Section 7.3")
    page: Optional[int] = Field(None, description="Page number if known")


class RiskMemoItem(BaseModel):
    """One item in the structured risk memo."""
    clause: str = Field(..., description="Clause text or excerpt")
    clause_ref: Optional[str] = Field(None, description="e.g. section_7_2 or Section 7.2")
    risk_level: str = Field(..., description="High / Medium / Low")
    rule_triggered: str = Field(..., description="Rule id e.g. R001")
    reason: str = Field(..., description="Why this is a risk or evaluator rationale")
    fallback_language: Optional[str] = Field(None, description="Suggested replacement wording")
    escalation: str = Field(..., description="Acceptable | Suggest Revision | Escalate for Human Review")
    citation: Optional[Citation] = Field(None, description="Section / page reference")
    evidence_summary: Optional[str] = Field(None, description="Scanner evidence summary")
    justified: Optional[bool] = Field(None, description="Critic: finding justified or not")
    confidence: Optional[str] = Field(None, description="Critic confidence: high/medium/low")


class StructuredRiskMemo(BaseModel):
    """Full output of the review pipeline: list of risk items."""
    contract_id: Optional[str] = Field(None, description="Contract under review")
    items: List[RiskMemoItem] = Field(default_factory=list, description="Risk memo items")
