from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.agent import Agent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent entities."""

    def __init__(self, db: Session):
        super().__init__(Agent, db)

    def get_by_name(self, name: str) -> Agent | None:
        """Get agent by name."""
        stmt = select(Agent).where(Agent.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_adapter_type(self, adapter_type: str) -> list[Agent]:
        """Get agents by adapter type."""
        stmt = select(Agent).where(Agent.adapter_type == adapter_type)
        return list(self.db.execute(stmt).scalars().all())
