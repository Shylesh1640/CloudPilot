# Deployment

1. Copy `.env.example` to `.env` and set production secrets and URLs.
2. Start the stack with `docker compose up --build`.
3. Apply schema changes with `docker compose exec backend alembic upgrade head` if the deployment entrypoint has not already run them.
4. Confirm `/api/v1/health/ready` returns `ready` and inspect `/api/v1/health/version`.

The Phase 9 migration is `0009_ai_incident_intelligence`; it follows Phase 8 (`0008_self_healing`). Back up PostgreSQL before production schema changes. Docker Compose mounts the Docker socket for the controlled orchestrator; do not expose that socket to the frontend or public network.

For external AI, set `AI_PROVIDER=openai`, `AI_MODEL`, and `AI_API_KEY` through a secret manager. With no API key or with `AI_PROVIDER=mock`, Phase 9 uses its deterministic fallback and continues to provide auditable advisory output.
