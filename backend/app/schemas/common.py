from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """Base for Read schemas — lets Pydantic build directly from SQLAlchemy model instances."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedRead(ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class Page[T](BaseModel):
    """Generic paginated list envelope used by every list endpoint."""

    items: list[T]
    total: int
    page: int
    page_size: int
