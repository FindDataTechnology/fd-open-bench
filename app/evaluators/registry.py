from typing import Any
from app.evaluators.protocols import Evaluator
from app.evaluators.validators import (
    RegexValidator,
    JsonSchemaValidator,
    KeywordValidator,
    LengthValidator,
    ContainsValidator,
    FormatValidator,
)
from app.evaluators.llm_judges import (
    DeepEvalMetricWrapper,
    CustomPromptJudge,
    ComparativeJudge,
)
from app.evaluators.executors import (
    SQLExecutor,
    APIExecutor,
    CodeExecutor,
    BusinessLogicExecutor,
)


class EvaluatorRegistry:
    """Registry for managing evaluator instances."""

    def __init__(self):
        self._evaluators: dict[str, Evaluator] = {}

    def register(self, evaluator: Evaluator) -> None:
        """Register an evaluator instance."""
        self._evaluators[evaluator.name] = evaluator

    def get(self, name: str) -> Evaluator | None:
        """Get evaluator by name."""
        return self._evaluators.get(name)

    def list(self) -> list[Evaluator]:
        """List all registered evaluators."""
        return list(self._evaluators.values())

    def create_from_config(self, config: dict[str, Any]) -> Evaluator:
        """Create evaluator from configuration dict."""
        eval_type = config.get("type")
        name = config.get("name", f"{eval_type}_evaluator")

        if eval_type == "regex":
            return RegexValidator(
                name=name,
                pattern=config["pattern"],
                must_match=config.get("must_match", True),
                flags=config.get("flags", 0),
            )
        elif eval_type == "json_schema":
            return JsonSchemaValidator(
                name=name,
                schema=config["schema"],
            )
        elif eval_type == "keyword":
            return KeywordValidator(
                name=name,
                keywords=config["keywords"],
                mode=config.get("mode", "all"),
            )
        elif eval_type == "length":
            return LengthValidator(
                name=name,
                min_length=config.get("min_length"),
                max_length=config.get("max_length"),
                unit=config.get("unit", "chars"),
            )
        elif eval_type == "contains":
            return ContainsValidator(
                name=name,
                substring=config["substring"],
                case_sensitive=config.get("case_sensitive", True),
            )
        elif eval_type == "format":
            return FormatValidator(
                name=name,
                format_type=config["format"],
            )
        elif eval_type == "deepeval_metric":
            return DeepEvalMetricWrapper(
                name=name,
                metric_name=config["metric"],
                threshold=config.get("threshold", 0.5),
                model=config.get("model", "gpt-4o"),
            )
        elif eval_type == "custom_prompt":
            return CustomPromptJudge(
                name=name,
                prompt_template=config["prompt"],
                score_range=tuple(config.get("score_range", (0, 10))),
                threshold=config.get("threshold", 0.7),
                model=config.get("model", "gpt-4o"),
            )
        elif eval_type == "comparative":
            return ComparativeJudge(
                name=name,
                prompt_template=config["prompt"],
                model=config.get("model", "gpt-4o"),
            )
        elif eval_type == "sql":
            return SQLExecutor(
                name=name,
                connection_string=config["connection"],
                validation=config["validation"],
                read_only=config.get("read_only", True),
            )
        elif eval_type == "api":
            return APIExecutor(
                name=name,
                validation=config["validation"],
            )
        elif eval_type == "code":
            return CodeExecutor(
                name=name,
                language=config.get("language", "python"),
                test_cases=config.get("test_cases", []),
                timeout=config.get("timeout", 10),
                memory_limit=config.get("memory_limit", "256m"),
            )
        elif eval_type == "business_logic":
            return BusinessLogicExecutor(
                name=name,
                module_path=config["module"],
                function_name=config["function"],
                config=config.get("config", {}),
            )
        else:
            raise ValueError(f"Unknown evaluator type: {eval_type}")


# Global registry instance
registry = EvaluatorRegistry()
