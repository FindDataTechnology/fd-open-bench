"""REST API routes for evaluations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import EvaluationRun, EvaluationResult
from app.repositories import EvaluationRunRepository, EvaluationResultRepository
from app.services.batch_evaluation import BatchEvaluationService

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


class EvaluationCreate(BaseModel):
    """Schema for creating an evaluation run."""
    agent_id: str
    dataset_id: str
    evaluator_configs: List[Dict[str, Any]]
    created_by: str = "system"


class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""
    id: str
    agent_id: str
    dataset_id: str
    status: str
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    current_cost: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results_summary: Dict[str, Any]


class EvaluationStatusResponse(BaseModel):
    """Schema for evaluation status response."""
    run_id: str
    status: str
    agent_id: str
    dataset_id: str
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    progress: float
    current_cost: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results_summary: Dict[str, Any]


class EvaluationResultResponse(BaseModel):
    """Schema for evaluation result response."""
    id: str
    run_id: str
    golden_id: str
    agent_output: str
    token_usage: Dict[str, Any]
    execution_time_ms: int
    metric_scores: Dict[str, float]
    validator_results: Dict[str, Any]
    business_value_delivered: float
    total_cost: float
    status: str
    error_message: str
    created_at: str


@router.get("/", response_model=List[EvaluationResponse])
async def list_evaluations(
    agent_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all evaluation runs."""
    repo = EvaluationRunRepository(db)

    if agent_id:
        runs = repo.get_by_agent(agent_id, skip=skip, limit=limit)
    else:
        runs = repo.get_all(skip=skip, limit=limit)

    if status:
        runs = [r for r in runs if r.status == status]

    return [run.to_dict() for run in runs]


@router.get("/{run_id}", response_model=EvaluationResponse)
async def get_evaluation(run_id: str, db: Session = Depends(get_db)):
    """Get an evaluation run by ID."""
    repo = EvaluationRunRepository(db)
    run = repo.get(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )
    return run.to_dict()


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    eval_data: EvaluationCreate,
    db: Session = Depends(get_db)
):
    """Create and start a new evaluation run."""
    service = BatchEvaluationService(db)

    try:
        run_id = await service.create_batch_evaluation(
            agent_id=eval_data.agent_id,
            dataset_id=eval_data.dataset_id,
            evaluator_configs=eval_data.evaluator_configs,
            created_by=eval_data.created_by
        )

        # Start execution in background
        # In production, this would be a Celery task
        import asyncio
        asyncio.create_task(service.execute_batch_evaluation(run_id))

        # Return the created run
        repo = EvaluationRunRepository(db)
        run = repo.get(run_id)
        return run.to_dict()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{run_id}/execute")
async def execute_evaluation(run_id: str, db: Session = Depends(get_db)):
    """Execute a pending evaluation run."""
    service = BatchEvaluationService(db)

    try:
        summary = await service.execute_batch_evaluation(run_id)
        return {
            'run_id': run_id,
            'status': 'completed',
            'summary': summary
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.post("/{run_id}/cancel")
async def cancel_evaluation(run_id: str, db: Session = Depends(get_db)):
    """Cancel a running evaluation."""
    service = BatchEvaluationService(db)

    try:
        await service.cancel_batch_evaluation(run_id)
        return {'run_id': run_id, 'status': 'cancelled'}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{run_id}/retry")
async def retry_evaluation(run_id: str, db: Session = Depends(get_db)):
    """Retry a failed evaluation."""
    service = BatchEvaluationService(db)

    try:
        new_run_id = await service.retry_failed_evaluation(run_id)
        return {
            'original_run_id': run_id,
            'new_run_id': new_run_id,
            'status': 'retried'
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{run_id}/status", response_model=EvaluationStatusResponse)
async def get_evaluation_status(run_id: str, db: Session = Depends(get_db)):
    """Get the status of an evaluation run."""
    service = BatchEvaluationService(db)

    try:
        status_data = await service.get_batch_evaluation_status(run_id)
        return status_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{run_id}/results", response_model=List[EvaluationResultResponse])
async def get_evaluation_results(
    run_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get results for an evaluation run."""
    # Check if run exists
    run_repo = EvaluationRunRepository(db)
    run = run_repo.get(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )

    repo = EvaluationResultRepository(db)
    results = repo.get_by_run(run_id, skip=skip, limit=limit)
    return [result.to_dict() for result in results]


@router.get("/{run_id}/results/summary")
async def get_results_summary(run_id: str, db: Session = Depends(get_db)):
    """Get aggregated summary of evaluation results."""
    # Check if run exists
    run_repo = EvaluationRunRepository(db)
    run = run_repo.get(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )

    repo = EvaluationResultRepository(db)
    stats = repo.aggregate_stats(run_id)
    return stats


@router.get("/results/{result_id}", response_model=EvaluationResultResponse)
async def get_evaluation_result(result_id: str, db: Session = Depends(get_db)):
    """Get a specific evaluation result."""
    repo = EvaluationResultRepository(db)
    result = repo.get(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation result {result_id} not found"
        )
    return result.to_dict()


@router.get("/results/{result_id}/trace")
async def get_result_trace(result_id: str, db: Session = Depends(get_db)):
    """Get the trace for an evaluation result."""
    from app.services.trace_persistence import TracePersistenceService

    repo = EvaluationResultRepository(db)
    result = repo.get(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation result {result_id} not found"
        )

    if not result.trace:
        return {'trace': None}

    # Decompress trace
    from app.utils.compression import decompress_trace
    return {'trace': decompress_trace(result.trace)}


@router.get("/results/{result_id}/trace/export")
async def export_result_trace(
    result_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Export trace in different formats."""
    from app.services.trace_persistence import TraceExportService

    repo = EvaluationResultRepository(db)
    result = repo.get(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation result {result_id} not found"
        )

    if not result.trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trace available for this result"
        )

    service = TraceExportService(db)

    # Traces are stored compressed on the evaluation result itself, not in
    # the traces table — decompress and export the in-memory trace.
    from app.models.trace import Trace
    from app.utils.compression import decompress_trace
    trace = Trace(**decompress_trace(result.trace))

    if format == "json":
        return service.export_trace_as_json(trace)
    elif format == "otel":
        return service.export_trace_as_opentelemetry(trace)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )


@router.get("/{run_id}/export")
async def export_evaluation(
    run_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Export evaluation results in different formats."""
    # Check if run exists
    run_repo = EvaluationRunRepository(db)
    run = run_repo.get(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )

    if format == "json":
        return run.to_dict()
    elif format == "csv":
        # TODO: Implement CSV export
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="CSV export not yet implemented"
        )
    elif format == "pdf":
        # TODO: Implement PDF export
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF export not yet implemented"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )
