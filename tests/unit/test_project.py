"""Unit tests for meta_agent.project module."""

from __future__ import annotations

import os

import pytest

from meta_agent.project import init_project, slugify, create_thread_id


class TestSlugify:
    def test_basic(self):
        assert slugify("Test Project") == "test-project"

    def test_special_chars(self):
        assert slugify("My App! v2.0") == "my-app-v20"

    def test_multiple_spaces(self):
        assert slugify("  hello   world  ") == "hello-world"

    def test_already_slug(self):
        assert slugify("my-project") == "my-project"


class TestCreateThreadId:
    def test_format(self):
        tid = create_thread_id("test-project", "abc123")
        assert tid == "project-test-project-abc123"

    def test_auto_session_id(self):
        tid = create_thread_id("test-project")
        assert tid.startswith("project-test-project-")


class TestInitProject:
    def test_creates_directories(self, temp_dir):
        result = init_project(temp_dir, "Test Project")
        project_dir = result["project_dir"]

        assert os.path.isdir(project_dir)
        assert os.path.isdir(os.path.join(project_dir, "artifacts", "intake"))
        assert os.path.isdir(os.path.join(project_dir, "artifacts", "research"))
        assert os.path.isdir(os.path.join(project_dir, "artifacts", "spec"))
        assert os.path.isdir(os.path.join(project_dir, "artifacts", "planning"))
        assert os.path.isdir(os.path.join(project_dir, "evals"))
        assert os.path.isdir(os.path.join(project_dir, "logs"))

    def test_creates_agent_dirs(self, temp_dir):
        result = init_project(temp_dir, "Test Project")
        project_dir = result["project_dir"]

        assert os.path.isdir(os.path.join(project_dir, ".agents", "orchestrator"))
        assert os.path.isfile(
            os.path.join(project_dir, ".agents", "orchestrator", "AGENTS.md")
        )

    def test_creates_meta_yaml(self, temp_dir):
        result = init_project(temp_dir, "Test Project")
        meta_path = os.path.join(result["project_dir"], "meta.yaml")
        assert os.path.isfile(meta_path)

    def test_returns_project_info(self, temp_dir):
        result = init_project(temp_dir, "Test Project", "A description")
        assert result["project_id"] == "test-project"
        assert "project_dir" in result
        assert "thread_id" in result
        assert result["thread_id"].startswith("project-test-project-")
