## MODIFIED Requirements

### Requirement: Evaluation engine orchestrates agent evaluation runs
评测引擎 SHALL 支持批量运行语义:一次批量操作针对同一 Benchmark 为多个 agent 各创建一个 run(携带相同 batch_id 与 benchmark_id),在进程内以后台任务并发执行(默认并发度 2)。评测执行 SHALL NOT 依赖 Celery/Redis。

#### Scenario: 批量执行
- **WHEN** 用户发起 3 agents × 1 benchmark 的批量评测
- **THEN** 系统创建 3 个共享 batch_id 的 run,后台并发执行,各自状态机独立(pending→running→completed/failed)

#### Scenario: 无外部队列依赖
- **WHEN** 仅启动单个 FastAPI 进程(无 Redis、无 Celery worker)
- **THEN** 批量评测完整执行完毕,结果落库

### Requirement: Evaluation engine provides evaluation dataset management
评测引擎 SHALL 通过 Benchmark 实体关联 dataset 与指标套件;run 记录 benchmark_id,使结果可归入对应基准的对比。

#### Scenario: run 归属基准
- **WHEN** 通过批量接口创建 run
- **THEN** run 携带 benchmark_id 与 batch_id,leaderboard 查询可据此聚合

## ADDED Requirements

### Requirement: 对比统计在引擎层产出
系统 SHALL 在服务层(comparison service)产出对比统计,每指标包含 avg、n、stddev、min、max;MCP 工具与前端 SHALL 复用该服务,不得各自重算。

#### Scenario: 统计口径
- **WHEN** 某 agent 在某 benchmark 下 task_completion 得分为 [0.8, 1.0, 0.6]
- **THEN** 统计输出 avg=0.8、n=3、stddev≈0.163、min=0.6、max=1.0
