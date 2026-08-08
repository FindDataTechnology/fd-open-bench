"""Domain tools: analyze results across runs and agents."""
from mcp_server.client import get


async def _run_results(run_id: str) -> list[dict]:
    return await get(f"/api/v1/evaluations/{run_id}/results", params={"limit": 1000})


async def _agent_run_ids(agent_id: str) -> list[str]:
    runs = await get("/api/v1/evaluations", params={"agent_id": agent_id, "limit": 1000})
    return [r["id"] for r in runs]


def _avg_metric_scores(results: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for res in results:
        for k, v in (res.get("metric_scores") or {}).items():
            if not isinstance(v, (int, float)):
                continue
            totals[k] = totals.get(k, 0.0) + v
            counts[k] = counts.get(k, 0) + 1
    return {k: totals[k] / counts[k] for k in totals} if counts else {}


def register(mcp):
    @mcp.tool
    async def analyze_weaknesses(
        run_id: str | None = None,
        agent_id: str | None = None,
        top_n: int = 5,
    ) -> dict:
        """Return the lowest-scoring metrics for a run, or an agent's latest
        run. Provide run_id OR agent_id. Returns {run_id, weaknesses: [...]}."""
        if not run_id and not agent_id:
            raise ValueError("provide run_id or agent_id")
        if run_id is None:
            ids = await _agent_run_ids(agent_id)
            if not ids:
                return {"weaknesses": [], "note": "no runs for agent"}
            run_id = ids[0]
        results = await _run_results(run_id)
        avgs = _avg_metric_scores(results)
        ranked = sorted(avgs.items(), key=lambda kv: kv[1])[:top_n]
        return {
            "run_id": run_id,
            "weaknesses": [{"metric": m, "avg_score": round(s, 4)} for m, s in ranked],
        }

    @mcp.tool
    async def compare_agents(agent_ids: list[str], metric: str = "task_completion") -> dict:
        """Compare agents on a metric. Returns {metric, comparison: [...]}."""
        out = []
        for aid in agent_ids:
            ids = await _agent_run_ids(aid)
            scores = []
            for rid in ids:
                avgs = _avg_metric_scores(await _run_results(rid))
                if metric in avgs:
                    scores.append(avgs[metric])
            avg = round(sum(scores) / len(scores), 4) if scores else None
            out.append({"agent_id": aid, "runs": len(ids), "avg_score": avg})
        return {"metric": metric, "comparison": out}

    @mcp.tool
    async def find_best_performer(dataset: str, metric: str = "task_completion") -> dict:
        """Find the top-performing agent on a dataset by metric. `dataset`
        accepts a name or ID. Returns {agent_id, run_id, score}."""
        datasets = await get("/api/v1/datasets", params={"limit": 1000})
        ds_id = next(
            (d["id"] for d in datasets if d.get("name") == dataset or d.get("id") == dataset),
            None,
        )
        if not ds_id:
            raise ValueError(f"dataset '{dataset}' not found")
        runs = await get("/api/v1/evaluations", params={"limit": 1000})
        # ponytail: O(runs * results) scan; fine for moderate volumes
        best = {"agent_id": None, "run_id": None, "score": -1.0}
        for r in runs:
            if r.get("dataset_id") != ds_id:
                continue
            avgs = _avg_metric_scores(await _run_results(r["id"]))
            if metric in avgs and avgs[metric] > best["score"]:
                best = {
                    "agent_id": r.get("agent_id"),
                    "run_id": r["id"],
                    "score": round(avgs[metric], 4),
                }
        if best["agent_id"] is None:
            return {"metric": metric, "dataset_id": ds_id, "note": "no runs with that metric"}
        return {"metric": metric, "dataset_id": ds_id, **best}
