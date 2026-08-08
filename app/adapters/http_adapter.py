"""HTTP adapter: runs an agent deployed as a separate remote service.

The platform POSTs `{input, run_id, agent_id}` to `base_url + "/evaluate"`;
the service returns:

    {"output": str, "spans": [{"span_type": "llm"|"tool"|"retriever",
        "name": str, "duration_ms": float,
        "token_usage": {"input_tokens": int, "output_tokens": int, "model": str} | None,
        "status": "success"|"error"}]}

Remote spans are injected as children of the agent span, so
TimingMetricsService can compute the per-module (llm/tool/retriever/idle)
breakdown. This is the "agent lives in a different architecture" path:
the only coupling is this JSON contract.
"""

from datetime import datetime

import httpx

from app.models.trace import Span, TokenUsage
from app.services.tracing import trace_service


class HttpAgentAdapter:
    """Adapter for agents deployed as a remote service."""

    def __init__(self, base_url: str, timeout: float = 120.0, **kwargs):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @trace_service.observe_agent(name="http_agent")
    async def run(self, input: str, run_id: str, agent_id: str, **kwargs) -> str:
        """Call the remote agent and fold its reported spans into the trace."""
        # trust_env=False: don't let http_proxy hijack the local agent call
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            resp = await client.post(
                f"{self.base_url}/evaluate",
                json={"input": input, "run_id": run_id, "agent_id": agent_id},
            )
            resp.raise_for_status()
            data = resp.json()

        self._inject_spans(run_id, data.get("spans") or [])
        return data.get("output", "")

    def _inject_spans(self, run_id: str, spans: list) -> None:
        """Import spans reported by the remote service into the active trace."""
        trace = trace_service.get_trace(run_id)
        if not trace:
            return
        stack = trace_service.current_span_stack.get(run_id) or []
        parent = stack[-1] if stack else None
        for s in spans:
            usage = s.get("token_usage")
            trace.add_span(Span(
                parent_span_id=parent,
                span_type=s.get("span_type", "llm"),
                name=s.get("name", "remote_call"),
                start_time=datetime.utcnow(),
                duration_ms=s.get("duration_ms", 0.0),
                token_usage=TokenUsage(**usage) if usage else None,
                status=s.get("status", "success"),
            ))
