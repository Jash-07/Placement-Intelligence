"""
Unit and End-to-End Integration Tests for Placement Intelligence Pipeline (MVP)
"""

import sys
import pytest
from pathlib import Path
from pii_001.pipeline import PlacementIntelligencePipeline
from pii_001.report_schemas import SkillGapReport
from pii_001.cli import main as cli_main


def test_pipeline_end_to_end_analysis(
    sample_txt_file: Path,
    sample_backend_jd_text: str,
    sample_company_prep_text: str,
    tmp_path: Path,
):
    """Verify complete end-to-end execution of PlacementIntelligencePipeline."""
    # Write company prep text to temp file
    company_doc_path = tmp_path / "company_guide.txt"
    company_doc_path.write_text(sample_company_prep_text, encoding="utf-8")

    pipeline = PlacementIntelligencePipeline()
    report: SkillGapReport = pipeline.analyze(
        resume_path=sample_txt_file,
        jd_text=sample_backend_jd_text,
        company_docs=[company_doc_path],
        top_k=2,
    )

    # 1. Verify Report Structure
    assert report.report_id is not None
    assert report.diagnostics.pipeline_version == "0.1.0-mvp"
    assert report.diagnostics.total_pipeline_time_ms > 0.0

    # 2. Verify Stages Completed
    expected_stages = [
        "resume_parsing",
        "skill_extraction",
        "jd_analysis",
        "fit_scoring",
        "rag_retrieval",
    ]
    assert expected_stages == report.diagnostics.stages_completed

    # 3. Verify Sub-component outputs
    assert report.resume_document.source_filename == "sample_resume.txt"
    assert report.candidate_skills.total_skills_found >= 5
    assert report.job_description.total_skills_required >= 4
    assert report.fit_report.required_skills_score == 100.0
    assert len(report.interview_prep_contexts) == 2
    assert "[Source: company_guide.txt #" in report.interview_prep_contexts[0].citation_tag


def test_pipeline_text_only_analysis(
    sample_standard_resume_text: str,
    sample_backend_jd_text: str,
):
    """Verify pipeline execution with raw string text inputs."""
    pipeline = PlacementIntelligencePipeline()
    report = pipeline.analyze(
        resume_text=sample_standard_resume_text,
        jd_text=sample_backend_jd_text,
    )

    assert report.fit_report.overall_fit_score >= 70.0
    assert report.diagnostics.rag_retrieval_time_ms == 0.0
    assert len(report.interview_prep_contexts) == 0


def test_pipeline_input_validation():
    """Verify value errors when mandatory inputs are omitted."""
    pipeline = PlacementIntelligencePipeline()

    with pytest.raises(ValueError, match="Either resume_path or resume_text must be provided."):
        pipeline.analyze(jd_text="Backend Engineer JD")

    with pytest.raises(ValueError, match="Either jd_text or jd_path must be provided."):
        pipeline.analyze(resume_text="John Doe Resume")


def test_cli_invocation(sample_txt_file: Path, sample_backend_jd_text: str, tmp_path: Path, capsys):
    """Verify CLI entry point invocation."""
    jd_file = tmp_path / "sample_jd.txt"
    jd_file.write_text(sample_backend_jd_text, encoding="utf-8")

    # Mock sys.argv
    sys.argv = ["pii-001", "--resume", str(sample_txt_file), "--jd", str(jd_file), "--pretty"]

    cli_main()

    captured = capsys.readouterr()
    assert captured.out != ""
    assert '"report_id":' in captured.out
    assert '"overall_fit_score":' in captured.out
