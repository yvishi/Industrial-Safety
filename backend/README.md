# Backend

FastAPI + SQLAlchemy 2.0 (async) + Alembic backend for the Industrial Safety Intelligence
Platform: plants, zones, workers, equipment, sensors, permits, an activity log, and a
**plant simulation engine** that continuously evolves the operational state (sensor telemetry,
worker movement, equipment lifecycle, permit workflow) and persists it to Postgres.
No auth, no AI, no computed risk state.

The engine and API are **industry-agnostic**: all domain knowledge lives in a **Plant Type
definition** (`app/plant_types/`) — typed Pydantic configuration describing zones, equipment,
instruments with per-instrument operating ranges, permit vocabulary, worker roster, and
simulation tuning. One plant type ships today (`crude_oil_refinery`, seeded as the Riverbend
Refinery); adding an industry means writing a new definition module and registering it.

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
  plant_types/         Plant Type configuration layer (industry definitions)
    schema.py          Pydantic schema: what a plant type IS (zones, instruments, ranges, tuning)
    refinery.py        the Crude Oil Refinery definition (the only industry so far)
    registry.py        slug -> definition lookup used by the simulator and seed
  simulation/          plant simulation engine (never imports from api/; industry-agnostic)
    behaviors/         sensors, workers, equipment, permits — one module each
    engine.py          the tick loop; resolves the plant type, one transaction per tick
    runner.py          standalone entrypoint (python -m app.simulation.runner)
alembic/              migrations
scripts/seed.py        materializes the plant type definition into the Riverbend Refinery
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

- **Sensors** are sampled on their own per-instrument interval and evolve by a dynamics mode
  from the plant type's catalog: mean-reverting (temperatures, pressures, gas ppm), integrating
  (bulk tank levels fill and draw), or equipment-coupled (a stopped pump's flow decays to zero,
  without spurious alarms). Operating ranges come from each sensor's own DB row; crossings emit
  `sensor_warning` / `sensor_critical` / `sensor_recovered` events (high *or* low side — oxygen
  and fire-water pressure alarm low) — raw readings are never events.
- **Workers** move between grid-adjacent zones with a homing bias toward their station; which
  roles roam vs stay at a console comes from the plant type's tuning.
- **Equipment** transitions operational/standby/under_maintenance with per-type dwell times
  from the catalog; safety-critical assets keep their seeded status, and installed-spare pairs
  (e.g. crude charge pumps A/B) auto-start the standby unit when the duty unit goes down.
- **Permits** walk draft -> pending -> approved -> active -> closed/expired. When an asset
  enters maintenance, the authorizing permit (type and isolation standard chosen from the
  plant type's permit catalog) is drafted against it; occasional planned-work permits appear too.

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
  constraints. The enums are the *union across supported plant types*: adding an industry
  extends them (and mirrors the change in the frontend unions), no migration needed.
- Per-instrument operating ranges (`normal_/warning_/critical_ min/max`) live on the `Sensor`
  row, seeded from the plant type definition. They are instrument metadata — like alarm
  setpoints in a DCS — that also drives simulation events and UI display. The future Risk
  Engine still owns its own judgment; these bands are inputs, not risk scores.
- `Sensor` is a registry/catalog record, not a telemetry store. Live readings are a deliberately
  separate concern (`sensor_readings`, pruned to a retention window).
- `Event` is a generic activity log. The Operational Timeline (see
  `operational-timeline-architecture.md`) is a filtered/sorted read-model composed over this
  table plus `RiskSnapshot`/`Recommendation`/`Incident` — it owns no table of its own. `Incident`
  itself *is* a new, separate table (`app/models/incident.py`): a stateful, correlated episode
  the Correlation Engine (`app/correlation_engine/`) opens/tracks/resolves, distinct from the
  plain per-row `Event` log — see that architecture doc for why a bounded, ownable lifecycle
  entity turned out to need its own table rather than being a view.
- Zone/equipment/sensor identity flows from `app/plant_types/refinery.py` through the seed into
  the DB; the frontend renders whatever the API returns, so plant-type changes need matching
  updates only to the frontend's type unions and icon/label maps.
