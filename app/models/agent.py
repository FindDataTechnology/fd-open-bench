from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class Agent(Base):
    """Agent configuration model."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="0.1.0")
    adapter_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="custom"
    )  # openai, langchain, custom
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # model, tools, system prompt, adapter-specific settings
    pricing_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # token pricing, time pricing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    evaluations: Mapped[list["EvaluationRun"]] = relationship(
        back_populates="agent", lazy="dynamic"
    )
    business_model: Mapped["BusinessModel | None"] = relationship(
        back_populates="agent", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "adapter_type": self.adapter_type,
            "config": self.config,
            "pricing_config": self.pricing_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
