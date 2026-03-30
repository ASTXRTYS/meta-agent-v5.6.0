"""Unit tests for meta_agent.stages module (Phase 2)."""

from __future__ import annotations

import os

import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from meta_agent.stages.intake import (
    IntakeStage,
    REQUIRED_PRD_SECTIONS,
    PRD_FRONTMATTER_TEMPLATE,
    MIN_CLARIFYING_QUESTIONS,
    MAX_CLARIFYING_QUESTIONS,
    MAX_REVISION_CYCLES as INTAKE_MAX_CYCLES,
)
from meta_agent.stages.prd_review import (
    PrdReviewStage,
    APPROVAL_PATTERNS,
    MAX_REVISION_CYCLES,
)
from meta_agent.stages import IntakeStage as IntakeStageFromInit, PrdReviewStage as PrdReviewStageFromInit


class TestIntakeStageInit:
    """Tests for IntakeStage initialization."""

    def test_sets_paths(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        assert stage.prd_path == f"{tmp_path}/artifacts/intake/prd.md"
        assert stage.eval_suite_path == f"{tmp_path}/evals/eval-suite-prd.json"
        assert stage.project_id == "test-proj"

    def test_entry_conditions_always_met(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        result = stage.check_entry_conditions()
        assert result["met"] is True


class TestIntakeExitConditions:
    """Tests for IntakeStage exit conditions."""

    def test_fails_without_prd(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        state = {"approval_history": []}
        result = stage.check_exit_conditions(state)
        assert result["met"] is False
        assert any("PRD not found" in u for u in result["unmet"])

    def test_fails_without_eval_suite(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        # Create PRD but not eval suite
        prd_dir = os.path.join(str(tmp_path), "artifacts", "intake")
        os.makedirs(prd_dir, exist_ok=True)
        with open(os.path.join(prd_dir, "prd.md"), "w") as f:
            f.write("PRD content")
        state = {"approval_history": []}
        result = stage.check_exit_conditions(state)
        assert result["met"] is False

    def test_fails_without_approvals(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        # Create both files
        prd_dir = os.path.join(str(tmp_path), "artifacts", "intake")
        eval_dir = os.path.join(str(tmp_path), "evals")
        os.makedirs(prd_dir, exist_ok=True)
        os.makedirs(eval_dir, exist_ok=True)
        with open(os.path.join(prd_dir, "prd.md"), "w") as f:
            f.write("PRD content")
        with open(os.path.join(eval_dir, "eval-suite-prd.json"), "w") as f:
            f.write("{\"metadata\": {}, \"evals\": []}")
        state = {"approval_history": []}
        result = stage.check_exit_conditions(state)
        assert result["met"] is False
        assert any("not approved" in u for u in result["unmet"])

    def test_passes_with_all_conditions(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        prd_dir = os.path.join(str(tmp_path), "artifacts", "intake")
        eval_dir = os.path.join(str(tmp_path), "evals")
        os.makedirs(prd_dir, exist_ok=True)
        os.makedirs(eval_dir, exist_ok=True)
        with open(os.path.join(prd_dir, "prd.md"), "w") as f:
            f.write("PRD content")
        with open(os.path.join(eval_dir, "eval-suite-prd.json"), "w") as f:
            f.write("{\"metadata\": {}, \"evals\": []}")
        state = {
            "approval_history": [
                {"artifact": "prd", "action": "approved"},
                {"artifact": "eval_suite", "action": "approved"},
            ],
        }
        result = stage.check_exit_conditions(state)
        assert result["met"] is True


class TestIntakePrdFrontmatter:
    """Tests for IntakeStage PRD frontmatter building."""

    def test_builds_frontmatter(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        fm = stage.build_prd_frontmatter("My PRD Title")
        assert "---" in fm
        assert "artifact:" in fm or "artifact: " in fm
        assert "My PRD Title" in fm

    def test_uses_project_id(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        fm = stage.build_prd_frontmatter("Title")
        assert "test-proj" in fm

    def test_override_project_id(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        fm = stage.build_prd_frontmatter("Title", project_id="other-proj")
        assert "other-proj" in fm


class TestIntakeValidatePrdSections:
    """Tests for PRD section validation."""

    def test_all_sections_present(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        content = "\n".join([f"## {s}\nContent here." for s in REQUIRED_PRD_SECTIONS])
        result = stage.validate_prd_sections(content)
        assert result["valid"] is True
        assert result["missing_sections"] == []

    def test_missing_sections(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        content = "## Product Summary\nSome content."
        result = stage.validate_prd_sections(content)
        assert result["valid"] is False
        assert len(result["missing_sections"]) == 9

    def test_case_insensitive(self, tmp_path):
        stage = IntakeStage(str(tmp_path), "test-proj")
        content = "\n".join([f"## {s.upper()}\nContent here." for s in REQUIRED_PRD_SECTIONS])
        result = stage.validate_prd_sections(content)
        assert result["valid"] is True


class TestIntakeConstants:
    """Tests for INTAKE constants."""

    def test_required_sections_count(self):
        assert len(REQUIRED_PRD_SECTIONS) == 10

    def test_clarifying_question_bounds(self):
        assert MIN_CLARIFYING_QUESTIONS == 3
        assert MAX_CLARIFYING_QUESTIONS == 7

    def test_max_revision_cycles(self):
        assert INTAKE_MAX_CYCLES == 5

    def test_frontmatter_template(self):
        assert PRD_FRONTMATTER_TEMPLATE["artifact"] == "prd"
        assert PRD_FRONTMATTER_TEMPLATE["status"] == "draft"
        assert PRD_FRONTMATTER_TEMPLATE["stage"] == "INTAKE"


# ===================================================================
# PrdReviewStage tests
# ===================================================================


class TestPrdReviewStageInit:
    """Tests for PrdReviewStage initialization."""

    def test_sets_paths(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        assert stage.prd_path == f"{tmp_path}/artifacts/intake/prd.md"
        assert stage.eval_suite_path == f"{tmp_path}/evals/eval-suite-prd.json"

    def test_initial_revision_count(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        assert stage.revision_count == 0


class TestPrdReviewEntryConditions:
    """Tests for PrdReviewStage entry conditions."""

    def test_fails_without_prd(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        result = stage.check_entry_conditions()
        assert result["met"] is False

    def test_passes_with_prd(self, tmp_path):
        prd_dir = os.path.join(str(tmp_path), "artifacts", "intake")
        os.makedirs(prd_dir, exist_ok=True)
        with open(os.path.join(prd_dir, "prd.md"), "w") as f:
            f.write("PRD content")
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        result = stage.check_entry_conditions()
        assert result["met"] is True


class TestPrdReviewExitConditions:
    """Tests for PrdReviewStage exit conditions (hard gate)."""

    def test_fails_without_approvals(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        state = {"approval_history": []}
        result = stage.check_exit_conditions(state)
        assert result["met"] is False
        assert result["prd_approved"] is False
        assert result["eval_approved"] is False

    def test_fails_with_only_prd_approval(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        state = {
            "approval_history": [
                {"artifact": "prd", "action": "approved"},
            ],
        }
        result = stage.check_exit_conditions(state)
        assert result["met"] is False
        assert result["prd_approved"] is True
        assert result["eval_approved"] is False

    def test_fails_with_only_eval_approval(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        state = {
            "approval_history": [
                {"artifact": "eval_suite", "action": "approved"},
            ],
        }
        result = stage.check_exit_conditions(state)
        assert result["met"] is False
        assert result["eval_approved"] is True
        assert result["prd_approved"] is False

    def test_passes_with_both_approvals(self, tmp_path):
        stage = PrdReviewStage(str(tmp_path), "test-proj")
        state = {
            "approval_history": [
                {"artifact": "prd", "action": "approved"},
                {"artifact": "eval_suite", "action": "approved"},
            ],
        }
        result = stage.check_exit_conditions(state)
        assert result["met"] is True


class TestPrdReviewClassifyResponse:
    """Tests for classify_user_response — all 7 branches."""

    def setup_method(self):
        self.stage = PrdReviewStage("/tmp/test", "test-proj")

    def test_approval_yes(self):
        assert self.stage.classify_user_response("yes") == "approval"

    def test_approval_looks_good(self):
        assert self.stage.classify_user_response("Looks good to me") == "approval"

    def test_approval_lgtm(self):
        assert self.stage.classify_user_response("LGTM") == "approval"

    def test_approval_ship_it(self):
        assert self.stage.classify_user_response("Ship it!") == "approval"

    def test_modify_eval(self):
        assert self.stage.classify_user_response("Modify EVAL-002 to use binary") == "modify"

    def test_change_eval(self):
        assert self.stage.classify_user_response("Change EVAL-001 threshold") == "modify"

    def test_add_eval(self):
        assert self.stage.classify_user_response("Add an eval for edge cases") == "add"

    def test_remove_specific_eval(self):
        assert self.stage.classify_user_response("Remove EVAL-003") == "remove"

    def test_remove_all_skip(self):
        assert self.stage.classify_user_response("Skip all evals") == "remove_all"

    def test_remove_all_no_eval(self):
        assert self.stage.classify_user_response("no eval needed") == "remove_all"

    def test_change_scoring(self):
        assert self.stage.classify_user_response("Change scoring to use likert") == "change_scoring"

    def test_unclear(self):
        assert self.stage.classify_user_response("What about the weather?") == "unclear"

    def test_unclear_empty(self):
        assert self.stage.classify_user_response("") == "unclear"


class TestPrdReviewRevisionCycles:
    """Tests for revision cycle tracking."""

    def test_increment_returns_true_under_limit(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        assert stage.increment_revision_count() is True
        assert stage.revision_count == 1

    def test_at_limit_after_max_cycles(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        for _ in range(MAX_REVISION_CYCLES):
            stage.increment_revision_count()
        assert stage.at_revision_limit() is True

    def test_not_at_limit_initially(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        assert stage.at_revision_limit() is False

    def test_increment_returns_false_at_limit(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        for _ in range(MAX_REVISION_CYCLES - 1):
            stage.increment_revision_count()
        assert stage.increment_revision_count() is False


class TestPrdReviewRecordApproval:
    """Tests for approval recording."""

    def test_records_prd_approval(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        entry = stage.record_approval("prd")
        assert entry.artifact == "prd"
        assert entry.action == "approved"
        assert entry.reviewer == "user"
        assert entry.stage == "PRD_REVIEW"

    def test_records_eval_approval(self):
        stage = PrdReviewStage("/tmp/test", "test-proj")
        entry = stage.record_approval("eval_suite", reviewer="admin")
        assert entry.artifact == "eval_suite"
        assert entry.reviewer == "admin"


class TestPackageExports:
    """Tests that __init__.py exports work."""

    def test_intake_stage_exported(self):
        assert IntakeStageFromInit is IntakeStage

    def test_prd_review_stage_exported(self):
        assert PrdReviewStageFromInit is PrdReviewStage


class TestApprovalPatterns:
    """Tests for approval pattern constants."""

    def test_has_common_patterns(self):
        assert "approved" in APPROVAL_PATTERNS
        assert "looks good" in APPROVAL_PATTERNS
        assert "lgtm" in APPROVAL_PATTERNS

    def test_max_revision_cycles(self):
        assert MAX_REVISION_CYCLES == 5
