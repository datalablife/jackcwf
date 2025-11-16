"""Base repository with async CRUD operations."""

import logging
from typing import Generic, TypeVar, Optional, List, Any, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository class for async CRUD operations.

    This class provides common database operations using SQLAlchemy async.
    Subclasses should set the model_class attribute.

    Example:
        class UserRepository(BaseRepository[UserORM]):
            model_class = UserORM
    """

    model_class: Optional[type] = None

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.

        Args:
            session: SQLAlchemy AsyncSession instance
        """
        if self.model_class is None:
            raise ValueError(f"{self.__class__.__name__} must define model_class")
        self.session = session

    async def create(self, **kwargs) -> T:
        """
        Create a new record with proper transaction handling.

        Args:
            **kwargs: Column values for the model

        Returns:
            Created model instance

        Raises:
            ValueError: If required fields are missing
            Exception: If database operation fails
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)

        try:
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model_class.__name__}: {str(e)}")
            raise

    async def get(self, id: Any) -> Optional[T]:
        """
        Get a record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        return await self.session.get(self.model_class, id)

    async def get_by(self, **filters) -> Optional[T]:
        """
        Get a single record matching the filters.

        Args:
            **filters: Column name = value pairs for WHERE clause

        Returns:
            First matching model instance or None
        """
        query = select(self.model_class)
        for key, value in filters.items():
            query = query.where(getattr(self.model_class, key) == value)

        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 10,
        order_by: Optional[str] = None,
        **filters
    ) -> List[T]:
        """
        List records with optional filtering and ordering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by (prefix with - for descending)
            **filters: Column name = value pairs for WHERE clause

        Returns:
            List of model instances
        """
        query = select(self.model_class)

        # Apply filters
        for key, value in filters.items():
            query = query.where(getattr(self.model_class, key) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                query = query.order_by(getattr(self.model_class, order_by[1:]).desc())
            else:
                query = query.order_by(getattr(self.model_class, order_by))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """
        Update a record by ID with proper transaction handling.

        Args:
            id: Primary key value
            **kwargs: Column values to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model_class.__name__}: {str(e)}")
            raise

    async def delete(self, id: Any) -> bool:
        """
        Delete a record by ID with proper transaction handling.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id)
        if not instance:
            return False

        try:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model_class.__name__}: {str(e)}")
            raise

    async def count(self, **filters) -> int:
        """
        Count records matching the filters.

        Args:
            **filters: Column name = value pairs for WHERE clause

        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model_class)

        for key, value in filters.items():
            query = query.where(getattr(self.model_class, key) == value)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(self, **filters) -> bool:
        """
        Check if a record matching the filters exists.

        Args:
            **filters: Column name = value pairs for WHERE clause

        Returns:
            True if matching record exists, False otherwise
        """
        count = await self.count(**filters)
        return count > 0

    async def bulk_create(self, instances: List[T]) -> List[T]:
        """
        Create multiple records in one transaction (optimized to avoid N+1).

        Args:
            instances: List of model instances

        Returns:
            List of created instances

        Note:
            This method avoids N+1 queries by flushing instead of refreshing
            each instance individually after insert.
        """
        try:
            self.session.add_all(instances)
            await self.session.flush()  # Flush to assign IDs without committing
            await self.session.commit()
            # Instances now have IDs; no need to refresh individually
            return instances
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to bulk create {self.model_class.__name__}: {str(e)}")
            raise

    async def bulk_delete(self, ids: List[Any]) -> int:
        """
        Delete multiple records by IDs with proper transaction handling.

        Args:
            ids: List of primary key values

        Returns:
            Number of deleted records
        """
        query = select(self.model_class).where(self.model_class.id.in_(ids))
        result = await self.session.execute(query)
        instances = result.scalars().all()

        try:
            for instance in instances:
                await self.session.delete(instance)

            await self.session.commit()
            return len(instances)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to bulk delete {self.model_class.__name__}: {str(e)}")
            raise
