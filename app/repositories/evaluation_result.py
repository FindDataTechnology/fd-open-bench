from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.evaluation_result import EvaluationResult, EvaluationResultStatus
from app.repositories.base import BaseRepository


class EvaluationResultRepository(BaseRepository[EvaluationResult]):
    """Repository for EvaluationResult entities."""

    def __init__(self, db: Session):
        super().__init__(EvaluationResult, db)

    def get_by_run(self, run_id: str, skip: int = 0, limit: int = 100) -> list[EvaluationResult]:
        """Get results from a specific run."""
        stmt = (
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def aggregate_stats(self, run_id: str) -> dict[str, any]:
        """Calculate aggregate statistics for a run's results."""
        from sqlalchemy import func, cast, Float

        # Get counts by status
        stmt_success = (
            select(func.count(EvaluationResult.id))
            .where(
                EvaluationResult.run_id == run_id,
                EvaluationResult.status == EvaluationResultStatus.SUCCESS,
            )
        )
        successful = self.db.execute(stmt_success).scalar_one()

        stmt_failed = (
            select(func.count(EvaluationResult.id))
            .where(
                EvaluationResult.run_id == run_id,
                EvaluationResult.status.in_([
                    EvaluationResultStatus.FAILED,
                    EvaluationResultStatus.TIMEOUT,
                    EvaluationResultStatus.ERROR,
                ]),
            )
        )
        failed = self.db.execute(stmt_failed).scalar_one()

        total = successful + failed

        # Calculate score distribution if results exist
        scores = []
        if total > 0:
            stmt_scores = select(cast(EvaluationResult.metric_scores["score"], Float))
            result_rows = self.db.execute(stmt_scores).fetchall()
            scores = [row[0] for row in result_rows if row[0]]

        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else None
        max_score = max(scores) if scores else None
        success_rate = (successful / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "avg_score": round(avg_score, 4),
            "min_score": round(min_score, 4) if min_score else None,
            "max_score": round(max_score, 4) if max_score else None,
            "success_rate": round(success_rate, 2),
        }

    def delete_old_results(self, older_than_days: int) -> int:
        """Delete results older than specified days."""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        stmt = (
            delete(EvaluationResult)
            .where(EvaluationResult.created_at < cutoff_date)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
