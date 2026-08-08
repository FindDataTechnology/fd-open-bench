# FD Open Bench - MCP Guide

## 概述

FD Open Bench 提供了基于 Model Context Protocol (MCP) 的接口，让你可以通过：

- **命令行** (`fd-bench`) — 一次命令调用一个工具，或交互式聊天
- **Claude Desktop / Cursor** — 自然语言驱动评估平台
- **任何支持 .mcp.json 的 MCP 客户端**

MCP 服务器（`mcp_server/`）提供统一的 API，无需浏览器即可完成评估工作流。

---

## 快速开始

### 1. 安装

```bash
pip install -e ".[dev]"
export FD_BENCH_API_URL=http://localhost:8999
export ANTHROPIC_API_KEY=sk-your-key-here  # 仅用于 `fd-bench chat`
```

### 2. 启动后端

确保 FastAPI 后端在运行：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8999
```

验证：`curl http://localhost:8999/health` 应返回 `{"status":"healthy"}`

### 3. Claude Desktop / Cursor 配置

`.mcp.json`（已创建在项目根目录）：

```json
{
  "mcpServers": {
    "fd-open-bench": {
      "command": "fd-bench",
      "args": ["mcp", "serve"],
      "env": {
        "FD_BENCH_API_URL": "http://localhost:8999",
        "ANTHROPIC_API_KEY": "sk-your-key-here",
        "ANTHROPIC_BASE_URL": "https://your-llm-endpoint/v1"
      }
    }
  }
}
```

然后在 Claude Desktop 中，通过 `/settings` → `Developer` → `MCP Servers` 导入此配置。

---

## 可用工具

### 7 个领域级工具 + 1 个 raw_api 逃逸通道

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `run_evaluation` | 启动评估运行 | `agent`, `dataset`, `metrics[]` |
| `get_evaluation_status` | 查询进度 | `run_id` |
| `analyze_weaknesses` | 识别最弱指标 | `run_id` 或 `agent_id` |
| `compare_agents` | 对比多个 agent | `agent_ids[]`, `metric` |
| `find_best_performer` | 找到最佳 agent | `dataset`, `metric` |
| `export_report` | 生成报告 | `run_id`, `format` |
| `raw_api` | 任意 REST 调用（不稳定） | `method`, `path`, `params`, `body` |

---

## 详细使用说明

### 1. run_evaluation

**作用：** 为指定 agent 和 dataset 启动评估，可选 metrics 列表。

**CLI 单条调用：**

```bash
fd-bench run-eval \
  --agent paybot \
  --dataset goldens_v2 \
  --metrics task_completion,step_efficiency,plan_quality
```

**返回：**

```json
{
  "run_id": "uuid-...",
  "status": "running",
  "tasks_total": 42,
  "tasks_completed": 0,
  ...
}
```

**MCP 工具调用（Chat 模式）：**

```
user: "为 paybot 对 goldens_v2 运行评估，用 task_completion 和 step_efficiency 指标"
→ MCP server: 解析名称→ID，POST /api/v1/evaluations，返回 run_id
→ Claude: "已启动评估 run abc123..."
```

**注意：** `agent` 和 `dataset` 接受**名称**或 ID，由 MCP 工具自动解析。

---

### 2. get_evaluation_status

**作用：** 轮询评估运行的状态、进度和摘要。

**CLI：**

```bash
fd-bench status <run_id>
```

**返回：**

```json
{
  "status": "completed",
  "tasks_total": 42,
  "tasks_completed": 42,
  "tasks_failed": 0,
  "progress": 100.0,
  "current_cost": 12.5,
  ...
}
```

**Chat 模式用法：**

```
user: "评估 run abc123 现在怎么样？"
→ MCP: call_tool("get_evaluation_status", {"run_id": "abc123"})
→ Claude: "已完成 42/42，花费 $12.5"
```

---

### 3. analyze_weaknesses

**作用：** 分析最低分指标，找出 agent/dataset 的表现弱点。

**CLI：**

```bash
# 针对单个 run
fd-bench weaknesses --run-id <run_id> --top 3

# 针对 agent（自动找最新 run）
fd-bench weaknesses --agent-id <agent_id>
```

**返回：**

```json
{
  "run_id": "...",
  "weaknesses": [
    {"metric": "plan_quality", "avg_score": 0.61},
    {"metric": "step_efficiency", "avg_score": 0.65},
    ...
  ]
}
```

**Chat 模式用法：**

```
user: "paybot 的弱点是什么？"
→ MCP: analyze_weaknesses(agent_id="paybot")
→ Claude: "表现最弱的三个指标是..."
```

---

### 4. compare_agents

**作用：** 对比多个 agent 在同一 metric 上的表现。

**CLI：**

```bash
fd-bench compare \
  --agents agent1,agent2,agent3 \
  --metric task_completion
```

**返回：**

```json
{
  "metric": "task_completion",
  "comparison": [
    {"agent_id": "agent1", "runs": 5, "avg_score": 0.82},
    {"agent_id": "agent2", "runs": 3, "avg_score": 0.76},
    ...
  ]
}
```

**Chat 模式用法：**

```
user: "对比一下 paybot 和 chatbot 的任务完成度"
→ MCP: compare_agents(["paybot", "chatbot"], "task_completion")
→ Claude: "paybot 平均 82%，chatbot 76%..."
```

---

### 5. find_best_performer

**作用：** 在一个 dataset 上找到最高分的 agent。

**CLI：**

```bash
fd-bench best \
  --dataset production_test \
  --metric task_completion
```

**返回：**

```json
{
  "metric": "task_completion",
  "dataset_id": "...",
  "agent_id": "...",
  "run_id": "...",
  "score": 0.91
}
```

**Chat 模式用法：**

```
user: "production_test 数据集上哪个 agent 表现最好？"
→ MCP: find_best_performer(dataset="production_test")
→ Claude: "agent 'best_agent' 以 91% 得分领先..."
```

---

### 6. export_report

**作用：** 将评估结果导出为 Markdown 或 JSON。

**CLI：**

```bash
# Markdown
fd-bench report <run_id> --format markdown > report.md

# JSON
fd-bench report <run_id> --format json
```

**输出（Markdown 片段）：**

```markdown
# Evaluation Report

- **Run**: uuid-...
- **Agent**: agent_id
- **Dataset**: dataset_id
- **Status**: completed
- **Tasks**: 42/42 (failed: 0)
- **Cost**: 12.5

## Summary
```json
{ ... }
```

## Results (42)
- `<id>` golden=`xxx` status=success cost=0.3 [task_completion=0.9, ...]
...
```

**Chat 模式用法：**

```
user: "给我这次评估的 markdown 报告"
→ MCP: export_report(run_id="...", format="markdown")
→ Claude: "报告已生成，你可以这样查看："
  [输出 412 chars 的 markdown 文本]
```

---

### 7. raw_api

**警告：** 不稳定逃逸通道，backend API 变更时可能失效。

**作用：** 直接调用任意 REST endpoint，用于调试或高级用例。

**CLI：**

```bash
# GET
fd-bench raw GET /api/v1/agents?limit=10

# POST
fd-bench raw POST /api/v1/evaluations \
  --body '{"agent_id":"xyz","dataset_id":"abc","evaluator_configs":[]}'
```

**Chat 模式用法：**

```
user: "获取前 5 个 dataset"
→ MCP: raw_api(method="GET", path="/api/v1/datasets?limit=5")
→ Claude: "[返回 JSON]"
```

**日志：** 每次 `raw_api` 调用会被记录（`structlog`），作为未来添加新 domain 工具的 backlog。

---

## CLI 子命令速查表

```bash
fd-bench --help

位置参数：
  {mcp,run-eval,status,weaknesses,compare,best,report,raw,chat} ...

mcp                     运行 MCP 服务器 (stdio/HTTP)
  serve                 服务 MCP (默认 stdio; --http/--port 切换)
run-eval                启动评估运行
                        --agent, --dataset, --metrics
status                  查询评估状态
                        <run_id>
weaknesses              分析最弱指标
                        --run-id / --agent-id, --top
compare                 对比 agent
                        --agents (逗号分隔), --metric
best                    查找最佳 performer
                        --dataset, --metric
report                  导出报告
                        <run_id>, --format [markdown|json]
raw                     原始 REST 调用 (不稳定)
                        <METHOD> <path> [--params] [--body]
chat                    交互式聊天 (Claude + MCP)
```

---

## Chat 模式详解

`fd-bench chat` 是一个 REPL，内置 Anthropic API（claude-opus-4-8 默认）。

### 启动

```bash
export ANTHROPIC_API_KEY=sk-ant-...  # 必须设置
fd-bench chat
```

### 提示词示例

```
fd-bench> 列出可用的 agents
fd-bench> 为什么 paybot 在 plan_quality 上得分低？
fd-bench> 生产测试数据集中谁表现最好？
fd-bench> 给 run xyz 生成 markdown 报告
fd-bench> 比较 agent1 和 agent2 的成本效益
```

### 环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `FD_BENCH_API_URL` | backend URL | `http://localhost:8999` |
| `ANTHROPIC_API_KEY` | Chat 模式必需 | (无) |
| `ANTHROPIC_BASE_URL` | Anthropic 端点 | (空；使用官方 API) |
| `FD_BENCH_MODEL` | Chat 模型 | `claude-opus-4-8` |

---

## MCP 传输模式

### stdio（默认）

**特点：** 管道/重定向友好，Claude Desktop 首选。

```bash
# 隐式（fd-bench mcp serve）
echo "list agents" | fd-bench mcp serve

# 显式
fd-bench mcp serve
```

### HTTP（未来扩展）

```bash
# 环境变量方式
export MCP_HTTP=1
fd-bench mcp serve

# 命令行参数
fd-bench mcp serve --http --port 8998
```

**注意：** HTTP 传输当前**仅限本地**。在暴露到公网前需添加认证。

---

## 常见问题

### Q: MCP 工具和 `fd-bench chat` 有什么区别？

**A:** 
- `fd-bench run-eval ...` — 单次命令，无 LLM，适合脚本/自动化
- `fd-bench chat` — REPL，Claude 调用工具，适合自然语言探索
- Claude Desktop — 独立的 Claude Desktop 应用，读取 `.mcp.json`，完全相同的一排工具

三者共享**同一个 MCP 服务器代码**（`mcp_server/main.py`），工具定义唯一来源。

### Q: 为什么我看到的评估总是 "failed"？

**A:** 这通常是因为 agent 配置为空（没有真实 LLM 执行）。你需要：

```python
# 创建 agent 时包含有效的 adapter 和 config
curl -X POST http://localhost:8999/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_agent",
    "adapter_type": "openai",
    "config": {"model": "gpt-4-turbo"}
  }'
```

MCP 工具本身功能正常——它们能创建 run、查询状态、生成报告。评分失败是业务数据问题。

### Q: 如何调试 `raw_api` 错误？

**A:** 检查 backend logs：

```bash
tail -f /tmp/backend.log  # 你启动 uvicorn 时的 log 文件
```

或直接 curl：

```bash
curl -v http://localhost:8999/api/v1/agents
```

### Q: MCP 服务器会持久化会话吗？

**A:** 不会。**MCP 服务器是无状态的**——每次工具调用都是独立请求 backend。这是有意设计，避免 session DB 复杂性。如果需要跨对话记忆，存储在 backend 的 evaluation runs 里，而非 MCP。

### Q: 能否修改现有 MCP 工具？

**A:** 可以！工具在 `mcp_server/tools/`：
- `evaluation.py` — `run_evaluation`, `get_evaluation_status`
- `analysis.py` — `analyze_weaknesses`, `compare_agents`, `find_best_performer`
- `reporting.py` — `export_report`
- `raw.py` — `raw_api`

每个工具有 typed docstrings，FastMCP 自动生成输入/输出 schema。添加新工具只需新增函数并装饰 `@mcp.tool`。

---

## 开发指南

### 添加新工具

1. **选择模块**（evaluation/analysis/reporting/raw）或新建文件
2. **定义 async 函数**：

   ```python
   from mcp_server.client import get

   @mcp.tool
   async def list_evaluations(
       agent_id: str | None = None,
       status: str | None = None,
       limit: int = 10
   ) -> list[dict]:
       """List recent evaluations with optional filters."""
       url = "/api/v1/evaluations/"
       params = {}
       if agent_id: params["agent_id"] = agent_id
       if status: params["status"] = status
       params["limit"] = limit
       return await get(url, params=params)
   ```

3. **注册到 `tools/__init__.py`**：

   ```python
   def register(mcp):
       from mcp_server.tools import evaluation, analysis, reporting, raw, my_new_tool
       for mod in (evaluation, analysis, reporting, raw, my_new_tool):
           mod.register(mcp)
   ```

4. **重启 MCP 服务器**即可使用。

### 调试技巧

```bash
# 内进程测试（无需 subprocess）
python -c "
from fastmcp import Client
from mcp_server.main import mcp
async with Client(mcp) as c:
    tools = await c.list_tools()
    for t in tools: print(t.name, '->', t.inputSchema)
"
```

```bash
# 日志输出
export MCP_LOG_LEVEL=debug
fd-bench mcp serve
# 日志会看到工具调用细节
```

---

## Troubleshooting

### "JSONRPC message from server" error

**症状：** `Failed to parse JSONRPC message`

**原因：** 服务器向 stdout 打印了非-JSON-RPC 内容（banner/logs）

**解决：** 已修复。如果复现：
1. 确认 `mcp_server/main.py` 有 `logging.basicConfig(stream=sys.stderr)`
2. 确保 structlog 指向 stderr

### "502 Bad Gateway"

**症状：** tool calls fail with 502

**原因：** httpx 被 proxy 拦截 localhost 流量

**解决：** 已修复。确认：
```python
httpx.AsyncClient(..., trust_env=False, follow_redirects=True)
```

### "500 Internal Server Error"

**常见原因：**
1. UUID 未导入（Python 3.12 无 `uuid7`）→ 使用 `uuid.uuid4()`
2. Pydantic 响应 model 字段类型不匹配 → `Optional[str]` 允许 None
3. 数据库迁移缺失 → `alembic upgrade head`

---

## 安全提醒

- **本地优先：** MCP 服务器设计用于本地（Claude Desktop / 终端），不支持外部访问
- **auth gate：** HTTP 传输需在暴露前添加 auth
- **API key 管理：** `ANTHROPIC_API_KEY` 仅在 `chat` 模式需要；`raw_api` 调用的 backend 可能已有鉴权（如 JWT）
- **不存 secrets 到 memory：** MCP 服务器不持久化任何会话或凭证

---

## 参考资源

- [README.md - CLI & MCP](../README.md#cli--mcp)
- [OpenSpec change: add-mcp-cli-interface](../openspec/changes/archive/2026-08-06-add-mcp-cli-interface/)
- [FastMCP docs](https://gofastmcp.com)
