"""
Taxonomy Manager for PII-001 Skill Extraction (SP-002)

Loads, validates, and indexes canonical skills and their alias variations.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from pii_001.skill_extractor.schemas import SkillTaxonomyEntry, SkillCategory

DEFAULT_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"


class TaxonomyManager:
    """Manages skill taxonomy entries, indexing, and compiled regex patterns."""

    def __init__(self, taxonomy_path: Optional[Path] = None):
        self.taxonomy_path = taxonomy_path or DEFAULT_TAXONOMY_PATH
        self.entries: List[SkillTaxonomyEntry] = []
        self.alias_map: Dict[str, SkillTaxonomyEntry] = {}
        self.pattern_map: List[Tuple[re.Pattern, str, SkillTaxonomyEntry]] = []
        self.load_taxonomy()

    def load_taxonomy(self) -> None:
        """Load taxonomy entries from JSON and build regex index."""
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Skill taxonomy file not found at: {self.taxonomy_path}")

        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.entries = [SkillTaxonomyEntry(**item) for item in data]
        self._build_index()

    def _build_index(self) -> None:
        """Build alias map and compiled regex patterns with boundary protection."""
        self.alias_map.clear()
        self.pattern_map.clear()

        # Sort aliases by length descending so multi-word aliases match before single tokens
        alias_tuples: List[Tuple[str, SkillTaxonomyEntry]] = []
        for entry in self.entries:
            for alias in entry.aliases:
                clean_alias = alias.strip().lower()
                self.alias_map[clean_alias] = entry
                alias_tuples.append((alias, entry))

        alias_tuples.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, entry in alias_tuples:
            escaped = re.escape(alias)
            # Use word boundaries (\b) unless alias ends/starts with special chars like +, #, .
            prefix = r"(?<!\w)"
            suffix = r"(?!\w)"

            if alias.endswith("+") or alias.endswith("#") or alias.endswith(".js"):
                suffix = r"(?=\s|$|[,\.\)])"

            pattern = re.compile(f"{prefix}{escaped}{suffix}", re.IGNORECASE)
            self.pattern_map.append((pattern, alias, entry))

    def get_skill_by_id(self, skill_id: str) -> Optional[SkillTaxonomyEntry]:
        """Lookup taxonomy entry by unique skill ID."""
        for entry in self.entries:
            if entry.skill_id == skill_id:
                return entry
        return None
