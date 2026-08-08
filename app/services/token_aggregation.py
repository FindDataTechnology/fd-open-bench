"""Token usage aggregation and cost calculation service."""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.trace import Trace, Span, TokenUsage


class TokenAggregationService:
    """Service for aggregating token usage and calculating costs."""

    # Default pricing per 1K tokens (in USD)
    DEFAULT_PRICING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'claude-2': {'input': 0.008, 'output': 0.024},
    }

    def __init__(self, custom_pricing: Optional[Dict[str, Dict[str, float]]] = None):
        """Initialize with optional custom pricing."""
        self.pricing = custom_pricing or self.DEFAULT_PRICING

    def aggregate_tokens(self, trace: Trace) -> Dict[str, int]:
        """Aggregate token usage across all LLM spans in a trace.

        Args:
            trace: The trace to aggregate tokens from

        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens
        """
        total_input = 0
        total_output = 0

        for span in trace.spans:
            if span.span_type == 'llm' and span.token_usage:
                total_input += span.token_usage.input_tokens
                total_output += span.token_usage.output_tokens

        return {
            'input_tokens': total_input,
            'output_tokens': total_output,
            'total_tokens': total_input + total_output
        }

    def calculate_span_cost(self, span: Span) -> float:
        """Calculate cost for a single LLM span.

        Args:
            span: The span to calculate cost for

        Returns:
            Estimated cost in USD
        """
        if span.span_type != 'llm' or not span.token_usage:
            return 0.0

        model = span.token_usage.model or span.metadata.get('model', 'gpt-3.5-turbo')
        pricing = self.pricing.get(model, self.pricing['gpt-3.5-turbo'])

        input_cost = (span.token_usage.input_tokens / 1000) * pricing['input']
        output_cost = (span.token_usage.output_tokens / 1000) * pricing['output']

        return input_cost + output_cost

    def calculate_trace_cost(self, trace: Trace) -> float:
        """Calculate total cost for all LLM spans in a trace.

        Args:
            trace: The trace to calculate cost for

        Returns:
            Total estimated cost in USD
        """
        total_cost = 0.0

        for span in trace.spans:
            if span.span_type == 'llm':
                total_cost += self.calculate_span_cost(span)

        return total_cost

    def update_trace_with_costs(self, trace: Trace) -> None:
        """Update trace and spans with calculated costs.

        Args:
            trace: The trace to update
        """
        for span in trace.spans:
            if span.span_type == 'llm' and span.token_usage:
                cost = self.calculate_span_cost(span)
                span.token_usage.estimated_cost = cost

        trace.calculate_totals()

    def get_cost_breakdown(self, trace: Trace) -> Dict[str, any]:
        """Get detailed cost breakdown by model.

        Args:
            trace: The trace to analyze

        Returns:
            Dictionary with cost breakdown by model
        """
        breakdown = {}

        for span in trace.spans:
            if span.span_type == 'llm' and span.token_usage:
                model = span.token_usage.model or span.metadata.get('model', 'unknown')
                cost = self.calculate_span_cost(span)

                if model not in breakdown:
                    breakdown[model] = {
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'total_tokens': 0,
                        'cost': 0.0,
                        'call_count': 0
                    }

                breakdown[model]['input_tokens'] += span.token_usage.input_tokens
                breakdown[model]['output_tokens'] += span.token_usage.output_tokens
                breakdown[model]['total_tokens'] += span.token_usage.total_tokens
                breakdown[model]['cost'] += cost
                breakdown[model]['call_count'] += 1

        return breakdown


class TimingMetricsService:
    """Service for computing execution timing metrics."""

    def compute_timing_metrics(self, trace: Trace) -> Dict[str, float]:
        """Compute timing metrics for a trace.

        Args:
            trace: The trace to analyze

        Returns:
            Dictionary with timing metrics
        """
        total_duration = 0.0
        llm_duration = 0.0
        tool_duration = 0.0
        retriever_duration = 0.0

        for span in trace.spans:
            if span.duration_ms:
                total_duration = max(total_duration, span.duration_ms)

                if span.span_type == 'llm':
                    llm_duration += span.duration_ms
                elif span.span_type == 'tool':
                    tool_duration += span.duration_ms
                elif span.span_type == 'retriever':
                    retriever_duration += span.duration_ms

        # Calculate idle time (time not spent in LLM/tool/retriever)
        active_time = llm_duration + tool_duration + retriever_duration
        idle_time = max(0, total_duration - active_time)

        return {
            'total_duration_ms': total_duration,
            'llm_duration_ms': llm_duration,
            'tool_duration_ms': tool_duration,
            'retriever_duration_ms': retriever_duration,
            'idle_time_ms': idle_time,
            'active_time_ms': active_time
        }

    def compute_time_breakdown(self, trace: Trace) -> Dict[str, float]:
        """Compute time breakdown as percentages.

        Args:
            trace: The trace to analyze

        Returns:
            Dictionary with time breakdown percentages
        """
        metrics = self.compute_timing_metrics(trace)
        total = metrics['total_duration_ms']

        if total == 0:
            return {
                'llm_percentage': 0.0,
                'tool_percentage': 0.0,
                'retriever_percentage': 0.0,
                'idle_percentage': 0.0
            }

        return {
            'llm_percentage': (metrics['llm_duration_ms'] / total) * 100,
            'tool_percentage': (metrics['tool_duration_ms'] / total) * 100,
            'retriever_percentage': (metrics['retriever_duration_ms'] / total) * 100,
            'idle_percentage': (metrics['idle_time_ms'] / total) * 100
        }

    def get_performance_summary(self, trace: Trace) -> Dict[str, any]:
        """Get comprehensive performance summary.

        Args:
            trace: The trace to analyze

        Returns:
            Dictionary with performance summary
        """
        timing = self.compute_timing_metrics(trace)
        breakdown = self.compute_time_breakdown(trace)
        token_agg = TokenAggregationService().aggregate_tokens(trace)
        cost = TokenAggregationService().calculate_trace_cost(trace)

        return {
            'timing': timing,
            'time_breakdown': breakdown,
            'token_usage': token_agg,
            'total_cost': cost,
            'span_count': len(trace.spans),
            'llm_call_count': sum(1 for s in trace.spans if s.span_type == 'llm'),
            'tool_call_count': sum(1 for s in trace.spans if s.span_type == 'tool'),
            'retriever_call_count': sum(1 for s in trace.spans if s.span_type == 'retriever')
        }
