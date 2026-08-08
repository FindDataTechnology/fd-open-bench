from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.evaluation_run import EvaluationRun, EvaluationRunStatus
from app.repositories.base import BaseRepository


class EvaluationRunRepository(BaseRepository[EvaluationRun]):
    """Repository for EvaluationRun entities."""

    def __init__(self, db: Session):
        super().__init__(EvaluationRun, db)

    def get_by_agent(self, agent_id: str, skip: int = 0, limit: int = 100) -> list[EvaluationRun]:
        """Get runs by agent ID."""
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.agent_id == agent_id)
            .order_by(EvaluationRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_active_runs(self) -> list[EvaluationRun]:
        """Get all running or pending evaluations."""
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.status.in_([
                EvaluationRunStatus.PENDING,
                EvaluationRunStatus.RUNNING,
            ]))
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_status(
        self,
        id: str,
        status: EvaluationRunStatus,
        **extra_updates: dict[str, any]
    ) -> EvaluationRun | None:
        """Update run status and optionally set timing."""
        instance = self.get(id)
        if not instance:
            return None

        updates = {"status": status}
        if status == EvaluationRunStatus.RUNNING and "started_at" not in extra_updates:
            updates["started_at"] = datetime.utcnow()
        elif status in [
            EvaluationRunStatus.COMPLETED,
            EvaluationRunStatus.FAILED,
            EvaluationRunStatus.CANCELLED,
        ] and "completed_at" not in extra_updates:
            updates["completed_at"] = datetime.utcnow()

        # Update any additional fields passed
        updates.update(extra_updates)

        for key, value in updates.items():
            setattr(instance, key, value)

        self.db.commit()
        self.db.refresh(instance)
        return instance
