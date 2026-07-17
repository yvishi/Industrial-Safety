"""
Independent background evaluator for the Compound Risk Engine — deliberately NOT hooked into
the simulation engine's tick loop. Two reasons: (1) the simulator explicitly stands in for
real telemetry ingestion and must be swappable/disableable without silently taking risk
assessment down with it; (2) persistence is change-gated (see RiskService), so re-evaluating
every 5s simulation tick would mostly be wasted no-op work. Reads/writes the database
independently on its own interval, matching this codebase's established pattern of the DB as
the single source of truth between decoupled subsystems.

Also reconciles the Recommendation Engine and the Correlation Engine (Incident lifecycle) on
the same tick, right after each zone's RiskAssessment is computed — unlike the risk-vs-simulation
split above, there is no analogous reason to decouple either of them onto their own poller: both
are architecturally downstream of RiskAssessment by design, so reconciling inline avoids extra
background tasks and avoids ever reconciling against a stale assessment. Ordering within the
per-zone loop matters: Incident correlation reads the Recommendation Engine's just-reconciled
active set for that same zone, so it must run after recommendation_service.reconcile() returns,
not as a separate pass over facts_by_zone.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.correlation_engine.decide import ThresholdState
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.risk import RiskRepository
from app.repositories.zone import ZoneRepository
from app.risk_engine.config.defaults import DEFAULT_RISK_CONFIG
from app.risk_engine.config.schema import RiskEngineConfig
from app.risk_engine.facts_builder import ZoneFactsBuilder
from app.services.incident import IncidentService
from app.services.recommendation import RecommendationService
from app.services.risk import RiskService

logger = logging.getLogger(__name__)


class RiskScheduler:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        *,
        interval_seconds: float = 15.0,
        config: RiskEngineConfig = DEFAULT_RISK_CONFIG,
    ) -> None:
        self.session_factory = session_factory
        self.interval_seconds = interval_seconds
        self.config = config
        self._running = False
        # Correlation Engine debounce counters, one per zone — owned here (not by
        # IncidentService, which is reconstructed fresh every tick) because this scheduler is
        # the one object that genuinely persists across ticks, the same reason it already owns
        # `_running`. See IncidentService.reconcile()'s docstring.
        self._incident_threshold_states: dict[UUID, ThresholdState] = {}

    async def run(self) -> None:
        logger.info("Risk scheduler started (evaluating every %.1fs)", self.interval_seconds)
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Risk evaluation pass failed")
            await asyncio.sleep(self.interval_seconds)

    async def run_once(self) -> None:
        # Guards against overlapping passes if a pass ever takes longer than interval_seconds.
        # An in-process flag, adequate for this single-process deployment (same assumption the
        # simulation engine already makes) — not safe for a multi-worker deployment.
        if self._running:
            logger.warning("Previous risk evaluation pass still running; skipping this cycle")
            return

        self._running = True
        try:
            async with self.session_factory() as session:
                builder = ZoneFactsBuilder(session)
                facts_by_zone = await builder.build_for_plant(self.config)
                risk_service = RiskService(RiskRepository(session), builder, EventRepository(session), self.config)
                recommendation_service = RecommendationService(
                    RecommendationRepository(session),
                    ZoneRepository(session),
                    EventRepository(session),
                    RiskRepository(session),
                )
                incident_service = IncidentService(
                    IncidentRepository(session),
                    RecommendationRepository(session),
                    EventRepository(session),
                    ZoneRepository(session),
                )

                persisted = 0
                for facts in facts_by_zone.values():
                    assessment, snapshot = await risk_service.evaluate(facts)
                    if snapshot is not None:
                        persisted += 1
                    active_recommendations = await recommendation_service.reconcile(assessment)
                    await incident_service.reconcile(
                        assessment, facts, active_recommendations, self._incident_threshold_states
                    )

                if persisted:
                    logger.info("Risk pass: %d zone snapshot(s) persisted", persisted)
        finally:
            self._running = False
