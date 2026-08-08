"""Spawn the fd-bench MCP server as a stdio subprocess and call its tools."""
import os

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


class McpRunner:
    """Thin async wrapper: spawn `fd-bench mcp serve`, call tools over stdio.

    One code path for one-shot and chat modes — and the same binary Claude
    Desktop runs, so the CLI exercises the real MCP transport.
    """

    def __init__(self, command: str | None = None):
        cmd = command or os.getenv("FD_BENCH_MCP_BIN", "fd-bench")
        self._client = Client(transport=StdioTransport(command=cmd, args=["mcp", "serve"]))

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc):
        await self._client.__aexit__(*exc)

    async def list_tools(self):
        return await self._client.list_tools()

    async def call_tool(self, name: str, arguments: dict | None = None):
        result = await self._client.call_tool(name, arguments or {})
        if getattr(result, "is_error", False):
            raise RuntimeError(f"tool '{name}' error: {getattr(result, 'content', None)}")
        return result.data
