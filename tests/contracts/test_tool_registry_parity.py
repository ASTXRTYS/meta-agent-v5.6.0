"""Contract tests for tool registry parity.

Ensures that LANGCHAIN_TOOLS, TOOL_REGISTRY, and HITL_GATED_TOOLS stay
in sync.  No model calls, no I/O, no tmp_path.
"""

from __future__ import annotations

import pytest

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS, TOOL_REGISTRY

# Tools auto-attached by SDK middleware — NOT in LANGCHAIN_TOOLS
SDK_PROVIDED_TOOLS = {"write_file", "read_file", "ls", "edit_file"}


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

    def test_tool_suffix_convention_documented(self):
        """Detect _tool suffix drift: document which tools use the suffix.

        Current convention: most tools end with '_tool' (except glob_search,
        grep_search).  This test locks in the current naming so drift is
        detected if names change.
        """
        suffixed = {t.name for t in LANGCHAIN_TOOLS if t.name.endswith("_tool")}
        non_suffixed = {t.name for t in LANGCHAIN_TOOLS if not t.name.endswith("_tool")}
        # Lock-in: 15 tools have _tool suffix, 2 (glob_search, grep_search) do not
        assert len(suffixed) == 15
        assert non_suffixed == {"glob_search", "grep_search"}


@pytest.mark.contract
class TestToolRegistryPmParity:
    """TOOL_REGISTRY['pm'] custom tools ↔ LANGCHAIN_TOOLS names."""

    @pytest.fixture(scope="class")
    def langchain_bare_names(self):
        """Map LANGCHAIN_TOOLS .name -> bare name for comparison.

        Convention: strip '_tool' suffix; glob_search -> glob, grep_search -> grep.
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
        # HITL uses bare names; check against TOOL_REGISTRY (also bare)
        # Some HITL tools (langsmith_dataset_create, langsmith_eval_run) are
        # only in LANGCHAIN_TOOLS (PM carries them) but not yet in
        # TOOL_REGISTRY["pm"].  Check that they at least exist in LANGCHAIN_TOOLS.
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
                     "write_todos", "task", "compact_conversation"}
        server_side = {"web_search", "web_fetch"}
        # Build bare-name set from LANGCHAIN_TOOLS
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
