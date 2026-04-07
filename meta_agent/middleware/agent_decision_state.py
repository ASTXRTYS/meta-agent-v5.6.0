"""AgentDecisionStateMiddleware — general-purpose decision/assumption state.

Provides ``decision_log``, ``assumption_log``, and ``approval_history``
state fields to ANY agent that needs structured decision tracking.

This is the lightweight, reusable counterpart to ``MetaAgentStateMiddleware``
(which carries the full PM orchestrator state).  Subagents like the
research-agent and verification-agent include this middleware so that
tools using ``InjectedState`` (e.g. ``record_decision_tool``,
``record_assumption_tool``) find the expected state fields.

Each agent instance gets its own isolated copy of these fields —
there is no collision with the PM agent's state.

Spec References: Sections 8.2, 8.3, 22.11
"""

from __future__ import annotations

import operator
# ``Any`` is unused here (no ``before_agent`` / hook signatures yet); kept in line
# with ``meta_state.py`` imports—remove in a typing cleanup pass if still unused.
from typing import Annotated, Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState


class AgentDecisionStateSchema(AgentState):
    """Minimal state extension for decision/assumption tracking.

    All list fields use ``Annotated[list, operator.add]`` for append-mode
    accumulation — ``Command(update={"decision_log": [entry]})`` appends
    rather than replaces.
    """

    decision_log: Annotated[list, operator.add]
    assumption_log: Annotated[list, operator.add]
    approval_history: Annotated[list, operator.add]


class AgentDecisionStateMiddleware(AgentMiddleware):
    """Middleware that merges decision/assumption state fields into any agent.

    Uses the same ``state_schema`` merging pattern as ``MetaAgentStateMiddleware``
    and ``TodoListMiddleware``.  The SDK's factory reads ``state_schema`` from
    each middleware and merges all fields via ``_resolve_schema``.

    This middleware is intentionally lightweight — it only declares state
    fields.  No ``before_model``, ``wrap_model_call``, or ``wrap_tool_call``
    hooks are needed.
    """

    state_schema = AgentDecisionStateSchema  # type: ignore[assignment]
