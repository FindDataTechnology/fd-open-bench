"""REST API routes for benchmarks."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
import uuid
from pydantic import BaseModel
from app.database import get_db
from app.models.benchmark import Benchmark
from app.repositories.dataset import DatasetRepository
from app.utils.expression import validate_formula, FormulaError
from app.services.comparison import ComparisonService

router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarks"])


class BenchmarkCreate(BaseModel):
    """Schema for creating a benchmark."""
    name: str
    description: str = ""
    dataset_id: str
    metric_suite: list = []
    value_formula: str = "business_value * success_score"
    time_value_rate: float = 0.0


class BenchmarkUpdate(BaseModel):
    """Schema for updating a benchmark."""
    name: str = None
    description: str = None
    dataset_id: str = None
    metric_suite: list = None
    value_formula: str = None
    time_value_rate: float = None


class BenchmarkResponse(BaseModel):
    """Schema for benchmark response."""
    id: str
    name: str
    description: str
    dataset_id: str
    metric_suite: list
    value_formula: str
    time_value_rate: float
    created_at: str
    updated_at: str


@router.get("/", response_model=List[BenchmarkResponse])
async def list_benchmarks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all benchmarks."""
    stmt = select(Benchmark).offset(skip).limit(limit)
    results = list(db.execute(stmt).scalars().all())
    return [benchmark.to_dict() for benchmark in results]


@router.post("/", response_model=BenchmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_benchmark(benchmark_data: BenchmarkCreate, db: Session = Depends(get_db)):
    """Create a new benchmark."""
    # Validate value formula
    try:
        validate_formula(benchmark_data.value_formula)
    except FormulaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value formula: {str(e)}"
        )

    # Check dataset existence
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(benchmark_data.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {benchmark_data.dataset_id} not found"
        )

    # Create benchmark
    benchmark = Benchmark(
        id=str(uuid.uuid4()),
        name=benchmark_data.name,
        description=benchmark_data.description,
        dataset_id=benchmark_data.dataset_id,
        metric_suite=benchmark_data.metric_suite,
        value_formula=benchmark_data.value_formula,
        time_value_rate=benchmark_data.time_value_rate,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)

    return benchmark.to_dict()


@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(benchmark_id: str, db: Session = Depends(get_db)):
    """Get a benchmark by ID."""
    benchmark = db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark {benchmark_id} not found"
        )
    return benchmark.to_dict()


@router.put("/{benchmark_id}", response_model=BenchmarkResponse)
async def update_benchmark(
    benchmark_id: str,
    benchmark_data: BenchmarkUpdate,
    db: Session = Depends(get_db)
):
    """Update a benchmark."""
    benchmark = db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark {benchmark_id} not found"
        )

    # Validate value formula if provided
    if benchmark_data.value_formula:
        try:
            validate_formula(benchmark_data.value_formula)
        except FormulaError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value formula: {str(e)}"
            )

    # Check dataset existence if changed
    if benchmark_data.dataset_id and benchmark_data.dataset_id != benchmark.dataset_id:
        dataset_repo = DatasetRepository(db)
        dataset = dataset_repo.get(benchmark_data.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {benchmark_data.dataset_id} not found"
            )

    # Update benchmark
    update_data = benchmark_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(benchmark, key, value)

    db.commit()
    db.refresh(benchmark)

    return benchmark.to_dict()


@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_benchmark(benchmark_id: str, db: Session = Depends(get_db)):
    """Delete a benchmark."""
    benchmark = db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark {benchmark_id} not found"
        )
    db.delete(benchmark)
    db.commit()
    return None


@router.get("/{benchmark_id}/leaderboard")
async def get_benchmark_leaderboard(
    benchmark_id: str,
    batch_id: Optional[str] = None,
    sort_by: str = "cost_per_success",
    sort_order: str = "asc",
    db: Session = Depends(get_db)
):
    """Get leaderboard for a benchmark.

    Returns agent comparison data sorted by specified field.
    """
    # Validate benchmark exists
    benchmark = db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark {benchmark_id} not found"
        )

    comparison_service = ComparisonService(db)
    try:
        leaderboard = comparison_service.get_benchmark_leaderboard(
            benchmark_id=benchmark_id,
            batch_id=batch_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return {
            "benchmark_id": benchmark_id,
            "benchmark_name": benchmark.name,
            "leaderboard": leaderboard,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
