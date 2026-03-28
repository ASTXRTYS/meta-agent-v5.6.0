"""Unit tests for meta_agent.state module."""

from __future__ import annotations

import pytest

from meta_agent.state import (
    ApprovalEntry,
    AssumptionEntry,
    DecisionEntry,
    MetaAgentState,
    VALID_TRANSITIONS,
    WorkflowStage,
    create_initial_state,
    is_valid_transition,
)


class TestWorkflowStage:
    """Tests for the WorkflowStage enum."""

    def test_has_ten_stages(self):
        assert len(WorkflowStage) == 10

    def test_all_stages_present(self):
        expected = {
            "INTAKE", "PRD_REVIEW", "RESEARCH", "SPEC_GENERATION",
            "SPEC_REVIEW", "PLANNING", "PLAN_REVIEW", "EXECUTION",
            "EVALUATION", "AUDIT",
        }
        actual = {s.value for s in WorkflowStage}
        assert actual == expected

    def test_string_value(self):
        assert WorkflowStage.INTAKE.value == "INTAKE"
        assert WorkflowStage.EXECUTION.value == "EXECUTION"

    def test_is_string_enum(self):
        assert isinstance(WorkflowStage.INTAKE, str)


class TestValidTransitions:
    """Tests for VALID_TRANSITIONS set."""

    def test_has_14_transitions(self):
        assert len(VALID_TRANSITIONS) == 14

    def test_forward_transitions_exist(self):
        assert ("INTAKE", "PRD_REVIEW") in VALID_TRANSITIONS
        assert ("PRD_REVIEW", "RESEARCH") in VALID_TRANSITIONS
        assert ("RESEARCH", "SPEC_GENERATION") in VALID_TRANSITIONS
        assert ("EXECUTION", "EVALUATION") in VALID_TRANSITIONS

    def test_backward_transitions_exist(self):
        assert ("PRD_REVIEW", "INTAKE") in VALID_TRANSITIONS
        assert ("SPEC_REVIEW", "SPEC_GENERATION") in VALID_TRANSITIONS
        assert ("PLAN_REVIEW", "PLANNING") in VALID_TRANSITIONS

    def test_invalid_transition_not_in_set(self):
        assert ("INTAKE", "EXECUTION") not in VALID_TRANSITIONS

    def test_is_valid_transition_normal(self):
        assert is_valid_transition("INTAKE", "PRD_REVIEW")
        assert not is_valid_transition("INTAKE", "EXECUTION")

    def test_is_valid_transition_audit_lateral(self):
        # Any stage can go to AUDIT
        for stage in WorkflowStage:
            assert is_valid_transition(stage.value, "AUDIT")
        # AUDIT can return to any stage
        for stage in WorkflowStage:
            if stage != WorkflowStage.AUDIT:
                assert is_valid_transition("AUDIT", stage.value)


class TestDecisionEntry:
    """Tests for DecisionEntry dataclass."""

    def test_create(self):
        entry = DecisionEntry.create(
            stage="INTAKE",
            decision="Use binary scoring",
            rationale="Behavior is deterministic",
            alternatives=["Likert", "LLM-judge"],
        )
        assert entry.stage == "INTAKE"
        assert entry.decision == "Use binary scoring"
        assert entry.rationale == "Behavior is deterministic"
        assert entry.alternatives_considered == ["Likert", "LLM-judge"]
        assert entry.timestamp  # should be non-empty

    def test_create_no_alternatives(self):
        entry = DecisionEntry.create(
            stage="RESEARCH",
            decision="Delegate to research-agent",
            rationale="Standard research flow",
        )
        assert entry.alternatives_considered == []


class TestAssumptionEntry:
    """Tests for AssumptionEntry dataclass."""

    def test_create_open(self):
        entry = AssumptionEntry.create(
            stage="INTAKE",
            assumption="User wants a CLI tool",
        )
        assert entry.status == "open"
        assert entry.resolution == ""

    def test_create_validated(self):
        entry = AssumptionEntry.create(
            stage="PRD_REVIEW",
            assumption="User wants a CLI tool",
            status="validated",
            resolution="User confirmed in review",
        )
        assert entry.status == "validated"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            AssumptionEntry.create(
                stage="INTAKE",
                assumption="test",
                status="invalid",
            )


class TestApprovalEntry:
    """Tests for ApprovalEntry dataclass."""

    def test_create_approved(self):
        entry = ApprovalEntry.create(
            stage="PRD_REVIEW",
            artifact="prd.md",
            action="approved",
            reviewer="user",
            comments="Looks good",
        )
        assert entry.action == "approved"
        assert entry.reviewer == "user"

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError, match="Invalid action"):
            ApprovalEntry.create(
                stage="PRD_REVIEW",
                artifact="prd.md",
                action="invalid",
                reviewer="user",
            )

    def test_valid_actions(self):
        for action in ["approved", "revised", "rejected"]:
            entry = ApprovalEntry.create(
                stage="PRD_REVIEW",
                artifact="prd.md",
                action=action,
                reviewer="user",
            )
            assert entry.action == action


class TestCreateInitialState:
    """Tests for create_initial_state."""

    def test_returns_dict_with_all_keys(self):
        state = create_initial_state("test-project")
        expected_keys = {
            "messages", "current_stage", "project_id",
            "current_prd_path", "current_spec_path", "current_plan_path",
            "current_research_path", "active_participation_mode",
            "decision_log", "assumption_log", "approval_history",
            "artifacts_written", "execution_plan_tasks", "current_task_id",
            "completed_task_ids", "execution_summary", "test_summary",
            "progress_log", "eval_suites", "eval_results",
            "current_eval_phase",
        }
        assert set(state.keys()) == expected_keys

    def test_initial_stage_is_intake(self):
        state = create_initial_state("test-project")
        assert state["current_stage"] == "INTAKE"

    def test_project_id_set(self):
        state = create_initial_state("my-project")
        assert state["project_id"] == "my-project"

    def test_lists_are_empty(self):
        state = create_initial_state("test")
        assert state["messages"] == []
        assert state["decision_log"] == []
        assert state["assumption_log"] == []
        assert state["approval_history"] == []
        assert state["artifacts_written"] == []

    def test_optional_fields_are_none(self):
        state = create_initial_state("test")
        assert state["current_prd_path"] is None
        assert state["current_spec_path"] is None
        assert state["current_plan_path"] is None
        assert state["current_research_path"] is None
        assert state["current_eval_phase"] is None
