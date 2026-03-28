"""Unit tests for meta_agent.tools module (Phase 1)."""

from __future__ import annotations

import os
import tempfile

import pytest
from langchain_core.messages import ToolMessage

from meta_agent.state import (
    ApprovalEntry,
    DecisionEntry,
    WorkflowStage,
    create_initial_state,
)
from meta_agent.tools import (
    InvalidTransitionError,
    PreconditionError,
    SecurityError,
    EXIT_CONDITIONS,
    _check_exit_conditions,
    transition_stage,
    record_decision,
    record_assumption,
    request_approval,
    toggle_participation,
    execute_command,
    langgraph_dev_server,
    langsmith_cli,
    glob_tool,
    grep_tool,
    get_server_side_tools,
    SERVER_SIDE_TOOLS,
)


class TestTransitionStage:
    """Tests for the transition_stage tool."""

    def test_valid_forward_transition(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/some/path/prd.md"
        result = transition_stage(state, "PRD_REVIEW", "PRD completed")
        assert result["current_stage"] == "PRD_REVIEW"
        assert len(result["decision_log"]) == 1

    def test_invalid_transition_raises(self):
        state = create_initial_state("test")
        with pytest.raises(InvalidTransitionError):
            transition_stage(state, "EXECUTION", "skip ahead")

    def test_invalid_stage_name_raises(self):
        state = create_initial_state("test")
        with pytest.raises(InvalidTransitionError, match="not a valid WorkflowStage"):
            transition_stage(state, "NONEXISTENT", "bad stage")

    def test_audit_from_any_stage(self):
        state = create_initial_state("test")
        result = transition_stage(state, "AUDIT", "audit requested")
        assert result["current_stage"] == "AUDIT"

    def test_unmet_exit_conditions_raises(self):
        state = create_initial_state("test")
        # current_prd_path is None — INTAKE exit condition not met
        with pytest.raises(PreconditionError, match="Exit conditions not met"):
            transition_stage(state, "PRD_REVIEW", "trying too early")

    def test_decision_logged_on_transition(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/path/prd.md"
        result = transition_stage(state, "PRD_REVIEW", "ready")
        entry = result["decision_log"][0]
        assert entry.decision == "Transition to PRD_REVIEW"
        assert entry.rationale == "ready"

    def test_backward_transition_after_approval(self):
        state = create_initial_state("test")
        state["current_stage"] = "PRD_REVIEW"
        # Backward transitions don't require exit conditions for PRD_REVIEW
        # but PRD_REVIEW requires approval_recorded
        state["approval_history"] = [
            ApprovalEntry.create("PRD_REVIEW", "prd.md", "approved", "user")
        ]
        result = transition_stage(state, "RESEARCH", "approved")
        assert result["current_stage"] == "RESEARCH"


class TestRecordDecision:
    """Tests for the record_decision tool."""

    def test_appends_entry(self):
        state = create_initial_state("test")
        result = record_decision(state, "Use React", "Best for this use case", ["Vue", "Angular"])
        assert len(result["decision_log"]) == 1
        entry = result["decision_log"][0]
        assert entry.decision == "Use React"
        assert entry.rationale == "Best for this use case"
        assert entry.alternatives_considered == ["Vue", "Angular"]

    def test_uses_current_stage(self):
        state = create_initial_state("test")
        state["current_stage"] = "RESEARCH"
        result = record_decision(state, "decision", "reason")
        assert result["decision_log"][0].stage == "RESEARCH"

    def test_no_alternatives(self):
        state = create_initial_state("test")
        result = record_decision(state, "choice", "reason")
        assert result["decision_log"][0].alternatives_considered == []


class TestRecordAssumption:
    """Tests for the record_assumption tool."""

    def test_appends_entry(self):
        state = create_initial_state("test")
        result = record_assumption(state, "API returns JSON", "Based on docs")
        assert len(result["assumption_log"]) == 1
        entry = result["assumption_log"][0]
        assert entry.assumption == "API returns JSON"
        assert entry.status == "open"

    def test_uses_current_stage(self):
        state = create_initial_state("test")
        state["current_stage"] = "PLANNING"
        result = record_assumption(state, "assume X", "context")
        assert result["assumption_log"][0].stage == "PLANNING"


class TestRequestApproval:
    """Tests for the request_approval tool."""

    def test_returns_interrupt_payload(self, tmp_path):
        artifact = tmp_path / "artifact.md"
        artifact.write_text("content")
        state = create_initial_state("test")
        result = request_approval(state, str(artifact), "Review this")
        assert "interrupt" in result
        assert result["interrupt"]["action"] == "request_approval"
        assert result["interrupt"]["summary"] == "Review this"

    def test_raises_on_missing_artifact(self):
        state = create_initial_state("test")
        with pytest.raises(FileNotFoundError):
            request_approval(state, "/nonexistent/path.md", "Review")


class TestToggleParticipation:
    """Tests for the toggle_participation tool."""

    def test_enable(self):
        state = create_initial_state("test")
        result = toggle_participation(state, True)
        assert result["active_participation_mode"] is True

    def test_disable(self):
        state = create_initial_state("test")
        result = toggle_participation(state, False)
        assert result["active_participation_mode"] is False


class TestExecuteCommand:
    """Tests for the execute_command tool."""

    def test_returns_interrupt_payload(self):
        state = create_initial_state("test")
        result = execute_command(state, "echo hello", "/workspace/")
        assert "interrupt" in result
        assert result["interrupt"]["action"] == "execute_command"
        assert result["interrupt"]["command"] == "echo hello"
        assert result["interrupt"]["timeout"] == 300


class TestLanggraphDevServer:
    """Tests for the langgraph_dev_server tool."""

    def test_invalid_action(self):
        result = langgraph_dev_server("invalid")
        assert "error" in result

    def test_start_requires_project_dir(self):
        result = langgraph_dev_server("start")
        assert "error" in result

    def test_start_checks_langgraph_json(self, tmp_path):
        result = langgraph_dev_server("start", str(tmp_path))
        assert "error" in result
        assert "langgraph.json" in result["error"]

    def test_status_returns_ok(self):
        result = langgraph_dev_server("status")
        assert result["status"] == "ok"


class TestGlobTool:
    """Tests for the glob_tool."""

    def test_finds_files(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.py").write_text("y")
        result = glob_tool("*.py", str(tmp_path))
        assert len(result) == 2

    def test_recursive_glob(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.py").write_text("z")
        result = glob_tool("**/*.py", str(tmp_path))
        assert len(result) >= 1

    def test_empty_result(self, tmp_path):
        result = glob_tool("*.xyz", str(tmp_path))
        assert result == []


class TestGrepTool:
    """Tests for the grep_tool."""

    def test_finds_matches_in_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world\nfoo bar\nhello again\n")
        result = grep_tool("hello", str(f))
        assert len(result) == 2
        assert result[0]["line"] == 1
        assert result[1]["line"] == 3

    def test_finds_matches_in_directory(self, tmp_path):
        (tmp_path / "a.txt").write_text("match here\n")
        (tmp_path / "b.txt").write_text("nothing relevant\n")
        result = grep_tool("match", str(tmp_path))
        assert len(result) == 1

    def test_regex_pattern(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("def foo():\n  pass\ndef bar():\n  pass\n")
        result = grep_tool(r"def \w+\(\)", str(f))
        assert len(result) == 2

    def test_empty_result(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("nothing relevant\n")
        result = grep_tool("xyz123", str(f))
        assert result == []


class TestExitConditions:
    """Tests for exit condition checking."""

    def test_intake_needs_prd_path(self):
        state = create_initial_state("test")
        unmet = _check_exit_conditions(state, "INTAKE")
        assert len(unmet) == 1
        assert "current_prd_path" in unmet[0]

    def test_intake_passes_with_prd(self):
        state = create_initial_state("test")
        state["current_prd_path"] = "/path/prd.md"
        unmet = _check_exit_conditions(state, "INTAKE")
        assert len(unmet) == 0

    def test_prd_review_needs_approval(self):
        state = create_initial_state("test")
        unmet = _check_exit_conditions(state, "PRD_REVIEW")
        assert len(unmet) == 1
        assert "approval" in unmet[0].lower()

    def test_prd_review_passes_with_approval(self):
        state = create_initial_state("test")
        state["approval_history"] = [
            ApprovalEntry.create("PRD_REVIEW", "prd.md", "approved", "user")
        ]
        unmet = _check_exit_conditions(state, "PRD_REVIEW")
        assert len(unmet) == 0


class TestServerSideTools:
    """Tests for server-side tool configs."""

    def test_web_search_config(self):
        assert SERVER_SIDE_TOOLS["web_search"]["type"] == "web_search_20260209"
        assert SERVER_SIDE_TOOLS["web_search"]["max_uses"] == 10

    def test_web_fetch_config(self):
        assert SERVER_SIDE_TOOLS["web_fetch"]["type"] == "web_fetch_20260209"

    def test_get_server_side_tools_returns_list(self):
        tools = get_server_side_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2


class TestCommandPattern:
    """Tests that state-mutating @tool wrappers return Command objects."""

    def test_transition_stage_tool_returns_command(self):
        from langgraph.types import Command
        from meta_agent.tools import transition_stage_tool
        result = transition_stage_tool.func("AUDIT", "audit needed", tool_call_id="test-call-123")
        assert isinstance(result, Command)
        assert result.update["current_stage"] == "AUDIT"
        assert len(result.update["decision_log"]) == 1
        assert any(isinstance(m, ToolMessage) for m in result.update["messages"])

    def test_record_decision_tool_returns_command(self):
        from langgraph.types import Command
        from meta_agent.tools import record_decision_tool
        result = record_decision_tool.func("Use Postgres", "Better JSON", tool_call_id="test-call-456")
        assert isinstance(result, Command)
        assert len(result.update["decision_log"]) == 1
        entry = result.update["decision_log"][0]
        assert entry.decision == "Use Postgres"
        assert entry.rationale == "Better JSON"

    def test_record_assumption_tool_returns_command(self):
        from langgraph.types import Command
        from meta_agent.tools import record_assumption_tool
        result = record_assumption_tool.func("Users prefer dark mode", "UX research", tool_call_id="test-call-789")
        assert isinstance(result, Command)
        assert len(result.update["assumption_log"]) == 1
        entry = result.update["assumption_log"][0]
        assert entry.assumption == "Users prefer dark mode"

    def test_toggle_participation_tool_returns_command(self):
        from langgraph.types import Command
        from meta_agent.tools import toggle_participation_tool
        result = toggle_participation_tool.func(True, tool_call_id="test-call-abc")
        assert isinstance(result, Command)
        assert result.update["active_participation_mode"] is True

    def test_transition_stage_tool_invalid_stage_returns_error_command(self):
        from langgraph.types import Command
        from meta_agent.tools import transition_stage_tool
        result = transition_stage_tool.func("NONEXISTENT", "bad", tool_call_id="test-call-err")
        assert isinstance(result, Command)
        assert "current_stage" not in result.update  # No stage update on error
        # Still has messages with error info
        assert len(result.update["messages"]) == 1

    def test_command_messages_have_tool_call_id(self):
        from langgraph.types import Command
        from meta_agent.tools import record_decision_tool
        result = record_decision_tool.func("Decision X", "Reason Y", tool_call_id="my-id-123")
        messages = result.update["messages"]
        assert len(messages) == 1
        assert messages[0].tool_call_id == "my-id-123"

    def test_langchain_tools_count(self):
        from meta_agent.tools import LANGCHAIN_TOOLS
        assert len(LANGCHAIN_TOOLS) == 16


class TestMetaAgentStateMiddleware:
    """Tests for the MetaAgentStateMiddleware."""

    def test_state_schema_has_custom_fields(self):
        import typing
        from meta_agent.middleware.meta_state import MetaAgentStateSchema
        hints = typing.get_type_hints(MetaAgentStateSchema, include_extras=True)
        assert "current_stage" in hints
        assert "decision_log" in hints
        assert "assumption_log" in hints
        assert "approval_history" in hints
        assert "active_participation_mode" in hints
        assert "project_id" in hints

    def test_state_schema_extends_agent_state(self):
        import typing
        from meta_agent.middleware.meta_state import MetaAgentStateSchema
        hints = typing.get_type_hints(MetaAgentStateSchema, include_extras=True)
        # Must have messages from AgentState
        assert "messages" in hints

    def test_before_agent_initializes_defaults(self):
        from meta_agent.middleware.meta_state import MetaAgentStateMiddleware
        mw = MetaAgentStateMiddleware()
        updates = mw.before_agent({}, None)
        assert updates["current_stage"] == "INTAKE"
        assert updates["active_participation_mode"] is False

    def test_before_agent_preserves_existing(self):
        from meta_agent.middleware.meta_state import MetaAgentStateMiddleware
        mw = MetaAgentStateMiddleware()
        state = {"current_stage": "RESEARCH", "active_participation_mode": True, "project_id": "foo"}
        updates = mw.before_agent(state, None)
        assert updates is None  # No updates needed

    def test_graph_has_custom_channels(self):
        from meta_agent.graph import create_graph
        graph = create_graph(project_id="test-channels")
        channels = list(graph.channels.keys())
        for field in ["current_stage", "decision_log", "approval_history", "assumption_log"]:
            assert field in channels, f"{field} not in graph channels"
