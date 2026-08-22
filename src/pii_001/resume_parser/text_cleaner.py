"""
Text Normalizer & Cleaner for PII-001 Resume Parser (SP-001 Increment B)

Strips bullet glyphs, normalizes Unicode spaces, and cleans noise formatting.
"""

import re
from typing import List

# Common bullet glyphs found in real-world PDF resumes
BULLET_PATTERN = re.compile(r"^[\s\t]*[•▪►\*❖o\-–—–‐⁃\+][\s\t]*")
EXTRA_WHITESPACE_PATTERN = re.compile(r"[ \t]+")
ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff\u00a0]")


class TextCleaner:
    """Utility for cleaning raw resume text and stripping bullet artifacts."""

    @staticmethod
    def clean_line(line: str) -> str:
        """Clean a single line of text."""
        if not line:
            return ""

        # Remove zero-width & non-breaking space characters
        cleaned = ZERO_WIDTH_PATTERN.sub(" ", line)
        # Strip leading bullet glyphs
        cleaned = BULLET_PATTERN.sub("", cleaned)
        # Collapse multiple inline spaces
        cleaned = EXTRA_WHITESPACE_PATTERN.sub(" ", cleaned)

        return cleaned.strip()

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean entire raw document text line by line while preserving line breaks."""
        if not text:
            return ""

        lines = text.splitlines()
        cleaned_lines = [TextCleaner.clean_line(line) for line in lines]
        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def normalize_header(header_line: str) -> str:
        """Clean and normalize a candidate section header string."""
        cleaned = TextCleaner.clean_line(header_line)
        # Strip trailing punctuation, dashes, or colons
        cleaned = re.sub(r"[:\-_=]+$", "", cleaned).strip()
        return cleaned
