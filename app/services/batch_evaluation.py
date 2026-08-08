"""Batch evaluation system for processing multiple evaluations."""

from typing import Dict, Any, List
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session
from app.models import Agent, EvaluationRun, Dataset, Golden
from app.services.evaluation_engine import EvaluationEngine
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class BatchEvaluationService:
    """Service for batch evaluation processing."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = EvaluationEngine(db)

    async def create_batch_evaluation(
        self,
        agent_id: str,
        dataset_id: str,
        evaluator_configs: List[Dict[str, Any]],
        created_by: str = "system"
    ) -> str:
        """Create a new batch evaluation run.

        Args:
            agent_id: Agent ID to evaluate
            dataset_id: Dataset ID with test cases
            evaluator_configs: List of evaluator configurations
            created_by: User who created the run

        Returns:
            Evaluation run ID
        """
        # Validate agent exists
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Validate dataset exists and get golden count
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        golden_count = self.db.query(Golden).filter(Golden.dataset_id == dataset_id).count()
        if golden_count == 0:
            raise ValueError(f"Dataset {dataset_id} has no test cases")

        # Create evaluation run
        run = EvaluationRun(
            agent_id=agent_id,
            dataset_id=dataset_id,
            status='pending',
            tasks_total=golden_count,
            tasks_completed=0,
            tasks_failed=0,
            current_cost=0.0,
            evaluation_config={
                'evaluators': evaluator_configs,
                'created_by': created_by
            }
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        logger.info(f"Created batch evaluation run {run.id} for agent {agent_id}")

        return run.id

    async def execute_batch_evaluation(self, run_id: str) -> Dict[str, Any]:
        """Execute a batch evaluation run.

        Args:
            run_id: Evaluation run ID

        Returns:
            Execution summary
        """
        # Get evaluation run
        run = self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")

        if run.status not in ['pending', 'failed']:
            raise ValueError(f"Evaluation run {run_id} is already {run.status}")

        # Update status to running
        run.status = 'running'
        run.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Run evaluation
            summary = await self.engine.run_evaluation(
                run_id=run.id,
                agent_id=run.agent_id,
                dataset_id=run.dataset_id,
                evaluator_configs=run.evaluation_config['evaluators']
            )

            # Update run with results
            run.status = 'completed'
            run.completed_at = datetime.utcnow()
            run.tasks_completed = summary['successful']
            run.tasks_failed = summary['failed']
            run.current_cost = summary['total_cost']
            run.results_summary = summary
            self.db.commit()

            logger.info(f"Completed batch evaluation run {run_id}")

            return summary

        except Exception as e:
            # Update run with error
            run.status = 'failed'
            run.completed_at = datetime.utcnow()
            run.results_summary = {'error': str(e)}
            self.db.commit()

            logger.error(f"Failed batch evaluation run {run_id}: {e}")
            raise

    async def cancel_batch_evaluation(self, run_id: str) -> bool:
        """Cancel a running batch evaluation.

        Args:
            run_id: Evaluation run ID

        Returns:
            True if cancelled successfully
        """
        run = self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")

        if run.status != 'running':
            raise ValueError(f"Evaluation run {run_id} is not running")

        run.status = 'cancelled'
        run.completed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Cancelled batch evaluation run {run_id}")

        return True

    async def get_batch_evaluation_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a batch evaluation run.

        Args:
            run_id: Evaluation run ID

        Returns:
            Status information
        """
        run = self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")

        # Calculate progress
        progress = (run.tasks_completed / run.tasks_total * 100) if run.tasks_total > 0 else 0

        return {
            'run_id': run.id,
            'status': run.status,
            'agent_id': run.agent_id,
            'dataset_id': run.dataset_id,
            'tasks_total': run.tasks_total,
            'tasks_completed': run.tasks_completed,
            'tasks_failed': run.tasks_failed,
            'progress': progress,
            'current_cost': run.current_cost,
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
            'results_summary': run.results_summary
        }

    async def list_batch_evaluations(
        self,
        agent_id: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List batch evaluation runs.

        Args:
            agent_id: Filter by agent ID
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of evaluation runs
        """
        query = self.db.query(EvaluationRun)

        if agent_id:
            query = query.filter(EvaluationRun.agent_id == agent_id)

        if status:
            query = query.filter(EvaluationRun.status == status)

        query = query.order_by(EvaluationRun.created_at.desc())
        query = query.offset(offset).limit(limit)

        runs = query.all()

        return [
            {
                'run_id': run.id,
                'agent_id': run.agent_id,
                'dataset_id': run.dataset_id,
                'status': run.status,
                'tasks_total': run.tasks_total,
                'tasks_completed': run.tasks_completed,
                'tasks_failed': run.tasks_failed,
                'current_cost': run.current_cost,
                'created_at': run.created_at.isoformat(),
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'completed_at': run.completed_at.isoformat() if run.completed_at else None
            }
            for run in runs
        ]

    async def retry_failed_evaluation(self, run_id: str) -> str:
        """Retry a failed batch evaluation.

        Args:
            run_id: Evaluation run ID

        Returns:
            New evaluation run ID
        """
        run = self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")

        if run.status != 'failed':
            raise ValueError(f"Evaluation run {run_id} is not failed")

        # Create new run with same configuration
        new_run_id = await self.create_batch_evaluation(
            agent_id=run.agent_id,
            dataset_id=run.dataset_id,
            evaluator_configs=run.evaluation_config['evaluators'],
            created_by=run.evaluation_config.get('created_by', 'system')
        )

        logger.info(f"Retried failed evaluation run {run_id} as {new_run_id}")

        return new_run_id
