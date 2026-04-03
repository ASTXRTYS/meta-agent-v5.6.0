"""Unit tests for meta_agent.graph module.

Tests use the real create_deep_agent() from deepagents SDK.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from meta_agent.graph import create_graph
from meta_agent.middleware.dynamic_system_prompt import DynamicSystemPromptMiddleware
from meta_agent.state import MetaAgentState, WorkflowStage


pytestmark = pytest.mark.legacy


class TestCreateGraph:
    """Tests for the create_graph factory using real deepagents SDK."""

    def test_creates_graph(self):
        graph = create_graph(project_id="test")
        assert graph is not None

    def test_graph_is_compiled(self):
        graph = create_graph(project_id="test")
        # Real create_deep_agent returns a CompiledStateGraph
        assert hasattr(graph, "invoke") or hasattr(graph, "nodes")

    def test_graph_has_get_state(self):
        graph = create_graph(project_id="test")
        assert hasattr(graph, "get_state")

    def test_graph_has_update_state(self):
        graph = create_graph(project_id="test")
        assert hasattr(graph, "update_state")


class TestDynamicPromptMiddleware:
    """Tests for DynamicSystemPromptMiddleware used in graph."""

    def test_middleware_creates(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        assert mw.project_dir == "/.agents/pm/projects/test"
        assert mw.project_id == "test-project"

    def test_before_model_injects_system_message(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"messages": [], "current_stage": "INTAKE"}
        result = mw.before_model_legacy(state)
        assert result is not None
        messages = result["messages"]
        system_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "system"]
        assert len(system_msgs) == 1
        assert "Product Manager" in system_msgs[0]["content"]

    def test_before_model_replaces_existing_system(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {
            "messages": [{"role": "system", "content": "old prompt"}],
            "current_stage": "RESEARCH",
        }
        result = mw.before_model_legacy(state)
        messages = result["messages"]
        system_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "system"]
        assert len(system_msgs) == 1
        assert "old prompt" not in system_msgs[0]["content"]

    def test_get_prompt_for_stage(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        prompt = mw.get_prompt_for_stage("INTAKE")
        assert "Product Manager" in prompt
