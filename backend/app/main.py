"""
CloudPilot FastAPI Application Entry Point.

Configures:
- CORS middleware (origin from environment)
- Structured request logging middleware
- API router (prefix: /api/v1)
- Global exception handlers
- OpenAPI documentation
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analyses, auth, deployments, health, plans, projects
from app.core.config import settings
from app.core.logging import RequestLoggingMiddleware, configure_logging

# ── Configure logging immediately ────────────────────────────────────────────
configure_logging()
logger = logging.getLogger("cloudpilot.main")


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CloudPilot API starting up (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("🛑 CloudPilot API shutting down")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="CloudPilot API",
    description=(
        "AI-powered self-healing deployment platform.\n\n"
        "**Phase 1**: Foundation — Authentication and Project Management.\n\n"
        "**Phase 2**: GitHub Repository Analyzer.\n\n"
        "**Phase 3**: AI Infrastructure Architecture Planner.\n\n"
        "**Phase 4**: Container & Service Orchestrator.\n\n"
        "Phases 5–10 will add health monitoring, real-time observability, "
        "autoscaling, failure injection, and AI root-cause analysis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(analyses.router)
app.include_router(plans.router)
app.include_router(deployments.router)


# ── Global Exception Handlers ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )


# ── Root redirect ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "CloudPilot API — see /docs for documentation"}
