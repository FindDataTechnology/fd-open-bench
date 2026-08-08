# FD Open Bench

An **Agent Benchmark Platform** for internal use: compare AI agents on the same
benchmark, and judge them by **technical quality AND business value** — cost per
successful task, ROI, human-cost replacement, and time value.

## Features

- **Benchmarks**: a dataset + a metric suite + a business model (`value_formula`,
  `time_value_rate`) — one unit of comparison
- **Batch evaluation**: run N agents against the same benchmark in one batch,
  with per-agent progress tracking
- **Leaderboard**: same-benchmark comparison of agents, technical stats
  (avg/stddev per metric) next to business metrics
- **Business metrics**: cost per successful task, human replacement ratio,
  time cost, custom value formulas (safe AST-evaluated, no `eval()`)
- **Runtime tracing**: full execution traces with token usage, timing, spans
- **DeepEval integration**: TaskCompletion, StepEfficiency, PlanQuality, etc.
- **CLI & MCP**: drive everything from `fd-bench` or Claude Desktop

## Architecture

Single process, single SQLite file — no Postgres, no Redis, no Celery:

```
┌──────────────────────────────────────────────┐
│        Web UI (React + TypeScript)           │
│   Leaderboard | Benchmarks | Agents | Runs   │
└──────────────────────┬───────────────────────┘
                       │ REST /api/v1
┌──────────────────────▼───────────────────────┐
│            FastAPI backend (8999)            │
│   agents | datasets | evaluations | batches  │
│   evaluators | benchmarks (leaderboard)      │
│   background eval execution via asyncio      │
└──────────────────────┬───────────────────────┘
                       │ SQLAlchemy
              ┌────────▼────────┐
              │  SQLite (WAL)   │
              │ fd_open_bench.db│
              └─────────────────┘

  fd-bench CLI / Claude Desktop ──MCP(stdio)──▶ mcp_server ──HTTP──▶ backend
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (frontend dev server)

### Development

```bash
git clone <repo> && cd fd-open-bench
python -m venv venv && source venv/bin/activate

./start.sh   # installs deps, runs migrations, starts backend :8999 + frontend :3118
```

`start.sh` creates `.env` from `.env.example` on first run — edit it to add your
LLM API keys, then re-run. SQLite database file is created automatically
(`fd_open_bench.db`, WAL mode).

Stop everything with `./stop.sh` (or Ctrl+C in the `start.sh` terminal).

- Backend API: http://localhost:8999 — Swagger docs at `/docs`
- Frontend: http://localhost:3118

### Docker (optional)

```bash
docker-compose up -d    # backend :8999 (SQLite in fd_data volume) + frontend :3000
docker-compose down
```

## Core Concepts

### Benchmark (题 + 尺 + 生意)

The unit of comparison: a **dataset** (the questions), a **metric suite** (the
ruler), and a **business model** (value formula + time value rate). Agents are
only ever compared within the same benchmark.

### Golden

A single test case: `input`, optional `expected_output` / `expected_tools`, plus
optional business fields — `business_value` ($ if the task succeeds),
`human_cost` ($ for a human to do it), `human_minutes`.

### Batch

One `POST /api/v1/batches` runs several agents against one benchmark; each agent
gets its own evaluation run sharing a `batch_id`. Compare within a batch or
across all runs of a benchmark.

### Leaderboard

`GET /api/v1/benchmarks/{id}/leaderboard` — per-agent technical stats and
business metrics (cost per success, human replacement, time cost, ROI), sorted
by cost per successful task.

### Evaluator

- **Validators**: fast, deterministic (regex, JSON schema, keywords)
- **LLM judges**: DeepEval metrics, custom prompts
- **Executors**: ground-truth validation (SQL, API, code execution)

## CLI & MCP

`fd-bench` drives the platform through an MCP server — no browser needed.
Usage is unchanged by the refactor.

### Setup

```bash
pip install -e ".[dev]"                              # installs the fd-bench console script
export FD_BENCH_API_URL=http://localhost:8999       # backend (default)
export ANTHROPIC_API_KEY=sk-ant-...                 # only for `fd-bench chat`
```

### One-shot (scriptable, no LLM)

```bash
fd-bench run-eval --agent paybot --dataset goldens_v2 --metrics task_completion,step_efficiency
fd-bench status <run_id>
fd-bench report <run_id> --format markdown > report.md
fd-bench weaknesses --agent-id <agent_id> --top 3
fd-bench raw GET /api/v1/agents                     # unstable escape hatch
```

### Chat (Claude + MCP tools)

```bash
fd-bench chat
fd-bench> "evaluate paybot on goldens_v2, then tell me where it's weakest"
```

Chat defaults to `claude-opus-4-8`; override with `FD_BENCH_MODEL=claude-sonnet-5`.

### Use with Claude Desktop

```jsonc
// Claude Desktop -> Settings -> Developer -> MCP Servers
{
  "mcpServers": {
    "fd-open-bench": { "command": "fd-bench", "args": ["mcp", "serve"] }
  }
}
```

Domain tools (`run_evaluation`, `get_evaluation_status`, `analyze_weaknesses`,
`compare_agents`, `find_best_performer`, `export_report`) plus the unstable
`raw_api` escape hatch. Every `raw_api` call is logged — repeated patterns get
promoted into dedicated tools.

### Transports

- `fd-bench mcp serve` — stdio (default; used by the CLI and Claude Desktop).
- `fd-bench mcp serve --http [--port 8998]` or `MCP_HTTP=1` — streamable HTTP.

> **Auth:** local-only by default. Set `FD_BENCH_API_TOKEN` on the backend to
> require `Authorization: Bearer <token>` on all API requests (empty = open).
> Do not expose the HTTP transport beyond localhost without it.

## Project Structure

```
fd-open-bench/
├── alembic/                 # Database migrations
├── app/
│   ├── api/routes/          # REST API endpoints
│   ├── core/                # Config, logging, single-token auth guard
│   ├── models/              # SQLAlchemy data models
│   ├── evaluators/          # Evaluator framework
│   ├── services/            # Business logic (incl. evaluation engine)
│   └── main.py              # Application entry point
├── cli/                     # fd-bench CLI
├── mcp_server/              # MCP server (stdio/HTTP)
├── frontend/                # React + TypeScript + Vite
├── tests/                   # unit / integration / e2e
├── start.sh / stop.sh       # dev environment scripts
└── docker-compose.yml       # optional container deployment
```

## License

MIT License

---

Built with FastAPI, React, DeepEval, and SQLite.
