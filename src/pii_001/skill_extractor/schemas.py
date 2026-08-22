"""
Pydantic data contracts for PII-001 Skill Extraction & Taxonomy Mapping (SP-002)
"""

from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, Field
from pii_001.resume_parser.schemas import SectionType


class SkillCategory(str, Enum):
    PROGRAMMING_LANGUAGES = "programming_languages"
    FRAMEWORKS_LIBRARIES = "frameworks_libraries"
    DATABASES_STORAGE = "databases_storage"
    CLOUD_DEVOPS = "cloud_devops"
    AI_ML_NLP = "ai_ml_nlp"
    DEVELOPMENT_TOOLS = "development_tools"
    METHODOLOGIES = "methodologies"


class SkillTaxonomyEntry(BaseModel):
    """Definition of a canonical skill in the taxonomy."""
    skill_id: str = Field(description="Unique identifier (slug) for the skill")
    canonical_name: str = Field(description="Official display name of the skill")
    category: SkillCategory = Field(description="Skill category classification")
    aliases: List[str] = Field(default_factory=list, description="Synonyms, abbreviations, and variation strings")


class ExtractedSkillMatch(BaseModel):
    """Represents a skill identified in a resume with explicit evidence grounding."""
    skill_id: str = Field(description="Canonical skill ID")
    canonical_name: str = Field(description="Official display name")
    category: SkillCategory = Field(description="Category classification")
    matched_alias: str = Field(description="Exact string or alias found in resume text")
    section_type: SectionType = Field(description="Resume section where skill was identified")
    evidence_text_span: str = Field(description="Surrounding text snippet providing evidence")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class CandidateSkillProfile(BaseModel):
    """Complete candidate skill profile extracted from a NormalizedResumeDocument."""
    document_id: str = Field(description="Source document ID")
    total_skills_found: int = Field(description="Total count of unique canonical skills extracted")
    extracted_skills: List[ExtractedSkillMatch] = Field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = Field(
        default_factory=dict, description="Map of category name to list of canonical skill names"
    )
    extraction_time_ms: float = Field(description="Extraction latency in milliseconds")
