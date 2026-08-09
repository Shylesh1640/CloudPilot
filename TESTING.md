# Testing

Backend tests run inside the backend environment:

```bash
docker compose exec backend pytest tests/ -v
```

Static backend syntax verification can be run with `python -m compileall -q app tests` from `backend`. Frontend validation is `npm run type-check`, `npm run lint`, and `npm run build` from `frontend` after `npm install`.

For Phase 9, test a valid structured provider response, timeout/unavailable/invalid responses, secret redaction, recommendation rejection for an unknown target, authorization isolation, and confirmation that AI analysis never calls the recovery executor. Exercise an injected incident in simulation before any controlled non-production recovery test.
