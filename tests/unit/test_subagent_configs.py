"""Unit tests for meta_agent.subagents.configs module (Phase 1)."""

from __future__ import annotations

import pytest

from meta_agent.subagents.configs import (
    SUBAGENT_CONFIGS,
    SUBAGENT_MIDDLEWARE,
    get_subagent_config,
    get_subagent_middleware,
    get_all_subagent_names,
)


pytestmark = pytest.mark.legacy


class TestSubagentConfigs:
    """Tests for the SUBAGENT_CONFIGS mapping."""

    def test_has_eight_subagents(self):
        assert len(SUBAGENT_CONFIGS) == 8

    def test_research_agent_config(self):
        cfg = SUBAGENT_CONFIGS["research-agent"]
        assert cfg["type"] == "deep_agent"
        assert cfg["effort"] == "max"
        assert cfg["recursion_limit"] == 100

    def test_code_agent_has_sub_agents(self):
        cfg = SUBAGENT_CONFIGS["code-agent"]
        assert "sub_agents" in cfg
        assert "observation-agent" in cfg["sub_agents"]
        assert "evaluation-agent" in cfg["sub_agents"]

    def test_eval_agent_is_reserved(self):
        cfg = SUBAGENT_CONFIGS["eval-agent"]
        assert cfg["type"] == "reserved"

    def test_document_renderer_is_dict_based(self):
        cfg = SUBAGENT_CONFIGS["document-renderer"]
        assert cfg["type"] == "dict_based"
        assert cfg["effort"] == "low"

    def test_all_deep_agents_have_thinking(self):
        for name, cfg in SUBAGENT_CONFIGS.items():
            if cfg["type"] == "deep_agent":
                assert "thinking" in cfg, f"{name} missing thinking config"
                assert cfg["thinking"]["type"] == "adaptive"

    def test_all_non_reserved_have_middleware(self):
        for name, cfg in SUBAGENT_CONFIGS.items():
            if cfg["type"] != "reserved":
                assert "middleware" in cfg, f"{name} missing middleware"


class TestSubagentMiddleware:
    """Tests for SUBAGENT_MIDDLEWARE mapping."""

    def test_all_have_tool_error_middleware(self):
        for name, mw_list in SUBAGENT_MIDDLEWARE.items():
            assert "ToolErrorMiddleware" in mw_list, f"{name} missing ToolErrorMiddleware"

    def test_code_agent_has_completion_guard(self):
        assert "CompletionGuardMiddleware" in SUBAGENT_MIDDLEWARE["code-agent"]

    def test_test_agent_has_completion_guard(self):
        assert "CompletionGuardMiddleware" in SUBAGENT_MIDDLEWARE["test-agent"]

    def test_observation_agent_has_completion_guard(self):
        assert "CompletionGuardMiddleware" in SUBAGENT_MIDDLEWARE["observation-agent"]

    def test_research_agent_has_summarization(self):
        assert "SummarizationToolMiddleware" in SUBAGENT_MIDDLEWARE["research-agent"]
        assert "SkillsMiddleware" in SUBAGENT_MIDDLEWARE["research-agent"]


class TestHelpers:
    """Tests for helper functions."""

    def test_get_subagent_config_exists(self):
        cfg = get_subagent_config("research-agent")
        assert cfg is not None
        assert cfg["type"] == "deep_agent"

    def test_get_subagent_config_none(self):
        cfg = get_subagent_config("nonexistent")
        assert cfg is None

    def test_get_subagent_middleware_exists(self):
        mw = get_subagent_middleware("code-agent")
        assert "ToolErrorMiddleware" in mw

    def test_get_subagent_middleware_default(self):
        mw = get_subagent_middleware("nonexistent")
        assert mw == ["ToolErrorMiddleware"]

    def test_get_all_subagent_names(self):
        names = get_all_subagent_names()
        assert len(names) == 8
        assert "research-agent" in names
        assert "eval-agent" in names
