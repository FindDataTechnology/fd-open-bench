"""Unit tests for trace capture, token aggregation, and timing metrics."""

import pytest
from datetime import datetime, timedelta
from app.models.trace import Trace, Span, TokenUsage
from app.services.tracing import trace_service
from app.services.token_aggregation import TokenAggregationService, TimingMetricsService


class TestTraceCapture:
    """Tests for trace capture service."""

    def test_start_trace(self):
        """Test starting a new trace."""
        trace = trace_service.start_trace(run_id="run_123", agent_id="agent_456")

        assert trace.run_id == "run_123"
        assert trace.agent_id == "agent_456"
        assert trace.trace_id is not None
        assert len(trace.spans) == 0

    def test_end_trace(self):
        """Test ending a trace and calculating totals."""
        trace = trace_service.start_trace(run_id="run_123", agent_id="agent_456")

        # Add some spans
        span1 = Span(
            span_type='llm',
            name='test_llm',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        )
        span1.end_time = span1.start_time + timedelta(milliseconds=500)
        span1.duration_ms = 500
        trace.add_span(span1)

        ended_trace = trace_service.end_trace(run_id="run_123")

        assert ended_trace is not None
        assert ended_trace.total_tokens == 150
        assert ended_trace.total_duration_ms == 500

    def test_get_trace(self):
        """Test retrieving an active trace."""
        trace = trace_service.start_trace(run_id="run_789", agent_id="agent_012")

        retrieved = trace_service.get_trace(run_id="run_789")

        assert retrieved is not None
        assert retrieved.run_id == "run_789"
        assert retrieved.agent_id == "agent_012"

    def test_add_span_to_trace(self):
        """Test adding spans to a trace."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span = Span(
            span_type='agent',
            name='test_agent',
            start_time=datetime.utcnow()
        )

        trace.add_span(span)

        assert len(trace.spans) == 1
        assert trace.root_span_id == span.span_id

    def test_calculate_totals(self):
        """Test calculating trace totals."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        # Add LLM spans with token usage
        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150, estimated_cost=0.01)
        )
        span1.end_time = span1.start_time + timedelta(milliseconds=500)
        span1.duration_ms = 500

        span2 = Span(
            span_type='llm',
            name='llm_2',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300, estimated_cost=0.02)
        )
        span2.end_time = span2.start_time + timedelta(milliseconds=300)
        span2.duration_ms = 300

        trace.add_span(span1)
        trace.add_span(span2)
        trace.calculate_totals()

        assert trace.total_tokens == 450
        assert trace.total_cost == 0.03


class TestTokenAggregation:
    """Tests for token aggregation service."""

    def test_aggregate_tokens(self):
        """Test aggregating tokens across spans."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        # Add LLM spans
        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        )

        span2 = Span(
            span_type='llm',
            name='llm_2',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300)
        )

        # Add non-LLM span (should be ignored)
        span3 = Span(
            span_type='tool',
            name='tool_1',
            start_time=datetime.utcnow()
        )

        trace.spans = [span1, span2, span3]

        service = TokenAggregationService()
        result = service.aggregate_tokens(trace)

        assert result['input_tokens'] == 300
        assert result['output_tokens'] == 150
        assert result['total_tokens'] == 450

    def test_calculate_span_cost(self):
        """Test calculating cost for a single span."""
        span = Span(
            span_type='llm',
            name='llm_call',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                model='gpt-4'
            )
        )

        service = TokenAggregationService()
        cost = service.calculate_span_cost(span)

        # GPT-4 pricing: $0.03/1K input, $0.06/1K output
        expected_cost = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert abs(cost - expected_cost) < 0.0001

    def test_calculate_trace_cost(self):
        """Test calculating total cost for a trace."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                model='gpt-4'
            )
        )

        span2 = Span(
            span_type='llm',
            name='llm_2',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(
                input_tokens=2000,
                output_tokens=1000,
                total_tokens=3000,
                model='gpt-3.5-turbo'
            )
        )

        trace.spans = [span1, span2]

        service = TokenAggregationService()
        total_cost = service.calculate_trace_cost(trace)

        # Should sum costs from both spans
        assert total_cost > 0

    def test_get_cost_breakdown(self):
        """Test getting cost breakdown by model."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                model='gpt-4'
            )
        )

        span2 = Span(
            span_type='llm',
            name='llm_2',
            start_time=datetime.utcnow(),
            token_usage=TokenUsage(
                input_tokens=2000,
                output_tokens=1000,
                total_tokens=3000,
                model='gpt-4'
            )
        )

        trace.spans = [span1, span2]

        service = TokenAggregationService()
        breakdown = service.get_cost_breakdown(trace)

        assert 'gpt-4' in breakdown
        assert breakdown['gpt-4']['call_count'] == 2
        assert breakdown['gpt-4']['input_tokens'] == 3000
        assert breakdown['gpt-4']['output_tokens'] == 1500


class TestTimingMetrics:
    """Tests for timing metrics service."""

    def test_compute_timing_metrics(self):
        """Test computing timing metrics."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        # Add spans with different durations
        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=500),
            duration_ms=500
        )

        span2 = Span(
            span_type='tool',
            name='tool_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=300),
            duration_ms=300
        )

        span3 = Span(
            span_type='retriever',
            name='retriever_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=200),
            duration_ms=200
        )

        trace.spans = [span1, span2, span3]

        service = TimingMetricsService()
        metrics = service.compute_timing_metrics(trace)

        assert metrics['llm_duration_ms'] == 500
        assert metrics['tool_duration_ms'] == 300
        assert metrics['retriever_duration_ms'] == 200
        assert metrics['active_time_ms'] == 1000

    def test_compute_time_breakdown(self):
        """Test computing time breakdown percentages."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=500),
            duration_ms=500
        )

        span2 = Span(
            span_type='tool',
            name='tool_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=500),
            duration_ms=500
        )

        trace.spans = [span1, span2]

        service = TimingMetricsService()
        breakdown = service.compute_time_breakdown(trace)

        assert breakdown['llm_percentage'] == 50.0
        assert breakdown['tool_percentage'] == 50.0
        assert breakdown['idle_percentage'] == 0.0

    def test_get_performance_summary(self):
        """Test getting comprehensive performance summary."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span1 = Span(
            span_type='llm',
            name='llm_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=500),
            duration_ms=500,
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        )

        span2 = Span(
            span_type='tool',
            name='tool_1',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=300),
            duration_ms=300
        )

        trace.spans = [span1, span2]

        service = TimingMetricsService()
        summary = service.get_performance_summary(trace)

        assert 'timing' in summary
        assert 'time_breakdown' in summary
        assert 'token_usage' in summary
        assert 'total_cost' in summary
        assert summary['span_count'] == 2
        assert summary['llm_call_count'] == 1
        assert summary['tool_call_count'] == 1


class TestSpanModel:
    """Tests for Span model."""

    def test_span_creation(self):
        """Test creating a span."""
        span = Span(
            span_type='llm',
            name='test_llm',
            start_time=datetime.utcnow()
        )

        assert span.span_id is not None
        assert span.span_type == 'llm'
        assert span.name == 'test_llm'
        assert span.status == 'success'

    def test_calculate_duration(self):
        """Test calculating span duration."""
        start = datetime.utcnow()
        end = start + timedelta(milliseconds=500)

        span = Span(
            span_type='llm',
            name='test_llm',
            start_time=start,
            end_time=end
        )

        duration = span.calculate_duration()

        assert duration == 500.0

    def test_span_to_dict(self):
        """Test converting span to dictionary."""
        span = Span(
            span_type='llm',
            name='test_llm',
            start_time=datetime.utcnow(),
            input='test input',
            output='test output'
        )

        result = span.to_dict()

        assert 'span_id' in result
        assert 'span_type' in result
        assert 'name' in result
        assert result['span_type'] == 'llm'
        assert result['name'] == 'test_llm'


class TestTraceModel:
    """Tests for Trace model."""

    def test_trace_creation(self):
        """Test creating a trace."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        assert trace.trace_id is not None
        assert trace.run_id == "run_123"
        assert trace.agent_id == "agent_456"
        assert len(trace.spans) == 0

    def test_get_span_tree(self):
        """Test getting hierarchical span tree."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        # Create parent span
        parent = Span(
            span_type='agent',
            name='agent',
            start_time=datetime.utcnow()
        )
        trace.add_span(parent)

        # Create child span
        child = Span(
            parent_span_id=parent.span_id,
            span_type='llm',
            name='llm_call',
            start_time=datetime.utcnow()
        )
        trace.add_span(child)

        tree = trace.get_span_tree()

        assert 'trace_id' in tree
        assert 'spans' in tree
        assert len(tree['spans']) == 1
        assert len(tree['spans'][0]['children']) == 1

    def test_trace_to_dict(self):
        """Test converting trace to dictionary."""
        trace = Trace(run_id="run_123", agent_id="agent_456")

        span = Span(
            span_type='llm',
            name='test_llm',
            start_time=datetime.utcnow()
        )
        trace.add_span(span)

        result = trace.to_dict()

        assert 'trace_id' in result
        assert 'run_id' in result
        assert 'agent_id' in result
        assert 'spans' in result
        assert len(result['spans']) == 1
