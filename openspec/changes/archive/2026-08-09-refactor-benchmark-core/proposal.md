## Why

FD Open Bench 的业务目标是:让用户**很容易地比较 agent 的优劣**,并提供技术层 + 商业层双层评估。现状与目标存在结构性差距:

1. **没有"对比"产品形态** — 前端 11 个页面没有排行榜/对比页;`compare_agents` 只是 MCP 工具,且跨数据集混算平均分,方法上不成立(agents 跑在不同数据集上,对比无意义)。
2. **商业层只是孤立的计算器** — `BusinessValueCalculator` 存在,但 business_value 是 golden metadata 里拍脑袋的数字;没有"每成功任务成本"、"vs 人工成本"、"时间价值"等决策指标;`value_formula` 用 `eval()` 执行(`app/services/business_value.py:70`),是安全隐患。
3. **复杂度淹没核心价值** — Celery + Redis + PostgreSQL + 多用户 auth,对一个内部对比工具是过度工程;项目无 git 版本控制;`app/api/*.py` 约 600 行死代码仍在启动时被 import;README 架构图(Postgres+Redis+Celery)与实际开发(SQLite)漂移。

## What Changes

以 **Benchmark(基准)** 和 **Leaderboard(对比榜)** 为新的核心实体,保留现有骨架(FastAPI + SQLAlchemy + React),分五个阶段逐层重造:

- **阶段 0 — 止血与地基**: git init;删除死代码 `app/api/*.py`;移除 Celery/Redis,改用 FastAPI 后台任务;多用户 auth 简化为单 token/免登录(内部工具);README 与现实对齐。
- **阶段 1 — 数据模型**: 新增 Benchmark 实体(dataset + 指标套件 + 商业模型);Golden 增加 `business_value` / `human_cost` / `human_minutes` 正式字段;实现安全表达式求值器替代 `eval()`。
- **阶段 2 — 引擎重造**: 一次批量评测 = N agents × 同一 Benchmark(同条件、可比);对比语义(平均分、样本数、stddev、min/max、每成功任务成本、ROI、人工替代率、时间成本)进入引擎/服务层。
- **阶段 3 — Leaderboard UI**: 首页即对比榜(替换 Dashboard);CostAnalyzer 并入对比视图;页面从 11 个收敛到约 6 个。
- **阶段 4 — MCP/CLI 同步**: `compare_agents` 基于同 benchmark 的真实对比;`report` 输出商业决策结论。

## Capabilities

### New Capabilities
- `benchmark-leaderboard`: Benchmark 实体、批量评测(多 agent 同基准)、对比榜查询与统计语义、Leaderboard 首页。

### Modified Capabilities
- `business-value-model`: 商业字段正式化(Golden 列)、每成功任务成本、vs 人工成本、时间价值、安全表达式求值(移除 `eval()`)。
- `evaluation-engine`: 批量运行语义(一次 run 组 = N agents × 同 benchmark)、对比统计在引擎层产出。
- `web-ui-dashboard`: 首页改为 Leaderboard;页面收敛;移除多用户 auth 界面。
- `mcp-interface`: `compare_agents` / `export_report` 基于 benchmark 对比语义。
- `data-storage-layer`: 新增 benchmarks 表;goldens 表新增商业字段列;新增迁移。

## Impact

**代码变更:**
- 删除: `app/api/*.py`(死代码)、`app/tasks.py` 及 Celery 配置、多用户 auth 相关前端页面/上下文
- 新增: `app/models/benchmark.py`、`app/services/comparison.py`、`app/services/batch_run.py`、安全表达式求值模块、Leaderboard 前端页面
- 修改: `app/models/golden.py`、`app/services/business_value.py`、`app/services/evaluation_engine.py`、`mcp_server/tools/analysis.py`、`mcp_server/tools/reporting.py`、前端路由与页面结构
- 迁移: alembic 新增迁移(benchmarks 表、goldens 商业列、evaluation_runs.benchmark_id/batch_id)

**依赖变化:**
- 移除: celery、redis(运行期依赖)
- 新增: 安全表达式求值库(如 `simpleeval`)或自研白名单求值器

**基础设施:**
- 运行依赖从 Postgres+Redis+Celery 收敛为 SQLite + 单进程 FastAPI(后台任务用 asyncio)
- docker-compose 相应简化

**进行中 change 的处理:**
- `add-e2e-tests`(53/173)暂停: 剩余任务大量覆盖将被替换的页面(Dashboard、独立 CostAnalyzer)。测试基建(fixtures/page objects/utils)保留,阶段 3 页面定型后重新瞄准。

## Non-goals

- 多租户、对外产品化、注册/邀请流
- 实时协作、CopilotKit 侧边栏
- 新增 agent adapter 类型(现有 http/openai/langchain/custom 保持)
- 评测指标本身的算法改进(DeepEval 集成方式不变)
