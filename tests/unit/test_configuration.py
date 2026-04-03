"""Unit tests for meta_agent.configuration and meta_agent.model modules."""

from __future__ import annotations

import os

import pytest

from meta_agent.configuration import MetaAgentConfig
from meta_agent.model import (
    AGENT_EFFORT_LEVELS,
    get_configured_model,
    get_model_config,
    parse_model_string,
)


pytestmark = pytest.mark.legacy


class TestMetaAgentConfig:
    """Tests for MetaAgentConfig."""

    def test_defaults(self):
        config = MetaAgentConfig()
        assert config.model == "anthropic:claude-opus-4-6"
        assert config.model_provider == "anthropic"
        assert config.model_name == "claude-opus-4-6"
        assert config.langsmith_tracing is True
        assert config.langsmith_project == "meta-agent"
        assert config.max_reflection_passes == 3

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("META_AGENT_MODEL", "openai:gpt-4")
        monkeypatch.setenv("META_AGENT_MODEL_PROVIDER", "openai")
        monkeypatch.setenv("META_AGENT_MODEL_NAME", "gpt-4")
        monkeypatch.setenv("LANGSMITH_TRACING", "false")
        monkeypatch.setenv("LANGSMITH_PROJECT", "test-project")
        monkeypatch.setenv("META_AGENT_MAX_REFLECTION_PASSES", "5")

        config = MetaAgentConfig.from_env()
        assert config.model == "openai:gpt-4"
        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.langsmith_tracing is False
        assert config.langsmith_project == "test-project"
        assert config.max_reflection_passes == 5

    def test_from_env_defaults(self, monkeypatch):
        # Clear relevant env vars
        for key in [
            "META_AGENT_MODEL", "META_AGENT_MODEL_PROVIDER",
            "META_AGENT_MODEL_NAME", "LANGSMITH_TRACING",
            "LANGSMITH_PROJECT", "META_AGENT_MAX_REFLECTION_PASSES",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = MetaAgentConfig.from_env()
        assert config.model == "anthropic:claude-opus-4-6"
        assert config.langsmith_tracing is True


class TestAgentEffortLevels:
    """Tests for AGENT_EFFORT_LEVELS."""

    def test_all_agents_have_levels(self):
        expected_agents = {
            "pm", "research-agent", "verification-agent",
            "spec-writer", "plan-writer", "code-agent", "test-agent",
            "document-renderer", "observation-agent", "evaluation-agent",
            "audit-agent",
        }
        assert set(AGENT_EFFORT_LEVELS.keys()) == expected_agents

    def test_valid_effort_values(self):
        valid_efforts = {"low", "medium", "high", "max"}
        for agent, effort in AGENT_EFFORT_LEVELS.items():
            assert effort in valid_efforts, f"{agent} has invalid effort: {effort}"

    def test_specific_levels(self):
        assert AGENT_EFFORT_LEVELS["pm"] == "high"
        assert AGENT_EFFORT_LEVELS["research-agent"] == "max"
        assert AGENT_EFFORT_LEVELS["document-renderer"] == "low"


class TestGetModelConfig:
    """Tests for get_model_config."""

    def test_default_config(self):
        config = get_model_config()
        assert config["provider"] == "anthropic"
        assert config["model_name"] == "claude-opus-4-6"
        assert config["thinking"] == {"type": "adaptive"}
        assert config["output_config"]["effort"] == "high"  # pm default

    def test_agent_effort(self):
        config = get_model_config("research-agent")
        assert config["output_config"]["effort"] == "max"

        config = get_model_config("document-renderer")
        assert config["output_config"]["effort"] == "low"

    def test_unknown_agent_gets_medium(self):
        config = get_model_config("unknown-agent")
        assert config["output_config"]["effort"] == "medium"

    def test_no_budget_tokens(self):
        config = get_model_config()
        assert "budget_tokens" not in config


class TestParseModelString:
    """Tests for parse_model_string."""

    def test_with_provider(self):
        provider, model = parse_model_string("anthropic:claude-opus-4-6")
        assert provider == "anthropic"
        assert model == "claude-opus-4-6"

    def test_without_provider(self):
        provider, model = parse_model_string("claude-opus-4-6")
        assert provider == "anthropic"
        assert model == "claude-opus-4-6"

    def test_openai(self):
        provider, model = parse_model_string("openai:gpt-4")
        assert provider == "openai"
        assert model == "gpt-4"



class TestGetConfiguredModel:
    """Tests for get_configured_model — CRITICAL-1 fix."""

    def test_returns_chat_anthropic_instance(self):
        from langchain_anthropic import ChatAnthropic
        model = get_configured_model("research-agent")
        assert isinstance(model, ChatAnthropic)

    def test_thinking_config_set(self):
        model = get_configured_model("research-agent")
        assert model.thinking == {"type": "adaptive"}

    def test_effort_max_for_research(self):
        model = get_configured_model("research-agent")
        assert model.effort == "max"

    def test_effort_high_for_spec_writer(self):
        model = get_configured_model("spec-writer")
        assert model.effort == "high"

    def test_effort_low_for_document_renderer(self):
        model = get_configured_model("document-renderer")
        assert model.effort == "low"

    def test_max_tokens_set(self):
        model = get_configured_model("research-agent")
        assert model.max_tokens == 16000

    def test_model_name_from_env(self):
        model = get_configured_model("pm")
        assert "claude" in model.model or "opus" in model.model

    def test_default_agent_name(self):
        model = get_configured_model()
        assert model.effort == "high"  # pm default
