"""Pydantic schemas for evidence agent outputs."""
from pydantic import BaseModel
from typing import Optional


class EvidenceNote(BaseModel):
    """Plain-language note for a single school."""
    school_id: int
    school_name: str
    note: str
    source: str  # "granite" | "template"


class DistrictSummary(BaseModel):
    """Data-quality summary for a district."""
    district: str
    summary: str
    source: str
    stats: dict


class EvidenceAgentOutput(BaseModel):
    """Full output from the evidence agent."""
    school_notes: list[EvidenceNote]
    district_summaries: list[DistrictSummary]
    provenance: str = "OFFICIAL"
