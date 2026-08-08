from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository for Dataset entities."""

    def __init__(self, db: Session):
        super().__init__(Dataset, db)

    def get_by_name(self, name: str) -> Dataset | None:
        """Get dataset by name."""
        stmt = select(Dataset).where(Dataset.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_golden_count(self, id: str) -> int:
        """Get number of goldens in a dataset."""
        from sqlalchemy import func
        from app.models.golden import Golden

        stmt = (
            select(func.count(Golden.id))
            .where(Golden.dataset_id == id)
        )
        return int(self.db.execute(stmt).scalar_one())
