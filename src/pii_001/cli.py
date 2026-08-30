"""
PII-001 CLI Entry Point

Usage:
    python -m pii_001.cli --resume resume.pdf --jd jd.txt [--company-docs doc1.txt doc2.txt] [--query "..."]
"""

import argparse
import json
import sys
from pathlib import Path

from pii_001.pipeline import PlacementIntelligencePipeline


def main():
    parser = argparse.ArgumentParser(
        prog="pii-001",
        description="PII-001 — AI-Powered Placement Intelligence & Interview Platform (MVP CLI)",
    )
    parser.add_argument("--resume", required=True, help="Path to resume file (PDF or TXT)")
    parser.add_argument("--jd", required=True, help="Path to job description file (TXT)")
    parser.add_argument("--company-docs", nargs="*", default=[], help="Optional company prep document paths")
    parser.add_argument("--query", default=None, help="Optional interview prep query for RAG retrieval")
    parser.add_argument("--top-k", type=int, default=3, help="Number of RAG context passages to retrieve (default: 3)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args()

    # Validate paths
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Error: Resume file not found at '{args.resume}'", file=sys.stderr)
        sys.exit(1)

    jd_path = Path(args.jd)
    if not jd_path.exists():
        print(f"Error: Job description file not found at '{args.jd}'", file=sys.stderr)
        sys.exit(1)

    jd_text = jd_path.read_text(encoding="utf-8", errors="replace")

    # Run pipeline
    pipeline = PlacementIntelligencePipeline()
    report = pipeline.analyze(
        resume_path=resume_path,
        jd_text=jd_text,
        company_docs=args.company_docs if args.company_docs else None,
        interview_query=args.query,
        top_k=args.top_k,
    )

    # Output report as JSON
    indent = 2 if args.pretty else None
    print(report.model_dump_json(indent=indent))


if __name__ == "__main__":
    main()
