"""Raw API escape hatch (unstable, logged)."""
import json

import structlog

from mcp_server.client import request

log = structlog.get_logger("mcp.raw_api")


def register(mcp):
    # ponytail: raw_api is the deliberate escape hatch for power users.
    # Upgrade path: promote repeated raw_api patterns into domain tools
    # (run_evaluation, get_evaluation_status, ...). The log of raw_api calls
    # is the backlog of future domain tools.
    @mcp.tool
    async def raw_api(
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> str:
        """UNSTABLE escape hatch: issue any REST call to the backend.
        `method` (GET/POST/...), `path` (e.g. /api/v1/agents), optional
        `params` (query) and `body` (JSON). Prefer the domain tools; this
        may break if backend routes change. Every call is logged."""
        log.info("raw_api", method=method, path=path, params=params)
        result = await request(method, path, params=params, body=body)
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2, default=str)
