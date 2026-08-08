# evaluation-engine Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: Evaluation engine orchestrates agent evaluation runs
The system SHALL provide an evaluation engine that orchestrates the execution of agent evaluations against test datasets. The engine SHALL accept an agent identifier, an evaluation dataset (collection of Goldens), and an evaluation configuration (set of evaluators and aggregation strategy). The engine SHALL execute the agent against each test case, collect outputs and traces, run configured evaluators, aggregate scores, and persist results. 评测引擎 SHALL 支持批量运行语义:一次批量操作针对同一 Benchmark 为多个 agent 各创建一个 run(携带相同 batch_id 与 benchmark_id),在进程内以后台任务并发执行(默认并发度 2)。评测执行 SHALL NOT 依赖 Celery/Redis。

#### Scenario: Successful batch evaluation run
- **WHEN** a user initiates an evaluation run with agent_id="travel-agent", dataset_id="flight-booking-tests", and evaluators=[task_completion, step_efficiency, regex_validator]
- **THEN** the system SHALL execute the travel-agent against each test case in the dataset, run all three evaluators on each output, aggregate scores per the configured strategy, and persist an EvaluationRun record with status="completed" and results_summary containing aggregate metrics

#### Scenario: Evaluation run with agent failure
- **WHEN** an agent raises an exception during execution for a specific test case
- **THEN** the system SHALL mark that test case result as status="failed", record the error message, continue execution for remaining test cases, and include the failure in the final results_summary

#### Scenario: Evaluation run with evaluator timeout
- **WHEN** an evaluator exceeds its configured timeout (default: 30 seconds for validators, 60 seconds for LLM judges, 120 seconds for executors)
- **THEN** the system SHALL mark that evaluator result as status="timeout", record the timeout duration, exclude that evaluator from score aggregation for that test case, and continue with remaining evaluators

#### Scenario: 批量执行
- **WHEN** 用户发起 3 agents × 1 benchmark 的批量评测
- **THEN** 系统创建 3 个共享 batch_id 的 run,后台并发执行,各自状态机独立(pending->running->completed/failed)

#### Scenario: 无外部队列依赖
- **WHEN** 仅启动单个 FastAPI 进程(无 Redis、无 Celery worker)
- **THEN** 批量评测完整执行完毕,结果落库

### Requirement: Evaluation engine integrates DeepEval metrics
The system SHALL integrate DeepEval's agent evaluation metrics as first-class evaluators. The system SHALL support end-to-end metrics (TaskCompletionMetric, StepEfficiencyMetric, PlanQualityMetric, PlanAdherenceMetric) that analyze the full agent trace. The system SHALL support component-level metrics (ToolCorrectnessMetric, ArgumentCorrectnessMetric) that analyze specific components within the trace.

#### Scenario: End-to-end metric evaluation
- **WHEN** an evaluation run is configured with TaskCompletionMetric
- **THEN** the system SHALL pass the full agent trace to DeepEval's TaskCompletionMetric, receive a score between 0.0 and 1.0, and persist the score with the evaluation result

#### Scenario: Component-level metric evaluation
- **WHEN** an evaluation run is configured with ToolCorrectnessMetric and the agent trace includes tool call spans
- **THEN** the system SHALL extract tool call information from the trace, pass it to DeepEval's ToolCorrectnessMetric along with expected_tools from the Golden, and persist the score

### Requirement: Evaluation engine supports configurable aggregation strategies
The system SHALL support multiple score aggregation strategies: "and" (all evaluators must pass), "or" (any evaluator must pass), "weighted_average" (weighted mean of scores), "tiered" (validators gate, then weighted average of judges and executors), and "custom" (user-provided Python function). The aggregation strategy SHALL be configurable per evaluation run.

#### Scenario: Tiered aggregation strategy
- **WHEN** an evaluation run uses aggregation strategy "tiered" with validators=[regex, json_schema] and llm_judges=[helpfulness, accuracy] with weights {helpfulness: 0.6, accuracy: 0.4}
- **THEN** the system SHALL first check if all validators passed; if any validator failed, the overall score SHALL be 0.0; if all validators passed, the system SHALL compute the weighted average of LLM judge scores

#### Scenario: Weighted average aggregation
- **WHEN** an evaluation run uses aggregation strategy "weighted_average" with evaluators=[eval_a (score=0.8, weight=0.5), eval_b (score=0.6, weight=0.3), eval_c (score=0.9, weight=0.2)]
- **THEN** the system SHALL compute overall_score = (0.8×0.5 + 0.6×0.3 + 0.9×0.2) / (0.5+0.3+0.2) = 0.76

### Requirement: Evaluation engine provides evaluation dataset management
The system SHALL support creating, reading, updating, and deleting evaluation datasets. A dataset SHALL contain a collection of Goldens (test cases). Each Golden SHALL have an input (string), optional expected_output (string), optional expected_tools (list of ToolCall), optional business_value (float), and optional metadata (dict). 评测引擎 SHALL 通过 Benchmark 实体关联 dataset 与指标套件;run 记录 benchmark_id,使结果可归入对应基准的对比。

#### Scenario: Create evaluation dataset
- **WHEN** a user creates a dataset with name="flight-booking-tests" and goldens=[{input: "Book NYC to Paris", expected_output: "Booked flight XYZ", expected_tools: [search_flights, book_flight], business_value: 50.0}]
- **THEN** the system SHALL persist the dataset and return a dataset_id

#### Scenario: Import dataset from JSON
- **WHEN** a user uploads a JSON file containing an array of Goldens
- **THEN** the system SHALL parse the JSON, validate each Golden against the schema, create a dataset, and return the dataset_id

#### Scenario: run 归属基准
- **WHEN** 通过批量接口创建 run
- **THEN** run 携带 benchmark_id 与 batch_id,leaderboard 查询可据此聚合

### Requirement: Evaluation engine supports agent adapter interface
The system SHALL define an AgentAdapter protocol that all agents must implement. The protocol SHALL include methods: run(input: str) -> AgentResult (containing output and metadata), and get_trace() -> Trace (containing execution spans). The system SHALL provide pre-built adapters for OpenAI and LangChain agents.

#### Scenario: Custom agent adapter implementation
- **WHEN** a user implements a custom AgentAdapter for their agent framework
- **THEN** the system SHALL accept the adapter, call adapter.run(input) for each test case, call adapter.get_trace() to retrieve the execution trace, and use the trace for evaluation

#### Scenario: Pre-built OpenAI adapter
- **WHEN** a user configures an agent with adapter_type="openai" and provides OpenAI API credentials and agent configuration (model, tools, system prompt)
- **THEN** the system SHALL use the pre-built OpenAI adapter to execute the agent and capture traces

### Requirement: 对比统计在引擎层产出
系统 SHALL 在服务层(comparison service)产出对比统计,每指标包含 avg、n、stddev、min、max;MCP 工具与前端 SHALL 复用该服务,不得各自重算。

#### Scenario: 统计口径
- **WHEN** 某 agent 在某 benchmark 下 task_completion 得分为 [0.8, 1.0, 0.6]
- **THEN** 统计输出 avg=0.8、n=3、stddev≈0.163、min=0.6、max=1.0

