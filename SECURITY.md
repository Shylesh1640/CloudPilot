# Security model

CloudPilot scopes projects and incidents to the authenticated user. JWT credentials authenticate API calls, SQLAlchemy parameterization protects database access, and CORS is restricted to `FRONTEND_URL`.

## AI incident boundaries

- AI receives only redacted, size-bounded incident context.
- The prompt treats logs and external text as untrusted data, not instructions.
- Provider output must pass Pydantic schema validation and a deterministic action/target allow-list.
- AI output is advisory only. It cannot execute Docker commands, shell commands, database queries, deletion, deployment, scaling, or recovery.
- Incident chat rejects command-oriented requests and can only explain the selected incident.
- Decision traces retain a context hash and redacted structured result, not raw prompts or secrets.

## Production checklist

Set a high-entropy `JWT_SECRET_KEY`, unique PostgreSQL credentials, explicit `FRONTEND_URL`, and provider credentials through your secret manager. Do not commit `.env`. Set `ENVIRONMENT=production`; failure injection is denied in production by policy. Restrict Docker socket access to the backend host and run the backend with the minimum privileges needed for managed deployments.
