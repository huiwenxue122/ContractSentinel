# Shared pipeline: parse -> segment -> extract -> ingest
from app.pipeline.run_structural import run_structural_pipeline

__all__ = ["run_structural_pipeline"]
