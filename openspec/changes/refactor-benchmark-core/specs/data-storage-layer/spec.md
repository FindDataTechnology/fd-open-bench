## MODIFIED Requirements

### Requirement: System provides Golden (test case) entity
Golden 实体 SHALL 提供正式的商业字段列:`business_value`(Numeric)、`human_cost`(Numeric)、`human_minutes`(Integer),均可空。迁移 SHALL 从既有 `extra_metadata.business_value` 回填。

#### Scenario: 商业字段落库
- **WHEN** 创建 golden 时提供 business_value=100、human_cost=30、human_minutes=15
- **THEN** 三者存储于独立列,可被商业计算与导入导出使用

### Requirement: System provides EvaluationRun entity with status tracking
EvaluationRun SHALL 增加 `benchmark_id`(可空 FK)与 `batch_id`(可空,建索引)。旧 run 两列为空,不进入任何 leaderboard。

#### Scenario: 批量 run 分组
- **WHEN** 批量接口创建 3 个 run
- **THEN** 三者共享 batch_id 且 benchmark_id 相同,可按 batch_id 一次查出

### Requirement: System implements database migrations
系统 SHALL 通过 alembic 迁移完成本 change 的 schema 变更: benchmarks 建表、goldens 三列(含回填)、evaluation_runs 两列。默认数据库为 SQLite(WAL 模式)。

#### Scenario: 迁移可前滚可回滚
- **WHEN** 执行 `alembic upgrade head` 后 `alembic downgrade -1`
- **THEN** schema 变更与回填均正确应用与撤销

## ADDED Requirements

### Requirement: System provides Benchmark entity
系统 SHALL 提供 Benchmark 实体表: id、name、description、dataset_id(FK)、metric_suite(JSON)、value_formula(Text)、time_value_rate(Float, 默认 0)、created_at、updated_at。

#### Scenario: Benchmark 持久化
- **WHEN** 创建 Benchmark
- **THEN** 全部字段持久化于 benchmarks 表,dataset 删除时 benchmark 级联删除或拒绝删除(取级联删除)
