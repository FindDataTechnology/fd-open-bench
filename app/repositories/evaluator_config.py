from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.evaluator_config import EvaluatorConfig
from app.repositories.base import BaseRepository


class EvaluatorConfigRepository(BaseRepository[EvaluatorConfig]):
    """Repository for EvaluatorConfig entities."""

    def __init__(self, db: Session):
        super().__init__(EvaluatorConfig, db)

    def get_by_name(self, name: str) -> EvaluatorConfig | None:
        """Get evaluator config by name."""
        stmt = select(EvaluatorConfig).where(EvaluatorConfig.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_type(self, eval_type: str) -> list[EvaluatorConfig]:
        """Get evaluators by type."""
        stmt = select(EvaluatorConfig).where(EvaluatorConfig.type == eval_type)
        return list(self.db.execute(stmt).scalars().all())

    def upsert(
        self,
        name: str,
        eval_type: str,
        config: dict[str, Any],
        **kwargs
    ) -> EvaluatorConfig:
        """Upsert (update or create) an evaluator configuration."""
        existing = self.get_by_name(name)
        if existing:
            return self.update(
                existing.id,
                type=eval_type,
                config=config,
                **kwargs
            )

        return self.create(name=name, type=eval_type, config=config, **kwargs)
