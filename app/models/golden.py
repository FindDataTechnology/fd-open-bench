from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class Golden(Base):
    """Test case (Golden) for agent evaluation."""

    __tablename__ = "goldens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)  # What to send to agent
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)  # Ground truth
    expected_tools: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # Expected tool calls
    business_value: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )  # Value in $ if the task succeeds
    human_cost: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )  # Cost in $ for a human to complete the same task
    human_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Minutes a human would need for the task
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="goldens")
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="golden", lazy="selectin", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "input": self.input,
            "expected_output": self.expected_output,
            "expected_tools": self.expected_tools,
            "business_value": float(self.business_value) if self.business_value is not None else None,
            "human_cost": float(self.human_cost) if self.human_cost is not None else None,
            "human_minutes": self.human_minutes,
            "metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


if TYPE_CHECKING:
    from .dataset import Dataset
    from .evaluation_result import EvaluationResult
