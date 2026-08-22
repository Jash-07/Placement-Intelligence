"""
PDF Extraction Adapter for PII-001 (SP-001 Baseline)

Provides deterministic text extraction from PDF files using pdfplumber with pypdf fallback.
"""

import io
from pathlib import Path
from typing import Union, Tuple, List
import pdfplumber
import pypdf

from pii_001.resume_parser.schemas import RawExtractedText


class PDFExtractorAdapter:
    """Adapter for extracting raw text from PDF files or byte streams with fallback handling."""

    def extract_from_file(self, file_path: Union[str, Path]) -> Tuple[RawExtractedText, List[str]]:
        """
        Extract text from a file path.
        
        Returns:
            Tuple of (RawExtractedText, list_of_warning_messages)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found at: {file_path}")

        if path.suffix.lower() == ".txt":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return RawExtractedText(
                raw_text=text,
                page_count=1,
                character_count=len(text),
                extraction_method="plaintext",
                pages_text=[text],
            ), []

        with open(path, "rb") as f:
            pdf_bytes = f.read()

        return self.extract_from_bytes(pdf_bytes, filename=path.name)

    def extract_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> Tuple[RawExtractedText, List[str]]:
        """
        Extract text from raw PDF bytes. Attempts pdfplumber first, falling back to pypdf.
        """
        warnings: List[str] = []

        if not pdf_bytes or len(pdf_bytes.strip()) == 0:
            warnings.append("Provided PDF byte buffer is empty.")
            return RawExtractedText(
                raw_text="",
                page_count=0,
                character_count=0,
                extraction_method="empty_input",
                pages_text=[],
            ), warnings

        # Attempt 1: pdfplumber
        try:
            pages_text = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    page_str = page.extract_text(layout=True) or page.extract_text() or ""
                    pages_text.append(page_str)

            full_text = "\n\n".join(pages_text).strip()
            if full_text:
                return RawExtractedText(
                    raw_text=full_text,
                    page_count=page_count,
                    character_count=len(full_text),
                    extraction_method="pdfplumber",
                    pages_text=pages_text,
                ), warnings
            else:
                warnings.append("pdfplumber extracted zero characters; attempting pypdf fallback.")
        except Exception as e:
            warnings.append(f"pdfplumber extraction failed ({type(e).__name__}: {str(e)}); attempting pypdf fallback.")

        # Attempt 2: pypdf fallback
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(reader.pages)
            pages_text = []
            for page in reader.pages:
                page_str = page.extract_text() or ""
                pages_text.append(page_str)

            full_text = "\n\n".join(pages_text).strip()
            if not full_text:
                warnings.append("pypdf extracted zero characters. PDF may contain scanned images or rasterized text.")

            return RawExtractedText(
                raw_text=full_text,
                page_count=page_count,
                character_count=len(full_text),
                extraction_method="pypdf",
                pages_text=pages_text,
            ), warnings
        except Exception as e:
            warnings.append(f"pypdf extraction failed ({type(e).__name__}: {str(e)}).")
            return RawExtractedText(
                raw_text="",
                page_count=0,
                character_count=0,
                extraction_method="failed",
                pages_text=[],
            ), warnings
