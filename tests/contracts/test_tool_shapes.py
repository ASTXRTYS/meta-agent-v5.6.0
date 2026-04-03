# REPLACES: tests/unit/test_tools.py::TestTransitionStageTool (partial — shape checks)
# REPLACES: tests/unit/test_tools.py::TestRecordDecisionTool (partial — shape checks)
# REPLACES: tests/unit/test_tools.py::TestRequestApprovalTool (partial — shape checks)
# REPLACES: tests/unit/test_eval_tools.py (partial — shape checks)
"""Contract tests for tool shapes — every tool in LANGCHAIN_TOOLS must be
correctly shaped, annotated, and invocable."""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

import pytest
from langchain_core.tools import BaseTool
from langgraph.types import Command

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools import (
    transition_stage,
    record_decision,
    record_assumption,
    request_approval,
    toggle_participation,
)
from meta_agent.tools import (
    transition_stage_tool,
    record_decision_tool,
    record_assumption_tool,
    request_approval_tool,
    request_eval_approval_tool,
    toggle_participation_tool,
    execute_command_tool,
)
from meta_agent.state import create_initial_state
from meta_agent.safety import validate_command, validate_path


# ---------------------------------------------------------------------------
# 1. Tool Instance Checks
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestToolInstances:
    """Every entry in LANGCHAIN_TOOLS must be a well-formed BaseTool."""

    def test_all_are_base_tool(self):
        for tool in LANGCHAIN_TOOLS:
            assert isinstance(tool, BaseTool), f"{tool} is not a BaseTool"

    def test_all_have_description(self):
        for tool in LANGCHAIN_TOOLS:
            assert tool.description, f"Tool {tool.name} has no description"

    def test_all_have_args_schema(self):
        for tool in LANGCHAIN_TOOLS:
            assert tool.args_schema is not None, (
                f"Tool {tool.name} has no args_schema"
            )

    def test_tool_count_is_expected(self):
        """Guard against accidental tool removal/addition."""
        assert len(LANGCHAIN_TOOLS) == 17

    def test_all_have_unique_names(self):
        names = [t.name for t in LANGCHAIN_TOOLS]
        assert len(names) == len(set(names)), (
            f"Duplicate tool names: {[n for n in names if names.count(n) > 1]}"
        )


# ---------------------------------------------------------------------------
# 2. State-Mutating Raw Functions Return Dicts with Expected Keys
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestStateMutatingRawFunctions:
    """Raw (non-@tool) state-mutating functions return dicts with expected keys."""

    def test_transition_stage_returns_dict_with_current_stage(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/tmp/prd.md"
        result = transition_stage(state, "PRD_REVIEW", "testing")
        assert isinstance(result, dict)
        assert "current_stage" in result
        assert result["current_stage"] == "PRD_REVIEW"

    def test_record_decision_returns_dict_with_decision_log(self):
        state = create_initial_state("test")
        result = record_decision(
            state=state,
            decision="Test decision",
            rationale="Test rationale",
            alternatives=["alt1"],
        )
        assert isinstance(result, dict)
        assert "decision_log" in result

    def test_record_assumption_returns_dict_with_assumption_log(self):
        state = create_initial_state("test")
        result = record_assumption(
            state=state,
            assumption="Test assumption",
            context="Test context",
        )
        assert isinstance(result, dict)
        assert "assumption_log" in result

    def test_toggle_participation_returns_dict(self):
        state = create_initial_state("test")
        result = toggle_participation(state=state, enabled=True)
        assert isinstance(result, dict)
        assert "active_participation_mode" in result
        assert result["active_participation_mode"] is True


# ---------------------------------------------------------------------------
# 3. @tool Versions Return Command Objects
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestToolWrappersReturnCommand:
    """@tool-decorated state-mutating tools return Command objects."""

    def _invoke(self, tool_obj: BaseTool, kwargs: dict[str, Any]) -> Any:
        """Invoke the underlying function of a @tool directly."""
        return tool_obj.func(**kwargs)

    def test_transition_stage_tool_returns_command(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/tmp/prd.md"
        result = self._invoke(transition_stage_tool, {
            "target_stage": "PRD_REVIEW",
            "reason": "testing",
            "tool_call_id": "test-call-id",
            "state": state,
        })
        assert isinstance(result, Command)
        assert "current_stage" in result.update

    def test_record_decision_tool_returns_command(self):
        state = create_initial_state("test")
        result = self._invoke(record_decision_tool, {
            "decision": "Test",
            "rationale": "Reason",
            "alternatives": "",
            "tool_call_id": "test-call-id",
            "state": state,
        })
        assert isinstance(result, Command)
        assert "decision_log" in result.update

    def test_record_assumption_tool_returns_command(self):
        state = create_initial_state("test")
        result = self._invoke(record_assumption_tool, {
            "assumption": "Test",
            "context": "Ctx",
            "tool_call_id": "test-call-id",
            "state": state,
        })
        assert isinstance(result, Command)
        assert "assumption_log" in result.update

    def test_toggle_participation_tool_returns_command(self):
        result = self._invoke(toggle_participation_tool, {
            "enabled": True,
            "tool_call_id": "test-call-id",
        })
        assert isinstance(result, Command)
        assert "active_participation_mode" in result.update


# ---------------------------------------------------------------------------
# 4. InjectedState and InjectedToolCallId Annotations
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestInjectedAnnotations:
    """Tools that need state injection must have InjectedState parameter."""

    _STATE_TOOLS = [
        transition_stage_tool,
        record_decision_tool,
        record_assumption_tool,
        request_approval_tool,
        request_eval_approval_tool,
        execute_command_tool,
    ]

    def test_state_tools_have_state_parameter(self):
        for tool_obj in self._STATE_TOOLS:
            fn = tool_obj.func
            sig = inspect.signature(fn)
            assert "state" in sig.parameters, (
                f"{tool_obj.name} missing 'state' parameter"
            )

    def test_state_tools_have_tool_call_id_parameter(self):
        for tool_obj in self._STATE_TOOLS:
            fn = tool_obj.func
            sig = inspect.signature(fn)
            assert "tool_call_id" in sig.parameters, (
                f"{tool_obj.name} missing 'tool_call_id' parameter"
            )

    def test_toggle_participation_has_tool_call_id(self):
        """toggle_participation_tool has tool_call_id but no state."""
        fn = toggle_participation_tool.func
        sig = inspect.signature(fn)
        assert "tool_call_id" in sig.parameters
        # toggle_participation_tool intentionally omits state


# ---------------------------------------------------------------------------
# 5. Safety Validation
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestSafetyValidation:
    """Safety module validates commands and paths correctly."""

    def test_validate_command_returns_allowed(self):
        result = validate_command("ls -la")
        assert isinstance(result, dict)
        assert result["allowed"] is True
        assert result["hitl_required"] is True

    def test_validate_command_always_hitl_required(self):
        """Every command requires HITL approval — no exceptions."""
        for cmd in ["ls", "echo hello", "python test.py"]:
            result = validate_command(cmd)
            assert result["hitl_required"] is True

    def test_validate_command_has_timeout(self):
        result = validate_command("sleep 1")
        assert "timeout" in result
        assert isinstance(result["timeout"], int)
        assert result["timeout"] > 0

    def test_validate_path_blocks_traversal(self):
        assert validate_path("../../../etc/passwd") is False

    def test_validate_path_allows_normal(self):
        assert validate_path("src/main.py") is True
