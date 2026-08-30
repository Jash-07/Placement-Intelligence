"""
PII-001: AI-Powered Placement Intelligence & Interview Platform
"""

from pii_001.pipeline import PlacementIntelligencePipeline
from pii_001.report_schemas import SkillGapReport, PipelineDiagnostics

__version__ = "0.1.0"

__all__ = [
    "PlacementIntelligencePipeline",
    "SkillGapReport",
    "PipelineDiagnostics",
]
