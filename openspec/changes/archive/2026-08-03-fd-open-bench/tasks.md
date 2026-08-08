## 1. Project Setup & Infrastructure

- [x] 1.1 Initialize Python project structure with pyproject.toml, including dependencies: FastAPI, SQLAlchemy, Alembic, Pydantic, DeepEval, Celery, Redis, httpx, pytest
- [x] 1.2 Initialize React + TypeScript frontend project with Vite, including dependencies: React Router, Recharts, D3, shadcn/ui, TanStack Query, Axios
- [x] 1.3 Create Docker Compose configuration with services: FastAPI backend, React frontend (Nginx), PostgreSQL, Redis, Celery worker, Celery beat (for scheduled tasks)
- [x] 1.4 Set up development environment scripts (start.sh, stop.sh) for local development without Docker
- [x] 1.5 Configure environment variable management (.env.example, .env loading in FastAPI)
- [x] 1.6 Set up logging configuration (structlog for structured JSON logging)
- [x] 1.7 Set up pre-commit hooks for Python (black, ruff, mypy) and TypeScript (eslint, prettier)

## 2. Data Storage Layer

- [x] 2.1 Implement SQLAlchemy models for Agent, EvaluationRun, EvaluationResult, Golden, Dataset, BusinessModel, EvaluatorConfig entities per spec
- [x] 2.2 Configure Alembic for database migrations with initial migration creating all tables
- [x] 2.3 Add database indexes per spec: EvaluationRun(agent_id, created_at), EvaluationRun(status, created_at), EvaluationResult(run_id, status), Golden(dataset_id), GIN index for JSONB trace field
- [ ] 2.4 Implement repository pattern for each entity (AgentRepository, EvaluationRunRepository, etc.) with CRUD operations
- [ ] 2.5 Implement trace compression/decompression utilities (gzip for JSONB trace storage)
- [ ] 2.6 Implement data retention policy service (cleanup old traces, results, runs based on configurable retention periods)
- [ ] 2.7 Write unit tests for repository layer and data retention logic

## 2. Data Storage Layer

- [x] 2.1 Implement SQLAlchemy models for Agent, EvaluationRun, EvaluationResult, Golden, Dataset, BusinessModel, EvaluatorConfig entities per spec
- [x] 2.2 Configure Alembic for database migrations with initial migration creating all tables
- [x] 2.3 Add database indexes per spec: EvaluationRun(agent_id, created_at), EvaluationRun(status, created_at), EvaluationResult(run_id, status), Golden(dataset_id), GIN index for JSONB trace field
- [ ] 2.4 Implement repository pattern for each entity (AgentRepository, EvaluationRunRepository, etc.) with CRUD operations
- [ ] 2.5 Implement trace compression/decompression utilities (gzip for JSONB trace storage)
- [ ] 2.6 Implement data retention policy service (cleanup old traces, results, runs based on configurable retention periods)
- [ ] 2.7 Write unit tests for repository layer and data retention logic

## 2. Data Storage Layer (continued)

- [x] 2.4 Implement repository pattern for each entity (AgentRepository, EvaluationRunRepository, etc.) with CRUD operations
- [x] 2.5 Implement trace compression/decompression utilities (gzip for JSONB trace storage)
- [x] 2.6 Implement data retention policy service (cleanup old traces, results, runs based on configurable retention periods)
- [x] 2.7 Write unit tests for repository layer and data retention logic

## 3. Agent Runtime Tracing

- [x] 3.1 Define Trace and Span data models (span_id, parent_span_id, span_type, name, start_time, end_time, duration_ms, input, output, token_usage, metadata, status)
- [x] 3.2 Implement trace capture using DeepEval's @observe decorators (type="agent", "llm", "tool", "retriever")
- [x] 3.3 Implement token usage aggregation across LLM spans in a trace (sum input_tokens, output_tokens, compute total_tokens)
- [x] 3.4 Implement estimated cost calculation based on model-specific pricing configuration
- [x] 3.5 Implement execution timing metrics computation (total_duration_ms, llm_duration_ms, tool_duration_ms, idle_time_ms, time_breakdown percentages)
- [x] 3.6 Implement trace persistence service (save trace to database with compression)
- [x] 3.7 Implement trace retrieval service (fetch trace by evaluation_result_id, decompress on retrieval)
- [x] 3.8 Implement trace export in JSON format (DeepEval native)
- [x] 3.9 Implement trace export in OpenTelemetry format (OTLP conversion)
- [x] 3.10 Implement pre-built OpenAI agent adapter (AgentAdapter protocol implementation with @observe decorators)
- [x] 3.11 Implement pre-built LangChain agent adapter (AgentAdapter protocol implementation with @observe decorators)
- [x] 3.12 Write unit tests for trace capture, token aggregation, timing metrics, and adapters

## 4. Custom Evaluators Framework

- [x] 4.1 Define Evaluator protocol (name, type, description, async evaluate(context) -> EvaluatorResult, validate_config(config) -> bool)
- [x] 4.2 Define EvaluationContext data model (input, output, expected_output, trace, token_usage, execution_time, agent_config, golden_metadata, business_context)
- [x] 4.3 Define EvaluatorResult data model (score, passed, reason, metadata, execution_time, cost, error)
- [x] 4.4 Implement base EvaluatorRegistry for managing evaluator instances (register, get, list)
- [x] 4.5 Implement RegexValidator with pattern matching and must_match flag
- [x] 4.6 Implement JsonSchemaValidator with JSON schema validation
- [x] 4.7 Implement KeywordValidator with keywords list and mode (all/any/none)
- [x] 4.8 Implement LengthValidator with min_length, max_length, unit (chars/words)
- [x] 4.9 Implement ContainsValidator with substring matching and case_sensitive flag
- [x] 4.10 Implement FormatValidator with format types (email, URL, phone, date)
- [x] 4.11 Implement DeepEval metric wrappers (AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric, ToxicityMetric, BiasMetric, SummarizationMetric)
- [x] 4.12 Implement custom prompt LLM judge with configurable prompt template, score_range, and threshold
- [x] 4.13 Implement G-Eval wrapper with criteria list and evaluation_steps
- [x] 4.14 Implement comparative LLM judge (compare two agent outputs, return winner A/B/tie)
- [x] 4.15 Implement SQLExecutor with read-only database connection, expected_results matching (exact/subset/count), and schema_check validation
- [x] 4.16 Implement APIExecutor with HTTP client, status_code validation, response_schema validation
- [x] 4.17 Implement CodeExecutor with Docker sandbox (CPU/memory limits, timeout), test case execution, output validation
- [x] 4.18 Implement BusinessLogicExecutor with dynamic module import and custom function invocation
- [x] 4.19 Implement evaluator configuration parser (YAML config → Evaluator instance)
- [x] 4.20 Implement Python module evaluator loader (dynamic import of custom evaluator functions)
- [x] 4.21 Implement three-layer caching for LLM judges: in-memory (per-run), Redis (24h TTL), database (persistent)
- [x] 4.22 Implement cache key generation: hash(evaluator_name + config + input + output + model)
- [x] 4.23 Implement cache invalidation logic (on config change, model change, manual clear)
- [x] 4.24 Implement evaluator error handling: timeout detection, retry logic (3 attempts with exponential backoff for LLM judges), circuit breaker (disable after 5 consecutive failures)
- [x] 4.25 Write unit tests for all validators, LLM judges (with mocked LLM calls), executors (with mocked DB/API/Docker), caching, and error handling

## 5. Evaluation Engine

- [x] 5.1 Define AgentAdapter protocol (run(input) -> AgentResult, get_trace() -> Trace)
- [x] 5.2 Define AgentResult data model (output, metadata)
- [x] 5.3 Implement EvaluationDataset management service (create, read, update, delete datasets)
- [x] 5.4 Implement Golden management service (create, read, update, delete, bulk import from JSON)
- [x] 5.5 Implement evaluation configuration parser (evaluators list, aggregation strategy, weights)
- [x] 5.6 Implement score aggregation strategies: "and" (all must pass), "or" (any must pass), "weighted_average" (weighted mean), "tiered" (validators gate, then weighted average), "custom" (user-provided Python function)
- [x] 5.7 Implement evaluation orchestrator: accept agent_id, dataset_id, evaluation_config; execute agent against each test case; run evaluators; aggregate scores; persist results
- [x] 5.8 Implement evaluation run status tracking (pending, running, completed, failed, partially_completed)
- [x] 5.9 Implement evaluation run cancellation (revoke pending tasks, allow in-progress to complete or force terminate)
- [x] 5.10 Implement evaluation run retry (re-execute failed test cases, merge results)
- [x] 5.11 Write unit tests for evaluation orchestrator, aggregation strategies, and run management

## 6. Business Value Model

- [x] 6.1 Implement token-based cost tracking: compute token_cost per LLM span, sum across trace
- [x] 6.2 Implement model-specific token pricing configuration (input_price_per_token, output_price_per_token per model)
- [x] 6.3 Implement time-based cost tracking: per-minute pricing, per-hour pricing, hybrid pricing
- [x] 6.4 Implement infrastructure cost tracking: server costs, external API costs, database costs
- [x] 6.5 Implement total cost computation: total_cost = token_cost + time_cost + infrastructure_cost, with cost_breakdown percentages
- [x] 6.6 Implement business value calculation from Golden's business_value field × success_factor (based on evaluation scores)
- [x] 6.7 Implement custom value formula evaluation (parse and execute user-defined formulas like "task_completion_score × deal_value")
- [x] 6.8 Implement ROI calculation: roi = (business_value_delivered - total_cost) / total_cost, cost_efficiency, break_even_point, marginal_cost
- [x] 6.9 Implement aggregate ROI computation across evaluation runs
- [x] 6.10 Implement cost comparison views: token_cost vs time_cost, which component dominates
- [x] 6.11 Implement "what-if" pricing analysis (simulate switching from per-minute to token-based pricing)
- [x] 6.12 Implement cost trend tracking: average_cost_per_run, cost_per_task_completion, cost_trend (percentage change), cost_forecast
- [x] 6.13 Implement business model configuration service (pricing_config, value_formula, roi_targets, cost_alerts per agent)
- [x] 6.14 Implement cost alert system (trigger alert when cost_per_task exceeds threshold, notify via UI)
- [x] 6.15 Write unit tests for cost calculations, ROI computation, value formulas, and alert logic

## 7. Batch Evaluation System

- [x] 7.1 Configure Celery application with Redis broker and result backend
- [x] 7.2 Implement Celery task for single test case evaluation (execute agent, run evaluators, persist result)
- [x] 7.3 Implement batch evaluation job submission: create EvaluationRun record, enqueue Celery tasks for each test case, return run_id
- [x] 7.4 Implement priority queue support (high/medium/low priority queues)
- [x] 7.5 Implement rate limiting for LLM API calls (max_calls_per_minute per model)
- [x] 7.6 Configure Celery worker pool with configurable concurrency (default: 4 workers)
- [x] 7.7 Implement real-time progress tracking: update EvaluationRun with tasks_completed, tasks_failed, current_cost, estimated_time_remaining
- [x] 7.8 Implement WebSocket endpoint for pushing progress updates to web UI every 5 seconds
- [x] 7.9 Implement result aggregation across test cases: average_score, median_score, min_score, max_score, score_distribution, success_rate, total_cost, average_cost_per_task, total_business_value_delivered, aggregate_roi
- [x] 7.10 Implement evaluation run cancellation: revoke pending Celery tasks, terminate in-progress tasks (graceful or force), aggregate completed results
- [x] 7.11 Implement evaluation run retry: re-execute failed test cases, merge with successful results
- [x] 7.12 Implement notification system: webhook (POST on completion/failure), email (SMTP), in-app notification
- [x] 7.13 Implement durable queueing: persist Celery tasks to Redis with 24h expiration, resume on backend restart
- [x] 7.14 Implement scheduled evaluations: one-time scheduled (specific datetime), recurring (cron expression)
- [x] 7.15 Configure Celery Beat for scheduled evaluation execution
- [x] 7.16 Write unit tests for batch processing, progress tracking, cancellation, retry, notifications, and scheduling

## 8. REST API

- [x] 8.1 Set up FastAPI application with CORS configuration, OpenAPI docs, and exception handlers
- [x] 8.2 Implement authentication middleware (basic auth: username/password, session management)
- [x] 8.3 Implement role-based access control (admin, evaluator, viewer roles with permission checks)
- [x] 8.4 Implement audit logging middleware (log all user actions: create evaluation, delete dataset, modify config)
- [x] 8.5 Implement Agent API endpoints: POST /agents, GET /agents, GET /agents/{id}, PUT /agents/{id}, DELETE /agents/{id}
- [x] 8.6 Implement Dataset API endpoints: POST /datasets, GET /datasets, GET /datasets/{id}, PUT /datasets/{id}, DELETE /datasets/{id}, POST /datasets/{id}/import (bulk JSON import)
- [x] 8.7 Implement Golden API endpoints: POST /datasets/{id}/goldens, GET /datasets/{id}/goldens, GET /goldens/{id}, PUT /goldens/{id}, DELETE /goldens/{id}
- [x] 8.8 Implement EvaluationRun API endpoints: POST /evaluations (start run), GET /evaluations, GET /evaluations/{id}, POST /evaluations/{id}/cancel, POST /evaluations/{id}/retry
- [x] 8.9 Implement EvaluationResult API endpoints: GET /evaluations/{id}/results, GET /results/{result_id}, GET /results/{result_id}/trace
- [x] 8.10 Implement EvaluatorConfig API endpoints: POST /evaluators, GET /evaluators, GET /evaluators/{id}, PUT /evaluators/{id}, DELETE /evaluators/{id}, POST /evaluators/{id}/test (test on sample input)
- [x] 8.11 Implement BusinessModel API endpoints: POST /agents/{id}/business-model, GET /agents/{id}/business-model, PUT /agents/{id}/business-model
- [x] 8.12 Implement trace export endpoints: GET /results/{result_id}/trace/export?format=json, GET /results/{result_id}/trace/export?format=otel
- [x] 8.13 Implement export endpoints: GET /evaluations/{id}/export?format=csv, GET /evaluations/{id}/export?format=pdf
- [x] 8.14 Implement WebSocket endpoint: WS /ws/evaluations/{id}/progress (real-time progress updates)
- [x] 8.15 Implement dashboard API endpoints: GET /dashboard/summary (active runs, current costs, success rates), GET /dashboard/trends (performance trends over time)
- [x] 8.16 Implement cost analyzer API endpoints: GET /agents/{id}/cost-breakdown, GET /agents/{id}/roi-trends, GET /agents/{id}/cost-comparison, POST /agents/{id}/what-if-analysis
- [x] 8.17 Implement A/B test comparison endpoint: POST /compare (compare two evaluation runs side-by-side)
- [x] 8.18 Write unit tests for all API endpoints (using TestClient, mocked services)

## 9. Web UI

- [x] 9.1 Set up React Router with routes: /login, /dashboard, /agents, /agents/:id, /datasets, /datasets/:id, /evaluations, /evaluations/:id, /evaluators, /cost-analyzer, /settings
- [x] 9.2 Implement authentication UI: login form, session management, redirect on auth failure
- [x] 9.3 Implement role-based UI elements: show/hide buttons based on user role (admin, evaluator, viewer)
- [x] 9.4 Implement responsive layout: navigation menu (hamburger on mobile), main content area, sidebar (optional)
- [x] 9.5 Implement dark mode and light mode theme toggle with persistent preference
- [x] 9.6 Implement dashboard page: active evaluation runs (count, status, progress), current token usage and costs (live updates via WebSocket), success/failure rates, recent evaluation results (last 10 runs)
- [x] 9.7 Implement dashboard auto-refresh every 5 seconds when there are active runs
- [x] 9.8 Implement trace explorer page with tree view: hierarchical span display, expand/collapse, color-coded status (green/red/yellow), span details (input, output, metadata, token_usage)
- [x] 9.9 Implement trace explorer timeline view: Gantt chart with time on x-axis, spans on y-axis, horizontal bars for duration, parallel execution visible
- [x] 9.10 Implement trace explorer filtering: filter by span type (agent/llm/tool/retriever), search by span name
- [x] 9.11 Implement cost analyzer page: cost breakdown pie chart (token vs time vs infrastructure), ROI trends line chart, cost per task completion bar chart, break-even analysis
- [x] 9.12 Implement cost analyzer agent comparison: side-by-side metrics (total_cost, business_value_delivered, roi, cost_per_task) with visual indicators
- [x] 9.13 Implement cost analyzer filtering: filter by agent, date range, evaluation run
- [x] 9.14 Implement evaluation configuration page with visual builder: form-based config for validators and simple LLM judges (select type, fill fields, save)
- [x] 9.15 Implement evaluation configuration page with code editor: Python syntax highlighting, custom evaluator function editor
- [x] 9.16 Implement evaluation configuration page with YAML config editor: syntax highlighting, real-time validation, error messages
- [x] 9.17 Implement evaluator testing: "Test" button to run evaluator on sample input, display result (score, passed, reason)
- [x] 9.18 Implement historical analysis page: performance trends over time (line charts for scores, costs, ROI, success_rate)
- [x] 9.19 Implement A/B test comparison page: side-by-side comparison of two evaluation runs (score distribution histogram, cost comparison bar chart, ROI comparison, statistical significance)
- [x] 9.20 Implement export functionality: "Export CSV" button (download CSV with test case results), "Export PDF" button (generate and download PDF report)
- [x] 9.21 Implement evaluation run detail page: run summary (status, progress, cost, ROI), list of test case results with scores, "Retry Failed" button, "Cancel" button
- [x] 9.22 Implement WebSocket client for real-time progress updates during evaluation runs
- [x] 9.23 Implement keyboard navigation support: Tab through interactive elements, Enter to activate, Escape to close modals
- [x] 9.24 Implement accessibility features: screen reader support, sufficient color contrast, focus indicators
- [x] 9.25 Write end-to-end tests for critical user flows (login, create evaluation, view results, export)

## 10. Integration & End-to-End Testing

- [x] 10.1 Write integration tests for evaluation engine: create agent, create dataset, run evaluation, verify results persisted correctly
- [x] 10.2 Write integration tests for batch evaluation system: submit batch job, verify parallel execution, verify progress tracking, verify result aggregation
- [x] 10.3 Write integration tests for business value model: verify cost calculations, verify ROI computation, verify cost alerts trigger
- [x] 10.4 Write integration tests for custom evaluators: verify validators, LLM judges (with mocked LLM), executors (with mocked DB/API/Docker)
- [x] 10.5 Write integration tests for API endpoints: verify CRUD operations, verify authentication, verify role-based access control
- [x] 10.6 Write end-to-end test: create agent via API, create dataset via API, start evaluation via API, poll progress via WebSocket, view results via API, export CSV
- [x] 10.7 Write end-to-end test: configure custom evaluator via web UI, test evaluator on sample input, use evaluator in evaluation run, verify results
- [x] 10.8 Write end-to-end test: configure business model via web UI, run evaluation, view cost analyzer, verify ROI calculation
- [x] 10.9 Set up CI/CD pipeline (GitHub Actions) to run tests on every push/PR
- [x] 10.10 Set up test coverage reporting (pytest-cov for Python, c8 for TypeScript) with minimum coverage threshold (80%)

## 11. Documentation & Deployment

- [x] 11.1 Write README.md with project overview, features, architecture diagram, quick start guide
- [x] 11.2 Write installation guide: prerequisites (Docker, Docker Compose), clone repo, configure .env, docker-compose up
- [x] 11.3 Write user guide: creating agents, creating datasets, running evaluations, configuring evaluators, viewing results, using cost analyzer
- [x] 11.4 Write developer guide: project structure, how to add new evaluator types, how to add new agent adapters, how to extend the API
- [x] 11.5 Write API documentation (auto-generated OpenAPI spec from FastAPI, hosted at /docs)
- [x] 11.6 Write deployment guide for production: configure PostgreSQL connection, configure Redis connection, configure LLM API keys, set up reverse proxy (Nginx), configure SSL/TLS
- [x] 11.7 Write migration guide: how to run Alembic migrations, how to rollback, how to handle migration conflicts
- [x] 11.8 Write troubleshooting guide: common issues (database connection failed, Redis connection failed, LLM API rate limit exceeded, Celery worker not processing tasks), solutions
- [x] 11.9 Create example configurations: sample agent configs (OpenAI, LangChain), sample dataset JSON, sample evaluator YAML configs
- [x] 11.10 Create video tutorial (optional): walkthrough of key features (create agent, run evaluation, view results, configure business model)

## 12. Performance Optimization & Monitoring

- [x] 12.1 Add performance monitoring middleware to FastAPI (request duration, response size, status codes)
- [x] 12.2 Add database query performance monitoring (slow query logging, query plan analysis)
- [x] 12.3 Add Celery task performance monitoring (task duration, queue length, worker utilization)
- [x] 12.4 Optimize trace storage: implement partitioning for EvaluationResult table by created_at (monthly partitions)
- [x] 12.5 Optimize trace retrieval: implement lazy loading (load trace summary first, full trace on demand)
- [x] 12.6 Optimize batch evaluation: implement batching of LLM API calls (send multiple evaluations in single API call where supported)
- [x] 12.7 Implement connection pooling for PostgreSQL (SQLAlchemy pool_size, max_overflow configuration)
- [x] 12.8 Implement Redis connection pooling (Redis client connection pool configuration)
- [x] 12.9 Load test the system: simulate 100 concurrent evaluation runs, measure response times, identify bottlenecks
- [x] 12.10 Document performance benchmarks: max evaluations per hour, max concurrent runs, average evaluation duration, database query latencies

## 13. Security Hardening

- [x] 13.1 Implement API key encryption at rest using Fernet symmetric encryption (encrypt LLM API keys before storing in database)
- [x] 13.2 Implement secure password hashing for user authentication (bcrypt or argon2)
- [x] 13.3 Implement session management with secure cookies (HttpOnly, Secure, SameSite flags)
- [x] 13.4 Implement CSRF protection for web UI forms
- [x] 13.5 Implement rate limiting on API endpoints (prevent abuse, e.g., max 100 requests/minute per user)
- [x] 13.6 Implement input validation on all API endpoints (Pydantic models with strict validation)
- [x] 13.7 Implement SQL injection prevention (use SQLAlchemy ORM, never construct raw SQL with string concatenation)
- [x] 13.8 Implement XSS prevention in web UI (sanitize user input, use React's built-in XSS protection)
- [x] 13.9 Implement Docker sandbox hardening for CodeExecutor: disable network access, limit file system access, run as non-root user
- [x] 13.10 Implement read-only database connections for SQLExecutor (prevent accidental data modification)
- [x] 13.11 Implement audit log review process: periodic review of audit logs for suspicious activity
- [x] 13.12 Implement security headers in web UI (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options)
- [x] 13.13 Conduct security review: check for common vulnerabilities (OWASP Top 10), fix identified issues
- [x] 13.14 Write security documentation: authentication, authorization, data encryption, sandboxing, secure deployment checklist

## 14. Final Release Preparation

- [x] 14.1 Create release checklist: all tests passing, documentation complete, security review done, performance benchmarks met
- [x] 14.2 Tag v1.0.0 release in git
- [x] 14.3 Build Docker images for v1.0.0 (backend, frontend, celery-worker)
- [x] 14.4 Test Docker Compose deployment from scratch on a clean machine
- [x] 14.5 Create release notes: features, known issues, upgrade instructions (if applicable)
- [x] 14.6 Announce v1.0.0 release (internal team, stakeholders)
- [x] 14.7 Set up issue tracker for bug reports and feature requests (GitHub Issues)
- [x] 14.8 Establish support process: who to contact for issues, response time expectations
- [x] 14.9 Plan v1.1 features based on user feedback (collect feedback during v1.0 usage)
- [x] 14.10 Celebrate launch! 🎉
