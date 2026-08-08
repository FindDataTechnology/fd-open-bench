# agent-runtime-tracing Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: System captures agent execution traces via @observe decorators
The system SHALL capture agent execution traces using DeepEval's @observe decorators. Agent adapters SHALL wrap their execution with @observe(type="agent") on the root function, @observe(type="llm") on LLM calls, @observe(type="tool") on tool executions, and @observe(type="retriever") on retrieval operations. The system SHALL capture a hierarchical trace tree with spans nested by parent-child relationships.

#### Scenario: Trace capture for multi-step agent
- **WHEN** an agent executes with the following sequence: agent root → LLM call → tool execution (search_flights) → LLM call → tool execution (book_flight)
- **THEN** the system SHALL capture a trace with one root span (type="agent"), four child spans (two type="llm", two type="tool"), and preserve the parent-child relationships and execution order

#### Scenario: Nested span hierarchy
- **WHEN** an agent calls a sub-agent which then calls tools
- **THEN** the trace SHALL reflect the nesting: agent span contains sub-agent span, which contains tool spans

### Requirement: Trace spans capture comprehensive runtime information
Each trace span SHALL capture: span_id (unique identifier), parent_span_id (null for root), span_type (agent/llm/tool/retriever), name (human-readable label), start_time (ISO 8601 timestamp), end_time (ISO 8601 timestamp), duration_ms (computed), input (string or JSON), output (string or JSON), token_usage (for LLM spans: input_tokens, output_tokens, total_tokens, model), metadata (dict for span-specific data like tool arguments, retriever top_k), and status (success/error/timeout).

#### Scenario: LLM span with token usage
- **WHEN** an agent makes an LLM call to gpt-4o that consumes 150 input tokens and 80 output tokens
- **THEN** the LLM span SHALL include token_usage={input_tokens: 150, output_tokens: 80, total_tokens: 230, model: "gpt-4o"}

#### Scenario: Tool span with arguments and result
- **WHEN** an agent calls a tool "search_flights" with arguments {origin: "NYC", destination: "Paris", date: "2025-03-18"} and receives a result [{id: "FL123", price: 450}]
- **THEN** the tool span SHALL include input={origin: "NYC", destination: "Paris", date: "2025-03-18"}, output=[{id: "FL123", price: 450}], and metadata={tool_name: "search_flights"}

#### Scenario: Span with error status
- **WHEN** a tool execution raises an exception
- **THEN** the span SHALL have status="error", metadata={error_type: "ValueError", error_message: "Invalid date format"}, and end_time set to when the error occurred

### Requirement: System aggregates token usage across trace
The system SHALL aggregate token usage across all LLM spans in a trace. The trace root SHALL include total_token_usage with summed input_tokens, output_tokens, and total_tokens. The system SHALL also compute estimated_cost based on model-specific pricing (configurable per model).

#### Scenario: Token aggregation across multiple LLM calls
- **WHEN** a trace contains three LLM spans with token usage: [100 input, 50 output], [200 input, 100 output], [150 input, 75 output]
- **THEN** the trace total_token_usage SHALL be {input_tokens: 450, output_tokens: 225, total_tokens: 675}

#### Scenario: Cost estimation
- **WHEN** a trace has total_token_usage={input_tokens: 450, output_tokens: 225} and the model pricing is configured as gpt-4o: {input: $0.0025/1K tokens, output: $0.01/1K tokens}
- **THEN** the trace SHALL include estimated_cost = (450/1000 × 0.0025) + (225/1000 × 0.01) = $0.001125 + $0.00225 = $0.003375

### Requirement: System persists traces for later retrieval
The system SHALL persist complete traces (all spans with metadata) in the database. Traces SHALL be linked to their corresponding EvaluationResult. The system SHALL support retrieving traces by evaluation_result_id, agent_id, or time range.

#### Scenario: Trace retrieval by result ID
- **WHEN** a user requests the trace for evaluation_result_id="abc123"
- **THEN** the system SHALL return the complete trace tree with all spans, preserving hierarchy and metadata

#### Scenario: Trace compression for storage
- **WHEN** a trace exceeds 10KB in size
- **THEN** the system SHALL compress the trace using gzip before storing in the database, and decompress on retrieval

### Requirement: System provides trace export in standard formats
The system SHALL support exporting traces in JSON format (DeepEval native) and OpenTelemetry format (for integration with external observability tools). Export SHALL include all span metadata and token usage data.

#### Scenario: Export trace as JSON
- **WHEN** a user requests trace export in JSON format for evaluation_result_id="abc123"
- **THEN** the system SHALL return a JSON file containing the complete trace tree with all spans and metadata

#### Scenario: Export trace as OpenTelemetry
- **WHEN** a user requests trace export in OpenTelemetry format
- **THEN** the system SHALL convert the trace to OTLP (OpenTelemetry Protocol) format, mapping span types to OTel span attributes, and return the converted trace

### Requirement: System computes execution timing metrics
The system SHALL compute timing metrics for each trace: total_duration_ms (root span duration), llm_duration_ms (sum of LLM span durations), tool_duration_ms (sum of tool span durations), idle_time_ms (time spent between spans, e.g., agent reasoning), and time_breakdown (percentage of time in each span type).

#### Scenario: Timing breakdown
- **WHEN** a trace has total_duration_ms=5000, llm_duration_ms=3000, tool_duration_ms=1500
- **THEN** the system SHALL compute idle_time_ms=500 and time_breakdown={llm: 60%, tool: 30%, idle: 10%}

