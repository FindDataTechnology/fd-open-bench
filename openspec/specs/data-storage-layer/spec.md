# data-storage-layer Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: System provides Agent entity with configuration
The system SHALL provide an Agent entity in the database with fields: id (UUID, primary key), name (string, unique), description (text), version (string), adapter_type (enum: openai, langchain, custom), config (JSONB: model, tools, system prompt, adapter-specific settings), pricing_config (JSONB: token pricing, time pricing), created_at (timestamp), updated_at (timestamp). The system SHALL support creating, reading, updating, and deleting agents.

#### Scenario: Create agent
- **WHEN** a user creates an agent with name="travel-agent", adapter_type="openai", config={model: "gpt-4o", tools: [...]}
- **THEN** the system SHALL persist the agent and return an agent_id

#### Scenario: Update agent configuration
- **WHEN** a user updates an agent's config (e.g., change model from gpt-4o to gpt-4o-mini)
- **THEN** the system SHALL update the config field and set updated_at to current timestamp

### Requirement: System provides EvaluationRun entity with status tracking
The system SHALL provide an EvaluationRun entity with fields: id (UUID, primary key), agent_id (foreign key to Agent), dataset_id (foreign key to Dataset), evaluation_config (JSONB: evaluators, aggregation strategy), status (enum: pending, running, completed, failed, cancelled, partially_completed), started_at (timestamp), completed_at (timestamp), tasks_total (integer), tasks_completed (integer), tasks_failed (integer), current_cost (decimal), results_summary (JSONB: aggregate metrics), created_at (timestamp). EvaluationRun SHALL 增加 `benchmark_id`(可空 FK)与 `batch_id`(可空,建索引)。旧 run 两列为空,不进入任何 leaderboard。The system SHALL support querying runs by agent_id, status, and date range.

#### Scenario: Create evaluation run
- **WHEN** a user initiates an evaluation run for agent_id="abc123" with dataset_id="def456"
- **THEN** the system SHALL create an EvaluationRun record with status="pending", tasks_total=100 (from dataset), and return a run_id

#### Scenario: Query runs by agent
- **WHEN** a user requests all evaluation runs for agent_id="abc123"
- **THEN** the system SHALL return all runs for that agent, ordered by created_at descending

#### Scenario: 批量 run 分组
- **WHEN** 批量接口创建 3 个 run
- **THEN** 三者共享 batch_id 且 benchmark_id 相同,可按 batch_id 一次查出

### Requirement: System provides EvaluationResult entity with trace storage
The system SHALL provide an EvaluationResult entity with fields: id (UUID, primary key), run_id (foreign key to EvaluationRun), golden_id (foreign key to Golden), agent_output (text), trace (JSONB, compressed), token_usage (JSONB: input_tokens, output_tokens, total_tokens, estimated_cost), execution_time_ms (integer), metric_scores (JSONB: {metric_name: score}), validator_results (JSONB: {validator_name: {passed, reason}}), business_value_delivered (decimal), total_cost (decimal), status (enum: success, failed, timeout, error), error_message (text, nullable), created_at (timestamp). The system SHALL support querying results by run_id and status.

#### Scenario: Persist evaluation result
- **WHEN** an evaluation task completes for a test case
- **THEN** the system SHALL persist an EvaluationResult with agent_output, trace (compressed), token_usage, metric_scores, validator_results, business_value_delivered, total_cost, and status

#### Scenario: Query results for a run
- **WHEN** a user requests all results for run_id="xyz789"
- **THEN** the system SHALL return all EvaluationResult records for that run, with traces decompressed on retrieval

### Requirement: System provides Golden (test case) entity
The system SHALL provide a Golden entity with fields: id (UUID, primary key), dataset_id (foreign key to Dataset), input (text), expected_output (text, nullable), expected_tools (JSONB array of ToolCall, nullable), business_value (Numeric, nullable), human_cost (Numeric, nullable), human_minutes (Integer, nullable), metadata (JSONB, nullable), created_at (timestamp). The system SHALL support bulk import of Goldens from JSON files. Migration SHALL backfill business_value from existing extra_metadata.business_value.

#### Scenario: Create Golden
- **WHEN** a user creates a Golden with input="Book a flight from NYC to Paris", expected_output="Booked flight XYZ", business_value=50.0
- **THEN** the system SHALL persist the Golden and return a golden_id

#### Scenario: Bulk import Goldens
- **WHEN** a user uploads a JSON file with 100 Goldens
- **THEN** the system SHALL parse the JSON, validate each Golden, create 100 Golden records, and return the count of successfully imported Goldens

#### Scenario: 商业字段落库
- **WHEN** 创建 golden 时提供 business_value=100、human_cost=30、human_minutes=15
- **THEN** 三者存储于独立列,可被商业计算与导入导出使用

### Requirement: System provides Dataset entity
The system SHALL provide a Dataset entity with fields: id (UUID, primary key), name (string), description (text), golden_count (integer, computed), created_at (timestamp), updated_at (timestamp). The system SHALL support creating, reading, updating, and deleting datasets. The system SHALL support associating multiple Goldens with a dataset.

#### Scenario: Create dataset
- **WHEN** a user creates a dataset with name="flight-booking-tests"
- **THEN** the system SHALL persist the dataset and return a dataset_id

#### Scenario: Compute golden_count
- **WHEN** a dataset has 100 associated Goldens
- **THEN** the system SHALL compute golden_count=100 and display it in dataset queries

### Requirement: System provides Benchmark entity
系统 SHALL 提供 Benchmark 实体表: id、name、description、dataset_id(FK)、metric_suite(JSON)、value_formula(Text)、time_value_rate(Float, 默认 0)、created_at、updated_at。

#### Scenario: Benchmark 持久化
- **WHEN** 创建 Benchmark
- **THEN** 全部字段持久化于 benchmarks 表,dataset 删除时 benchmark 级联删除或拒绝删除(取级联删除)

### Requirement: System provides BusinessModel entity
The system SHALL provide a BusinessModel entity with fields: id (UUID, primary key), agent_id (foreign key to Agent), pricing_config (JSONB: token pricing, time pricing, infrastructure pricing), value_formula (text, custom formula for calculating business value), roi_targets (JSONB: minimum_roi, target_roi), cost_alerts (JSONB: threshold, metric), created_at (timestamp), updated_at (timestamp). The system SHALL support one BusinessModel per agent.

#### Scenario: Create business model
- **WHEN** a user creates a business model for agent_id="abc123" with pricing_config={type: "hybrid", ...}, value_formula="task_completion_score × deal_value"
- **THEN** the system SHALL persist the business model and associate it with the agent

### Requirement: System provides EvaluatorConfig entity
The system SHALL provide an EvaluatorConfig entity with fields: id (UUID, primary key), name (string, unique), type (enum: validator, llm_judge, executor), config (JSONB: evaluator-specific configuration), created_at (timestamp), updated_at (timestamp). The system SHALL support creating, reading, updating, and deleting evaluator configurations. The system SHALL validate evaluator configs on creation.

#### Scenario: Create evaluator config
- **WHEN** a user creates an evaluator config with name="email_validator", type="validator", config={type: "regex", pattern: "\\S+@\\S+\\.\\S+"}
- **THEN** the system SHALL validate the config, persist it, and return an evaluator_config_id

### Requirement: System implements database indexing for query performance
The system SHALL implement database indexes to optimize query performance. Indexes SHALL include: EvaluationRun(agent_id, created_at), EvaluationRun(status, created_at), EvaluationResult(run_id, status), Golden(dataset_id), Trace(evaluation_result_id) using GIN index for JSONB. The system SHALL analyze query patterns and add indexes as needed.

#### Scenario: Query optimization for run listing
- **WHEN** a user queries evaluation runs by agent_id and date range
- **THEN** the system SHALL use the EvaluationRun(agent_id, created_at) index to execute the query in <100ms for 10,000 runs

### Requirement: System implements database migrations
The system SHALL implement database migrations using Alembic. Migrations SHALL be versioned and reversible. The system SHALL provide a migration script that creates all tables and indexes. The system SHALL support rolling back migrations in case of deployment failure. 系统 SHALL 通过 alembic 迁移完成本 change 的 schema 变更: benchmarks 建表、goldens 三列(含回填)、evaluation_runs 两列。默认数据库为 SQLite(WAL 模式)。

#### Scenario: Apply migrations
- **WHEN** the system is deployed for the first time
- **THEN** the system SHALL run Alembic migrations to create all tables (Agent, EvaluationRun, EvaluationResult, Golden, Dataset, BusinessModel, EvaluatorConfig) and indexes

#### Scenario: Rollback migration
- **WHEN** a deployment fails and the user needs to rollback
- **THEN** the system SHALL run Alembic downgrade to revert the last migration

#### Scenario: 迁移可前滚可回滚
- **WHEN** 执行 `alembic upgrade head` 后 `alembic downgrade -1`
- **THEN** schema 变更与回填均正确应用与撤销

### Requirement: System implements data retention policies
The system SHALL implement data retention policies to manage storage growth. The system SHALL support configurable retention periods: traces (default: 90 days), evaluation results (default: 1 year), evaluation runs (default: 2 years). On retention expiry, the system SHALL delete or archive old data. The system SHALL support manual cleanup via the web UI.

#### Scenario: Automatic trace cleanup
- **WHEN** a trace is older than 90 days (configurable retention period)
- **THEN** the system SHALL delete the trace from the database, but keep the EvaluationResult record with aggregated metrics

#### Scenario: Manual cleanup
- **WHEN** a user clicks "Cleanup Old Data" in the web UI
- **THEN** the system SHALL delete all data older than the configured retention periods and report the amount of storage freed

