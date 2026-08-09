# API reference

Interactive OpenAPI documentation is available at `/docs`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/health/ready` | Database-backed readiness check |
| GET | `/api/v1/health/version` | API version and environment |
| GET | `/api/v1/deployments/{deployment_id}/incidents` | Incident list |
| GET | `/api/v1/incidents/{incident_id}/timeline` | Recovery/audit timeline |
| POST | `/api/v1/incidents/{incident_id}/recover` | Deterministic recovery request |
| GET | `/api/v1/incidents/{incident_id}/ai-analysis` | Cached or new advisory AI analysis |
| POST | `/api/v1/incidents/{incident_id}/ai-analysis` | Refresh advisory AI analysis |
| POST | `/api/v1/incidents/{incident_id}/assistant` | Bounded explanatory incident question |

Except for health endpoints, requests require `Authorization: Bearer <token>`. AI analysis responses include `status`, `fallback`, `cached`, `trace_id`, and validation results. A fallback result is valid advisory output, not an execution request.
