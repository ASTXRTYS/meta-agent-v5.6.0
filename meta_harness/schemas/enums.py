"""Foundation enums for the Meta Harness coordination layer.

These enums define the vocabulary for agent roles, project phases,
handoff reasons, and handoff statuses used throughout the Project
Coordination Graph and handoff protocol.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "AgentRole",
    "Phase",
    "HandoffReason",
    "HandoffStatus",
]


class AgentRole(StrEnum):
    """Identifies one of the 7 peer Deep Agent roles mounted under the PCG.

    Values use underscores to match the ``current_agent`` field in
    ``ProjectCoordinationState`` and the checkpoint namespace strings.
    """

    PROJECT_MANAGER = "project_manager"
    HARNESS_ENGINEER = "harness_engineer"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    PLANNER = "planner"
    DEVELOPER = "developer"
    EVALUATOR = "evaluator"


class Phase(StrEnum):
    """Project lifecycle phases tracked by the PCG ``current_phase`` field."""

    SCOPING = "scoping"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    ACCEPTANCE = "acceptance"


class HandoffReason(StrEnum):
    """Semantic verb for a handoff — encodes the *type* of transition.

    Middleware dispatches on the ``(source_agent, target_agent, reason)``
    triple to determine which gate logic to apply.
    """

    DELIVER = "deliver"
    RETURN = "return"
    SUBMIT = "submit"
    CONSULT = "consult"
    ANNOUNCE = "announce"
    COORDINATE = "coordinate"
    QUESTION = "question"


class HandoffStatus(StrEnum):
    """Lifecycle status of a handoff record.

    Set by the PCG ``process_handoff`` node, not by agent tools.
    """

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
