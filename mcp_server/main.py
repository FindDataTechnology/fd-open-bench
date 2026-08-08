"""FastMCP server for FD Open Bench: domain tools + raw_api over stdio/HTTP."""
import logging
import os
import sys

import structlog
from fastmcp import FastMCP

from mcp_server.tools import register_all

# Configure stdlib logging to stderr — keeps stdout clean for JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)

# Configure structlog to stderr too (raw_api tool uses structlog)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

mcp = FastMCP("fd-open-bench")
register_all(mcp)


def run_server(http: bool = False, port: int | None = None) -> None:
    """Run the MCP server. stdio by default; streamable-HTTP if http=True."""
    if http:
        mcp.run(transport="http", port=port or 8998)
    else:
        mcp.run()  # stdio


def main() -> None:
    http = bool(os.getenv("MCP_HTTP"))
    port = int(os.getenv("MCP_HTTP_PORT", "0")) or None
    run_server(http=http, port=port)


if __name__ == "__main__":
    main()
