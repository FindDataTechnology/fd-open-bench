from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app.repositories import DatasetRepository, GoldenRepository
from pydantic import BaseModel


router = APIRouter(prefix="/datasets", tags=["Datasets"])


class DatasetCreate(BaseModel):
    name: str
    description: str | None = None


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str | None
    golden_count: int

    class Config:
        from_attributes = True


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all datasets."""
    repo = DatasetRepository(db)
    datasets = repo.get_all(skip=skip, limit=limit)
    return [d.to_dict() for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset by ID."""
    repo = DatasetRepository(db)
    dataset = repo.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = dataset.to_dict()
    result["golden_count"] = repo.get_golden_count(dataset_id)
    return result


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    data: DatasetCreate,
    db: Session = Depends(get_db),
):
    """Create a new dataset."""
    repo = DatasetRepository(db)

    # Check if dataset with same name exists
    existing = repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Dataset with this name already exists")

    dataset = repo.create(name=data.name, description=data.description)
    return dataset.to_dict()


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete a dataset (will cascade to goldens)."""
    repo = DatasetRepository(db)
    success = repo.delete(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": "Dataset deleted"}


@router.post("/{dataset_id}/goldens")
async def bulk_import_goldens(
    dataset_id: str,
    file_data: bytes = Depends(lambda file: file),  # Binary file data
    db: Session = Depends(get_db),
):
    """Bulk import goldens from JSON file."""
    try:
        goldens_data = json.loads(file_data.decode())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    repo = GoldenRepository(db)
    goldens = repo.bulk_create_from_dicts(dataset_id, goldens_data)

    return {
        "message": f"Imported {len(goldens)} goldens",
        "count": len(goldens),
    }


@router.get("/{dataset_id}/goldens", response_model=list[dict])
async def list_goldens(
    dataset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List goldens in a dataset."""
    repo = GoldenRepository(db)
    golden_list = repo.get_by_dataset(dataset_id)[skip : skip + limit]
    return [g.to_dict() for g in golden_list]


@router.delete("/test")
async def test_import(
    sample_json: str = '{"input": "Test input", "expected_output": "Expected output"}',
):
    """Test endpoint for imports."""
    return {"status": "ok", "received": sample_json}
