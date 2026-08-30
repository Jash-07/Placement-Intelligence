"""
Unified Skill-Gap Report Schema for PII-001 MVP

Wraps all sub-component outputs into a single auditable report.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from pii_001.resume_parser.schemas import NormalizedResumeDocument
from pii_001.skill_extractor.schemas import CandidateSkillProfile
from pii_001.jd_analyzer.schemas import NormalizedJobDescription
from pii_001.fit_scorer.schemas import CandidateRoleFitReport
from pii_001.rag_retriever.schemas import RetrievedContext


class PipelineDiagnostics(BaseModel):
    """Telemetry and diagnostics for the full pipeline execution."""
    pipeline_version: str = Field(default="0.1.0-mvp")
    total_pipeline_time_ms: float = Field(description="End-to-end pipeline execution time in ms")
    resume_parsing_time_ms: float = Field(default=0.0)
    skill_extraction_time_ms: float = Field(default=0.0)
    jd_parsing_time_ms: float = Field(default=0.0)
    fit_scoring_time_ms: float = Field(default=0.0)
    rag_retrieval_time_ms: float = Field(default=0.0)
    warnings: List[str] = Field(default_factory=list)
    stages_completed: List[str] = Field(default_factory=list)


class SkillGapReport(BaseModel):
    """MVP unified output: the complete Placement Intelligence analysis report."""
    report_id: str = Field(description="Unique report identifier")

    # Sub-component outputs
    resume_document: NormalizedResumeDocument = Field(description="Parsed resume output (SP-001)")
    candidate_skills: CandidateSkillProfile = Field(description="Extracted skill profile (SP-002)")
    job_description: NormalizedJobDescription = Field(description="Parsed JD output (SP-003)")
    fit_report: CandidateRoleFitReport = Field(description="Fit scoring and gap analysis (SP-004)")
    interview_prep_contexts: List[RetrievedContext] = Field(
        default_factory=list, description="RAG-retrieved interview prep passages (SP-005)"
    )

    # Pipeline metadata
    diagnostics: PipelineDiagnostics = Field(description="Pipeline execution diagnostics")
