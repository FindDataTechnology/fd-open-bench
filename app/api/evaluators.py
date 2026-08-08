from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.repositories import EvaluatorConfigRepository
from app.evaluators.registry import registry as eval_registry
from pydantic import BaseModel


router = APIRouter(prefix="/evaluators", tags=["Evaluators"])


class EvaluatorCreate(BaseModel):
    name: str
    type: str  # validator, llm_judge, executor
    config: dict


class EvaluatorResponse(BaseModel):
    id: str
    name: str
    type: str
    config: dict

    class Config:
        from_attributes = True


@router.get("", response_model=List[EvaluatorResponse])
async def list_evaluators(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all evaluators."""
    repo = EvaluatorConfigRepository(db)
    configs = repo.get_all(skip=skip, limit=limit)
    return [c.to_dict() for c in configs]


@router.get("/{evaluator_name}")
async def get_evaluator(evaluator_name: str, db: Session = Depends(get_db)):
    """Get evaluator by name (from registry or config)."""
    # Try registry first
    if evaluator := eval_registry.get(evaluator_name):
        return {
            "name": evaluator.name,
            "type": evaluator.type,
            "registered": True,
            "config": {},
        }

    # Then try database
    repo = EvaluatorConfigRepository(db)
    config = repo.get_by_name(evaluator_name)
    if not config:
        raise HTTPException(status_code=404, detail="Evaluator not found")

    return {
        "id": config.id,
        "name": config.name,
        "type": config.type,
        "config": config.config,
        "registered": False,
    }


@router.post("/test")
async def test_evaluator(name: str, input_text: str, output_text: str, db: Session = Depends(get_db)):
    """Test an evaluator on sample input/output."""
    from app.evaluators.protocols import EvaluationContext

    # Get evaluator
    if evaluator := eval_registry.get(name):
        context = EvaluationContext(input=input_text, output=output_text)
        result = await evaluator.evaluate(context)
        return {
            "evaluator": name,
            "score": result.score,
            "passed": result.passed,
            "reason": result.reason,
            "error": result.error,
        }

    # Load from database
    repo = EvaluatorConfigRepository(db)
    config = repo.get_by_name(name)
    if not config:
        raise HTTPException(status_code=404, detail="Evaluator not found")

    # Create instance from config
    try:
        evaluator = eval_registry.create_from_config({**config.config, "name": name})
        context = EvaluationContext(input=input_text, output=output_text)
        result = await evaluator.evaluate(context)
        return {
            "evaluator": name,
            "score": result.score,
            "passed": result.passed,
            "reason": result.reason,
            "error": result.error,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("")
async def create_evaluator(data: EvaluatorCreate, db: Session = Depends(get_db)):
    """Create a new evaluator configuration."""
    repo = EvaluatorConfigRepository(db)

    # Check if evaluator with same name exists
    existing = repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Evaluator with this name already exists")

    # Validate config
    try:
        evaluator = eval_registry.create_from_config({**data.model_dump(), "name": data.name})
        if not evaluator.validate_config(data.config):
            raise ValueError("Invalid evaluator configuration")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")

    # Save to database
    config = repo.create(name=data.name, type=data.type, config=data.config)
    return config.to_dict()


@router.put("/{evaluator_name}")
async def update_evaluator(
    evaluator_name: str,
    data: EvaluatorCreate,
    db: Session = Depends(get_db),
):
    """Update an evaluator configuration."""
    repo = EvaluatorConfigRepository(db)
    existing = repo.get_by_name(evaluator_name)

    if not existing:
        raise HTTPException(status_code=404, detail="Evaluator not found")

    # Validate config
    try:
        evaluator = eval_registry.create_from_config({**data.model_dump(), "name": evaluator_name})
        if not evaluator.validate_config(data.config):
            raise ValueError("Invalid evaluator configuration")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Update
    updated = repo.update(existing.id, type=data.type, config=data.config)
    return updated.to_dict()


@router.delete("/{evaluator_name}")
async def delete_evaluator(evaluator_name: str, db: Session = Depends(get_db)):
    """Delete an evaluator configuration."""
    repo = EvaluatorConfigRepository(db)
    config = repo.get_by_name(evaluator_name)
    if not config:
        raise HTTPException(status_code=404, detail="Evaluator not found")

    success = repo.delete(config.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete evaluator")

    return {"message": "Evaluator deleted"}
