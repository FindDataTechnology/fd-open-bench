from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.agent import Agent
from app.repositories import AgentRepository
from pydantic import BaseModel


router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    adapter_type: str = "custom"
    config: dict = {}
    pricing_config: dict = {}


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    adapter_type: str | None = None
    config: dict | None = None
    pricing_config: dict | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str | None
    version: str
    adapter_type: str
    config: dict
    pricing_config: dict

    class Config:
        from_attributes = True


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all agents."""
    repo = AgentRepository(db)
    agents = repo.get_all(skip=skip, limit=limit)
    return [a.to_dict() for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID."""
    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_dict()


@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
):
    """Create a new agent."""
    repo = AgentRepository(db)

    # Check if agent with same name exists
    existing = repo.get_by_name(agent_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")

    agent = repo.create(**agent_data.model_dump())
    return agent.to_dict()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
):
    """Update an agent."""
    repo = AgentRepository(db)
    updated = repo.update(agent_id, **agent_data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated.to_dict()


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent."""
    repo = AgentRepository(db)
    success = repo.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}
