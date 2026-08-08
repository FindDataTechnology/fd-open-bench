"""Comparison service for aggregating and comparing agent evaluation results."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models import EvaluationRun, EvaluationResult, Agent, Benchmark
from app.models.evaluation_run import EvaluationRunStatus
import statistics
import logging

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing agent performance on benchmarks."""

    def __init__(self, db: Session):
        self.db = db

    def get_benchmark_leaderboard(
        self,
        benchmark_id: str,
        batch_id: Optional[str] = None,
        sort_by: str = "cost_per_success",
        sort_order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """Get leaderboard for a benchmark.

        Args:
            benchmark_id: Benchmark ID to compare agents on
            batch_id: Optional batch ID to filter by
            sort_by: Field to sort by (cost_per_success, roi, human_replacement, avg_score)
            sort_order: Sort order (asc or desc)

        Returns:
            List of agent performance summaries
        """
        # Get benchmark to access time_value_rate
        benchmark = self.db.query(Benchmark).filter(Benchmark.id == benchmark_id).first()
        if not benchmark:
            raise ValueError(f"Benchmark {benchmark_id} not found")

        time_value_rate = benchmark.time_value_rate or 0.0

        # Build query for runs
        query = self.db.query(EvaluationRun).filter(
            EvaluationRun.benchmark_id == benchmark_id,
            EvaluationRun.status == EvaluationRunStatus.COMPLETED.value
        )

        if batch_id:
            query = query.filter(EvaluationRun.batch_id == batch_id)

        runs = query.all()

        if not runs:
            return []

        # Group runs by agent
        agent_runs = {}
        for run in runs:
            if run.agent_id not in agent_runs:
                agent_runs[run.agent_id] = []
            agent_runs[run.agent_id].append(run)

        # Calculate stats for each agent
        leaderboard = []
        for agent_id, runs_list in agent_runs.items():
            agent_stats = self._calculate_agent_stats(agent_id, runs_list, time_value_rate)
            if agent_stats:
                leaderboard.append(agent_stats)

        # Sort leaderboard
        reverse = sort_order.lower() == "desc"

        # Handle sorting with None values (put them at the end)
        def sort_key(x):
            value = x.get(sort_by)
            if value is None:
                return float('inf') if not reverse else float('-inf')
            return value

        leaderboard.sort(key=sort_key, reverse=reverse)

        return leaderboard

    def _calculate_agent_stats(
        self,
        agent_id: str,
        runs: List[EvaluationRun],
        time_value_rate: float
    ) -> Optional[Dict[str, Any]]:
        """Calculate statistics for an agent across multiple runs.

        Args:
            agent_id: Agent ID
            runs: List of evaluation runs for this agent
            time_value_rate: Time value rate from benchmark ($/hour)

        Returns:
            Agent statistics or None if no valid data
        """
        # Get agent name
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        # Collect all results
        all_results = []
        for run in runs:
            results = self.db.query(EvaluationResult).filter(
                EvaluationResult.run_id == run.id
            ).all()
            all_results.extend(results)

        if not all_results:
            return None

        # Calculate technical metrics from metric_scores
        all_scores = []
        costs = []
        latencies = []

        for result in all_results:
            # Extract scores from metric_scores dict
            if result.metric_scores:
                all_scores.extend(result.metric_scores.values())

            # Extract cost
            if result.total_cost:
                try:
                    costs.append(float(result.total_cost))
                except (ValueError, TypeError):
                    pass

            # Extract latency
            if result.execution_time_ms:
                latencies.append(result.execution_time_ms / 1000.0)  # Convert to seconds

        # Calculate business metrics
        business_values = []
        human_costs = []
        human_minutes_list = []

        for result in all_results:
            if result.golden:
                if result.golden.business_value is not None:
                    business_values.append(float(result.golden.business_value))
                if result.golden.human_cost is not None:
                    human_costs.append(float(result.golden.human_cost))
                if result.golden.human_minutes is not None:
                    human_minutes_list.append(result.golden.human_minutes)

        # Calculate aggregate metrics
        total_cost = sum(costs) if costs else 0.0
        # Prefer the per-task value the engine already computed from the
        # benchmark's value formula; fall back to raw golden business_value
        # for runs from before formulas were wired into the engine.
        delivered = [
            float(r.business_value_delivered)
            for r in all_results
            if r.business_value_delivered is not None
        ]
        total_business_value = (sum(delivered) if delivered
                                else (sum(business_values) if business_values else 0.0))

        # Success criteria: status is SUCCESS and has metric scores
        success_count = len([r for r in all_results if r.status.value == "success" and r.metric_scores])
        total_tasks = len(all_results)

        # Cost per success
        cost_per_success = total_cost / success_count if success_count > 0 else None

        # Human replacement rate
        human_replacement = None
        if human_costs and cost_per_success is not None:
            avg_human_cost = sum(human_costs) / len(human_costs)
            human_replacement = cost_per_success / avg_human_cost if avg_human_cost > 0 else None

        # Time cost
        total_time_seconds = sum(latencies) if latencies else 0.0
        time_cost = total_time_seconds * time_value_rate / 3600.0  # Convert hours to seconds

        # ROI
        net_value = total_business_value - total_cost - time_cost
        roi = (net_value / total_cost * 100) if total_cost > 0 else None

        # Technical statistics
        tech_stats = self._calculate_technical_stats(all_results)

        # Calculate overall average score across all metrics
        avg_score = statistics.mean(all_scores) if all_scores else None
        stddev_score = statistics.stdev(all_scores) if len(all_scores) > 1 else None

        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "run_count": len(runs),
            "task_count": total_tasks,
            "success_count": success_count,
            "success_rate": success_count / total_tasks if total_tasks > 0 else 0.0,

            # Technical metrics
            "avg_score": avg_score,
            "stddev_score": stddev_score,
            "min_score": min(all_scores) if all_scores else None,
            "max_score": max(all_scores) if all_scores else None,
            "avg_cost": statistics.mean(costs) if costs else None,
            "avg_latency_s": statistics.mean(latencies) if latencies else None,

            # Business metrics
            "total_cost": total_cost,
            "total_business_value": total_business_value,
            "cost_per_success": cost_per_success,
            "human_replacement": human_replacement,
            "time_cost": time_cost,
            "net_value": net_value,
            "roi": roi,

            # Detailed tech stats by evaluator
            "tech_stats": tech_stats,
        }

    def _calculate_technical_stats(self, results: List[EvaluationResult]) -> Dict[str, Dict[str, float]]:
        """Calculate technical statistics by metric.

        Args:
            results: List of evaluation results

        Returns:
            Dictionary of metric stats
        """
        # Collect all metric scores
        metric_scores = {}
        for result in results:
            if result.metric_scores:
                for metric_name, score in result.metric_scores.items():
                    if metric_name not in metric_scores:
                        metric_scores[metric_name] = []
                    metric_scores[metric_name].append(score)

        # Calculate stats for each metric
        tech_stats = {}
        for metric_name, scores in metric_scores.items():
            if scores:
                tech_stats[metric_name] = {
                    "avg": statistics.mean(scores),
                    "stddev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                }

        return tech_stats

    def get_batch_comparison(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """Get comparison data for a specific batch.

        Args:
            batch_id: Batch ID

        Returns:
            Batch comparison data
        """
        # Get all runs in this batch
        runs = self.db.query(EvaluationRun).filter(
            EvaluationRun.batch_id == batch_id
        ).all()

        if not runs:
            raise ValueError(f"Batch {batch_id} not found")

        # Get benchmark info
        benchmark_id = runs[0].benchmark_id
        benchmark = self.db.query(Benchmark).filter(Benchmark.id == benchmark_id).first()

        # Calculate stats for each agent
        agents_data = []
        for run in runs:
            agent = self.db.query(Agent).filter(Agent.id == run.agent_id).first()
            if not agent:
                continue

            # Get results for this run
            results = self.db.query(EvaluationResult).filter(
                EvaluationResult.run_id == run.id
            ).all()

            # Calculate average score from metric_scores
            all_scores = []
            for result in results:
                if result.metric_scores:
                    all_scores.extend(result.metric_scores.values())

            avg_score = statistics.mean(all_scores) if all_scores else None

            agents_data.append({
                "run_id": run.id,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "status": run.status,
                "tasks_total": run.tasks_total,
                "tasks_completed": run.tasks_completed,
                "tasks_failed": run.tasks_failed,
                "progress": (run.tasks_completed / run.tasks_total * 100) if run.tasks_total > 0 else 0,
                "current_cost": float(run.current_cost) if run.current_cost else 0.0,
                "results_count": len(results),
                "avg_score": avg_score,
            })

        return {
            "batch_id": batch_id,
            "benchmark_id": benchmark_id,
            "benchmark_name": benchmark.name if benchmark else None,
            "agents": agents_data,
        }