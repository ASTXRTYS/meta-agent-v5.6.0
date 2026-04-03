"""Contract tests for MetaAgentState schema.

Validates that the state TypedDict, WorkflowStage enum, transition map,
and create_initial_state() factory all conform to spec.
No model calls, no I/O, no tmp_path.
"""

from __future__ import annotations

import pytest

from meta_agent.state import (
    MetaAgentState,
    WorkflowStage,
    VALID_TRANSITIONS,
    create_initial_state,
    is_valid_transition,
)


# ---------------------------------------------------------------------------
# MetaAgentState fields — Section 4.1
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestMetaAgentStateFields:
    """MetaAgentState TypedDict has all required annotations."""

    @pytest.fixture(scope="class")
    def annotations(self):
        return MetaAgentState.__annotations__

    def test_has_core_fields(self, annotations):
        core = {
            "messages", "current_stage", "project_id",
            "current_prd_path", "current_spec_path",
            "current_plan_path", "current_research_path",
            "active_participation_mode",
        }
        assert core.issubset(set(annotations.keys())), (
            f"Missing core fields: {core - set(annotations.keys())}"
        )

    def test_has_structured_logs(self, annotations):
        logs = {
            "decision_log", "assumption_log",
            "approval_history", "artifacts_written",
        }
        assert logs.issubset(set(annotations.keys())), (
            f"Missing log fields: {logs - set(annotations.keys())}"
        )

    def test_has_execution_tracking(self, annotations):
        execution = {
            "execution_plan_tasks", "current_task_id",
            "completed_task_ids", "execution_summary",
            "test_summary", "progress_log",
        }
        assert execution.issubset(set(annotations.keys())), (
            f"Missing execution fields: {execution - set(annotations.keys())}"
        )

    def test_has_eval_fields(self, annotations):
        eval_fields = {
            "eval_suites", "eval_results",
            "current_eval_phase", "verification_results",
            "spec_generation_feedback_cycles",
            "pending_research_gap_request",
        }
        assert eval_fields.issubset(set(annotations.keys())), (
            f"Missing eval fields: {eval_fields - set(annotations.keys())}"
        )


# ---------------------------------------------------------------------------
# WorkflowStage enum — Section 3.11
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestWorkflowStage:
    """WorkflowStage enum matches the spec."""

    def test_stage_count(self):
        assert len(WorkflowStage) == 10

    def test_expected_stages(self):
        expected = {
            "INTAKE", "PRD_REVIEW", "RESEARCH", "SPEC_GENERATION",
            "SPEC_REVIEW", "PLANNING", "PLAN_REVIEW", "EXECUTION",
            "EVALUATION", "AUDIT",
        }
        actual = {s.value for s in WorkflowStage}
        assert expected == actual

    def test_str_enum_values(self):
        """Each member's value equals its name (str enum pattern)."""
        for stage in WorkflowStage:
            assert stage.value == stage.name


# ---------------------------------------------------------------------------
# VALID_TRANSITIONS — Section 3.11
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestValidTransitions:
    """Transition map includes the core happy path and key rework loops."""

    def test_happy_path(self):
        happy = [
            ("INTAKE", "PRD_REVIEW"),
            ("PRD_REVIEW", "RESEARCH"),
            ("RESEARCH", "SPEC_GENERATION"),
            ("SPEC_GENERATION", "SPEC_REVIEW"),
            ("SPEC_REVIEW", "PLANNING"),
            ("PLANNING", "PLAN_REVIEW"),
            ("PLAN_REVIEW", "EXECUTION"),
            ("EXECUTION", "EVALUATION"),
        ]
        for pair in happy:
            assert pair in VALID_TRANSITIONS, f"Missing happy-path transition: {pair}"

    def test_rework_loops(self):
        rework = [
            ("PRD_REVIEW", "INTAKE"),
            ("RESEARCH", "PRD_REVIEW"),
            ("SPEC_REVIEW", "SPEC_GENERATION"),
            ("SPEC_REVIEW", "RESEARCH"),
            ("PLAN_REVIEW", "PLANNING"),
            ("EVALUATION", "EXECUTION"),
        ]
        for pair in rework:
            assert pair in VALID_TRANSITIONS, f"Missing rework transition: {pair}"

    def test_audit_lateral_any_to_audit(self):
        """Any stage can transition to AUDIT (special-case in is_valid_transition)."""
        for stage in WorkflowStage:
            assert is_valid_transition(stage.value, "AUDIT")

    def test_audit_lateral_audit_to_any(self):
        """AUDIT can return to any stage."""
        for stage in WorkflowStage:
            assert is_valid_transition("AUDIT", stage.value)


# ---------------------------------------------------------------------------
# create_initial_state() — factory defaults
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestCreateInitialState:
    """create_initial_state() returns spec-compliant defaults."""

    @pytest.fixture(scope="class")
    def state(self):
        return create_initial_state(project_id="test-project")

    def test_stage_is_intake(self, state):
        assert state["current_stage"] == "INTAKE"

    def test_messages_empty(self, state):
        assert state["messages"] == []

    def test_logs_empty(self, state):
        assert state["decision_log"] == []
        assert state["assumption_log"] == []
        assert state["approval_history"] == []
        assert state["artifacts_written"] == []

    def test_project_id_set(self, state):
        assert state["project_id"] == "test-project"

    def test_all_state_keys_present(self, state):
        """Every annotated field has a default in create_initial_state."""
        for key in MetaAgentState.__annotations__:
            assert key in state, f"create_initial_state missing key: {key}"
