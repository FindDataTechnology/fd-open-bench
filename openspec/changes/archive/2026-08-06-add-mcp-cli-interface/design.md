## Context

FD Open Bench today exposes a FastAPI backend (`/api/v1/agents`, `/datasets`, `/evaluations`, `/evaluators`) and a React web UI. There is no terminal or chat surface. Operators want to drive evaluations and read results without a browser, and want an LLM in the loop for ad-hoc analysis. The backend and web UI stay as-is; this change adds an MCP server as the canonical tool surface and a `fd-bench` CLI as its primary client.

## Goals / Non-Goals

**Goals:**
- One MCP server, reusable by the `fd-bench` CLI and Claude Desktop (stdio) and a future web sidebar (HTTP), from a single FastMCP server definition.
- Domain-level tools for the common evaluation workflows, plus a `raw_api` escape hatch for everything else.
- Stateless / ephemeral: no chat-history tables, no session store.
- The CLI ships a one-shot mode (scriptable, no LLM) and a chat REPL (Anthropic tool-calling), both sharing the same tools.

**Non-Goals:**
- CopilotKit sidebar / Node runtime (deferred to a later change).
- Persistent chat history or resuming a chat session across CLI invocations.
- New backend REST endpoints — the server is a client of the existing API over `httpx`.
- Auth on the MCP server itself (local-first; see Risks).

## Decisions

**FastMCP for the server.** Native multi-transport (stdio + streamable-HTTP) and tool decorators in one definition; adding the same tools twice (once per transport) is avoided. *Alternatives considered:* the raw `mcp` SDK (more boilerplate, transport plumbing is manual); a CopilotKit-only surface (Node runtime — stack mismatch for a Python project). FastMCP wins on transport reuse and Python fit.

**CLI spawns the MCP server as a stdio subprocess** via a single `fd-bench mcp serve` entrypoint. *Alternatives considered:* importing the server in-process (faster, but Claude Desktop could not reuse the same path and we'd maintain two ways to run the server). Subprocess + shared binary gives one code path for CLI and Claude Desktop.

**Chat mode calls the Anthropic API directly** with the MCP tools surfaced as function definitions; the CLI executes returned tool calls against the spawned server. *Alternatives considered:* routing chat through a CopilotKit runtime (would force Node into the CLI path and couple the CLI to the deferred web work). Direct API keeps the CLI dependency-light and decoupled from CopilotKit.

**`raw_api` as one explicit tool** taking `method`, `path`, `params`, `body`. *Alternatives considered:* auto-generating one tool per OpenAPI operation (explodes the tool count, leaks internal shape, harder for the LLM to choose among). A small set of hand-written domain verbs + one raw escape hatch keeps the tool list small and intentful; repeated `raw_api` use is the signal for the next domain tool.

**Ephemeral sessions.** No session DB. *Alternatives considered:* persistent conversation state. Ephemeral removes a whole subsystem; because the backend already persists evaluation runs, a user can resume work in a new CLI session by referencing a `run_id` via `get_evaluation_status`.

## Risks / Trade-offs

- [raw_api leaks internal API shape to the LLM; refactors break old transcripts] → documented as unstable in tool descriptions and README; every call logged so repeated patterns surface as backlog; prefer domain tools in docs.
- [Long-running evaluations do not survive CLI exit in chat] → non-goal; `run_evaluation` returns a `run_id` and the user can poll with `get_evaluation_status` in a later session. Documented in README.
- [Two transports = two failure surfaces] → FastMCP abstracts both; both exercised in tasks. Acceptable.
- [Anthropic API key required for chat mode] → one-shot mode works without it; chat mode exits with a clear error if `ANTHROPIC_API_KEY` is unset.
- [MCP server trusts the local backend and has no auth] → local-first assumption is fine for CLI/Claude Desktop. **Before the deferred CopilotKit phase exposes the HTTP transport beyond localhost, auth MUST be added** — this is the gate for that later change.

## Migration Plan

Additive: new `mcp_server/` and `fd_bench/` packages, new deps in `pyproject.toml`, no backend changes. Deploy = install new deps + expose the `fd-bench` console script. Rollback = remove the two packages and deps; backend and web UI are unaffected. No DB migrations.

## Open Questions

- Exact boundary of the initial domain tool set — resolved in tasks as "start minimal (`run_evaluation`, `get_evaluation_status`, `analyze_weaknesses`, `compare_agents`, `find_best_performer`, `export_report`); `raw_api` covers the rest incrementally."
- Backend base URL source — propose a new `FD_BENCH_API_URL` env var (default `http://localhost:8000`), shared by the server and CLI; confirm in tasks.
