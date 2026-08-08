"""Domain tools: analyze results across runs and agents."""
from mcp_server.client import get, post


async def _run_results(run_id: str) -> list[dict]:
    return await get(f"/api/v1/evaluations/{run_id}/results", params={"limit": 1000})


async def _resolve_benchmark_id(name_or_id: str) -> str:
    """Resolve benchmark name or ID to benchmark ID."""
    benchmarks = await get("/api/v1/benchmarks/", params={"limit": 1000})
    for b in benchmarks:
        if b.get("name") == name_or_id or b.get("id") == name_or_id:
            return b["id"]
    raise ValueError(f"benchmark '{name_or_id}' not found")


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
        benchmark: str,
        agent_id: str | None = None,
        top_n: int = 5,
    ) -> dict:
        """Return the lowest-scoring metrics for an agent on a specific benchmark.
        Provide benchmark (name or ID) and optionally agent_id. If agent_id is omitted,
        analyzes the top-performing agent. Returns {benchmark_id, agent_id, weaknesses: [...]}."""
        benchmark_id = await _resolve_benchmark_id(benchmark)

        # Get leaderboard to find agent
        leaderboard = await get(f"/api/v1/benchmarks/{benchmark_id}/leaderboard")

        if not leaderboard.get("leaderboard"):
            return {"weaknesses": [], "note": "no evaluation runs for this benchmark"}

        if agent_id is None:
            # Use top performer
            agent_id = leaderboard["leaderboard"][0]["agent_id"]

        # Find agent's run for this benchmark
        runs = await get("/api/v1/evaluations", params={
            "agent_id": agent_id,
            "benchmark_id": benchmark_id,
            "limit": 1
        })
        if not runs:
            return {"weaknesses": [], "note": f"no runs for agent {agent_id} on this benchmark"}

        run_id = runs[0]["id"]
        results = await _run_results(run_id)
        avgs = _avg_metric_scores(results)
        ranked = sorted(avgs.items(), key=lambda kv: kv[1])[:top_n]
        return {
            "benchmark_id": benchmark_id,
            "agent_id": agent_id,
            "run_id": run_id,
            "weaknesses": [{"metric": m, "avg_score": round(s, 4)} for m, s in ranked],
        }

    @mcp.tool
    async def compare_agents(benchmark: str, agent_ids: list[str] | None = None) -> dict:
        """Compare agents on a specific benchmark. Returns technical and business metrics.
        `benchmark` is required (name or ID). If `agent_ids` is omitted, compares all agents
        that have runs on this benchmark. Returns {benchmark_id, comparison: [...]}."""
        benchmark_id = await _resolve_benchmark_id(benchmark)

        leaderboard = await get(f"/api/v1/benchmarks/{benchmark_id}/leaderboard")

        if not leaderboard.get("leaderboard"):
            return {"comparison": [], "note": "no evaluation runs for this benchmark"}

        # Filter by agent_ids if provided
        entries = leaderboard["leaderboard"]
        if agent_ids:
            entries = [e for e in entries if e["agent_id"] in agent_ids]

        comparison = []
        for entry in entries:
            comparison.append({
                "agent_id": entry["agent_id"],
                "agent_name": entry["agent_name"],
                "run_count": entry["run_count"],
                "task_count": entry["task_count"],
                "success_rate": round(entry["success_rate"], 4),
                "avg_score": round(entry["avg_score"], 4) if entry["avg_score"] is not None else None,
                "cost_per_success": entry["cost_per_success"],
                "roi": entry["roi"],
                "human_replacement": entry["human_replacement"],
                "time_cost": entry["time_cost"],
            })

        return {
            "benchmark_id": benchmark_id,
            "benchmark_name": leaderboard.get("benchmark_name"),
            "comparison": comparison,
        }

    @mcp.tool
    async def find_best_performer(benchmark: str, metric: str = "cost_per_success") -> dict:
        """Find the top-performing agent on a benchmark by a specific metric.
        `benchmark` is required (name or ID). `metric` can be: cost_per_success, roi,
        human_replacement, avg_score, success_rate. Returns {agent_id, agent_name, value}."""
        benchmark_id = await _resolve_benchmark_id(benchmark)

        leaderboard = await get(f"/api/v1/benchmarks/{benchmark_id}/leaderboard", params={
            "sort_by": metric,
            "sort_order": "asc" if metric in ["cost_per_success"] else "desc"
        })

        if not leaderboard.get("leaderboard"):
            return {"note": "no evaluation runs for this benchmark"}

        best = leaderboard["leaderboard"][0]
        return {
            "benchmark_id": benchmark_id,
            "benchmark_name": leaderboard.get("benchmark_name"),
            "metric": metric,
            "agent_id": best["agent_id"],
            "agent_name": best["agent_name"],
            "value": best.get(metric),
        }

    @mcp.tool
    async def get_leaderboard(benchmark: str, sort_by: str = "cost_per_success", sort_order: str = "asc") -> dict:
        """Get the full leaderboard for a benchmark. Returns agent rankings with technical
        and business metrics. `benchmark` is required (name or ID). `sort_by` can be:
        cost_per_success, roi, human_replacement, avg_score, success_rate."""
        benchmark_id = await _resolve_benchmark_id(benchmark)
        leaderboard = await get(f"/api/v1/benchmarks/{benchmark_id}/leaderboard", params={
            "sort_by": sort_by,
            "sort_order": sort_order
        })
        return leaderboard

    @mcp.tool
    async def run_benchmark(
        benchmark: str,
        agents: list[str],
    ) -> dict:
        """Run a batch evaluation on a benchmark with multiple agents.
        `benchmark` is required (name or ID). `agents` is a list of agent names or IDs.
        Returns the batch_id and initial status."""
        benchmark_id = await _resolve_benchmark_id(benchmark)

        # Resolve agent IDs
        from mcp_server.tools.evaluation import _resolve_agent_id
        agent_ids = []
        for agent in agents:
            agent_id = await _resolve_agent_id(agent)
            agent_ids.append(agent_id)

        # Create batch
        batch = await post("/api/v1/batches/", body={
            "benchmark_id": benchmark_id,
            "agent_ids": agent_ids,
        })

        return {
            "batch_id": batch.get("batch_id"),
            "status": "started",
            "agent_count": len(agent_ids),
            "benchmark_id": benchmark_id,
        }
