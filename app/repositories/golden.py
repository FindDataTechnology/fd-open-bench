from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.golden import Golden
from app.repositories.base import BaseRepository


class GoldenRepository(BaseRepository[Golden]):
    """Repository for Golden entities."""

    def __init__(self, db: Session):
        super().__init__(Golden, db)

    def get_by_dataset(self, dataset_id: str) -> list[Golden]:
        """Get all goldens from a dataset."""
        stmt = select(Golden).where(Golden.dataset_id == dataset_id)
        return list(self.db.execute(stmt).scalars().all())

    def bulk_create_from_dicts(self, dataset_id: str, goldens_data: list[dict[str, Any]]) -> list[Golden]:
        """Bulk create multiple goldens from dictionary data."""
        goldens = []
        for data in goldens_data:
            golden = Golden(
                dataset_id=dataset_id,
                input=data.get("input", ""),
                expected_output=data.get("expected_output"),
                expected_tools=data.get("expected_tools"),
                business_value=data.get("business_value"),
                metadata=data.get("metadata", {}),
            )
            self.db.add(golden)
            goldens.append(golden)
        self.db.commit()
        self.db.refresh(goldens[0] if goldens else None)
        return goldens
