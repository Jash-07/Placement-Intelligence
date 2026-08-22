"""
Deterministic Skill Extractor Engine for PII-001 (SP-002)

Extracts candidate skills from NormalizedResumeDocument sections, grounds matches in evidence text spans,
and categorizes them against the canonical taxonomy.
"""

import time
from typing import List, Dict, Set, Optional
from pii_001.resume_parser.schemas import NormalizedResumeDocument, SectionType
from pii_001.skill_extractor.schemas import (
    ExtractedSkillMatch,
    CandidateSkillProfile,
    SkillCategory,
)
from pii_001.skill_extractor.taxonomy_manager import TaxonomyManager


class DeterministicSkillExtractor:
    """
    Skill Extractor Engine (SP-002).
    Extracts skills deterministically from parsed resume sections without LLM dependencies.
    """

    def __init__(self, taxonomy_manager: Optional[TaxonomyManager] = None):
        self.taxonomy_manager = taxonomy_manager or TaxonomyManager()

    def extract_skills(self, document: NormalizedResumeDocument) -> CandidateSkillProfile:
        """
        Extract skills from a NormalizedResumeDocument and produce a CandidateSkillProfile.
        """
        start_time = time.perf_counter()
        extracted_matches: List[ExtractedSkillMatch] = []
        seen_skills_by_section: Set[str] = set()
        seen_canonical_skills: Set[str] = set()

        skills_by_category: Dict[str, List[str]] = {cat.value: [] for cat in SkillCategory}

        # Weight section confidence (SKILLS/PROJECTS/WORK_EXPERIENCE have high confidence 1.0, SUMMARY 0.9, UNKNOWN 0.8)
        section_weights = {
            SectionType.SKILLS: 1.0,
            SectionType.WORK_EXPERIENCE: 1.0,
            SectionType.PROJECTS: 1.0,
            SectionType.CERTIFICATIONS: 0.95,
            SectionType.SUMMARY: 0.9,
            SectionType.EDUCATION: 0.9,
            SectionType.UNKNOWN: 0.8,
            SectionType.CONTACT_INFO: 0.5,
        }

        for section in document.sections:
            sec_weight = section_weights.get(section.section_type, 0.8)
            content = section.content

            for pattern, alias, entry in self.taxonomy_manager.pattern_map:
                section_skill_key = f"{section.section_type}:{entry.skill_id}"
                if section_skill_key in seen_skills_by_section:
                    continue

                match = pattern.search(content)
                if match:
                    seen_skills_by_section.add(section_skill_key)

                    # Extract evidence text span (surrounding 40 chars before and after match)
                    start_pos = max(0, match.start() - 40)
                    end_pos = min(len(content), match.end() + 40)
                    evidence_span = content[start_pos:end_pos].strip()

                    # Clean snippet whitespace
                    evidence_span = " ".join(evidence_span.split())

                    extracted_matches.append(
                        ExtractedSkillMatch(
                            skill_id=entry.skill_id,
                            canonical_name=entry.canonical_name,
                            category=entry.category,
                            matched_alias=match.group(0),
                            section_type=section.section_type,
                            evidence_text_span=evidence_span,
                            confidence_score=sec_weight,
                        )
                    )

                    if entry.canonical_name not in skills_by_category[entry.category.value]:
                        skills_by_category[entry.category.value].append(entry.canonical_name)
                    seen_canonical_skills.add(entry.skill_id)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return CandidateSkillProfile(
            document_id=document.document_id,
            total_skills_found=len(seen_canonical_skills),
            extracted_skills=extracted_matches,
            skills_by_category=skills_by_category,
            extraction_time_ms=round(elapsed_ms, 2),
        )
