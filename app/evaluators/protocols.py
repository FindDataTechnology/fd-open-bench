from typing import Protocol, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationContext:
    """Context passed to evaluators containing all relevant data."""

    input: str
    output: str
    expected_output: str | None = None
    trace: dict[str, Any] | None = None
    token_usage: dict[str, Any] | None = None
    execution_time_ms: int | None = None
    agent_config: dict[str, Any] = field(default_factory=dict)
    golden_metadata: dict[str, Any] = field(default_factory=dict)
    business_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluatorResult:
    """Result from an evaluator."""

    score: float  # 0.0 to 1.0
    passed: bool
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    cost: float = 0.0
    error: str | None = None


class Evaluator(Protocol):
    """Protocol for all evaluators."""

    name: str
    type: str  # "validator", "llm_judge", "executor"
    description: str

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        """Evaluate the given context."""
        ...

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate evaluator configuration."""
        ...
