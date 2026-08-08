## Context

FD Open Bench 现有骨架(FastAPI 路由/服务/仓储分层、SQLAlchemy 模型、React 前端、MCP 工具)质量尚可,问题集中在:核心实体缺失(无 Benchmark/对比概念)、商业层数据模型简陋、运行栈超出内部工具需求。本设计在不推翻骨架的前提下重造核心。

**目标用户**: 作者本人 + 小团队内部使用。一切设计取舍以"打开工具 5 分钟内看到'A vs B 谁更值'"为北极星。

## Goals / Non-Goals

**Goals:**
- Benchmark 成为一等实体: dataset + 指标套件 + 商业模型的可复用组合
- 对比只在同一 Benchmark 下发生,统计口径正确(样本数、stddev、min/max)
- 商业层四指标: 每成功任务成本 + ROI、vs 人工成本、自定义价值公式(安全)、时间价值
- 运行栈极简: SQLite + 单进程 FastAPI,无 Celery/Redis/多用户
- 项目置于 git 版本控制之下

**Non-Goals:**
- 多租户/对外产品化(实体设计为此留路,但不实现)
- 实时协作、通知系统
- 分布式任务队列(单机后台任务足够)

## Decisions

### D1: Benchmark 实体

```
Benchmark
├── id, name, description
├── dataset_id          → Dataset(含 Goldens)
├── metric_suite        → JSON: evaluator configs(复用现有 evaluator registry 格式)
├── value_formula       → str: 安全表达式(见 D3),如 "business_value * success_score"
├── time_value_rate     → float: 延迟的商业成本($/秒),默认 0
└── created_at / updated_at
```

一个 Benchmark 回答:"用这把尺子、这套题、这个生意模型,量所有 agent。"

**备选方案**: 复用 Dataset 挂商业字段 —— 否决,dataset 是"题",benchmark 是"题+尺+生意",同一套题应能配不同商业模型。

### D2: 批量评测与对比语义

- 一次"跑基准"操作创建 **batch**: N 个 EvaluationRun(每 agent 一个),共享 `batch_id`,每个 run 记录 `benchmark_id`。
- 保持 run = 1 agent 的现有模型(迁移成本最低),batch 只是分组标签。
- **对比服务**(`app/services/comparison.py`): 输入 benchmark_id(可选 batch_id),输出每 agent 的聚合:
  - 技术层: 每指标 avg / n / stddev / min / max
  - 成本层: 总成本、avg 成本/任务、**每成功任务成本 = 总成本 / 成功数**
  - 商业层: 总价值、ROI、**人工替代率 = agent 每成功任务成本 / 人工每任务成本**、**时间成本 = 总延迟 × time_value_rate**
- 只统计同一 benchmark 下的 run。跨 benchmark 对比是非法操作,API 层面不暴露。

**备选方案**: 一个 run 内多 agent(results 加 agent_id 列)—— 否决,改动面更大且无收益。

### D3: 安全表达式求值(替代 eval())

现状 `BusinessValueCalculator` 用 `eval(self.value_formula, {"__builtins__": {}}, context)`,可被 `"__class__"` 等属性链击穿。

决策: 使用白名单 AST 求值器(自研,约 60 行,基于 `ast` 模块递归解释):
- 允许: 数字、变量(`business_value`、`success_score`、`human_cost`、`latency_s`、`input_tokens`、`output_tokens`)、四则运算、比较、条件表达式、`min/max/abs/round`
- 禁止: 属性访问、函数调用(除白名单)、下标、import、赋值
- 求值失败 → 回退默认公式 `business_value * success_score`,并在结果 metadata 记录 `formula_error`

### D4: Golden 商业字段正式化

`business_value` 目前在 `extra_metadata` 里。提升为列:
- `goldens.business_value NUMERIC` — 任务成功交付的商业价值($)
- `goldens.human_cost NUMERIC` — 人工完成该任务的成本($)
- `goldens.human_minutes INTEGER` — 人工完成该任务的时长(展示用)
- 迁移时从 `extra_metadata` 回填,保留 metadata 作扩展位。

### D5: 运行栈简化

- **队列**: Celery/Redis → FastAPI `BackgroundTasks` + asyncio。评测任务本质是"顺序跑 N 个 golden 的协程",单机进程内足够;并发批量用 `asyncio.gather` + 信号量限流。
- **数据库**: SQLite 为默认(现状已如此),保留 Postgres 兼容性(SQLAlchemy 层面不写死),但不作为开发依赖。
- **Auth**: 移除登录页与用户体系。前端免登录;API 保留可选的单 token 头校验(`FD_BENCH_API_TOKEN`,默认关闭),防止误暴露。
- **删除**: `app/tasks.py`、celery 配置、`app/api/*.py` 死代码、前端 Login/AuthContext/ProtectedRoute。

### D6: 前端信息架构

页面 11 → 6:

```
/                    Leaderboard(首页,选 benchmark 出对比榜)   [新]
/benchmarks          Benchmark 列表/创建                        [新,吸收 Datasets 入口]
/benchmarks/:id      Benchmark 详情: 题目、尺子、历史 batch
/agents              Agent 列表/创建                             [保留]
/agents/:id          Agent 详情(含其历史 run)                  [保留]
/runs/:batchId       一次批量评测的详情(逐 golden 结果、trace)  [改造自 EvaluationDetail]
/settings            设置(token 定价表等)                       [保留]
```

删除: Dashboard(被 Leaderboard 取代)、独立 CostAnalyzer(并入 Leaderboard 商业列与 run 详情)、Evaluators 独立页(指标套件在 Benchmark 内配置)、Login。

## Data Flow(重造后)

```
用户选 N 个 agent + 1 个 Benchmark → POST /api/v1/batches
        │
        ▼
后台任务: 每 agent 一个 EvaluationRun(benchmark_id, batch_id)
        │  每 golden: adapter 执行 → trace → evaluators → 商业计算(D3/D4)
        ▼
GET /api/v1/benchmarks/:id/leaderboard
        │  comparison service 聚合同 benchmark 的 runs
        ▼
Leaderboard 表格: 技术分列 + 商业分列,默认按"每成功任务成本"排序
```

## Migration Plan

1. `alembic` 迁移: benchmarks 表;goldens 三列(回填);evaluation_runs 加 benchmark_id / batch_id(可空,旧数据兼容)
2. 旧 run(无 benchmark_id)不进任何 leaderboard,UI 提示"历史数据,未关联基准"
3. 死代码删除先于迁移执行(减少迁移时的 import 面)

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| 无 git 历史,重构不可逆 | 阶段 0 第一件事 `git init` + 基线 commit |
| 删 Celery 后发现长任务超 HTTP 超时 | 后台任务本就异步;run 状态轮询已有(`get_evaluation_status`) |
| SQLite 并发写 | WAL 模式;评测写负载低(批量顺序写) |
| 暂停中的 e2e change 腐坏 | 在 add-e2e-tests/tasks.md 顶部标注暂停原因与重启条件 |
| 安全表达式表达力不足 | 白名单函数集可扩展;回退公式保证不中断 |

## Open Questions

- (无阻塞)Benchmark 的 metric_suite 是否需要版本化(改尺子后旧榜可比性)?—— 首版不版本化,修改 benchmark 时提示影响历史对比。
