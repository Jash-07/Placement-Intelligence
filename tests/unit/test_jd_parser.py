"""
Unit tests for Job Description Parser Engine (SP-003)
"""

import pytest
from pii_001.jd_analyzer.jd_parser import JDParser
from pii_001.jd_analyzer.requirement_classifier import RequirementClassifier
from pii_001.jd_analyzer.schemas import (
    RequirementPriority,
    JDSectionType,
    NormalizedJobDescription,
)


def test_requirement_classifier_context_cues():
    """Verify sentence cue classification for Required vs Preferred requirements."""
    classifier = RequirementClassifier()

    assert classifier.classify_priority(
        JDSectionType.REQUIREMENTS_QUALIFICATIONS, "Experience with Docker is nice to have"
    ) == RequirementPriority.PREFERRED

    assert classifier.classify_priority(
        JDSectionType.REQUIREMENTS_QUALIFICATIONS, "Must have 3+ years experience with Python"
    ) == RequirementPriority.REQUIRED

    assert classifier.classify_priority(
        JDSectionType.PREFERRED_QUALIFICATIONS, "Knowledge of AWS"
    ) == RequirementPriority.PREFERRED


def test_jd_section_segmentation(sample_backend_jd_text: str):
    """Verify segmentation of raw JD into structured section blocks."""
    parser = JDParser()
    jd: NormalizedJobDescription = parser.parse_jd_text(sample_backend_jd_text)

    assert jd.role_title is not None
    assert "Senior Backend Engineer" in jd.role_title
    assert "TechCorp Inc." in jd.company_name

    detected_types = {sec.section_type for sec in jd.sections}
    expected = {
        JDSectionType.ROLE_OVERVIEW,
        JDSectionType.RESPONSIBILITIES,
        JDSectionType.REQUIREMENTS_QUALIFICATIONS,
        JDSectionType.PREFERRED_QUALIFICATIONS,
    }
    assert expected.issubset(detected_types)


def test_required_vs_preferred_classification(sample_backend_jd_text: str):
    """Verify accurate segregation of Required vs Preferred skill requirements."""
    parser = JDParser()
    jd = parser.parse_jd_text(sample_backend_jd_text)

    required_names = {s.canonical_name for s in jd.required_skills}
    preferred_names = {s.canonical_name for s in jd.preferred_skills}

    # Verify Required Skills
    assert "Python" in required_names
    assert "FastAPI" in required_names
    assert "PostgreSQL" in required_names
    assert "SQL" in required_names

    # Verify Preferred Skills
    assert "Docker" in preferred_names
    assert "Kubernetes" in preferred_names
    assert "AWS" in preferred_names
    assert "Redis" in preferred_names
    assert "CI/CD" in preferred_names

    assert jd.total_skills_required >= 4
    assert jd.total_skills_preferred >= 4
    assert jd.parsing_time_ms < 50.0


def test_empty_jd_text():
    """Verify graceful handling of empty JD input."""
    parser = JDParser()
    jd = parser.parse_jd_text("")

    assert jd.raw_text == ""
    assert len(jd.sections) == 0
    assert jd.total_skills_required == 0
    assert jd.total_skills_preferred == 0
