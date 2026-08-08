## MODIFIED Requirements

### Requirement: System calculates business value delivered
系统 SHALL 基于 Benchmark 上的 value_formula 计算商业价值,公式通过安全表达式求值器执行,禁止 `eval()`。允许变量: business_value、success_score、human_cost、latency_s、input_tokens、output_tokens;允许白名单函数: min、max、abs、round。求值失败时 SHALL 回退到默认公式 `business_value * success_score` 并在结果 metadata 记录 `formula_error`。

#### Scenario: 自定义公式求值
- **WHEN** Benchmark 的 value_formula 为 `business_value * success_score - time_cost`
- **THEN** 系统使用安全求值器计算,结果正确反映公式语义

#### Scenario: 恶意公式被拒绝
- **WHEN** value_formula 包含属性访问、import 或任意函数调用(如 `__class__.__bases__`)
- **THEN** 求值器拒绝执行,回退默认公式,metadata 记录 formula_error

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: System compares token spend vs time-based cost
**Reason**: what-if 定价对比不服务"agent 对比"核心目标,随 CostAnalyzer 独立页一并移除;定价表保留于 Settings。
**Migration**: 定价配置数据保留于 agent.pricing_config,无数据迁移。
