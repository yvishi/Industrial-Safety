"""
Standalone simulator process, for running the engine outside the API server:

    uv run python -m app.simulation.runner

The same engine also runs embedded in FastAPI when SIMULATION_ENABLED=true; use this
entrypoint if you want the API and the simulator in separate processes.
"""

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import AsyncSessionLocal
from app.simulation.engine import SimulationEngine


async def main() -> None:
    configure_logging()
    settings = get_settings()
    engine = SimulationEngine(
        AsyncSessionLocal,
        tick_seconds=settings.simulation_tick_seconds,
        retention_hours=settings.sensor_reading_retention_hours,
    )
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
