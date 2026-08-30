from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import router as findings_router
from app.config import settings
from app.core.logging import setup_logging
from app.database import db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to handle startup data seeding and cleanup."""
    setup_logging(log_level=settings.log_level)
    if db.count() == 0:
        db.seed(count=settings.seed_record_count)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DevSecOps Security Findings CRUD API with In-Memory Storage and Observability",
    lifespan=lifespan,
)

# Include API routers
app.include_router(findings_router)


@app.get("/health", tags=["Health & Diagnostics"], summary="Liveness and Readiness Probe")
def healthcheck() -> dict[str, object]:
    """Healthcheck endpoint for container orchestration and liveness checks."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "records_loaded": db.count(),
    }


@app.get("/", tags=["Root"], summary="API Root Info")
def root() -> dict[str, str]:
    """Root endpoint providing links to documentation and health status."""
    return {
        "message": "Security Findings API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_v1_url": "/api/v1/findings",
    }
