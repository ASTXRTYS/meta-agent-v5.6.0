"""Unit tests for meta_agent.tools module (Phase 1)."""

from __future__ import annotations

import pytest

from meta_agent.state import (
    ApprovalEntry,
    create_initial_state,
)
from meta_agent.tools import (
    EXIT_CONDITIONS,
    _check_exit_conditions,
    toggle_participation,
    execute_command,
    langgraph_dev_server,
    langsmith_cli,
    glob_tool,
    grep_tool,
    get_server_side_tools,
    SERVER_SIDE_TOOLS,
)


pytestmark = pytest.mark.legacy





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
        state = {
            "current_stage": "RESEARCH",
            "active_participation_mode": True,
            "project_id": "foo",
            "verification_results": {},
            "spec_generation_feedback_cycles": 0,
            "pending_research_gap_request": None,
        }
        updates = mw.before_agent(state, None)
        assert updates is None  # No updates needed

    def test_graph_has_custom_channels(self):
        from meta_agent.graph import create_graph
        graph = create_graph(project_id="test-channels")
        channels = list(graph.channels.keys())
        for field in ["current_stage", "decision_log", "approval_history", "assumption_log"]:
            assert field in channels, f"{field} not in graph channels"


class TestRequestEvalApprovalTool:
    """Tests for request_eval_approval_tool."""

    def test_request_eval_approval_tool_exists(self):
        from meta_agent.tools import LANGCHAIN_TOOLS
        tool_names = [t.name for t in LANGCHAIN_TOOLS]
        assert "request_eval_approval_tool" in tool_names
