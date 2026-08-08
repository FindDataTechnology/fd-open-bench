## Why

Teams building AI agents lack a unified way to evaluate agent performance across multiple dimensions: technical quality (did the agent complete the task correctly?), operational efficiency (how much time and tokens did it spend?), and business value (does the agent deliver ROI?). Existing tools focus on one aspect—DeepEval provides LLM metrics but no business modeling; cost trackers monitor spend but don't evaluate quality; custom test harnesses require significant engineering effort. This fragmentation makes it impossible to answer the fundamental question: "Is this agent actually valuable to the business, and at what cost?"

We need a comprehensive evaluation platform that combines DeepEval's agent metrics, custom result validation, runtime tracing, and business value modeling into a single system with a web UI for visualization and analysis. This enables data-driven decisions about agent deployment, optimization, and retirement.

## What Changes

- **New evaluation engine** built on DeepEval that evaluates custom agents in batch testing mode, supporting both end-to-end metrics (task completion, step efficiency, plan quality) and component-level metrics (tool correctness, argument correctness)
- **Agent runtime tracing** using DeepEval's `@observe` decorators to capture full execution traces (agent → LLM → tool → retriever spans) with token usage, timing, and input/output data per span
- **Custom evaluator framework** with three tiers: fast deterministic validators (regex, JSON schema, keywords), LLM-based judges (DeepEval metrics, custom prompts, G-Eval), and domain-specific executors (SQL validation, API testing, code execution, business logic checks)
- **Business value modeling** that tracks both cost side (token spend, per-minute/per-hour pricing, infrastructure costs) and value side (revenue generated, cost savings, business outcomes), calculates ROI, and compares token-based costs against time-based pricing
- **Web UI dashboard** with real-time monitoring, trace visualization (tree view and timeline), cost analyzer with ROI trends, evaluation configuration interface (visual builder + code editor + YAML), historical analysis with A/B testing, and export capabilities (CSV, PDF reports)
- **Batch evaluation system** with queue-based processing, parallel evaluation runs, progress tracking, and result aggregation across test cases
- **Data storage layer** using PostgreSQL for evaluation results, traces, business metrics, and test case datasets (Goldens)

## Capabilities

### New Capabilities

- `evaluation-engine`: Core evaluation orchestration built on DeepEval, supporting batch evaluation of custom agents with configurable metric collections and evaluation datasets
- `agent-runtime-tracing`: Execution trace capture using DeepEval's observe decorators, storing full span trees with token usage, timing, and I/O data for each agent run
- `custom-evaluators`: Pluggable evaluator framework with three tiers (validators, LLM judges, domain executors), supporting YAML config, custom Python functions, and visual builder UI
- `business-value-model`: Cost tracking (tokens, time-based pricing, infrastructure), value calculation (revenue, cost savings, business outcomes), ROI computation, and cost-benefit comparison views
- `web-ui-dashboard`: React-based web interface with real-time monitoring, trace explorer, cost analyzer, evaluation config builder, historical trends, A/B testing, and export functionality
- `batch-evaluation-system`: Queue-based batch processing with parallel execution, progress tracking, result aggregation, and webhook/email notifications on completion
- `data-storage-layer`: PostgreSQL schema for agents, evaluation runs, results, traces, test cases (Goldens), business models, and evaluator configurations with appropriate indexing for query performance

### Modified Capabilities

(None - this is a new system)

## Impact

**New dependencies:**
- DeepEval (Python evaluation framework)
- FastAPI (async web framework for backend API)
- React + TypeScript + Recharts/D3 (frontend dashboard)
- PostgreSQL (primary data store)
- Redis + Celery (batch evaluation queue and worker pool)
- Docker/Docker Compose (deployment)

**APIs:**
- REST API for evaluation management (create runs, query results, manage agents)
- WebSocket API for real-time evaluation progress and live monitoring
- Webhook callbacks for batch evaluation completion notifications

**Systems affected:**
- Agent codebases must be instrumented with `@observe` decorators (or wrapped in adapter layer)
- LLM API keys required for both agent execution and LLM-based evaluators
- Optional: Docker for sandboxed code execution in domain evaluators
- Optional: Email/webhook endpoints for notifications

**Data volume:**
- Evaluation traces can be large (10KB-1MB per run depending on agent complexity)
- Estimated storage: 1GB per 10,000 evaluation runs with full traces
- Time-series metrics for trend analysis require efficient indexing

**Security considerations:**
- Multi-tenant data isolation (if deployed as SaaS)
- Secure storage of LLM API keys and database credentials
- Sandboxed execution for code evaluators to prevent malicious code execution
- Read-only database connections for SQL validators to prevent accidental data modification
