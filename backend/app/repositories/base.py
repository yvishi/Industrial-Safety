from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD data access shared by every entity repository.

    Entity-specific repositories subclass this, set `model`, and add lookups that matter for
    that entity's business rules (e.g. `get_by_code`) rather than re-implementing plumbing.
    """

    model: type[ModelType]
    # Column expressions applied to every list() query, e.g. (Model.occurred_at.desc(),).
    default_order_by: tuple[Any, ...] = ()

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        return await self.session.get(self.model, entity_id)

    async def list(
        self, *, page: int = 1, page_size: int = 50, **filters: Any
    ) -> tuple[list[ModelType], int]:
        stmt = select(self.model)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)

        total = (
            await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        if self.default_order_by:
            stmt = stmt.order_by(*self.default_order_by)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = (await self.session.execute(stmt)).scalars().all()
        return list(items), total

    async def create(self, values: dict[str, Any]) -> ModelType:
        obj = self.model(**values)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, values: dict[str, Any]) -> ModelType:
        for field, value in values.items():
            setattr(obj, field, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.commit()

    async def find_one(self, **filters: Any) -> ModelType | None:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt.limit(1))
        return result.scalars().first()
