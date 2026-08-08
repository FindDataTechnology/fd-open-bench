"""Data retention policy service for automatic cleanup."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete, and_
from app.models import EvaluationResult, EvaluationRun, Trace
from app.core.config import settings


class RetentionService:
    """Service for managing data retention policies."""

    def __init__(self, db: Session):
        self.db = db

    def cleanup_old_traces(
        self,
        days: Optional[int] = None,
        batch_size: int = 1000
    ) -> int:
        """Delete traces older than specified days.

        Args:
            days: Number of days to retain (default from settings)
            batch_size: Number of records to delete per batch

        Returns:
            Number of traces deleted
        """
        retention_days = days or settings.TRACE_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        total_deleted = 0
        while True:
            # Get batch of IDs to delete
            traces = self.db.query(Trace.id).filter(
                Trace.created_at < cutoff_date
            ).limit(batch_size).all()

            if not traces:
                break

            trace_ids = [t[0] for t in traces]

            # Delete in batch
            deleted = self.db.execute(
                delete(Trace).where(Trace.id.in_(trace_ids))
            )
            self.db.commit()
            total_deleted += deleted.rowcount

        return total_deleted

    def cleanup_old_results(
        self,
        days: Optional[int] = None,
        batch_size: int = 1000
    ) -> int:
        """Delete evaluation results older than specified days.

        Args:
            days: Number of days to retain (default from settings)
            batch_size: Number of records to delete per batch

        Returns:
            Number of results deleted
        """
        retention_days = days or settings.RESULT_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        total_deleted = 0
        while True:
            # Get batch of IDs to delete
            results = self.db.query(EvaluationResult.id).filter(
                EvaluationResult.created_at < cutoff_date
            ).limit(batch_size).all()

            if not results:
                break

            result_ids = [r[0] for r in results]

            # Delete in batch
            deleted = self.db.execute(
                delete(EvaluationResult).where(EvaluationResult.id.in_(result_ids))
            )
            self.db.commit()
            total_deleted += deleted.rowcount

        return total_deleted

    def cleanup_old_runs(
        self,
        days: Optional[int] = None,
        batch_size: int = 1000
    ) -> int:
        """Delete evaluation runs older than specified days.

        Args:
            days: Number of days to retain (default from settings)
            batch_size: Number of records to delete per batch

        Returns:
            Number of runs deleted
        """
        retention_days = days or settings.RUN_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        total_deleted = 0
        while True:
            # Get batch of IDs to delete (only completed/failed/cancelled runs)
            runs = self.db.query(EvaluationRun.id).filter(
                and_(
                    EvaluationRun.created_at < cutoff_date,
                    EvaluationRun.status.in_(['completed', 'failed', 'cancelled'])
                )
            ).limit(batch_size).all()

            if not runs:
                break

            run_ids = [r[0] for r in runs]

            # Delete in batch (cascade will handle related results)
            deleted = self.db.execute(
                delete(EvaluationRun).where(EvaluationRun.id.in_(run_ids))
            )
            self.db.commit()
            total_deleted += deleted.rowcount

        return total_deleted

    def run_full_cleanup(
        self,
        trace_days: Optional[int] = None,
        result_days: Optional[int] = None,
        run_days: Optional[int] = None
    ) -> dict[str, int]:
        """Run complete cleanup across all data types.

        Args:
            trace_days: Days to retain traces
            result_days: Days to retain results
            run_days: Days to retain runs

        Returns:
            Dictionary with counts of deleted records
        """
        return {
            'traces_deleted': self.cleanup_old_traces(trace_days),
            'results_deleted': self.cleanup_old_results(result_days),
            'runs_deleted': self.cleanup_old_runs(run_days)
        }

    def get_retention_stats(self) -> dict:
        """Get statistics about data age and retention.

        Returns:
            Dictionary with retention statistics
        """
        now = datetime.utcnow()

        # Trace stats
        oldest_trace = self.db.query(Trace.created_at).order_by(
            Trace.created_at.asc()
        ).first()

        # Result stats
        oldest_result = self.db.query(EvaluationResult.created_at).order_by(
            EvaluationResult.created_at.asc()
        ).first()

        # Run stats
        oldest_run = self.db.query(EvaluationRun.created_at).filter(
            EvaluationRun.status.in_(['completed', 'failed', 'cancelled'])
        ).order_by(EvaluationRun.created_at.asc()).first()

        return {
            'trace_retention_days': settings.TRACE_RETENTION_DAYS,
            'result_retention_days': settings.RESULT_RETENTION_DAYS,
            'run_retention_days': settings.RUN_RETENTION_DAYS,
            'oldest_trace': oldest_trace[0].isoformat() if oldest_trace else None,
            'oldest_result': oldest_result[0].isoformat() if oldest_result else None,
            'oldest_run': oldest_run[0].isoformat() if oldest_run else None,
            'current_time': now.isoformat()
        }
