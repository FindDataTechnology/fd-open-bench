import time
import json
import subprocess
import tempfile
from typing import Any

from app.evaluators.protocols import Evaluator, EvaluationContext, EvaluatorResult


class SQLExecutor:
    """Executes SQL queries and validates results."""

    type = "executor"
    description = "SQL query executor"

    def __init__(
        self,
        name: str,
        connection_string: str,
        validation: dict[str, Any],
        read_only: bool = True,
    ):
        self.name = name
        self.connection_string = connection_string
        self.validation = validation
        self.read_only = read_only

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(self.connection_string)

            # Extract SQL from output (assume it's in the output)
            sql_query = context.output.strip()

            with engine.connect() as conn:
                if self.read_only:
                    # Check for write operations
                    sql_lower = sql_query.lower()
                    if any(kw in sql_lower for kw in ["insert", "update", "delete", "drop", "create", "alter"]):
                        elapsed = (time.perf_counter() - start) * 1000
                        return EvaluatorResult(
                            score=0.0,
                            passed=False,
                            reason="Write operations not allowed in read-only mode",
                            execution_time_ms=elapsed,
                        )

                result = conn.execute(sqlalchemy.text(sql_query))
                rows = [dict(row._mapping) for row in result]

            # Validate results
            if "expected_results" in self.validation:
                expected = self.validation["expected_results"]
                match_mode = self.validation.get("match_mode", "exact")

                if match_mode == "exact":
                    passed = rows == expected
                elif match_mode == "subset":
                    passed = all(any(row == exp for row in rows) for exp in expected)
                elif match_mode == "count":
                    passed = len(rows) == len(expected)
                else:
                    passed = False

                reason = "Results match" if passed else "Results do not match"
            elif "schema_check" in self.validation:
                schema = self.validation["schema_check"]
                if rows:
                    actual_columns = set(rows[0].keys())
                    expected_columns = set(schema.get("columns", []))
                    passed = actual_columns == expected_columns
                    reason = "Schema matches" if passed else "Schema mismatch"
                else:
                    passed = False
                    reason = "No results returned"
            else:
                passed = True
                reason = "Query executed successfully"

            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=1.0 if passed else 0.0,
                passed=passed,
                reason=reason,
                metadata={"rows_returned": len(rows)},
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"SQL execution failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "connection" in config and "validation" in config


class APIExecutor:
    """Calls APIs and validates responses."""

    type = "executor"
    description = "API call executor"

    def __init__(self, name: str, validation: dict[str, Any]):
        self.name = name
        self.validation = validation

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            import httpx

            # Parse API call details from context or output
            api_config = json.loads(context.output)
            url = api_config.get("url")
            method = api_config.get("method", "GET")
            headers = api_config.get("headers", {})
            body = api_config.get("body")

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )

            # Validate response
            passed = True
            reason = "API call successful"

            if "status_code" in self.validation:
                if response.status_code != self.validation["status_code"]:
                    passed = False
                    reason = f"Expected status {self.validation['status_code']}, got {response.status_code}"

            if passed and "response_schema" in self.validation:
                try:
                    response_data = response.json()
                    # Simple schema check
                    schema = self.validation["response_schema"]
                    if "type" in schema:
                        if schema["type"] == "object" and not isinstance(response_data, dict):
                            passed = False
                            reason = "Response is not an object"
                        elif schema["type"] == "array" and not isinstance(response_data, list):
                            passed = False
                            reason = "Response is not an array"
                except json.JSONDecodeError:
                    passed = False
                    reason = "Response is not valid JSON"

            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=1.0 if passed else 0.0,
                passed=passed,
                reason=reason,
                metadata={"status_code": response.status_code},
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"API call failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "validation" in config


class CodeExecutor:
    """Executes code in sandboxed environment."""

    type = "executor"
    description = "Code execution in sandbox"

    def __init__(
        self,
        name: str,
        language: str = "python",
        test_cases: list[dict[str, Any]] | None = None,
        timeout: int = 10,
        memory_limit: str = "256m",
    ):
        self.name = name
        self.language = language
        self.test_cases = test_cases or []
        self.timeout = timeout
        self.memory_limit = memory_limit

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            code = context.output

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                code_file = f.name

            # Run tests
            all_passed = True
            test_results = []

            for test_case in self.test_cases:
                test_input = test_case.get("input", "")
                expected_output = test_case.get("expected_output")

                # Create test script
                test_script = f"""
import sys
sys.path.insert(0, '{code_file.rsplit('/', 1)[0]}')
import {code_file.rsplit('/', 1)[1].replace('.py', '')}

try:
    result = {test_input}
    print(result)
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""

                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
                    tf.write(test_script)
                    test_file = tf.name

                # Execute in subprocess (simplified sandbox)
                result = subprocess.run(
                    ["python", test_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                actual_output = result.stdout.strip()
                passed = str(expected_output) == actual_output
                all_passed = all_passed and passed

                test_results.append({
                    "input": test_input,
                    "expected": expected_output,
                    "actual": actual_output,
                    "passed": passed,
                })

            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=1.0 if all_passed else 0.0,
                passed=all_passed,
                reason=f"{sum(t['passed'] for t in test_results)}/{len(test_results)} tests passed",
                metadata={"test_results": test_results},
                execution_time_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason="Code execution timed out",
                error="Timeout",
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Code execution failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return True


class BusinessLogicExecutor:
    """Executes custom business logic validation."""

    type = "executor"
    description = "Custom business logic executor"

    def __init__(self, name: str, module_path: str, function_name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.module_path = module_path
        self.function_name = function_name
        self.config = config or {}

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            # Dynamically import module
            import importlib
            module = importlib.import_module(self.module_path)
            func = getattr(module, self.function_name)

            # Call function with context
            result = func(context, **self.config)

            elapsed = (time.perf_counter() - start) * 1000

            if isinstance(result, EvaluatorResult):
                result.execution_time_ms = elapsed
                return result
            else:
                # Assume result is a dict with score and passed
                return EvaluatorResult(
                    score=result.get("score", 0.0),
                    passed=result.get("passed", False),
                    reason=result.get("reason", ""),
                    metadata=result.get("metadata", {}),
                    execution_time_ms=elapsed,
                )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Business logic execution failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "module" in config and "function" in config
