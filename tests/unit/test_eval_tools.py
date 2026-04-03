"""Unit tests for meta_agent.tools.eval_tools module."""

from __future__ import annotations

import json

import pytest

from meta_agent.tools.eval_tools import (
    EVAL_SUITE_TEMPLATE,
    REQUIRED_EVAL_FIELDS,
    VALID_CATEGORIES,
    VALID_STRATEGIES,
    _build_eval_entry,
    create_eval_dataset,
    propose_evals,
    validate_eval_suite,
)


pytestmark = pytest.mark.legacy


def _metadata() -> dict:
    return {
        "artifact": "eval-suite-prd",
        "project_id": "test-proj",
        "version": "1.0.0",
        "tier": 1,
        "langsmith_dataset_name": "test-proj-tier-1-evals",
        "created_by": "orchestrator",
        "status": "draft",
        "lineage": ["intake-prd.md"],
    }


class TestProposeEvals:
    def test_basic_proposal(self):
        reqs = [{"id": "REQ-001", "description": "Must parse tags", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert result["eval_count"] == 1
        assert result["tier"] == 1
        assert result["status"] == "proposed"
        assert "json_content" in result
        assert "path" in result

    def test_multiple_requirements(self):
        reqs = [
            {"id": "REQ-001", "description": "Parse tags", "type": "deterministic"},
            {"id": "REQ-002", "description": "Search quality", "type": "qualitative"},
            {"id": "REQ-003", "description": "Export works", "type": "deterministic"},
        ]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert result["eval_count"] == 3

    def test_empty_requirements_returns_error(self):
        result = propose_evals([], tier=1, project_id="test-proj")
        assert "error" in result

    def test_invalid_tier_returns_error(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=3, project_id="test-proj")
        assert "error" in result

    def test_tier_2_proposal(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=2, project_id="test-proj")
        assert result["tier"] == 2
        assert "architecture" in result["path"]

    def test_dataset_name_format(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="my-project")
        assert result["dataset_name"] == "my-project-tier-1-evals"

    def test_json_content_has_metadata(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        data = json.loads(result["json_content"])
        assert data["metadata"]["artifact"] == "eval-suite-prd"

    def test_json_content_has_evals(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        data = json.loads(result["json_content"])
        assert data["evals"][0]["id"] == "EVAL-001"

    def test_default_type_is_deterministic(self):
        reqs = [{"id": "REQ-001", "description": "test"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        data = json.loads(result["json_content"])
        assert data["evals"][0]["scoring"]["strategy"] == "binary"

    def test_auto_generated_req_ids(self):
        reqs = [{"description": "test requirement"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert result["eval_count"] == 1


class TestBuildEvalEntry:
    def test_deterministic_gets_binary(self):
        entry = _build_eval_entry("EVAL-001", "REQ-001", "test desc", "deterministic")
        assert entry["scoring"]["strategy"] == "binary"
        assert entry["scoring"]["threshold"] == 1.0

    def test_qualitative_gets_likert(self):
        entry = _build_eval_entry("EVAL-001", "REQ-001", "test desc", "qualitative")
        assert entry["scoring"]["strategy"] == "likert"
        assert entry["scoring"]["threshold"] == 3.5

    def test_unknown_type_defaults_binary(self):
        entry = _build_eval_entry("EVAL-001", "REQ-001", "test desc", "unknown")
        assert entry["scoring"]["strategy"] == "binary"

    def test_has_required_fields(self):
        entry = _build_eval_entry("EVAL-001", "REQ-001", "desc", "deterministic")
        for field in REQUIRED_EVAL_FIELDS:
            assert field in entry, f"Missing required field: {field}"

    def test_category_is_acceptance(self):
        entry = _build_eval_entry("EVAL-001", "REQ-001", "desc", "deterministic")
        assert entry["category"] == "acceptance"

    def test_name_includes_req_id(self):
        entry = _build_eval_entry("EVAL-001", "REQ-042", "Some description", "deterministic")
        assert "REQ-042" in entry["name"]


class TestValidateEvalSuite:
    def test_valid_suite(self, tmp_path):
        suite = {
            "metadata": _metadata(),
            "evals": [
                {
                    "id": "EVAL-001",
                    "name": "Test eval",
                    "category": "acceptance",
                    "input": {"scenario": "test"},
                    "expected": {"behavior": "passes"},
                    "scoring": {"strategy": "binary", "threshold": 1.0},
                }
            ],
        }
        path = tmp_path / "eval-suite.json"
        path.write_text(json.dumps(suite))
        result = validate_eval_suite(str(path))
        assert result["valid"] is True

    def test_missing_file(self):
        result = validate_eval_suite("/nonexistent/path.json")
        assert result["valid"] is False

    def test_missing_evals_key(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"metadata": _metadata()}))
        result = validate_eval_suite(str(path))
        assert result["valid"] is False

    def test_empty_evals(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text(json.dumps({"metadata": _metadata(), "evals": []}))
        result = validate_eval_suite(str(path))
        assert result["valid"] is False

    def test_missing_required_fields(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"metadata": _metadata(), "evals": [{"id": "EVAL-001", "name": "Test"}]}))
        result = validate_eval_suite(str(path))
        assert result["valid"] is False
        assert any("missing fields" in e for e in result["errors"])

    def test_invalid_strategy(self, tmp_path):
        suite = {
            "metadata": _metadata(),
            "evals": [
                {
                    "id": "EVAL-001",
                    "name": "Test",
                    "category": "acceptance",
                    "input": {"scenario": "test"},
                    "expected": {"behavior": "passes"},
                    "scoring": {"strategy": "invalid_strategy"},
                }
            ],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(suite))
        result = validate_eval_suite(str(path))
        assert result["valid"] is False
        assert any("invalid strategy" in e for e in result["errors"])


class TestCreateEvalDataset:
    def test_creates_local_dataset(self, tmp_path):
        suite = {
            "metadata": _metadata(),
            "evals": [
                {
                    "id": "EVAL-001",
                    "name": "Test eval",
                    "category": "acceptance",
                    "input": {"scenario": "test scenario", "preconditions": {}},
                    "expected": {"behavior": "should pass"},
                    "scoring": {"strategy": "binary", "threshold": 1.0},
                }
            ],
        }
        path = tmp_path / "eval-suite.json"
        path.write_text(json.dumps(suite))
        result = create_eval_dataset(str(path), "test-dataset")
        assert result["status"] in ("created", "local_only", "error")
        assert result["dataset_name"] == "test-dataset"
        if result["status"] != "error":
            assert result["example_count"] == 1

    def test_local_only_has_examples(self, tmp_path):
        suite = {
            "metadata": _metadata(),
            "evals": [
                {
                    "id": "EVAL-001",
                    "name": "Test eval",
                    "category": "acceptance",
                    "input": {"scenario": "test", "preconditions": {}},
                    "expected": {"behavior": "passes"},
                    "scoring": {"strategy": "binary", "threshold": 1.0},
                },
                {
                    "id": "EVAL-002",
                    "name": "Test eval 2",
                    "category": "acceptance",
                    "input": {"scenario": "test 2"},
                    "expected": {"behavior": "passes 2"},
                    "scoring": {"strategy": "likert", "threshold": 3.5},
                },
            ],
        }
        path = tmp_path / "eval-suite.json"
        path.write_text(json.dumps(suite))
        result = create_eval_dataset(str(path), "test-dataset")
        if result["status"] == "local_only":
            assert len(result["examples"]) == 2
            assert result["examples"][0]["inputs"]["eval_id"] == "EVAL-001"


def test_eval_suite_template_is_json_shape():
    assert set(EVAL_SUITE_TEMPLATE) == {"metadata", "evals"}
    assert EVAL_SUITE_TEMPLATE["metadata"]["artifact"] == "eval-suite-prd"


def test_valid_constants_are_nonempty():
    assert VALID_CATEGORIES
    assert VALID_STRATEGIES
