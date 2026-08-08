"""Interactive chat REPL: Anthropic API (claude-opus-4-8) + MCP tools."""
import json
import os
import sys

from anthropic import AsyncAnthropic

from mcp_server.config import ANTHROPIC_API_KEY
from fd_bench.runner import McpRunner

# claude-api skill: default to claude-opus-4-8; never downgrade for cost.
# The user can override via FD_BENCH_MODEL (e.g. claude-sonnet-5).
DEFAULT_MODEL = "claude-opus-4-8"


def _model() -> str:
    return os.getenv("FD_BENCH_MODEL", DEFAULT_MODEL)


async def chat() -> None:
    if not ANTHROPIC_API_KEY:
        print(
            "error: ANTHROPIC_API_KEY is not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...   (or run `ant auth login`)",
            file=sys.stderr,
        )
        sys.exit(1)

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    model = _model()
    system = (
        "You drive the FD Open Bench evaluation platform through MCP tools. "
        "Call tools to run evaluations, inspect results, and analyze agent "
        "performance. Prefer domain tools over raw_api. Be concise."
    )

    async with McpRunner() as runner:
        tools_list = await runner.list_tools()
        tools = [
            {
                "name": t.name,
                "description": (t.description or t.name).strip()[:1024],
                "input_schema": t.inputSchema or {"type": "object", "properties": {}},
            }
            for t in tools_list
        ]

        messages: list[dict] = []
        print(f"fd-bench chat ({model}). Ctrl-D to exit.")
        while True:
            try:
                user = input("fd-bench> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user.strip():
                continue
            messages.append({"role": "user", "content": user})
            await _turn(client, model, system, tools, messages, runner)


async def _turn(client, model, system, tools, messages, runner) -> None:
    """Run one assistant turn: loop tool calls until end_turn."""
    while True:
        resp = await client.messages.create(
            model=model,
            max_tokens=16384,
            system=system,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        for block in resp.content:
            if getattr(block, "type", None) == "text":
                print(block.text)

        tool_blocks = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not tool_blocks:
            break

        results = []
        for tb in tool_blocks:
            args = tb.input or {}
            print(f"[tool] {tb.name} {json.dumps(args, default=str)[:160]}")
            try:
                data = await runner.call_tool(tb.name, args)
                out = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
            except Exception as e:
                out = f"ERROR: {e}"
            print(f"[tool] {tb.name} -> {out[:200]}")
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": out[:8000],
                }
            )
        messages.append({"role": "user", "content": results})
