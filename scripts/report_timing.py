"""Print per-module timing breakdown for an evaluation run.

Usage:
    python3 scripts/report_timing.py <run_id>

Reads evaluation_results for the run from the DB, decompresses each trace,
and aggregates llm/tool/retriever/idle durations across goldens.
"""

import sys
from statistics import mean

from sqlalchemy import select

from app.database import SessionLocal
from app.models.evaluation_result import EvaluationResult
from app.models.trace import Trace
from app.services.token_aggregation import TimingMetricsService
from app.utils.compression import decompress_trace


def run_report(run_id: str) -> None:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(EvaluationResult).where(EvaluationResult.run_id == run_id)
        ).scalars().all()
    finally:
        db.close()

    if not rows:
        print(f"no evaluation results for run {run_id}")
        sys.exit(1)

    timings = []
    print(f"run {run_id}: {len(rows)} result(s)\n")
    print(f"{'golden':<12} {'total':>8} {'llm':>8} {'tool':>8} {'retri':>8} {'idle':>8}  tokens")
    for res in rows:
        trace = Trace(**decompress_trace(res.trace)) if res.trace else None
        if not trace:
            print(f"{res.golden_id:<12} {'(no trace)':>8}")
            continue
        perf = TimingMetricsService().get_performance_summary(trace)
        t = perf["timing"]
        timings.append((perf, t))
        print(
            f"{res.golden_id:<12} {t['total_duration_ms']:8.1f} "
            f"{t['llm_duration_ms']:8.1f} {t['tool_duration_ms']:8.1f} "
            f"{t['retriever_duration_ms']:8.1f} {t['idle_time_ms']:8.1f}  "
            f"{perf['token_usage']['total_tokens']}"
        )

    if not timings:
        sys.exit(1)

    def avg(key):
        return mean(t[key] for _, t in timings)

    total = avg("total_duration_ms")
    print("\n=== average (per golden) ===")
    print(f"  total : {total:8.1f} ms")
    for key, label in (("llm_duration_ms", "llm"), ("tool_duration_ms", "tool"),
                       ("retriever_duration_ms", "retriever"), ("idle_time_ms", "idle")):
        v = avg(key)
        print(f"  {label:<10}: {v:8.1f} ms  ({v / total * 100:5.1f}%)" if total else f"  {label}: {v}")
    calls = {k: mean(p[k] for p, _ in timings) for k in ("llm_call_count", "tool_call_count")}
    print(f"\n  avg calls: llm={calls['llm_call_count']:.1f} tool={calls['tool_call_count']:.1f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    run_report(sys.argv[1])
