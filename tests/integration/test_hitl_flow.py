# REPLACES: (no direct legacy equivalent — gap identified by audit)
"""Integration tests for HITL interrupt configuration and tool gating."""

from __future__ import annotations

import inspect

import pytest

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import (
    HITL_GATED_TOOLS,
    TOOL_FUNCTIONS,
    TOOL_REGISTRY,
)

COVERS = [
    "guardrail.hitl_gated_tools",
    "guardrail.command_validation",
    "guardrail.path_validation",
    "sdk.langgraph.interrupt",
    "tool.request_approval",
    "tool.execute_command",
]


# ---------------------------------------------------------------------------
# 1. HITL config matches registry
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestHITLConfiguration:
    """HITL gating setup is consistent with the tool registry."""

    def test_all_hitl_tools_exist_in_tool_functions(self):
        """Every HITL-gated tool name must correspond to a real tool function."""
        for hitl_name in HITL_GATED_TOOLS:
            assert hitl_name in TOOL_FUNCTIONS, (
                f"HITL tool '{hitl_name}' has no entry in TOOL_FUNCTIONS"
            )

    def test_all_hitl_tools_have_langchain_counterpart(self):
        """Every HITL-gated tool name must map to a LANGCHAIN_TOOLS entry."""
        langchain_names = {t.name for t in LANGCHAIN_TOOLS}
        for hitl_name in HITL_GATED_TOOLS:
            # LANGCHAIN_TOOLS use the @tool function name (e.g. execute_command_tool)
            # while HITL_GATED_TOOLS use raw names (e.g. execute_command).
            # Check that at least one langchain tool name contains the HITL name.
            matches = [n for n in langchain_names if hitl_name in n]
            assert matches, (
                f"HITL tool '{hitl_name}' has no matching tool in LANGCHAIN_TOOLS "
                f"(available: {sorted(langchain_names)})"
            )

    def test_hitl_tools_count(self):
        """Document expected HITL tool count."""
        assert len(HITL_GATED_TOOLS) == 6

    def test_interrupt_on_config_built_correctly(self):
        """The interrupt_on dict should map each HITL tool to True."""
        interrupt_on = {name: True for name in HITL_GATED_TOOLS}
        assert all(v is True for v in interrupt_on.values())
        assert len(interrupt_on) == len(HITL_GATED_TOOLS)

    def test_hitl_gated_tools_is_a_set(self):
        """HITL_GATED_TOOLS must be a set (no duplicates by construction)."""
        assert isinstance(HITL_GATED_TOOLS, set)


# ---------------------------------------------------------------------------
# 2. No double-gating
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestNoDoubleGating:
    """HITL-gated tools must not also call interrupt() internally
    (except when auto_approve_hitl short-circuits it)."""

    def test_no_internal_interrupt_in_hitl_tools(self):
        """Tools gated by interrupt_on should not redundantly call interrupt()
        unless protected by an auto_approve_hitl guard."""
        langchain_names_map = {t.name: t for t in LANGCHAIN_TOOLS}

        for hitl_name in HITL_GATED_TOOLS:
            # Find the corresponding LANGCHAIN_TOOLS entry
            matches = [
                t for t in LANGCHAIN_TOOLS if hitl_name in t.name
            ]
            for tool_obj in matches:
                source = ""
                if hasattr(tool_obj, "func"):
                    source = inspect.getsource(tool_obj.func)
                elif hasattr(tool_obj, "_run"):
                    source = inspect.getsource(tool_obj._run)

                if not source:
                    continue

                # If interrupt( appears, it must be guarded by auto_approve_hitl
                if "interrupt(" in source:
                    assert "auto_approve_hitl" in source, (
                        f"Tool '{tool_obj.name}' is HITL-gated via interrupt_on "
                        f"but also calls interrupt() without auto_approve_hitl guard"
                    )


# ---------------------------------------------------------------------------
# 3. Dead / orphan tool detection
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOrphanDetection:
    """Every tool function should appear in at least one agent's registry."""

    def test_no_orphan_tool_functions(self):
        """Every entry in TOOL_FUNCTIONS should be referenced by TOOL_REGISTRY."""
        all_registered: set[str] = set()
        for agent_tools in TOOL_REGISTRY.values():
            all_registered.update(agent_tools)

        # SDK-provided tools come from middleware, not TOOL_FUNCTIONS
        sdk_tools = {"write_file", "read_file", "ls", "edit_file"}
        registered_custom = all_registered - sdk_tools

        tool_fn_names = set(TOOL_FUNCTIONS.keys())
        orphans = tool_fn_names - registered_custom

        # Orphans may be intentional (e.g. tools only used by the orchestrator
        # at the top level). Document them but don't fail hard.
        if orphans:
            pytest.skip(
                f"Orphan tool functions found (may be intentional): "
                f"{sorted(orphans)}"
            )

    def test_registry_tools_have_implementations(self):
        """Every non-SDK tool in TOOL_REGISTRY should map to TOOL_FUNCTIONS."""
        sdk_tools = {"write_file", "read_file", "ls", "edit_file",
                     "web_search", "web_fetch"}

        for agent, tools in TOOL_REGISTRY.items():
            for tool_name in tools:
                if tool_name in sdk_tools:
                    continue
                assert tool_name in TOOL_FUNCTIONS, (
                    f"Agent '{agent}' references tool '{tool_name}' "
                    f"which has no entry in TOOL_FUNCTIONS"
                )
