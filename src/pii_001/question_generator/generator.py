"""
Role-Specific Interview Question Generator Engine for PII-001 (Phase 1 Increment B)

Targets critical skill gaps, verified skills, and role seniority to generate grounded interview questions.
"""

import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Set

from pii_001.question_generator.schemas import (
    GeneratedQuestion,
    GeneratedQuestionSet,
    QuestionCategory,
    QuestionDifficulty,
)
from pii_001.fit_scorer.schemas import CandidateRoleFitReport

DEFAULT_QUESTION_BANK_PATH = Path(__file__).parent / "question_bank.json"


class InterviewQuestionGenerator:
    """
    Role-Specific Interview Question Generator.
    Generates tailored, evidence-backed technical & behavioral interview questions with evaluation rubrics.
    """

    def __init__(self, question_bank_path: Optional[Path] = None):
        self.question_bank_path = question_bank_path or DEFAULT_QUESTION_BANK_PATH
        self.question_bank: List[Dict] = []
        self.load_question_bank()

    def load_question_bank(self) -> None:
        """Load seed question bank entries from JSON."""
        if not self.question_bank_path.exists():
            raise FileNotFoundError(f"Question bank JSON not found at: {self.question_bank_path}")

        with open(self.question_bank_path, "r", encoding="utf-8") as f:
            self.question_bank = json.load(f)

    def generate_questions(
        self,
        fit_report: CandidateRoleFitReport,
        max_questions: int = 6,
    ) -> GeneratedQuestionSet:
        """
        Generate a targeted GeneratedQuestionSet from a CandidateRoleFitReport.
        """
        start_time = time.perf_counter()
        set_id = str(uuid.uuid4())

        generated_questions: List[GeneratedQuestion] = []
        seen_skill_ids: Set[str] = set()

        # 1. Target Missing Required Skills (Critical Gaps -> TECHNICAL_GAP)
        for skill_name in fit_report.missing_required_skills:
            skill_id = skill_name.lower().replace(" ", "_")
            if skill_id in seen_skill_ids:
                continue
            seen_skill_ids.add(skill_id)

            bank_match = self._find_question(skill_id, QuestionCategory.TECHNICAL_GAP)
            if bank_match:
                generated_questions.append(
                    GeneratedQuestion(
                        question_id=str(uuid.uuid4()),
                        question_text=bank_match["question_text"],
                        category=QuestionCategory.TECHNICAL_GAP,
                        difficulty=QuestionDifficulty(bank_match.get("difficulty", "mid")),
                        target_skill_id=skill_id,
                        target_skill_name=skill_name,
                        rationale_evidence=f"Critical requirement gap: Candidate lacks required skill '{skill_name}' on resume.",
                        key_evaluation_points=bank_match["key_evaluation_points"],
                        expected_answer_hints=bank_match["expected_answer_hints"],
                    )
                )
            else:
                # Dynamic fallback question template
                generated_questions.append(
                    GeneratedQuestion(
                        question_id=str(uuid.uuid4()),
                        question_text=f"Explain core principles of {skill_name} and how you would apply it to build scalable features in this role.",
                        category=QuestionCategory.TECHNICAL_GAP,
                        difficulty=QuestionDifficulty.MID,
                        target_skill_id=skill_id,
                        target_skill_name=skill_name,
                        rationale_evidence=f"Critical requirement gap: Candidate lacks required skill '{skill_name}'.",
                        key_evaluation_points=[f"Demonstrates understanding of {skill_name} fundamentals", "Explains practical implementation steps"],
                        expected_answer_hints=[skill_name, "Architecture", "Best Practices"],
                    )
                )

        # 2. Target Matched Required Skills (Technical Verification Deep-Dive)
        for skill_name in fit_report.matched_required_skills:
            if len(generated_questions) >= max_questions:
                break

            skill_id = skill_name.lower().replace(" ", "_")
            if skill_id in seen_skill_ids:
                continue
            seen_skill_ids.add(skill_id)

            bank_match = self._find_question(skill_id, QuestionCategory.TECHNICAL_VERIFICATION)
            if bank_match:
                # Find resume evidence for rationale
                resume_span = "Claimed on resume."
                for detail in fit_report.skill_details:
                    if detail.skill_id == skill_id and detail.resume_evidence_span:
                        resume_span = f"Resume evidence: '{detail.resume_evidence_span}'"
                        break

                generated_questions.append(
                    GeneratedQuestion(
                        question_id=str(uuid.uuid4()),
                        question_text=bank_match["question_text"],
                        category=QuestionCategory.TECHNICAL_VERIFICATION,
                        difficulty=QuestionDifficulty(bank_match.get("difficulty", "mid")),
                        target_skill_id=skill_id,
                        target_skill_name=skill_name,
                        rationale_evidence=f"Technical Verification: Candidate claims '{skill_name}'. {resume_span}",
                        key_evaluation_points=bank_match["key_evaluation_points"],
                        expected_answer_hints=bank_match["expected_answer_hints"],
                    )
                )

        # 3. Target System Design / Architecture Questions
        if len(generated_questions) < max_questions:
            design_match = self._find_question("system_design", QuestionCategory.SYSTEM_DESIGN)
            if design_match:
                generated_questions.append(
                    GeneratedQuestion(
                        question_id=str(uuid.uuid4()),
                        question_text=design_match["question_text"],
                        category=QuestionCategory.SYSTEM_DESIGN,
                        difficulty=QuestionDifficulty.SENIOR,
                        target_skill_id="system_design",
                        target_skill_name="System Design",
                        rationale_evidence=f"System Architecture requirement for {fit_report.role_title or 'Engineering Role'}.",
                        key_evaluation_points=design_match["key_evaluation_points"],
                        expected_answer_hints=design_match["expected_answer_hints"],
                    )
                )

        # 4. Behavioral / Situational Question
        if len(generated_questions) < max_questions:
            generated_questions.append(
                GeneratedQuestion(
                    question_id=str(uuid.uuid4()),
                    question_text="Describe a complex production bug or API performance bottleneck you encountered. How did you diagnose, resolve, and prevent it from recurring?",
                    category=QuestionCategory.BEHAVIORAL,
                    difficulty=QuestionDifficulty.MID,
                    target_skill_id=None,
                    target_skill_name=None,
                    rationale_evidence="Behavioral & Problem-Solving evaluation for production engineering readiness.",
                    key_evaluation_points=[
                        "Explains systematic debugging and root-cause analysis",
                        "Mentions monitoring tools, logs, and unit/integration testing",
                        "Demonstrates accountability and post-mortem reflection",
                    ],
                    expected_answer_hints=["Root Cause Analysis", "Logging & Metrics", "Testing", "Post-Mortem"],
                )
            )

        # Count by category
        by_cat: Dict[str, int] = {}
        for q in generated_questions:
            by_cat[q.category.value] = by_cat.get(q.category.value, 0) + 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return GeneratedQuestionSet(
            set_id=set_id,
            role_title=fit_report.role_title,
            total_questions=len(generated_questions),
            questions=generated_questions,
            questions_by_category=by_cat,
            generation_time_ms=round(elapsed_ms, 2),
        )

    def _find_question(self, skill_id: str, category: QuestionCategory) -> Optional[Dict]:
        """Find matching entry in question bank by skill ID or category."""
        for entry in self.question_bank:
            if entry["skill_id"] == skill_id and entry["category"] == category.value:
                return entry

        # Fallback search by skill_id only
        for entry in self.question_bank:
            if entry["skill_id"] == skill_id:
                return entry

        return None
