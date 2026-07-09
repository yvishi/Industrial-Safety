# Backend

FastAPI + SQLAlchemy 2.0 (async) + Alembic backend for the Industrial Safety Intelligence
Platform. This is the data-access foundation: plants, zones, workers, equipment, sensors,
permits, and an activity log — structural/CRUD data only. No auth, no AI, no computed risk state.

## Stack

- **FastAPI** — API layer, versioned under `/api/v1`
- **SQLAlchemy 2.0** (async, `asyncpg` driver) — ORM
- **Alembic** — migrations
- **PostgreSQL** — database (async in the app; tests run against in-memory SQLite for speed)
- **uv** — dependency management

## Architecture

```
app/
  api/v1/endpoints/   FastAPI routers — one per entity, thin (no DB session logic here)
  core/               settings, exception -> HTTP mapping, logging
  database/           declarative base, mixins (UUID PK, timestamps), session/engine
  models/             SQLAlchemy ORM models
  schemas/            Pydantic Create/Update/Read models + enums (validation boundary)
  repositories/        SQLAlchemy queries, one class per entity + a generic CRUD base
  services/            not-found/conflict rules + orchestration above repositories
alembic/              migrations
scripts/seed.py        populates a believable fictional plant
tests/                  pytest + httpx, SQLite-backed
```

Request flow: **router -> service -> repository -> model**. Routers never touch a SQLAlchemy
session directly — that's what lets the future Risk/Recommendation engines reuse the same
services the API uses, instead of re-deriving data access.

## Setup

```bash
uv sync --group dev
cp .env.example .env   # adjust DATABASE_URL if needed
```

Postgres: either run locally (`docker compose up -d` using the provided `docker-compose.yml`)
or point `DATABASE_URL` in `.env` at any Postgres 14+ instance. Then:

```bash
uv run alembic upgrade head
uv run python -m scripts.seed
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000/api/v1
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Test

```bash
uv run pytest
```

## Notes for future modules

- `zone_type`, `equipment_type`, `sensor_type`, `permit_type`, `permit_status`, `event_type` are
  plain strings validated by a Pydantic enum at the API boundary — not Postgres enum/CHECK
  constraints. Extending any of these vocabularies (new event types especially) needs no
  migration.
- `Sensor` is a registry/catalog record, not a telemetry store. Live readings are a deliberately
  separate future concern with its own storage shape (likely not a plain relational table).
- `Event` is a generic activity log. The future Incident Timeline is a filtered/sorted view over
  this table, not a new one.
- Zone codes/types/grid positions mirror `src/features/plant/data/zones.ts` in the frontend
  exactly, so swapping the frontend's static data for a real API call needs no remapping.
