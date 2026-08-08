"""Domain tools: start and monitor evaluation runs."""
from mcp_server.client import get, post

# ponytail: minimal metric->DeepEval-class mapping; unknown names pass
# through and are validated by the backend. Add mappings as patterns stabilize.
KNOWN_METRICS = {
    "task_completion": "TaskCompletion",
    "step_efficiency": "StepEfficiency",
    "plan_quality": "PlanQuality",
}


def _metric_to_evaluator_config(name: str) -> dict:
    metric_cls = KNOWN_METRICS.get(name, name)
    return {
        "name": name,
        "type": "deepeval_metric",
        "config": {"metric": metric_cls, "threshold": 0.5},
    }


async def _resolve_agent_id(name_or_id: str) -> str:
    # ponytail: linear scan of the agent list; fine until thousands of agents
    agents = await get("/api/v1/agents", params={"limit": 1000})
    for a in agents:
        if a.get("name") == name_or_id or a.get("id") == name_or_id:
            return a["id"]
    raise ValueError(f"agent '{name_or_id}' not found")


async def _resolve_dataset_id(name_or_id: str) -> str:
    datasets = await get("/api/v1/datasets", params={"limit": 1000})
    for d in datasets:
        if d.get("name") == name_or_id or d.get("id") == name_or_id:
            return d["id"]
    raise ValueError(f"dataset '{name_or_id}' not found")


def register(mcp):
    @mcp.tool
    async def run_evaluation(
        agent: str,
        dataset: str,
        metrics: list[str] | None = None,
        created_by: str = "mcp",
    ) -> dict:
        """Start an evaluation run. `agent` and `dataset` accept names or IDs.
        `metrics` is a list of metric names (e.g. ["task_completion",
        "step_efficiency"]); defaults to ["task_completion"]. Returns the new
        run's id and status."""
        if metrics is None:
            metrics = ["task_completion"]
        agent_id = await _resolve_agent_id(agent)
        dataset_id = await _resolve_dataset_id(dataset)
        evaluator_configs = [_metric_to_evaluator_config(m) for m in metrics]
        run = await post(
            "/api/v1/evaluations",
            body={
                "agent_id": agent_id,
                "dataset_id": dataset_id,
                "evaluator_configs": evaluator_configs,
                "created_by": created_by,
            },
        )
        return {"run_id": run.get("id"), "status": run.get("status"), "run": run}

    @mcp.tool
    async def get_evaluation_status(run_id: str) -> dict:
        """Get status, progress, and results summary for an evaluation run."""
        return await get(f"/api/v1/evaluations/{run_id}/status")
