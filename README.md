# CloudPilot

## Phase 7 — Traffic & deterministic autoscaling

Phase 7 adds controlled load testing and a deterministic, policy-driven horizontal autoscaler. The decision path is `telemetry → stabilization window → threshold/hysteresis → cooldown → safety validation → replica manager → Docker runtime`; no LLM participates in replica decisions.

Scaling policies support CPU, memory, request-rate (only when supplied by application telemetry), and p95-latency targets. Scale-up uses any breached configured metric; scale-down requires every configured metric to be below its lower hysteresis threshold. Policies enforce min/max replicas, bounded steps, separate cooldowns, stale-telemetry blocking, dry-run, and simulation flags.

Authenticated APIs include `GET/PUT /api/v1/deployments/{deployment_id}/services/{service_id}/scaling`, policy toggling, manual safe scaling, decision/event history, and managed traffic runs at `/api/v1/deployments/{deployment_id}/traffic`. Traffic can only target a running CloudPilot-managed public service and is capped by `TRAFFIC_MAX_RPS` (500), `TRAFFIC_MAX_DURATION_SECONDS` (300), and `TRAFFIC_MAX_CONCURRENT_RUNS` (2). The dashboard is available at `/deployments/:deploymentId/autoscaling`.

## Phase 8 — Failure injection & self-healing

Phase 8 adds an evidence-driven, allowlisted recovery path: health/container signals create a deduplicated incident, dependency analysis identifies a root service, a deterministic policy selects the least disruptive recovery, and a safety gate verifies policy, cooldown, attempts, deployment state, and operation locks before the recovery executor can use the container runtime. Recovery is verified through both runtime state and Phase 5 health before resolution; failed repeated attempts are escalated with exponential backoff and a full audit trail.

Controlled injection is restricted to active CloudPilot-managed services in non-production environments. The supported scenarios are container stop, controlled kill-equivalent, single-replica failure, service failure, and health-check simulation. APIs provide injection, incidents, timelines, recovery attempts, manual recovery, and safe recovery-policy configuration. The reliability dashboard is at `/deployments/:deploymentId/reliability`.

> AI-powered self-healing deployment platform.

CloudPilot allows developers to connect a GitHub repository, analyze it automatically, generate infrastructure, build and deploy containers, monitor services in real time, autoscale, inject failures, and self-heal — all powered by AI.

**Current Phase: Phase 1 — Foundation**

---

## Architecture

```
CloudPilot
│
├── frontend/         React + Vite + TypeScript + Tailwind CSS
├── backend/          FastAPI + SQLAlchemy + Alembic + PostgreSQL
├── infrastructure/   Docker Compose
└── docs/             Documentation
```

## Phase Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Foundation — Auth, Projects, Dashboard | ✅ Complete |
| 2 | GitHub Repository Analyzer | 🔜 Planned |
| 3 | AI Infrastructure Planner | 🔜 Planned |
| 4 | Container Manager | 🔜 Planned |
| 5 | Deployment Engine | 🔜 Planned |
| 6 | Real-Time Observability | 🔜 Planned |
| 7 | Autoscaling | 🔜 Planned |
| 8 | Failure Injection | 🔜 Planned |
| 9 | Self-Healing Engine | 🔜 Planned |
| 10 | AI Root-Cause Analysis | 🔜 Planned |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.20
- Git

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/cloudpilot.git
cd cloudpilot
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set a secure `JWT_SECRET_KEY`. All other defaults work for local development.

### 3. Start with Docker Compose

```bash
docker compose up --build
```

This will:
1. Start PostgreSQL and wait for it to be healthy
2. Start the FastAPI backend, run Alembic migrations, and wait for it to be healthy
3. Start the React frontend

### 4. Open the application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |

### 5. Create an account

Visit http://localhost:5173/register and create your first account.

---

## Development

### Running tests

```bash
docker compose exec backend pytest tests/ -v
```

### Running only backend locally (without Docker)

```bash
cd backend
pip install -r requirements.txt

# Set DATABASE_URL to a local PostgreSQL instance
export DATABASE_URL=postgresql+asyncpg://cloudpilot:cloudpilot@localhost:5432/cloudpilot

alembic upgrade head
uvicorn app.main:app --reload
```

### Running only frontend locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

Interactive API documentation is available at `http://localhost:8000/docs`.

### Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Create a new account |
| `POST` | `/api/v1/auth/login` | Login and receive JWT |
| `GET` | `/api/v1/auth/me` | Get current user profile |

### Project Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/projects` | List your projects |
| `POST` | `/api/v1/projects` | Create a project |
| `GET` | `/api/v1/projects/{id}` | Get a project |
| `PUT` | `/api/v1/projects/{id}` | Update a project |
| `DELETE` | `/api/v1/projects/{id}` | Delete a project |

### Authentication

All project endpoints require an `Authorization: Bearer <token>` header. Obtain a token from `POST /api/v1/auth/login`.

---

## Project Structure

```
cloudpilot/
│
├── frontend/
│   └── src/
│       ├── components/         Reusable UI components
│       ├── pages/              Route-level page components
│       ├── layouts/            Application shell layouts
│       ├── hooks/              Custom React hooks
│       ├── services/           API service layer (Axios)
│       ├── context/            React context providers
│       ├── types/              TypeScript interfaces
│       └── utils/              Utility functions
│
├── backend/
│   └── app/
│       ├── api/routes/         FastAPI route handlers
│       ├── core/               Config, security, database, logging
│       ├── models/             SQLAlchemy ORM models
│       ├── schemas/            Pydantic request/response schemas
│       ├── repositories/       Database access layer
│       └── services/           Business logic (+ Phase 2–10 stubs)
│
├── infrastructure/             Docker configuration files
├── .env.example                Environment template
├── docker-compose.yml          Full-stack Docker configuration
└── README.md
```

---

## Security

- Passwords are hashed with **bcrypt** — never stored in plaintext
- Authentication uses **JWT** (HS256) with configurable expiry
- Projects are **user-scoped** — you can only access your own projects
- CORS is configured to allow only the configured `FRONTEND_URL`
- SQL injection is prevented by **SQLAlchemy** ORM
- Secrets are loaded from **environment variables** — never committed

---

## Troubleshooting

**Backend fails to start**
- Check that PostgreSQL is healthy: `docker compose ps`
- Check backend logs: `docker compose logs backend`

**Migrations fail**
- Ensure `DATABASE_URL` points to the Postgres service
- Run manually: `docker compose exec backend alembic upgrade head`

**Frontend cannot reach backend**
- Verify `VITE_API_URL` is set correctly in `.env`
- Check CORS: `FRONTEND_URL` must match the frontend origin

---

## Reliability and AI incident intelligence

CloudPilot includes controlled traffic, deterministic autoscaling, failure injection, and self-healing. Phase 9 adds advisory incident intelligence:

- incident-scoped context with bounded logs, metrics, topology, recovery events, and relevant prior incidents;
- redaction before provider calls and redacted structured decision traces at rest;
- schema validation, safe action allow-listing, and deterministic fallback when AI is unavailable, times out, or returns invalid output;
- incident chat limited to explanatory, non-executing questions.

AI suggestions never invoke Docker, shells, databases, or recovery actions. Recovery remains governed by the existing deterministic policy.

See [AI.md](AI.md), [API.md](API.md), and [SECURITY.md](SECURITY.md) for operational details.
