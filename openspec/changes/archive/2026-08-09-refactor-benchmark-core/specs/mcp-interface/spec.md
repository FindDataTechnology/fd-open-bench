## MODIFIED Requirements

### Requirement: MCP server exposes domain tools
MCP server 的对比类工具 SHALL 基于 benchmark 语义:`compare_agents` 必须指定 benchmark(名称或 ID),返回 leaderboard 完整对比(技术统计 + 商业指标);SHALL 新增 `run_benchmark` 与 `get_leaderboard` 工具;`export_report` SHALL 输出商业结论段(推荐 agent、每成功任务成本、ROI、人工替代率、数据缺口提示)。

#### Scenario: 同基准对比
- **WHEN** 调用 compare_agents(agent_ids=[...], benchmark="goldens_v2")
- **THEN** 返回该 benchmark 下各 agent 的对比表,含 cost_per_success 与排序

#### Scenario: 跨基准对比被拒绝
- **WHEN** 调用方试图比较无共同 benchmark 的 agents
- **THEN** 工具返回明确错误,提示先对这些 agent 跑同一 benchmark

#### Scenario: 报告含商业结论
- **WHEN** 调用 export_report(run_id 或 batch_id)
- **THEN** 报告包含推荐结论段:推荐哪个 agent、理由(成本/ROI/替代率)、缺哪些数据

### Requirement: fd-bench CLI one-shot mode
CLI SHALL 提供 `run-benchmark`(benchmark + agents)、`leaderboard <benchmark>` 命令;`run-eval`/`report` 输出与 benchmark 语义对齐;`raw` 逃生舱保留。

#### Scenario: CLI 跑基准
- **WHEN** 用户执行 `fd-bench run-benchmark --benchmark goldens_v2 --agents paybot,helper`
- **THEN** 创建批量评测并输出 batch_id

#### Scenario: CLI 看榜
- **WHEN** 用户执行 `fd-bench leaderboard goldens_v2`
- **THEN** 输出对比表(文本格式,含商业列)

## REMOVED Requirements

无。(stdio/HTTP transport、无状态、raw_api、chat 模式、base URL 配置均保留不变。)
