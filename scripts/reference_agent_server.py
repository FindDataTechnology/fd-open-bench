"""Reference remote agent service — the contract `HttpAgentAdapter` expects.

This is a STUB agent that fakes LLM/tool work with sleeps so you can test the
whole pipeline without wiring your real agent. Point your real agent at the
same contract:

    POST /evaluate  {input, run_id, agent_id}
    ->  {"output": str, "spans": [{span_type, name, duration_ms, token_usage?}]}

Run:
    uvicorn scripts.reference_agent_server:app --port 8099
"""

import asyncio
import time

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class EvalRequest(BaseModel):
    input: str
    run_id: str
    agent_id: str


async def _fake(llm_tokens: tuple, sleep: float) -> dict:
    """One fake module: sleep, then report its duration."""
    t0 = time.perf_counter()
    await asyncio.sleep(sleep)
    return {
        "span_type": "llm",
        "name": "llm_call",
        "duration_ms": (time.perf_counter() - t0) * 1000,
        "token_usage": {
            "input_tokens": llm_tokens[0],
            "output_tokens": llm_tokens[1],
            "model": "gpt-4o",
        },
    }


@app.post("/evaluate")
async def evaluate(req: EvalRequest):
    # fake modules: plan -> tool -> answer
    plan = await _fake((120, 40), 0.05)

    t0 = time.perf_counter()
    await asyncio.sleep(0.2)
    tool = {
        "span_type": "tool",
        "name": "search",
        "duration_ms": (time.perf_counter() - t0) * 1000,
    }

    answer = await _fake((80, 60), 0.1)

    return {
        "output": f"answer: {req.input}",
        "spans": [plan, tool, answer],
    }
