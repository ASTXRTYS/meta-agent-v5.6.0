"""Unit tests for meta_agent.tools.registry module (Phase 1)."""

from __future__ import annotations

import pytest

from meta_agent.tools.registry import (
    TOOL_FUNCTIONS,
    TOOL_REGISTRY,
    HITL_GATED_TOOLS,
    get_tools_for_agent,
    get_tool_function,
    get_custom_tools_for_agent,
    is_hitl_gated,
)


class TestToolRegistry:
    """Tests for the TOOL_REGISTRY mapping."""

    def test_pm_has_tools(self):
        tools = TOOL_REGISTRY["pm"]
        assert "transition_stage" in tools
        assert "record_decision" in tools
        assert "glob" in tools

    def test_research_agent_has_web_tools(self):
        tools = TOOL_REGISTRY["research-agent"]
        assert "web_search" in tools
        assert "web_fetch" in tools

    def test_code_agent_has_dev_server(self):
        tools = TOOL_REGISTRY["code-agent"]
        assert "langgraph_dev_server" in tools
        assert "langsmith_cli" in tools

    def test_all_agents_have_entries(self):
        expected_agents = [
            "pm", "research-agent", "spec-writer",
            "plan-writer", "code-agent", "verification-agent",
            "test-agent", "document-renderer",
        ]
        for agent in expected_agents:
            assert agent in TOOL_REGISTRY, f"Missing registry entry for {agent}"


class TestToolFunctions:
    """Tests for the TOOL_FUNCTIONS mapping."""

    def test_has_all_custom_tools(self):
        expected = [
            "transition_stage", "record_decision", "record_assumption",
            "request_approval", "toggle_participation", "execute_command",
            "langgraph_dev_server", "langsmith_cli", "glob", "grep",
        ]
        for tool in expected:
            assert tool in TOOL_FUNCTIONS, f"Missing function for {tool}"

    def test_has_langsmith_tools(self):
        assert "langsmith_trace_list" in TOOL_FUNCTIONS
        assert "langsmith_trace_get" in TOOL_FUNCTIONS
        assert "langsmith_dataset_create" in TOOL_FUNCTIONS
        assert "langsmith_eval_run" in TOOL_FUNCTIONS

    def test_functions_are_callable(self):
        for name, fn in TOOL_FUNCTIONS.items():
            assert callable(fn), f"Tool {name} is not callable"


class TestGetToolFunction:
    """Tests for get_tool_function helper."""

    def test_returns_function(self):
        fn = get_tool_function("glob")
        assert fn is not None
        assert callable(fn)

    def test_returns_none_for_unknown(self):
        fn = get_tool_function("nonexistent_tool")
        assert fn is None


class TestGetToolsForAgent:
    """Tests for get_tools_for_agent helper."""

    def test_returns_tool_list(self):
        tools = get_tools_for_agent("pm")
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_unknown_agent_returns_empty(self):
        tools = get_tools_for_agent("nonexistent-agent")
        assert tools == []


class TestGetCustomToolsForAgent:
    """Tests for get_custom_tools_for_agent."""

    def test_returns_callable_functions(self):
        tools = get_custom_tools_for_agent("pm")
        assert isinstance(tools, list)
        for fn in tools:
            assert callable(fn)


class TestHitlGating:
    """Tests for HITL gating."""

    def test_execute_command_is_hitl_gated(self):
        assert is_hitl_gated("execute_command")

    def test_langsmith_dataset_create_is_hitl_gated(self):
        assert is_hitl_gated("langsmith_dataset_create")

    def test_glob_is_not_hitl_gated(self):
        assert not is_hitl_gated("glob")

    def test_record_decision_not_hitl_gated(self):
        assert not is_hitl_gated("record_decision")
