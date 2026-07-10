from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class PlantBase(BaseModel):
    code: str
    name: str
    # Selects the PlantTypeDefinition (app/plant_types/) this site is an instance of.
    plant_type: str = "crude_oil_refinery"
    description: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "UTC"


class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    plant_type: str | None = None
    description: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None


class PlantRead(PlantBase, TimestampedRead):
    pass
