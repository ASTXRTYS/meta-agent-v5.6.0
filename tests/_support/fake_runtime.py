"""Minimal ToolRuntime builders for tests.

Modeled after the SDK pattern in
.reference/deepagents/libs/deepagents/tests/unit_tests/backends/test_composite_backend.py
"""

from __future__ import annotations

from typing import Any


def make_runtime(tid: str = "tc", *, store: Any = None) -> Any:
    """Create a minimal ToolRuntime for unit tests.

    Args:
        tid: Tool call ID to embed in the runtime.
        store: Optional LangGraph store instance. Defaults to InMemoryStore.

    Returns:
        A ToolRuntime instance with sensible test defaults.
    """
    from langchain.tools import ToolRuntime
    from langgraph.store.memory import InMemoryStore

    return ToolRuntime(
        state={"messages": [], "files": {}},
        context=None,
        tool_call_id=tid,
        store=store or InMemoryStore(),
        stream_writer=lambda _: None,
        config={},
    )
