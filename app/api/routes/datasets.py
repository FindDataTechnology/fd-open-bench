"""REST API routes for datasets and goldens."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import json
from app.database import get_db
from app.models import Dataset, Golden
from app.repositories import DatasetRepository, GoldenRepository

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


class DatasetCreate(BaseModel):
    """Schema for creating a dataset."""
    name: str
    description: str = ""


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset."""
    name: str = None
    description: str = None


class DatasetResponse(BaseModel):
    """Schema for dataset response."""
    id: str
    name: str
    description: str
    golden_count: int
    created_at: str
    updated_at: str


class GoldenCreate(BaseModel):
    """Schema for creating a golden."""
    input: str
    expected_output: str = None
    expected_tools: List[Dict[str, Any]] = None
    business_value: float = None
    human_cost: float = None
    human_minutes: int = None
    metadata: Dict[str, Any] = {}


class GoldenResponse(BaseModel):
    """Schema for golden response."""
    id: str
    dataset_id: str
    input: str
    expected_output: str | None = None
    expected_tools: List[Dict[str, Any]] | None = None
    business_value: float | None = None
    human_cost: float | None = None
    human_minutes: int | None = None
    metadata: Dict[str, Any]
    created_at: str


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all datasets."""
    repo = DatasetRepository(db)
    datasets = repo.get_all(skip=skip, limit=limit)

    results = []
    for dataset in datasets:
        data = dataset.to_dict()
        data['golden_count'] = repo.get_golden_count(dataset.id)
        results.append(data)

    return results


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get a dataset by ID."""
    repo = DatasetRepository(db)
    dataset = repo.get(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    data = dataset.to_dict()
    data['golden_count'] = repo.get_golden_count(dataset_id)
    return data


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(dataset_data: DatasetCreate, db: Session = Depends(get_db)):
    """Create a new dataset."""
    repo = DatasetRepository(db)

    # Check if dataset with same name exists
    existing = repo.get_by_name(dataset_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset with name '{dataset_data.name}' already exists"
        )

    dataset = repo.create(
        name=dataset_data.name,
        description=dataset_data.description
    )

    data = dataset.to_dict()
    data['golden_count'] = 0
    return data


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    dataset_data: DatasetUpdate,
    db: Session = Depends(get_db)
):
    """Update a dataset."""
    repo = DatasetRepository(db)

    # Check if dataset exists
    existing = repo.get(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Check if new name conflicts
    if dataset_data.name and dataset_data.name != existing.name:
        name_conflict = repo.get_by_name(dataset_data.name)
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset with name '{dataset_data.name}' already exists"
            )

    # Update dataset
    update_data = dataset_data.dict(exclude_unset=True)
    dataset = repo.update(dataset_id, **update_data)

    data = dataset.to_dict()
    data['golden_count'] = repo.get_golden_count(dataset_id)
    return data


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete a dataset (cascades to goldens)."""
    repo = DatasetRepository(db)

    # Check if dataset exists
    existing = repo.get(dataset_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    repo.delete(dataset_id)
    return None


@router.get("/{dataset_id}/goldens", response_model=List[GoldenResponse])
async def list_goldens(
    dataset_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all goldens in a dataset."""
    # Check if dataset exists
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    repo = GoldenRepository(db)
    goldens = repo.get_by_dataset(dataset_id, skip=skip, limit=limit)
    return [golden.to_dict() for golden in goldens]


@router.post("/{dataset_id}/goldens", response_model=GoldenResponse, status_code=status.HTTP_201_CREATED)
async def create_golden(
    dataset_id: str,
    golden_data: GoldenCreate,
    db: Session = Depends(get_db)
):
    """Create a new golden in a dataset."""
    # Check if dataset exists
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    repo = GoldenRepository(db)
    golden = repo.create(
        dataset_id=dataset_id,
        input=golden_data.input,
        expected_output=golden_data.expected_output,
        expected_tools=golden_data.expected_tools,
        business_value=golden_data.business_value,
        human_cost=golden_data.human_cost,
        human_minutes=golden_data.human_minutes,
        metadata=golden_data.metadata
    )

    return golden.to_dict()


@router.post("/{dataset_id}/goldens/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_goldens(
    dataset_id: str,
    goldens_data: List[GoldenCreate],
    db: Session = Depends(get_db)
):
    """Bulk create goldens in a dataset."""
    # Check if dataset exists
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    repo = GoldenRepository(db)
    goldens_dicts = []
    for g in goldens_data:
        goldens_dicts.append({
            "input": g.input,
            "expected_output": g.expected_output,
            "expected_tools": g.expected_tools,
            "business_value": g.business_value,
            "human_cost": g.human_cost,
            "human_minutes": g.human_minutes,
            "metadata": g.metadata,
        })
    goldens = repo.bulk_create_from_dicts(dataset_id, goldens_dicts)

    return {
        'created': len(goldens),
        'golden_ids': [g.id for g in goldens]
    }


@router.post("/{dataset_id}/goldens/import")
async def import_goldens(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import goldens from a JSON file."""
    # Check if dataset exists
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Read and parse file
    try:
        content = await file.read()
        goldens_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )

    if not isinstance(goldens_data, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON file must contain an array of goldens"
        )

    # Create goldens
    repo = GoldenRepository(db)
    # Ensure business_value/human_cost/human_minutes are in each golden dict
    for g in goldens_data:
        if 'metadata' not in g:
            g['metadata'] = {}
    goldens = repo.bulk_create_from_dicts(dataset_id, goldens_data)

    return {
        'imported': len(goldens),
        'golden_ids': [g.id for g in goldens]
    }


@router.get("/goldens/{golden_id}", response_model=GoldenResponse)
async def get_golden(golden_id: str, db: Session = Depends(get_db)):
    """Get a golden by ID."""
    repo = GoldenRepository(db)
    golden = repo.get(golden_id)
    if not golden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Golden {golden_id} not found"
        )
    return golden.to_dict()


@router.put("/goldens/{golden_id}", response_model=GoldenResponse)
async def update_golden(
    golden_id: str,
    golden_data: GoldenCreate,
    db: Session = Depends(get_db)
):
    """Update a golden."""
    repo = GoldenRepository(db)

    # Check if golden exists
    existing = repo.get(golden_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Golden {golden_id} not found"
        )

    # Update golden
    golden = repo.update(
        golden_id,
        input=golden_data.input,
        expected_output=golden_data.expected_output,
        expected_tools=golden_data.expected_tools,
        business_value=golden_data.business_value,
        human_cost=golden_data.human_cost,
        human_minutes=golden_data.human_minutes,
        metadata=golden_data.metadata
    )

    return golden.to_dict()


@router.delete("/goldens/{golden_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_golden(golden_id: str, db: Session = Depends(get_db)):
    """Delete a golden."""
    repo = GoldenRepository(db)

    # Check if golden exists
    existing = repo.get(golden_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Golden {golden_id} not found"
        )

    repo.delete(golden_id)
    return None
