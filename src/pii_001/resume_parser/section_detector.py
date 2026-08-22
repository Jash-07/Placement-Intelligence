"""
Rule-Based Section Detector for PII-001 Baseline (SP-001 Increment B)

Performs deterministic line-by-line section boundary detection, expanded header taxonomy matching,
and contact info extraction.
"""

import re
from typing import List, Tuple, Dict, Optional
from pii_001.resume_parser.schemas import (
    SectionType,
    DetectedSection,
    ExtractedContactInfo,
)
from pii_001.resume_parser.text_cleaner import TextCleaner

# Standard regex mappings for standard and expanded resume sections
SECTION_PATTERNS: Dict[SectionType, List[re.Pattern]] = {
    SectionType.SUMMARY: [
        re.compile(r"^(summary|professional summary|executive summary|profile|profile summary|executive profile|about me|about|objective|career objective|career summary)\b", re.I),
    ],
    SectionType.WORK_EXPERIENCE: [
        re.compile(r"^(work experience|professional experience|employment history|experience|work history|career history|professional background|internships|relevant experience)\b", re.I),
    ],
    SectionType.EDUCATION: [
        re.compile(r"^(education|academic background|qualifications|academic history|scholastic achievements|education & credentials)\b", re.I),
    ],
    SectionType.SKILLS: [
        re.compile(r"^(skills|technical skills|technical proficiency|core competencies|key skills|skills & tools|skills & abilities|technologies|tools & technologies)\b", re.I),
    ],
    SectionType.PROJECTS: [
        re.compile(r"^(projects|key projects|academic projects|personal projects|featured projects|portfolio)\b", re.I),
    ],
    SectionType.CERTIFICATIONS: [
        re.compile(r"^(certifications|licenses & certifications|certifications & licenses|certificates|licenses|certifications & training)\b", re.I),
    ],
    SectionType.LANGUAGES: [
        re.compile(r"^(languages|language proficiency|languages spoken)\b", re.I),
    ],
    SectionType.AWARDS: [
        re.compile(r"^(awards|honors|honors & awards|achievements|key achievements|scholarships|awards & honors)\b", re.I),
    ],
    SectionType.PUBLICATIONS: [
        re.compile(r"^(publications|research papers|papers|published works)\b", re.I),
    ],
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")
URL_REGEX = re.compile(r"https?://[^\s]+|github\.com/[^\s]+|linkedin\.com/in/[^\s]+")


class RuleBasedSectionDetector:
    """Detects section boundaries and candidate contact info from raw resume text."""

    def detect_sections(self, raw_text: str) -> Tuple[List[DetectedSection], List[SectionType]]:
        """
        Segment raw text into a list of DetectedSection objects using expanded section patterns.
        """
        if not raw_text or not raw_text.strip():
            missing = [SectionType.WORK_EXPERIENCE, SectionType.EDUCATION, SectionType.SKILLS]
            return [], missing

        lines = raw_text.splitlines()
        header_matches: List[Tuple[int, SectionType, str]] = []

        for idx, line in enumerate(lines):
            clean_line = TextCleaner.normalize_header(line)
            if not clean_line or len(clean_line) > 60:
                continue

            matched_type = self._match_section_header(clean_line)
            if matched_type:
                header_matches.append((idx + 1, matched_type, clean_line))

        detected_sections: List[DetectedSection] = []

        if not header_matches:
            detected_sections.append(
                DetectedSection(
                    section_type=SectionType.UNKNOWN,
                    heading_title="Document Body",
                    content=TextCleaner.clean_text(raw_text),
                    start_line=1,
                    end_line=len(lines),
                )
            )
        else:
            first_line_num = header_matches[0][0]
            if first_line_num > 1:
                pre_header_content = "\n".join(lines[: first_line_num - 1]).strip()
                if pre_header_content:
                    detected_sections.append(
                        DetectedSection(
                            section_type=SectionType.CONTACT_INFO,
                            heading_title="Header / Contact Details",
                            content=TextCleaner.clean_text(pre_header_content),
                            start_line=1,
                            end_line=first_line_num - 1,
                        )
                    )

            for i, (line_num, sec_type, title) in enumerate(header_matches):
                if i + 1 < len(header_matches):
                    next_line_num = header_matches[i + 1][0]
                    sec_lines = lines[line_num : next_line_num - 1]
                    end_line = next_line_num - 1
                else:
                    sec_lines = lines[line_num:]
                    end_line = len(lines)

                sec_content = TextCleaner.clean_text("\n".join(sec_lines))
                detected_sections.append(
                    DetectedSection(
                        section_type=sec_type,
                        heading_title=title,
                        content=sec_content,
                        start_line=line_num,
                        end_line=end_line,
                    )
                )

        found_types = {sec.section_type for sec in detected_sections}
        critical_sections = [SectionType.WORK_EXPERIENCE, SectionType.EDUCATION, SectionType.SKILLS]
        missing_critical = [s for s in critical_sections if s not in found_types]

        return detected_sections, missing_critical

    def extract_contact_info(self, raw_text: str) -> ExtractedContactInfo:
        """Deterministically extract email, phone, and professional links."""
        emails = EMAIL_REGEX.findall(raw_text)
        phones = PHONE_REGEX.findall(raw_text)
        urls = URL_REGEX.findall(raw_text)

        phone_str = None
        if phones:
            p = phones[0]
            phone_str = "".join(p) if isinstance(p, tuple) else str(p)

        return ExtractedContactInfo(
            email=emails[0] if emails else None,
            phone=phone_str if phone_str else None,
            links=list(set(urls)),
        )

    def _match_section_header(self, text: str) -> Optional[SectionType]:
        """Match a text line against expanded section patterns."""
        for sec_type, patterns in SECTION_PATTERNS.items():
            for pat in patterns:
                if pat.search(text):
                    return sec_type
        return None
