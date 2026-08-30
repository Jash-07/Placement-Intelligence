"""
FastAPI application factory for PII-001
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pii_001.api.routes import router as api_router, health_check


def create_app() -> FastAPI:
    """Application factory for PII-001 REST API service."""
    app = FastAPI(
        title="PII-001 Placement Intelligence Platform API",
        description="AI-powered candidate-role fit, skill-gap analysis, and grounded interview preparation API.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.add_api_route("/health", health_check, tags=["Health"], methods=["GET"])
    app.include_router(api_router)

    return app


app = create_app()
