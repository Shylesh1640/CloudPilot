"""Health check route."""
from __future__ import annotations

from fastapi import APIRouter

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
    return {"status": "healthy", "service": "cloudpilot-api"}
