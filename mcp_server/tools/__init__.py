"""Register all MCP tool groups onto a FastMCP server instance."""


def register_all(mcp):
    from mcp_server.tools import evaluation, analysis, reporting, raw

    for mod in (evaluation, analysis, reporting, raw):
        mod.register(mcp)
