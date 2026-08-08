# Tasks: refactor-benchmark-core

## 阶段 0 — 止血与地基

- [x] 0.1 `git init`,添加 `.gitignore`(node_modules、__pycache__、*.db、.env、venv),提交现状为基线 commit
- [x] 0.2 删除死代码 `app/api/agents.py`、`datasets.py`、`goldens.py`、`evaluations.py`、`evaluators.py`,并将 `app/api/__init__.py` 清空为纯包标记(不再有 import 副作用)
- [x] 0.3 验证删除后应用正常启动、全部路由可达(对照 `app/api/routes/` 注册的 5 个 router)
- [x] 0.4 移除 Celery/Redis: 删除 `app/tasks.py`、`pyproject.toml` 中 celery/redis 依赖、docker-compose 中 celery/redis 服务
- [x] 0.5 将 Celery 调用的评测入口改为 FastAPI BackgroundTasks / asyncio 后台执行,保持 run 状态机(pending→running→completed/failed)不变
- [x] 0.6 SQLite 开启 WAL 模式(连接初始化处设置 `PRAGMA journal_mode=WAL`)
- [x] 0.7 移除多用户 auth: 删除前端 Login 页、AuthContext、ProtectedRoute;后端 auth 路由改为可选单 token 校验(`FD_BENCH_API_TOKEN`,空则放行)
- [x] 0.8 重写 README: 架构图改为 SQLite + 单进程;Quick Start 与实际启动方式(`start.sh`)一致;标注 `fd-bench` CLI/MCP 用法不变
- [x] 0.9 在 `add-e2e-tests/tasks.md` 顶部标注: 本 change 暂停,待 refactor-benchmark-core 阶段 3 页面定型后重新瞄准
- [x] 0.10 提交阶段 0,验证: 后端启动、前端构建、MCP `raw_api GET /api/v1/agents` 可用

## 阶段 1 — 数据模型

- [x] 1.1 新增 `app/models/benchmark.py`: id/name/description/dataset_id/metric_suite(JSON)/value_formula/time_value_rate/时间戳
- [x] 1.2 Golden 模型新增列: `business_value`(Numeric)、`human_cost`(Numeric)、`human_minutes`(Integer),均可空
- [x] 1.3 EvaluationRun 模型新增列: `benchmark_id`(可空,FK)、`batch_id`(可空,索引)
- [x] 1.4 编写 alembic 迁移: benchmarks 建表;goldens 三列并从 `extra_metadata.business_value` 回填;evaluation_runs 两列
- [x] 1.5 实现安全表达式求值器 `app/utils/expression.py`: AST 白名单(变量/四则/比较/条件/min/max/abs/round),禁止属性访问与任意调用
- [x] 1.6 求值器单元测试: 合法公式正确求值;`__class__`、`import`、属性链等攻击载荷被拒绝;求值异常走回退
- [x] 1.7 Benchmark CRUD API: `POST/GET/PUT/DELETE /api/v1/benchmarks`,含 dataset 存在性校验
- [x] 1.8 Golden API 支持商业字段读写(创建/编辑/导入时接受 business_value/human_cost/human_minutes)

## 阶段 2 — 引擎重造

- [x] 2.1 `BusinessValueCalculator` 移除 `eval()`,改用安全求值器;公式失败回退 `business_value * success_score` 并在 metadata 记录 `formula_error`
- [x] 2.2 新增每成功任务成本: `cost_per_success = total_cost / success_count`(success_count=0 时返回 null 而非除零)
- [x] 2.3 新增人工替代率: `human_replacement = cost_per_success / human_cost_per_task`(golden 缺 human_cost 的样本跳过并计数)
- [x] 2.4 新增时间成本: `time_cost = total_latency_s × benchmark.time_value_rate`,计入商业价值净额
- [x] 2.5 新增批量接口 `POST /api/v1/batches`: 入参 benchmark_id + agent_ids;为每 agent 创建带 batch_id/benchmark_id 的 run;后台并发执行(asyncio 信号量限流,默认 2)
- [x] 2.6 批量进度查询 `GET /api/v1/batches/{batch_id}`: 每 agent run 的状态/进度/已完成 golden 数
- [x] 2.7 新增 `app/services/comparison.py`: 输入 benchmark_id(可选 batch_id),聚合该 benchmark 下 runs,输出每 agent 的技术统计(avg/n/stddev/min/max per metric)+ 商业指标(2.2-2.4)
- [x] 2.8 `GET /api/v1/benchmarks/{id}/leaderboard`: 调用 comparison service,默认按 cost_per_success 升序;无数据 agent 列末尾并标注
- [x] 2.9 引擎层单元测试: 统计口径正确(手算小样本对照)、跨 benchmark 数据不混入、缺字段样本跳过逻辑
- [x] 2.10 提交阶段 2,验证: 构造 2 agents × 1 benchmark 的批量跑,leaderboard API 返回正确排序与统计

## 阶段 3 — Leaderboard UI

- [x] 3.1 新建 Leaderboard 页面为首页 `/`: benchmark 选择器 + 对比表格(技术列: 各指标 avg±stddev;商业列: 每成功任务成本/ROI/人工替代率/时间成本)
- [x] 3.2 表格支持排序切换(按任意列)、点击 agent 行钻取到该 batch 的 run 详情
- [x] 3.3 新建 Benchmarks 列表/创建页 `/benchmarks`: 选 dataset、勾选指标套件、填 value_formula(带语法校验提示)与 time_value_rate
- [x] 3.4 Benchmark 详情页: 题目列表(含商业字段)、历史 batch 列表、"运行新批量"入口(选 agents → POST /batches)
- [x] 3.5 改造 EvaluationDetail 为 batch 详情 `/runs/:batchId`: 多 agent 进度、逐 golden 结果、trace 查看保留
- [x] 3.6 Golden 编辑/导入界面支持 business_value/human_cost/human_minutes
- [x] 3.7 删除 Dashboard、独立 CostAnalyzer、Evaluators 独立页及其路由;Layout 导航收敛为 Leaderboard/Benchmarks/Agents/Settings
- [x] 3.8 商业列空态处理: 无 human_cost 数据时显示"补全人工成本数据后可用"而非 0 或报错
- [x] 3.9 提交阶段 3,验证: 前端构建通过;完整走通"建 benchmark → 跑批量 → 看榜 → 钻取详情"

## 阶段 4 — MCP/CLI 同步

- [x] 4.1 `compare_agents` 改为必选 benchmark 参数: 调 leaderboard API,返回完整对比表(技术+商业),拒绝跨 benchmark 对比
- [x] 4.2 新增 MCP 工具 `run_benchmark`(benchmark + agents 名/ID → 创建批量)与 `get_leaderboard`(benchmark → 榜)
- [x] 4.3 `export_report` 增加商业结论段: 推荐 agent、推荐理由(每成功任务成本/ROI/人工替代率)、数据缺口提示
- [x] 4.4 `analyze_weaknesses` / `find_best_performer` 迁移到 benchmark 语义(弃用"agent 全部 run 混算")
- [x] 4.5 `fd-bench` CLI 同步: `run-eval` → `run-benchmark`;`report` 输出商业结论;保留 `raw` 逃生舱
- [x] 4.6 更新 docs/(user-guide.md、mcp-guide.md)与 README 的 CLI 示例
- [x] 4.7 提交阶段 4,验证: Claude Code 中 `compare_agents` 返回同基准对比表;`report` 含推荐结论

## 阶段 5 — 收尾

- [ ] 5.1 全仓 grep 确认无残留引用: celery、redis、`app.api.agents`(旧)、eval(
- [ ] 5.2 `add-e2e-tests` 重启评估: 按新页面结构修订其 tasks.md(或关闭并另起 change)
- [ ] 5.3 最终回归: 从空库起步,README Quick Start 逐步执行至看到 Leaderboard
- [ ] 5.4 archive 本 change
