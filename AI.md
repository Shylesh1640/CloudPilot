# AI Incident Intelligence

Phase 9 is an advisory layer for one incident at a time. The context builder gathers only the incident, relevant managed services, health, latest metrics, limited logs, recovery events, local topology, and a small set of matching redacted incident memories. Configurable defaults cap logs at 100 lines, events at 20, and history at five items.

Before a provider call, strings and structured data are redacted for common secrets, credentials, bearer tokens, JWTs, connection-string passwords, private keys, and user/contact fields. The provider is asked for JSON and its output is Pydantic-validated. Recommendations are then checked against a fixed safe action allow-list and known context targets.

Provider failure, timeout, malformed JSON, or schema failure returns a deterministic, low-confidence fallback with an explicit status. AI results never control the recovery worker. The UI labels fallback results and reminds operators that recommendations are advisory.

For OpenAI-backed deployments, configure `AI_PROVIDER=openai` and a key via the environment. The integration uses structured JSON responses and validates the response against the application schema; see OpenAI's [structured outputs guidance](https://platform.openai.com/docs/guides/structured-outputs).
