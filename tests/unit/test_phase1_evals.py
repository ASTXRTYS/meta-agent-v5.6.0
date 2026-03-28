"""Unit tests for Phase 1 eval implementations."""

from __future__ import annotations

import os

import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from meta_agent.evals.infrastructure.test_infra import (
    eval_infra_005_eval_suite_artifact_exists,
    eval_infra_006_eval_suite_schema_valid,
    eval_infra_007_agents_md_created,
    eval_infra_008_dynamic_prompt_after_transition,
)
from meta_agent.evals.stage_transitions.test_stages import (
    eval_stage_001_valid_transitions_only,
    eval_stage_002_exit_conditions_met,
)
from meta_agent.evals.runner import (
    EVAL_REGISTRY,
    PHASE_EVALS,
    filter_evals,
    run_eval,
)


SAMPLE_EVAL_SUITE = """evals:
  - id: EVAL-001
    name: Test eval 1
    category: functional
    input: "test input"
    expected: "test output"
    scoring: binary
  - id: EVAL-002
    name: Test eval 2
    category: functional
    input: "test input 2"
    expected: "test output 2"
    scoring: binary
"""


class TestInfra005:
    """Tests for INFRA-005: Eval suite artifact exists."""

    def test_fails_without_eval_suite(self, test_project_dir):
        result = eval_infra_005_eval_suite_artifact_exists(test_project_dir)
        assert result["pass"] is False

    def test_passes_with_eval_suite(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.yaml")
        with open(eval_path, "w") as f:
            f.write(SAMPLE_EVAL_SUITE)
        result = eval_infra_005_eval_suite_artifact_exists(test_project_dir)
        assert result["pass"] is True


class TestInfra006:
    """Tests for INFRA-006: Eval suite schema valid."""

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_passes_with_valid_schema(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.yaml")
        with open(eval_path, "w") as f:
            f.write(SAMPLE_EVAL_SUITE)
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is True

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_fails_with_missing_fields(self, test_project_dir):
        bad_suite = "evals:\n  - id: EVAL-001\n    name: Test\n"
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.yaml")
        with open(eval_path, "w") as f:
            f.write(bad_suite)
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False
        assert "missing fields" in result["reason"]

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_fails_with_no_evals(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.yaml")
        with open(eval_path, "w") as f:
            f.write("evals: []\n")
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False

    def test_fails_without_file(self, test_project_dir):
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False


class TestInfra007:
    """Tests for INFRA-007: Per-agent AGENTS.md created."""

    def test_passes_with_agents_md(self, test_project_dir):
        result = eval_infra_007_agents_md_created(test_project_dir)
        assert result["pass"] is True

    def test_fails_without_agents_md(self, tmp_path):
        result = eval_infra_007_agents_md_created(str(tmp_path))
        assert result["pass"] is False


class TestInfra008:
    """Tests for INFRA-008: Dynamic prompt recomposition after stage transition."""

    def test_passes_prompt_recomposition(self):
        result = eval_infra_008_dynamic_prompt_after_transition()
        assert result["pass"] is True
        assert "correctly recomposed" in result["reason"]


class TestStage001:
    """Tests for STAGE-001: Only valid transitions."""

    def test_passes_with_valid_transitions(self):
        trace = {
            "state_transitions": [
                {"from": "INTAKE", "to": "PRD_REVIEW"},
                {"from": "PRD_REVIEW", "to": "RESEARCH"},
            ]
        }
        result = eval_stage_001_valid_transitions_only(trace)
        assert result["pass"] is True

    def test_fails_with_invalid_transition(self):
        trace = {
            "state_transitions": [
                {"from": "INTAKE", "to": "EXECUTION"},
            ]
        }
        result = eval_stage_001_valid_transitions_only(trace)
        assert result["pass"] is False

    def test_allows_audit_from_any_stage(self):
        trace = {
            "state_transitions": [
                {"from": "INTAKE", "to": "AUDIT"},
                {"from": "EXECUTION", "to": "AUDIT"},
            ]
        }
        result = eval_stage_001_valid_transitions_only(trace)
        assert result["pass"] is True

    def test_passes_with_empty_trace(self):
        trace = {"state_transitions": []}
        result = eval_stage_001_valid_transitions_only(trace)
        assert result["pass"] is True


class TestStage002:
    """Tests for STAGE-002: Exit conditions met."""

    def test_passes_with_all_conditions_met(self):
        trace = {
            "state_transitions": [
                {
                    "from": "INTAKE",
                    "to": "PRD_REVIEW",
                },
            ],
            "artifacts_created": ["prd.md"],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is True

    def test_fails_with_missing_artifact(self):
        trace = {
            "state_transitions": [
                {"from": "INTAKE", "to": "PRD_REVIEW"},
            ],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is False

    def test_fails_with_missing_approval(self):
        trace = {
            "state_transitions": [
                {"from": "PRD_REVIEW", "to": "RESEARCH", "approval_received": False},
            ],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is False

    def test_passes_with_approval(self):
        trace = {
            "state_transitions": [
                {"from": "PRD_REVIEW", "to": "RESEARCH", "approval_received": True},
            ],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is True


class TestEvalRunner:
    """Tests for the updated eval runner."""

    def test_phase_1_evals_registered(self):
        phase_1_ids = PHASE_EVALS[1]
        assert "INFRA-005" in phase_1_ids
        assert "INFRA-006" in phase_1_ids
        assert "INFRA-007" in phase_1_ids
        assert "INFRA-008" in phase_1_ids
        assert "STAGE-001" in phase_1_ids
        assert "STAGE-002" in phase_1_ids

    def test_all_phase_1_evals_in_registry(self):
        for eval_id in PHASE_EVALS[1]:
            assert eval_id in EVAL_REGISTRY, f"{eval_id} not in EVAL_REGISTRY"

    def test_filter_by_phase_1(self):
        ids = filter_evals(phase=1)
        assert len(ids) == 6

    def test_filter_by_stage_transitions(self):
        ids = filter_evals(category="stage_transitions")
        assert "STAGE-001" in ids
        assert "STAGE-002" in ids

    def test_run_infra_008_eval(self):
        result = run_eval("INFRA-008", "")
        assert result["pass"] is True
        assert result["eval_id"] == "INFRA-008"

    def test_run_stage_001_with_trace(self):
        trace = {
            "state_transitions": [
                {"from": "INTAKE", "to": "PRD_REVIEW"},
            ]
        }
        result = run_eval("STAGE-001", "", trace=trace)
        assert result["pass"] is True
