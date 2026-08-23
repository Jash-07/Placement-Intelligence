"""
Job Description Parser Engine for PII-001 (SP-003)

Segments raw job postings, extracts role metadata, classifies skill requirements into Required vs Preferred,
and generates NormalizedJobDescription objects.
"""

import time
import uuid
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Set

from pii_001.resume_parser.text_cleaner import TextCleaner, BULLET_PATTERN
from pii_001.skill_extractor.taxonomy_manager import TaxonomyManager
from pii_001.jd_analyzer.schemas import (
    JDSectionType,
    ParsedJDSection,
    ExtractedJDSkill,
    NormalizedJobDescription,
    RequirementPriority,
)
from pii_001.jd_analyzer.requirement_classifier import RequirementClassifier

JD_SECTION_PATTERNS: Dict[JDSectionType, List[re.Pattern]] = {
    JDSectionType.ROLE_OVERVIEW: [
        re.compile(r"^(about the role|about the job|company overview|job summary|position summary|role overview|about us)$", re.I),
    ],
    JDSectionType.RESPONSIBILITIES: [
        re.compile(r"^(responsibilities|what you will do|what you\'ll do|key responsibilities|duties & responsibilities|job duties|your impact)$", re.I),
    ],
    JDSectionType.REQUIREMENTS_QUALIFICATIONS: [
        re.compile(r"^(requirements|qualifications|minimum qualifications|basic qualifications|what we are looking for|what you\'ll bring|skills & experience|who you are|required skills)$", re.I),
    ],
    JDSectionType.PREFERRED_QUALIFICATIONS: [
        re.compile(r"^(preferred qualifications|nice to have|nice to haves|bonus points|preferred skills|desirable skills|what will make you stand out)$", re.I),
    ],
    JDSectionType.BENEFITS: [
        re.compile(r"^(benefits|what we offer|perks|perks & benefits|compensation|why join us)$", re.I),
    ],
}


class JDParser:
    """
    Job Description Parser (SP-003).
    Segments JD text, extracts role metadata, and classifies skill requirements into Required vs Preferred.
    """

    def __init__(self, taxonomy_manager: Optional[TaxonomyManager] = None):
        self.taxonomy_manager = taxonomy_manager or TaxonomyManager()
        self.classifier = RequirementClassifier()

    def parse_jd_file(self, file_path: Union[str, Path]) -> NormalizedJobDescription:
        """Parse a job description file from disk."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Job Description file not found at: {file_path}")

        text = path.read_text(encoding="utf-8", errors="replace")
        return self.parse_jd_text(text, filename=path.name)

    def parse_jd_text(self, raw_text: str, filename: str = "job_description.txt") -> NormalizedJobDescription:
        """Parse raw job description text string."""
        start_time = time.perf_counter()

        cleaned_text = TextCleaner.clean_text(raw_text)
        sections = self._segment_sections(cleaned_text)
        role_title, company_name = self._extract_metadata(cleaned_text)

        all_extracted_skills: List[ExtractedJDSkill] = []
        required_skills: List[ExtractedJDSkill] = []
        preferred_skills: List[ExtractedJDSkill] = []

        seen_skills_by_priority: Set[Tuple[str, RequirementPriority]] = set()

        for section in sections:
            content = section.content

            for pattern, alias, entry in self.taxonomy_manager.pattern_map:
                match = pattern.search(content)
                if match:
                    # Extract evidence span (40 chars before and after match)
                    start_pos = max(0, match.start() - 40)
                    end_pos = min(len(content), match.end() + 40)
                    evidence_span = " ".join(content[start_pos:end_pos].split())

                    priority = self.classifier.classify_priority(section.section_type, evidence_span)

                    skill_key = (entry.skill_id, priority)
                    if skill_key in seen_skills_by_priority:
                        continue

                    seen_skills_by_priority.add(skill_key)

                    jd_skill = ExtractedJDSkill(
                        skill_id=entry.skill_id,
                        canonical_name=entry.canonical_name,
                        category=entry.category,
                        priority=priority,
                        matched_alias=match.group(0),
                        evidence_text_span=evidence_span,
                        section_type=section.section_type,
                    )

                    all_extracted_skills.append(jd_skill)
                    if priority == RequirementPriority.PREFERRED:
                        preferred_skills.append(jd_skill)
                    else:
                        required_skills.append(jd_skill)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return NormalizedJobDescription(
            jd_id=str(uuid.uuid4()),
            role_title=role_title,
            company_name=company_name,
            raw_text=cleaned_text,
            sections=sections,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            all_extracted_skills=all_extracted_skills,
            total_skills_required=len({s.skill_id for s in required_skills}),
            total_skills_preferred=len({s.skill_id for s in preferred_skills}),
            parsing_time_ms=round(elapsed_ms, 2),
        )

    def _segment_sections(self, raw_text: str) -> List[ParsedJDSection]:
        """Segment JD text into ParsedJDSection list based on header patterns."""
        if not raw_text or not raw_text.strip():
            return []

        lines = raw_text.splitlines()
        header_matches: List[Tuple[int, JDSectionType, str]] = []

        for idx, line in enumerate(lines):
            raw_line = line.strip()
            if BULLET_PATTERN.search(line) or "," in raw_line:
                continue

            clean_line = TextCleaner.normalize_header(line)
            if not clean_line or len(clean_line) > 50:
                continue

            matched_type = self._match_jd_section_header(clean_line)
            if matched_type:
                header_matches.append((idx + 1, matched_type, clean_line))

        sections: List[ParsedJDSection] = []

        if not header_matches:
            sections.append(
                ParsedJDSection(
                    section_type=JDSectionType.ROLE_OVERVIEW,
                    heading_title="Job Body",
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
                    sections.append(
                        ParsedJDSection(
                            section_type=JDSectionType.ROLE_OVERVIEW,
                            heading_title="Header / Role Overview",
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
                sections.append(
                    ParsedJDSection(
                        section_type=sec_type,
                        heading_title=title,
                        content=sec_content,
                        start_line=line_num,
                        end_line=end_line,
                    )
                )

        return sections

    def _extract_metadata(self, raw_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Heuristically extract job title and company from top lines of posting."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()][:5]
        role_title = None
        company_name = None

        title_keywords = re.compile(
            r"\b(engineer|developer|architect|analyst|data scientist|manager|specialist|lead|consultant)\b",
            re.I,
        )

        for line in lines:
            if not role_title and title_keywords.search(line):
                role_title = line
            elif not company_name and len(line) < 40 and not title_keywords.search(line):
                company_name = line

        return role_title, company_name

    def _match_jd_section_header(self, text: str) -> Optional[JDSectionType]:
        """Match text line against known JD section header patterns."""
        for sec_type, patterns in JD_SECTION_PATTERNS.items():
            for pat in patterns:
                if pat.search(text):
                    return sec_type
        return None
