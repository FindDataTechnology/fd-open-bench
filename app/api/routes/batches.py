"""REST API routes for batch evaluations."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import asyncio
import uuid
from datetime import datetime
from app.database import get_db
from app.models import EvaluationRun, Agent, Benchmark
from app.models.evaluation_run import EvaluationRunStatus
from app.services.batch_evaluation import BatchEvaluationService
from app.services.comparison import ComparisonService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/batches", tags=["batches"])

# Semaphore for concurrency control (default 2)
batch_semaphore = asyncio.Semaphore(2)


class BatchCreate(BaseModel):
    """Schema for creating a batch evaluation."""
    benchmark_id: str
    agent_ids: List[str]
    evaluator_configs: List[Dict[str, Any]] = []


class BatchResponse(BaseModel):
    """Schema for batch response."""
    batch_id: str
    benchmark_id: str
    status: str
    agents: List[Dict[str, Any]]
    created_at: str


class BatchStatusResponse(BaseModel):
    """Schema for batch status response."""
    batch_id: str
    benchmark_id: str
    benchmark_name: str
    agents: List[Dict[str, Any]]


@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_data: BatchCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new batch evaluation for multiple agents on a benchmark."""
    # Validate benchmark exists
    benchmark = db.query(Benchmark).filter(Benchmark.id == batch_data.benchmark_id).first()
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark {batch_data.benchmark_id} not found"
        )

    # Validate agents exist
    agents = db.query(Agent).filter(Agent.id.in_(batch_data.agent_ids)).all()
    if len(agents) != len(batch_data.agent_ids):
        found_ids = {a.id for a in agents}
        missing = [aid for aid in batch_data.agent_ids if aid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {missing}"
        )

    # Create batch ID
    batch_id = str(uuid.uuid4())

    # Create evaluation runs for each agent
    runs = []
    for agent in agents:
        run = EvaluationRun(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            dataset_id=benchmark.dataset_id,
            benchmark_id=benchmark.id,
            batch_id=batch_id,
            status=EvaluationRunStatus.PENDING.value,
            tasks_total=0,  # Will be updated when evaluation starts
            tasks_completed=0,
            tasks_failed=0,
            current_cost=0.0,
            evaluation_config={
                'evaluators': batch_data.evaluator_configs,
                'batch_id': batch_id,
            }
        )
        db.add(run)
        runs.append(run)

    db.commit()

    # Start background tasks for each agent (with semaphore)
    batch_service = BatchEvaluationService(db)
    for run in runs:
        background_tasks.add_task(
            run_agent_evaluation,
            batch_service,
            run.id
        )

    return BatchResponse(
        batch_id=batch_id,
        benchmark_id=benchmark.id,
        status="running",
        agents=[{
            "run_id": run.id,
            "agent_id": run.agent_id,
            "agent_name": next(a.name for a in agents if a.id == run.agent_id),
            "status": run.status,
        } for run in runs],
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a batch evaluation."""
    comparison_service = ComparisonService(db)
    try:
        batch_data = comparison_service.get_batch_comparison(batch_id)
        return batch_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


async def run_agent_evaluation(batch_service: BatchEvaluationService, run_id: str):
    """Run evaluation for a single agent (with semaphore)."""
    async with batch_semaphore:
        try:
            # Execute the batch evaluation
            await batch_service.execute_batch_evaluation(run_id)
        except Exception as e:
            logger.error(f"Failed to execute evaluation for run {run_id}: {e}")
            # Update run status to failed
            # Note: This would need proper error handling in production