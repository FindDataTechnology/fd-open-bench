"""Build an adapter instance from an Agent record (adapter_type + config)."""

import importlib

from app.adapters.http_adapter import HttpAgentAdapter


def build_adapter(agent) -> object:
    """Instantiate the adapter for an agent.

    - 'http':      config = {"base_url": "http://host:port", ...}
    - 'openai':    config = {"model": ..., "client": ...}
    - 'langchain': config = {"agent": <already-built agent>, ...}
    - 'custom':    config = {"class": "pkg.module:ClassName", "kwargs": {...}}
    """
    t = agent.adapter_type
    cfg = dict(agent.config or {})

    if t == "http":
        return HttpAgentAdapter(**cfg)

    if t == "openai":
        from app.adapters.openai_adapter import OpenAIAgentAdapter
        return OpenAIAgentAdapter(client=cfg.pop("client", None), **cfg)

    if t == "langchain":
        from app.adapters.langchain_adapter import LangChainAgentAdapter
        return LangChainAgentAdapter(agent=cfg.pop("agent", None), **cfg)

    # custom: import wrapper class by dotted path
    mod, _, cls = cfg["class"].rpartition(":")
    return getattr(importlib.import_module(mod), cls)(**cfg.get("kwargs", {}))
