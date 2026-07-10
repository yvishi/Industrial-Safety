"""
Seeds the database with the Riverbend Refinery — an instance of the crude_oil_refinery
plant type. Zones, equipment, instruments (with their operating ranges) and the worker
roster are materialized from the PlantTypeDefinition (app/plant_types/refinery.py), so the
plant structure has exactly one source of truth. Only the site identity and a short
opening narrative of permits/events are authored here.

Usage (from backend/):
    uv run python -m scripts.seed
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from app.database.session import AsyncSessionLocal
from app.models import Equipment, Event, Permit, Plant, Sensor, Worker, Zone
from app.plant_types import get_plant_type

PLANT_TYPE = "crude_oil_refinery"

PLANT = dict(
    code="RVB-01",
    name="Riverbend Refinery",
    plant_type=PLANT_TYPE,
    description=(
        "A 180,000 bpd crude oil refinery on the Gulf Coast: atmospheric and vacuum "
        "distillation, bulk tank storage, truck loading, and full site utilities."
    ),
    city="Riverbend",
    region="TX",
    country="USA",
    latitude=29.7604,
    longitude=-95.3698,
    timezone="America/Chicago",
)


def days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


def days_from_now(n: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=n)


# A believable opening state for the permit board; the simulator takes over from here.
PERMITS = [
    dict(
        permit_number="PTW-2026-0101", permit_type="hot_work", zone="CDU-100", equipment="100-E-101",
        required_isolation="gas_test_and_fire_watch",
        description="Weld repair on Crude Preheat Exchanger (100-E-101) shell nozzle.",
        requested_by="EMP-1015", approved_by="EMP-1002", status="active",
        valid_from=days_ago(0), valid_until=days_from_now(2),
    ),
    dict(
        permit_number="PTW-2026-0102", permit_type="confined_space", zone="TKF-01", equipment="TK-301",
        required_isolation="blind_purge_and_gas_test",
        description="Internal inspection of Crude Storage Tank 1 ahead of scheduled turnaround.",
        requested_by="EMP-1015", approved_by="EMP-1003", status="approved",
        valid_from=days_from_now(1), valid_until=days_from_now(3),
    ),
    dict(
        permit_number="PTW-2026-0103", permit_type="lockout_tagout", zone="PMP-01", equipment="P-501B",
        required_isolation="lockout_tagout",
        description="Mechanical seal replacement on Product Transfer Pump B (P-501B).",
        requested_by="EMP-1013", approved_by="EMP-1004", status="active",
        valid_from=days_ago(1), valid_until=days_from_now(1),
    ),
    dict(
        permit_number="PTW-2026-0104", permit_type="working_at_height", zone="FLR-01", equipment="FS-701",
        required_isolation="none",
        description="Flare tip pilot inspection via elevated platform.",
        requested_by="EMP-1020", approved_by=None, status="pending_approval",
        valid_from=None, valid_until=None,
    ),
    dict(
        permit_number="PTW-2026-0105", permit_type="line_breaking", zone="LDB-01", equipment="LA-601",
        required_isolation="depressurize_drain_and_blind",
        description="Swivel joint replacement on Truck Loading Arm No. 1 (LA-601).",
        requested_by="EMP-1014", approved_by="EMP-1003", status="closed",
        valid_from=days_ago(10), valid_until=days_ago(6),
    ),
    dict(
        permit_number="PTW-2026-0106", permit_type="electrical", zone="UTL-01", equipment="K-401",
        required_isolation="electrical_isolation",
        description="Motor control center inspection for Instrument Air Compressor A (K-401).",
        requested_by="EMP-1018", approved_by="EMP-1002", status="expired",
        valid_from=days_ago(20), valid_until=days_ago(18),
    ),
    dict(
        permit_number="PTW-2026-0107", permit_type="hot_work", zone="VDU-200", equipment="200-H-201",
        required_isolation="gas_test_and_fire_watch",
        description="Refractory repair on Vacuum Charge Heater (200-H-201).",
        requested_by="EMP-1015", approved_by=None, status="draft",
        valid_from=None, valid_until=None,
    ),
    dict(
        permit_number="PTW-2026-0108", permit_type="confined_space", zone="FLR-01", equipment="D-701",
        required_isolation="blind_purge_and_gas_test",
        description="Flare knock-out drum entry — withdrawn pending gas-test re-assessment.",
        requested_by="EMP-1020", approved_by="EMP-1004", status="revoked",
        valid_from=days_ago(5), valid_until=days_ago(4),
    ),
]

EVENTS = [
    dict(event_type="worker_check_in", title="Day shift check-in", zone="CCR-01", equipment=None, permit=None, recorded_by="EMP-1004", occurred_at=days_ago(0)),
    dict(event_type="worker_check_in", title="Unit 100 field round started", zone="CDU-100", equipment=None, permit=None, recorded_by="EMP-1010", occurred_at=days_ago(0)),
    dict(event_type="worker_check_out", title="Night shift check-out", zone="VDU-200", equipment=None, permit=None, recorded_by="EMP-1011", occurred_at=days_ago(1)),
    dict(event_type="equipment_status_change", title="Crude Charge Pump B placed on standby", zone="CDU-100", equipment="100-P-101B", permit=None, recorded_by="EMP-1010", occurred_at=days_ago(2)),
    dict(event_type="equipment_status_change", title="Instrument Air Compressor B placed on standby", zone="UTL-01", equipment="K-402", permit=None, recorded_by="EMP-1019", occurred_at=days_ago(3)),
    dict(event_type="maintenance_logged", title="Exchanger bundle cleaning completed", zone="CDU-100", equipment="100-E-101", permit=None, recorded_by="EMP-1015", occurred_at=days_ago(7)),
    dict(event_type="general", title="Quarterly refinery safety walkthrough completed", zone="CCR-01", equipment=None, permit=None, recorded_by="EMP-1002", occurred_at=days_ago(4)),
    dict(event_type="general", title="Weekly fire pump test run completed", zone="FWS-01", equipment="P-802", permit=None, recorded_by="EMP-1002", occurred_at=days_ago(2)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0101 submitted", zone="CDU-100", equipment="100-E-101", permit="PTW-2026-0101", recorded_by="EMP-1015", occurred_at=days_ago(1)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0101 approved", zone="CDU-100", equipment="100-E-101", permit="PTW-2026-0101", recorded_by="EMP-1002", occurred_at=days_ago(0)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0102 submitted", zone="TKF-01", equipment="TK-301", permit="PTW-2026-0102", recorded_by="EMP-1015", occurred_at=days_ago(2)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0102 approved", zone="TKF-01", equipment="TK-301", permit="PTW-2026-0102", recorded_by="EMP-1003", occurred_at=days_ago(1)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0103 submitted", zone="PMP-01", equipment="P-501B", permit="PTW-2026-0103", recorded_by="EMP-1013", occurred_at=days_ago(2)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0103 approved", zone="PMP-01", equipment="P-501B", permit="PTW-2026-0103", recorded_by="EMP-1004", occurred_at=days_ago(1)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0104 submitted", zone="FLR-01", equipment="FS-701", permit="PTW-2026-0104", recorded_by="EMP-1020", occurred_at=days_ago(0)),
    dict(event_type="permit_closed", title="Permit PTW-2026-0105 closed out", zone="LDB-01", equipment="LA-601", permit="PTW-2026-0105", recorded_by="EMP-1014", occurred_at=days_ago(6)),
    dict(event_type="general", title="Permit PTW-2026-0108 revoked pending re-assessment", zone="FLR-01", equipment="D-701", permit="PTW-2026-0108", recorded_by="EMP-1004", occurred_at=days_ago(4)),
]


async def seed() -> None:
    definition = get_plant_type(PLANT_TYPE)

    async with AsyncSessionLocal() as session:
        plant = Plant(**PLANT)
        session.add(plant)
        await session.flush()

        zones_by_code: dict[str, Zone] = {}
        equipment_by_tag: dict[str, Equipment] = {}
        sensor_count = 0

        for zone_template in definition.zones:
            zone = Zone(
                plant_id=plant.id,
                code=zone_template.code,
                name=zone_template.name,
                zone_type=zone_template.zone_type,
                zone_category=zone_template.zone_category.value,
                description=zone_template.description,
                grid_row=zone_template.grid_row,
                grid_col=zone_template.grid_col,
            )
            session.add(zone)
            zones_by_code[zone_template.code] = zone
            await session.flush()

            for equipment_template in zone_template.equipment:
                equipment = Equipment(
                    zone_id=zone.id,
                    tag_number=equipment_template.tag,
                    name=equipment_template.name,
                    equipment_type=equipment_template.equipment_type,
                    status=equipment_template.status,
                    criticality=equipment_template.criticality,
                    manufacturer=equipment_template.manufacturer,
                )
                session.add(equipment)
                equipment_by_tag[equipment_template.tag] = equipment
            await session.flush()

            for sensor_template in zone_template.sensors:
                type_spec = definition.sensor_types[sensor_template.sensor_type]
                sensor = Sensor(
                    zone_id=zone.id,
                    equipment_id=(
                        equipment_by_tag[sensor_template.equipment_tag].id
                        if sensor_template.equipment_tag
                        else None
                    ),
                    tag_number=sensor_template.tag,
                    sensor_type=sensor_template.sensor_type,
                    unit_of_measure=sensor_template.unit or type_spec.unit,
                    installation_date=date(2024, 1, 15),
                    normal_min=sensor_template.range.normal_min,
                    normal_max=sensor_template.range.normal_max,
                    warning_min=sensor_template.range.warning_min,
                    warning_max=sensor_template.range.warning_max,
                    critical_min=sensor_template.range.critical_min,
                    critical_max=sensor_template.range.critical_max,
                    sampling_interval_seconds=(
                        sensor_template.sampling_interval_seconds
                        or type_spec.sampling_interval_seconds
                    ),
                )
                session.add(sensor)
                sensor_count += 1
        await session.flush()

        workers_by_employee_id: dict[str, Worker] = {}
        for worker_template in definition.workers:
            zone_id = (
                zones_by_code[worker_template.zone_code].id if worker_template.zone_code else None
            )
            worker = Worker(
                employee_id=worker_template.employee_id,
                first_name=worker_template.first_name,
                last_name=worker_template.last_name,
                role=worker_template.role,
                shift=worker_template.shift,
                employment_status=worker_template.employment_status,
                primary_zone_id=zone_id,
                current_zone_id=zone_id,  # everyone starts at their station
            )
            session.add(worker)
            workers_by_employee_id[worker.employee_id] = worker
        await session.flush()

        permits_by_number: dict[str, Permit] = {}
        for data in PERMITS:
            data = dict(data)
            zone_code = data.pop("zone")
            equipment_tag = data.pop("equipment")
            requested_by_emp = data.pop("requested_by")
            approved_by_emp = data.pop("approved_by")
            permit = Permit(
                zone_id=zones_by_code[zone_code].id,
                equipment_id=equipment_by_tag[equipment_tag].id if equipment_tag else None,
                requested_by_id=workers_by_employee_id[requested_by_emp].id,
                approved_by_id=workers_by_employee_id[approved_by_emp].id if approved_by_emp else None,
                **data,
            )
            session.add(permit)
            permits_by_number[permit.permit_number] = permit
        await session.flush()

        for data in EVENTS:
            data = dict(data)
            zone_code = data.pop("zone")
            equipment_tag = data.pop("equipment")
            permit_number = data.pop("permit")
            recorded_by_emp = data.pop("recorded_by")
            event = Event(
                zone_id=zones_by_code[zone_code].id if zone_code else None,
                equipment_id=equipment_by_tag[equipment_tag].id if equipment_tag else None,
                permit_id=permits_by_number[permit_number].id if permit_number else None,
                recorded_by_id=workers_by_employee_id[recorded_by_emp].id if recorded_by_emp else None,
                **data,
            )
            session.add(event)

        await session.commit()

    print(
        f"Seeded {PLANT['name']} ({definition.label}): {len(definition.zones)} zones, "
        f"{len(definition.workers)} workers, {len(equipment_by_tag)} equipment, "
        f"{sensor_count} sensors, {len(PERMITS)} permits, {len(EVENTS)} events."
    )


if __name__ == "__main__":
    asyncio.run(seed())
