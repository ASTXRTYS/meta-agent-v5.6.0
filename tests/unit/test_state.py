"""Unit tests for meta_agent.state module."""

from __future__ import annotations

import pytest

from meta_agent.state import (
    ApprovalEntry,
    AssumptionEntry,
    DecisionEntry,
    MetaAgentState,
    WorkflowStage,
    create_initial_state,
)


pytestmark = pytest.mark.legacy



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
            "verification_results", "spec_generation_feedback_cycles",
            "pending_research_gap_request",
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
