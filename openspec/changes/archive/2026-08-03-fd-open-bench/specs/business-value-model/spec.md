## ADDED Requirements

### Requirement: System tracks token-based costs
The system SHALL track token-based costs for each evaluation run. The system SHALL compute token_cost = (input_tokens × input_price_per_token) + (output_tokens × output_price_per_token) for each LLM span in the trace, and sum across all spans for the total token_cost. Token prices SHALL be configurable per model (e.g., gpt-4o: input=$0.0025/1K, output=$0.01/1K). The system SHALL support multiple currencies (USD, EUR, etc.) with configurable exchange rates.

#### Scenario: Token cost calculation for single LLM call
- **WHEN** an LLM span has input_tokens=1000, output_tokens=500, and model pricing is gpt-4o: input=$0.0025/1K, output=$0.01/1K
- **THEN** the system SHALL compute token_cost = (1000/1000 × 0.0025) + (500/1000 × 0.01) = $0.0025 + $0.005 = $0.0075

#### Scenario: Total token cost across trace
- **WHEN** a trace has three LLM spans with token costs: $0.0075, $0.0050, $0.0030
- **THEN** the system SHALL compute total_token_cost = $0.0155

### Requirement: System tracks time-based costs
The system SHALL track time-based costs for each evaluation run. The system SHALL support three pricing models: per-minute (cost = duration_minutes × price_per_minute), per-hour (cost = duration_hours × price_per_hour), and hybrid (token_cost + time_cost). Time-based cost SHALL be computed from the agent's total execution time (root span duration). Pricing SHALL be configurable per agent.

#### Scenario: Per-minute pricing
- **WHEN** an agent has pricing_config={type: "per_minute", price: 0.10} and execution time is 5 minutes
- **THEN** the system SHALL compute time_cost = 5 × $0.10 = $0.50

#### Scenario: Per-hour pricing
- **WHEN** an agent has pricing_config={type: "per_hour", price: 6.00} and execution time is 30 seconds
- **THEN** the system SHALL compute time_cost = (30/3600) × $6.00 = $0.05

#### Scenario: Hybrid pricing
- **WHEN** an agent has pricing_config={type: "hybrid", token_pricing: {...}, time_pricing: {type: "per_minute", price: 0.05}} and token_cost=$0.01, execution_time=2 minutes
- **THEN** the system SHALL compute total_cost = $0.01 + (2 × $0.05) = $0.11

### Requirement: System tracks infrastructure costs
The system SHALL track infrastructure costs for each evaluation run. Infrastructure costs SHALL include: server costs (configurable per_hour rate for the evaluation server), external API costs (sum of costs for external API calls made by the agent, e.g., flight search APIs), and database costs (configurable per_query rate). Infrastructure costs SHALL be optional and configurable per agent.

#### Scenario: External API cost tracking
- **WHEN** an agent makes 3 external API calls during execution, each costing $0.01
- **THEN** the system SHALL compute external_api_cost = 3 × $0.01 = $0.03

#### Scenario: Total infrastructure cost
- **WHEN** an agent has server_cost=$0.05, external_api_cost=$0.03, database_cost=$0.01
- **THEN** the system SHALL compute total_infrastructure_cost = $0.09

### Requirement: System computes total cost per evaluation
The system SHALL compute total_cost = token_cost + time_cost + infrastructure_cost for each evaluation result. The system SHALL also compute cost_breakdown showing the percentage contribution of each cost component.

#### Scenario: Total cost calculation
- **WHEN** an evaluation result has token_cost=$0.015, time_cost=$0.05, infrastructure_cost=$0.03
- **THEN** the system SHALL compute total_cost = $0.095 and cost_breakdown = {token: 15.8%, time: 52.6%, infrastructure: 31.6%}

### Requirement: System calculates business value delivered
The system SHALL calculate business_value delivered by each evaluation result. Business value SHALL be computed from the Golden's business_value field (if provided) multiplied by a success_factor (0.0 to 1.0 based on evaluation scores). Alternatively, business value SHALL be computable via a custom formula configured per agent (e.g., value = task_completion_score × deal_value).

#### Scenario: Business value from Golden
- **WHEN** a Golden has business_value=50.0 and the evaluation result has overall_score=0.8
- **THEN** the system SHALL compute business_value_delivered = 50.0 × 0.8 = $40.0

#### Scenario: Custom value formula
- **WHEN** an agent has value_formula="task_completion_score × deal_value" and the evaluation result has task_completion_score=0.9 and deal_value=100.0 (from Golden metadata)
- **THEN** the system SHALL compute business_value_delivered = 0.9 × 100.0 = $90.0

### Requirement: System computes ROI (Return on Investment)
The system SHALL compute ROI for each evaluation result and aggregate ROI across evaluation runs. ROI SHALL be computed as: roi = (business_value_delivered - total_cost) / total_cost. The system SHALL also compute: cost_efficiency = business_value_delivered / total_cost, break_even_point = total_cost / business_value_per_task, and marginal_cost = cost of next additional task.

#### Scenario: ROI calculation
- **WHEN** an evaluation result has business_value_delivered=$40.0 and total_cost=$0.095
- **THEN** the system SHALL compute roi = (40.0 - 0.095) / 0.095 = 420.05 (or 42005%), cost_efficiency = 40.0 / 0.095 = 421.05

#### Scenario: Aggregate ROI across run
- **WHEN** an evaluation run has 100 test cases with total business_value_delivered=$2000 and total_cost=$9.50
- **THEN** the system SHALL compute aggregate_roi = (2000 - 9.50) / 9.50 = 209.53

### Requirement: System compares token spend vs time-based cost
The system SHALL provide comparison views showing token_cost vs time_cost for each evaluation result and aggregated across runs. The system SHALL highlight which cost component dominates. The system SHALL support "what-if" analysis: "If we switch from per-minute to token-based pricing, how does cost change?"

#### Scenario: Cost comparison view
- **WHEN** an evaluation result has token_cost=$0.015 and time_cost=$0.05
- **THEN** the system SHALL display a comparison showing time_cost is 3.33× higher than token_cost, and time_cost represents 76.9% of total cost

#### Scenario: What-if pricing analysis
- **WHEN** a user requests "what-if" analysis switching from per-minute ($0.10/min) to token-based pricing for an agent with average execution_time=5 minutes and average token_usage=2000 tokens
- **THEN** the system SHALL compute current_cost = 5 × $0.10 = $0.50, alternative_cost = token_cost_at_2000_tokens, and show the difference

### Requirement: System tracks cost trends over time
The system SHALL track cost trends across evaluation runs for each agent. The system SHALL compute: average_cost_per_run, cost_per_task_completion (total_cost / number of successful tasks), cost_trend (percentage change in average cost over time), and cost_forecast (predicted cost for next N runs based on trend).

#### Scenario: Cost trend analysis
- **WHEN** an agent has evaluation runs over 30 days with average_cost_per_run: week1=$10, week2=$8, week3=$6, week4=$5
- **THEN** the system SHALL compute cost_trend = -50% (decreasing) and display a line chart showing the trend

### Requirement: System supports business model configuration per agent
The system SHALL support configuring a business model per agent. The business model SHALL include: pricing_config (token pricing, time pricing, infrastructure pricing), value_formula (custom formula for calculating business value), roi_targets (minimum_roi, target_roi), and cost_alerts (alert if cost_per_task exceeds threshold).

#### Scenario: Configure business model
- **WHEN** a user configures a business model for agent "sales-agent" with pricing_config={type: "hybrid", ...}, value_formula="task_completion_score × deal_value", roi_targets={minimum_roi: 10.0, target_roi: 50.0}
- **THEN** the system SHALL persist the business model and use it for all future evaluation runs of that agent

#### Scenario: Cost alert
- **WHEN** an agent has cost_alert={threshold: 1.00, metric: "cost_per_task"} and an evaluation run computes cost_per_task=$1.50
- **THEN** the system SHALL trigger an alert and notify the user via the UI
