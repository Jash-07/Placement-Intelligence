"""
Pydantic data contracts for PII-001 Candidate-Role Fit Scorer Engine
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from pii_001.skill_extractor.schemas import SkillCategory


class SkillMatchStatus(str, Enum):
    MATCHED_REQUIRED = "matched_required"
    MATCHED_PREFERRED = "matched_preferred"
    MISSING_REQUIRED = "missing_required"
    MISSING_PREFERRED = "missing_preferred"


class SkillEvidenceDetail(BaseModel):
    """Detailed evidence grounding comparing candidate resume span vs JD span for a skill."""
    skill_id: str = Field(description="Canonical skill ID from taxonomy")
    canonical_name: str = Field(description="Official display name")
    category: SkillCategory = Field(description="Skill category classification")
    status: SkillMatchStatus = Field(description="Categorized match status")
    resume_evidence_span: Optional[str] = Field(default=None, description="Surrounding context snippet from candidate resume")
    jd_evidence_span: Optional[str] = Field(default=None, description="Surrounding context snippet from job description")


class CandidateRoleFitReport(BaseModel):
    """Comprehensive, auditable fit analysis report comparing candidate skills to job requirements."""
    report_id: str = Field(description="Unique UUID for this fit report")
    candidate_doc_id: str = Field(description="Source candidate resume document ID")
    jd_id: str = Field(description="Source job description ID")
    role_title: Optional[str] = Field(default=None, description="Extracted job title")
    company_name: Optional[str] = Field(default=None, description="Extracted company name")
    overall_fit_score: float = Field(ge=0.0, le=100.0, description="Weighted fit score (0.0 to 100.0)")
    required_skills_score: float = Field(ge=0.0, le=100.0, description="Mandatory skills match score (0.0 to 100.0)")
    preferred_skills_score: float = Field(ge=0.0, le=100.0, description="Nice-to-have skills match score (0.0 to 100.0)")
    matched_required_skills: List[str] = Field(default_factory=list, description="Canonical names of matched required skills")
    matched_preferred_skills: List[str] = Field(default_factory=list, description="Canonical names of matched preferred skills")
    missing_required_skills: List[str] = Field(default_factory=list, description="Canonical names of missing required skills (gaps)")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Canonical names of missing preferred skills")
    skill_details: List[SkillEvidenceDetail] = Field(default_factory=list, description="Detailed evidence grounding list")
    summary_explanation: str = Field(description="Human-readable text summary of fit analysis")
    scoring_time_ms: float = Field(description="Fit scoring duration in ms")
