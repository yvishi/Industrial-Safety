"""
Per-sensor-type physics profiles for the simulation engine.

These live in code, not the database, on purpose: warning levels here drive *simulation
behavior* (when to emit sensor_warning events), they are not risk-engine configuration.
When the Risk Engine arrives it will own its own thresholds.

Values are loosely grounded in real process-industry ranges (e.g. vibration warning at
7.1 mm/s follows the ISO 10816 zone C boundary; gas detection warning at 20 ppm is a
typical H2S alarm setpoint).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorProfile:
    baseline: float  # value the reading reverts toward
    sigma: float  # per-tick gaussian noise
    theta: float  # mean-reversion strength per tick (0..1)
    warning: float  # crossing this emits a sensor_warning event
    minimum: float  # hard clamp floor
    maximum: float  # hard clamp ceiling


SENSOR_PROFILES: dict[str, SensorProfile] = {
    "temperature": SensorProfile(baseline=165.0, sigma=1.2, theta=0.08, warning=210.0, minimum=15.0, maximum=260.0),
    "pressure": SensorProfile(baseline=125.0, sigma=1.5, theta=0.08, warning=175.0, minimum=0.0, maximum=220.0),
    "flow": SensorProfile(baseline=340.0, sigma=4.0, theta=0.10, warning=460.0, minimum=0.0, maximum=550.0),
    "level": SensorProfile(baseline=62.0, sigma=0.5, theta=0.05, warning=88.0, minimum=0.0, maximum=100.0),
    "gas_detection": SensorProfile(baseline=2.5, sigma=0.35, theta=0.12, warning=20.0, minimum=0.0, maximum=60.0),
    "vibration": SensorProfile(baseline=2.8, sigma=0.15, theta=0.10, warning=7.1, minimum=0.0, maximum=12.0),
    "smoke": SensorProfile(baseline=0.4, sigma=0.06, theta=0.15, warning=4.0, minimum=0.0, maximum=10.0),
}

DEFAULT_PROFILE = SensorProfile(
    baseline=50.0, sigma=1.0, theta=0.1, warning=90.0, minimum=0.0, maximum=120.0
)


def profile_for(sensor_type: str) -> SensorProfile:
    return SENSOR_PROFILES.get(sensor_type, DEFAULT_PROFILE)
