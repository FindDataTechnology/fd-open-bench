from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.repositories import GoldenRepository
from pydantic import BaseModel


router = APIRouter(prefix="/goldens", tags=["Goldens"])


class GoldenCreate(BaseModel):
    dataset_id: str
    input: str
    expected_output: str | None = None
    expected_tools: list[dict] | None = None
    business_value: float | None = None
    metadata: dict = {}


@router.get("", response_model=List[dict])
async def list_goldens(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all goldens (with pagination)."""
    repo = GoldenRepository(db)
    goldens = repo.get_all(skip=skip, limit=limit)
    return [g.to_dict() for g in goldens]


@router.post("/test")
async def test_import(payload: dict):
    """Test endpoint for golden imports."""
    return {"status": "ok", "received": payload}
