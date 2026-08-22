"""
Unit tests for Baseline Resume Parser (SP-001)
"""

import io
import pytest
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.resume_parser.section_detector import RuleBasedSectionDetector
from pii_001.resume_parser.pdf_extractor import PDFExtractorAdapter
from pii_001.resume_parser.schemas import SectionType, NormalizedResumeDocument


def generate_synthetic_pdf_bytes() -> bytes:
    """Generate in-memory PDF bytes with reportlab for integration testing."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "John Doe")
    c.drawString(100, 735, "Email: john.doe@example.com | Phone: +1-555-019-2831")
    c.drawString(100, 700, "WORK EXPERIENCE")
    c.drawString(100, 685, "Senior Developer at Tech Co (2021-Present)")
    c.drawString(100, 650, "EDUCATION")
    c.drawString(100, 635, "BS Computer Science, Tech University")
    c.drawString(100, 600, "SKILLS")
    c.drawString(100, 585, "Python, SQL, FastAPI, Docker")
    c.save()
    return buffer.getvalue()


def test_parse_raw_text_standard(sample_standard_resume_text: str):
    """Verify parsing of a standard well-structured resume."""
    parser = BaselineResumeParser()
    doc: NormalizedResumeDocument = parser.parse_raw_text(sample_standard_resume_text, filename="test_resume.txt")

    assert doc.source_filename == "test_resume.txt"
    assert doc.raw_text == sample_standard_resume_text
    assert doc.diagnostics.total_characters > 500

    # Verify Contact Info Extraction
    assert doc.contact_info.email == "alex.morgan@example.com"
    assert doc.contact_info.phone is not None
    assert any("github.com/alexmorgan" in link for link in doc.contact_info.links)

    # Verify Section Detection
    detected_types = {sec.section_type for sec in doc.sections}
    expected_types = {
        SectionType.SUMMARY,
        SectionType.WORK_EXPERIENCE,
        SectionType.EDUCATION,
        SectionType.SKILLS,
        SectionType.PROJECTS,
        SectionType.CERTIFICATIONS,
    }
    assert expected_types.issubset(detected_types)
    assert len(doc.diagnostics.missing_critical_sections) == 0
    assert doc.diagnostics.confidence_score >= 0.85


def test_parse_raw_text_minimal(sample_minimal_resume_text: str):
    """Verify detection of missing critical sections and confidence deduction."""
    parser = BaselineResumeParser()
    doc = parser.parse_raw_text(sample_minimal_resume_text, filename="minimal.txt")

    assert doc.contact_info.email == "jane.doe@example.com"
    assert SectionType.WORK_EXPERIENCE in doc.diagnostics.missing_critical_sections
    assert SectionType.EDUCATION in doc.diagnostics.missing_critical_sections
    assert SectionType.SKILLS in doc.diagnostics.missing_critical_sections
    assert doc.diagnostics.confidence_score < 0.8


def test_parse_file_txt(sample_txt_file: Path):
    """Verify file parsing via file path."""
    parser = BaselineResumeParser()
    doc = parser.parse_file(sample_txt_file)

    assert doc.source_filename == "sample_resume.txt"
    assert doc.diagnostics.extraction_time_ms >= 0.0
    assert len(doc.sections) > 0


def test_parse_pdf_bytes():
    """Verify parsing real PDF binary streams."""
    pdf_bytes = generate_synthetic_pdf_bytes()
    parser = BaselineResumeParser()
    doc = parser.parse_bytes(pdf_bytes, filename="john_doe_resume.pdf")

    assert doc.source_filename == "john_doe_resume.pdf"
    assert doc.diagnostics.total_pages == 1
    assert "John Doe" in doc.raw_text
    assert doc.contact_info.email == "john.doe@example.com"
    
    detected_types = {sec.section_type for sec in doc.sections}
    assert SectionType.WORK_EXPERIENCE in detected_types
    assert SectionType.EDUCATION in detected_types
    assert SectionType.SKILLS in detected_types


def test_empty_pdf_bytes_handling():
    """Verify handling of corrupt/empty PDF bytes."""
    parser = BaselineResumeParser()
    doc = parser.parse_bytes(b"", filename="corrupt.pdf")

    assert doc.raw_text == ""
    assert doc.diagnostics.total_characters == 0
    assert len(doc.diagnostics.warnings) > 0


def test_pdf_extractor_nonexistent_file():
    """Verify error raised when accessing missing file."""
    extractor = PDFExtractorAdapter()
    with pytest.raises(FileNotFoundError):
        extractor.extract_from_file("nonexistent_resume.pdf")


def test_rule_based_section_detector_boundaries():
    """Verify line boundary calculations in section detector."""
    detector = RuleBasedSectionDetector()
    text = (
        "Name: John\n"
        "\n"
        "WORK EXPERIENCE\n"
        "Dev at Company A\n"
        "\n"
        "EDUCATION\n"
        "BS in CS\n"
    )
    sections, missing = detector.detect_sections(text)

    assert len(sections) == 3
    assert sections[0].section_type == SectionType.CONTACT_INFO
    assert sections[1].section_type == SectionType.WORK_EXPERIENCE
    assert sections[1].start_line == 3
    assert sections[2].section_type == SectionType.EDUCATION
    assert sections[2].start_line == 6
