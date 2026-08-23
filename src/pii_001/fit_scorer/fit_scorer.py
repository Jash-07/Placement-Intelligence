"""
Candidate-Role Fit Scoring Engine for PII-001

Computes transparent weighted fit scores, identifies skill gaps, and grounds matches in dual evidence spans.
"""

import time
import uuid
from typing import Dict, List, Set, Optional

from pii_001.skill_extractor.schemas import CandidateSkillProfile, ExtractedSkillMatch
from pii_001.jd_analyzer.schemas import NormalizedJobDescription, ExtractedJDSkill, RequirementPriority
from pii_001.fit_scorer.schemas import (
    SkillMatchStatus,
    SkillEvidenceDetail,
    CandidateRoleFitReport,
)


class FitScoringEngine:
    """
    Deterministic Candidate-Role Fit Scoring Engine.
    Calculates weighted fit scores and categorizes skill gaps with dual evidence grounding.
    """

    def calculate_fit(
        self,
        candidate_profile: CandidateSkillProfile,
        job_description: NormalizedJobDescription,
        required_weight: float = 0.70,
        preferred_weight: float = 0.30,
    ) -> CandidateRoleFitReport:
        """
        Compare CandidateSkillProfile against NormalizedJobDescription to generate CandidateRoleFitReport.
        """
        start_time = time.perf_counter()

        # Map candidate skills by skill_id
        candidate_skill_map: Dict[str, ExtractedSkillMatch] = {
            s.skill_id: s for s in candidate_profile.extracted_skills
        }

        matched_required: List[str] = []
        missing_required: List[str] = []
        matched_preferred: List[str] = []
        missing_preferred: List[str] = []

        skill_details: List[SkillEvidenceDetail] = []
        processed_jd_skill_ids: Set[str] = set()

        # 1. Process Required Job Skills
        for jd_skill in job_description.required_skills:
            if jd_skill.skill_id in processed_jd_skill_ids:
                continue
            processed_jd_skill_ids.add(jd_skill.skill_id)

            if jd_skill.skill_id in candidate_skill_map:
                cand_match = candidate_skill_map[jd_skill.skill_id]
                matched_required.append(jd_skill.canonical_name)
                skill_details.append(
                    SkillEvidenceDetail(
                        skill_id=jd_skill.skill_id,
                        canonical_name=jd_skill.canonical_name,
                        category=jd_skill.category,
                        status=SkillMatchStatus.MATCHED_REQUIRED,
                        resume_evidence_span=cand_match.evidence_text_span,
                        jd_evidence_span=jd_skill.evidence_text_span,
                    )
                )
            else:
                missing_required.append(jd_skill.canonical_name)
                skill_details.append(
                    SkillEvidenceDetail(
                        skill_id=jd_skill.skill_id,
                        canonical_name=jd_skill.canonical_name,
                        category=jd_skill.category,
                        status=SkillMatchStatus.MISSING_REQUIRED,
                        resume_evidence_span=None,
                        jd_evidence_span=jd_skill.evidence_text_span,
                    )
                )

        # 2. Process Preferred Job Skills
        for jd_skill in job_description.preferred_skills:
            if jd_skill.skill_id in processed_jd_skill_ids:
                continue
            processed_jd_skill_ids.add(jd_skill.skill_id)

            if jd_skill.skill_id in candidate_skill_map:
                cand_match = candidate_skill_map[jd_skill.skill_id]
                matched_preferred.append(jd_skill.canonical_name)
                skill_details.append(
                    SkillEvidenceDetail(
                        skill_id=jd_skill.skill_id,
                        canonical_name=jd_skill.canonical_name,
                        category=jd_skill.category,
                        status=SkillMatchStatus.MATCHED_PREFERRED,
                        resume_evidence_span=cand_match.evidence_text_span,
                        jd_evidence_span=jd_skill.evidence_text_span,
                    )
                )
            else:
                missing_preferred.append(jd_skill.canonical_name)
                skill_details.append(
                    SkillEvidenceDetail(
                        skill_id=jd_skill.skill_id,
                        canonical_name=jd_skill.canonical_name,
                        category=jd_skill.category,
                        status=SkillMatchStatus.MISSING_PREFERRED,
                        resume_evidence_span=None,
                        jd_evidence_span=jd_skill.evidence_text_span,
                    )
                )

        # 3. Calculate Scores
        total_req_count = len(matched_required) + len(missing_required)
        total_pref_count = len(matched_preferred) + len(missing_preferred)

        req_score = (len(matched_required) / total_req_count * 100.0) if total_req_count > 0 else 100.0
        pref_score = (len(matched_preferred) / total_pref_count * 100.0) if total_pref_count > 0 else 100.0

        if total_req_count == 0 and total_pref_count == 0:
            overall_score = 100.0
        elif total_pref_count == 0:
            overall_score = req_score
        else:
            overall_score = (required_weight * req_score) + (preferred_weight * pref_score)

        overall_score = round(overall_score, 1)
        req_score = round(req_score, 1)
        pref_score = round(pref_score, 1)

        # 4. Generate Auditable Summary Explanation
        explanation = self._build_explanation(
            overall_score,
            req_score,
            pref_score,
            len(matched_required),
            total_req_count,
            len(matched_preferred),
            total_pref_count,
            missing_required,
            missing_preferred,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return CandidateRoleFitReport(
            report_id=str(uuid.uuid4()),
            candidate_doc_id=candidate_profile.document_id,
            jd_id=job_description.jd_id,
            role_title=job_description.role_title,
            company_name=job_description.company_name,
            overall_fit_score=overall_score,
            required_skills_score=req_score,
            preferred_skills_score=pref_score,
            matched_required_skills=matched_required,
            matched_preferred_skills=matched_preferred,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            skill_details=skill_details,
            summary_explanation=explanation,
            scoring_time_ms=round(elapsed_ms, 2),
        )

    def _build_explanation(
        self,
        overall: float,
        req_score: float,
        pref_score: float,
        matched_req: int,
        total_req: int,
        matched_pref: int,
        total_pref: int,
        missing_req: List[str],
        missing_pref: List[str],
    ) -> str:
        """Construct a clear, evidence-based text summary explanation."""
        parts = [
            f"Candidate achieved an overall fit score of {overall:.1f}%.",
            f"Required Skills Match: {matched_req}/{total_req} ({req_score:.1f}%).",
        ]
        if total_pref > 0:
            parts.append(f"Preferred Skills Match: {matched_pref}/{total_pref} ({pref_score:.1f}%).")

        if missing_req:
            parts.append(f"Critical Skill Gaps (Required): {', '.join(missing_req)}.")
        else:
            parts.append("Critical Skill Gaps: None.")

        if missing_pref:
            parts.append(f"Optional Skill Gaps (Preferred): {', '.join(missing_pref)}.")

        return " ".join(parts)
