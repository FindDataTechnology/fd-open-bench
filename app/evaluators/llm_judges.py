import time
import json
from typing import Any

from app.evaluators.protocols import Evaluator, EvaluationContext, EvaluatorResult


class DeepEvalMetricWrapper:
    """Wrapper for DeepEval built-in metrics."""

    type = "llm_judge"
    description = "DeepEval metric wrapper"

    def __init__(self, name: str, metric_name: str, threshold: float = 0.5, model: str = "gpt-4o"):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.model = model
        self._metric = None

    def _get_metric(self):
        """Lazy load DeepEval metric."""
        if self._metric is None:
            try:
                from deepeval.metrics import (
                    AnswerRelevancyMetric,
                    FaithfulnessMetric,
                    HallucinationMetric,
                    ToxicityMetric,
                    BiasMetric,
                    SummarizationMetric,
                )
                metric_map = {
                    "answer_relevancy": AnswerRelevancyMetric,
                    "faithfulness": FaithfulnessMetric,
                    "hallucination": HallucinationMetric,
                    "toxicity": ToxicityMetric,
                    "bias": BiasMetric,
                    "summarization": SummarizationMetric,
                }
                if self.metric_name not in metric_map:
                    raise ValueError(f"Unknown metric: {self.metric_name}")
                self._metric = metric_map[self.metric_name](threshold=self.threshold)
            except ImportError:
                raise ImportError("DeepEval not installed. Install with: pip install deepeval")
        return self._metric

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            from deepeval.test_case import LLMTestCase

            metric = self._get_metric()
            test_case = LLMTestCase(
                input=context.input,
                actual_output=context.output,
                expected_output=context.expected_output,
            )
            metric.measure(test_case)
            elapsed = (time.perf_counter() - start) * 1000

            return EvaluatorResult(
                score=metric.score,
                passed=metric.score >= self.threshold,
                reason=metric.reason if hasattr(metric, "reason") else "",
                metadata={"metric": self.metric_name, "model": self.model},
                execution_time_ms=elapsed,
                cost=0.01,  # Approximate cost per LLM call
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Evaluation failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "metric" in config


class CustomPromptJudge:
    """LLM judge with custom prompt template."""

    type = "llm_judge"
    description = "Custom prompt LLM judge"

    def __init__(
        self,
        name: str,
        prompt_template: str,
        score_range: tuple[int, int] = (0, 10),
        threshold: float = 0.7,
        model: str = "gpt-4o",
    ):
        self.name = name
        self.prompt_template = prompt_template
        self.score_range = score_range
        self.threshold = threshold
        self.model = model

    async def evaluate(self, context: EvaluationContext) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            # Format prompt with context
            prompt = self.prompt_template.format(
                input=context.input,
                output=context.output,
                expected_output=context.expected_output or "N/A",
            )

            # Call LLM (using OpenAI as default)
            import openai
            client = openai.AsyncOpenAI()

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an evaluation assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            score = result.get("score", 0)
            reason = result.get("reason", "")

            # Normalize score to 0-1 range
            min_score, max_score = self.score_range
            normalized_score = (score - min_score) / (max_score - min_score)

            elapsed = (time.perf_counter() - start) * 1000
            cost = 0.01  # Approximate

            return EvaluatorResult(
                score=normalized_score,
                passed=normalized_score >= self.threshold,
                reason=reason,
                metadata={"model": self.model, "raw_score": score},
                execution_time_ms=elapsed,
                cost=cost,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Evaluation failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "prompt" in config


class ComparativeJudge:
    """LLM judge that compares two agent outputs."""

    type = "llm_judge"
    description = "Comparative LLM judge"

    def __init__(self, name: str, prompt_template: str, model: str = "gpt-4o"):
        self.name = name
        self.prompt_template = prompt_template
        self.model = model

    async def evaluate(
        self,
        context: EvaluationContext,
        output_a: str,
        output_b: str,
    ) -> EvaluatorResult:
        start = time.perf_counter()
        try:
            prompt = self.prompt_template.format(
                input=context.input,
                output_a=output_a,
                output_b=output_b,
            )

            import openai
            client = openai.AsyncOpenAI()

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an evaluation assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            winner = result.get("winner", "tie")
            reason = result.get("reason", "")

            # Score: 1.0 if A wins, 0.5 if tie, 0.0 if B wins
            score = 1.0 if winner == "A" else (0.5 if winner == "tie" else 0.0)

            elapsed = (time.perf_counter() - start) * 1000
            cost = 0.01

            return EvaluatorResult(
                score=score,
                passed=score >= 0.5,
                reason=reason,
                metadata={"winner": winner, "model": self.model},
                execution_time_ms=elapsed,
                cost=cost,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EvaluatorResult(
                score=0.0,
                passed=False,
                reason=f"Evaluation failed: {str(e)}",
                error=str(e),
                execution_time_ms=elapsed,
            )

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "prompt" in config
