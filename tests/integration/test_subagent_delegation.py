# REPLACES: tests/unit/test_subagent_configs.py::TestSubagentConfigs (metadata-only checks)
"""Integration tests for subagent delegation configs.

Verifies that the real subagent configurations from
meta_agent/subagents/configs.py produce SDK-compatible
SubAgent / CompiledSubAgent dicts with correct structure.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from meta_agent.subagents.configs import (
    SUBAGENT_CONFIGS,
    SUBAGENT_DESCRIPTIONS,
    SUBAGENT_MIDDLEWARE,
    build_pm_subagents,
    get_subagent_config,
    get_all_subagent_names,
)

COVERS = [
    "subagent.research-agent",
    "subagent.spec-writer",
    "subagent.verification-agent",
    "subagent.plan-writer",
    "subagent.code-agent",
    "subagent.test-agent",
    "subagent.document-renderer",
    "sdk.deepagents.SubAgent",
]


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Agents that are compiled Deep Agents (return CompiledSubAgent)
COMPILED_AGENTS = {
    "research-agent", "verification-agent", "spec-writer",
    "plan-writer", "code-agent", "evaluation-agent",
}

# All agents that build_pm_subagents iterates over
EXPECTED_BUILT_AGENTS = {
    "research-agent",
    "spec-writer",
    "plan-writer",
    "code-agent",
    "verification-agent",
    "evaluation-agent",
    "document-renderer",
}

# Agents defined in SUBAGENT_CONFIGS
EXPECTED_CONFIG_AGENTS = {
    "research-agent",
    "spec-writer",
    "plan-writer",
    "code-agent",
    "verification-agent",
    "evaluation-agent",
    "document-renderer",
}


# ---------------------------------------------------------------------------
# Tests: SUBAGENT_CONFIGS shape
# ---------------------------------------------------------------------------


class TestSubagentConfigShape:
    """Verify SUBAGENT_CONFIGS dict has the expected entries and keys."""

    def test_all_expected_agents_present(self):
        assert set(SUBAGENT_CONFIGS.keys()) == EXPECTED_CONFIG_AGENTS

    def test_no_duplicate_names(self):
        names = list(SUBAGENT_CONFIGS.keys())
        assert len(names) == len(set(names))

    def test_each_config_has_type(self):
        for name, config in SUBAGENT_CONFIGS.items():
            assert "type" in config, f"{name} missing 'type' key"

    def test_non_reserved_configs_have_effort(self):
        for name, config in SUBAGENT_CONFIGS.items():
            if config.get("type") == "reserved":
                continue
            assert "recursion_limit" in config, f"{name} missing 'recursion_limit'"
            if name != "research-agent":
                assert "effort" in config, f"{name} missing 'effort'"

    def test_research_agent_has_web_tools(self):
        cfg = SUBAGENT_CONFIGS["research-agent"]
        tools = cfg.get("tools", []) + cfg.get("server_side_tools", [])
        assert "web_search" in tools
        assert "web_fetch" in tools

    def test_spec_writer_has_propose_evals(self):
        cfg = SUBAGENT_CONFIGS["spec-writer"]
        assert "propose_evals" in cfg.get("tools", [])


# ---------------------------------------------------------------------------
# Tests: SUBAGENT_DESCRIPTIONS
# ---------------------------------------------------------------------------


class TestSubagentDescriptions:
    """Verify descriptions exist for all non-reserved agents."""

    def test_descriptions_cover_built_agents(self):
        for name in EXPECTED_BUILT_AGENTS:
            assert name in SUBAGENT_DESCRIPTIONS, f"Missing description for {name}"

    def test_descriptions_are_nonempty_strings(self):
        for name, desc in SUBAGENT_DESCRIPTIONS.items():
            assert isinstance(desc, str) and len(desc) > 10, f"Bad description for {name}"


# ---------------------------------------------------------------------------
# Tests: SUBAGENT_MIDDLEWARE
# ---------------------------------------------------------------------------


class TestSubagentMiddleware:
    """Verify middleware stacks are declared for all agents."""

    def test_middleware_entries_exist(self):
        for name in EXPECTED_BUILT_AGENTS:
            assert name in SUBAGENT_MIDDLEWARE, f"Missing middleware for {name}"

    def test_all_have_tool_error_middleware(self):
        for name, mw_list in SUBAGENT_MIDDLEWARE.items():
            assert "ToolErrorMiddleware" in mw_list, f"{name} missing ToolErrorMiddleware"


# ---------------------------------------------------------------------------
# Tests: build_pm_subagents
# ---------------------------------------------------------------------------


class TestBuildPmSubagents:
    """Test build_pm_subagents returns valid SDK-compatible entries."""

    @pytest.fixture()
    def subagents(self):
        """Build subagents with mocked compiled-agent factories to avoid API calls.

        Patches all create_*_subagent functions so that
        build_pm_subagents never hits real model creation paths
        (get_model_config → resolve_model → init_chat_model).
        """
        from deepagents.middleware.subagents import CompiledSubAgent

        mock_runnable = MagicMock()
        mock_runnable.invoke = MagicMock(return_value={"messages": []})

        def _mock_compiled(name, desc):
            return CompiledSubAgent(name=name, description=desc, runnable=mock_runnable)

        with patch(
            "meta_agent.subagents.research_agent.create_research_agent_subagent",
            return_value=_mock_compiled("research-agent", "Mock research agent."),
        ), patch(
            "meta_agent.subagents.verification_agent_runtime.create_verification_agent_subagent",
            return_value=_mock_compiled("verification-agent", "Mock verification agent."),
        ), patch(
            "meta_agent.subagents.spec_writer_agent.create_spec_writer_agent_subagent",
            return_value=_mock_compiled("spec-writer", "Mock spec-writer agent."),
        ), patch(
            "meta_agent.subagents.plan_writer_runtime.create_plan_writer_agent_subagent",
            return_value=_mock_compiled("plan-writer", "Mock plan-writer agent."),
        ), patch(
            "meta_agent.subagents.code_agent_runtime.create_code_agent_subagent",
            return_value=_mock_compiled("code-agent", "Mock code agent."),
        ), patch(
            "meta_agent.subagents.evaluation_agent_runtime.create_evaluation_agent_subagent",
            return_value=_mock_compiled("evaluation-agent", "Mock evaluation agent."),
        ):
            return build_pm_subagents(project_dir="/tmp/test", project_id="test-project")

    def test_returns_correct_count(self, subagents):
        assert len(subagents) == len(EXPECTED_BUILT_AGENTS)

    def test_all_expected_names_present(self, subagents):
        names = {_get_name(sa) for sa in subagents}
        assert names == EXPECTED_BUILT_AGENTS

    def test_no_duplicate_names_in_output(self, subagents):
        names = [_get_name(sa) for sa in subagents]
        assert len(names) == len(set(names))

    def test_compiled_subagents_have_runnable(self, subagents):
        for sa in subagents:
            name = _get_name(sa)
            if name in COMPILED_AGENTS:
                # CompiledSubAgent is a TypedDict — check for key, not attribute
                has_runnable = (
                    ("runnable" in sa) if isinstance(sa, dict) else hasattr(sa, "runnable")
                )
                assert has_runnable, f"{name} should be CompiledSubAgent with 'runnable'"

    def test_dict_subagents_have_required_keys(self, subagents):
        for sa in subagents:
            name = _get_name(sa)
            if name not in COMPILED_AGENTS and isinstance(sa, dict):
                assert "name" in sa, f"{name} missing 'name'"
                assert "description" in sa, f"{name} missing 'description'"
                assert "system_prompt" in sa, f"{name} missing 'system_prompt'"


def _get_name(sa: object) -> str:
    """Extract name from a subagent entry (dict or object)."""
    if isinstance(sa, dict):
        return sa.get("name", "")
    return getattr(sa, "name", "")
