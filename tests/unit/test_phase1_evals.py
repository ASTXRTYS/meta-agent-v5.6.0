"""Unit tests for Phase 1 eval implementations."""

from __future__ import annotations

import json
import os

from meta_agent.evals.infrastructure.test_infra import (
    eval_infra_005_eval_suite_artifact_exists,
    eval_infra_006_eval_suite_schema_valid,
    eval_infra_007_agents_md_created,
    eval_infra_008_dynamic_prompt_after_transition,
)
from meta_agent.evals.runner import EVAL_REGISTRY, PHASE_EVALS, filter_evals, run_eval
from meta_agent.evals.stage_transitions.test_stages import (
    eval_stage_001_valid_transitions_only,
    eval_stage_002_exit_conditions_met,
)


SAMPLE_EVAL_SUITE = {
    "metadata": {
        "artifact": "eval-suite-prd",
        "project_id": "test-project",
        "version": "1.0.0",
        "tier": 1,
        "langsmith_dataset_name": "test-project-tier-1-evals",
        "created_by": "orchestrator",
        "status": "draft",
        "lineage": ["intake-prd.md"],
    },
    "evals": [
        {
            "id": "EVAL-001",
            "name": "Test eval 1",
            "category": "behavioral",
            "input": {"scenario": "test input"},
            "expected": {"behavior": "test output"},
            "scoring": {"strategy": "binary", "threshold": 1.0},
        },
        {
            "id": "EVAL-002",
            "name": "Test eval 2",
            "category": "acceptance",
            "input": {"scenario": "test input 2"},
            "expected": {"behavior": "test output 2"},
            "scoring": {"strategy": "binary", "threshold": 1.0},
        },
    ],
}


class TestInfra005:
    def test_fails_without_eval_suite(self, test_project_dir):
        result = eval_infra_005_eval_suite_artifact_exists(test_project_dir)
        assert result["pass"] is False

    def test_passes_with_eval_suite(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.json")
        with open(eval_path, "w") as f:
            json.dump(SAMPLE_EVAL_SUITE, f)
        result = eval_infra_005_eval_suite_artifact_exists(test_project_dir)
        assert result["pass"] is True


class TestInfra006:
    def test_passes_with_valid_schema(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.json")
        with open(eval_path, "w") as f:
            json.dump(SAMPLE_EVAL_SUITE, f)
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is True

    def test_fails_with_missing_fields(self, test_project_dir):
        bad_suite = {
            "metadata": SAMPLE_EVAL_SUITE["metadata"],
            "evals": [{"id": "EVAL-001", "name": "Test"}],
        }
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.json")
        with open(eval_path, "w") as f:
            json.dump(bad_suite, f)
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False
        assert "missing fields" in result["reason"]

    def test_fails_with_no_evals(self, test_project_dir):
        eval_path = os.path.join(test_project_dir, "evals", "eval-suite-prd.json")
        with open(eval_path, "w") as f:
            json.dump({"metadata": SAMPLE_EVAL_SUITE["metadata"], "evals": []}, f)
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False

    def test_fails_without_file(self, test_project_dir):
        result = eval_infra_006_eval_suite_schema_valid(test_project_dir)
        assert result["pass"] is False


class TestInfra007:
    def test_passes_with_agents_md(self, test_project_dir):
        result = eval_infra_007_agents_md_created(test_project_dir)
        assert result["pass"] is True

    def test_fails_without_agents_md(self, tmp_path):
        result = eval_infra_007_agents_md_created(str(tmp_path))
        assert result["pass"] is False


class TestInfra008:
    def test_passes_prompt_recomposition(self):
        result = eval_infra_008_dynamic_prompt_after_transition()
        assert result["pass"] is True
        assert "correctly recomposed" in result["reason"]


class TestStage001:
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
        trace = {"state_transitions": [{"from": "INTAKE", "to": "EXECUTION"}]}
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
        result = eval_stage_001_valid_transitions_only({"state_transitions": []})
        assert result["pass"] is True


class TestStage002:
    def test_passes_with_all_conditions_met(self):
        trace = {
            "state_transitions": [{"from": "INTAKE", "to": "PRD_REVIEW"}],
            "artifacts_created": ["prd.md"],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is True

    def test_fails_with_missing_artifact(self):
        trace = {
            "state_transitions": [{"from": "INTAKE", "to": "PRD_REVIEW"}],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is False

    def test_fails_with_missing_approval(self):
        trace = {
            "state_transitions": [{"from": "PRD_REVIEW", "to": "RESEARCH", "approval_received": False}],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is False

    def test_passes_with_approval(self):
        trace = {
            "state_transitions": [{"from": "PRD_REVIEW", "to": "RESEARCH", "approval_received": True}],
            "artifacts_created": [],
        }
        result = eval_stage_002_exit_conditions_met(trace)
        assert result["pass"] is True


class TestEvalRunner:
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
        trace = {"state_transitions": [{"from": "INTAKE", "to": "PRD_REVIEW"}]}
        result = run_eval("STAGE-001", "", trace=trace)
        assert result["pass"] is True
