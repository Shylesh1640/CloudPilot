"""Liveness, readiness, and version endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Service health check",
    description="Returns the health status of the CloudPilot API service. Use this endpoint for container health checks and uptime monitoring.",
    response_description="Health status object",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "service": "cloudpilot-api"}
                }
            },
        }
    },
)
async def health_check() -> dict:
    """Liveness only: the process can answer HTTP requests."""
    return {"status": "healthy", "service": "cloudpilot-api"}


@router.get("/ready", summary="Service readiness check")
async def readiness_check() -> dict:
    """Readiness requires the database dependency to answer a real query."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "service": "cloudpilot-api", "database": "unavailable"},
        ) from exc
    return {"status": "ready", "service": "cloudpilot-api", "database": "available"}


@router.get("/version", summary="Build and runtime version")
async def version() -> dict:
    return {"service": "cloudpilot-api", "version": "1.0.0", "environment": settings.ENVIRONMENT}
