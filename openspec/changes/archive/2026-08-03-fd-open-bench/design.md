## Context

We are building a new agent performance evaluation system from scratch. The project repository (`fd-open-bench`) currently contains only the OpenSpec planning scaffolding—no existing code, no dependencies, no prior architecture. This is a greenfield project.

**Stakeholders:**
- Agent developers who need to iterate on agent quality with fast feedback loops
- Engineering managers who need to decide whether to deploy, optimize, or retire agents
- Business stakeholders who need to understand agent ROI in dollar terms

**Constraints:**
- Must integrate with DeepEval as the core evaluation framework (user requirement)
- Must support custom agents (not just OpenAI/LangChain)—agents may use any framework or be framework-less
- Must support batch evaluation (offline testing), not just production monitoring
- Must provide a web UI—CLI-only is insufficient
- Must model business value alongside technical metrics

**Current state:** Nothing exists. We have full freedom to choose the stack and architecture, but also full responsibility for building everything.

## Goals / Non-Goals

**Goals:**
- Provide a unified evaluation platform that answers "Is this agent valuable, and at what cost?"
- Integrate DeepEval's agent metrics (TaskCompletion, StepEfficiency, PlanQuality, PlanAdherence, ToolCorrectness, ArgumentCorrectness) as first-class citizens
- Support three tiers of custom evaluators: validators (fast/deterministic), LLM judges (flexible/expensive), and domain executors (ground truth)
- Model both cost (tokens, time, infrastructure) and value (revenue, savings, outcomes) to compute ROI
- Provide a web UI that serves developers (trace inspection), managers (dashboards), and business users (cost-benefit views)
- Support batch evaluation of hundreds of test cases with parallel execution
- Allow evaluators to be configured via YAML, Python code, or a visual builder—different users have different preferences
- Ship as a self-hosted Docker Compose deployment initially, with a path to multi-tenant Kubernetes deployment

**Non-Goals:**
- Real-time production monitoring with sub-second latency (we're building for batch testing; production monitoring is a future extension)
- Support for proprietary agent frameworks that don't expose function call boundaries (we need observable spans)
- Multi-region deployment or geo-distributed data storage
- Built-in agent hosting—we evaluate agents, we don't run them in production
- Automatic prompt optimization (DeepEval has this; we're not building it in v1)
- Red-teaming or adversarial evaluation (future work)

## Decisions

### Decision 1: Backend framework — FastAPI (Python)

**Choice:** FastAPI for the backend API.

**Alternatives considered:**
- **Django REST Framework:** More batteries-included, but heavier and synchronous-by-default. Our workload is I/O-bound (LLM API calls, DB queries, agent execution), so async matters.
- **Flask + asyncio:** Possible, but FastAPI gives us async support, automatic OpenAPI docs, and Pydantic validation out of the box.
- **Go (Gin/Fiber):** Faster, but we need deep Python integration with DeepEval. A Go backend would require a Python sidecar, adding operational complexity.

**Rationale:** FastAPI is async-native, has first-class Pydantic integration (which DeepEval also uses), generates OpenAPI specs automatically, and is Python—so we can import DeepEval directly without IPC or subprocess overhead. The Python ecosystem also gives us the richest set of evaluator implementations.

### Decision 2: Frontend framework — React + TypeScript + Recharts

**Choice:** React with TypeScript for the UI, Recharts for standard charts, D3 for custom trace visualization.

**Alternatives considered:**
- **Vue/Svelte:** Lighter, but smaller ecosystem for the kind of complex dashboard components we need (trace trees, Gantt timelines, resizable panels).
- **Streamlit/Gradio:** Fast to build, but insufficient for a production-grade dashboard with complex state management and custom visualizations.
- **Next.js vs Vite:** Next.js gives us SSR, but our app is a dashboard behind auth—SSR adds complexity without benefit. Vite + React is simpler and faster to develop.

**Rationale:** React has the largest ecosystem for dashboard UIs. Recharts handles 80% of our charting needs (line charts, bar charts, pie charts) with minimal config. D3 is needed for the trace tree visualization, which has non-standard layout requirements (nested spans with timing data). TypeScript catches the kind of bugs that erode trust in a dashboard.

### Decision 3: Database — PostgreSQL (single instance, JSONB for flexible data)

**Choice:** PostgreSQL with JSONB columns for semi-structured data (traces, evaluator configs, metric scores).

**Alternatives considered:**
- **PostgreSQL + TimescaleDB:** TimescaleDB adds time-series optimizations. We don't need it in v1—PostgreSQL's native indexing handles our query patterns. Add TimescaleDB later if trend queries become slow.
- **MongoDB:** Flexible schema is tempting for traces, but we have relational data (agents → runs → results) that benefits from SQL joins and transactions. MongoDB would force us to denormalize or do client-side joins.
- **SQLite:** Simpler, but doesn't support concurrent writes well. Batch evaluation with parallel workers will hit write contention. PostgreSQL handles this natively.

**Rationale:** PostgreSQL is the right default for a system with both relational structure and semi-structured payloads. JSONB lets us store traces and evaluator configs without rigid schemas, while SQL gives us transactional integrity for evaluation runs and results. We can add TimescaleDB as an extension later if needed—no migration required.

### Decision 4: Batch processing — Redis + Celery

**Choice:** Redis as the message broker, Celery as the task queue for batch evaluation.

**Alternatives considered:**
- **RQ (Redis Queue):** Simpler than Celery, but lacks Celery's workflow primitives (chains, groups, chords) which we'll need for complex evaluation pipelines (e.g., "run all validators, then aggregate, then run LLM judges").
- **Dramatiq:** Similar to Celery but smaller community. Celery's ecosystem (monitoring with Flower, retry policies, result backends) is more mature.
- **In-process asyncio tasks:** Works for small batches, but doesn't scale to hundreds of concurrent evaluations or survive backend restarts. We need durable queueing.
- **Kafka/ RabbitMQ:** Overkill for v1. Redis is already needed for caching; using it as the broker too reduces operational footprint.

**Rationale:** Celery is the battle-tested choice for Python batch processing. Redis is already in the stack for caching, so we're not adding a new dependency. Celery's canvas primitives (chains, groups) map naturally to our evaluation pipeline: validators run in parallel (group), then aggregation (chain), then LLM judges (group). Celery also gives us per-task retry policies, rate limiting (important for LLM API quotas), and result expiration.

### Decision 5: Agent instrumentation — Adapter pattern with @observe decorators

**Choice:** Define an `AgentAdapter` protocol. Users implement the adapter for their agent. The adapter wraps agent execution with DeepEval's `@observe` decorators to produce traces.

**Alternatives considered:**
- **Require users to add @observe directly to their agent code:** Intrusive—users must modify their agent codebase. The adapter pattern lets them wrap existing agents without modification.
- **Auto-instrumentation via monkey-patching:** Fragile and framework-specific. Different agent frameworks (LangChain, LlamaIndex, custom) have different internals.
- **OpenTelemetry integration:** OTel is the industry standard for tracing, but DeepEval's tracing is purpose-built for LLM evaluation (captures token usage, span types like "llm"/"tool"/"agent", etc.). We'd lose fidelity by forcing OTel.

**Rationale:** The adapter pattern gives us a clean abstraction: the evaluation engine calls `adapter.run(input)` and `adapter.get_trace()`, without knowing how the agent works internally. Users implement the adapter once per agent framework. The `@observe` decorators inside the adapter capture traces without adding latency (DeepEval's tracing is async and non-blocking). This also lets us ship pre-built adapters for popular frameworks (OpenAI, LangChain) while supporting custom agents.

### Decision 6: Evaluator execution model — Async with tier-specific concurrency

**Choice:** All evaluators implement an `async evaluate()` method. Validators run concurrently (CPU-bound, fast). LLM judges run concurrently with rate limiting (I/O-bound, expensive). Executors run with configurable concurrency (some have side effects and need sequential execution).

**Alternatives considered:**
- **Synchronous execution:** Simpler, but LLM judges take 1-30 seconds each. Sequential execution of 5 judges = 2 minutes per test case. Concurrent execution = 30 seconds.
- **Separate process pool for evaluators:** Adds complexity (IPC, serialization). Not needed—async is sufficient for I/O-bound work. CPU-bound validators are fast enough that they don't need process isolation.

**Rationale:** Async execution is the right abstraction for our workload. Validators are fast (<100ms) and can all run in parallel. LLM judges are I/O-bound (waiting on API responses) and benefit from concurrency, but need rate limiting to respect API quotas. Executors vary—SQL queries are I/O-bound, code execution may be CPU-bound. The async interface lets each evaluator type optimize internally while presenting a uniform API to the orchestrator.

### Decision 7: Score aggregation — Configurable strategy with tiered default

**Choice:** Aggregation strategy is configurable per evaluation run. Default is "tiered": validators gate (all must pass), then LLM judges and executors are weighted-averaged.

**Alternatives considered:**
- **Fixed strategy (e.g., always weighted average):** Too rigid. Some use cases need hard gates (e.g., "if safety check fails, score is 0 regardless of other metrics").
- **Always AND/OR:** Too simplistic. Real-world evaluation needs nuance—a response can be partially correct.
- **Custom Python function only:** Maximum flexibility, but high friction. Most users want a config option, not to write code.

**Rationale:** The tiered default (validators gate, then weighted average) matches how humans evaluate: "First, is it even acceptable? Then, how good is it?" Making it configurable lets power users override with AND/OR/weighted/custom strategies. The config is per-run, so the same agent can be evaluated with different strategies for different purposes (e.g., strict for production readiness, lenient for exploratory testing).

### Decision 8: Deployment — Docker Compose for v1, Kubernetes-ready design

**Choice:** Ship v1 as Docker Compose (FastAPI + React + PostgreSQL + Redis + Celery worker). Design the system so it can migrate to Kubernetes without architectural changes.

**Alternatives considered:**
- **Kubernetes from day 1:** More scalable, but higher operational complexity. Most teams don't need K8s for an internal tool. Docker Compose is sufficient for single-tenant deployment.
- **Serverless (AWS Lambda, etc.):** Doesn't fit—our workload includes long-running evaluations (minutes to hours) and persistent state (traces, results). Serverless is optimized for short, stateless requests.
- **Single binary (e.g., Go + embedded DB):** Simpler deployment, but we've chosen Python + PostgreSQL. A single binary would require rewriting in Go and using SQLite, which we've ruled out.

**Rationale:** Docker Compose is the right level of complexity for v1. It's easy to run locally, easy to deploy to a single server, and easy to understand. The design is Kubernetes-ready: stateless FastAPI workers, stateless Celery workers, external PostgreSQL and Redis. Migrating to K8s means writing Helm charts, not rewriting code.

### Decision 9: Caching strategy — Three-layer cache for LLM judges

**Choice:** Three-layer cache: in-memory (per-run), Redis (shared across runs, 24h TTL), database (persistent). Cache key is hash of (evaluator_name + config + input + output + model).

**Alternatives considered:**
- **No caching:** Wasteful. LLM judges cost $0.01-0.10 per call. Re-evaluating the same output during development burns money.
- **Database-only cache:** Slow (disk I/O). Most cache hits happen within a development session—Redis is faster and sufficient.
- **In-memory + Redis only:** Loses cache on restart. For persistent reference (e.g., "what did this evaluator score 3 months ago?"), we need database storage.

**Rationale:** The three-layer cache balances speed, cost, and persistence. In-memory avoids Redis round-trips within a run. Redis avoids re-evaluation during development. Database provides an audit trail and enables "show me historical scores for this evaluator." Cache invalidation is explicit: config changes invalidate that evaluator, model changes invalidate LLM judges.

### Decision 10: Security model — Sandbox executors, read-only DB connections, API key encryption

**Choice:** Code executors run in Docker containers with resource limits (CPU, memory, network). SQL validators use read-only database connections. LLM API keys are encrypted at rest using Fernet symmetric encryption.

**Alternatives considered:**
- **No sandboxing:** Faster, but a malicious agent output could execute arbitrary code on the host. Unacceptable for a multi-tenant deployment.
- **WebAssembly (WASM) sandbox:** Lighter than Docker, but WASM support for Python is immature. Docker is the pragmatic choice.
- **Plaintext API keys in env vars:** Simpler, but a database leak exposes all keys. Encryption at rest is a small cost for significant security.

**Rationale:** Security is non-negotiable for a system that executes user-provided code and stores API keys. Docker sandboxing is the industry standard for untrusted code execution. Read-only DB connections prevent accidental data modification by SQL validators. Fernet encryption is well-audited and adds minimal overhead.

## Risks / Trade-offs

**Risk: DeepEval version compatibility**
DeepEval is actively developed and may introduce breaking changes. → **Mitigation:** Pin DeepEval version in dependencies. Abstract DeepEval behind an internal interface so version upgrades require changes in one place. Test upgrades in a staging environment before production.

**Risk: LLM judge non-determinism**
LLM judges may produce different scores for the same input across runs, even with temperature=0. → **Mitigation:** Cache judge results aggressively (3-layer cache). Document that LLM judges are inherently non-deterministic. Provide a "confidence interval" metric by running judges multiple times and reporting variance (optional, power-user feature).

**Risk: Trace storage bloat**
Traces can be large (10KB-1MB per run). At scale, storage costs grow. → **Mitigation:** Compress traces before storage (gzip JSON). Set retention policies (e.g., delete traces older than 90 days, keep aggregate metrics). Provide a "trace summary" view that doesn't require loading the full trace.

**Risk: Batch evaluation performance**
Evaluating 1000 test cases with 5 LLM judges each = 5000 LLM API calls. At 1 call/second, this takes 83 minutes. → **Mitigation:** Parallel execution with rate limiting (Celery worker pool). Use cheaper models for simple judges (e.g., GPT-4o-mini instead of GPT-4o). Cache results to avoid re-evaluation. Provide progress estimates so users can plan.

**Risk: Custom evaluator complexity**
Users may write evaluators that are slow, buggy, or have side effects. → **Mitigation:** Provide a testing harness ("test this evaluator on 5 sample inputs"). Enforce timeouts per evaluator. Run custom evaluators in isolated processes to prevent crashes from affecting the system. Document best practices.

**Risk: Business value model oversimplification**
ROI calculation may not capture the full business impact of an agent (e.g., customer satisfaction, brand reputation). → **Mitigation:** Make the value formula configurable—users can encode their own business logic. Document that ROI is an estimate, not a ground truth. Provide sensitivity analysis ("how does ROI change if value_per_task varies by ±20%?").

**Trade-off: Flexibility vs. simplicity**
Supporting YAML config, Python code, and visual builder for evaluators adds complexity to the codebase. → **Acceptance:** This is a core requirement. Different users have different preferences. The visual builder is a nice-to-have for v1; YAML and Python are must-haves.

**Trade-off: Self-hosted vs. SaaS**
Self-hosted gives users control, but we lose the ability to push updates or monitor usage. → **Acceptance:** v1 is self-hosted. If demand emerges for a SaaS version, we can add multi-tenancy later (the design is Kubernetes-ready).

**Trade-off: DeepEval dependency**
DeepEval is a third-party dependency. If it's abandoned or becomes unusable, we're blocked. → **Acceptance:** DeepEval is open-source (MIT license) and actively maintained (Confident AI). We abstract it behind an internal interface, so switching to an alternative (e.g., Ragas, custom metrics) is a contained change.

## Migration Plan

Not applicable—this is a greenfield project. There is no existing system to migrate from.

**Deployment sequence:**
1. Set up repository structure (Python backend, React frontend, Docker Compose config)
2. Implement core evaluation engine with DeepEval integration
3. Build agent adapter interface and ship adapters for OpenAI and LangChain
4. Implement custom evaluator framework (validators first, then LLM judges, then executors)
5. Build batch evaluation system with Celery
6. Implement business value model and ROI calculation
7. Build web UI (dashboard → trace explorer → cost analyzer → eval config → historical analysis)
8. Add caching, error handling, and security hardening
9. Write documentation and deployment guides
10. Release v1

**Rollback strategy:** Not applicable for v1. For future versions, use database migrations (Alembic) with rollback scripts. Docker images are versioned, so rolling back means deploying the previous image.

## Open Questions

**Question 1: Multi-tenancy model**
If we build a SaaS version, how do we isolate tenant data? Schema-per-tenant (strong isolation, complex queries) vs. row-level security (simpler, requires careful policy enforcement)? → **Decision deferred** until SaaS demand is validated.

**Question 2: Evaluator marketplace**
Should users be able to share evaluators (e.g., a "helpfulness judge" template)? If so, how do we handle trust (malicious evaluators) and versioning? → **Decision deferred** to post-v1. Focus on getting evaluator creation right first.

**Question 3: Real-time production monitoring**
v1 is batch-only. If users want production monitoring (evaluate every agent call in real-time), do we extend the same system or build a separate service? → **Decision deferred.** The evaluation engine is reusable, but the ingestion pipeline (high-throughput, low-latency) is different. Likely a separate service that calls the same engine.

**Question 4: Pricing model for LLM judges**
Should we abstract LLM providers (OpenAI, Anthropic, local models) behind a unified interface, or hardcode OpenAI for v1? → **Decision:** Abstract from day 1. DeepEval already supports multiple LLM providers. We expose a `judge_model` config per evaluator.

**Question 5: Trace format**
Should we use a standard trace format (OpenTelemetry) or DeepEval's native format? → **Decision:** Use DeepEval's native format for fidelity (captures LLM-specific data). Provide an OTel exporter for users who want to integrate with existing observability tools.

**Question 6: Evaluation dataset format**
Should we support importing datasets from other tools (e.g., LangSmith, Arize Phoenix)? → **Decision:** Yes, but post-v1. v1 uses DeepEval's `Golden` format. We can add importers for other formats later.

**Question 7: Web UI framework**
We chose React + Vite. Should we use a component library (Material-UI, Ant Design, shadcn/ui) or build custom components? → **Decision:** Use shadcn/ui for basic components (buttons, inputs, tables, modals). It's unstyled by default, so we can brand it. Custom components for complex visualizations (trace tree, Gantt chart).

**Question 8: Authentication**
v1 is single-tenant. Do we need auth? → **Decision:** Yes, even for single-tenant. Basic auth (username/password) or API key. Multi-tenant auth (OAuth, SSO) is deferred to SaaS version.
