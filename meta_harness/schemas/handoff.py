"""HandoffRecord — the core data contract for PCG handoff audit trail.

``HandoffRecord`` extends ``BaseMessage`` so that it implements the message
protocol required by LangGraph's ``add_messages`` reducer. This allows the
``handoff_log`` field in ``ProjectCoordinationState`` to use ``add_messages``
for append-without-overwrite semantics. The ``id`` field (inherited from
``BaseMessage``) is derived from ``handoff_id`` to ensure handoff identity
and message-protocol identity are consistent.

``HandoffRecord`` is frozen (immutable) after construction. Fields that are
PCG-owned (``handoff_id``, ``langsmith_run_id``, ``status``, ``created_at``)
are populated by the ``process_handoff`` node, not by agent tools.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import Field, model_validator

from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus, Phase

__all__ = ["HandoffRecord", "AgentRole", "HandoffReason", "HandoffStatus", "Phase"]


class HandoffRecord(BaseMessage):
    """Immutable audit record for a single agent-to-agent handoff.

    Implements the ``BaseMessage`` protocol so it can be used with the
    ``add_messages`` reducer in ``ProjectCoordinationState.handoff_log``.

    Parameters
    ----------
    project_id : str
        Root project thread identifier.
    handoff_id : str
        Unique identifier for this handoff (doubles as ``id`` for message protocol).
    source_agent : AgentRole
        Agent that initiated the handoff.
    target_agent : AgentRole
        Agent that will receive the handoff.
    reason : HandoffReason
        Semantic verb for the transition type.
    brief : str
        Prose summary for the receiving agent.
    artifact_paths : list[str]
        References to artifacts included in the handoff (default ``[]``).
    langsmith_run_id : str | None
        LangSmith run ID for tracing correlation (default ``None``).
    status : HandoffStatus
        Lifecycle status — set by ``process_handoff`` (default ``queued``).
    created_at : datetime
        RFC3339-compatible timestamp (default: current UTC time).
    accepted : bool | None
        Acceptance stamp for QA gates (default ``None``).
    """

    # -- Message protocol --
    type: str = "handoff"

    # -- Base handoff fields (10) --
    project_id: str
    handoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: AgentRole
    target_agent: AgentRole
    reason: HandoffReason
    brief: str
    artifact_paths: list[str] = Field(default_factory=list)
    langsmith_run_id: str | None = None
    status: HandoffStatus = HandoffStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # -- Extension field (11th) --
    accepted: bool | None = None

    # -- BaseMessage plumbing --
    # ``content`` is required by BaseMessage; we derive it from ``brief``.
    content: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sync_message_fields(cls, data: Any) -> Any:
        """Derive ``content`` from ``brief`` and ``id`` from ``handoff_id``."""
        if isinstance(data, dict):
            # Set content from brief if not explicitly provided
            if not data.get("content"):
                data["content"] = data.get("brief", "")
            # Set id from handoff_id for message protocol
            if not data.get("id"):
                data["id"] = data.get("handoff_id", str(uuid.uuid4()))
        return data

    model_config = {"frozen": True}
