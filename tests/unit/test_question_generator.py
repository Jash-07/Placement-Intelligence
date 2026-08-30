"""
Unit and API integration tests for Role-Specific Interview Question Generator (Phase 1 Increment B)
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from pii_001.api.app import app
from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.skill_extractor.skill_extractor import DeterministicSkillExtractor
from pii_001.jd_analyzer.jd_parser import JDParser
from pii_001.fit_scorer.fit_scorer import FitScoringEngine
from pii_001.question_generator.generator import InterviewQuestionGenerator
from pii_001.question_generator.schemas import QuestionCategory, GeneratedQuestionSet

client = TestClient(app)


def test_question_generator_gap_targeting(sample_minimal_resume_text: str, sample_backend_jd_text: str):
    """Verify technical gap questions generated for candidate missing required skills."""
    resume_parser = BaselineResumeParser()
    resume_doc = resume_parser.parse_raw_text(sample_minimal_resume_text)

    skill_extractor = DeterministicSkillExtractor()
    candidate_profile = skill_extractor.extract_skills(resume_doc)

    jd_parser = JDParser()
    jd_doc = jd_parser.parse_jd_text(sample_backend_jd_text)

    fit_engine = FitScoringEngine()
    fit_report = fit_engine.calculate_fit(candidate_profile, jd_doc)

    generator = InterviewQuestionGenerator()
    q_set: GeneratedQuestionSet = generator.generate_questions(fit_report, max_questions=5)

    assert q_set.total_questions > 0
    assert q_set.generation_time_ms < 50.0

    gap_questions = [q for q in q_set.questions if q.category == QuestionCategory.TECHNICAL_GAP]
    assert len(gap_questions) > 0

    for q in gap_questions:
        assert q.target_skill_name is not None
        assert "Critical requirement gap:" in q.rationale_evidence
        assert len(q.key_evaluation_points) > 0
        assert len(q.expected_answer_hints) > 0


def test_question_generator_api_endpoint(sample_txt_file: Path, sample_backend_jd_text: str):
    """Verify POST /api/v1/generate-questions REST endpoint."""
    with open(sample_txt_file, "rb") as f:
        files = {"resume_file": ("sample_resume.txt", f, "text/plain")}
        data = {"jd_text": sample_backend_jd_text, "max_questions": "5"}

        response = client.post("/api/v1/generate-questions", files=files, data=data)

    assert response.status_code == 200
    q_set = response.json()
    assert q_set["total_questions"] > 0
    assert len(q_set["questions"]) > 0
    assert "questions_by_category" in q_set
