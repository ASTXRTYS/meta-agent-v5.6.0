"""Tracing foundation for the meta-agent system.

Spec References: Sections 18.1-18.3, 18.5.1, 18.5.3

LangSmith auto-tracing is enabled via LANGSMITH_TRACING=true.
This module provides @traceable decorator stubs, Gap 1/3 span stubs,
and trace metadata tag constants.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Trace metadata tag constants — Section 18.3
# ---------------------------------------------------------------------------

TRACE_TAGS = {
    "stage": str,
    "artifact_type": str,
    "subagent": str,
    "participation_mode": str,
    "eval_phase": str,
    "eval_run_id": str,
    "commit_hash": str,
}


# ---------------------------------------------------------------------------
# @traceable decorator stub — Section 18.2
# ---------------------------------------------------------------------------

def traceable(
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator stub for LangSmith custom spans.

    When langsmith is installed and LANGSMITH_TRACING=true, this wraps
    the function in a custom trace span. Otherwise, it's a passthrough.
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                from langsmith import traceable as ls_traceable
                traced = ls_traceable(
                    name=name or fn.__name__,
                    metadata=metadata or {},
                )(fn)
                return traced(*args, **kwargs)
            except ImportError:
                return fn(*args, **kwargs)
        return wrapper  # type: ignore[return-value]
    return decorator


# ---------------------------------------------------------------------------
# Gap 1: Agent State Loading spans — Section 18.5.1
# ---------------------------------------------------------------------------

@traceable(name="prepare_agent_state")
def prepare_agent_state(
    agent_name: str,
    state_keys: list[str] | None = None,
    artifact_paths: list[str] | None = None,
    skill_dirs: list[str] | None = None,
    tools: list[str] | None = None,
) -> dict[str, Any]:
    """Stub for prepare_{agent_name}_state trace span.

    Every sub-agent invocation emits this span with:
    - state keys populated
    - artifact paths loaded as context
    - skill directories available
    - tool set provisioned
    """
    return {
        "agent_name": agent_name,
        "state_keys": state_keys or [],
        "artifact_paths": artifact_paths or [],
        "skill_dirs": skill_dirs or [],
        "tools": tools or [],
    }


# ---------------------------------------------------------------------------
# Gap 3: Delegation Decision spans — Section 18.5.3
# ---------------------------------------------------------------------------

@traceable(name="delegation_decision")
def delegation_decision(
    target_agent: str,
    delegation_reason: str,
    current_stage: str,
    task_description: str,
) -> dict[str, Any]:
    """Stub for delegation_decision trace span.

    Orchestrator emits this before each sub-agent invocation.
    """
    return {
        "target_agent": target_agent,
        "delegation_reason": delegation_reason,
        "current_stage": current_stage,
        "task_description": task_description,
    }
