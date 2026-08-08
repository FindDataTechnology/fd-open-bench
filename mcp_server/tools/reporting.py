"""Domain tools: render evaluation reports."""
import json

from mcp_server.client import get


def _build_business_conclusion(leaderboard: list[dict]) -> dict:
    """Build recommendation + data-gap analysis from leaderboard entries.

    Returns {"recommended": {...}|None, "reasons": [...], "data_gaps": [...]}.
    """
    conclusion = {"recommended": None, "reasons": [], "data_gaps": []}
    if not leaderboard:
        conclusion["data_gaps"].append("该 benchmark 下暂无评测数据,无法给出推荐。")
        return conclusion

    # Recommend the agent with the lowest cost per successful task.
    ranked = [e for e in leaderboard if e.get("cost_per_success") is not None]
    ranked.sort(key=lambda e: e["cost_per_success"])

    if ranked:
        best = ranked[0]
        conclusion["recommended"] = {
            "agent_id": best.get("agent_id"),
            "agent_name": best.get("agent_name"),
        }
        reasons = [f"每成功任务成本最低: {best['cost_per_success']:.4f}"]
        if best.get("roi") is not None:
            reasons.append(f"ROI: {best['roi']:.2f}")
        if best.get("human_replacement") is not None:
            reasons.append(
                f"人工替代率: {best['human_replacement']:.4f}"
                " (每成功任务成本/平均人工成本, 小于 1 表示比人工便宜)"
            )
        conclusion["reasons"] = reasons

    gaps = []
    if not ranked:
        gaps.append("所有 agent 均无成功任务,每成功任务成本不可计算,无法给出推荐。")
    if any(e.get("cost_per_success") is None for e in leaderboard):
        gaps.append("部分 agent 成功任务数为 0,每成功任务成本不可用。")
    if any(e.get("human_replacement") is None for e in leaderboard):
        gaps.append(
            "部分 agent 缺少人工替代率: golden 未填 human_cost,"
            "补全人工成本数据后可用。"
        )
    if any(not e.get("total_business_value") for e in leaderboard):
        gaps.append(
            "部分 golden 未填 business_value,ROI/净值结果不准确。"
        )
    conclusion["data_gaps"] = gaps
    return conclusion


def register(mcp):
    @mcp.tool
    async def export_report(run_id: str, format: str = "markdown") -> str:
        """Generate a report for an evaluation run. `format` is 'markdown' or
        'json'. Returns the report as a string. If the run belongs to a
        benchmark, includes a business conclusion: recommended agent, reasons
        (cost per success / ROI / human replacement), and data-gap hints."""
        run = await get(f"/api/v1/evaluations/{run_id}")
        summary = await get(f"/api/v1/evaluations/{run_id}/results/summary")

        # Business conclusion requires benchmark context (same-benchmark comparison).
        conclusion = None
        leaderboard = []
        benchmark_name = None
        benchmark_id = run.get("benchmark_id")
        if benchmark_id:
            board = await get(f"/api/v1/benchmarks/{benchmark_id}/leaderboard")
            leaderboard = board.get("leaderboard", [])
            benchmark_name = board.get("benchmark_name")
            conclusion = _build_business_conclusion(leaderboard)

        if format == "json":
            return json.dumps(
                {
                    "run": run,
                    "summary": summary,
                    "benchmark": {"id": benchmark_id, "name": benchmark_name},
                    "business_conclusion": conclusion,
                },
                indent=2,
                default=str,
            )

        results = await get(f"/api/v1/evaluations/{run_id}/results", params={"limit": 1000})
        lines = [
            "# Evaluation Report",
            "",
            f"- **Run**: {run.get('id')}",
            f"- **Agent**: {run.get('agent_id')}",
            f"- **Benchmark**: {benchmark_name or benchmark_id or 'n/a'}",
            f"- **Dataset**: {run.get('dataset_id')}",
            f"- **Status**: {run.get('status')}",
            f"- **Tasks**: {run.get('tasks_completed')}/{run.get('tasks_total')} "
            f"(failed: {run.get('tasks_failed')})",
            f"- **Cost**: {run.get('current_cost')}",
            "",
            "## Summary",
            "```json",
            json.dumps(summary, indent=2, default=str),
            "```",
        ]

        if conclusion is not None:
            lines += ["", "## Business Conclusion", ""]
            rec = conclusion["recommended"]
            if rec:
                lines.append(f"**推荐 Agent**: {rec.get('agent_name')} (`{rec.get('agent_id')}`)")
                lines.append("")
                lines.append("推荐理由:")
                for reason in conclusion["reasons"]:
                    lines.append(f"- {reason}")
            else:
                lines.append("暂无推荐 Agent。")
            if conclusion["data_gaps"]:
                lines.append("")
                lines.append("数据缺口提示:")
                for gap in conclusion["data_gaps"]:
                    lines.append(f"- {gap}")

        lines += ["", f"## Results ({len(results)})"]
        for res in results:
            scores = res.get("metric_scores") or {}
            score_str = ", ".join(f"{k}={v:.3f}" for k, v in scores.items()) or "n/a"
            lines.append(
                f"- `{res.get('id')}` golden={res.get('golden_id')} "
                f"status={res.get('status')} cost={res.get('total_cost')} [{score_str}]"
            )
        return "\n".join(lines)
