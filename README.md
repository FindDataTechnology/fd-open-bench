# FD Open Bench

An **Agent Performance Evaluation Platform** built with DeepEval integration, providing comprehensive evaluation of AI agents with runtime tracing, custom evaluators, business value modeling, and a web UI for analysis.

## Features

- **DeepEval Integration**: First-class support for DeepEval metrics (TaskCompletion, StepEfficiency, PlanQuality, etc.)
- **Custom Evaluators**: Three-tier evaluator framework (validators, LLM judges, domain executors)
- **Business Value Modeling**: Track costs (tokens, time) vs. business value with ROI calculation
- **Runtime Tracing**: Full execution traces with token usage, timing, and span hierarchy
- **Batch Evaluation**: Queue-based parallel evaluation with progress tracking
- **Web Dashboard**: Real-time monitoring, trace visualization, cost analysis, A/B testing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (React + TypeScript)              │
│  Dashboard | Trace Explorer | Cost Analyzer | Config Builder│
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket/REST
┌──────────────────────────▼──────────────────────────────────┐
│               FastAPI Backend                               │
│  Agents | Datasets | Evaluations | Results | Evaluators    │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐
│   PostgreSQL    │ │    Redis    │ │   Celery Workers │
│   Database      │ │   Queue     │ │   (Evaluation)   │
└─────────────────┘ └─────────────┘ └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional, for full stack)

### Installation (Development)

```bash
# Clone the repository
git clone https://github.com/your-org/fd-open-bench.git
cd fd-open-bench

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using Docker Compose

```bash
# Start all services (backend, frontend, db, redis, celery)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Project Structure

```
fd-open-bench/
├── alembic/                 # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/                 # REST API endpoints
│   ├── core/                # Configuration, logging, security
│   ├── models/              # SQLAlchemy data models
│   ├── repositories/        # Data access layer
│   ├── evaluators/          # Evaluator framework (validators, judges, executors)
│   ├── services/            # Business logic services
│   ├── tasks/               # Celery tasks for batch processing
│   └── main.py              # Application entry point
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── pyproject.toml           # Python dependencies
├── docker-compose.yml       # Container orchestration
└── README.md
```

## Core Concepts

### Agent

An agent configuration including its adapter type (OpenAI, LangChain, custom), model settings, tools, and pricing configuration.

### Dataset

A collection of test cases (Goldens) used for batch evaluation.

### Golden

A single test case containing:
- `input`: What to send to the agent
- `expected_output`: Optional ground truth
- `expected_tools`: Optional list of expected tool calls
- `business_value`: Expected value if task succeeds

### Evaluation Run

A batch evaluation job that runs an agent against a dataset with configured evaluators.

### Evaluator

A check that validates agent outputs:
- **Validators**: Fast, deterministic (regex, JSON schema, keywords)
- **LLM Judges**: Flexible, expensive (DeepEval metrics, custom prompts)
- **Executors**: Ground truth validation (SQL, API, code execution)

## CLI & MCP

`fd-bench` is a chat-first CLI that drives the platform through an MCP server — no browser needed. The same MCP server also powers Claude Desktop and (later) a web sidebar.

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

Point Claude Desktop at the same binary — no separate server process to run:

```jsonc
// Claude Desktop -> Settings -> Developer -> MCP Servers
{
  "mcpServers": {
    "fd-open-bench": { "command": "fd-bench", "args": ["mcp", "serve"] }
  }
}
```

The domain tools (`run_evaluation`, `get_evaluation_status`, `analyze_weaknesses`, `compare_agents`, `find_best_performer`, `export_report`) and the unstable `raw_api` escape hatch are then available in Claude Desktop. Every `raw_api` call is logged — that log is the backlog of future domain tools (promote repeated patterns into dedicated tools).

### Transports

- `fd-bench mcp serve` — stdio (default; used by the CLI and Claude Desktop).
- `fd-bench mcp serve --http [--port 8998]` or `MCP_HTTP=1` — streamable HTTP, for the future CopilotKit sidebar.

> **Auth gate:** the HTTP transport is local-only for now. Before exposing it beyond localhost (e.g. for CopilotKit), add auth to the MCP server. CopilotKit itself is deferred — the existing web UI keeps working in the meantime.

## API Documentation

Interactive API docs are available at `/docs` when running the backend:

```bash
http://localhost:8000/docs
```

## License

MIT License

---

Built with ❤️ using FastAPI, React, DeepEval, and PostgreSQL.
