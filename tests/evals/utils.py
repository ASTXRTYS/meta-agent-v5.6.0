"""Eval test utilities — helpers for running agent scenarios and capturing trajectories."""

from __future__ import annotations

from typing import Any


def run_agent_scenario(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
    """Run the meta-agent with given messages and return trajectory.

    Stub — O6 (Live Behavioral Evals) will implement.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        **kwargs: Additional configuration for the agent run.

    Returns:
        A dict containing the agent trajectory and results.

    Raises:
        NotImplementedError: Always — this is a stub for O6.
    """
    raise NotImplementedError("O6 will implement run_agent_scenario")
