"""Echo adapter: deterministic fake agent for smoke tests / demo runs.

No external API needed — lets the whole pipeline (benchmark → batch →
leaderboard) run from a fresh install. Returns the input (optionally
prefixed), simulates latency, and records a fake LLM span with token usage
so cost and time-cost business metrics are populated.

Config:
    prefix: str      text prepended to the echo (default "")
    latency_ms: int  simulated latency per call (default 0)
    model: str       fake model name used for pricing lookup (default "gpt-3.5-turbo")
    input_tokens: int   fake input tokens per call (default 100)
    output_tokens: int  fake output tokens per call (default 40)
"""

import asyncio
from datetime import datetime

from app.models.trace import Span, TokenUsage
from app.services.tracing import trace_service


class EchoAgentAdapter:
    """Adapter that echoes its input with optional simulated cost/latency."""

    def __init__(self, prefix: str = "", latency_ms: int = 0, model: str = "gpt-3.5-turbo",
                 input_tokens: int = 100, output_tokens: int = 40, **kwargs):
        self.prefix = prefix
        self.latency_ms = latency_ms
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    @trace_service.observe_agent(name="echo_agent")
    async def run(self, input: str, run_id: str, agent_id: str, **kwargs) -> str:
        # Inject a fake LLM span so token/cost aggregation has something to add up.
        trace = trace_service.get_trace(run_id)
        if trace:
            parent = (trace_service.current_span_stack.get(run_id) or [None])[-1]
            trace.add_span(Span(
                parent_span_id=parent,
                span_type="llm",
                name="echo_llm",
                start_time=datetime.utcnow(),
                duration_ms=float(self.latency_ms),
                input=input,
                token_usage=TokenUsage(
                    input_tokens=self.input_tokens,
                    output_tokens=self.output_tokens,
                    total_tokens=self.input_tokens + self.output_tokens,
                    model=self.model,
                ),
                status="success",
            ))

        if self.latency_ms:
            await asyncio.sleep(self.latency_ms / 1000.0)
        return f"{self.prefix}{input}"
