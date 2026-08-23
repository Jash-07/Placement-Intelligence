"""
Pytest configuration and synthetic resume & JD fixtures for PII-001
"""

import pytest
from pathlib import Path

SAMPLE_STANDARD_RESUME = """
Alex Morgan
Email: alex.morgan@example.com | Phone: +1-555-019-2831 | GitHub: github.com/alexmorgan

SUMMARY
Dedicated Software Engineer with 4 years of experience building scalable backend APIs, distributed systems, and data pipelines using Python, FastAPI, and PostgreSQL.

WORK EXPERIENCE
Senior Backend Engineer | TechCorp Inc.
2022 - Present
- Designed microservices architecture handling 10M daily requests with FastAPI and PostgreSQL.
- Improved database query performance by 40% using query optimization and indexing.

Software Developer | DataFlow Systems
2020 - 2022
- Implemented real-time ETL pipelines in Python processing 500GB daily telemetry data.
- Built automated CI/CD pipelines with GitHub Actions reducing deployment cycles by 30%.

EDUCATION
Bachelor of Science in Computer Science
University of Technology | Graduated May 2020 | GPA: 3.8/4.0

SKILLS
- Languages: Python, SQL, JavaScript, C++
- Frameworks & Tools: FastAPI, PyTorch, Docker, PostgreSQL, Git, Redis
- Expertise: System Architecture, REST API Design, Data Pipelines

PROJECTS
Placement Intelligence Platform
- Built end-to-end resume parser using Python, spaCy, and Pydantic.
- Implemented fit scoring engine using TF-IDF and cosine similarity.

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate (2023)
"""

SAMPLE_MINIMAL_RESUME = """
Jane Doe
Email: jane.doe@example.com

SUMMARY
Passionate beginner coder looking for entry level software opportunities.
"""

SAMPLE_BACKEND_ENGINEER_JD = """
TechCorp Inc.
Senior Backend Engineer

JOB SUMMARY
We are seeking an experienced Senior Backend Engineer to join our core platform engineering team. You will lead the design and implementation of high-throughput REST APIs and microservices.

RESPONSIBILITIES
- Architect, build, and maintain production backend microservices in Python and FastAPI.
- Optimize complex database queries and database models in PostgreSQL.
- Collaborate with frontend engineers to integrate REST APIs.

MINIMUM QUALIFICATIONS
- Minimum 4+ years of professional software engineering experience.
- Strong proficiency in Python, FastAPI, and SQL.
- Extensive experience working with PostgreSQL or relational databases.
- Required: Solid understanding of REST API design and Microservices.

PREFERRED QUALIFICATIONS
- Experience with Docker and Kubernetes containerization is a plus.
- Knowledge of Redis caching and AWS cloud infrastructure is preferred.
- Familiarity with CI/CD automation pipelines is nice to have.
"""


@pytest.fixture
def sample_standard_resume_text() -> str:
    """Fixture providing a well-structured synthetic resume text."""
    return SAMPLE_STANDARD_RESUME


@pytest.fixture
def sample_minimal_resume_text() -> str:
    """Fixture providing a minimal synthetic resume text with missing critical sections."""
    return SAMPLE_MINIMAL_RESUME


@pytest.fixture
def sample_backend_jd_text() -> str:
    """Fixture providing a synthetic Senior Backend Engineer Job Description."""
    return SAMPLE_BACKEND_ENGINEER_JD


@pytest.fixture
def sample_txt_file(tmp_path: Path) -> Path:
    """Fixture generating a temporary text resume file."""
    file_path = tmp_path / "sample_resume.txt"
    file_path.write_text(SAMPLE_STANDARD_RESUME, encoding="utf-8")
    return file_path
