"""
Seeds the database with a believable fictional petrochemical plant: one plant, its 8 zones
(mirroring the frontend's Riverbend Processing Facility exactly), workers, equipment, sensors,
permits, and a activity log. Structural/identity data only — no live telemetry, no computed
risk/state.

Usage (from backend/):
    uv run python -m scripts.seed
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from app.database.session import AsyncSessionLocal
from app.models import Equipment, Event, Permit, Plant, Sensor, Worker, Zone


def days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


def days_from_now(n: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=n)


ZONES = [
    dict(
        code="CR-01",
        name="Central Control Room",
        zone_type="control_room",
        description="Centralized monitoring and process control for all site operations.",
        grid_row=1,
        grid_col=1,
    ),
    dict(
        code="PU-01",
        name="Crude Distillation Unit",
        zone_type="processing_unit",
        description="Atmospheric distillation and primary hydrocarbon separation.",
        grid_row=1,
        grid_col=2,
    ),
    dict(
        code="PU-02",
        name="Catalytic Reformer Unit",
        zone_type="processing_unit",
        description="Converts naphtha into high-octane reformate via catalytic reforming.",
        grid_row=1,
        grid_col=3,
    ),
    dict(
        code="UT-01",
        name="Utilities & Steam Plant",
        zone_type="utilities",
        description="Steam generation, compressed air, and site-wide power distribution.",
        grid_row=1,
        grid_col=4,
    ),
    dict(
        code="TF-01",
        name="Tank Farm",
        zone_type="tank_farm",
        description="Bulk storage for crude feedstock and finished petroleum products.",
        grid_row=2,
        grid_col=1,
    ),
    dict(
        code="PS-01",
        name="Pump Station",
        zone_type="pump_station",
        description="Transfer pumping between storage, process units, and loading systems.",
        grid_row=2,
        grid_col=2,
    ),
    dict(
        code="LR-01",
        name="Loading Rack",
        zone_type="loading_rack",
        description="Truck and rail loading for finished product distribution.",
        grid_row=2,
        grid_col=3,
    ),
    dict(
        code="FS-01",
        name="Flare Stack",
        zone_type="flare_stack",
        description="Emergency pressure relief and combustion of process off-gases.",
        grid_row=2,
        grid_col=4,
    ),
]

WORKERS = [
    dict(employee_id="EMP-1001", first_name="Elena", last_name="Martinez", role="plant_manager", zone="CR-01", shift="day"),
    dict(employee_id="EMP-1002", first_name="Marcus", last_name="Whitfield", role="safety_officer", zone="CR-01", shift="day"),
    dict(employee_id="EMP-1003", first_name="Priya", last_name="Chandrasekaran", role="safety_officer", zone="CR-01", shift="night"),
    dict(employee_id="EMP-1004", first_name="Daniel", last_name="Osei", role="shift_supervisor", zone="CR-01", shift="day"),
    dict(employee_id="EMP-1005", first_name="Grace", last_name="Lindqvist", role="shift_supervisor", zone="CR-01", shift="night"),
    dict(employee_id="EMP-1006", first_name="Robert", last_name="Kim", role="shift_supervisor", zone="CR-01", shift="swing"),
    dict(employee_id="EMP-1007", first_name="Amara", last_name="Okafor", role="operations_director", zone=None, shift="day"),
    dict(employee_id="EMP-1008", first_name="Tomas", last_name="Reyes", role="process_operator", zone="PU-01", shift="day"),
    dict(employee_id="EMP-1009", first_name="Hannah", last_name="Fitzgerald", role="process_operator", zone="PU-02", shift="night"),
    dict(employee_id="EMP-1010", first_name="Ibrahim", last_name="Al-Sayed", role="process_operator", zone="TF-01", shift="day"),
    dict(employee_id="EMP-1011", first_name="Chloe", last_name="Bergstrom", role="process_operator", zone="PS-01", shift="swing"),
    dict(employee_id="EMP-1012", first_name="Nathaniel", last_name="Voss", role="process_operator", zone="LR-01", shift="day"),
    dict(employee_id="EMP-1013", first_name="Sofia", last_name="Delacroix", role="maintenance_technician", zone="UT-01", shift="day"),
    dict(employee_id="EMP-1014", first_name="Jamal", last_name="Whitaker", role="maintenance_technician", zone="PU-01", shift="night", employment_status="on_leave"),
    dict(employee_id="EMP-1015", first_name="Wei", last_name="Chen", role="maintenance_technician", zone="FS-01", shift="day"),
    dict(employee_id="EMP-1016", first_name="Diego", last_name="Fernandez", role="contractor", zone="LR-01", shift="day", employment_status="contractor"),
]

EQUIPMENT = [
    dict(tag_number="DCS-101", name="Distributed Control System Cabinet", equipment_type="instrument", zone="CR-01"),
    dict(tag_number="P-101A", name="Crude Feed Pump A", equipment_type="pump", zone="PU-01", manufacturer="Flowserve"),
    dict(tag_number="E-101", name="Crude Preheat Exchanger", equipment_type="heat_exchanger", zone="PU-01"),
    dict(tag_number="V-101", name="Atmospheric Distillation Column", equipment_type="vessel", zone="PU-01", criticality="safety_critical"),
    dict(tag_number="R-201", name="Catalytic Reformer Reactor", equipment_type="reactor", zone="PU-02", criticality="safety_critical"),
    dict(tag_number="F-201", name="Reformer Charge Heater", equipment_type="furnace", zone="PU-02"),
    dict(tag_number="C-201", name="Recycle Gas Compressor", equipment_type="compressor", zone="PU-02", manufacturer="Ingersoll Rand"),
    dict(tag_number="B-301", name="Package Boiler No.1", equipment_type="furnace", zone="UT-01"),
    dict(tag_number="K-301", name="Instrument Air Compressor", equipment_type="compressor", zone="UT-01"),
    dict(tag_number="T-401", name="Crude Storage Tank 1", equipment_type="tank", zone="TF-01", criticality="high"),
    dict(tag_number="T-402", name="Finished Product Tank 1", equipment_type="tank", zone="TF-01", status="under_maintenance"),
    dict(tag_number="P-501A", name="Main Transfer Pump A", equipment_type="pump", zone="PS-01"),
    dict(tag_number="P-501B", name="Main Transfer Pump B", equipment_type="pump", zone="PS-01", status="standby"),
    dict(tag_number="LV-601", name="Truck Loading Arm Valve", equipment_type="valve", zone="LR-01"),
    dict(tag_number="LV-602", name="Rail Loading Arm Valve", equipment_type="valve", zone="LR-01"),
    dict(tag_number="FS-701", name="Main Flare Stack", equipment_type="vessel", zone="FS-01", criticality="safety_critical"),
]

SENSORS = [
    dict(tag_number="TT-101", sensor_type="temperature", unit_of_measure="C", zone="PU-01", equipment="E-101"),
    dict(tag_number="PT-101", sensor_type="pressure", unit_of_measure="psi", zone="PU-01", equipment="V-101"),
    dict(tag_number="LT-101", sensor_type="level", unit_of_measure="%", zone="PU-01", equipment="V-101"),
    dict(tag_number="GD-101", sensor_type="gas_detection", unit_of_measure="ppm", zone="PU-01", equipment=None),
    dict(tag_number="TT-201", sensor_type="temperature", unit_of_measure="C", zone="PU-02", equipment="R-201"),
    dict(tag_number="PT-201", sensor_type="pressure", unit_of_measure="psi", zone="PU-02", equipment="R-201"),
    dict(tag_number="FT-201", sensor_type="flow", unit_of_measure="m3/h", zone="PU-02", equipment="C-201"),
    dict(tag_number="GD-201", sensor_type="gas_detection", unit_of_measure="ppm", zone="PU-02", equipment=None),
    dict(tag_number="PT-301", sensor_type="pressure", unit_of_measure="psi", zone="UT-01", equipment="B-301"),
    dict(tag_number="FT-301", sensor_type="flow", unit_of_measure="m3/h", zone="UT-01", equipment="K-301"),
    dict(tag_number="VT-301", sensor_type="vibration", unit_of_measure="mm/s", zone="UT-01", equipment="K-301"),
    dict(tag_number="LT-401", sensor_type="level", unit_of_measure="%", zone="TF-01", equipment="T-401"),
    dict(tag_number="TT-401", sensor_type="temperature", unit_of_measure="C", zone="TF-01", equipment="T-401"),
    dict(tag_number="LT-402", sensor_type="level", unit_of_measure="%", zone="TF-01", equipment="T-402"),
    dict(tag_number="GD-401", sensor_type="gas_detection", unit_of_measure="ppm", zone="TF-01", equipment=None),
    dict(tag_number="PT-501", sensor_type="pressure", unit_of_measure="psi", zone="PS-01", equipment="P-501A"),
    dict(tag_number="VT-501", sensor_type="vibration", unit_of_measure="mm/s", zone="PS-01", equipment="P-501A"),
    dict(tag_number="VT-502", sensor_type="vibration", unit_of_measure="mm/s", zone="PS-01", equipment="P-501B"),
    dict(tag_number="FT-601", sensor_type="flow", unit_of_measure="m3/h", zone="LR-01", equipment=None),
    dict(tag_number="GD-601", sensor_type="gas_detection", unit_of_measure="ppm", zone="LR-01", equipment=None),
    dict(tag_number="TT-701", sensor_type="temperature", unit_of_measure="C", zone="FS-01", equipment="FS-701"),
    dict(tag_number="GD-701", sensor_type="gas_detection", unit_of_measure="ppm", zone="FS-01", equipment=None),
    dict(tag_number="SD-001", sensor_type="smoke", unit_of_measure="% obs/m", zone="CR-01", equipment=None),
]

PERMITS = [
    dict(
        permit_number="PTW-2026-0101", permit_type="hot_work", zone="PU-01", equipment="P-101A",
        description="Weld repair on feed pump discharge flange.",
        requested_by="EMP-1014", approved_by="EMP-1002", status="active",
        valid_from=days_ago(0), valid_until=days_from_now(2),
    ),
    dict(
        permit_number="PTW-2026-0102", permit_type="confined_space", zone="TF-01", equipment="T-401",
        description="Internal tank inspection ahead of scheduled turnaround.",
        requested_by="EMP-1013", approved_by="EMP-1003", status="approved",
        valid_from=days_from_now(1), valid_until=days_from_now(3),
    ),
    dict(
        permit_number="PTW-2026-0103", permit_type="lockout_tagout", zone="PS-01", equipment="P-501B",
        description="Mechanical seal replacement on standby transfer pump.",
        requested_by="EMP-1011", approved_by="EMP-1004", status="active",
        valid_from=days_ago(1), valid_until=days_from_now(1),
    ),
    dict(
        permit_number="PTW-2026-0104", permit_type="working_at_height", zone="FS-01", equipment="FS-701",
        description="Flare tip inspection via elevated platform.",
        requested_by="EMP-1015", approved_by=None, status="pending_approval",
        valid_from=None, valid_until=None,
    ),
    dict(
        permit_number="PTW-2026-0105", permit_type="excavation", zone="TF-01", equipment=None,
        description="Excavation for tank farm secondary containment repair.",
        requested_by="EMP-1016", approved_by="EMP-1003", status="closed",
        valid_from=days_ago(10), valid_until=days_ago(6),
    ),
    dict(
        permit_number="PTW-2026-0106", permit_type="electrical", zone="UT-01", equipment="K-301",
        description="Motor control center inspection on instrument air compressor.",
        requested_by="EMP-1013", approved_by="EMP-1002", status="expired",
        valid_from=days_ago(20), valid_until=days_ago(18),
    ),
    dict(
        permit_number="PTW-2026-0107", permit_type="hot_work", zone="PU-02", equipment="F-201",
        description="Refractory repair on reformer charge heater.",
        requested_by="EMP-1014", approved_by=None, status="draft",
        valid_from=None, valid_until=None,
    ),
    dict(
        permit_number="PTW-2026-0108", permit_type="confined_space", zone="LR-01", equipment=None,
        description="Loading rack sump entry — withdrawn pending re-assessment.",
        requested_by="EMP-1012", approved_by="EMP-1004", status="revoked",
        valid_from=days_ago(5), valid_until=days_ago(4),
    ),
]

EVENTS = [
    dict(event_type="worker_check_in", title="Shift check-in", zone="CR-01", equipment=None, permit=None, recorded_by="EMP-1004", occurred_at=days_ago(0)),
    dict(event_type="worker_check_in", title="Shift check-in", zone="PU-01", equipment=None, permit=None, recorded_by="EMP-1008", occurred_at=days_ago(0)),
    dict(event_type="worker_check_out", title="Shift check-out", zone="PU-02", equipment=None, permit=None, recorded_by="EMP-1009", occurred_at=days_ago(1)),
    dict(event_type="equipment_status_change", title="Tank taken offline for maintenance", zone="TF-01", equipment="T-402", permit=None, recorded_by="EMP-1013", occurred_at=days_ago(3)),
    dict(event_type="equipment_status_change", title="Pump B placed on standby", zone="PS-01", equipment="P-501B", permit=None, recorded_by="EMP-1011", occurred_at=days_ago(2)),
    dict(event_type="maintenance_logged", title="Routine exchanger cleaning completed", zone="PU-01", equipment="E-101", permit=None, recorded_by="EMP-1014", occurred_at=days_ago(7)),
    dict(event_type="general", title="Quarterly safety walkthrough completed", zone="CR-01", equipment=None, permit=None, recorded_by="EMP-1002", occurred_at=days_ago(4)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0101 submitted", zone="PU-01", equipment="P-101A", permit="PTW-2026-0101", recorded_by="EMP-1014", occurred_at=days_ago(1)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0101 approved", zone="PU-01", equipment="P-101A", permit="PTW-2026-0101", recorded_by="EMP-1002", occurred_at=days_ago(0)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0102 submitted", zone="TF-01", equipment="T-401", permit="PTW-2026-0102", recorded_by="EMP-1013", occurred_at=days_ago(2)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0102 approved", zone="TF-01", equipment="T-401", permit="PTW-2026-0102", recorded_by="EMP-1003", occurred_at=days_ago(1)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0103 submitted", zone="PS-01", equipment="P-501B", permit="PTW-2026-0103", recorded_by="EMP-1011", occurred_at=days_ago(2)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0103 approved", zone="PS-01", equipment="P-501B", permit="PTW-2026-0103", recorded_by="EMP-1004", occurred_at=days_ago(1)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0104 submitted", zone="FS-01", equipment="FS-701", permit="PTW-2026-0104", recorded_by="EMP-1015", occurred_at=days_ago(0)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0105 submitted", zone="TF-01", equipment=None, permit="PTW-2026-0105", recorded_by="EMP-1016", occurred_at=days_ago(11)),
    dict(event_type="permit_approved", title="Permit PTW-2026-0105 approved", zone="TF-01", equipment=None, permit="PTW-2026-0105", recorded_by="EMP-1003", occurred_at=days_ago(10)),
    dict(event_type="permit_closed", title="Permit PTW-2026-0105 closed out", zone="TF-01", equipment=None, permit="PTW-2026-0105", recorded_by="EMP-1016", occurred_at=days_ago(6)),
    dict(event_type="permit_issued", title="Permit PTW-2026-0108 submitted", zone="LR-01", equipment=None, permit="PTW-2026-0108", recorded_by="EMP-1012", occurred_at=days_ago(5)),
    dict(event_type="general", title="Permit PTW-2026-0108 revoked pending re-assessment", zone="LR-01", equipment=None, permit="PTW-2026-0108", recorded_by="EMP-1004", occurred_at=days_ago(4)),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        plant = Plant(
            code="RPF-01",
            name="Riverbend Processing Facility",
            description="A single-site crude processing and product distribution facility.",
            city="Riverbend",
            region="TX",
            country="USA",
            latitude=29.7604,
            longitude=-95.3698,
            timezone="America/Chicago",
        )
        session.add(plant)
        await session.flush()

        zones_by_code: dict[str, Zone] = {}
        for data in ZONES:
            zone = Zone(plant_id=plant.id, **data)
            session.add(zone)
            zones_by_code[data["code"]] = zone
        await session.flush()

        workers_by_employee_id: dict[str, Worker] = {}
        for data in WORKERS:
            zone_code = data.pop("zone")
            zone_id = zones_by_code[zone_code].id if zone_code else None
            worker = Worker(
                primary_zone_id=zone_id,
                current_zone_id=zone_id,  # everyone starts at their station
                employment_status=data.pop("employment_status", "active"),
                **data,
            )
            session.add(worker)
            workers_by_employee_id[worker.employee_id] = worker
        await session.flush()

        equipment_by_tag: dict[str, Equipment] = {}
        for data in EQUIPMENT:
            zone_code = data.pop("zone")
            equipment = Equipment(zone_id=zones_by_code[zone_code].id, **data)
            session.add(equipment)
            equipment_by_tag[equipment.tag_number] = equipment
        await session.flush()

        for data in SENSORS:
            zone_code = data.pop("zone")
            equipment_tag = data.pop("equipment")
            sensor = Sensor(
                zone_id=zones_by_code[zone_code].id,
                equipment_id=equipment_by_tag[equipment_tag].id if equipment_tag else None,
                installation_date=date(2024, 1, 15),
                **data,
            )
            session.add(sensor)
        await session.flush()

        permits_by_number: dict[str, Permit] = {}
        for data in PERMITS:
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
        f"Seeded 1 plant, {len(ZONES)} zones, {len(WORKERS)} workers, {len(EQUIPMENT)} equipment, "
        f"{len(SENSORS)} sensors, {len(PERMITS)} permits, {len(EVENTS)} events."
    )


if __name__ == "__main__":
    asyncio.run(seed())
