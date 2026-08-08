## ADDED Requirements

### Requirement: Benchmark entity
系统 SHALL 提供 Benchmark 实体,将 dataset、指标套件(metric_suite)与商业模型(value_formula、time_value_rate)组合为可复用的评测基准。

#### Scenario: 创建 Benchmark
- **WHEN** 用户 POST /api/v1/benchmarks,提供 name、dataset_id、metric_suite、value_formula、time_value_rate
- **THEN** 系统创建 Benchmark 并返回其 id
- **AND** dataset_id 对应的 dataset 不存在时返回 422

#### Scenario: 同一 dataset 配置多个 Benchmark
- **WHEN** 用户对同一 dataset 创建两个不同 value_formula 的 Benchmark
- **THEN** 两者独立存在,各自维护独立的 leaderboard

### Requirement: 批量评测(Batch)
系统 SHALL 提供批量评测接口,对同一 Benchmark 并行评测多个 agent,保证对比条件一致。

#### Scenario: 发起批量评测
- **WHEN** 用户 POST /api/v1/batches,提供 benchmark_id 与 agent_ids 列表
- **THEN** 系统为每个 agent 创建一个 EvaluationRun,均携带相同的 batch_id 与该 benchmark_id
- **AND** 所有 run 在后台并发执行(默认并发度 2,信号量限流)

#### Scenario: 查询批量进度
- **WHEN** 用户 GET /api/v1/batches/{batch_id}
- **THEN** 返回每个 agent run 的状态、进度与已完成 golden 数

### Requirement: 对比榜(Leaderboard)查询
系统 SHALL 提供 leaderboard 查询,仅聚合同一 Benchmark 下的评测结果,输出技术统计与商业指标。

#### Scenario: 获取对比榜
- **WHEN** 用户 GET /api/v1/benchmarks/{id}/leaderboard
- **THEN** 返回该 benchmark 下每个 agent 的聚合: 每指标 avg/n/stddev/min/max,以及 cost_per_success、ROI、human_replacement、time_cost
- **AND** 默认按 cost_per_success 升序排列
- **AND** 成功数为 0 的 agent,cost_per_success 为 null 并列于末尾

#### Scenario: 跨基准数据隔离
- **WHEN** 某 agent 在 Benchmark A 与 Benchmark B 下均有 run
- **THEN** Benchmark A 的 leaderboard 不混入 Benchmark B 的任何结果

### Requirement: Leaderboard 首页
系统 SHALL 将 Web UI 首页(`/`)设为 Leaderboard 视图,用户选定 Benchmark 后即可看到全部参评 agent 的对比表格。

#### Scenario: 首页查看对比
- **WHEN** 用户打开首页并选择一个 Benchmark
- **THEN** 表格展示每个 agent 的技术列(各指标 avg±stddev)与商业列(每成功任务成本、ROI、人工替代率、时间成本)
- **AND** 用户可点击任意列排序,可点击 agent 行钻取到对应 batch 的 run 详情

#### Scenario: 商业数据缺口提示
- **WHEN** 部分 golden 缺少 human_cost 数据
- **THEN** 人工替代率列显示缺口提示(如"3/10 题缺人工成本数据"),而非显示 0 或报错
