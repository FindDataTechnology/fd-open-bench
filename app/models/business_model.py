import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class BusinessModel(Base):
    """Business value model for an agent."""

    __tablename__ = "business_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    pricing_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    # token_pricing, time_pricing, infrastructure_pricing
    value_formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Custom formula like "task_completion_score * deal_value"
    roi_targets: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    # minimum_roi, target_roi
    cost_alerts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    # threshold, metric
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="business_model")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "pricing_config": self.pricing_config,
            "value_formula": self.value_formula,
            "roi_targets": self.roi_targets,
            "cost_alerts": self.cost_alerts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


if TYPE_CHECKING:
    from .agent import Agent
