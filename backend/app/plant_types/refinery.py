"""
Plant Type: Crude Oil Refinery.

The complete domain definition for a fuels refinery — process units, tank storage, product
movement, utilities, and the layered safety systems around them. Operating ranges are loosely
grounded in real practice: H2S alarms at 10/20 ppm follow common occupational limits, LEL
alarms at 10/25 %LEL are typical detector setpoints, vibration bands follow ISO 10816, and
unit temperatures/pressures sit in credible ranges for atmospheric and vacuum distillation.

Zone grid = simplified site plot plan (drives the overview layout and worker movement):

    row 1:  Control Room | CDU (Unit 100) | VDU (Unit 200) | Flare & Relief
    row 2:  Workshop     | Pump House     | Utilities      | Fire Water
    row 3:  Loading Bay  | Tank Farm      |                |
"""

from app.plant_types.schema import (
    EquipmentBehavior,
    EquipmentTemplate,
    EquipmentTypeSpec,
    OperatingRange,
    PermitTypeSpec,
    PlantTypeDefinition,
    SensorDynamics,
    SensorTemplate,
    SensorTypeSpec,
    SimulationTuning,
    WorkerTemplate,
    ZoneCategory,
    ZoneTemplate,
)

SENSOR_TYPES = {
    "temperature": SensorTypeSpec(
        slug="temperature", label="Temperature", unit="°C",
        theta=0.06, noise_fraction=0.008, excursion_probability=0.00008,
        sampling_interval_seconds=10,
    ),
    "pressure": SensorTypeSpec(
        slug="pressure", label="Pressure", unit="psi",
        theta=0.08, noise_fraction=0.012, excursion_probability=0.00008,
        sampling_interval_seconds=5,
    ),
    "flow": SensorTypeSpec(
        slug="flow", label="Flow Rate", unit="m³/hr",
        dynamics=SensorDynamics.EQUIPMENT_COUPLED,
        theta=0.10, noise_fraction=0.020, sampling_interval_seconds=10,
    ),
    "level": SensorTypeSpec(
        slug="level", label="Level", unit="%",
        theta=0.05, noise_fraction=0.006, sampling_interval_seconds=60,
        hard_min=0.0, hard_max=100.0,
    ),
    "h2s": SensorTypeSpec(
        slug="h2s", label="Hydrogen Sulfide (H₂S)", unit="ppm",
        theta=0.12, noise_fraction=0.040, baseline_fraction=0.15,
        excursion_probability=0.00025, sampling_interval_seconds=5, hard_min=0.0,
    ),
    "combustible_gas": SensorTypeSpec(
        slug="combustible_gas", label="Combustible Gas (LEL)", unit="%LEL",
        theta=0.12, noise_fraction=0.040, baseline_fraction=0.12,
        excursion_probability=0.0002, sampling_interval_seconds=5, hard_min=0.0,
    ),
    "oxygen": SensorTypeSpec(
        slug="oxygen", label="Oxygen (O₂)", unit="%",
        theta=0.15, noise_fraction=0.010, baseline_fraction=0.75,
        sampling_interval_seconds=10, hard_min=0.0, hard_max=25.0,
    ),
    "vibration": SensorTypeSpec(
        slug="vibration", label="Vibration", unit="mm/s",
        dynamics=SensorDynamics.EQUIPMENT_COUPLED,
        theta=0.10, noise_fraction=0.020, sampling_interval_seconds=30, hard_min=0.0,
    ),
    "valve_position": SensorTypeSpec(
        slug="valve_position", label="Valve Position", unit="%",
        theta=0.04, noise_fraction=0.050, sampling_interval_seconds=10,
        hard_min=0.0, hard_max=100.0,
    ),
    "smoke": SensorTypeSpec(
        slug="smoke", label="Smoke Density", unit="% obs/m",
        theta=0.15, noise_fraction=0.030, baseline_fraction=0.10,
        sampling_interval_seconds=5, hard_min=0.0,
    ),
}

EQUIPMENT_TYPES = {
    "pump": EquipmentTypeSpec(slug="pump", label="Pump"),
    "fire_pump": EquipmentTypeSpec(slug="fire_pump", label="Fire Pump"),
    "compressor": EquipmentTypeSpec(slug="compressor", label="Compressor"),
    "heat_exchanger": EquipmentTypeSpec(
        slug="heat_exchanger", label="Heat Exchanger",
        behavior=EquipmentBehavior(p_go_standby=0.0002),
    ),
    "fired_heater": EquipmentTypeSpec(
        slug="fired_heater", label="Fired Heater",
        behavior=EquipmentBehavior(p_start_maintenance=0.0004, p_go_standby=0.0),
    ),
    "boiler": EquipmentTypeSpec(
        slug="boiler", label="Boiler",
        behavior=EquipmentBehavior(p_start_maintenance=0.0004, p_go_standby=0.0),
    ),
    "distillation_column": EquipmentTypeSpec(
        slug="distillation_column", label="Distillation Column",
        behavior=EquipmentBehavior(p_start_maintenance=0.0, p_go_standby=0.0),
    ),
    "vessel": EquipmentTypeSpec(
        slug="vessel", label="Pressure Vessel",
        behavior=EquipmentBehavior(p_start_maintenance=0.0003, p_go_standby=0.0),
    ),
    "tank": EquipmentTypeSpec(
        slug="tank", label="Storage Tank",
        behavior=EquipmentBehavior(p_start_maintenance=0.0003, p_go_standby=0.0),
    ),
    "control_valve": EquipmentTypeSpec(slug="control_valve", label="Control Valve"),
    "relief_valve": EquipmentTypeSpec(slug="relief_valve", label="Relief Valve"),
    "loading_arm": EquipmentTypeSpec(
        slug="loading_arm", label="Loading Arm",
        # Loading arms idle between truck/rail slots far more than process assets do.
        behavior=EquipmentBehavior(p_go_standby=0.0030, p_leave_standby=0.0060),
    ),
    "flare_stack": EquipmentTypeSpec(slug="flare_stack", label="Flare Stack"),
    "vacuum_ejector": EquipmentTypeSpec(slug="vacuum_ejector", label="Vacuum Ejector"),
    "generator": EquipmentTypeSpec(slug="generator", label="Emergency Generator"),
    "control_system": EquipmentTypeSpec(
        slug="control_system", label="Control System",
        behavior=EquipmentBehavior(p_start_maintenance=0.0001, p_go_standby=0.0),
    ),
    "hvac": EquipmentTypeSpec(slug="hvac", label="HVAC / Ventilation"),
    "crane": EquipmentTypeSpec(
        slug="crane", label="Overhead Crane",
        behavior=EquipmentBehavior(p_go_standby=0.0030, p_leave_standby=0.0050),
    ),
}

PERMIT_TYPES = {
    "hot_work": PermitTypeSpec(
        slug="hot_work", label="Hot Work", required_isolation="gas_test_and_fire_watch",
        description_templates=[
            "Weld repair on {target}",
            "Grinding and cutting near {target}",
            "Refractory repair on {target}",
        ],
        applies_to=["heat_exchanger", "fired_heater", "boiler", "distillation_column",
                    "vessel", "tank", "flare_stack", "loading_arm", "crane"],
    ),
    "confined_space": PermitTypeSpec(
        slug="confined_space", label="Confined Space Entry",
        required_isolation="blind_purge_and_gas_test",
        description_templates=[
            "Internal inspection of {target}",
            "Cleaning and sludge removal in {target}",
        ],
        applies_to=["tank", "vessel", "distillation_column", "boiler"],
    ),
    "line_breaking": PermitTypeSpec(
        slug="line_breaking", label="Line Breaking",
        required_isolation="depressurize_drain_and_blind",
        description_templates=[
            "Flange break on {target} discharge line",
            "Spool removal at {target}",
            "Gasket replacement on {target} suction line",
        ],
        applies_to=["pump", "heat_exchanger", "control_valve", "relief_valve",
                    "loading_arm", "vacuum_ejector"],
    ),
    "lockout_tagout": PermitTypeSpec(
        slug="lockout_tagout", label="Lockout / Tagout", required_isolation="lockout_tagout",
        description_templates=[
            "Mechanical seal replacement on {target}",
            "Bearing replacement on {target}",
            "Coupling alignment on {target}",
        ],
        applies_to=["pump", "compressor", "fire_pump", "generator", "crane", "hvac"],
    ),
    "working_at_height": PermitTypeSpec(
        slug="working_at_height", label="Working at Height", required_isolation="none",
        description_templates=[
            "Elevated platform work at {target}",
            "Scaffold erection beside {target}",
        ],
        applies_to=[],  # any asset
    ),
    "electrical": PermitTypeSpec(
        slug="electrical", label="Electrical Work", required_isolation="electrical_isolation",
        description_templates=[
            "Motor control center inspection for {target}",
            "Instrument loop check on {target}",
        ],
        applies_to=["compressor", "pump", "control_system", "generator", "boiler", "hvac"],
    ),
}

# Shorthand for the zone tables below.
_R = OperatingRange
_E = EquipmentTemplate
_S = SensorTemplate

ZONES = [
    ZoneTemplate(
        code="CCR-01", name="Central Control Room",
        zone_type="control_room", zone_category=ZoneCategory.SUPPORT,
        description="DCS operations hub — board operators monitor and control every unit on site.",
        grid_row=1, grid_col=1,
        equipment=[
            _E(tag="DCS-01", name="Distributed Control System", equipment_type="control_system",
               criticality="safety_critical", manufacturer="Honeywell"),
            _E(tag="UPS-01", name="Uninterruptible Power Supply", equipment_type="control_system",
               criticality="high"),
            _E(tag="HVAC-01", name="Control Room Pressurization Unit", equipment_type="hvac"),
        ],
        sensors=[
            _S(tag="SD-901", sensor_type="smoke",
               range=_R(normal_min=0.0, normal_max=1.0, warning_max=4.0, critical_max=8.0)),
            _S(tag="AI-901", sensor_type="oxygen", equipment_tag="HVAC-01",
               range=_R(normal_min=20.4, normal_max=21.2, warning_min=19.5, warning_max=22.5,
                        critical_min=18.0, critical_max=23.5)),
        ],
    ),
    ZoneTemplate(
        code="CDU-100", name="Crude Distillation Unit (Unit 100)",
        zone_type="crude_distillation", zone_category=ZoneCategory.PROCESS,
        description="Atmospheric distillation — the front end of the refinery, separating raw "
                    "crude into naphtha, kerosene, diesel and atmospheric residue.",
        grid_row=1, grid_col=2,
        equipment=[
            _E(tag="100-P-101A", name="Crude Charge Pump A", equipment_type="pump",
               manufacturer="Flowserve", spare_group="cdu-charge"),
            _E(tag="100-P-101B", name="Crude Charge Pump B", equipment_type="pump",
               manufacturer="Flowserve", spare_group="cdu-charge", status="standby"),
            _E(tag="100-E-101", name="Crude Preheat Exchanger", equipment_type="heat_exchanger"),
            _E(tag="100-H-101", name="Atmospheric Charge Heater", equipment_type="fired_heater",
               criticality="high"),
            _E(tag="100-C-101", name="Atmospheric Distillation Column",
               equipment_type="distillation_column", criticality="safety_critical"),
            _E(tag="100-PSV-101", name="Column Overhead Relief Valve", equipment_type="relief_valve",
               criticality="safety_critical"),
            _E(tag="100-FV-101", name="Crude Feed Control Valve", equipment_type="control_valve"),
        ],
        sensors=[
            _S(tag="100-TI-101", sensor_type="temperature", equipment_tag="100-H-101",
               range=_R(normal_min=340, normal_max=365, warning_max=375, critical_max=390)),
            _S(tag="100-TI-102", sensor_type="temperature", equipment_tag="100-C-101",
               range=_R(normal_min=105, normal_max=130, warning_max=140, critical_max=155)),
            _S(tag="100-PI-101", sensor_type="pressure", equipment_tag="100-C-101",
               range=_R(normal_min=12, normal_max=22, warning_max=26, critical_max=32)),
            _S(tag="100-FI-101", sensor_type="flow", equipment_tag="100-P-101A",
               range=_R(normal_min=280, normal_max=360, warning_min=200, warning_max=390,
                        critical_max=420)),
            _S(tag="100-LI-101", sensor_type="level", equipment_tag="100-C-101",
               range=_R(normal_min=40, normal_max=70, warning_min=20, warning_max=80,
                        critical_min=10, critical_max=92)),
            _S(tag="100-ZI-101", sensor_type="valve_position", equipment_tag="100-FV-101",
               range=_R(normal_min=25, normal_max=75)),
            _S(tag="100-AI-101", sensor_type="h2s",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=20)),
            _S(tag="100-AI-102", sensor_type="combustible_gas",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=25)),
        ],
    ),
    ZoneTemplate(
        code="VDU-200", name="Vacuum Distillation Unit (Unit 200)",
        zone_type="vacuum_distillation", zone_category=ZoneCategory.PROCESS,
        description="Vacuum distillation of atmospheric residue into gas oils under deep vacuum, "
                    "feeding downstream conversion and lube streams.",
        grid_row=1, grid_col=3,
        equipment=[
            _E(tag="200-H-201", name="Vacuum Charge Heater", equipment_type="fired_heater",
               criticality="high"),
            _E(tag="200-C-201", name="Vacuum Distillation Column",
               equipment_type="distillation_column", criticality="safety_critical"),
            _E(tag="200-EJ-201", name="First-Stage Steam Ejector", equipment_type="vacuum_ejector"),
            _E(tag="200-E-201", name="Vacuum Overhead Condenser", equipment_type="heat_exchanger"),
            _E(tag="200-P-201", name="Vacuum Residue Pump", equipment_type="pump",
               manufacturer="Sulzer"),
        ],
        sensors=[
            _S(tag="200-PI-201", sensor_type="pressure", equipment_tag="200-C-201", unit="mmHg",
               range=_R(normal_min=25, normal_max=60, warning_max=90, critical_max=120)),
            _S(tag="200-TI-201", sensor_type="temperature", equipment_tag="200-H-201",
               range=_R(normal_min=385, normal_max=410, warning_max=420, critical_max=430)),
            _S(tag="200-TI-202", sensor_type="temperature", equipment_tag="200-C-201",
               range=_R(normal_min=340, normal_max=365, warning_max=375, critical_max=385)),
            _S(tag="200-FI-201", sensor_type="flow", equipment_tag="200-P-201",
               range=_R(normal_min=90, normal_max=140, warning_min=50, warning_max=160,
                        critical_max=180)),
            _S(tag="200-AI-201", sensor_type="h2s",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=20)),
        ],
    ),
    ZoneTemplate(
        code="FLR-01", name="Flare & Relief System",
        zone_type="flare_system", zone_category=ZoneCategory.SAFETY_SYSTEMS,
        description="Emergency pressure relief — collects unit relief loads through the knock-out "
                    "drum and burns them safely at the elevated flare.",
        grid_row=1, grid_col=4,
        equipment=[
            _E(tag="FS-701", name="Main Flare Stack", equipment_type="flare_stack",
               criticality="safety_critical"),
            _E(tag="D-701", name="Flare Knock-Out Drum", equipment_type="vessel",
               criticality="high"),
        ],
        sensors=[
            # Pilot-flame thermocouple: a LOW reading is the emergency (pilot loss).
            _S(tag="TI-701", sensor_type="temperature", equipment_tag="FS-701",
               sampling_interval_seconds=10,
               range=_R(normal_min=380, normal_max=650, warning_min=300, critical_min=200)),
            # Flare header flow sits near idle; excursions model relief events.
            _S(tag="FI-701", sensor_type="flow", equipment_tag="FS-701",
               excursion_probability=0.0006,
               range=_R(normal_min=10, normal_max=120, warning_max=300, critical_max=500)),
            _S(tag="LI-701", sensor_type="level", equipment_tag="D-701",
               range=_R(normal_min=5, normal_max=30, warning_max=60, critical_max=80)),
            _S(tag="AI-701", sensor_type="h2s",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=20)),
        ],
    ),
    ZoneTemplate(
        code="MWS-01", name="Maintenance Workshop",
        zone_type="maintenance_workshop", zone_category=ZoneCategory.SUPPORT,
        description="Central maintenance base — machining, welding bays and the lay-down area for "
                    "equipment pulled from the units.",
        grid_row=2, grid_col=1,
        equipment=[
            _E(tag="WS-CRN-01", name="Overhead Gantry Crane", equipment_type="crane"),
            _E(tag="WS-CMP-01", name="Workshop Air Compressor", equipment_type="compressor"),
            _E(tag="WS-VNT-01", name="Welding Bay Extraction Fan", equipment_type="hvac"),
        ],
        sensors=[
            _S(tag="AI-951", sensor_type="combustible_gas",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=25)),
            _S(tag="SD-951", sensor_type="smoke",
               range=_R(normal_min=0, normal_max=1.5, warning_max=4.0, critical_max=8.0)),
        ],
    ),
    ZoneTemplate(
        code="PMP-01", name="Pump House",
        zone_type="pump_house", zone_category=ZoneCategory.PRODUCT_MOVEMENT,
        description="Transfer pumping between the tank farm, process units and the loading bay.",
        grid_row=2, grid_col=2,
        equipment=[
            _E(tag="P-501A", name="Product Transfer Pump A", equipment_type="pump",
               manufacturer="Flowserve", spare_group="product-transfer"),
            _E(tag="P-501B", name="Product Transfer Pump B", equipment_type="pump",
               manufacturer="Flowserve", spare_group="product-transfer", status="standby"),
            _E(tag="P-502", name="Crude Transfer Pump", equipment_type="pump"),
        ],
        sensors=[
            _S(tag="PI-501", sensor_type="pressure", equipment_tag="P-501A",
               dynamics=SensorDynamics.EQUIPMENT_COUPLED,
               range=_R(normal_min=110, normal_max=140, warning_max=155, critical_max=170)),
            _S(tag="FI-501", sensor_type="flow", equipment_tag="P-501A",
               range=_R(normal_min=180, normal_max=260, warning_min=120, warning_max=285,
                        critical_max=310)),
            _S(tag="VI-501", sensor_type="vibration", equipment_tag="P-501A",
               range=_R(normal_min=1.0, normal_max=4.5, warning_max=7.1, critical_max=11.0)),
            _S(tag="VI-502", sensor_type="vibration", equipment_tag="P-501B",
               range=_R(normal_min=1.0, normal_max=4.5, warning_max=7.1, critical_max=11.0)),
            _S(tag="AI-501", sensor_type="combustible_gas",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=25)),
        ],
    ),
    ZoneTemplate(
        code="UTL-01", name="Utilities & Steam",
        zone_type="utilities", zone_category=ZoneCategory.UTILITIES,
        description="Steam generation, instrument air and emergency power for the whole site.",
        grid_row=2, grid_col=3,
        equipment=[
            _E(tag="B-401", name="Steam Boiler No. 1", equipment_type="boiler", criticality="high"),
            _E(tag="K-401", name="Instrument Air Compressor A", equipment_type="compressor",
               manufacturer="Ingersoll Rand", spare_group="instrument-air"),
            _E(tag="K-402", name="Instrument Air Compressor B", equipment_type="compressor",
               manufacturer="Ingersoll Rand", spare_group="instrument-air", status="standby"),
            _E(tag="GEN-401", name="Emergency Diesel Generator", equipment_type="generator",
               criticality="safety_critical", status="standby"),
        ],
        sensors=[
            _S(tag="PI-401", sensor_type="pressure", equipment_tag="B-401",
               range=_R(normal_min=140, normal_max=165, warning_min=125, warning_max=175,
                        critical_min=110, critical_max=190)),
            _S(tag="TI-401", sensor_type="temperature", equipment_tag="B-401",
               range=_R(normal_min=165, normal_max=220, warning_max=250, critical_max=280)),
            # Instrument air header: LOW pressure starves control valves site-wide.
            _S(tag="PI-402", sensor_type="pressure", equipment_tag="K-401",
               range=_R(normal_min=95, normal_max=115, warning_min=85, critical_min=75)),
            _S(tag="VI-401", sensor_type="vibration", equipment_tag="K-401",
               range=_R(normal_min=1.0, normal_max=4.5, warning_max=7.1, critical_max=11.0)),
        ],
    ),
    ZoneTemplate(
        code="FWS-01", name="Fire Water System",
        zone_type="fire_water", zone_category=ZoneCategory.SAFETY_SYSTEMS,
        description="Firefighting backbone — storage tank, jockey pump holding header pressure, "
                    "and the diesel fire pump on standby.",
        grid_row=2, grid_col=4,
        equipment=[
            _E(tag="P-801", name="Jockey Pump", equipment_type="pump"),
            _E(tag="P-802", name="Diesel Fire Pump", equipment_type="fire_pump",
               criticality="safety_critical", status="standby"),
            _E(tag="TK-801", name="Fire Water Storage Tank", equipment_type="tank",
               criticality="safety_critical"),
        ],
        sensors=[
            # LOW header pressure means no firefighting capability.
            _S(tag="PI-801", sensor_type="pressure", equipment_tag="P-801",
               range=_R(normal_min=140, normal_max=160, warning_min=120, critical_min=100)),
            _S(tag="LI-801", sensor_type="level", equipment_tag="TK-801",
               range=_R(normal_min=85, normal_max=100, warning_min=70, critical_min=50)),
        ],
    ),
    ZoneTemplate(
        code="LDB-01", name="Loading Bay",
        zone_type="loading_bay", zone_category=ZoneCategory.PRODUCT_MOVEMENT,
        description="Truck loading gantry for finished products, with vapour recovery on every arm.",
        grid_row=3, grid_col=1,
        equipment=[
            _E(tag="LA-601", name="Truck Loading Arm No. 1", equipment_type="loading_arm"),
            _E(tag="LA-602", name="Truck Loading Arm No. 2", equipment_type="loading_arm"),
            _E(tag="P-601", name="Loading Pump", equipment_type="pump"),
            _E(tag="VRU-601", name="Vapour Recovery Compressor", equipment_type="compressor"),
        ],
        sensors=[
            _S(tag="FI-601", sensor_type="flow", equipment_tag="P-601",
               range=_R(normal_min=100, normal_max=180, warning_max=200, critical_max=220)),
            _S(tag="ZI-601", sensor_type="valve_position", equipment_tag="LA-601",
               range=_R(normal_min=10, normal_max=90)),
            _S(tag="AI-601", sensor_type="combustible_gas",
               range=_R(normal_min=0, normal_max=6, warning_max=12, critical_max=25)),
            _S(tag="AI-602", sensor_type="h2s",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=20)),
        ],
    ),
    ZoneTemplate(
        code="TKF-01", name="Tank Farm",
        zone_type="tank_farm", zone_category=ZoneCategory.STORAGE,
        description="Bulk storage in diked enclosures — crude feedstock ahead of Unit 100 and "
                    "finished products awaiting dispatch.",
        grid_row=3, grid_col=2,
        equipment=[
            _E(tag="TK-301", name="Crude Storage Tank 1", equipment_type="tank", criticality="high"),
            _E(tag="TK-302", name="Crude Storage Tank 2", equipment_type="tank"),
            _E(tag="TK-305", name="Diesel Product Tank", equipment_type="tank"),
            _E(tag="TK-306", name="Naphtha Product Tank", equipment_type="tank", criticality="high"),
            _E(tag="MOV-301", name="Tank Farm Manifold Valve", equipment_type="control_valve"),
        ],
        sensors=[
            _S(tag="LI-301", sensor_type="level", equipment_tag="TK-301",
               dynamics=SensorDynamics.INTEGRATING,
               range=_R(normal_min=20, normal_max=85, warning_min=10, warning_max=92,
                        critical_min=5, critical_max=97)),
            _S(tag="LI-302", sensor_type="level", equipment_tag="TK-302",
               dynamics=SensorDynamics.INTEGRATING,
               range=_R(normal_min=20, normal_max=85, warning_min=10, warning_max=92,
                        critical_min=5, critical_max=97)),
            _S(tag="LI-305", sensor_type="level", equipment_tag="TK-305",
               dynamics=SensorDynamics.INTEGRATING,
               range=_R(normal_min=20, normal_max=85, warning_min=10, warning_max=92,
                        critical_min=5, critical_max=97)),
            _S(tag="LI-306", sensor_type="level", equipment_tag="TK-306",
               dynamics=SensorDynamics.INTEGRATING,
               range=_R(normal_min=20, normal_max=85, warning_min=10, warning_max=92,
                        critical_min=5, critical_max=97)),
            # Nitrogen blanket on the naphtha tank — small positive pressure band.
            _S(tag="PI-306", sensor_type="pressure", equipment_tag="TK-306",
               range=_R(normal_min=0.4, normal_max=1.8, warning_min=0.15, warning_max=2.5,
                        critical_min=0.05, critical_max=3.5)),
            _S(tag="TI-301", sensor_type="temperature", equipment_tag="TK-301",
               range=_R(normal_min=15, normal_max=45, warning_max=55, critical_max=65)),
            _S(tag="AI-301", sensor_type="h2s",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=20)),
            _S(tag="AI-302", sensor_type="combustible_gas",
               range=_R(normal_min=0, normal_max=5, warning_max=10, critical_max=25)),
        ],
    ),
]

WORKERS = [
    WorkerTemplate(employee_id="EMP-1001", first_name="Elena", last_name="Martinez",
                   role="plant_manager", shift="day", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1002", first_name="Marcus", last_name="Whitfield",
                   role="safety_officer", shift="day", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1003", first_name="Priya", last_name="Chandrasekaran",
                   role="safety_officer", shift="night", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1004", first_name="Daniel", last_name="Osei",
                   role="shift_supervisor", shift="day", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1005", first_name="Grace", last_name="Lindqvist",
                   role="shift_supervisor", shift="night", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1006", first_name="Robert", last_name="Kim",
                   role="console_operator", shift="swing", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1007", first_name="Amara", last_name="Okafor",
                   role="operations_director", shift="day", zone_code=None),
    WorkerTemplate(employee_id="EMP-1008", first_name="Tomas", last_name="Reyes",
                   role="console_operator", shift="day", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1009", first_name="Hannah", last_name="Fitzgerald",
                   role="console_operator", shift="night", zone_code="CCR-01"),
    WorkerTemplate(employee_id="EMP-1010", first_name="Ibrahim", last_name="Al-Sayed",
                   role="field_operator", shift="day", zone_code="CDU-100"),
    WorkerTemplate(employee_id="EMP-1011", first_name="Chloe", last_name="Bergstrom",
                   role="field_operator", shift="swing", zone_code="VDU-200"),
    WorkerTemplate(employee_id="EMP-1012", first_name="Nathaniel", last_name="Voss",
                   role="field_operator", shift="day", zone_code="TKF-01"),
    WorkerTemplate(employee_id="EMP-1013", first_name="Sofia", last_name="Delacroix",
                   role="field_operator", shift="day", zone_code="PMP-01"),
    WorkerTemplate(employee_id="EMP-1014", first_name="Jamal", last_name="Whitaker",
                   role="field_operator", shift="night", zone_code="LDB-01"),
    WorkerTemplate(employee_id="EMP-1015", first_name="Wei", last_name="Chen",
                   role="maintenance_technician", shift="day", zone_code="MWS-01"),
    WorkerTemplate(employee_id="EMP-1016", first_name="Diego", last_name="Fernandez",
                   role="maintenance_technician", shift="night", zone_code="MWS-01",
                   employment_status="on_leave"),
    WorkerTemplate(employee_id="EMP-1017", first_name="Fatima", last_name="Hassan",
                   role="maintenance_planner", shift="day", zone_code="MWS-01"),
    WorkerTemplate(employee_id="EMP-1018", first_name="Viktor", last_name="Petrov",
                   role="contractor", shift="day", zone_code="UTL-01",
                   employment_status="contractor"),
    WorkerTemplate(employee_id="EMP-1019", first_name="Aisha", last_name="Ndiaye",
                   role="field_operator", shift="night", zone_code="UTL-01"),
    WorkerTemplate(employee_id="EMP-1020", first_name="Lucas", last_name="Meyer",
                   role="field_operator", shift="day", zone_code="FLR-01"),
]

TUNING = SimulationTuning(
    desk_roles={"plant_manager", "operations_director", "safety_officer", "shift_supervisor",
                "console_operator", "maintenance_planner"},
    approver_roles={"safety_officer", "shift_supervisor"},
    requester_roles={"field_operator", "maintenance_technician", "contractor"},
)

CRUDE_OIL_REFINERY = PlantTypeDefinition(
    slug="crude_oil_refinery",
    label="Crude Oil Refinery",
    description="A fuels refinery: crude and vacuum distillation, tank storage, product loading, "
                "utilities, and the flare / fire water safety systems around them.",
    sensor_types=SENSOR_TYPES,
    equipment_types=EQUIPMENT_TYPES,
    permit_types=PERMIT_TYPES,
    zones=ZONES,
    workers=WORKERS,
    tuning=TUNING,
)
