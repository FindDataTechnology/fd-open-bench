"""Optional single-token API guard.

fd-open-bench is an internal tool: no multi-user accounts, no login flow.
If ``FD_BENCH_API_TOKEN`` is set, every API request must carry
``Authorization: Bearer <token>``. Empty token (default) = open access,
which is the expected setup for local usage.
"""

import secrets

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


async def verify_api_token(request: Request) -> None:
    """FastAPI dependency enforcing the optional single API token."""
    expected = get_settings().fd_bench_api_token
    if not expected:
        return  # open access (default for local internal tool)

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and secrets.compare_digest(
        auth_header[len("Bearer "):], expected
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API token",
        headers={"WWW-Authenticate": "Bearer"},
    )
