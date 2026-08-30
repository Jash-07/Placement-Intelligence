"""
FastAPI REST API routes for PII-001
"""

import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from pii_001.pipeline import PlacementIntelligencePipeline
from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.resume_parser.schemas import NormalizedResumeDocument
from pii_001.jd_analyzer.jd_parser import JDParser
from pii_001.jd_analyzer.schemas import NormalizedJobDescription
from pii_001.report_schemas import SkillGapReport
from pii_001.question_generator.generator import InterviewQuestionGenerator
from pii_001.question_generator.schemas import GeneratedQuestionSet

router = APIRouter(prefix="/api/v1", tags=["Placement Intelligence"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """System health check endpoint."""
    return {"status": "healthy", "service": "pii-001-api", "version": "0.1.0"}


@router.post("/parse-resume", response_model=NormalizedResumeDocument, status_code=status.HTTP_200_OK)
async def parse_resume(resume_file: UploadFile = File(...)):
    """
    Parse a resume PDF or text file into a NormalizedResumeDocument.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    contents = await resume_file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    parser = BaselineResumeParser()
    try:
        return parser.parse_bytes(contents, filename=resume_file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


@router.post("/parse-jd", response_model=NormalizedJobDescription, status_code=status.HTTP_200_OK)
def parse_jd(jd_text: str = Form(...)):
    """
    Parse raw Job Description text into a NormalizedJobDescription.
    """
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")

    parser = JDParser()
    return parser.parse_jd_text(jd_text)


@router.post("/analyze", response_model=SkillGapReport, status_code=status.HTTP_200_OK)
async def analyze_placement(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
    company_docs: List[UploadFile] = File(default=[]),
    query: Optional[str] = Form(default=None),
    top_k: int = Form(default=3),
):
    """
    End-to-end placement intelligence analysis: Ingest resume + JD + company docs -> return SkillGapReport.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume file must have a valid filename.")

    resume_bytes = await resume_file.read()
    if not resume_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")

    # Write uploaded files to temp directory for pipeline processing
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        resume_path = tmp_path / resume_file.filename
        resume_path.write_bytes(resume_bytes)

        temp_doc_paths: List[Path] = []
        for doc in company_docs:
            if doc.filename and doc.filename.strip():
                doc_bytes = await doc.read()
                if doc_bytes:
                    doc_path = tmp_path / doc.filename
                    doc_path.write_bytes(doc_bytes)
                    temp_doc_paths.append(doc_path)

        pipeline = PlacementIntelligencePipeline()
        report = pipeline.analyze(
            resume_path=resume_path,
            jd_text=jd_text,
            company_docs=temp_doc_paths if temp_doc_paths else None,
            interview_query=query,
            top_k=top_k,
        )
        return report


@router.post("/generate-questions", response_model=GeneratedQuestionSet, status_code=status.HTTP_200_OK)
async def generate_interview_questions(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
    max_questions: int = Form(default=6),
):
    """
    Generate role-specific technical and behavioral interview questions targeting candidate skill gaps and evidence.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume file must have a valid filename.")

    resume_bytes = await resume_file.read()
    if not resume_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        resume_path = tmp_path / resume_file.filename
        resume_path.write_bytes(resume_bytes)

        pipeline = PlacementIntelligencePipeline()
        report = pipeline.analyze(resume_path=resume_path, jd_text=jd_text)

        generator = InterviewQuestionGenerator()
        question_set = generator.generate_questions(report.fit_report, max_questions=max_questions)
        return question_set
