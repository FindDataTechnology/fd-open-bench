import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Column, String, Text, JSON, DateTime, ForeignKey, Integer, Index, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class EvaluationRunStatus(str, Enum):
    """Status of an evaluation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class EvaluationRun(Base):
    """Evaluation run containing multiple evaluation results."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    benchmark_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("benchmarks.id", ondelete="SET NULL"), nullable=True
    )  # Set when the run belongs to a benchmark batch
    batch_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # Groups runs of one batch (N agents × same benchmark)
    evaluation_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # evaluators, aggregation strategy, weights
    status: Mapped[EvaluationRunStatus] = mapped_column(
        SQLEnum(EvaluationRunStatus), default=EvaluationRunStatus.PENDING
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tasks_total: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0)
    current_cost: Mapped[float] = mapped_column(
        "current_cost", String(50), default=0.0
    )  # Stored as string for precision
    results_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )  # Aggregate metrics
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="evaluations")
    dataset: Mapped["Dataset"] = relationship()
    benchmark: Mapped["Benchmark | None"] = relationship(back_populates="runs")
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run", lazy="selectin", cascade="all, delete-orphan"
    )
    trace: Mapped["TraceDB"] = relationship(
        back_populates="run", uselist=False, cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_run_agent_created", "agent_id", "created_at"),
        Index("idx_run_status_created", "status", "created_at"),
        Index("idx_run_batch", "batch_id"),
        Index("idx_run_benchmark", "benchmark_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "dataset_id": self.dataset_id,
            "benchmark_id": self.benchmark_id,
            "batch_id": self.batch_id,
            "evaluation_config": self.evaluation_config,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "current_cost": float(self.current_cost) if self.current_cost else 0.0,
            "results_summary": self.results_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


if TYPE_CHECKING:
    from .agent import Agent
    from .benchmark import Benchmark
    from .evaluation_result import EvaluationResult
    from .trace import TraceDB
