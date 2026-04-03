"""Eval test utilities — helpers for running agent scenarios and capturing trajectories.

REPLACES: tests/unit/test_evals.py (partial — run_agent_scenario stub)
"""

from __future__ import annotations

from typing import Any


def run_agent_scenario(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
    """Run the meta-agent with given messages and return the final state.

    Args:
        messages: List of {"role": "user", "content": "..."} dicts.
        **kwargs: Passed to graph.invoke config.  Accepts ``thread_id``
            (pulled out and placed inside ``configurable``) and any other
            keys forwarded to the LangGraph config dict.

    Returns:
        Final state dict from graph.invoke.
    """
    from meta_agent.graph import create_graph
    from meta_agent.state import create_initial_state
    from langchain_core.messages import HumanMessage

    graph = create_graph()
    state = create_initial_state(project_id=kwargs.pop("project_id", "eval-run"))
    state["messages"] = [
        HumanMessage(content=m["content"]) for m in messages if m.get("role") == "user"
    ]

    thread_id = kwargs.pop("thread_id", f"eval-{id(messages)}")
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    config.update(kwargs)

    return graph.invoke(state, config=config)
