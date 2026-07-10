"""
The Plant Type configuration schema: a typed, validated description of everything that makes
one industry's plant different from another's — zones, equipment, instruments, operating
ranges, permit vocabulary, and simulation tuning.

The simulation engine and the seed script both consume a PlantTypeDefinition; neither contains
industry knowledge of its own. Supporting a new industry (chemical plant, steel plant, LNG
terminal, ...) means writing a new definition module and registering it — no simulator changes.

Definitions are configuration-as-code: plain Python validated by Pydantic at import time.
"""

from enum import Enum

from pydantic import BaseModel, model_validator


class ZoneCategory(str, Enum):
    """Coarse cross-industry grouping; the fine-grained identity lives in zone_type."""

    PROCESS = "process"
    STORAGE = "storage"
    PRODUCT_MOVEMENT = "product_movement"
    UTILITIES = "utilities"
    SAFETY_SYSTEMS = "safety_systems"
    SUPPORT = "support"


class SensorDynamics(str, Enum):
    """How a simulated reading evolves between samples."""

    # Wanders around a resting value and always comes home (temperatures, pressures, gas ppm).
    MEAN_REVERTING = "mean_reverting"
    # Accumulates a slow fill/draw rate that occasionally reverses (bulk tank levels).
    INTEGRATING = "integrating"
    # Follows the attached equipment: nominal while it runs, decays toward zero when it stops
    # (flows, discharge pressures, vibration).
    EQUIPMENT_COUPLED = "equipment_coupled"


class SensorTypeSpec(BaseModel):
    """One measurement type in this industry's instrument catalog, with its simulation physics."""

    slug: str
    label: str
    unit: str
    dynamics: SensorDynamics = SensorDynamics.MEAN_REVERTING
    # Mean-reversion strength per update (0..1) and per-update noise as a fraction of the
    # normal operating span — expressing sigma as a fraction lets one type cover instruments
    # of very different magnitudes (a 30 °C tank and a 400 °C heater outlet).
    theta: float = 0.08
    noise_fraction: float = 0.012
    # Where in the normal band the resting value sits (0.5 = midpoint; gas detectors rest
    # near the bottom of their range, oxygen near the top).
    baseline_fraction: float = 0.5
    # Per-update chance of starting a controlled drift toward the warning band.
    excursion_probability: float = 0.0
    sampling_interval_seconds: int = 5
    # Physical clamps (e.g. 0-100 for a level %); when None they are derived from the
    # instrument's configured ranges.
    hard_min: float | None = None
    hard_max: float | None = None


class OperatingRange(BaseModel):
    """Alarm-rationalization-style bands for one installed instrument."""

    normal_min: float
    normal_max: float
    warning_min: float | None = None
    warning_max: float | None = None
    critical_min: float | None = None
    critical_max: float | None = None

    @model_validator(mode="after")
    def _ordered(self) -> "OperatingRange":
        if self.normal_min >= self.normal_max:
            raise ValueError(f"normal_min must be below normal_max ({self.normal_min} >= {self.normal_max})")
        if self.warning_max is not None and self.warning_max < self.normal_max:
            raise ValueError("warning_max must sit at or above normal_max")
        if self.warning_min is not None and self.warning_min > self.normal_min:
            raise ValueError("warning_min must sit at or below normal_min")
        if self.critical_max is not None and self.warning_max is not None and self.critical_max < self.warning_max:
            raise ValueError("critical_max must sit at or above warning_max")
        if self.critical_min is not None and self.warning_min is not None and self.critical_min > self.warning_min:
            raise ValueError("critical_min must sit at or below warning_min")
        return self


class SensorTemplate(BaseModel):
    """One installed instrument within a zone template."""

    tag: str
    sensor_type: str
    range: OperatingRange
    equipment_tag: str | None = None
    # Per-instrument overrides of the type defaults.
    unit: str | None = None
    dynamics: SensorDynamics | None = None
    sampling_interval_seconds: int | None = None
    excursion_probability: float | None = None


class EquipmentBehavior(BaseModel):
    """Per-tick lifecycle transition probabilities (tuned for a 5 s tick)."""

    p_start_maintenance: float = 0.0008
    p_go_standby: float = 0.0006
    p_leave_standby: float = 0.0040
    p_finish_maintenance: float = 0.0035


class EquipmentTypeSpec(BaseModel):
    slug: str
    label: str
    behavior: EquipmentBehavior = EquipmentBehavior()


class EquipmentTemplate(BaseModel):
    """One physical asset within a zone template."""

    tag: str
    name: str
    equipment_type: str
    status: str = "operational"
    criticality: str | None = None
    manufacturer: str | None = None
    # Assets sharing a spare_group are an installed-spare set (P-101A/B): the simulator keeps
    # one running and brings the spare online when the duty unit goes down.
    spare_group: str | None = None


class PermitTypeSpec(BaseModel):
    slug: str
    label: str
    # Isolation standard demanded before this work may start (stored on each permit row).
    required_isolation: str
    # Work descriptions with a {target} placeholder for the asset name/tag.
    description_templates: list[str]
    # Equipment types this work realistically applies to; empty means any asset.
    applies_to: list[str] = []


class WorkerTemplate(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    role: str
    shift: str
    zone_code: str | None = None
    employment_status: str = "active"


class SimulationTuning(BaseModel):
    """Cross-cutting behavior parameters (per 5 s tick unless noted)."""

    # Roles that stay at their station (control room / office) vs roam the site.
    desk_roles: set[str]
    approver_roles: set[str]
    requester_roles: set[str]
    field_move_probability: float = 0.010
    desk_move_probability: float = 0.003
    max_concurrent_maintenance: int = 2
    # Spontaneous new permit drafts (planned work), plus the chance that a maintenance
    # start is accompanied by its authorizing permit.
    p_new_permit: float = 0.0035
    p_permit_follows_maintenance: float = 0.9


class ZoneTemplate(BaseModel):
    code: str
    name: str
    zone_type: str
    zone_category: ZoneCategory
    description: str
    grid_row: int
    grid_col: int
    equipment: list[EquipmentTemplate] = []
    sensors: list[SensorTemplate] = []


class PlantTypeDefinition(BaseModel):
    slug: str
    label: str
    description: str
    sensor_types: dict[str, SensorTypeSpec]
    equipment_types: dict[str, EquipmentTypeSpec]
    permit_types: dict[str, PermitTypeSpec]
    zones: list[ZoneTemplate]
    workers: list[WorkerTemplate]
    tuning: SimulationTuning

    @model_validator(mode="after")
    def _cross_references(self) -> "PlantTypeDefinition":
        for key, spec in {**self.sensor_types, **self.equipment_types, **self.permit_types}.items():
            if key != spec.slug:
                raise ValueError(f"catalog key {key!r} does not match spec slug {spec.slug!r}")

        zone_codes: set[str] = set()
        equipment_tags: set[str] = set()
        sensor_tags: set[str] = set()
        for zone in self.zones:
            if zone.code in zone_codes:
                raise ValueError(f"duplicate zone code {zone.code!r}")
            zone_codes.add(zone.code)

            zone_equipment_tags = set()
            for asset in zone.equipment:
                if asset.tag in equipment_tags:
                    raise ValueError(f"duplicate equipment tag {asset.tag!r}")
                equipment_tags.add(asset.tag)
                zone_equipment_tags.add(asset.tag)
                if asset.equipment_type not in self.equipment_types:
                    raise ValueError(f"{asset.tag}: unknown equipment type {asset.equipment_type!r}")

            for sensor in zone.sensors:
                if sensor.tag in sensor_tags:
                    raise ValueError(f"duplicate sensor tag {sensor.tag!r}")
                sensor_tags.add(sensor.tag)
                if sensor.sensor_type not in self.sensor_types:
                    raise ValueError(f"{sensor.tag}: unknown sensor type {sensor.sensor_type!r}")
                if sensor.equipment_tag is not None and sensor.equipment_tag not in zone_equipment_tags:
                    raise ValueError(
                        f"{sensor.tag}: equipment_tag {sensor.equipment_tag!r} is not in zone {zone.code}"
                    )

        for permit_type in self.permit_types.values():
            for equipment_type in permit_type.applies_to:
                if equipment_type not in self.equipment_types:
                    raise ValueError(
                        f"permit type {permit_type.slug!r}: unknown equipment type {equipment_type!r}"
                    )

        for worker in self.workers:
            if worker.zone_code is not None and worker.zone_code not in zone_codes:
                raise ValueError(f"{worker.employee_id}: unknown zone code {worker.zone_code!r}")

        return self

    def sensor_template_by_tag(self, tag: str) -> SensorTemplate | None:
        return self._sensor_templates.get(tag)

    @property
    def _sensor_templates(self) -> dict[str, SensorTemplate]:
        # Cached on first use; definitions are immutable in practice.
        cache = self.__dict__.get("_sensor_templates_cache")
        if cache is None:
            cache = {s.tag: s for zone in self.zones for s in zone.sensors}
            self.__dict__["_sensor_templates_cache"] = cache
        return cache

    def permit_types_for_equipment(self, equipment_type: str) -> list[PermitTypeSpec]:
        """Permit types plausible for work on this kind of asset (specific ones first)."""
        specific = [p for p in self.permit_types.values() if equipment_type in p.applies_to]
        return specific or [p for p in self.permit_types.values() if not p.applies_to]
