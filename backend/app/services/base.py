from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Thin orchestration above a repository: not-found/conflict rules live here, not in routers.

    Entity services subclass this and override `unique_fields` to get automatic duplicate-key
    checks on create/update, or override create/update entirely for more involved validation.
    """

    entity_name: str = "resource"
    unique_fields: tuple[str, ...] = ()

    def __init__(self, repository: BaseRepository[ModelType]) -> None:
        self.repository = repository

    async def get(self, entity_id: UUID) -> ModelType:
        obj = await self.repository.get_by_id(entity_id)
        if obj is None:
            raise NotFoundError(f"{self.entity_name} '{entity_id}' not found")
        return obj

    async def list(
        self, *, page: int = 1, page_size: int = 50, **filters: Any
    ) -> tuple[list[ModelType], int]:
        return await self.repository.list(page=page, page_size=page_size, **filters)

    async def create(self, payload: BaseModel) -> ModelType:
        values = payload.model_dump()
        await self._ensure_unique(values, exclude_id=None)
        return await self.repository.create(values)

    async def update(self, entity_id: UUID, payload: BaseModel) -> ModelType:
        obj = await self.get(entity_id)
        values = payload.model_dump(exclude_unset=True)
        await self._ensure_unique(values, exclude_id=entity_id)
        return await self.repository.update(obj, values)

    async def delete(self, entity_id: UUID) -> None:
        obj = await self.get(entity_id)
        await self.repository.delete(obj)

    async def _ensure_unique(self, values: dict[str, Any], *, exclude_id: UUID | None) -> None:
        for field in self.unique_fields:
            if field not in values:
                continue
            existing = await self.repository.find_one(**{field: values[field]})
            if existing is not None and existing.id != exclude_id:
                raise ConflictError(
                    f"{self.entity_name} with {field}='{values[field]}' already exists"
                )
