"""PCG state schemas for the Project Coordination Graph.

Defines ``ProjectCoordinationState`` (the full PCG state), plus
``ProjectCoordinationInput``, ``ProjectCoordinationOutput``, and
``ProjectCoordinationContext`` for graph boundary control.
"""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from meta_harness.schemas.enums import AgentRole, Phase
from meta_harness.schemas.handoff import HandoffRecord

__all__ = [
    "ProjectCoordinationState",
    "ProjectCoordinationInput",
    "ProjectCoordinationOutput",
    "ProjectCoordinationContext",
]


class ProjectCoordinationState(TypedDict):
    """Full state schema for the Project Coordination Graph.

    Carries only deterministic coordination data — no agent cognition,
    no artifact content, no specialist messages.

    Key invariants
    --------------
    - ``messages`` is the user-facing I/O channel (lifecycle bookends only).
    - ``handoff_log`` uses ``add_messages`` for append-without-overwrite.
    - ``pending_handoff`` is an execution cursor, not a data store.
    - Child agents never see any key except ``messages``.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    """User-facing I/O channel.  Accumulates stakeholder input and PM's
    final product response only — lifecycle bookends."""

    project_id: str
    """Root thread identifier; doubles as project namespace."""

    current_phase: Phase
    """Current project phase; middleware reads this for gate dispatch."""

    current_agent: AgentRole
    """Which role graph is currently active."""

    handoff_log: Annotated[list[HandoffRecord], add_messages]
    """Append-only coordination audit trail.  Uses ``add_messages`` reducer
    for its append-without-overwrite semantics."""

    pending_handoff: HandoffRecord | None
    """Active handoff cursor — set by ``process_handoff``, consumed by
    ``run_agent``, cleared on completion."""


class ProjectCoordinationInput(TypedDict):
    """Input schema for child graph node mounting.

    Exposes only ``messages`` to prevent PCG-private keys from leaking
    into child agent input.  Set via ``input_schema=`` on ``add_node``.
    """

    messages: Annotated[list[AnyMessage], add_messages]


class ProjectCoordinationOutput(TypedDict):
    """Output schema for the PCG graph.

    Exposes the user-facing messages channel so that final responses
    propagate to the caller.
    """

    messages: Annotated[list[AnyMessage], add_messages]


class ProjectCoordinationContext(TypedDict):
    """Context schema for graph-level configuration (checkpointer, store).

    Passed to ``StateGraph(..., config_schema=ProjectCoordinationContext)``
    for type-safe access to runtime config values.
    """

    project_id: str
    """Project identifier propagated via config for runtime access."""
