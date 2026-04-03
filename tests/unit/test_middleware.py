"""Unit tests for custom middleware."""

from __future__ import annotations

import pytest

from meta_agent.middleware import (
    ToolErrorMiddleware,
    CompletionGuardMiddleware,
)
from meta_agent.middleware.completion_guard import NUDGE_MESSAGE, CONFIRMATION_MESSAGE


pytestmark = pytest.mark.legacy


class TestToolErrorMiddleware:
    """Tests for ToolErrorMiddleware."""

    def test_successful_tool_call(self):
        mw = ToolErrorMiddleware()
        result = mw.wrap_tool_call_legacy("test_tool", lambda: "success")
        assert result["status"] == "success"
        assert result["name"] == "test_tool"
        assert result["result"] == "success"

    def test_failed_tool_call(self):
        def failing_tool():
            raise ValueError("something went wrong")

        mw = ToolErrorMiddleware()
        result = mw.wrap_tool_call_legacy("test_tool", failing_tool)
        assert result["status"] == "error"
        assert result["error_type"] == "ValueError"
        assert "something went wrong" in result["error"]
        assert result["name"] == "test_tool"

    def test_format_error_message(self):
        error = RuntimeError("test error")
        msg = ToolErrorMiddleware.format_error_message("my_tool", error)
        assert msg["error"] == "test error"
        assert msg["error_type"] == "RuntimeError"
        assert msg["status"] == "error"
        assert msg["name"] == "my_tool"

    def test_create_tool_message(self):
        error = FileNotFoundError("not found")
        msg = ToolErrorMiddleware.create_tool_message("read_file", error)
        assert msg["type"] == "tool"
        assert msg["name"] == "read_file"
        assert msg["status"] == "error"
        assert "not found" in msg["content"]

    def test_is_agent_middleware(self):
        from langchain.agents.middleware.types import AgentMiddleware
        mw = ToolErrorMiddleware()
        assert isinstance(mw, AgentMiddleware)


class TestCompletionGuardMiddleware:
    """Tests for CompletionGuardMiddleware."""

    def test_no_intervention_when_tool_calls_present(self):
        mw = CompletionGuardMiddleware()
        result = mw.check_response({
            "content": "some text",
            "tool_calls": [{"name": "write_file"}],
        })
        assert result is None

    def test_nudge_when_no_content_no_tools(self):
        mw = CompletionGuardMiddleware()
        result = mw.check_response({"content": "", "tool_calls": []})
        assert result is not None
        assert result["type"] == "nudge"
        assert result["content"] == NUDGE_MESSAGE

    def test_confirmation_when_text_no_tools(self):
        mw = CompletionGuardMiddleware()
        result = mw.check_response({
            "content": "I'm done with the task.",
            "tool_calls": [],
        })
        assert result is not None
        assert result["type"] == "confirmation"
        assert result["content"] == CONFIRMATION_MESSAGE

    def test_should_apply_to_correct_agents(self):
        assert CompletionGuardMiddleware.should_apply("code-agent")
        assert CompletionGuardMiddleware.should_apply("test-agent")
        assert CompletionGuardMiddleware.should_apply("observation-agent")
        assert not CompletionGuardMiddleware.should_apply("pm")
        assert not CompletionGuardMiddleware.should_apply("research-agent")

    def test_is_agent_middleware(self):
        from langchain.agents.middleware.types import AgentMiddleware
        mw = CompletionGuardMiddleware()
        assert isinstance(mw, AgentMiddleware)



