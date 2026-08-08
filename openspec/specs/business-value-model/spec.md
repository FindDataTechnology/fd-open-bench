# business-value-model Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
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
系统 SHALL 基于 Benchmark 上的 value_formula 计算商业价值,公式通过安全表达式求值器执行,禁止 `eval()`。允许变量: business_value、success_score、human_cost、latency_s、input_tokens、output_tokens;允许白名单函数: min、max、abs、round。求值失败时 SHALL 回退到默认公式 `business_value * success_score` 并在结果 metadata 记录 `formula_error`。

#### Scenario: 自定义公式求值
- **WHEN** Benchmark 的 value_formula 为 `business_value * success_score - time_cost`
- **THEN** 系统使用安全求值器计算,结果正确反映公式语义

#### Scenario: 恶意公式被拒绝
- **WHEN** value_formula 包含属性访问、import 或任意函数调用(如 `__class__.__bases__`)
- **THEN** 求值器拒绝执行,回退默认公式,metadata 记录 formula_error

### Requirement: System computes ROI (Return on Investment)
The system SHALL compute ROI for each evaluation result and aggregate ROI across evaluation runs. ROI SHALL be computed as: roi = (business_value_delivered - total_cost) / total_cost. The system SHALL also compute: cost_efficiency = business_value_delivered / total_cost, break_even_point = total_cost / business_value_per_task, and marginal_cost = cost of next additional task.

#### Scenario: ROI calculation
- **WHEN** an evaluation result has business_value_delivered=$40.0 and total_cost=$0.095
- **THEN** the system SHALL compute roi = (40.0 - 0.095) / 0.095 = 420.05 (or 42005%), cost_efficiency = 40.0 / 0.095 = 421.05

#### Scenario: Aggregate ROI across run
- **WHEN** an evaluation run has 100 test cases with total business_value_delivered=$2000 and total_cost=$9.50
- **THEN** the system SHALL compute aggregate_roi = (2000 - 9.50) / 9.50 = 209.53

### Requirement: 每成功任务成本
系统 SHALL 计算 cost_per_success = 总成本 / 成功任务数,作为商业层核心指标。

#### Scenario: 正常计算
- **WHEN** 某 agent 在 benchmark 下总成本 $12、成功 8 题
- **THEN** cost_per_success = $1.50

#### Scenario: 零成功保护
- **WHEN** 成功数为 0
- **THEN** cost_per_success 为 null(不除零、不显示 0)

### Requirement: 人工替代率
系统 SHALL 在 golden 提供 human_cost 时,计算 human_replacement = agent 每成功任务成本 / 人工每任务成本;缺数据的样本 SHALL 跳过并报告计数。

#### Scenario: 计算替代率
- **WHEN** agent 每成功任务成本 $1.50,golden 平均 human_cost $30
- **THEN** human_replacement = 0.05(即人工成本的 5%)

#### Scenario: 部分缺数据
- **WHEN** 10 题中 4 题无 human_cost
- **THEN** 替代率基于 6 题计算,并标注 "4/10 题缺人工成本数据"

### Requirement: 时间价值成本
系统 SHALL 按 Benchmark 的 time_value_rate($/秒)将总延迟折算为 time_cost,并从商业价值净额中扣除。

#### Scenario: 时间成本计入
- **WHEN** time_value_rate = $0.10/秒,某 run 总延迟 300 秒
- **THEN** time_cost = $30,商业净额 = 总价值 - 总成本 - time_cost

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

