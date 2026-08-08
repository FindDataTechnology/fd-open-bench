import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Column, String, Text, JSON, DateTime, ForeignKey, Index, Integer, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class EvaluationResultStatus(str, Enum):
    """Status of an evaluation result for a single test case."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class EvaluationResult(Base):
    """Evaluation result for a single test case in an evaluation run."""

    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    golden_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("goldens.id", ondelete="CASCADE"), nullable=False
    )
    agent_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # Compressed
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metric_scores: Mapped[dict[str, float]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # {metric_name: score}
    validator_results: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # {validator_name: {passed, reason}}
    business_value_delivered: Mapped[float | None] = mapped_column(
        "business_value_delivered", String(50), nullable=True
    )
    total_cost: Mapped[float | None] = mapped_column(
        "total_cost", String(50), nullable=True
    )  # Stored as string for precision
    status: Mapped[EvaluationResultStatus] = mapped_column(
        SQLEnum(EvaluationResultStatus), default=EvaluationResultStatus.SUCCESS
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["EvaluationRun"] = relationship(back_populates="results")
    golden: Mapped["Golden"] = relationship(back_populates="results")

    # Indexes
    __table_args__ = (
        Index("idx_result_run_status", "run_id", "status"),
        Index("idx_result_run_created", "run_id", "created_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "golden_id": self.golden_id,
            "agent_output": self.agent_output,
            "trace": self.trace,
            "token_usage": self.token_usage,
            "execution_time_ms": self.execution_time_ms,
            "metric_scores": self.metric_scores,
            "validator_results": self.validator_results,
            "business_value_delivered": float(self.business_value_delivered) if self.business_value_delivered else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


if TYPE_CHECKING:
    from .evaluation_run import EvaluationRun
    from .golden import Golden
