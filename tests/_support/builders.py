"""Graph and state builder helpers for tests."""

from __future__ import annotations

from typing import Any

from meta_agent.state import MetaAgentState, WorkflowStage, create_initial_state


def build_minimal_state(**overrides: Any) -> dict:
    """Create a MetaAgentState dict with sensible defaults.

    Uses `create_initial_state` with a default project ID, then applies
    any caller-supplied overrides on top.

    Args:
        **overrides: Key/value pairs to override in the initial state.

    Returns:
        A dict conforming to MetaAgentState with all required keys.
    """
    state = create_initial_state(overrides.pop("project_id", "test-project"))
    state.update(overrides)
    return state


def build_graph(**kwargs: Any) -> Any:
    """Create the real graph from `meta_agent.graph.create_graph`.

    Wraps with sensible defaults so callers don't need to import directly.

    Args:
        **kwargs: Forwarded to `create_graph`.

    Returns:
        A compiled LangGraph StateGraph.
    """
    from meta_agent.graph import create_graph

    return create_graph(**kwargs)
