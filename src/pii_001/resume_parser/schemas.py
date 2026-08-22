"""
Pydantic data contracts for PII-001 Resume Parser Baseline (SP-001)
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SectionType(str, Enum):
    CONTACT_INFO = "contact_info"
    SUMMARY = "summary"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    UNKNOWN = "unknown"


class DetectedSection(BaseModel):
    """Represents an identified section boundary within the resume."""
    section_type: SectionType = Field(description="Normalized section category")
    heading_title: str = Field(description="Original header text found in document")
    content: str = Field(description="Raw text content of the section")
    start_line: int = Field(description="1-indexed starting line number of the section block")
    end_line: int = Field(description="1-indexed ending line number of the section block")


class RawExtractedText(BaseModel):
    """Container for lower-level PDF text extraction output before sectioning."""
    raw_text: str = Field(description="Full concatenated text extracted from PDF")
    page_count: int = Field(description="Total page count of PDF document")
    character_count: int = Field(description="Total character count of extracted text")
    extraction_method: str = Field(description="Engine used for extraction (e.g. pdfplumber, pypdf)")
    pages_text: List[str] = Field(default_factory=list, description="Per-page raw text list")


class ParsingDiagnostics(BaseModel):
    """Diagnostic flags and performance telemetry for evaluating extraction reliability."""
    parser_version: str = Field(default="0.1.0-baseline")
    extraction_time_ms: float = Field(description="Total processing time in milliseconds")
    total_pages: int = Field(description="Total pages processed")
    total_characters: int = Field(description="Total characters extracted")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during parsing")
    missing_critical_sections: List[SectionType] = Field(
        default_factory=list, description="Standard sections not detected in resume"
    )
    confidence_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Heuristic parsing confidence score"
    )


class ExtractedContactInfo(BaseModel):
    """Basic candidate contact information extracted deterministically if present."""
    email: Optional[str] = Field(default=None, description="Extracted email address")
    phone: Optional[str] = Field(default=None, description="Extracted phone number")
    links: List[str] = Field(default_factory=list, description="Extracted GitHub/LinkedIn/Portfolio URLs")


class NormalizedResumeDocument(BaseModel):
    """Canonical representation of a parsed resume passed to downstream NLP/matching engines."""
    document_id: str = Field(description="Unique document UUID or hash")
    source_filename: str = Field(description="Original filename of input resume")
    raw_text: str = Field(description="Complete raw unsectioned text")
    contact_info: ExtractedContactInfo = Field(default_factory=ExtractedContactInfo)
    sections: List[DetectedSection] = Field(default_factory=list)
    diagnostics: ParsingDiagnostics
