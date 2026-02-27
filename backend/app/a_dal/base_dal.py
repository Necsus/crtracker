"""Base Data Access Layer with generic CRUD operations.

All DAL classes should inherit from BaseDAL to get
standard CRUD functionality for their entities.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Result, Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseDAL(Generic[ModelType]):
    """Generic base class for Data Access Layer operations.

    Provides common CRUD operations that work with any SQLAlchemy model.
    All database queries must go through the DAL layer.
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """Initialize the DAL with a database session and model.

        Args:
            session: SQLAlchemy async session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    # ==========================================================================
    # READ OPERATIONS
    # ==========================================================================

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        """Get a single entity by its primary key.

        Args:
            entity_id: Primary key value

        Returns:
            The entity if found, None otherwise
        """
        stmt = select(self.model).where(self.model.id == entity_id)
        result: Result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Get all entities with pagination.

        Args:
            offset: Number of rows to skip
            limit: Maximum number of rows to return

        Returns:
            List of entities
        """
        stmt = select(self.model).offset(offset).limit(limit)
        result: Result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count of entities in the table
        """
        stmt = select(func.count(self.model.id))
        result: Result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, entity_id: int) -> bool:
        """Check if an entity exists by ID.

        Args:
            entity_id: Primary key to check

        Returns:
            True if entity exists, False otherwise
        """
        stmt = select(func.count(self.model.id)).where(self.model.id == entity_id)
        result: Result = await self.session.execute(stmt)
        return (result.scalar() or 0) > 0

    # ==========================================================================
    # WRITE OPERATIONS
    # ==========================================================================

    async def create(self, entity: ModelType) -> ModelType:
        """Create a new entity.

        Args:
            entity: Entity instance to create

        Returns:
            Created entity with populated ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity_id: int, **kwargs: Any) -> ModelType | None:
        """Update an entity by ID.

        Args:
            entity_id: Primary key of entity to update
            **kwargs: Field names and values to update

        Returns:
            Updated entity if found, None otherwise
        """
        stmt = (
            update(self.model)
            .where(self.model.id == entity_id)
            .values(**kwargs)
            .returning(self.model)
        )
        result: Result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: Primary key of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        stmt = delete(self.model).where(self.model.id == entity_id)
        result: Result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ==========================================================================
    # BULK OPERATIONS
    # ==========================================================================

    async def create_many(self, entities: list[ModelType]) -> list[ModelType]:
        """Create multiple entities efficiently.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities with populated IDs
        """
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    # ==========================================================================
    # QUERY BUILDING HELPERS
    # ==========================================================================

    def build_select(self) -> Select[tuple[ModelType]]:
        """Create a new select statement for this model.

        Returns:
            SQLAlchemy Select statement
        """
        return select(self.model)
