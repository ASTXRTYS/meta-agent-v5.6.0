"""Unit tests for meta_agent.subagents.document_renderer module (Phase 2)."""

from __future__ import annotations

import os

import pytest

from meta_agent.subagents.document_renderer import (
    DOCUMENT_RENDERER_CONFIG,
    RENDERING_TRIGGERS,
    OUTPUT_FORMATS,
    get_render_config,
    should_render,
    get_output_path,
    render_artifact,
)


pytestmark = pytest.mark.legacy


class TestDocumentRendererConfig:
    """Tests for document renderer configuration."""

    def test_config_type(self):
        assert DOCUMENT_RENDERER_CONFIG["type"] == "dict_based"

    def test_config_effort(self):
        assert DOCUMENT_RENDERER_CONFIG["effort"] == "low"

    def test_config_tools(self):
        tools = DOCUMENT_RENDERER_CONFIG["tools"]
        assert "read_file" in tools
        assert "write_file" in tools

    def test_config_skills(self):
        skills = DOCUMENT_RENDERER_CONFIG["skills"]
        assert "anthropic/docx" in skills
        assert "anthropic/pdf" in skills

    def test_get_render_config_returns_copy(self):
        config = get_render_config()
        assert config == DOCUMENT_RENDERER_CONFIG
        config["extra"] = "test"
        assert "extra" not in DOCUMENT_RENDERER_CONFIG


class TestRenderingTriggers:
    """Tests for rendering trigger configuration."""

    def test_intake_triggers(self):
        assert "prd" in RENDERING_TRIGGERS["INTAKE"]

    def test_prd_review_triggers(self):
        assert "prd" in RENDERING_TRIGGERS["PRD_REVIEW"]

    def test_spec_generation_triggers(self):
        assert "technical-specification" in RENDERING_TRIGGERS["SPEC_GENERATION"]

    def test_planning_triggers(self):
        assert "implementation-plan" in RENDERING_TRIGGERS["PLANNING"]


class TestShouldRender:
    """Tests for should_render function."""

    def test_prd_in_intake(self):
        assert should_render("INTAKE", "prd") is True

    def test_prd_in_execution(self):
        assert should_render("EXECUTION", "prd") is False

    def test_unknown_artifact(self):
        assert should_render("INTAKE", "unknown") is False

    def test_unknown_stage(self):
        assert should_render("NONEXISTENT", "prd") is False


class TestGetOutputPath:
    """Tests for get_output_path function."""

    def test_docx_output(self):
        path = get_output_path("/workspace/artifacts/intake/prd.md", "docx")
        assert path == "/workspace/artifacts/intake/prd.docx"

    def test_pdf_output(self):
        path = get_output_path("/workspace/artifacts/intake/prd.md", "pdf")
        assert path == "/workspace/artifacts/intake/prd.pdf"

    def test_preserves_directory(self):
        path = get_output_path("/some/deep/path/spec.md", "docx")
        assert path == "/some/deep/path/spec.docx"


class TestOutputFormats:
    """Tests for output format constants."""

    def test_has_docx(self):
        assert "docx" in OUTPUT_FORMATS

    def test_has_pdf(self):
        assert "pdf" in OUTPUT_FORMATS


class TestRenderArtifact:
    """Tests for render_artifact function."""

    def test_no_render_for_wrong_stage(self, tmp_path):
        source = tmp_path / "prd.md"
        source.write_text("# PRD")
        result = render_artifact(str(source), "EXECUTION")
        assert result["rendered"] is False

    def test_no_render_for_missing_file(self):
        result = render_artifact("/nonexistent/prd.md", "INTAKE")
        assert result["rendered"] is False

    def test_renders_prd_in_intake(self, tmp_path):
        source = tmp_path / "prd.md"
        source.write_text("# PRD Content")
        result = render_artifact(str(source), "INTAKE")
        assert result["rendered"] is True
        assert "docx" in result["outputs"]
        assert "pdf" in result["outputs"]
        assert result["status"] == "pending"

    def test_render_output_paths_correct(self, tmp_path):
        source = tmp_path / "prd.md"
        source.write_text("# PRD")
        result = render_artifact(str(source), "INTAKE")
        assert result["outputs"]["docx"].endswith(".docx")
        assert result["outputs"]["pdf"].endswith(".pdf")
