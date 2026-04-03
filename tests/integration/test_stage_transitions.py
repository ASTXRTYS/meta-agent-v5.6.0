# REPLACES: tests/unit/test_state.py::TestWorkflowStageTransitions (partial)
# REPLACES: tests/unit/test_stages.py::TestIntakeStage (partial — shape checks)
"""Integration tests for the stage transition system.

Verifies WorkflowStage enum, VALID_TRANSITIONS, transition_stage(),
create_initial_state(), and stage handler classes.
"""

from __future__ import annotations

import pytest

from meta_agent.state import WorkflowStage, VALID_TRANSITIONS, create_initial_state
from meta_agent.stages.intake import IntakeStage
from meta_agent.stages.prd_review import PrdReviewStage
from meta_agent.tools import transition_stage, InvalidTransitionError, PreconditionError


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Tests: WorkflowStage enum
# ---------------------------------------------------------------------------


class TestWorkflowStageEnum:
    """Verify the WorkflowStage enum has the correct members."""

    EXPECTED_STAGES = {
        "INTAKE",
        "PRD_REVIEW",
        "RESEARCH",
        "SPEC_GENERATION",
        "SPEC_REVIEW",
        "PLANNING",
        "PLAN_REVIEW",
        "EXECUTION",
        "EVALUATION",
        "AUDIT",
    }

    def test_has_all_10_stages(self):
        actual = {s.value for s in WorkflowStage}
        assert actual == self.EXPECTED_STAGES

    def test_stage_count(self):
        assert len(WorkflowStage) == 10

    def test_str_enum_values_match_names(self):
        for stage in WorkflowStage:
            assert stage.value == stage.name


# ---------------------------------------------------------------------------
# Tests: VALID_TRANSITIONS
# ---------------------------------------------------------------------------


class TestValidTransitions:
    """Verify the happy path exists in VALID_TRANSITIONS."""

    HAPPY_PATH = [
        ("INTAKE", "PRD_REVIEW"),
        ("PRD_REVIEW", "RESEARCH"),
        ("RESEARCH", "SPEC_GENERATION"),
        ("SPEC_GENERATION", "SPEC_REVIEW"),
        ("SPEC_REVIEW", "PLANNING"),
        ("PLANNING", "PLAN_REVIEW"),
        ("PLAN_REVIEW", "EXECUTION"),
    ]

    def test_happy_path_transitions_all_valid(self):
        for from_stage, to_stage in self.HAPPY_PATH:
            assert (from_stage, to_stage) in VALID_TRANSITIONS, (
                f"Missing happy-path transition: {from_stage} → {to_stage}"
            )

    def test_no_self_transitions(self):
        for from_stage, to_stage in VALID_TRANSITIONS:
            assert from_stage != to_stage, (
                f"Self-transition found: {from_stage} → {to_stage}"
            )

    def test_all_entries_reference_valid_stages(self):
        valid_names = {s.value for s in WorkflowStage}
        for from_stage, to_stage in VALID_TRANSITIONS:
            assert from_stage in valid_names, f"Unknown stage: {from_stage}"
            assert to_stage in valid_names, f"Unknown stage: {to_stage}"


# ---------------------------------------------------------------------------
# Tests: create_initial_state
# ---------------------------------------------------------------------------


class TestCreateInitialState:
    """Verify create_initial_state() produces a valid starting state."""

    def test_starts_at_intake(self):
        state = create_initial_state("test-project")
        assert state["current_stage"] == "INTAKE"

    def test_project_id_set(self):
        state = create_initial_state("my-project")
        assert state["project_id"] == "my-project"

    def test_messages_empty(self):
        state = create_initial_state("test")
        assert state["messages"] == []

    def test_all_log_lists_empty(self):
        state = create_initial_state("test")
        for key in ("decision_log", "assumption_log", "approval_history",
                     "artifacts_written", "progress_log"):
            assert state[key] == [], f"{key} should start empty"


# ---------------------------------------------------------------------------
# Tests: transition_stage (raw function)
# ---------------------------------------------------------------------------


class TestTransitionStage:
    """Verify transition_stage validates and applies transitions."""

    def test_valid_transition_updates_stage(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/tmp/prd.md"
        result = transition_stage(state, "PRD_REVIEW", "PRD drafted")
        assert result["current_stage"] == "PRD_REVIEW"

    def test_invalid_transition_raises(self):
        state = create_initial_state("test")
        with pytest.raises(InvalidTransitionError):
            transition_stage(state, "EXECUTION", "skip ahead")

    def test_invalid_stage_name_raises(self):
        state = create_initial_state("test")
        with pytest.raises(InvalidTransitionError):
            transition_stage(state, "NONEXISTENT", "bad stage")


# ---------------------------------------------------------------------------
# Tests: Stage handler classes (shape checks)
# ---------------------------------------------------------------------------


class TestStageHandlerShapes:
    """Verify IntakeStage and PrdReviewStage are instantiable with expected API."""

    def test_intake_stage_instantiates(self):
        stage = IntakeStage(project_dir="/tmp/p", project_id="test")
        assert stage.project_id == "test"

    def test_intake_stage_has_gate_methods(self):
        stage = IntakeStage(project_dir="/tmp/p", project_id="test")
        assert callable(stage.check_entry_conditions)
        assert callable(stage.check_exit_conditions)

    def test_prd_review_stage_instantiates(self):
        stage = PrdReviewStage(project_dir="/tmp/p", project_id="test")
        assert stage.project_id == "test"

    def test_prd_review_stage_has_gate_methods(self):
        stage = PrdReviewStage(project_dir="/tmp/p", project_id="test")
        assert callable(stage.check_entry_conditions)
        assert callable(stage.check_exit_conditions)
