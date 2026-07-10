import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Equipment, Permit, Plant, Sensor, SensorReading, Worker, Zone
from app.simulation.engine import SimulationEngine

VALID_EQUIPMENT_STATUSES = {"operational", "standby", "under_maintenance", "decommissioned"}

# Physical clamps the engine derives for the seeded temperature instrument below:
# ranges 340-365 normal / 375 warning / 390 critical, span 25 -> hard band 333.75..396.25.
TT_HARD_MIN = 340 - 0.25 * 25
TT_HARD_MAX = 390 + 0.25 * 25


async def _seed_minimal_plant(session: AsyncSession) -> None:
    plant = Plant(code="TST-01", name="Test Refinery", plant_type="crude_oil_refinery")
    session.add(plant)
    await session.flush()

    zone_a = Zone(
        plant_id=plant.id, code="CDU-1", name="Crude Unit", zone_type="crude_distillation",
        zone_category="process", grid_row=1, grid_col=1,
    )
    zone_b = Zone(
        plant_id=plant.id, code="TKF-1", name="Tank Farm", zone_type="tank_farm",
        zone_category="storage", grid_row=1, grid_col=2,
    )
    session.add_all([zone_a, zone_b])
    await session.flush()

    worker = Worker(
        employee_id="EMP-1", first_name="Test", last_name="Operator",
        role="field_operator", primary_zone_id=zone_a.id, current_zone_id=zone_a.id,
    )
    pump = Equipment(zone_id=zone_a.id, tag_number="P-1", name="Charge Pump", equipment_type="pump")
    sensor = Sensor(
        zone_id=zone_a.id, equipment_id=None, tag_number="TT-1", sensor_type="temperature",
        unit_of_measure="°C", normal_min=340, normal_max=365, warning_max=375, critical_max=390,
        sampling_interval_seconds=0,  # always due, so every engine tick produces a reading
    )
    session.add_all([worker, pump, sensor])
    await session.flush()

    permit = Permit(
        zone_id=zone_a.id, permit_number="PTW-2026-0001", permit_type="hot_work",
        required_isolation="gas_test_and_fire_watch", status="draft", requested_by_id=worker.id,
    )
    session.add(permit)
    await session.commit()


async def test_tick_produces_readings_and_valid_state(
    session_factory: async_sessionmaker, db_session: AsyncSession
) -> None:
    await _seed_minimal_plant(db_session)

    engine = SimulationEngine(session_factory, rng=random.Random(42))
    await engine.tick()
    await engine.tick()

    async with session_factory() as session:
        sensor = (await session.execute(select(Sensor))).scalars().one()
        assert sensor.last_value is not None
        assert sensor.last_reading_at is not None
        assert TT_HARD_MIN <= sensor.last_value <= TT_HARD_MAX

        readings = (await session.execute(select(SensorReading))).scalars().all()
        assert len(readings) == 2  # one per tick

        equipment = (await session.execute(select(Equipment))).scalars().one()
        assert equipment.status in VALID_EQUIPMENT_STATUSES

        worker = (await session.execute(select(Worker))).scalars().one()
        zone_ids = {z.id for z in (await session.execute(select(Zone))).scalars().all()}
        assert worker.current_zone_id in zone_ids


async def test_many_ticks_keep_values_in_band_and_permits_progress(
    session_factory: async_sessionmaker, db_session: AsyncSession
) -> None:
    await _seed_minimal_plant(db_session)

    engine = SimulationEngine(session_factory, rng=random.Random(7))
    for _ in range(200):
        await engine.tick()

    async with session_factory() as session:
        sensor = (await session.execute(select(Sensor))).scalars().one()
        assert TT_HARD_MIN <= sensor.last_value <= TT_HARD_MAX

        # Over 200 ticks the draft permit should have moved (p=0.01/tick to submit).
        permits = (await session.execute(select(Permit))).scalars().all()
        statuses = {p.status for p in permits}
        assert statuses - {"draft"}, f"permit never progressed: {statuses}"

        # Simulator-drafted permits must carry the plant type's isolation standard.
        assert all(p.required_isolation for p in permits)


async def test_sampling_interval_gates_readings(
    session_factory: async_sessionmaker, db_session: AsyncSession
) -> None:
    await _seed_minimal_plant(db_session)

    async with session_factory() as session:
        sensor = (await session.execute(select(Sensor))).scalars().one()
        sensor.sampling_interval_seconds = 3600  # only the first tick should sample
        await session.commit()

    engine = SimulationEngine(session_factory, rng=random.Random(3))
    for _ in range(5):
        await engine.tick()

    async with session_factory() as session:
        readings = (await session.execute(select(SensorReading))).scalars().all()
        assert len(readings) == 1
