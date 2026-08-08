from sqlalchemy.orm import Session

from app.models.business_model import BusinessModel
from app.repositories.base import BaseRepository


class BusinessModelRepository(BaseRepository[BusinessModel]):
    """Repository for BusinessModel entities."""

    def __init__(self, db: Session):
        super().__init__(BusinessModel, db)

    def get_by_agent(self, agent_id: str) -> BusinessModel | None:
        """Get business model for an agent."""
        from sqlalchemy import select
        stmt = select(BusinessModel).where(BusinessModel.agent_id == agent_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_for_agent(
        self,
        agent_id: str,
        defaults: dict[str, any] | None = None
    ) -> BusinessModel:
        """Get existing or create new business model for agent."""
        instance = self.get_by_agent(agent_id)
        if instance:
            return instance

        kwargs = defaults or {}
        return self.create(agent_id=agent_id, **kwargs)

    def update_pricing_config(
        self,
        agent_id: str,
        pricing_config: dict[str, any]
    ) -> BusinessModel | None:
        """Update pricing configuration for an agent's business model."""
        instance = self.get_by_agent(agent_id)
        if not instance:
            return None

        instance.pricing_config.update(pricing_config)
        self.db.commit()
        self.db.refresh(instance)
        return instance
