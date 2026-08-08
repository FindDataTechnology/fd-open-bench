"""HTTP client wrapping the FD Open Bench REST API (httpx.AsyncClient)."""
import httpx

from mcp_server.config import FD_BENCH_API_URL

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=FD_BENCH_API_URL,
            timeout=60.0,
            follow_redirects=True,
            trust_env=False,  # avoid proxy interception on localhost calls
        )
    return _client


async def request(
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
):
    """Issue a REST call to the backend; return parsed JSON ({} on 204)."""
    c = await _get_client()
    r = await c.request(method, path, params=params, json=body)
    r.raise_for_status()
    if r.status_code == 204 or not r.content:
        return {}
    return r.json()


async def get(path: str, params: dict | None = None):
    return await request("GET", path, params=params)


async def post(path: str, body: dict | None = None):
    return await request("POST", path, body=body)
