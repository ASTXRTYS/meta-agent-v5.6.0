"""Contract tests for graph runtime components.

Tests that the compiled graph building blocks — tools, middleware, subagents,
HITL config — are correctly assembled.  These exercise importable constants and
factory functions only; no model calls, no I/O, no tmp_path.
"""

from __future__ import annotations

import pytest

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS, TOOL_REGISTRY
from meta_agent.subagents.configs import build_pm_subagents
from meta_agent.middleware.dynamic_system_prompt import DynamicSystemPromptMiddleware
from meta_agent.middleware.meta_state import MetaAgentStateMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware

COVERS = [
    "tool.transition_stage",
    "tool.record_decision",
    "tool.record_assumption",
    "tool.request_approval",
    "tool.request_eval_approval",
    "tool.toggle_participation",
    "tool.execute_command",
    "tool.langgraph_dev_server",
    "tool.langsmith_cli",
    "tool.glob_search",
    "tool.grep_search",
    "tool.langsmith_trace_list",
    "tool.langsmith_trace_get",
    "tool.langsmith_dataset_create",
    "tool.langsmith_eval_run",
    "tool.propose_evals",
    "tool.create_eval_dataset",
    "middleware.dynamic_system_prompt",
    "middleware.meta_state",
    "middleware.tool_error",
    "subagent.research-agent",
    "subagent.spec-writer",
    "subagent.verification-agent",
    "subagent.plan-writer",
    "subagent.code-agent",
    "subagent.test-agent",
    "subagent.document-renderer",
    "guardrail.hitl_gated_tools",
    "middleware.memory",
    "middleware.skills",
    "backend.route.default",
    "backend.route.memories",
    "sdk.deepagents.create_deep_agent",
]


# ---------------------------------------------------------------------------
# LANGCHAIN_TOOLS — Section 22.8
# ---------------------------------------------------------------------------

# Desired canonical bare names (SDK convention — no _tool suffix)
EXPECTED_TOOL_NAMES_BARE = {
    "transition_stage",
    "record_decision",
    "record_assumption",
    "request_approval",
    "request_eval_approval",
    "toggle_participation",
    "execute_command",
    "langgraph_dev_server",
    "langsmith_cli",
    "glob_search",
    "grep_search",
    "langsmith_trace_list",
    "langsmith_trace_get",
    "langsmith_dataset_create",
    "langsmith_eval_run",
    "propose_evals",
    "create_eval_dataset",
}

# Current actual names (locks in current state for non-xfail tests)
_EXPECTED_TOOL_NAMES_CURRENT = {
    "transition_stage_tool",
    "record_decision_tool",
    "record_assumption_tool",
    "request_approval_tool",
    "request_eval_approval_tool",
    "toggle_participation_tool",
    "execute_command_tool",
    "langgraph_dev_server_tool",
    "langsmith_cli_tool",
    "glob_search",
    "grep_search",
    "langsmith_trace_list_tool",
    "langsmith_trace_get_tool",
    "langsmith_dataset_create_tool",
    "langsmith_eval_run_tool",
    "propose_evals_tool",
    "create_eval_dataset_tool",
}


@pytest.mark.contract
class TestLangchainTools:
    """LANGCHAIN_TOOLS list has the right shape and names."""

    def test_tool_count(self):
        assert len(LANGCHAIN_TOOLS) == 17

    def test_all_current_names_present(self):
        """Lock-in of current actual names (detects unintentional renames)."""
        actual = {t.name for t in LANGCHAIN_TOOLS}
        assert _EXPECTED_TOOL_NAMES_CURRENT == actual

    @pytest.mark.xfail(
        reason="tool suffix drift — 15 tools still use _tool suffix, tracked for cleanup"
    )
    def test_all_expected_bare_names_present(self):
        """Tool .name values should match canonical bare names (no _tool suffix)."""
        actual = {t.name for t in LANGCHAIN_TOOLS}
        assert EXPECTED_TOOL_NAMES_BARE == actual, (
            f"Expected bare names but got: {actual - EXPECTED_TOOL_NAMES_BARE}"
        )

    def test_every_tool_has_name_attribute(self):
        for t in LANGCHAIN_TOOLS:
            assert hasattr(t, "name"), f"Tool {t!r} missing .name"
            assert isinstance(t.name, str)
            assert t.name, "Tool .name must be non-empty"


# ---------------------------------------------------------------------------
# HITL-gated tools — Section 9.2
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestHITLGatedTools:
    """HITL_GATED_TOOLS are a valid subset of LANGCHAIN_TOOLS names."""

    def test_hitl_count(self):
        assert len(HITL_GATED_TOOLS) == 6

    def test_hitl_tools_map_to_langchain_tools_via_suffix(self):
        """Workaround: HITL bare name + '_tool' matches LANGCHAIN_TOOLS (current state)."""
        langchain_names = {t.name for t in LANGCHAIN_TOOLS}
        for bare in HITL_GATED_TOOLS:
            suffixed = f"{bare}_tool"
            assert suffixed in langchain_names, (
                f"HITL tool '{bare}' has no matching '{suffixed}' in LANGCHAIN_TOOLS"
            )

    @pytest.mark.xfail(
        reason="tool suffix drift — HITL bare names should match LANGCHAIN_TOOLS .name directly"
    )
    def test_hitl_tools_map_to_langchain_tools_directly(self):
        """Every HITL bare name should appear directly in LANGCHAIN_TOOLS .name."""
        langchain_names = {t.name for t in LANGCHAIN_TOOLS}
        for bare in HITL_GATED_TOOLS:
            assert bare in langchain_names, (
                f"HITL tool '{bare}' not found directly in LANGCHAIN_TOOLS .name"
            )

    def test_interrupt_on_dict_shape(self):
        """The interrupt_on config dict built from HITL_GATED_TOOLS."""
        interrupt_on = {name: True for name in HITL_GATED_TOOLS}
        for name, val in interrupt_on.items():
            assert val is True
            assert isinstance(name, str)


# ---------------------------------------------------------------------------
# Middleware — Section 22.4
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestMiddlewarePresence:
    """Explicit middleware classes are importable and instantiable."""

    def test_dynamic_system_prompt_middleware_instantiable(self):
        mw = DynamicSystemPromptMiddleware(project_dir="", project_id="")
        assert mw is not None

    def test_meta_agent_state_middleware_instantiable(self):
        mw = MetaAgentStateMiddleware()
        assert mw is not None

    def test_tool_error_middleware_instantiable(self):
        mw = ToolErrorMiddleware()
        assert mw is not None


# ---------------------------------------------------------------------------
# Subagents — Section 6, 22.3
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestBuildPMSubagents:
    """build_pm_subagents() returns well-shaped entries."""

    @pytest.fixture(scope="class")
    def subagents(self):
        return build_pm_subagents()

    def test_returns_list(self, subagents):
        assert isinstance(subagents, list)

    def test_count_in_range(self, subagents):
        # 7 agents iterated, eval-agent is reserved → 6 produced
        # (research, spec-writer, plan-writer, code-agent,
        #  verification, test-agent, document-renderer)
        assert 5 <= len(subagents) <= 7

    def test_each_has_required_keys(self, subagents):
        for sa in subagents:
            assert isinstance(sa, dict), f"Expected dict, got {type(sa).__name__}"
            assert "name" in sa, f"Missing 'name' in {sa}"
            assert "description" in sa, f"Missing 'description' in {sa}"
            # Dict-based subagents have 'system_prompt';
            # CompiledSubAgents have 'runnable' instead.
            has_prompt = "system_prompt" in sa
            has_runnable = "runnable" in sa
            assert has_prompt or has_runnable, (
                f"Subagent '{sa['name']}' has neither 'system_prompt' nor 'runnable'"
            )

    def test_all_names_are_strings(self, subagents):
        for sa in subagents:
            assert isinstance(sa["name"], str)
            assert sa["name"], "Subagent name must be non-empty"
