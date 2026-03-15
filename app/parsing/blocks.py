"""
Simple block types for PDF parsing output.
"""
from pydantic import BaseModel, Field
from typing import Optional


class TextBlock(BaseModel):
    """A block of text from the PDF (e.g. a paragraph), with optional page info."""
    text: str = Field(..., description="Block text content")
    page: Optional[int] = Field(None, description="1-based page number")
