from typing import Generic, TypeVar, Type, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: str) -> ModelType | None:
        """Get entity by ID."""
        return self.db.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get all entities with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, **kwargs: Any) -> ModelType:
        """Create new entity."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, id: str, **kwargs: Any) -> ModelType | None:
        """Update entity by ID."""
        instance = self.get(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        instance = self.get(id)
        if not instance:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True

    def count(self) -> int:
        """Count total entities."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        return int(self.db.execute(stmt).scalar_one())
