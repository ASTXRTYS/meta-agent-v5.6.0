"""Core state model for the meta-agent system.

Spec References: Sections 4.1, 3.11, 5.8.1-5.8.3, 22.1
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional, TypedDict


# ---------------------------------------------------------------------------
# WorkflowStage enum — 10 stages per Section 3.11
# ---------------------------------------------------------------------------

class WorkflowStage(str, Enum):
    """Ten workflow stages of the meta-agent state machine."""

    INTAKE = "INTAKE"
    PRD_REVIEW = "PRD_REVIEW"
    RESEARCH = "RESEARCH"
    SPEC_GENERATION = "SPEC_GENERATION"
    SPEC_REVIEW = "SPEC_REVIEW"
    PLANNING = "PLANNING"
    PLAN_REVIEW = "PLAN_REVIEW"
    EXECUTION = "EXECUTION"
    EVALUATION = "EVALUATION"
    AUDIT = "AUDIT"


# ---------------------------------------------------------------------------
# VALID_TRANSITIONS — Section 3.11
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: set[tuple[str, str]] = {
    ("INTAKE", "PRD_REVIEW"),
    ("PRD_REVIEW", "RESEARCH"),
    ("PRD_REVIEW", "INTAKE"),
    ("RESEARCH", "SPEC_GENERATION"),
    ("RESEARCH", "PRD_REVIEW"),
    ("SPEC_GENERATION", "SPEC_REVIEW"),
    ("SPEC_REVIEW", "PLANNING"),
    ("SPEC_REVIEW", "SPEC_GENERATION"),
    ("SPEC_REVIEW", "RESEARCH"),
    ("PLANNING", "PLAN_REVIEW"),
    ("PLAN_REVIEW", "EXECUTION"),
    ("PLAN_REVIEW", "PLANNING"),
    ("EXECUTION", "EVALUATION"),
    ("EVALUATION", "EXECUTION"),
}


def is_valid_transition(from_stage: str, to_stage: str) -> bool:
    """Check if a stage transition is valid.

    Lateral AUDIT transitions are handled as a special case:
    any stage can transition to AUDIT, and AUDIT can return to
    its previous stage.
    """
    if to_stage == WorkflowStage.AUDIT.value:
        return True
    if from_stage == WorkflowStage.AUDIT.value:
        # AUDIT can return to any stage (the "previous" stage)
        return True
    return (from_stage, to_stage) in VALID_TRANSITIONS


# ---------------------------------------------------------------------------
# Structured log entry types — Sections 5.8.1-5.8.3
# ---------------------------------------------------------------------------

@dataclass
class DecisionEntry:
    """A recorded PM decision with rationale. Section 5.8.1."""

    timestamp: str
    stage: str
    decision: str
    rationale: str
    alternatives_considered: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        stage: str,
        decision: str,
        rationale: str,
        alternatives: list[str] | None = None,
    ) -> DecisionEntry:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            decision=decision,
            rationale=rationale,
            alternatives_considered=alternatives or [],
        )


@dataclass
class AssumptionEntry:
    """A recorded assumption with validation status. Section 5.8.2."""

    timestamp: str
    stage: str
    assumption: str
    status: str  # "open" | "validated" | "invalidated"
    resolution: str = ""

    VALID_STATUSES = {"open", "validated", "invalidated"}

    @classmethod
    def create(
        cls,
        stage: str,
        assumption: str,
        status: str = "open",
        resolution: str = "",
    ) -> AssumptionEntry:
        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {cls.VALID_STATUSES}"
            )
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            assumption=assumption,
            status=status,
            resolution=resolution,
        )


@dataclass
class ApprovalEntry:
    """A recorded approval event. Section 5.8.3."""

    timestamp: str
    stage: str
    artifact: str
    action: str  # "approved" | "revised" | "rejected"
    reviewer: str
    comments: str = ""

    VALID_ACTIONS = {"approved", "revised", "rejected"}

    @classmethod
    def create(
        cls,
        stage: str,
        artifact: str,
        action: str,
        reviewer: str,
        comments: str = "",
    ) -> ApprovalEntry:
        if action not in cls.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action '{action}'. Must be one of {cls.VALID_ACTIONS}"
            )
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            artifact=artifact,
            action=action,
            reviewer=reviewer,
            comments=comments,
        )


# ---------------------------------------------------------------------------
# MetaAgentState — Section 4.1
# ---------------------------------------------------------------------------

class MetaAgentState(TypedDict):
    """Complete state model for the meta-agent graph.

    Fields with ``Annotated[list, operator.add]`` use append-only
    accumulation via LangGraph reducers.
    """

    # Core fields
    messages: Annotated[list, operator.add]
    current_stage: str  # WorkflowStage enum value
    project_id: str
    current_prd_path: Optional[str]
    current_spec_path: Optional[str]
    current_plan_path: Optional[str]
    current_research_path: Optional[str]
    active_participation_mode: bool

    # Append-only structured logs
    decision_log: Annotated[list[DecisionEntry], operator.add]
    assumption_log: Annotated[list[AssumptionEntry], operator.add]
    approval_history: Annotated[list[ApprovalEntry], operator.add]
    artifacts_written: Annotated[list[str], operator.add]

    # v5.4 execution tracking fields
    execution_plan_tasks: list[dict]
    current_task_id: Optional[str]
    completed_task_ids: Annotated[list[str], operator.add]
    execution_summary: dict
    test_summary: dict
    progress_log: Annotated[list[str], operator.add]

    # v5.6 eval-related state fields
    eval_suites: list[str]  # Paths to eval suite JSON files
    eval_results: dict  # Mapping eval run IDs to results
    current_eval_phase: Optional[str]  # Current phase being evaluated
    verification_results: dict  # Verification verdicts by artifact type
    spec_generation_feedback_cycles: int  # Orchestrator-mediated research/spec retries
    pending_research_gap_request: Optional[str]  # Targeted research request from spec-writer


def create_initial_state(project_id: str) -> dict:
    """Create a default initial state for a new project."""
    return {
        "messages": [],
        "current_stage": WorkflowStage.INTAKE.value,
        "project_id": project_id,
        "current_prd_path": None,
        "current_spec_path": None,
        "current_plan_path": None,
        "current_research_path": None,
        "active_participation_mode": False,
        "decision_log": [],
        "assumption_log": [],
        "approval_history": [],
        "artifacts_written": [],
        "execution_plan_tasks": [],
        "current_task_id": None,
        "completed_task_ids": [],
        "execution_summary": {},
        "test_summary": {},
        "progress_log": [],
        "eval_suites": [],
        "eval_results": {},
        "current_eval_phase": None,
        "verification_results": {},
        "spec_generation_feedback_cycles": 0,
        "pending_research_gap_request": None,
    }
