# CloudPilot

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

## Ready for Phase 2

Phase 2 will add:
- GitHub repository connection and OAuth
- Automatic repository analysis (language, framework, dependencies)
- Analysis result storage and display in the Architecture tab

See `backend/app/services/repository_analyzer.py` for the prepared interface.