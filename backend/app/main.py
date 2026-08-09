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

from app.api.routes import ai_incident, analyses, auth, autoscaling, deployments, health, health_check, observability, plans, projects, readme, self_healing
from app.core.config import settings
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.services.health.scheduler import HealthScheduler
from app.services.observability.scheduler import MetricsScheduler
from app.services.autoscaling.scheduler import AutoscalingScheduler
from app.services.self_healing.scheduler import SelfHealingScheduler
from app.services.self_healing.worker import RecoveryWorker

# ── Configure logging immediately ────────────────────────────────────────────
configure_logging()
logger = logging.getLogger("cloudpilot.main")
health_scheduler = HealthScheduler()
metrics_scheduler = MetricsScheduler()
autoscaling_scheduler = AutoscalingScheduler()
recovery_worker = RecoveryWorker()
self_healing_scheduler = SelfHealingScheduler(recovery_worker)
self_healing.set_recovery_worker(recovery_worker)


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CloudPilot API starting up (env=%s)", settings.ENVIRONMENT)
    health_scheduler.start()
    metrics_scheduler.start()
    autoscaling_scheduler.start()
    recovery_worker.start()
    self_healing_scheduler.start()
    yield
    metrics_scheduler.stop()
    health_scheduler.stop()
    autoscaling_scheduler.stop()
    self_healing_scheduler.stop()
    recovery_worker.stop()
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
        "**Phase 5**: Deployment & Health Check Engine.\n\n"
        "**Phase 6**: Real-Time Observability Platform.\n\n"
        "**Phase 7**: Controlled Traffic & Deterministic Autoscaling.\n\n"
        "**Phase 8**: Failure Injection & Evidence-Driven Autonomous Self-Healing.\n\n"
        "**Phase 9**: Advisory AI Incident Intelligence with bounded context, "
        "redaction, schema validation, deterministic fallback, and audit traces."
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
app.include_router(health_check.router, prefix=API_PREFIX)
app.include_router(observability.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(analyses.router)
app.include_router(plans.router)
app.include_router(deployments.router)
app.include_router(autoscaling.router)
app.include_router(self_healing.router)
app.include_router(ai_incident.router)
app.include_router(readme.router)


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
