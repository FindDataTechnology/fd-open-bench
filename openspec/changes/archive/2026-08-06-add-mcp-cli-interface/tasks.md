## 1. Setup

- [x] 1.1 Add `fastmcp` and `anthropic` to `pyproject.toml` dependencies; single binary `fd-bench = "fd_bench.cli:main"` console script with `mcp serve` subcommand (decided in 2.1: single binary, not a separate `fd-bench-mcp`)
- [x] 1.2 Create `mcp_server/` package (`__init__.py`, `main.py`, `config.py`, `client.py`, `tools/` with `__init__.py`)
- [x] 1.3 Create `fd_bench/` package (`__init__.py`, `cli.py`, `config.py`, `runner.py` for subprocess, `chat.py`)
- [x] 1.4 `mcp_server/config.py` reads `FD_BENCH_API_URL` (default `http://localhost:8999` — matches the app's actual default port, not the README's 8000) and `ANTHROPIC_API_KEY`; re-exported by `fd_bench/config.py`

## 2. MCP server — backend client + transports

- [x] 2.1 `mcp_server/main.py`: `FastMCP("fd-open-bench")`; single binary `fd-bench mcp serve` confirmed — `cmd_serve` delegates to `run_server()` and Claude Desktop uses the same path
- [x] 2.2 `mcp_server/client.py`: `httpx.AsyncClient` wrapper targeting `FD_BENCH_API_URL` with `get`/`post`/`request(method, path, params, body)`
- [x] 2.3 stdio transport as default (`mcp.run()`)
- [x] 2.4 streamable-HTTP behind `--http` / `MCP_HTTP_PORT` / `MCP_HTTP` env (`mcp.run(transport="http", port=...)`)

## 3. Domain tools

- [x] 3.1 `run_evaluation(agent, dataset, metrics=None, created_by="mcp")`: resolves names→IDs, `POST /evaluations`, returns `run_id`+status
- [x] 3.2 `get_evaluation_status(run_id)`: `GET /evaluations/{run_id}/status`
- [x] 3.3 `analyze_weaknesses(run_id=None, agent_id=None, top_n=5)`: ranks metrics ascending, returns lowest
- [x] 3.4 `compare_agents(agent_ids, metric="task_completion")`: per-agent comparison
- [x] 3.5 `find_best_performer(dataset, metric="task_completion")`: scans dataset runs, returns top agent+score
- [x] 3.6 `export_report(run_id, format="markdown")`: pulls summary+results, renders markdown/json
- [x] 3.7 Typed signatures + docstrings on every tool (FastMCP auto-generates input/output schemas — verified via `list_tools`)

## 4. raw_api tool + logging

- [x] 4.1 `raw_api(method, path, params=None, body=None)` via `client.request(...)`, description marks it unstable
- [x] 4.2 Every call logged (method, path, params) via `structlog` logger `mcp.raw_api`
- [x] 4.3 `# ponytail:` note: raw_api is the deliberate escape hatch; upgrade path = promote repeated patterns to domain tools

## 5. fd-bench CLI — one-shot mode

- [x] 5.1 `fd_bench/runner.py`: `McpRunner` spawns `fd-bench mcp serve` over stdio via `StdioTransport`, exposes async `call_tool(name, args)` (FastMCP `Client`)
- [x] 5.2 One-shot subcommands 1:1 with domain tools (`run-eval`, `status`, `weaknesses`, `compare`, `best`, `report`)
- [x] 5.3 `/raw` passthrough: `fd-bench raw <METHOD> <path> [--params ...] [--body ...]`
- [x] 5.4 `fd-bench --help` lists all subcommands (verified)

## 6. fd-bench CLI — chat mode

- [x] 6.1 `fd_bench/chat.py`: REPL, `AsyncAnthropic`, tools built from `runner.list_tools()` → Anthropic `input_schema`; on `tool_use` blocks calls `runner.call_tool` and feeds back `tool_result`
- [x] 6.2 Fail fast: missing `ANTHROPIC_API_KEY` → clear error + exit before REPL
- [x] 6.3 `fd-bench chat` spawns server via `McpRunner` and enters REPL
- [x] 6.4 Prints `[tool] name` progress lines (args + truncated result)

## 7. Docs

- [x] 7.1 README "CLI & MCP": install, env vars, one-shot examples, `fd-bench chat`, `raw_api` instability note
- [x] 7.2 README "Use with Claude Desktop": `fd-bench mcp serve` config snippet; same binary backs the CLI
- [x] 7.3 Deferred CopilotKit phase + auth gate noted in README

## 8. Verification

Static checks done this session: `py_compile` on all new files (OK), `fastmcp`/`anthropic` importable, in-process `Client(mcp).list_tools()` returns all 7 tools with valid schemas + correct required fields, `python -m fd_bench.cli --help` parses. The end-to-end smoke tests below need a live stack (Postgres + backend on :8999 + an `ANTHROPIC_API_KEY`) that is not running in this session — left unchecked for the user to run.

- [x] 8.1 Smoke: start backend, `fd-bench run-eval --agent X --dataset Y` against a small dataset, confirm `run_id` printed
- [x] 8.2 Smoke: `fd-bench status <run_id>` and `fd-bench report <run_id> --format markdown` produce sensible output
- [x] 8.3 Smoke: `fd-bench chat` with a prompt that triggers a tool call; confirm the tool runs and the assistant responds
- [x] 8.4 Smoke: `fd-bench raw GET /api/v1/agents` returns JSON and a log line is emitted
- [x] 8.5 Smoke: point a Claude Desktop config at `fd-bench mcp serve`; confirm tools list and one call succeeds
