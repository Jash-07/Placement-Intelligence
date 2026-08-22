"""
Baseline Resume Parser Pipeline for PII-001 (SP-001 Increment B)

Main entry point orchestrating text extraction, section boundary detection, OCR diagnostics, and telemetry.
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
from pii_001.resume_parser.text_cleaner import TextCleaner


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
        cleaned_text = TextCleaner.clean_text(raw_data.raw_text)

        sections, missing_critical = self.detector.detect_sections(cleaned_text)
        contact_info = self.detector.extract_contact_info(cleaned_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        requires_ocr = raw_data.page_count > 0 and len(cleaned_text.strip()) == 0
        if requires_ocr:
            extraction_warnings.append("Document appears to be a scanned image-only PDF; OCR engine recommended.")

        confidence = self._compute_confidence(
            len(cleaned_text), missing_critical, extraction_warnings, requires_ocr
        )

        diagnostics = ParsingDiagnostics(
            parser_version="0.2.0-baseline-sp001b",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=raw_data.page_count,
            total_characters=len(cleaned_text),
            requires_ocr=requires_ocr,
            warnings=extraction_warnings,
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=path.name,
            raw_text=cleaned_text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def parse_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> NormalizedResumeDocument:
        """Parse raw PDF bytes."""
        start_time = time.perf_counter()

        raw_data, extraction_warnings = self.extractor.extract_from_bytes(pdf_bytes, filename=filename)
        cleaned_text = TextCleaner.clean_text(raw_data.raw_text)

        sections, missing_critical = self.detector.detect_sections(cleaned_text)
        contact_info = self.detector.extract_contact_info(cleaned_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        requires_ocr = raw_data.page_count > 0 and len(cleaned_text.strip()) == 0
        if requires_ocr:
            extraction_warnings.append("Document appears to be a scanned image-only PDF; OCR engine recommended.")

        confidence = self._compute_confidence(
            len(cleaned_text), missing_critical, extraction_warnings, requires_ocr
        )

        diagnostics = ParsingDiagnostics(
            parser_version="0.2.0-baseline-sp001b",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=raw_data.page_count,
            total_characters=len(cleaned_text),
            requires_ocr=requires_ocr,
            warnings=extraction_warnings,
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=filename,
            raw_text=cleaned_text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def parse_raw_text(self, text: str, filename: str = "raw_resume.txt") -> NormalizedResumeDocument:
        """Parse plain string text directly."""
        start_time = time.perf_counter()

        cleaned_text = TextCleaner.clean_text(text)
        sections, missing_critical = self.detector.detect_sections(cleaned_text)
        contact_info = self.detector.extract_contact_info(cleaned_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        confidence = self._compute_confidence(len(cleaned_text), missing_critical, [], False)

        diagnostics = ParsingDiagnostics(
            parser_version="0.2.0-baseline-sp001b",
            extraction_time_ms=round(elapsed_ms, 2),
            total_pages=1,
            total_characters=len(cleaned_text),
            requires_ocr=False,
            warnings=[],
            missing_critical_sections=missing_critical,
            confidence_score=confidence,
        )

        return NormalizedResumeDocument(
            document_id=str(uuid.uuid4()),
            source_filename=filename,
            raw_text=cleaned_text,
            contact_info=contact_info,
            sections=sections,
            diagnostics=diagnostics,
        )

    def _compute_confidence(self, char_count: int, missing_critical: list, warnings: list, requires_ocr: bool) -> float:
        """Calculate deterministic heuristic confidence score."""
        score = 1.0
        if requires_ocr:
            return 0.0

        if char_count < 50:
            score -= 0.5
        elif char_count < 200:
            score -= 0.2

        score -= len(missing_critical) * 0.15

        if warnings:
            score -= 0.1 * min(len(warnings), 3)

        return max(0.0, min(1.0, round(score, 2)))
