"""Domain tools: render evaluation reports."""
import json

from mcp_server.client import get


def register(mcp):
    @mcp.tool
    async def export_report(run_id: str, format: str = "markdown") -> str:
        """Generate a report for an evaluation run. `format` is 'markdown' or
        'json'. Returns the report as a string."""
        run = await get(f"/api/v1/evaluations/{run_id}")
        summary = await get(f"/api/v1/evaluations/{run_id}/results/summary")
        if format == "json":
            return json.dumps({"run": run, "summary": summary}, indent=2, default=str)
        results = await get(f"/api/v1/evaluations/{run_id}/results", params={"limit": 1000})
        lines = [
            "# Evaluation Report",
            "",
            f"- **Run**: {run.get('id')}",
            f"- **Agent**: {run.get('agent_id')}",
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
            "",
            f"## Results ({len(results)})",
        ]
        for res in results:
            scores = res.get("metric_scores") or {}
            score_str = ", ".join(f"{k}={v:.3f}" for k, v in scores.items()) or "n/a"
            lines.append(
                f"- `{res.get('id')}` golden={res.get('golden_id')} "
                f"status={res.get('status')} cost={res.get('total_cost')} [{score_str}]"
            )
        return "\n".join(lines)
