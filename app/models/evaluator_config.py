from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import Column, String, Text, JSON, DateTime, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class EvaluatorType(str):
    """Evaluator type enum."""

    VALIDATOR = "validator"
    LLM_JUDGE = "llm_judge"
    EXECUTOR = "executor"


class EvaluatorConfig(Base):
    """Configuration for a reusable evaluator."""

    __tablename__ = "evaluator_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # validator, llm_judge, executor
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships (evaluators used in runs are referenced via run's evaluation_config)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


if TYPE_CHECKING:
    pass
