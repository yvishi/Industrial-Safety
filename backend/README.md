# Backend

FastAPI + SQLAlchemy 2.0 (async) + Alembic backend for the Industrial Safety Intelligence
Platform: plants, zones, workers, equipment, sensors, permits, an activity log, and a
**plant simulation engine** that continuously evolves the operational state (sensor telemetry,
worker movement, equipment lifecycle, permit workflow) and persists it to Postgres.
No auth, no AI, no computed risk state.

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
  simulation/          plant simulation engine (never imports from api/)
    profiles.py        per-sensor-type physics: baseline, noise, warning levels
    behaviors/         sensors, workers, equipment, permits — one module each
    engine.py          the tick loop; one transaction per tick
    runner.py          standalone entrypoint (python -m app.simulation.runner)
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

## Simulation

The simulator runs inside the API process by default (`SIMULATION_ENABLED=true`), ticking
every `SIMULATION_TICK_SECONDS` (default 5s):

- **Sensors** take a mean-reverting random-walk step each tick; occasional controlled
  excursions climb toward the warning level and recover. Band crossings emit
  `sensor_warning` / `sensor_recovered` events — raw readings are never events.
- **Workers** move between grid-adjacent zones with a homing bias toward their station.
- **Equipment** transitions operational/standby/under_maintenance with realistic dwell
  times; safety-critical assets never stop.
- **Permits** walk draft -> pending -> approved -> active -> closed/expired, and new
  realistic permits appear over time.

Every meaningful change is committed in the same transaction as its Event row.
Readings are pruned past `SENSOR_READING_RETENTION_HOURS` (default 24h).

To run the simulator as its own process instead, set `SIMULATION_ENABLED=false` in `.env`
and start `uv run python -m app.simulation.runner` alongside uvicorn.

Key read endpoints for the frontend:

- `GET /api/v1/state` — aggregate live snapshot (zones with occupants, equipment,
  latest sensor values, active permits, recent events)
- `GET /api/v1/sensors/{id}/readings?minutes=60` — reading history, oldest first
- `GET /api/v1/events?page_size=50` — newest first

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
