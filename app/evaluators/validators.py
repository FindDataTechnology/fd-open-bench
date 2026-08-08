import re
import json
import time
from typing import Any

from app.evaluators.protocols import Evaluator, EvaluationContext, EvaluatorResult


class RegexValidator:
    """Validates output against regex pattern."""

    type = "validator"
    description = "Pattern matching validator"

    def __init__(self, name: str, pattern: str, must_match: bool = True, flags: int = 0):
        self.name = name
        self.pattern = pattern
        self.must_match = must_match
        self.flags = flags
        self._compiled = re.compile(pattern, flags)

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        match = self._compiled.search(context.output)
        elapsed = (time.perf_counter() - start) * 1000

        passed = match is not None if self.must_match else match is None
        return EvaluatorResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            reason="Pattern matched" if passed else "Pattern not matched",
            execution_time_ms=elapsed,
        )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "pattern" in config


class JsonSchemaValidator:
    """Validates output against JSON schema."""

    type = "validator"
    description = "JSON schema validation"

    def __init__(self, name: str, schema: dict[str, Any]):
        self.name = name
        self.schema = schema

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            data = json.loads(context.output)
            # Simple schema validation (check required fields)
            if "required" in self.schema:
                for field in self.schema["required"]:
                    if field not in data:
                        elapsed = (time.perf_counter() - start) * 1000
                        return EvaluatorResult(
                            score=0.0,
                            passed=False,
                            reason=f"Missing required field: {field}",
                            execution_time_ms=elapsed,
                        )
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=1.0,
                passed=True,
                reason="JSON matches schema",
                execution_time_ms=elapsed,
            )
        except json.JSONDecodeError as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Invalid JSON: {str(e)}",
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "schema" in config


class KeywordValidator:
    """Validates presence/absence of keywords."""

    type = "validator"
    description = "Keyword presence validation"

    def __init__(self, name: str, keywords: list[str], mode: str = "all"):
        self.name = name
        self.keywords = keywords
        self.mode = mode  # "all", "any", "none"

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        output_lower = context.output.lower()

        if self.mode == "all":
            missing = [kw for kw in self.keywords if kw.lower() not in output_lower]
            passed = len(missing) == 0
            reason = "All keywords found" if passed else f"Missing keywords: {', '.join(missing)}"
        elif self.mode == "any":
            found = [kw for kw in self.keywords if kw.lower() in output_lower]
            passed = len(found) > 0
            reason = f"Found keywords: {', '.join(found)}" if passed else "No keywords found"
        else:  # none
            found = [kw for kw in self.keywords if kw.lower() in output_lower]
            passed = len(found) == 0
            reason = "No keywords found" if passed else f"Found unwanted keywords: {', '.join(found)}"

        elapsed = (time.perf_counter() - start) * 1000
        return EvaluatorResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=reason,
            execution_time_ms=elapsed,
        )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "keywords" in config and "mode" in config


class LengthValidator:
    """Validates output length constraints."""

    type = "validator"
    description = "Length validation"

    def __init__(self, name: str, min_length: int | None = None, max_length: int | None = None, unit: str = "chars"):
        self.name = name
        self.min_length = min_length
        self.max_length = max_length
        self.unit = unit  # "chars" or "words"

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()

        if self.unit == "words":
            length = len(context.output.split())
        else:
            length = len(context.output)

        passed = True
        reason = "Length within bounds"

        if self.min_length is not None and length < self.min_length:
            passed = False
            reason = f"{self.unit.capitalize()} count {length} is below minimum {self.min_length}"
        elif self.max_length is not None and length > self.max_length:
            passed = False
            reason = f"{self.unit.capitalize()} count {length} exceeds maximum {self.max_length}"

        elapsed = (time.perf_counter() - start) * 1000
        return EvaluatorResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=reason,
            execution_time_ms=elapsed,
        )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "min_length" in config or "max_length" in config


class ContainsValidator:
    """Validates substring presence."""

    type = "validator"
    description = "Substring validation"

    def __init__(self, name: str, substring: str, case_sensitive: bool = True):
        self.name = name
        self.substring = substring
        self.case_sensitive = case_sensitive

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()

        if self.case_sensitive:
            passed = self.substring in context.output
        else:
            passed = self.substring.lower() in context.output.lower()

        elapsed = (time.perf_counter() - start) * 1000
        return EvaluatorResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            reason="Substring found" if passed else "Substring not found",
            execution_time_ms=elapsed,
        )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "substring" in config


class FormatValidator:
    """Validates common formats (email, URL, phone, date)."""

    type = "validator"
    description = "Format validation"

    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "url": r"https?://[^\s/$.?#].[^\s]*",
        "phone": r"\+?1?\d{9,15}",
        "date": r"\d{4}-\d{2}-\d{2}",
    }

    def __init__(self, name: str, format_type: str):
        self.name = name
        self.format_type = format_type
        if format_type not in self.PATTERNS:
            raise ValueError(f"Unknown format type: {format_type}")
        self._pattern = re.compile(self.PATTERNS[format_type])

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        match = self._pattern.search(context.output)
        elapsed = (time.perf_counter() - start) * 1000

        passed = match is not None
        return EvaluatorResult(
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=f"Valid {self.format_type} found" if passed else f"No valid {self.format_type} found",
            execution_time_ms=elapsed,
        )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "format" in config
