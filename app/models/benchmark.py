import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class Benchmark(Base):
    """Benchmark: the unit of agent comparison.

    A benchmark bundles 题+尺+生意:
    - 题 (questions): a dataset of goldens
    - 尺 (ruler): metric_suite — evaluator configs applied to every run
    - 生意 (business model): value_formula + time_value_rate used to turn
      technical results into business metrics (cost per success, ROI,
      human replacement, time cost)

    Agents are only ever compared within the same benchmark.
    """

    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False
    )
    metric_suite: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )  # evaluator configs, e.g. [{"type": "task_completion", "threshold": 0.7}]
    value_formula: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # safe expression; None/empty = default business_value * success_score
    time_value_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # $ per second of agent latency
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship()
    runs: Mapped[list["EvaluationRun"]] = relationship(
        back_populates="benchmark", lazy="selectin"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dataset_id": self.dataset_id,
            "metric_suite": self.metric_suite,
            "value_formula": self.value_formula,
            "time_value_rate": self.time_value_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


if TYPE_CHECKING:
    from .dataset import Dataset
    from .evaluation_run import EvaluationRun
