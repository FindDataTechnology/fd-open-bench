## Why

The platform's only interactive surface today is the web UI. Operators and developers want to drive evaluations, inspect results, and get insights from a terminal or an LLM chat — without a browser. Making the MCP server the the primary, chat-first interface means one tool surface reusable by a custom CLI, Claude Desktop, and (later) a web sidebar — while the FastAPI backend and existing web UI keep working unchanged.

## What Changes

- Add an **MCP server** (`mcp_server/` package, built on FastMCP) exposing the platform as model-context tools: domain-level verbs plus a `raw_api` escape hatch.
- Add a thin **`fd-bench` CLI** that is the primary client: one-shot mode (scriptable, no LLM) and a chat REPL (Anthropic tool-calling). The CLI spawns the MCP server as a stdio subprocess.
- **One server, two transports**: stdio (CLI + Claude Desktop) and HTTP/SSE (future CopilotKit sidebar), served from a single FastMCP definition — no duplicated tool code.
- **Ephemeral by design**: no chat-history tables, no session store, no context restoration. The MCP server is stateless; each CLI invocation is fresh.
- **Two-tier tools**: domain verbs (`run_evaluation`, `get_evaluation_status`, `analyze_weaknesses`, `compare_agents`, `find_best_performer`, `export_report`, and a small initial set more) **and** `raw_api` (method/path/params/body) for power users. `raw_api` is documented unstable and logged so repeated use becomes the backlog of future domain tools.
- Add deps to `pyproject.toml`: `fastmcp`, `anthropic` (chat mode). `httpx` is already present.
- README: how to use `fd-bench` and how to point Claude Desktop at the MCP server binary.

## Capabilities

### New Capabilities

- `mcp-interface`: The MCP server (domain tools, `raw_api`, stdio + HTTP transports) and the `fd-bench` CLI client (one-shot + chat modes) that together provide a chat-first, terminal-native interface to the platform's existing evaluation capabilities.

### Modified Capabilities

<!-- None. The MCP server and CLI are additive — they call the existing FastAPI backend over httpx but change no existing spec-level behavior. -->

## Impact

- **New code**: `mcp_server/` package (tools, transports, server entrypoint); `fd_bench/` CLI package (one-shot dispatch, chat REPL, subprocess spawn).
- **Backend**: no changes. The MCP server is a client of the existing REST API (`/api/v1/agents`, `/datasets`, `/evaluations`, `/evaluators`) over `httpx`.
- **Dependencies**: `pyproject.toml` gains `fastmcp` and `anthropic`; `httpx` already declared.
- **Web UI**: unchanged. CopilotKit sidebar is explicitly deferred (Node runtime is a stack-mismatch cost for a Python project; chat > web lowers near-term ROI). Existing React UI keeps working.
- **Operations**: a new long-lived-ish process only when the CLI/Claude Desktop is running; otherwise stateless and on-demand.
