"""fd-bench command-line interface.

One binary, two modes — both drive the same MCP server subprocess:
  - one-shot: `fd-bench run-eval ...` (no LLM; calls one tool directly)
  - chat:     `fd-bench chat`        (Claude + MCP tools)
"""
import argparse
import asyncio
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fd-bench",
        description="Chat-first CLI for FD Open Bench (drives the MCP server).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # mcp serve [--http] [--port N]
    p_mcp = sub.add_parser("mcp", help="Run the MCP server.")
    mcp_sub = p_mcp.add_subparsers(dest="mcp_cmd", required=True)
    p_serve = mcp_sub.add_parser("serve", help="Serve MCP (stdio by default).")
    p_serve.add_argument("--http", action="store_true", help="Serve over HTTP.")
    p_serve.add_argument("--port", type=int, default=None)
    p_serve.set_defaults(func=cmd_serve)

    # one-shot tools (1:1 with domain tools)
    p_run = sub.add_parser("run-eval", help="Start an evaluation run.")
    p_run.add_argument("--agent", required=True)
    p_run.add_argument("--dataset", required=True)
    p_run.add_argument("--metrics", default=None, help="comma-separated metric names")
    p_run.set_defaults(func=cmd_run_eval)

    p_status = sub.add_parser("status", help="Get evaluation status.")
    p_status.add_argument("run_id")
    p_status.set_defaults(func=cmd_status)

    p_weak = sub.add_parser("weaknesses", help="Analyze weakest metrics.")
    p_weak.add_argument("--run-id", dest="run_id")
    p_weak.add_argument("--agent-id", dest="agent_id")
    p_weak.add_argument("--top", type=int, default=5)
    p_weak.set_defaults(func=cmd_weaknesses)

    p_cmp = sub.add_parser("compare", help="Compare agents on a metric.")
    p_cmp.add_argument("--agents", required=True, help="comma-separated agent IDs")
    p_cmp.add_argument("--metric", default="task_completion")
    p_cmp.set_defaults(func=cmd_compare)

    p_best = sub.add_parser("best", help="Find best performer on a dataset.")
    p_best.add_argument("--dataset", required=True)
    p_best.add_argument("--metric", default="task_completion")
    p_best.set_defaults(func=cmd_best)

    p_rep = sub.add_parser("report", help="Export a run report.")
    p_rep.add_argument("run_id")
    p_rep.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p_rep.set_defaults(func=cmd_report)

    p_raw = sub.add_parser("raw", help="Raw REST call (unstable escape hatch).")
    p_raw.add_argument("method")
    p_raw.add_argument("path")
    p_raw.add_argument("--params", default=None, help="JSON query params")
    p_raw.add_argument("--body", default=None, help="JSON body")
    p_raw.set_defaults(func=cmd_raw)

    p_chat = sub.add_parser("chat", help="Interactive chat with Claude + MCP tools.")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_serve(args) -> None:
    from mcp_server.main import run_server

    run_server(http=args.http, port=args.port)


def cmd_run_eval(args) -> None:
    metrics = args.metrics.split(",") if args.metrics else None
    _print(_call("run_evaluation", {
        "agent": args.agent, "dataset": args.dataset, "metrics": metrics}))


def cmd_status(args) -> None:
    _print(_call("get_evaluation_status", {"run_id": args.run_id}))


def cmd_weaknesses(args) -> None:
    _print(_call("analyze_weaknesses", {
        "run_id": args.run_id, "agent_id": args.agent_id, "top_n": args.top}))


def cmd_compare(args) -> None:
    agent_ids = [a for a in args.agents.split(",") if a]
    _print(_call("compare_agents", {"agent_ids": agent_ids, "metric": args.metric}))


def cmd_best(args) -> None:
    _print(_call("find_best_performer", {
        "dataset": args.dataset, "metric": args.metric}))


def cmd_report(args) -> None:
    _print(_call("export_report", {"run_id": args.run_id, "format": args.format}))


def cmd_raw(args) -> None:
    params = json.loads(args.params) if args.params else None
    body = json.loads(args.body) if args.body else None
    _print(_call("raw_api", {
        "method": args.method, "path": args.path, "params": params, "body": body}))


def cmd_chat(args) -> None:
    from fd_bench.chat import chat

    asyncio.run(chat())


def _call(name: str, arguments: dict):
    from fd_bench.runner import McpRunner

    async def _run():
        async with McpRunner() as runner:
            return await runner.call_tool(name, arguments)

    return asyncio.run(_run())


def _print(out) -> None:
    if isinstance(out, str):
        print(out)
    else:
        print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
