"""
Requirement Priority Classifier for PII-001 JD Analyzer (SP-003)

Classifies extracted skills into Required (Mandatory) vs Preferred (Nice-to-have) using section context and linguistic cues.
"""

import re
from pii_001.jd_analyzer.schemas import RequirementPriority, JDSectionType

PREFERRED_CONTEXT_CUES = re.compile(
    r"\b(preferred|nice to have|plus|bonus|optional|good to have|desirable|asset|ideal)\b",
    re.IGNORECASE,
)

REQUIRED_CONTEXT_CUES = re.compile(
    r"\b(required|must have|must possess|essential|minimum|mandatory|strong experience|proficient in|proficient with)\b",
    re.IGNORECASE,
)


class RequirementClassifier:
    """Classifies skill requirements into REQUIRED vs PREFERRED based on section and context cues."""

    def classify_priority(self, section_type: JDSectionType, context_span: str) -> RequirementPriority:
        """
        Determine requirement priority for a skill based on section origin and surrounding text context.
        """
        # Section level rules take primary precedence
        if section_type == JDSectionType.PREFERRED_QUALIFICATIONS:
            return RequirementPriority.PREFERRED

        # Check local sentence context cues
        if PREFERRED_CONTEXT_CUES.search(context_span):
            return RequirementPriority.PREFERRED

        if REQUIRED_CONTEXT_CUES.search(context_span):
            return RequirementPriority.REQUIRED

        if section_type == JDSectionType.REQUIREMENTS_QUALIFICATIONS:
            return RequirementPriority.REQUIRED

        if section_type == JDSectionType.RESPONSIBILITIES:
            return RequirementPriority.REQUIRED

        return RequirementPriority.UNSPECIFIED
