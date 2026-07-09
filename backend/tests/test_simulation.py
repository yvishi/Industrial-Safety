import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Equipment, Permit, Plant, Sensor, SensorReading, Worker, Zone
from app.simulation.engine import SimulationEngine

VALID_EQUIPMENT_STATUSES = {"operational", "standby", "under_maintenance", "decommissioned"}


async def _seed_minimal_plant(session: AsyncSession) -> None:
    plant = Plant(code="TST-01", name="Test Plant")
    session.add(plant)
    await session.flush()

    zone_a = Zone(plant_id=plant.id, code="ZA", name="Zone A", zone_type="processing_unit", grid_row=1, grid_col=1)
    zone_b = Zone(plant_id=plant.id, code="ZB", name="Zone B", zone_type="tank_farm", grid_row=1, grid_col=2)
    session.add_all([zone_a, zone_b])
    await session.flush()

    worker = Worker(
        employee_id="EMP-1", first_name="Test", last_name="Operator",
        role="process_operator", primary_zone_id=zone_a.id, current_zone_id=zone_a.id,
    )
    pump = Equipment(zone_id=zone_a.id, tag_number="P-1", name="Test Pump", equipment_type="pump")
    sensor = Sensor(zone_id=zone_a.id, equipment_id=None, tag_number="TT-1", sensor_type="temperature", unit_of_measure="C")
    session.add_all([worker, pump, sensor])
    await session.flush()

    permit = Permit(
        zone_id=zone_a.id, permit_number="PTW-2026-0001", permit_type="hot_work",
        status="draft", requested_by_id=worker.id,
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
        assert 15.0 <= sensor.last_value <= 260.0  # within the temperature profile clamps

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
        assert 15.0 <= sensor.last_value <= 260.0

        # Over 200 ticks the draft permit should have moved (p=0.01/tick to submit).
        permits = (await session.execute(select(Permit))).scalars().all()
        statuses = {p.status for p in permits}
        assert statuses - {"draft"}, f"permit never progressed: {statuses}"
