import asyncio
import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    simulation_task: asyncio.Task | None = None
    risk_task: asyncio.Task | None = None

    if settings.simulation_enabled:
        # Imported here so the API can start (and tests can run) without the simulator.
        from app.database.session import AsyncSessionLocal
        from app.simulation.engine import SimulationEngine

        engine = SimulationEngine(
            AsyncSessionLocal,
            tick_seconds=settings.simulation_tick_seconds,
            retention_hours=settings.sensor_reading_retention_hours,
        )
        simulation_task = asyncio.create_task(engine.run())

    if settings.risk_engine_enabled:
        # A separate task, parallel to (not integrated into) the simulation engine — the Risk
        # Engine must keep running even if the simulator is disabled or swapped for a real
        # telemetry feed. See app/risk_engine/engine/scheduler.py for the isolation rationale.
        from app.database.session import AsyncSessionLocal as RiskSessionLocal
        from app.risk_engine.engine.scheduler import RiskScheduler

        scheduler = RiskScheduler(
            RiskSessionLocal,
            interval_seconds=settings.risk_evaluation_interval_seconds,
        )
        risk_task = asyncio.create_task(scheduler.run())

    yield

    if simulation_task is not None:
        simulation_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await simulation_task

    if risk_task is not None:
        risk_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await risk_task


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
