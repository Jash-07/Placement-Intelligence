# PII-001 — AI-Powered Placement Intelligence & Interview Platform

## Project Status

**Status:** Planning / Feasibility
**Current Phase:** Phase 0 — Feasibility
**Baseline:** 15 August 2026
**Project Code:** PII-001

PII-001 is a production-oriented career intelligence platform designed to transform unstructured resumes and job descriptions into normalized skills, evidence-backed candidate-role fit analysis, actionable skill gaps, grounded interview preparation, role-specific interview questions, structured interview evaluation, and candidate analytics.

The project is being developed as an applied **NLP / Information Retrieval / Generative AI** system rather than as a thin LLM wrapper.

---

## Overview

The platform aims to provide a traceable workflow from candidate evidence and job requirements to recommendations and interview evaluation.

The core vision is:

> Every recommendation should be traceable to resume evidence, job requirements, retrieved source material, or an explicitly stated inference.

The system is designed to separate deterministic processing and scoring from retrieval and generative explanation so that individual components can be measured and evaluated independently.

---

## Current Phase

### Phase 0 — Feasibility

**Target:** 17–23 August 2026

The current phase focuses on validating the assumptions required for the broader system before committing to the complete implementation.

Current feasibility areas include:

* Resume parsing
* Data assumptions
* Retrieval assumptions
* LLM assumptions

### Current Spike

**SP-001 — Resume Parsing Feasibility**

Key question:

> Can real-world PDF/text resumes be reliably transformed into normalized structured documents that downstream components can consume?

The initial approach is to establish a baseline parser before introducing LLM-based parsing, embeddings, vector databases, or the complete application.

---

## Planned Product Scope

The planned platform includes:

* PDF/text resume ingestion and normalization
* Job-description ingestion from permitted sources or user-provided files
* Skill taxonomy and synonym normalization
* Candidate-role fit scoring
* Skill-gap analysis
* Hybrid retrieval and ranking
* Company and role intelligence
* Role-specific interview question generation
* Structured interview evaluation
* Candidate analytics
* API and web application
* Evaluation, observability, and deployment infrastructure

The initial release is not intended to provide guaranteed job placement, hiring decisions, automated job applications, background checks, or autonomous career decisions.

---

## Release Direction

### MVP

**Purpose:** Prove core candidate-role intelligence.

Planned capabilities:

* Resume parser
* Skill taxonomy
* JD matching
* Skill-gap report

**Exit criterion:** Gold-set extraction and matching evaluation passed.

### V1

**Purpose:** Provide a usable interview intelligence product.

Planned capabilities:

* Retrieval-augmented generation
* Company/role preparation
* Interview question generation
* Dashboard
* API

**Exit criterion:** End-to-end user journey passes and the evaluation baseline is beaten.

### V2

**Purpose:** Provide adaptive and scalable intelligence.

Planned capabilities:

* Interview adaptation
* Advanced ranking
* Cohort analytics
* Monitoring

V2 will not begin until the MVP evaluation passes.

---

## Planned Technology Direction

The current proposed technology direction is:

| Layer               | Planned Technology             |
| ------------------- | ------------------------------ |
| Frontend            | Next.js + Tailwind             |
| API                 | FastAPI                        |
| Primary Database    | PostgreSQL                     |
| Vector Retrieval    | PostgreSQL + pgvector          |
| NLP                 | spaCy + transformers as needed |
| LLM Layer           | Provider-agnostic gateway      |
| Experiment Tracking | MLflow + structured JSON logs  |
| Deployment          | Docker + cloud service         |

These technologies represent the current planning baseline. Feasibility results and architecture decisions may lead to documented changes.

---

## Evaluation Philosophy

AI components will be treated as experimental hypotheses rather than accepted solely because their outputs appear convincing.

A simple baseline will be established before introducing more sophisticated methods.

Current baseline directions include:

* **Skill extraction:** Keyword dictionary + string matching
* **Retrieval:** BM25 / lexical retrieval
* **Fit scoring:** Weighted skill overlap
* **Interview generation:** Fixed template question bank

Important evaluation metrics include:

* Precision
* Recall
* F1
* Recall@K
* MRR
* NDCG
* Groundedness
* Citation accuracy
* Rubric agreement
* Latency
* Cost

Model improvements will be accepted based on measured evidence rather than subjective demonstrations.

---

## Engineering Principles

PII-001 follows these core principles:

1. **Evidence first** — recommendations should be traceable to supporting evidence.
2. **Baseline first** — establish a measurable reference before adding complexity.
3. **Deterministic core** — separate deterministic processing and scoring from generative explanation.
4. **Provider agnostic** — avoid unnecessary dependence on a single LLM or embedding provider.
5. **Version everything important** — code, prompts, taxonomies, datasets, model IDs, and evaluation artifacts.
6. **Design for failure** — parsing errors, unavailable sources, empty retrieval, provider failures, and malformed model outputs must be handled explicitly.
7. **Privacy conscious** — minimize sensitive candidate information and never commit secrets.
8. **Reproducible engineering** — experiments and releases should be traceable to their relevant versions and evidence.

---

## Repository Direction

The repository will evolve toward the following structure:

```text
placement-intelligence/
├── apps/
│   └── web/
├── services/
│   ├── api/
│   ├── ingestion/
│   ├── retrieval/
│   └── evaluation/
├── packages/
│   └── taxonomy/
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
├── experiments/
├── tests/
├── docs/
├── infra/
├── .github/
│   └── workflows/
├── docker/
├── README.md
├── pyproject.toml
└── docker-compose.yml
```

Components will be introduced incrementally according to the project lifecycle rather than creating unused production structures prematurely.

---

## Documentation

The **PII-001 Project Master Dossier** is the authoritative project specification.

It defines:

* Project Charter
* Product Requirements Document
* Architecture & Technical Design
* Timeline & Execution Plan
* Data Plan
* Experiment & Evaluation Plan
* Engineering & Project Documentation

Project documentation is maintained under:

```text
docs/
```

The current master dossier is located at:

```text
docs/project/PII-001_Project_Master_Dossier_v1.0.docx
```

---

## Development Lifecycle

PII-001 follows:

```text
Plan
  ↓
Build
  ↓
Validate
  ↓
Deploy
  ↓
Review
```

The development workflow uses:

* Feature branches
* Pull requests
* Unit tests
* Integration tests
* End-to-end tests
* Architecture Decision Records
* Changelog
* Versioned releases
* CI
* Reproducible environments
* Versioned datasets and evaluation artifacts

Even though the project is being developed by a single student developer, pull requests are used for review and traceability.

---

## Data & Privacy

Resume data is treated as sensitive personal data.

The project will:

* Minimize personally identifiable information in logs
* Avoid committing private user data
* Keep raw resume data outside Git
* Preserve provenance for external evidence
* Respect licensing and terms of service
* Avoid unauthorized scraping or access-control bypasses
* Maintain appropriate deletion and retention workflows

Unknown skills should remain unknown rather than being silently mapped to an unrelated taxonomy item.

---

## Current Repository State

This repository is currently being established as a new, independent project.

The repository has no relationship to the previously abandoned `PlacementPrep-AI` project.

PII-001 maintains its own:

* Repository
* Git history
* Architecture
* Documentation
* Evaluation framework
* Development lifecycle

---

## License

A project license has not yet been selected.

This will be decided explicitly before a public release.
