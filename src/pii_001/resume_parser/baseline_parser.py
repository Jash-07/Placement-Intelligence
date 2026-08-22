"""
Baseline Resume Parser Pipeline for PII-001 (SP-001)

Main entry point orchestrating text extraction, section boundary detection, and diagnostic scoring.
"""

import time
import uuid
from pathlib import Path
from typing import Union, Optional

from pii_001.resume_parser.schemas import (
    NormalizedResumeDocument,
    ParsingDiagnostics,
)
from pii_001.resume_parser.pdf_extractor import PDFExtractorAdapter
from pii_001.resume_parser.section_detector import RuleBasedSectionDetector


class BaselineResumeParser:
    """
    Baseline Resume Parser (SP-001).
    Transforms PDF or raw text resumes into NormalizedResumeDocument objects without LLM or vector DB dependencies.
    """

    def __init__(self):
        self.extractor = PDFExtractorAdapter()
        self.detector = RuleBasedSectionDetector()

    def parse_file(self, file_path: Union[str, Path]) -> NormalizedResumeDocument:
        """Parse a resume file on disk (PDF or plain text)."""
        path = Path(file_path)
        start_time = time.perf_counter()

        raw_data, extraction_warnings = self.extractor.extract_from_file(path)
        sections, missing_critical = self.detector.detect_sections(raw_data.raw_text)
        contact_info = self.detector.extract_contact_info(raw_data.raw_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Calculate heuristic confidence score
        confidence = self._compute_confidence(raw_data.character_count, missing_critical, extraction_warnings)

        diagnostics = ParsingDiagnostics(
            parser_version="0.1.0-baseline",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=raw_data.page_count,
            total_characters=raw_data.character_count,
            warnings=extraction_warnings,
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=path.name,
            raw_text=raw_data.raw_text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def parse_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> NormalizedResumeDocument:
        """Parse raw PDF bytes."""
        start_time = time.perf_counter()

        raw_data, extraction_warnings = self.extractor.extract_from_bytes(pdf_bytes, filename=filename)
        sections, missing_critical = self.detector.detect_sections(raw_data.raw_text)
        contact_info = self.detector.extract_contact_info(raw_data.raw_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        confidence = self._compute_confidence(raw_data.character_count, missing_critical, extraction_warnings)

        diagnostics = ParsingDiagnostics(
            parser_version="0.1.0-baseline",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=raw_data.page_count,
            total_characters=raw_data.character_count,
            warnings=extraction_warnings,
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=filename,
            raw_text=raw_data.raw_text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def parse_raw_text(self, text: str, filename: str = "raw_resume.txt") -> NormalizedResumeDocument:
        """Parse plain string text directly."""
        start_time = time.perf_counter()

        sections, missing_critical = self.detector.detect_sections(text)
        contact_info = self.detector.extract_contact_info(text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        confidence = self._compute_confidence(len(text), missing_critical, [])

        diagnostics = ParsingDiagnostics(
            parser_version="0.1.0-baseline",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=1,
            total_characters=len(text),
            warnings=[],
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=filename,
            raw_text=text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def _compute_confidence(self, char_count: int, missing_critical: list, warnings: list) -> float:
        """Calculate simple deterministic heuristic confidence score."""
        score = 1.0
        if char_count < 50:
            score -= 0.5
        elif char_count < 200:
            score -= 0.2

        # Deduct 0.15 for each missing critical section (work, education, skills)
        score -= len(missing_critical) * 0.15

        if warnings:
            score -= 0.1 * min(len(warnings), 3)

        return max(0.0, min(1.0, round(score, 2)))
