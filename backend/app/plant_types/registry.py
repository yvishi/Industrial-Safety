"""
Registry of supported plant types. Adding an industry = write a definition module, import it
here. The simulator and seed script resolve definitions only through this registry.
"""

import logging

from app.plant_types.refinery import CRUDE_OIL_REFINERY
from app.plant_types.schema import PlantTypeDefinition

logger = logging.getLogger(__name__)

_PLANT_TYPES: dict[str, PlantTypeDefinition] = {
    CRUDE_OIL_REFINERY.slug: CRUDE_OIL_REFINERY,
}

DEFAULT_PLANT_TYPE = CRUDE_OIL_REFINERY.slug


def get_plant_type(slug: str) -> PlantTypeDefinition:
    """Resolve a plant type; unknown slugs fall back to the default rather than halting the plant."""
    definition = _PLANT_TYPES.get(slug)
    if definition is None:
        logger.warning("Unknown plant type %r — falling back to %r", slug, DEFAULT_PLANT_TYPE)
        return _PLANT_TYPES[DEFAULT_PLANT_TYPE]
    return definition
