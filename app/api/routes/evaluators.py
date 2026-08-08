"""REST API routes for evaluators."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models import EvaluatorConfig
from app.repositories import EvaluatorConfigRepository
from app.evaluators.registry import EvaluatorRegistry

router = APIRouter(prefix="/api/v1/evaluators", tags=["evaluators"])


class EvaluatorCreate(BaseModel):
    """Schema for creating an evaluator."""
    name: str
    type: str
    config: Dict[str, Any] = {}


class EvaluatorUpdate(BaseModel):
    """Schema for updating an evaluator."""
    name: str = None
    type: str = None
    config: Dict[str, Any] = None


class EvaluatorResponse(BaseModel):
    """Schema for evaluator response."""
    id: str
    name: str
    type: str
    config: Dict[str, Any]
    created_at: str
    updated_at: str


class EvaluatorTestRequest(BaseModel):
    """Schema for testing an evaluator."""
    input_text: str
    output_text: str
    expected_output: str = None
    context: Dict[str, Any] = {}


class EvaluatorTestResponse(BaseModel):
    """Schema for evaluator test response."""
    evaluator_name: str
    score: float
    passed: bool
    reason: str
    metadata: Dict[str, Any]
    execution_time_ms: float
    cost: float
    error: str


@router.get("/", response_model=List[EvaluatorResponse])
async def list_evaluators(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all evaluators."""
    repo = EvaluatorConfigRepository(db)
    evaluators = repo.get_all(skip=skip, limit=limit)
    return [evaluator.to_dict() for evaluator in evaluators]


@router.get("/{evaluator_id}", response_model=EvaluatorResponse)
async def get_evaluator(evaluator_id: str, db: Session = Depends(get_db)):
    """Get an evaluator by ID."""
    repo = EvaluatorConfigRepository(db)
    evaluator = repo.get(evaluator_id)
    if not evaluator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluator {evaluator_id} not found"
        )
    return evaluator.to_dict()


@router.post("/", response_model=EvaluatorResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluator(
    evaluator_data: EvaluatorCreate,
    db: Session = Depends(get_db)
):
    """Create a new evaluator."""
    repo = EvaluatorConfigRepository(db)

    # Check if evaluator with same name exists
    existing = repo.get_by_name(evaluator_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluator with name '{evaluator_data.name}' already exists"
        )

    # Validate evaluator config
    registry = EvaluatorRegistry()
    try:
        registry.create_from_config({
            'name': evaluator_data.name,
            'type': evaluator_data.type,
            **evaluator_data.config
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid evaluator configuration: {str(e)}"
        )

    evaluator = repo.create(
        name=evaluator_data.name,
        type=evaluator_data.type,
        config=evaluator_data.config
    )

    return evaluator.to_dict()


@router.put("/{evaluator_id}", response_model=EvaluatorResponse)
async def update_evaluator(
    evaluator_id: str,
    evaluator_data: EvaluatorUpdate,
    db: Session = Depends(get_db)
):
    """Update an evaluator."""
    repo = EvaluatorConfigRepository(db)

    # Check if evaluator exists
    existing = repo.get(evaluator_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluator {evaluator_id} not found"
        )

    # Check if new name conflicts
    if evaluator_data.name and evaluator_data.name != existing.name:
        name_conflict = repo.get_by_name(evaluator_data.name)
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evaluator with name '{evaluator_data.name}' already exists"
            )

    # Validate new config if provided
    if evaluator_data.config or evaluator_data.type:
        registry = EvaluatorRegistry()
        config = evaluator_data.config or existing.config
        eval_type = evaluator_data.type or existing.type
        try:
            registry.create_from_config({
                'name': evaluator_data.name or existing.name,
                'type': eval_type,
                **config
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid evaluator configuration: {str(e)}"
            )

    # Update evaluator
    update_data = evaluator_data.dict(exclude_unset=True)
    evaluator = repo.update(evaluator_id, **update_data)

    return evaluator.to_dict()


@router.delete("/{evaluator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluator(evaluator_id: str, db: Session = Depends(get_db)):
    """Delete an evaluator."""
    repo = EvaluatorConfigRepository(db)

    # Check if evaluator exists
    existing = repo.get(evaluator_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluator {evaluator_id} not found"
        )

    repo.delete(evaluator_id)
    return None


@router.post("/test", response_model=EvaluatorTestResponse)
async def test_evaluator(
    evaluator_data: EvaluatorCreate,
    test_request: EvaluatorTestRequest,
    db: Session = Depends(get_db)
):
    """Test an evaluator configuration."""
    from app.evaluators.protocols import EvaluationContext
    import asyncio

    registry = EvaluatorRegistry()

    try:
        # Create evaluator from config
        evaluator = registry.create_from_config({
            'name': evaluator_data.name,
            'type': evaluator_data.type,
            **evaluator_data.config
        })

        # Create evaluation context
        context = EvaluationContext(
            input=test_request.input_text,
            output=test_request.output_text,
            expected_output=test_request.expected_output,
            trace=test_request.context.get('trace'),
            token_usage=test_request.context.get('token_usage'),
            execution_time_ms=test_request.context.get('execution_time_ms'),
            agent_config=test_request.context.get('agent_config', {}),
            golden_metadata=test_request.context.get('golden_metadata', {}),
            business_context=test_request.context.get('business_context', {})
        )

        # Run evaluator
        result = asyncio.run(evaluator.evaluate(context))

        return EvaluatorTestResponse(
            evaluator_name=evaluator_data.name,
            score=result.score,
            passed=result.passed,
            reason=result.reason,
            metadata=result.metadata,
            execution_time_ms=result.execution_time_ms,
            cost=result.cost,
            error=result.error
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluator test failed: {str(e)}"
        )


@router.post("/{evaluator_id}/test", response_model=EvaluatorTestResponse)
async def test_saved_evaluator(
    evaluator_id: str,
    test_request: EvaluatorTestRequest,
    db: Session = Depends(get_db)
):
    """Test a saved evaluator configuration."""
    from app.evaluators.protocols import EvaluationContext
    import asyncio

    repo = EvaluatorConfigRepository(db)

    # Get evaluator config
    evaluator_config = repo.get(evaluator_id)
    if not evaluator_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluator {evaluator_id} not found"
        )

    registry = EvaluatorRegistry()

    try:
        # Create evaluator from saved config
        evaluator = registry.create_from_config({
            'name': evaluator_config.name,
            'type': evaluator_config.type,
            **evaluator_config.config
        })

        # Create evaluation context
        context = EvaluationContext(
            input=test_request.input_text,
            output=test_request.output_text,
            expected_output=test_request.expected_output,
            trace=test_request.context.get('trace'),
            token_usage=test_request.context.get('token_usage'),
            execution_time_ms=test_request.context.get('execution_time_ms'),
            agent_config=test_request.context.get('agent_config', {}),
            golden_metadata=test_request.context.get('golden_metadata', {}),
            business_context=test_request.context.get('business_context', {})
        )

        # Run evaluator
        result = asyncio.run(evaluator.evaluate(context))

        return EvaluatorTestResponse(
            evaluator_name=evaluator_config.name,
            score=result.score,
            passed=result.passed,
            reason=result.reason,
            metadata=result.metadata,
            execution_time_ms=result.execution_time_ms,
            cost=result.cost,
            error=result.error
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluator test failed: {str(e)}"
        )


@router.get("/types")
async def list_evaluator_types():
    """List available evaluator types."""
    return {
        'validators': [
            'regex',
            'json_schema',
            'keyword',
            'length',
            'contains',
            'format'
        ],
        'llm_judges': [
            'deepeval_metric',
            'custom_prompt',
            'comparative'
        ],
        'executors': [
            'sql',
            'api',
            'code',
            'business_logic'
        ]
    }


@router.get("/types/{evaluator_type}/schema")
async def get_evaluator_schema(evaluator_type: str):
    """Get the configuration schema for an evaluator type."""
    schemas = {
        'regex': {
            'pattern': {'type': 'string', 'required': True},
            'must_match': {'type': 'boolean', 'default': True},
            'flags': {'type': 'integer', 'default': 0}
        },
        'json_schema': {
            'schema': {'type': 'object', 'required': True}
        },
        'keyword': {
            'keywords': {'type': 'array', 'items': {'type': 'string'}, 'required': True},
            'mode': {'type': 'string', 'enum': ['all', 'any', 'none'], 'default': 'all'}
        },
        'length': {
            'min_length': {'type': 'integer'},
            'max_length': {'type': 'integer'},
            'unit': {'type': 'string', 'enum': ['chars', 'words'], 'default': 'chars'}
        },
        'contains': {
            'substring': {'type': 'string', 'required': True},
            'case_sensitive': {'type': 'boolean', 'default': True}
        },
        'format': {
            'format': {'type': 'string', 'enum': ['email', 'url', 'phone', 'date'], 'required': True}
        },
        'deepeval_metric': {
            'metric': {'type': 'string', 'required': True},
            'threshold': {'type': 'number', 'default': 0.5},
            'model': {'type': 'string', 'default': 'gpt-4o'}
        },
        'custom_prompt': {
            'prompt': {'type': 'string', 'required': True},
            'score_range': {'type': 'array', 'items': {'type': 'number'}, 'default': [0, 10]},
            'threshold': {'type': 'number', 'default': 0.7},
            'model': {'type': 'string', 'default': 'gpt-4o'}
        },
        'comparative': {
            'prompt': {'type': 'string', 'required': True},
            'model': {'type': 'string', 'default': 'gpt-4o'}
        },
        'sql': {
            'connection': {'type': 'string', 'required': True},
            'validation': {'type': 'object', 'required': True},
            'read_only': {'type': 'boolean', 'default': True}
        },
        'api': {
            'validation': {'type': 'object', 'required': True}
        },
        'code': {
            'language': {'type': 'string', 'default': 'python'},
            'test_cases': {'type': 'array'},
            'timeout': {'type': 'integer', 'default': 10},
            'memory_limit': {'type': 'string', 'default': '256m'}
        },
        'business_logic': {
            'module': {'type': 'string', 'required': True},
            'function': {'type': 'string', 'required': True},
            'config': {'type': 'object'}
        }
    }

    if evaluator_type not in schemas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluator type '{evaluator_type}' not found"
        )

    return {
        'type': evaluator_type,
        'schema': schemas[evaluator_type]
    }
