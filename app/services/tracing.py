"""Trace capture service using DeepEval's @observe decorators."""

from typing import Callable, Any, Optional, Dict
from datetime import datetime
from functools import wraps
import asyncio
import time
from app.models.trace import Span, Trace, TokenUsage
from app.utils.compression import compress_trace


class TraceCaptureService:
    """Service for capturing agent execution traces."""

    def __init__(self):
        self.active_traces: Dict[str, Trace] = {}
        self.current_span_stack: Dict[str, list] = {}

    def start_trace(self, run_id: str, agent_id: str) -> Trace:
        """Start a new trace for an agent run."""
        trace = Trace(run_id=run_id, agent_id=agent_id)
        self.active_traces[run_id] = trace
        self.current_span_stack[run_id] = []
        return trace

    def end_trace(self, run_id: str) -> Optional[Trace]:
        """End a trace and calculate totals."""
        trace = self.active_traces.get(run_id)
        if trace:
            trace.calculate_totals()
            del self.active_traces[run_id]
            del self.current_span_stack[run_id]
        return trace

    def get_trace(self, run_id: str) -> Optional[Trace]:
        """Get active trace by run ID."""
        return self.active_traces.get(run_id)

    def observe_agent(self, name: str = "agent"):
        """Decorator to observe agent execution."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract run_id and agent_id from kwargs or context
                run_id = kwargs.get('run_id') or (args[0] if args else None)
                agent_id = kwargs.get('agent_id') or (args[1] if len(args) > 1 else None)

                if not run_id or not agent_id:
                    # If no run_id, just execute without tracing
                    return await func(*args, **kwargs)

                # Start trace if not already started
                trace = self.get_trace(run_id)
                if not trace:
                    trace = self.start_trace(run_id, agent_id)

                # Create agent span
                span = Span(
                    span_type='agent',
                    name=name,
                    start_time=datetime.utcnow(),
                    input=str(kwargs.get('input', ''))
                )

                # Add to trace
                trace.add_span(span)
                self.current_span_stack[run_id].append(span.span_id)

                try:
                    # Execute function
                    result = await func(*args, **kwargs)

                    # Update span with output
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.output = str(result) if result is not None else None
                    span.status = 'success'

                    return result

                except Exception as e:
                    # Mark span as error
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.status = 'error'
                    span.error_message = str(e)
                    raise

                finally:
                    # Remove from stack
                    if self.current_span_stack[run_id]:
                        self.current_span_stack[run_id].pop()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, run in event loop
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def observe_llm(self, name: str = "llm_call", model: Optional[str] = None):
        """Decorator to observe LLM calls."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                run_id = kwargs.get('run_id')
                if not run_id:
                    return await func(*args, **kwargs)

                trace = self.get_trace(run_id)
                if not trace:
                    return await func(*args, **kwargs)

                # Get parent span
                parent_span_id = None
                if self.current_span_stack[run_id]:
                    parent_span_id = self.current_span_stack[run_id][-1]

                # Create LLM span
                span = Span(
                    parent_span_id=parent_span_id,
                    span_type='llm',
                    name=name,
                    start_time=datetime.utcnow(),
                    input=str(kwargs.get('prompt', kwargs.get('messages', ''))),
                    metadata={'model': model} if model else {}
                )

                trace.add_span(span)
                self.current_span_stack[run_id].append(span.span_id)

                try:
                    # Execute function
                    result = await func(*args, **kwargs)

                    # Update span with output and token usage
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.output = str(result) if result is not None else None
                    span.status = 'success'

                    # Extract token usage if available
                    if hasattr(result, 'usage'):
                        span.token_usage = TokenUsage(
                            input_tokens=getattr(result.usage, 'prompt_tokens', 0),
                            output_tokens=getattr(result.usage, 'completion_tokens', 0),
                            total_tokens=getattr(result.usage, 'total_tokens', 0),
                            model=model
                        )

                    return result

                except Exception as e:
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.status = 'error'
                    span.error_message = str(e)
                    raise

                finally:
                    if self.current_span_stack[run_id]:
                        self.current_span_stack[run_id].pop()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def observe_tool(self, name: str = "tool_call"):
        """Decorator to observe tool executions."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                run_id = kwargs.get('run_id')
                if not run_id:
                    return await func(*args, **kwargs)

                trace = self.get_trace(run_id)
                if not trace:
                    return await func(*args, **kwargs)

                # Get parent span
                parent_span_id = None
                if self.current_span_stack[run_id]:
                    parent_span_id = self.current_span_stack[run_id][-1]

                # Create tool span
                span = Span(
                    parent_span_id=parent_span_id,
                    span_type='tool',
                    name=name,
                    start_time=datetime.utcnow(),
                    input=str(kwargs.get('tool_input', kwargs))
                )

                trace.add_span(span)
                self.current_span_stack[run_id].append(span.span_id)

                try:
                    result = await func(*args, **kwargs)

                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.output = str(result) if result is not None else None
                    span.status = 'success'

                    return result

                except Exception as e:
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.status = 'error'
                    span.error_message = str(e)
                    raise

                finally:
                    if self.current_span_stack[run_id]:
                        self.current_span_stack[run_id].pop()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def observe_retriever(self, name: str = "retriever"):
        """Decorator to observe retriever calls."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                run_id = kwargs.get('run_id')
                if not run_id:
                    return await func(*args, **kwargs)

                trace = self.get_trace(run_id)
                if not trace:
                    return await func(*args, **kwargs)

                # Get parent span
                parent_span_id = None
                if self.current_span_stack[run_id]:
                    parent_span_id = self.current_span_stack[run_id][-1]

                # Create retriever span
                span = Span(
                    parent_span_id=parent_span_id,
                    span_type='retriever',
                    name=name,
                    start_time=datetime.utcnow(),
                    input=str(kwargs.get('query', ''))
                )

                trace.add_span(span)
                self.current_span_stack[run_id].append(span.span_id)

                try:
                    result = await func(*args, **kwargs)

                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.output = str(result) if result is not None else None
                    span.status = 'success'

                    return result

                except Exception as e:
                    span.end_time = datetime.utcnow()
                    span.duration_ms = span.calculate_duration()
                    span.status = 'error'
                    span.error_message = str(e)
                    raise

                finally:
                    if self.current_span_stack[run_id]:
                        self.current_span_stack[run_id].pop()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator


# Global trace capture service instance
trace_service = TraceCaptureService()
