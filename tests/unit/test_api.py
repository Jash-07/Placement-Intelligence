"""
Unit and integration tests for FastAPI REST API endpoints (SP-005 Phase 1)
"""

import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from pii_001.api.app import app

client = TestClient(app)


def test_api_health_check():
    """Verify health check endpoints return HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    response_v1 = client.get("/api/v1/health")
    assert response_v1.status_code == 200
    assert response_v1.json()["status"] == "healthy"


def test_api_parse_resume_file(sample_txt_file: Path):
    """Verify parsing a uploaded resume file via REST API."""
    with open(sample_txt_file, "rb") as f:
        response = client.post(
            "/api/v1/parse-resume",
            files={"resume_file": ("sample_resume.txt", f, "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["source_filename"] == "sample_resume.txt"
    assert len(data["sections"]) > 0


def test_api_parse_jd_text(sample_backend_jd_text: str):
    """Verify parsing JD text via Form POST."""
    response = client.post(
        "/api/v1/parse-jd",
        data={"jd_text": sample_backend_jd_text},
    )

    assert response.status_code == 200
    data = response.json()
    assert "Senior Backend Engineer" in data["role_title"]
    assert data["total_skills_required"] >= 4


def test_api_analyze_end_to_end(
    sample_txt_file: Path,
    sample_backend_jd_text: str,
    sample_company_prep_text: str,
):
    """Verify end-to-end placement intelligence analysis via REST API."""
    with open(sample_txt_file, "rb") as f:
        files = [
            ("resume_file", ("sample_resume.txt", f, "text/plain")),
            ("company_docs", ("company_guide.txt", sample_company_prep_text.encode("utf-8"), "text/plain")),
        ]
        data = {
            "jd_text": sample_backend_jd_text,
            "query": "System Design questions",
            "top_k": "2",
        }

        response = client.post("/api/v1/analyze", files=files, data=data)

    assert response.status_code == 200
    report = response.json()
    assert report["fit_report"]["required_skills_score"] == 100.0
    assert len(report["interview_prep_contexts"]) == 2
    assert report["diagnostics"]["pipeline_version"] == "0.1.0-mvp"


def test_api_validation_empty_inputs():
    """Verify HTTP 400/422 validation errors when mandatory fields are omitted."""
    # Empty resume file
    files = {"resume_file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    data = {"jd_text": "Senior Backend Engineer"}

    response = client.post("/api/v1/analyze", files=files, data=data)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
