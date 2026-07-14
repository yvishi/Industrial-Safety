"""
Standalone Risk Engine process, for running the scheduler outside the API server:

    uv run python -m app.risk_engine.runner

The same scheduler also runs embedded in FastAPI when RISK_ENGINE_ENABLED=true (the default);
use this entrypoint if you want the API and the Risk Engine in separate processes — e.g. so
retuning rule config or restarting the engine never affects request-serving. Mirrors
app/simulation/runner.py's standalone-process pattern.
"""

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import AsyncSessionLocal
from app.risk_engine.engine.scheduler import RiskScheduler


async def main() -> None:
    configure_logging()
    settings = get_settings()
    scheduler = RiskScheduler(
        AsyncSessionLocal,
        interval_seconds=settings.risk_evaluation_interval_seconds,
    )
    await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
