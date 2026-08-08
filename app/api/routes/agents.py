"""REST API routes for agents."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models import Agent
from app.repositories import AgentRepository

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str
    description: str = ""
    adapter_type: str = "openai"
    config: Dict[str, Any] = {}
    pricing_config: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: str = None
    description: str = None
    adapter_type: str = None
    config: Dict[str, Any] = None
    pricing_config: Dict[str, Any] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""
    id: str
    name: str
    description: str
    adapter_type: str
    config: Dict[str, Any]
    pricing_config: Dict[str, Any]
    created_at: str
    updated_at: str


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all agents."""
    repo = AgentRepository(db)
    agents = repo.get_all(skip=skip, limit=limit)
    return [agent.to_dict() for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get an agent by ID."""
    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    return agent.to_dict()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent."""
    repo = AgentRepository(db)

    # Check if agent with same name exists
    existing = repo.get_by_name(agent_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with name '{agent_data.name}' already exists"
        )

    agent = repo.create(
        name=agent_data.name,
        description=agent_data.description,
        adapter_type=agent_data.adapter_type,
        config=agent_data.config,
        pricing_config=agent_data.pricing_config
    )

    return agent.to_dict()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update an agent."""
    repo = AgentRepository(db)

    # Check if agent exists
    existing = repo.get(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    # Check if new name conflicts
    if agent_data.name and agent_data.name != existing.name:
        name_conflict = repo.get_by_name(agent_data.name)
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with name '{agent_data.name}' already exists"
            )

    # Update agent
    update_data = agent_data.dict(exclude_unset=True)
    agent = repo.update(agent_id, **update_data)

    return agent.to_dict()


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent."""
    repo = AgentRepository(db)

    # Check if agent exists
    existing = repo.get(agent_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    repo.delete(agent_id)
    return None


@router.get("/{agent_id}/evaluations")
async def get_agent_evaluations(
    agent_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get evaluation runs for an agent."""
    from app.repositories import EvaluationRunRepository

    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    run_repo = EvaluationRunRepository(db)
    runs = run_repo.get_by_agent(agent_id, skip=skip, limit=limit)

    return [run.to_dict() for run in runs]


@router.get("/{agent_id}/business-model")
async def get_agent_business_model(agent_id: str, db: Session = Depends(get_db)):
    """Get business model for an agent."""
    from app.repositories import BusinessModelRepository

    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    bm_repo = BusinessModelRepository(db)
    business_model = bm_repo.get_by_agent(agent_id)

    if not business_model:
        return {
            'agent_id': agent_id,
            'pricing_config': agent.pricing_config,
            'value_formula': None,
            'roi_targets': {},
            'cost_alerts': {}
        }

    return business_model.to_dict()
