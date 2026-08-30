"""
Pydantic data contracts for PII-001 Role-Specific Interview Question Generator (Phase 1 Increment B)
"""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    TECHNICAL_GAP = "technical_gap"
    TECHNICAL_VERIFICATION = "technical_verification"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"


class QuestionDifficulty(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class GeneratedQuestion(BaseModel):
    """Represents a generated interview question with evaluation rubrics and rationale evidence."""
    question_id: str = Field(description="Unique question ID")
    question_text: str = Field(description="Interview prompt or technical question text")
    category: QuestionCategory = Field(description="Question focus category")
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MID, description="Difficulty target level")
    target_skill_id: Optional[str] = Field(default=None, description="Canonical skill ID targeted")
    target_skill_name: Optional[str] = Field(default=None, description="Canonical skill display name")
    rationale_evidence: str = Field(description="Why this question was generated (resume evidence or gap justification)")
    key_evaluation_points: List[str] = Field(default_factory=list, description="Actionable evaluation rubric points for interviewer")
    expected_answer_hints: List[str] = Field(default_factory=list, description="Core technical concepts required in candidate response")


class GeneratedQuestionSet(BaseModel):
    """Container for complete role-specific interview question set."""
    set_id: str = Field(description="Unique question set identifier")
    role_title: Optional[str] = Field(default=None, description="Target job role title")
    total_questions: int = Field(description="Total count of questions generated")
    questions: List[GeneratedQuestion] = Field(default_factory=list, description="List of generated questions")
    questions_by_category: Dict[str, int] = Field(default_factory=dict, description="Count of questions grouped by category")
    generation_time_ms: float = Field(description="Question set generation duration in ms")
