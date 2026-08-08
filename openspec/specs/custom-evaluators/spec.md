# custom-evaluators Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: System provides validator evaluators (fast, deterministic)
The system SHALL provide a set of built-in validator evaluators that execute in <100ms, require no external API calls, and produce deterministic results. Validators SHALL include: RegexValidator (pattern matching), JsonSchemaValidator (JSON schema validation), KeywordValidator (keyword presence/absence), LengthValidator (character/word count constraints), ContainsValidator (substring matching), and FormatValidator (email, URL, phone, date format validation).

#### Scenario: RegexValidator matches pattern
- **WHEN** a RegexValidator is configured with pattern="\\S+@\\S+\\.\\S+" and must_match=true, and the agent output contains "Contact us at support@example.com"
- **THEN** the validator SHALL return score=1.0, passed=true, reason="Pattern matched"

#### Scenario: JsonSchemaValidator validates structure
- **WHEN** a JsonSchemaValidator is configured with schema={type: "object", required: ["status", "message"]}, and the agent output is {"status": "success", "message": "Done", "data": {...}}
- **THEN** the validator SHALL return score=1.0, passed=true, reason="JSON matches schema"

#### Scenario: KeywordValidator with mode="all"
- **WHEN** a KeywordValidator is configured with keywords=["refund", "policy"] and mode="all", and the agent output contains "refund" but not "policy"
- **THEN** the validator SHALL return score=0.0, passed=false, reason="Missing keyword: policy"

#### Scenario: LengthValidator enforces word count
- **WHEN** a LengthValidator is configured with min_length=100, max_length=500, unit="words", and the agent output has 75 words
- **THEN** the validator SHALL return score=0.0, passed=false, reason="Word count 75 is below minimum 100"

### Requirement: System provides LLM judge evaluators (flexible, expensive)
The system SHALL provide LLM judge evaluators that use LLMs to evaluate agent outputs. Judges SHALL include: DeepEval built-in metrics (AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric, ToxicityMetric, BiasMetric, SummarizationMetric), custom prompt judges (user-defined evaluation prompts), G-Eval (criteria-based evaluation with natural language criteria), and comparative judges (compare two agent outputs).

#### Scenario: DeepEval AnswerRelevancyMetric
- **WHEN** an evaluation run uses AnswerRelevancyMetric with threshold=0.7
- **THEN** the system SHALL pass the input and output to DeepEval's AnswerRelevancyMetric, receive a score between 0.0 and 1.0, and return passed=true if score >= 0.7

#### Scenario: Custom prompt judge
- **WHEN** a custom prompt judge is configured with prompt="Rate helpfulness from 0-10. User: {input}. Response: {output}. Return JSON: {score: N, reason: '...'}" and score_range=[0, 10], threshold=7
- **THEN** the system SHALL format the prompt with input and output, call the configured LLM, parse the JSON response, normalize the score to 0.0-1.0 range, and return passed=true if normalized score >= 0.7

#### Scenario: G-Eval with multiple criteria
- **WHEN** a G-Eval judge is configured with criteria=["Code is syntactically correct", "Code follows best practices", "Code handles edge cases"]
- **THEN** the system SHALL use DeepEval's G-Eval metric to evaluate the output against all criteria and return an aggregated score

#### Scenario: Comparative judge
- **WHEN** a comparative judge is configured to compare agent_a_output against agent_b_output
- **THEN** the system SHALL prompt the LLM to compare the two outputs and return winner="A"|"B"|"tie" with reasoning

### Requirement: System provides domain executor evaluators (ground truth)
The system SHALL provide domain executor evaluators that validate agent outputs against ground truth by executing domain-specific logic. Executors SHALL include: SQLExecutor (execute SQL queries and validate results), APIExecutor (call APIs and validate responses), CodeExecutor (execute code in sandboxed environment and run tests), and BusinessLogicExecutor (user-defined business validation functions).

#### Scenario: SQLExecutor validates query results
- **WHEN** a SQLExecutor is configured with connection="postgres://...", validation={expected_results: [{id: 1, name: "Alice"}], match_mode: "exact"}, and the agent output is a SQL query
- **THEN** the system SHALL execute the query against the database (read-only mode), compare results to expected_results, and return score=1.0 if exact match, else score=0.0

#### Scenario: CodeExecutor runs tests in sandbox
- **WHEN** a CodeExecutor is configured with language="python", sandbox="docker", test_cases=[{input: "add(2, 3)", expected_output: 5}], and the agent output is Python code defining an add function
- **THEN** the system SHALL execute the code in a Docker container with resource limits (CPU: 1 core, memory: 256MB, timeout: 10s), run the test cases, and return score=1.0 if all tests pass

#### Scenario: BusinessLogicExecutor with custom function
- **WHEN** a BusinessLogicExecutor is configured with module="my_validators", function="validate_pricing", and the agent output is a pricing calculation
- **THEN** the system SHALL import and call the validate_pricing function with the evaluation context, and return the EvaluatorResult from that function

### Requirement: System supports custom evaluator registration
The system SHALL support registering custom evaluators via three methods: YAML configuration (for built-in validators and simple LLM judges), Python module (for custom functions and complex evaluators), and visual builder UI (for no-code configuration). Custom evaluators SHALL implement the Evaluator protocol with methods: evaluate(context: EvaluationContext) -> EvaluatorResult, and validate_config(config: dict) -> bool.

#### Scenario: Register evaluator via YAML
- **WHEN** a user provides YAML config: {type: "regex", name: "email_format", config: {pattern: "\\S+@\\S+\\.\\S+"}}
- **THEN** the system SHALL instantiate a RegexValidator with the provided config and make it available for evaluation runs

#### Scenario: Register evaluator via Python module
- **WHEN** a user provides module path "my_evaluators.custom_judge" and function name "evaluate_helpfulness"
- **THEN** the system SHALL dynamically import the module, verify the function implements the Evaluator protocol, and register it as a custom evaluator

#### Scenario: Register evaluator via visual builder
- **WHEN** a user configures an evaluator through the web UI visual builder (selects type, fills in config fields, clicks "Save")
- **THEN** the system SHALL generate the corresponding YAML config, validate it, and register the evaluator

### Requirement: System executes evaluators with configurable concurrency
The system SHALL execute evaluators asynchronously. Validators SHALL run concurrently (all validators in parallel). LLM judges SHALL run concurrently with rate limiting (configurable max_concurrent_calls per judge). Executors SHALL run with configurable concurrency (some executors have side effects and may require sequential execution).

#### Scenario: Parallel validator execution
- **WHEN** an evaluation run has 5 validators configured
- **THEN** the system SHALL execute all 5 validators concurrently and wait for all to complete before proceeding to aggregation

#### Scenario: Rate-limited LLM judge execution
- **WHEN** an evaluation run has 3 LLM judges configured with max_concurrent_calls=2
- **THEN** the system SHALL execute at most 2 judges concurrently, queue the third, and respect API rate limits

### Requirement: System implements three-layer caching for LLM judges
The system SHALL implement a three-layer cache for LLM judge results: in-memory cache (per evaluation run, fastest), Redis cache (shared across runs, 24-hour TTL), and database cache (persistent, for audit trail). Cache key SHALL be hash(evaluator_name + evaluator_config + input + output + model). Cache SHALL be invalidated when evaluator config changes or model changes.

#### Scenario: Cache hit on identical evaluation
- **WHEN** an LLM judge is called with the same (evaluator_name, config, input, output, model) as a previous call within the TTL period
- **THEN** the system SHALL return the cached result without calling the LLM API

#### Scenario: Cache invalidation on config change
- **WHEN** a user modifies an LLM judge's prompt
- **THEN** the system SHALL invalidate all cached results for that judge

### Requirement: System handles evaluator errors gracefully
The system SHALL handle evaluator errors (timeout, API error, parse error, execution error) gracefully. On error, the system SHALL mark the evaluator result as status="error", record the error details, exclude that evaluator from aggregation for that test case, and continue with remaining evaluators. The system SHALL implement retry logic for LLM judges (3 attempts with exponential backoff on API errors). The system SHALL implement circuit breaker pattern (if a judge fails 5 times in a row, disable it for the run).

#### Scenario: LLM judge API timeout
- **WHEN** an LLM judge API call exceeds the configured timeout (60 seconds)
- **THEN** the system SHALL mark that evaluator result as status="timeout", record timeout_duration=60, exclude it from aggregation, and continue

#### Scenario: Circuit breaker activation
- **WHEN** an LLM judge fails 5 consecutive times due to API errors
- **THEN** the system SHALL disable that judge for the remainder of the evaluation run, log a warning, and notify the user via the UI

