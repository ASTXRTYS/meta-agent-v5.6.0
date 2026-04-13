"""Foundation schemas for the Meta Harness coordination layer.

Re-exports all public types for convenient import::

    from meta_harness.schemas import HandoffRecord, AgentRole, Phase
"""

from meta_harness.schemas.enums import (
    AgentRole,
    HandoffReason,
    HandoffStatus,
    Phase,
)
from meta_harness.schemas.handoff import HandoffRecord
from meta_harness.schemas.state import (
    ProjectCoordinationContext,
    ProjectCoordinationInput,
    ProjectCoordinationOutput,
    ProjectCoordinationState,
)

__all__ = [
    "AgentRole",
    "HandoffReason",
    "HandoffStatus",
    "Phase",
    "HandoffRecord",
    "ProjectCoordinationState",
    "ProjectCoordinationInput",
    "ProjectCoordinationOutput",
    "ProjectCoordinationContext",
]
