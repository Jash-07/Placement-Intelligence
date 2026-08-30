"""
Placement Intelligence Pipeline for PII-001 MVP

Orchestrates the full analysis chain: Resume → Skills → JD → Fit Score → RAG Prep.
"""

import time
import uuid
from pathlib import Path
from typing import List, Optional, Union

from pii_001.resume_parser.baseline_parser import BaselineResumeParser
from pii_001.skill_extractor.skill_extractor import DeterministicSkillExtractor
from pii_001.jd_analyzer.jd_parser import JDParser
from pii_001.fit_scorer.fit_scorer import FitScoringEngine
from pii_001.rag_retriever.document_chunker import DocumentChunker
from pii_001.rag_retriever.lexical_retriever import LexicalRetriever
from pii_001.rag_retriever.schemas import RetrievedContext
from pii_001.report_schemas import SkillGapReport, PipelineDiagnostics


class PlacementIntelligencePipeline:
    """
    MVP Pipeline orchestrating the full PII-001 analysis chain.

    Usage:
        pipeline = PlacementIntelligencePipeline()
        report = pipeline.analyze(
            resume_path="resume.pdf",
            jd_text="Senior Backend Engineer at TechCorp...",
            company_docs=["company_prep_guide.txt"],
        )
    """

    def __init__(self):
        self.resume_parser = BaselineResumeParser()
        self.skill_extractor = DeterministicSkillExtractor()
        self.jd_parser = JDParser()
        self.fit_engine = FitScoringEngine()
        self.chunker = DocumentChunker(chunk_size=300, overlap=50)
        self.retriever = LexicalRetriever()

    def analyze(
        self,
        resume_path: Optional[Union[str, Path]] = None,
        resume_text: Optional[str] = None,
        jd_text: Optional[str] = None,
        jd_path: Optional[Union[str, Path]] = None,
        company_docs: Optional[List[Union[str, Path]]] = None,
        interview_query: Optional[str] = None,
        top_k: int = 3,
    ) -> SkillGapReport:
        """
        Run the full placement intelligence analysis chain.

        Args:
            resume_path: Path to resume file (PDF or TXT).
            resume_text: Raw resume text (alternative to resume_path).
            jd_text: Raw job description text.
            jd_path: Path to job description file (alternative to jd_text).
            company_docs: Optional list of file paths to company/role prep documents for RAG.
            interview_query: Optional query for RAG interview prep retrieval.
            top_k: Number of RAG context passages to retrieve.

        Returns:
            SkillGapReport with all sub-component outputs.
        """
        pipeline_start = time.perf_counter()
        warnings: List[str] = []
        stages_completed: List[str] = []

        # ── Stage 1: Resume Parsing (SP-001) ──
        if resume_path:
            resume_doc = self.resume_parser.parse_file(resume_path)
        elif resume_text:
            resume_doc = self.resume_parser.parse_raw_text(resume_text)
        else:
            raise ValueError("Either resume_path or resume_text must be provided.")

        stages_completed.append("resume_parsing")
        resume_time = resume_doc.diagnostics.extraction_time_ms

        if resume_doc.diagnostics.requires_ocr:
            warnings.append("Resume appears to be a scanned image PDF; results may be incomplete.")

        # ── Stage 2: Skill Extraction (SP-002) ──
        candidate_skills = self.skill_extractor.extract_skills(resume_doc)
        stages_completed.append("skill_extraction")
        skill_time = candidate_skills.extraction_time_ms

        if candidate_skills.total_skills_found == 0:
            warnings.append("No skills were extracted from the resume. Fit scoring may be unreliable.")

        # ── Stage 3: JD Analysis (SP-003) ──
        if jd_text:
            jd_doc = self.jd_parser.parse_jd_text(jd_text)
        elif jd_path:
            jd_doc = self.jd_parser.parse_jd_file(jd_path)
        else:
            raise ValueError("Either jd_text or jd_path must be provided.")

        stages_completed.append("jd_analysis")
        jd_time = jd_doc.parsing_time_ms

        if jd_doc.total_skills_required == 0:
            warnings.append("No required skills detected in JD. Fit scoring may not be meaningful.")

        # ── Stage 4: Fit Scoring (SP-004) ──
        fit_report = self.fit_engine.calculate_fit(candidate_skills, jd_doc)
        stages_completed.append("fit_scoring")
        fit_time = fit_report.scoring_time_ms

        # ── Stage 5: RAG Retrieval (SP-005, optional) ──
        interview_contexts: List[RetrievedContext] = []
        rag_time = 0.0

        if company_docs:
            all_chunks = []
            for doc_path in company_docs:
                path = Path(doc_path)
                if path.exists():
                    doc_text = path.read_text(encoding="utf-8", errors="replace")
                    chunks = self.chunker.chunk_text(doc_text, source_title=path.name)
                    all_chunks.extend(chunks)
                else:
                    warnings.append(f"Company document not found: {doc_path}")

            if all_chunks:
                self.retriever.index_chunks(all_chunks)

                # Auto-generate interview query from JD role if not provided
                query = interview_query or self._build_default_query(jd_doc.role_title, fit_report.missing_required_skills)
                response = self.retriever.query(query, top_k=top_k)
                interview_contexts = response.retrieved_contexts
                rag_time = response.retrieval_time_ms

            stages_completed.append("rag_retrieval")

        # ── Assemble Report ──
        total_time = (time.perf_counter() - pipeline_start) * 1000.0

        diagnostics = PipelineDiagnostics(
            pipeline_version="0.1.0-mvp",
            total_pipeline_time_ms=round(total_time, 2),
            resume_parsing_time_ms=round(resume_time, 2),
            skill_extraction_time_ms=round(skill_time, 2),
            jd_parsing_time_ms=round(jd_time, 2),
            fit_scoring_time_ms=round(fit_time, 2),
            rag_retrieval_time_ms=round(rag_time, 2),
            warnings=warnings,
            stages_completed=stages_completed,
        )

        return SkillGapReport(
            report_id=str(uuid.uuid4()),
            resume_document=resume_doc,
            candidate_skills=candidate_skills,
            job_description=jd_doc,
            fit_report=fit_report,
            interview_prep_contexts=interview_contexts,
            diagnostics=diagnostics,
        )

    def _build_default_query(self, role_title: Optional[str], missing_skills: List[str]) -> str:
        """Build a sensible default interview prep query from JD metadata."""
        parts = []
        if role_title:
            parts.append(f"interview preparation for {role_title}")
        if missing_skills:
            parts.append(f"focus on {', '.join(missing_skills[:3])}")
        return " ".join(parts) if parts else "technical interview preparation"
