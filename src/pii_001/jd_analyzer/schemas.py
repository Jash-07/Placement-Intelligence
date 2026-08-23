"""
Pydantic data contracts for PII-001 Job Description Analysis (SP-003)
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from pii_001.skill_extractor.schemas import SkillCategory


class RequirementPriority(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    UNSPECIFIED = "unspecified"


class JDSectionType(str, Enum):
    ROLE_OVERVIEW = "role_overview"
    RESPONSIBILITIES = "responsibilities"
    REQUIREMENTS_QUALIFICATIONS = "requirements_qualifications"
    PREFERRED_QUALIFICATIONS = "preferred_qualifications"
    BENEFITS = "benefits"
    UNKNOWN = "unknown"


class ParsedJDSection(BaseModel):
    """Represents a segmented section within a Job Description."""
    section_type: JDSectionType = Field(description="Normalized JD section classification")
    heading_title: str = Field(description="Original section header title text")
    content: str = Field(description="Cleaned text content of section")
    start_line: int = Field(description="1-indexed starting line number")
    end_line: int = Field(description="1-indexed ending line number")


class ExtractedJDSkill(BaseModel):
    """Represents a skill requirement extracted from a Job Description with evidence and priority."""
    skill_id: str = Field(description="Canonical skill ID from taxonomy")
    canonical_name: str = Field(description="Official skill display name")
    category: SkillCategory = Field(description="Category classification")
    priority: RequirementPriority = Field(description="Mandatory (Required) vs Optional (Preferred)")
    matched_alias: str = Field(description="Exact string matched in JD text")
    evidence_text_span: str = Field(description="Surrounding text snippet establishing context")
    section_type: JDSectionType = Field(description="JD section origin where skill was extracted")


class NormalizedJobDescription(BaseModel):
    """Canonical representation of a parsed Job Description passed to fit scoring engines."""
    jd_id: str = Field(description="Unique ID or hash for the job description")
    role_title: Optional[str] = Field(default=None, description="Extracted job title if identified")
    company_name: Optional[str] = Field(default=None, description="Extracted company name if identified")
    raw_text: str = Field(description="Full unsegmented text of the job posting")
    sections: List[ParsedJDSection] = Field(default_factory=list)
    required_skills: List[ExtractedJDSkill] = Field(default_factory=list)
    preferred_skills: List[ExtractedJDSkill] = Field(default_factory=list)
    all_extracted_skills: List[ExtractedJDSkill] = Field(default_factory=list)
    total_skills_required: int = Field(description="Count of unique mandatory skills")
    total_skills_preferred: int = Field(description="Count of unique preferred skills")
    parsing_time_ms: float = Field(description="JD parsing and requirement extraction duration in ms")
