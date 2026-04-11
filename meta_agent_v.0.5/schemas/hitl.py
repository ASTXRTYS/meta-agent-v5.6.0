"""Lightweight types for standard HITL (Human-in-the-Loop) interrupt payloads.

Extracted from the tools namespace so UI clients can statically parse 
Interrupt endpoints (like approval or command execution modals) over the API.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field
from typing_extensions import NotRequired, TypedDict


class ApprovalRequest(TypedDict):
    """Payload emitted when the agent requests user approval for an artifact."""

    action: Literal["request_approval"]
    artifact_path: Annotated[str, Field(description="Path to the artifact being reviewed")]
    summary: Annotated[str, Field(description="Summary of what needs approval")]
    stage: Annotated[str, Field(description="Current workflow stage")]


class EvalApprovalRequest(TypedDict):
    """Payload emitted when the agent requests user approval for an eval suite."""

    action: Literal["request_eval_approval"]
    eval_suite_path: Annotated[str, Field(description="Path to the evaluation suite JSON")]
    summary: Annotated[str, Field(description="Summary of the eval suite")]
    stage: Annotated[str, Field(description="Current workflow stage")]


class ExecuteCommandRequest(TypedDict):
    """Payload emitted when the agent requests to run a shell command."""

    action: Literal["execute_command"]
    command: Annotated[str, Field(description="The shell command string")]
    working_dir: Annotated[str, Field(description="Target directory for execution")]
    timeout: Annotated[int, Field(description="Timeout in seconds")]
    warnings: NotRequired[Annotated[list[str], Field(description="Security warnings from safety checks")]]


class HitlResponse(TypedDict):
    """Standardized response provided by the UI when resuming a HITL pause."""

    action: NotRequired[Annotated[str, Field(description="Approval action (e.g., approved, rejected, revised)")]]
    status: NotRequired[Annotated[str, Field(description="Fallback alias for action")]]
    decision: NotRequired[Annotated[str, Field(description="Fallback alias for action")]]
    comments: NotRequired[Annotated[str, Field(description="User feedback or revision instructions")]]
    comment: NotRequired[Annotated[str, Field(description="Fallback alias for comments")]]
    feedback: NotRequired[Annotated[str, Field(description="Fallback alias for comments")]]
