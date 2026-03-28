"""Unit tests for meta_agent.tools.eval_tools module (Phase 2)."""

from __future__ import annotations

import os
import tempfile

import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from meta_agent.tools.eval_tools import (
    propose_evals,
    create_eval_dataset,
    validate_eval_suite,
    _build_eval_entry,
    VALID_CATEGORIES,
    VALID_STRATEGIES,
    REQUIRED_EVAL_FIELDS,
)


class TestProposeEvals:
    """Tests for the propose_evals tool."""

    def test_basic_proposal(self):
        reqs = [
            {"id": "REQ-001", "description": "Must parse tags", "type": "deterministic"},
        ]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert result["eval_count"] == 1
        assert result["tier"] == 1
        assert result["status"] == "proposed"
        assert "yaml_content" in result
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

    def test_yaml_content_has_frontmatter(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        yaml_content = result["yaml_content"]
        assert yaml_content.startswith("---")
        assert "artifact:" in yaml_content or "artifact: " in yaml_content

    def test_yaml_content_has_evals(self):
        reqs = [{"id": "REQ-001", "description": "test", "type": "deterministic"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert "evals:" in result["yaml_content"]
        assert "EVAL-001" in result["yaml_content"]

    def test_default_type_is_deterministic(self):
        reqs = [{"id": "REQ-001", "description": "test"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert "binary" in result["yaml_content"]

    def test_auto_generated_req_ids(self):
        reqs = [{"description": "test requirement"}]
        result = propose_evals(reqs, tier=1, project_id="test-proj")
        assert result["eval_count"] == 1


class TestBuildEvalEntry:
    """Tests for _build_eval_entry helper."""

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
    """Tests for validate_eval_suite."""

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_valid_suite(self, tmp_path):
        suite_content = """---
artifact: eval-suite-prd
---
evals:
  - id: EVAL-001
    name: Test eval
    category: acceptance
    input:
      scenario: test
    expected:
      behavior: passes
    scoring:
      strategy: binary
      threshold: 1.0
"""
        path = tmp_path / "eval-suite.yaml"
        path.write_text(suite_content)
        result = validate_eval_suite(str(path))
        assert result["valid"] is True

    def test_missing_file(self):
        result = validate_eval_suite("/nonexistent/path.yaml")
        assert result["valid"] is False

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_missing_evals_key(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("metadata: test\n")
        result = validate_eval_suite(str(path))
        assert result["valid"] is False

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_empty_evals(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("evals: []\n")
        result = validate_eval_suite(str(path))
        assert result["valid"] is False

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_missing_required_fields(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("evals:\n  - id: EVAL-001\n    name: Test\n")
        result = validate_eval_suite(str(path))
        assert result["valid"] is False
        assert any("missing fields" in e for e in result["errors"])

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_invalid_strategy(self, tmp_path):
        suite_content = """evals:
  - id: EVAL-001
    name: Test
    category: acceptance
    input: test
    expected: passes
    scoring:
      strategy: invalid_strategy
"""
        path = tmp_path / "bad.yaml"
        path.write_text(suite_content)
        result = validate_eval_suite(str(path))
        assert result["valid"] is False
        assert any("invalid strategy" in e for e in result["errors"])


class TestCreateEvalDataset:
    """Tests for create_eval_dataset."""

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_creates_local_dataset(self, tmp_path):
        suite_content = """---
artifact: eval-suite-prd
---
evals:
  - id: EVAL-001
    name: Test eval
    category: acceptance
    input:
      scenario: test scenario
      preconditions: {}
    expected:
      behavior: should pass
    scoring:
      strategy: binary
      threshold: 1.0
"""
        path = tmp_path / "eval-suite.yaml"
        path.write_text(suite_content)
        result = create_eval_dataset(str(path), "test-dataset")
        # Status depends on LangSmith availability and auth:
        # "created" = full LangSmith, "local_only" = no langsmith package,
        # "error" = langsmith installed but not authenticated
        assert result["status"] in ("created", "local_only", "error")
        assert result["dataset_name"] == "test-dataset"
        if result["status"] != "error":
            assert result["example_count"] == 1

    @pytest.mark.skipif(not HAS_YAML, reason="yaml not installed")
    def test_local_only_has_examples(self, tmp_path):
        suite_content = """---
artifact: eval-suite-prd
---
evals:
  - id: EVAL-001
    name: Test eval
    category: acceptance
    input:
      scenario: test
      preconditions: {}
    expected:
      behavior: passes
    scoring:
      strategy: binary
      threshold: 1.0
  - id: EVAL-002
    name: Test eval 2
    category: acceptance
    input:
      scenario: test 2
    expected:
      behavior: passes 2
    scoring:
      strategy: likert
      threshold: 3.5
"""
        path = tmp_path / "eval-suite.yaml"
        path.write_text(suite_content)
        result = create_eval_dataset(str(path), "test-dataset")
        if result["status"] == "local_only":
            assert len(result["examples"]) == 2
            assert result["examples"][0]["inputs"]["eval_id"] == "EVAL-001"

    def test_invalid_suite_returns_error(self):
        result = create_eval_dataset("/nonexistent.yaml", "test-dataset")
        assert result["status"] == "error"


class TestConstants:
    """Tests for module-level constants."""

    def test_valid_categories(self):
        assert "behavioral" in VALID_CATEGORIES
        assert "acceptance" in VALID_CATEGORIES
        assert "edge_case" in VALID_CATEGORIES
        assert "user_intent" in VALID_CATEGORIES

    def test_valid_strategies(self):
        assert "binary" in VALID_STRATEGIES
        assert "likert" in VALID_STRATEGIES
        assert "llm-judge" in VALID_STRATEGIES
        assert "pairwise" in VALID_STRATEGIES

    def test_required_fields(self):
        assert "id" in REQUIRED_EVAL_FIELDS
        assert "scoring" in REQUIRED_EVAL_FIELDS
