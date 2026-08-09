# CloudPilot architecture

CloudPilot is a React/Vite frontend and FastAPI backend backed by PostgreSQL. The backend separates API routes, services, repositories, and SQLAlchemy models. Docker is accessed only through the orchestrator service layer.

```text
Browser -> FastAPI routes -> service policy -> repository -> PostgreSQL
                              |
                              +-> container runtime (controlled operations only)

Incident -> context builder -> redaction -> AI provider -> schema validation
        -> recommendation policy -> advisory response + audit trace
```

Phase 7 traffic generation produces bounded load and records metrics. The autoscaler evaluates persisted, fresh metric windows and applies deterministic policy. Phase 8 failure injection and recovery are separately policy-gated; they do not accept arbitrary commands. Phase 9 only reads a bounded incident context and produces advice. It has no reference to the recovery executor or Docker runtime.

`ai_decision_traces` stores the provider/model, context hash, structured result, validation result, latency, and error status. `incident_memory` stores redacted facts from resolved incidents for limited history lookup. Raw prompts and raw log payloads are not persisted.
