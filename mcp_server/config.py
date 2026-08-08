"""Shared config for the MCP server and the fd-bench CLI (stdlib only)."""
import os

# Backend FastAPI base URL. The app's own default is 8999 (see app/core/config.py).
FD_BENCH_API_URL = os.getenv("FD_BENCH_API_URL", "http://localhost:8999")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
