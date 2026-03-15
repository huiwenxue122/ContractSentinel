"""
Contract structure: clauses, definitions, parties, obligations, cross-references.
Used by extraction output and graph ingest.
"""
from pydantic import BaseModel, Field
from typing import Optional


class Clause(BaseModel):
    """A contract clause/section (by Section)."""
    id: str = Field(..., description="Unique id, e.g. section number")
    section_id: Optional[str] = Field(None, description="Section id as in document")
    text: str = Field(..., description="Clause text (full section text)")
    page: Optional[int] = None


class Definition(BaseModel):
    """A defined term in the contract."""
    term: str = Field(..., description="The defined term")
    definition: str = Field(..., description="Definition text")
    source_clause_id: Optional[str] = Field(None, description="Clause where defined")


class CrossReference(BaseModel):
    """Reference from one clause to another."""
    from_clause_id: str = Field(..., description="Clause that contains the reference")
    to_clause_id: str = Field(..., description="Referenced clause/section")
    ref_text: Optional[str] = Field(None, description="Raw reference text, e.g. 'Section 4.1'")


class Party(BaseModel):
    """Contract party."""
    name: str = Field(..., description="Party name or role")
    description: Optional[str] = None


class Obligation(BaseModel):
    """Obligation linked to a clause."""
    description: str = Field(..., description="Obligation description")
    clause_id: Optional[str] = Field(None, description="Clause imposing the obligation")


class Contract(BaseModel):
    """Full contract structure after extraction."""
    contract_id: Optional[str] = Field(None, description="Optional id for this contract")
    raw_text: str = Field(default="", description="Full document text")
    clauses: list[Clause] = Field(default_factory=list)
    definitions: list[Definition] = Field(default_factory=list)
    cross_references: list[CrossReference] = Field(default_factory=list)
    parties: list[Party] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
