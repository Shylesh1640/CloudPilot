# Troubleshooting

**Readiness returns 503.** Verify PostgreSQL is healthy, `DATABASE_URL` is correct, and migrations have completed. `/health` is liveness-only; use `/health/ready` for dependency status.

**AI analysis reports a fallback.** This is expected with `AI_PROVIDER=mock`, no `AI_API_KEY`, provider timeouts, network failures, malformed JSON, or validation failure. Inspect the response `status` and `trace_id`; recovery policy remains available independently.

**A recommendation is missing.** Recommendations whose action is outside the allow-list or whose target is not in the bounded incident context are rejected. Use the incident timeline and controlled recovery endpoint instead of attempting an arbitrary command.

**No logs appear in analysis.** Ensure the incident service has a managed container and that the backend can read its logs. Log collection failure does not block analysis; the system uses health, metrics, events, and deterministic fallback.

**Migration error.** Check the current revision with `alembic current`, then run `alembic upgrade head` from `backend` using the same database URL as the application.
