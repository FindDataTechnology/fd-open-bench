"""Evaluation engine for orchestrating agent evaluations."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import asyncio
from sqlalchemy.orm import Session
from app.models import Agent, EvaluationRun, EvaluationResult, Golden
from app.models.trace import Trace
from app.evaluators.protocols import Evaluator, EvaluationContext, EvaluatorResult
from app.evaluators.registry import registry as evaluator_registry
from app.services.tracing import trace_service
from app.services.token_aggregation import TokenAggregationService, TimingMetricsService
from app.services.business_value import BusinessValueCalculator
from app.utils.compression import compress_trace


class EvaluationEngine:
    """Main evaluation engine for orchestrating agent evaluations."""

    def __init__(self, db: Session):
        self.db = db
        # Use the global singleton: adapters decorate the same instance, so
        # their spans land in the trace the engine starts here.
        self.trace_service = trace_service
        self.token_service = TokenAggregationService()
        self.timing_service = TimingMetricsService()
        self.business_calculator = BusinessValueCalculator()

    async def run_evaluation(
        self,
        run_id: str,
        agent_id: str,
        dataset_id: str,
        evaluator_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run a complete evaluation.

        Args:
            run_id: Evaluation run ID
            agent_id: Agent ID to evaluate
            dataset_id: Dataset ID with test cases
            evaluator_configs: List of evaluator configurations

        Returns:
            Evaluation results summary
        """
        # Get agent and dataset
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        dataset = self.db.query(Golden).filter(Golden.dataset_id == dataset_id).all()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found or empty")

        # Use the run's benchmark value formula, if any, so business value
        # per task follows the benchmark config (not just raw sums).
        from app.models import Benchmark, EvaluationRun
        run = self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        benchmark = None
        if run and run.benchmark_id:
            benchmark = self.db.query(Benchmark).filter(Benchmark.id == run.benchmark_id).first()
        if benchmark and benchmark.value_formula:
            self.business_calculator = BusinessValueCalculator(
                {"value_formula": benchmark.value_formula}
            )

        # Initialize evaluators
        evaluators = []
        for config in evaluator_configs:
            evaluator = evaluator_registry.create_from_config(config)
            evaluators.append(evaluator)

        # Run evaluation for each golden
        results = []
        for golden in dataset:
            result = await self._evaluate_single_golden(
                run_id=run_id,
                agent=agent,
                golden=golden,
                evaluators=evaluators
            )
            results.append(result)

        # Aggregate results
        summary = self._aggregate_results(results)

        return summary

    async def _evaluate_single_golden(
        self,
        run_id: str,
        agent: Agent,
        golden: Golden,
        evaluators: List[Evaluator]
    ) -> Dict[str, Any]:
        """Evaluate a single golden test case.

        Args:
            run_id: Evaluation run ID
            agent: Agent to evaluate
            golden: Golden test case
            evaluators: List of evaluators to run

        Returns:
            Evaluation result for this golden
        """
        # Start trace capture
        trace = self.trace_service.start_trace(run_id, agent.id)

        try:
            # Execute agent
            agent_output = await self._execute_agent(agent, golden.input, run_id)

            # End trace and calculate metrics
            trace = self.trace_service.end_trace(run_id)
            self.token_service.update_trace_with_costs(trace)

            # Merge the golden's business columns (the canonical source) into
            # the formula context, overriding any legacy extra_metadata values.
            golden_metadata = dict(golden.extra_metadata or {})
            if golden.business_value is not None:
                golden_metadata["business_value"] = float(golden.business_value)
            if golden.human_cost is not None:
                golden_metadata["human_cost"] = float(golden.human_cost)
            if golden.human_minutes is not None:
                golden_metadata["human_minutes"] = golden.human_minutes

            # Create evaluation context
            context = EvaluationContext(
                input=golden.input,
                output=agent_output,
                expected_output=golden.expected_output,
                trace=trace.to_dict(),
                token_usage=self.token_service.aggregate_tokens(trace),
                execution_time_ms=trace.total_duration_ms,
                agent_config=agent.config,
                golden_metadata=golden_metadata,
                business_context={}
            )

            # Run evaluators
            evaluator_results = []
            for evaluator in evaluators:
                result = await evaluator.evaluate(context)
                evaluator_results.append({
                    'evaluator_name': evaluator.name,
                    'evaluator_type': evaluator.type,
                    'score': result.score,
                    'passed': result.passed,
                    'reason': result.reason,
                    'metadata': result.metadata,
                    'execution_time_ms': result.execution_time_ms,
                    'cost': result.cost,
                    'error': result.error
                })

            # Calculate business value (formula context gets the measured latency/tokens)
            golden_metadata["latency_s"] = (trace.total_duration_ms or 0) / 1000.0
            tu = context.token_usage or {}
            golden_metadata["input_tokens"] = tu.get("input_tokens", 0)
            golden_metadata["output_tokens"] = tu.get("output_tokens", 0)
            business_value = self.business_calculator.calculate_business_value(
                task_completed=True,
                success_score=sum(r['score'] for r in evaluator_results) / len(evaluator_results) if evaluator_results else 0,
                golden_metadata=golden_metadata
            )

            # Calculate total cost
            total_cost = trace.total_cost + sum(r['cost'] for r in evaluator_results)

            # Save result to database
            db_result = EvaluationResult(
                run_id=run_id,
                golden_id=golden.id,
                agent_output=agent_output,
                trace=compress_trace(trace.to_dict()),
                token_usage=context.token_usage,
                execution_time_ms=context.execution_time_ms,
                metric_scores={r['evaluator_name']: r['score'] for r in evaluator_results},
                validator_results={r['evaluator_name']: r for r in evaluator_results},
                business_value_delivered=str(business_value),
                total_cost=str(total_cost),
                status='success'
            )
            self.db.add(db_result)
            self.db.commit()

            return {
                'golden_id': golden.id,
                'agent_output': agent_output,
                'evaluator_results': evaluator_results,
                'business_value': business_value,
                'total_cost': total_cost,
                'trace_summary': {
                    'total_duration_ms': trace.total_duration_ms,
                    'total_tokens': trace.total_tokens,
                    'span_count': len(trace.spans)
                }
            }

        except Exception as e:
            # Save error result
            db_result = EvaluationResult(
                run_id=run_id,
                golden_id=golden.id,
                agent_output=None,
                trace=None,
                token_usage=None,
                execution_time_ms=None,
                metric_scores={},
                validator_results={},
                business_value_delivered=0,
                total_cost=0,
                status='error',
                error_message=str(e)
            )
            self.db.add(db_result)
            self.db.commit()

            return {
                'golden_id': golden.id,
                'error': str(e),
                'status': 'error'
            }

    async def _execute_agent(
        self,
        agent: Agent,
        input_text: str,
        run_id: str
    ) -> str:
        """Execute an agent with the given input.

        Args:
            agent: Agent to execute
            input_text: Input text
            run_id: Run ID for tracing

        Returns:
            Agent output
        """
        # Build the adapter for this agent and run it (traced end-to-end)
        from app.adapters.factory import build_adapter
        adapter = build_adapter(agent)
        return await adapter.run(input=input_text, run_id=run_id, agent_id=agent.id)

    def _aggregate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate results from multiple goldens.

        Args:
            results: List of evaluation results

        Returns:
            Aggregated summary
        """
        successful = [r for r in results if r.get('status') != 'error']
        failed = [r for r in results if r.get('status') == 'error']

        if not successful:
            return {
                'total': len(results),
                'successful': 0,
                'failed': len(failed),
                'avg_score': 0,
                'total_cost': 0,
                'total_business_value': 0,
                'roi': 0
            }

        # Calculate average scores per evaluator
        evaluator_scores = {}
        for result in successful:
            for eval_result in result.get('evaluator_results', []):
                name = eval_result['evaluator_name']
                if name not in evaluator_scores:
                    evaluator_scores[name] = []
                evaluator_scores[name].append(eval_result['score'])

        avg_scores = {
            name: sum(scores) / len(scores)
            for name, scores in evaluator_scores.items()
        }

        # Calculate totals (float() — BusinessValueCalculator returns Decimal,
        # which would break the JSON results_summary column)
        total_cost = sum(r.get('total_cost', 0) for r in successful)
        total_business_value = float(sum(r.get('business_value', 0) for r in successful))

        # Calculate ROI
        roi = self.business_calculator.calculate_roi(
            Decimal(str(total_business_value)), Decimal(str(total_cost)))

        return {
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'avg_scores': avg_scores,
            'total_cost': total_cost,
            'total_business_value': total_business_value,
            'roi': roi,
            'cost_efficiency': self.business_calculator.calculate_cost_efficiency(
                Decimal(str(total_business_value)), Decimal(str(total_cost))
            )
        }
