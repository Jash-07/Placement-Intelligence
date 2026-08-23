"""
Unit tests for Candidate-Role Fit Scoring Engine
"""

import pytest
from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.skill_extractor.skill_extractor import DeterministicSkillExtractor
from pii_001.jd_analyzer.jd_parser import JDParser
from pii_001.fit_scorer.fit_scorer import FitScoringEngine
from pii_001.fit_scorer.schemas import SkillMatchStatus, CandidateRoleFitReport


def test_end_to_end_fit_scoring_standard(sample_standard_resume_text: str, sample_backend_jd_text: str):
    """Verify end-to-end fit scoring combining SP-001 + SP-002 + SP-003."""
    # 1. Parse Resume (SP-001)
    resume_parser = BaselineResumeParser()
    resume_doc = resume_parser.parse_raw_text(sample_standard_resume_text, filename="alex_morgan.txt")

    # 2. Extract Candidate Skills (SP-002)
    skill_extractor = DeterministicSkillExtractor()
    candidate_profile = skill_extractor.extract_skills(resume_doc)

    # 3. Parse Job Description (SP-003)
    jd_parser = JDParser()
    jd_doc = jd_parser.parse_jd_text(sample_backend_jd_text, filename="senior_backend_jd.txt")

    # 4. Compute Fit Score
    fit_engine = FitScoringEngine()
    report: CandidateRoleFitReport = fit_engine.calculate_fit(candidate_profile, jd_doc)

    assert report.candidate_doc_id == resume_doc.document_id
    assert report.jd_id == jd_doc.jd_id
    assert report.role_title == jd_doc.role_title
    assert report.company_name == jd_doc.company_name

    # All required skills (Python, FastAPI, PostgreSQL, SQL, REST API, Microservices) are matched
    assert report.required_skills_score == 100.0
    assert len(report.missing_required_skills) == 0

    # Preferred skills (Docker, AWS, Redis, CI/CD matched; Kubernetes missing)
    assert report.preferred_skills_score > 0.0
    assert "Docker" in report.matched_preferred_skills
    assert "Redis" in report.matched_preferred_skills
    assert "Kubernetes" in report.missing_preferred_skills

    # Overall score should be weighted
    assert 70.0 <= report.overall_fit_score <= 100.0
    assert report.scoring_time_ms < 50.0
    assert "Candidate achieved an overall fit score of" in report.summary_explanation


def test_fit_scoring_missing_required_skills(sample_minimal_resume_text: str, sample_backend_jd_text: str):
    """Verify detection of critical missing required skills for minimal resume."""
    resume_parser = BaselineResumeParser()
    resume_doc = resume_parser.parse_raw_text(sample_minimal_resume_text)

    skill_extractor = DeterministicSkillExtractor()
    candidate_profile = skill_extractor.extract_skills(resume_doc)

    jd_parser = JDParser()
    jd_doc = jd_parser.parse_jd_text(sample_backend_jd_text)

    fit_engine = FitScoringEngine()
    report = fit_engine.calculate_fit(candidate_profile, jd_doc)

    assert report.required_skills_score == 0.0
    assert "Python" in report.missing_required_skills
    assert "FastAPI" in report.missing_required_skills
    assert "PostgreSQL" in report.missing_required_skills
    assert report.overall_fit_score < 30.0
    assert "Critical Skill Gaps (Required):" in report.summary_explanation


def test_dual_evidence_span_preservation(sample_standard_resume_text: str, sample_backend_jd_text: str):
    """Verify dual evidence span preservation (Resume span + JD span) for matched skills."""
    resume_parser = BaselineResumeParser()
    resume_doc = resume_parser.parse_raw_text(sample_standard_resume_text)

    skill_extractor = DeterministicSkillExtractor()
    candidate_profile = skill_extractor.extract_skills(resume_doc)

    jd_parser = JDParser()
    jd_doc = jd_parser.parse_jd_text(sample_backend_jd_text)

    fit_engine = FitScoringEngine()
    report = fit_engine.calculate_fit(candidate_profile, jd_doc)

    matched_details = [d for d in report.skill_details if d.status == SkillMatchStatus.MATCHED_REQUIRED]
    assert len(matched_details) > 0

    for detail in matched_details:
        assert detail.resume_evidence_span is not None
        assert detail.jd_evidence_span is not None
        assert len(detail.resume_evidence_span) > 3
        assert len(detail.jd_evidence_span) > 3
