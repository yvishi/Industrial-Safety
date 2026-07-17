"""Every EventType member must have a severity mapping — severity is always derived
server-side (see EventRepository.create / simulation/events.py::make_event), never accepted
from a caller, so a missing entry would silently fall back to INFO rather than fail loudly."""

from app.schemas.event import EVENT_SEVERITY_MAP, EventType


def test_every_event_type_has_a_severity_mapping() -> None:
    for event_type in EventType:
        assert event_type.value in EVENT_SEVERITY_MAP, f"{event_type.value} has no severity mapping"


def test_no_orphan_severity_entries() -> None:
    valid_values = {e.value for e in EventType}
    for key in EVENT_SEVERITY_MAP:
        assert key in valid_values, f"'{key}' in EVENT_SEVERITY_MAP is not a real EventType"
