# Industrial Safety Intelligence Platform

An enterprise-style operational view of an industrial site — currently the **Riverbend
Refinery**, a fictional Gulf Coast crude oil refinery: process units, tank storage, product
loading, utilities and safety systems, with workers, equipment, instruments and
permits-to-work continuously evolved by a backend simulation engine.

- **Frontend** (`src/`) — React + TypeScript + Vite + Tailwind, enterprise design system, the Plant module
- **Backend** (`backend/`) — FastAPI + SQLAlchemy (async) + PostgreSQL + a tick-based plant simulator

The domain is **configuration-driven**: everything refinery-specific (zones, equipment,
instruments and their operating ranges, permit vocabulary, simulation behavior) lives in a
Plant Type definition (`backend/app/plant_types/refinery.py`). Supporting another industry —
chemical plant, steel plant, LNG terminal — means adding a new definition, not rewriting the
simulator or the UI.

The frontend polls the backend every 5 seconds, so once both are running the refinery
genuinely changes on its own — process values drift within their operating bands, tank levels
fill and draw, workers move between zones, equipment cycles through maintenance with the
authorizing permit raised alongside it.

## Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.12+ and [uv](https://docs.astral.sh/uv/)
- **PostgreSQL** 14+ running locally. This machine has it installed via `winget install PostgreSQL.PostgreSQL.17`
  as the `postgresql-x64-17` Windows service (starts automatically — nothing to do). On a
  different machine, either install Postgres the same way or run `docker compose up -d`
  from `backend/` (see `backend/docker-compose.yml`).

## Running the local testing environment

Two terminals: one for the backend, one for the frontend.

### 1. Backend

```bash
cd backend
uv sync --group dev
cp .env.example .env          # adjust DATABASE_URL if your Postgres differs
uv run alembic upgrade head   # create/update the schema
uv run python -m scripts.seed # populate the Riverbend Refinery (safe to skip if already seeded)
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000/api/v1
- Interactive docs: http://localhost:8000/docs
- The simulation engine starts automatically with the API (`SIMULATION_ENABLED=true` by
  default) and ticks every 5 seconds — see `backend/README.md` for what it actually does.

### 2. Frontend

From the repo root:

```bash
cp .env.example .env   # only needed once — points the app at the backend above
npm install
npm run dev
```

Open http://localhost:5173, then go to **Plant** in the sidebar. Data updates on its own
every few seconds; watch a zone's sensor values or worker list change between refreshes.

### Resetting the simulated data

The simulator continuously mutates the database, so after a while it'll have drifted well
past the original seed. To start over:

```bash
# from backend/, with the API stopped or at least momentarily quiesced
export PATH="/c/Program Files/PostgreSQL/17/bin:$PATH"   # if psql isn't already on PATH
PGPASSWORD=postgres psql -U postgres -h localhost -d industrial_safety -c "TRUNCATE plants CASCADE;"
uv run python -m scripts.seed
```

## Testing

```bash
cd backend && uv run pytest    # backend: pytest against an in-memory SQLite fixture
npx tsc -b && npm run build    # frontend: type-check + production build (no test suite yet)
```

## Project structure

```
src/                    Frontend (see src/features/plant/ for the one real feature module)
backend/                Backend (see backend/README.md for its architecture and API)
.env.example            Frontend env template (VITE_API_BASE_URL)
backend/.env.example    Backend env template (DATABASE_URL, simulation settings)
```

## Linting

```bash
npm run lint   # oxlint
```

Type-aware lint rules are available but not enabled by default — see `.oxlintrc.json` and the
[Oxlint docs](https://oxc.rs/docs/guide/usage/linter/rules) if you want to turn them on.
