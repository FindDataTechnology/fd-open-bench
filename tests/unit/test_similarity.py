"""Checks for the default metric_suite scorer (token-overlap F1)."""
import pytest

from app.evaluators.validators import SimilarityValidator
from app.evaluators.protocols import EvaluationContext


@pytest.mark.asyncio
async def test_exact_match_scores_one():
    v = SimilarityValidator("accuracy")
    r = await v.evaluate(EvaluationContext(input="x", output="Track my order",
                                           expected_output="Track my order"))
    assert r.score == 1.0 and r.passed


@pytest.mark.asyncio
async def test_disjoint_output_scores_zero():
    v = SimilarityValidator("accuracy")
    r = await v.evaluate(EvaluationContext(input="x", output="hello world",
                                           expected_output="refund policy"))
    assert r.score == 0.0 and not r.passed


@pytest.mark.asyncio
async def test_partial_overlap_scores_below_one():
    v = SimilarityValidator("accuracy")
    r = await v.evaluate(EvaluationContext(
        input="x",
        output="This is a sample response about refund policy",
        expected_output="refund policy",
    ))
    assert 0.0 < r.score < 1.0
