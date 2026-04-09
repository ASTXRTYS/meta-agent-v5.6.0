"""Contract tests for tool registry parity.

Ensures that LANGCHAIN_TOOLS, TOOL_REGISTRY, and HITL_GATED_TOOLS stay
in sync.  No model calls, no I/O, no tmp_path.
"""

from __future__ import annotations

import pytest

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS, TOOL_REGISTRY

COVERS = [
    "guardrail.hitl_gated_tools",
    "tool.transition_stage",
    "tool.record_decision",
    "tool.record_assumption",
    "tool.request_approval",
    "tool.request_eval_approval",
    "tool.execute_command",
    "tool.propose_evals",
    "tool.create_eval_dataset",
]

# Tools auto-attached by SDK middleware — NOT in LANGCHAIN_TOOLS
SDK_PROVIDED_TOOLS = {"write_file", "read_file", "ls", "edit_file", "validate_artifact"}


@pytest.mark.contract
class TestToolNameAttributes:
    """Every entry in LANGCHAIN_TOOLS has a well-formed .name."""

    def test_every_tool_has_name(self):
        for t in LANGCHAIN_TOOLS:
            assert hasattr(t, "name"), f"{t!r} missing .name"
            assert isinstance(t.name, str) and t.name

    def test_no_duplicate_names(self):
        names = [t.name for t in LANGCHAIN_TOOLS]
        assert len(names) == len(set(names)), (
            f"Duplicate tool names: {[n for n in names if names.count(n) > 1]}"
        )

    @pytest.mark.xfail(
        reason="tool suffix drift — 15 tools still use _tool suffix, tracked for cleanup"
    )
    def test_no_tool_suffix_drift(self):
        """Tool .name values should not end in _tool (SDK convention is bare names)."""
        suffixed = [t.name for t in LANGCHAIN_TOOLS if t.name.endswith("_tool")]
        assert not suffixed, f"Tools with _tool suffix (should be bare names): {suffixed}"


@pytest.mark.contract
class TestToolRegistryPmParity:
    """TOOL_REGISTRY['pm'] custom tools ↔ LANGCHAIN_TOOLS names."""

    @pytest.fixture(scope="class")
    def langchain_bare_names(self):
        """Map LANGCHAIN_TOOLS .name -> bare name for comparison.

        Workaround: strips '_tool' suffix and normalises glob_search/grep_search
        until the tool suffix drift is resolved.
        """
        mapping = {}
        for t in LANGCHAIN_TOOLS:
            if t.name == "glob_search":
                mapping[t.name] = "glob"
            elif t.name == "grep_search":
                mapping[t.name] = "grep"
            elif t.name.endswith("_tool"):
                mapping[t.name] = t.name[: -len("_tool")]
            else:
                mapping[t.name] = t.name
        return set(mapping.values())

    @pytest.fixture(scope="class")
    def langchain_direct_names(self):
        """Raw .name values from LANGCHAIN_TOOLS — no suffix stripping."""
        return {t.name for t in LANGCHAIN_TOOLS}

    @pytest.mark.xfail(
        reason="tool suffix drift — LANGCHAIN_TOOLS .name values still use _tool suffix"
    )
    def test_pm_tools_match_langchain_names_directly(self, langchain_direct_names, pm_custom_tools):
        """PM custom tool names should appear directly in LANGCHAIN_TOOLS .name (no stripping needed)."""
        missing = pm_custom_tools - langchain_direct_names
        assert not missing, (
            f"TOOL_REGISTRY['pm'] bare names not found directly in LANGCHAIN_TOOLS .name: {missing}"
        )

    @pytest.fixture(scope="class")
    def pm_custom_tools(self):
        """PM tools minus SDK-provided ones."""
        return set(TOOL_REGISTRY["pm"]) - SDK_PROVIDED_TOOLS

    def test_pm_custom_tools_in_langchain(self, langchain_bare_names, pm_custom_tools):
        """Every custom tool in TOOL_REGISTRY['pm'] maps to a LANGCHAIN_TOOLS entry."""
        missing = pm_custom_tools - langchain_bare_names
        assert not missing, (
            f"TOOL_REGISTRY['pm'] lists tools not in LANGCHAIN_TOOLS: {missing}"
        )

    def test_langchain_covers_pm_custom(self, langchain_bare_names, pm_custom_tools):
        """No PM custom tool is missing from LANGCHAIN_TOOLS (bare-name match)."""
        missing = pm_custom_tools - langchain_bare_names
        assert not missing, (
            f"PM custom tools missing from LANGCHAIN_TOOLS: {missing}"
        )


@pytest.mark.contract
class TestHITLRegistryParity:
    """Every HITL-gated tool appears in at least one agent's TOOL_REGISTRY."""

    def test_hitl_tools_in_some_agent(self):
        """Every HITL bare name appears in at least one agent's registry."""
        all_registered = set()
        for tools in TOOL_REGISTRY.values():
            all_registered.update(tools)
        # Workaround: strip _tool suffix until drift is resolved.
        langchain_bare = set()
        for t in LANGCHAIN_TOOLS:
            if t.name.endswith("_tool"):
                langchain_bare.add(t.name[: -len("_tool")])
            elif t.name == "glob_search":
                langchain_bare.add("glob")
            elif t.name == "grep_search":
                langchain_bare.add("grep")
            else:
                langchain_bare.add(t.name)
        combined = all_registered | langchain_bare
        missing = HITL_GATED_TOOLS - combined
        assert not missing, (
            f"HITL tools not in any registry or LANGCHAIN_TOOLS: {missing}"
        )

    @pytest.mark.xfail(
        reason="tool suffix drift — HITL bare names not directly in LANGCHAIN_TOOLS .name"
    )
    def test_hitl_bare_names_match_langchain_directly(self):
        """HITL bare names should match LANGCHAIN_TOOLS .name directly (no suffix stripping)."""
        langchain_names = {t.name for t in LANGCHAIN_TOOLS}
        all_registered = set()
        for tools in TOOL_REGISTRY.values():
            all_registered.update(tools)
        combined = all_registered | langchain_names
        missing = HITL_GATED_TOOLS - combined
        assert not missing, (
            f"HITL bare names not found directly in LANGCHAIN_TOOLS .name: {missing}"
        )


@pytest.mark.contract
class TestCrossAgentConsistency:
    """Broad checks across all agents in the registry."""

    def test_every_agent_has_at_least_one_tool(self):
        for agent, tools in TOOL_REGISTRY.items():
            assert len(tools) > 0, f"Agent '{agent}' has no tools"

    def test_no_unknown_sdk_tool_names(self):
        """Every tool name in TOOL_REGISTRY is either SDK-provided,
        a LANGCHAIN_TOOLS bare name, or a server-side tool."""
        known_sdk = {"write_file", "read_file", "ls", "edit_file",
                     "write_todos", "task", "compact_conversation", "validate_artifact"}
        server_side = {"web_search", "web_fetch"}
        # Workaround: strip _tool suffix until drift is resolved.
        langchain_bare = set()
        for t in LANGCHAIN_TOOLS:
            if t.name == "glob_search":
                langchain_bare.add("glob")
            elif t.name == "grep_search":
                langchain_bare.add("grep")
            elif t.name.endswith("_tool"):
                langchain_bare.add(t.name[: -len("_tool")])
            else:
                langchain_bare.add(t.name)
        all_names = set()
        for tools in TOOL_REGISTRY.values():
            all_names.update(tools)
        unrecognised = all_names - langchain_bare - known_sdk - server_side
        assert not unrecognised, (
            f"Unrecognised tool names in TOOL_REGISTRY: {unrecognised}"
        )

    @pytest.mark.xfail(
        reason="tool suffix drift — TOOL_REGISTRY bare names not directly in LANGCHAIN_TOOLS .name"
    )
    def test_registry_names_match_langchain_directly(self):
        """Every TOOL_REGISTRY name should match LANGCHAIN_TOOLS .name directly."""
        known_sdk = {"write_file", "read_file", "ls", "edit_file",
                     "write_todos", "task", "compact_conversation", "validate_artifact"}
        server_side = {"web_search", "web_fetch"}
        langchain_names = {t.name for t in LANGCHAIN_TOOLS}
        all_names = set()
        for tools in TOOL_REGISTRY.values():
            all_names.update(tools)
        unrecognised = all_names - langchain_names - known_sdk - server_side
        assert not unrecognised, (
            f"TOOL_REGISTRY names not found directly in LANGCHAIN_TOOLS .name: {unrecognised}"
        )
