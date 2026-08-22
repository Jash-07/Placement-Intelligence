"""
Unit tests for Skill Extractor Engine (SP-002)
"""

import pytest
from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.skill_extractor.taxonomy_manager import TaxonomyManager
from pii_001.skill_extractor.skill_extractor import DeterministicSkillExtractor
from pii_001.skill_extractor.schemas import SkillCategory, CandidateSkillProfile


def test_taxonomy_manager_loading():
    """Verify taxonomy JSON loading and alias index compilation."""
    tm = TaxonomyManager()
    assert len(tm.entries) >= 30
    assert "python" in tm.alias_map
    assert "postgres" in tm.alias_map
    
    entry = tm.get_skill_by_id("postgresql")
    assert entry is not None
    assert entry.canonical_name == "PostgreSQL"
    assert entry.category == SkillCategory.DATABASES_STORAGE


def test_skill_extraction_standard_resume(sample_standard_resume_text: str):
    """Verify end-to-end skill extraction from a NormalizedResumeDocument."""
    parser = BaselineResumeParser()
    doc = parser.parse_raw_text(sample_standard_resume_text, filename="alex_morgan.txt")

    extractor = DeterministicSkillExtractor()
    profile: CandidateSkillProfile = extractor.extract_skills(doc)

    assert profile.document_id == doc.document_id
    assert profile.total_skills_found >= 7
    assert profile.extraction_time_ms < 50.0

    found_canonicals = {m.canonical_name for m in profile.extracted_skills}
    expected = {"Python", "FastAPI", "PostgreSQL", "Docker", "Git", "SQL"}
    assert expected.issubset(found_canonicals)


def test_skill_alias_mapping():
    """Verify extraction of aliases (py, postgres, k8s) mapping to canonical names."""
    parser = BaselineResumeParser()
    text = (
        "SKILLS\n"
        "- Tech: py, postgres, k8s, drf, tf, ts\n"
    )
    doc = parser.parse_raw_text(text)

    extractor = DeterministicSkillExtractor()
    profile = extractor.extract_skills(doc)

    found_canonicals = {m.canonical_name for m in profile.extracted_skills}
    assert "Python" in found_canonicals
    assert "PostgreSQL" in found_canonicals
    assert "Kubernetes" in found_canonicals
    assert "Django" in found_canonicals
    assert "TensorFlow" in found_canonicals
    assert "TypeScript" in found_canonicals


def test_evidence_text_span_grounding(sample_standard_resume_text: str):
    """Verify evidence text span is non-empty and anchors matched skill."""
    parser = BaselineResumeParser()
    doc = parser.parse_raw_text(sample_standard_resume_text)

    extractor = DeterministicSkillExtractor()
    profile = extractor.extract_skills(doc)

    for match in profile.extracted_skills:
        assert match.evidence_text_span != ""
        assert len(match.evidence_text_span) > 5
        assert match.confidence_score > 0.0


def test_skills_categorization(sample_standard_resume_text: str):
    """Verify skills are correctly grouped into categories."""
    parser = BaselineResumeParser()
    doc = parser.parse_raw_text(sample_standard_resume_text)

    extractor = DeterministicSkillExtractor()
    profile = extractor.extract_skills(doc)

    categories = profile.skills_by_category
    assert "Python" in categories[SkillCategory.PROGRAMMING_LANGUAGES.value]
    assert "FastAPI" in categories[SkillCategory.FRAMEWORKS_LIBRARIES.value]
    assert "PostgreSQL" in categories[SkillCategory.DATABASES_STORAGE.value]
    assert "Docker" in categories[SkillCategory.CLOUD_DEVOPS.value]
