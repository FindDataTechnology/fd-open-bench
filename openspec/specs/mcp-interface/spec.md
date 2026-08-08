# mcp-interface Specification

## Purpose
TBD - created by archiving change add-mcp-cli-interface. Update Purpose after archive.
## Requirements
### Requirement: MCP server exposes domain tools

The system SHALL expose domain-level MCP tools that orchestrate calls to the existing REST API. The initial set SHALL include at least `run_evaluation`, `get_evaluation_status`, `analyze_weaknesses`, `compare_agents`, `find_best_performer`, and `export_report`. Each domain tool SHALL accept human-friendly identifiers (e.g., agent name, dataset name) where practical and resolve them to backend IDs internally. 对比类工具 SHALL 基于 benchmark 语义:`compare_agents` 必须指定 benchmark(名称或 ID),返回 leaderboard 完整对比(技术统计 + 商业指标);SHALL 新增 `run_benchmark` 与 `get_leaderboard` 工具;`export_report` SHALL 输出商业结论段(推荐 agent、每成功任务成本、ROI、人工替代率、数据缺口提示)。

#### Scenario: Start an evaluation by name

- **WHEN** a client calls `run_evaluation` with an agent name and a dataset name
- **THEN** the server resolves both names to IDs via the backend, creates an evaluation run via `POST /api/v1/evaluations`, and returns the `run_id` with its initial status

#### Scenario: Poll evaluation status

- **WHEN** a client calls `get_evaluation_status` with a `run_id`
- **THEN** the server returns the current status, progress, and results summary from `GET /api/v1/evaluations/{run_id}/status`

#### Scenario: 同基准对比

- **WHEN** 调用 compare_agents(agent_ids=[...], benchmark="goldens_v2")
- **THEN** 返回该 benchmark 下各 agent 的对比表,含 cost_per_success 与排序

#### Scenario: 跨基准对比被拒绝

- **WHEN** 调用方试图比较无共同 benchmark 的 agents
- **THEN** 工具返回明确错误,提示先对这些 agent 跑同一 benchmark

#### Scenario: 报告含商业结论

- **WHEN** 调用 export_report(run_id 或 batch_id)
- **THEN** 报告包含推荐结论段:推荐哪个 agent、理由(成本/ROI/替代率)、缺哪些数据

### Requirement: MCP server exposes a raw_api escape hatch

The system SHALL provide a single `raw_api` tool accepting `method`, `path`, `params`, and `body` that issues the corresponding call to the backend over `httpx` and returns the JSON response. The tool description SHALL mark it as unstable. Every `raw_api` call SHALL be logged with method, path, and params.

#### Scenario: Raw GET to an endpoint

- **WHEN** a client calls `raw_api` with `method=GET`, `path=/api/v1/evaluations`, `params={status: completed}`
- **THEN** the server issues `GET /api/v1/evaluations?status=completed` against the backend and returns the JSON body

#### Scenario: Raw calls are logged

- **WHEN** any `raw_api` call is made
- **THEN** an entry containing method, path, and params is appended to a log destination

### Requirement: MCP server supports stdio and HTTP transports

The system SHALL serve the same tools over both stdio (default) and streamable HTTP, from one FastMCP server definition, so the CLI, Claude Desktop, and a future web client share identical tools.

#### Scenario: Default stdio transport

- **WHEN** the server is started with no transport flag
- **THEN** it communicates over stdio

#### Scenario: Optional HTTP transport

- **WHEN** the server is started with an HTTP flag
- **THEN** it serves tools over streamable HTTP at a configurable port

### Requirement: MCP server is stateless

The system SHALL hold no per-conversation state. Each tool call SHALL be a pure function of its arguments and the backend's current state.

#### Scenario: Repeatable across sessions

- **WHEN** two separate CLI invocations call `get_evaluation_status` with the same `run_id`
- **THEN** both return the backend's current state without relying on any prior conversation context

### Requirement: fd-bench CLI one-shot mode

The system SHALL provide a one-shot CLI mode that invokes exactly one domain tool from CLI arguments and prints its result, with no LLM call. CLI SHALL 提供 `run-benchmark`(benchmark + agents)、`leaderboard <benchmark>` 命令;`run-eval`/`report` 输出与 benchmark 语义对齐;`raw` 逃生舱保留。

#### Scenario: One-shot evaluation start

- **WHEN** the user runs `fd-bench run-eval --agent X --dataset Y`
- **THEN** the CLI calls the `run_evaluation` tool directly and prints the `run_id` and status

#### Scenario: Help lists subcommands

- **WHEN** the user runs `fd-bench --help`
- **THEN** the available one-shot subcommands are listed

#### Scenario: CLI 跑基准

- **WHEN** 用户执行 `fd-bench run-benchmark --benchmark goldens_v2 --agents paybot,helper`
- **THEN** 创建批量评测并输出 batch_id

#### Scenario: CLI 看榜

- **WHEN** 用户执行 `fd-bench leaderboard goldens_v2`
- **THEN** 输出对比表(文本格式,含商业列)

### Requirement: fd-bench CLI chat mode

The system SHALL provide a chat REPL that sends user input to the Anthropic API with the MCP tools available as callable functions, executes any returned tool calls against the spawned MCP server, and prints tool results and assistant text.

#### Scenario: Natural-language request

- **WHEN** the user runs `fd-bench chat` and types a natural-language request
- **THEN** the CLI sends it to the Anthropic API with tool definitions, executes returned tool calls, and prints the final assistant response

#### Scenario: Missing API key fails fast

- **WHEN** `ANTHROPIC_API_KEY` is unset and the user runs `fd-bench chat`
- **THEN** the CLI exits with a clear error message before starting the REPL

### Requirement: fd-bench CLI spawns the MCP server as a subprocess

The system SHALL launch the MCP server as a stdio subprocess from both CLI modes using a single shared entrypoint (`fd-bench mcp serve`), so Claude Desktop can reuse the same binary.

#### Scenario: Subprocess lifecycle

- **WHEN** the CLI starts in one-shot or chat mode
- **THEN** it spawns `fd-bench mcp serve` as a subprocess and communicates over stdio

#### Scenario: Claude Desktop reuse

- **WHEN** a user configures Claude Desktop to run `fd-bench mcp serve`
- **THEN** the domain tools and `raw_api` are available in Claude Desktop with no separately-managed server process

### Requirement: Backend base URL configuration

The system SHALL read the backend base URL from an `FD_BENCH_API_URL` environment variable, defaulting to `http://localhost:8000`, used by both the MCP server's `httpx` calls and the CLI.

#### Scenario: Default URL

- **WHEN** `FD_BENCH_API_URL` is unset
- **THEN** the server and CLI target `http://localhost:8000`

#### Scenario: Override URL

- **WHEN** `FD_BENCH_API_URL` is set
- **THEN** all backend calls target that URL
