# 远程 Agent HTTP 契约（HttpAgentAdapter）

当你的 agent 与平台不在同一进程/架构（独立部署、跨语言、不能装进后端 venv）时，平台通过 HTTP 调用你的 agent 服务来执行评估，并接收它报告的各模块耗时。

平台侧实现：`app/adapters/http_adapter.py`（`HttpAgentAdapter`），由 `app/adapters/factory.py` 的 `build_adapter` 按 `adapter_type="http"` 实例化。

---

## 1. 契约总览

| 项 | 值 |
|---|---|
| 方法 | `POST` |
| 路径 | `{base_url}/evaluate` |
| 请求体 | `{input, run_id, agent_id}` |
| 响应体 | `{output, spans}` |
| 唯一耦合 | 就是这份 JSON 契约，没有其他 |

平台在评估每个测试用例（golden）时调用一次。你的服务收到请求后执行 agent，返回最终输出文本和本次执行里每个"模块"（LLM 调用 / 工具 / 检索）的耗时与 token 数据。

## 2. 请求

```jsonc
POST /evaluate
{
  "input": "What is 2+2?",   // 测试用例输入（必填）
  "run_id": "uuid",          // 本次评估 run（透传，用于区分 trace）
  "agent_id": "uuid"         // 被评估的 agent（透传）
}
```

## 3. 响应

```jsonc
{
  "output": "answer: What is 2+2?",   // agent 最终文本，平台作为评估输入（必填）
  "spans": [                           // 各模块耗时，可选；缺省则只记 agent 级总耗时
    {
      "span_type": "llm",              // llm | tool | retriever
      "name": "llm_call",              // 模块名，任意字符串
      "duration_ms": 51.2,             // 该模块耗时（毫秒，浮点）
      "token_usage": {                 // 可选，仅 LLM span 需要
        "input_tokens": 120,
        "output_tokens": 40,
        "model": "gpt-4o"
      },
      "status": "success"              // 可选: success | error
    },
    {
      "span_type": "tool",
      "name": "search",
      "duration_ms": 201.4
    }
  ]
}
```

### span 字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `span_type` | 是 | `llm` / `tool` / `retriever`，决定归入哪类耗时 |
| `name` | 否 | 模块名，用于 trace 可视化，默认 `remote_call` |
| `duration_ms` | 是 | 该模块耗时（毫秒）。**用真实计时**，不要用 `time.sleep` 的设定值 |
| `token_usage` | 否 | token 计数与模型名；平台用它算成本 |
| `status` | 否 | `success`（默认）/ `error` |

## 4. 平台侧如何汇总

- 平台把 `spans` 注入当前 trace，作为根 `agent` span（= 整个 HTTP 往返耗时）的子节点，形成树。
- `TimingMetricsService`（`app/services/token_aggregation.py`）按 `span_type` 聚合成 **llm / tool / retriever / idle** 四类耗时及占比：
  - `idle = 总耗时 - (llm + tool + retriever)` —— 即 HTTP 开销、序列化、你的服务内部非埋点逻辑。
- 每个 LLM span 的 `token_usage` 参与成本计算（`TokenAggregationService`）。

## 5. 注册 agent

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "my_remote_agent",
    "adapter_type": "http",
    "config": {"base_url": "http://your-host:8099", "timeout": 120}
  }'
```

评估时引擎调用 `build_adapter(agent)` → `HttpAgentAdapter(config)` → `run(input, run_id, agent_id)`。

## 6. 参考实现与测试

- **参考服务**：`scripts/reference_agent_server.py`（FastAPI 样板，假模块演示；`uvicorn scripts.reference_agent_server:app --port 8099`）。
- **端到端验证**：注册 `adapter_type="http"` 的 agent 后跑一次评估，从 `evaluation_results.trace` 读回 span 树即可看到各模块耗时。

## 7. 注意事项

- **不要走代理**：`HttpAgentAdapter` 已设 `trust_env=False`，避免环境 `http_proxy` 劫持本地服务调用。你自己的服务若在公网，需自行处理网络策略。
- **契约版本**：当前为 v1。字段新增会向后兼容，改动 `span_type` 语义则视为破坏性变更。
- **鉴权**：平台目前对 `evaluate` 端点不做鉴权（仅限本地/内网使用）。对外暴露前需在服务侧加认证。
