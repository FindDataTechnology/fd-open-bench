from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.repositories import EvaluationRunRepository, EvaluationResultRepository, DatasetRepository
from pydantic import BaseModel


router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


class EvaluationCreate(BaseModel):
    agent_id: str
    dataset_id: str
    evaluators: list[dict]
    aggregation_strategy: str = "tiered"


class EvaluationResponse(BaseModel):
    id: str
    agent_id: str
    dataset_id: str
    status: str
    tasks_total: int
    tasks_completed: int
    current_cost: float
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[EvaluationResponse])
async def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all evaluations."""
    repo = EvaluationRunRepository(db)
    runs = repo.get_all(skip=skip, limit=limit)
    return [r.to_dict() for r in runs]


@router.post("", response_model=EvaluationResponse)
async def create_evaluation(data: EvaluationCreate, db: Session = Depends(get_db)):
    """Start a new evaluation run."""
    # Validate inputs
    repo_dataset = DatasetRepository(db)
    if not repo_dataset.get(data.dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")

    # TODO: Create evaluation run and trigger Celery task
    # For now, return a mock response
    return {
        "id": f"run_{data.dataset_id}",
        "agent_id": data.agent_id,
        "dataset_id": data.dataset_id,
        "status": "pending",
        "tasks_total": 0,
        "tasks_completed": 0,
        "current_cost": 0.0,
        "created_at": "",
    }


@router.post("/{evaluation_id}/cancel")
async def cancel_evaluation(evaluation_id: str, db: Session = Depends(get_db)):
    """Cancel an evaluation run."""
    repo = EvaluationRunRepository(db)
    updated = repo.update_status(evaluation_id, "CANCELLED")
    if not updated:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {"message": "Evaluation cancelled"}


@router.post("/{evaluation_id}/retry")
async def retry_evaluation(evaluation_id: str, db: Session = Depends(get_db)):
    """Retry failed test cases in an evaluation."""
    repo = EvaluationRunRepository(db)
    # TODO: Implement retry logic
    return {"message": "Retry queued"}


@router.get("/{evaluation_id}/results")
async def get_evaluation_results(
    evaluation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get results for an evaluation run."""
    repo = EvaluationResultRepository(db)
    results = repo.get_by_run(evaluation_id, skip=skip, limit=limit)

    stats = repo.aggregate_stats(evaluation_id)

    return {
        "total_results": len(results),
        "statistics": stats,
        "results": [r.to_dict() for r in results],
    }
