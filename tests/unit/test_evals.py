"""Unit tests for Phase 0 eval implementations."""

from __future__ import annotations

import os

import pytest

from meta_agent.evals.infrastructure.test_infra import (
    eval_infra_001_project_directory_structure,
    eval_infra_002_prd_artifact_path,
    eval_infra_003_prd_frontmatter_valid,
    eval_infra_004_prd_required_sections,
)


class TestInfra001:
    """Tests for INFRA-001: Project directory structure."""

    def test_passes_with_full_structure(self, test_project_dir):
        result = eval_infra_001_project_directory_structure(test_project_dir)
        assert result["pass"] is True

    def test_fails_with_missing_dirs(self, tmp_path):
        result = eval_infra_001_project_directory_structure(str(tmp_path / "nonexistent"))
        assert result["pass"] is False


class TestInfra002:
    """Tests for INFRA-002: PRD artifact path."""

    def test_passes_with_prd(self, test_project_with_prd):
        result = eval_infra_002_prd_artifact_path(test_project_with_prd)
        assert result["pass"] is True

    def test_fails_without_prd(self, test_project_dir):
        result = eval_infra_002_prd_artifact_path(test_project_dir)
        assert result["pass"] is False


class TestInfra003:
    """Tests for INFRA-003: PRD frontmatter validation."""

    def test_passes_with_valid_frontmatter(self, test_project_with_prd):
        result = eval_infra_003_prd_frontmatter_valid(test_project_with_prd)
        assert result["pass"] is True

    def test_fails_without_prd(self, test_project_dir):
        result = eval_infra_003_prd_frontmatter_valid(test_project_dir)
        assert result["pass"] is False

    def test_fails_with_missing_fields(self, test_project_dir):
        prd_path = os.path.join(test_project_dir, "artifacts", "intake", "prd.md")
        with open(prd_path, "w") as f:
            f.write("---\ntitle: Test\n---\nContent")
        result = eval_infra_003_prd_frontmatter_valid(test_project_dir)
        assert result["pass"] is False
        assert "Missing required fields" in result["reason"]


class TestInfra004:
    """Tests for INFRA-004: PRD required sections."""

    def test_passes_with_all_sections(self, test_project_with_prd):
        result = eval_infra_004_prd_required_sections(test_project_with_prd)
        assert result["pass"] is True

    def test_fails_without_prd(self, test_project_dir):
        result = eval_infra_004_prd_required_sections(test_project_dir)
        assert result["pass"] is False

    def test_fails_with_missing_sections(self, test_project_dir):
        prd_path = os.path.join(test_project_dir, "artifacts", "intake", "prd.md")
        with open(prd_path, "w") as f:
            f.write("---\ntitle: Test\n---\n## Product Summary\nJust a summary.")
        result = eval_infra_004_prd_required_sections(test_project_dir)
        assert result["pass"] is False
        assert "Missing sections" in result["reason"]
