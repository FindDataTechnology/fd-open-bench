from celery import Celery
from datetime import datetime
from typing import Any

from app.database import SessionLocal
from app.models.evaluation_run import EvaluationRun, EvaluationRunStatus
from app.models.evaluation_result import EvaluationResult, EvaluationResultStatus
from app.models.golden import Golden
from app.repositories import EvaluationRunRepository, EvaluationResultRepository, GoldenRepository
from app.evaluators.protocols import EvaluationContext
from app.evaluators.registry import registry as eval_registry


def make_celery() -> Celery:
    """Create Celery instance."""
    import os
    return Celery(
        "fd_open_bench",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    )


celery_app = make_celery()


@celery_app.task(name="app.tasks.evaluate_single_golden")
def evaluate_single_golden(
    run_id: str,
    golden_id: str,
    agent_id: str,
    evaluator_configs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate a single golden (test case) with an agent."""
    db = SessionLocal()
    try:
        # Get golden
        golden_repo = GoldenRepository(db)
        golden = golden_repo.get(golden_id)
        if not golden:
            return {"status": "error", "message": "Golden not found"}

        # TODO: Execute agent with golden.input
        # For now, simulate agent execution
        agent_output = f"Simulated response for: {golden.input}"
        trace_data = {
            "spans": [
                {
                    "span_id": "1",
                    "span_type": "agent",
                    "name": "agent",
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "duration_ms": 100,
                }
            ]
        }
        token_usage = {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        execution_time_ms = 100

        # Create evaluation context
        context = EvaluationContext(
            input=golden.input,
            output=agent_output,
            expected_output=golden.expected_output,
            trace=trace_data,
            token_usage=token_usage,
            execution_time_ms=execution_time_ms,
            golden_metadata=golden.metadata,
        )

        # Run evaluators
        evaluator_results = {}
        total_cost = 0.0

        for config in evaluator_configs:
            evaluator_name = config.get("name")
            evaluator = eval_registry.get(evaluator_name)

            if not evaluator:
                # Try to create from config
                try:
                    evaluator = eval_registry.create_from_config(config)
                    eval_registry.register(evaluator)
                except Exception as e:
                    evaluator_results[evaluator_name] = {
                        "score": 0.0,
                        "passed": False,
                        "reason": f"Failed to create evaluator: {str(e)}",
                        "error": str(e),
                    }
                    continue

            # Run evaluator
            try:
                import asyncio
                result = asyncio.run(evaluator.evaluate(context))
                evaluator_results[evaluator_name] = {
                    "score": result.score,
                    "passed": result.passed,
                    "reason": result.reason,
                    "metadata": result.metadata,
                    "error": result.error,
                }
                total_cost += result.cost
            except Exception as e:
                evaluator_results[evaluator_name] = {
                    "score": 0.0,
                    "passed": False,
                    "reason": f"Evaluation failed: {str(e)}",
                    "error": str(e),
                }

        # Calculate overall score (simple average for now)
        scores = [r["score"] for r in evaluator_results.values() if r["score"] > 0]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Create evaluation result
        result_repo = EvaluationResultRepository(db)
        result = result_repo.create(
            run_id=run_id,
            golden_id=golden_id,
            agent_output=agent_output,
            trace=trace_data,
            token_usage=token_usage,
            execution_time_ms=execution_time_ms,
            metric_scores={"overall": overall_score},
            validator_results=evaluator_results,
            total_cost=str(total_cost),
            status=EvaluationResultStatus.SUCCESS if overall_score > 0 else EvaluationResultStatus.FAILED,
        )

        return {
            "status": "success",
            "result_id": result.id,
            "score": overall_score,
            "cost": total_cost,
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.update_run_progress")
def update_run_progress(run_id: str, tasks_completed: int, tasks_failed: int, current_cost: float):
    """Update evaluation run progress."""
    db = SessionLocal()
    try:
        run_repo = EvaluationRunRepository(db)
        run_repo.update(
            run_id,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            current_cost=str(current_cost),
        )
    finally:
        db.close()


@celery_app.task(name="app.tasks.finalize_run")
def finalize_run(run_id: str):
    """Finalize evaluation run after all tasks complete."""
    db = SessionLocal()
    try:
        run_repo = EvaluationRunRepository(db)
        result_repo = EvaluationResultRepository(db)

        # Get aggregate stats
        stats = result_repo.aggregate_stats(run_id)

        # Update run status
        run_repo.update(
            run_id,
            status=EvaluationRunStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            results_summary=stats,
        )
    finally:
        db.close()
