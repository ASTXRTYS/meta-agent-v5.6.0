"""Unit tests for DynamicSystemPromptMiddleware (Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest
from langchain_core.messages import SystemMessage

from meta_agent.middleware.dynamic_system_prompt import (
    DynamicSystemPromptMiddleware,
    _is_system_message,
)


pytestmark = pytest.mark.legacy


@dataclass
class _RequestWithSystemPrompt:
    state: dict
    messages: list
    system_prompt: str | None = None

    def override(self, **kwargs):
        return replace(self, **kwargs)


@dataclass
class _RequestWithSystemMessage:
    state: dict
    messages: list
    system_message: SystemMessage | None = None

    def override(self, **kwargs):
        return replace(self, **kwargs)


@dataclass
class _RequestWithMessagesOnly:
    state: dict
    messages: list

    def override(self, **kwargs):
        return replace(self, **kwargs)


class TestDynamicSystemPromptMiddleware:
    """Tests for the DynamicSystemPromptMiddleware."""

    def test_injects_system_message_when_none_exists(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "INTAKE", "messages": []}
        result = mw.before_model_legacy(state)
        msgs = result["messages"]
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"
        assert "Product Manager" in msgs[0]["content"]

    def test_replaces_existing_system_message(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {
            "current_stage": "INTAKE",
            "messages": [
                {"role": "system", "content": "old prompt"},
                {"role": "user", "content": "hello"},
            ],
        }
        result = mw.before_model_legacy(state)
        msgs = result["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "Product Manager" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"

    def test_intake_has_scoring_strategy(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "INTAKE", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        assert "Scoring Strategy Selection" in content

    def test_intake_has_no_delegation(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "INTAKE", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        assert "Delegation Protocol" not in content

    def test_research_has_delegation(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "RESEARCH", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        assert "Delegation Protocol" in content

    def test_research_has_no_scoring_strategy(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "RESEARCH", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        assert "Scoring Strategy Selection" not in content

    def test_prompt_changes_between_stages(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        intake_result = mw.before_model_legacy({"current_stage": "INTAKE", "messages": []})
        research_result = mw.before_model_legacy({"current_stage": "RESEARCH", "messages": []})
        assert intake_result["messages"][0]["content"] != research_result["messages"][0]["content"]

    def test_get_prompt_for_stage(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        prompt = mw.get_prompt_for_stage("INTAKE")
        assert "Product Manager" in prompt
        assert "INTAKE" in prompt

    def test_prd_review_has_eval_approval_protocol(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "PRD_REVIEW", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        # PRD_REVIEW should include EVAL_APPROVAL_PROTOCOL
        assert "PRD_REVIEW" in content

    def test_execution_has_delegation(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {"current_stage": "EXECUTION", "messages": []}
        result = mw.before_model_legacy(state)
        content = result["messages"][0]["content"]
        assert "Delegation Protocol" in content

    def test_preserves_non_system_messages(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        state = {
            "current_stage": "INTAKE",
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        }
        result = mw.before_model_legacy(state)
        msgs = result["messages"]
        assert len(msgs) == 3
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert msgs[2]["role"] == "assistant"

    def test_before_model_strips_existing_system_messages(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        result = mw.before_model(
            {
                "current_stage": "INTAKE",
                "messages": [
                    {"role": "system", "content": "old"},
                    {"role": "user", "content": "hello"},
                ],
            }
        )
        assert result is not None
        messages = result["messages"]
        assert len(messages) == 1
        assert not _is_system_message(messages[0])
        assert messages[0]["role"] == "user"

    def test_wrap_model_call_supports_system_prompt_requests(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        request = _RequestWithSystemPrompt(
            state={"current_stage": "INTAKE"},
            messages=[
                {"role": "system", "content": "old"},
                {"role": "user", "content": "hello"},
            ],
        )

        result = mw.wrap_model_call(request, lambda updated: updated)
        assert isinstance(result, _RequestWithSystemPrompt)
        assert result is not request
        assert result.system_prompt is not None
        assert "Product Manager" in result.system_prompt
        assert len(result.messages) == 1
        assert result.messages[0]["role"] == "user"

    def test_wrap_model_call_supports_system_message_requests(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        request = _RequestWithSystemMessage(
            state={"current_stage": "INTAKE"},
            messages=[{"role": "user", "content": "hello"}],
        )

        result = mw.wrap_model_call(request, lambda updated: updated)
        assert isinstance(result, _RequestWithSystemMessage)
        assert result is not request
        assert isinstance(result.system_message, SystemMessage)
        assert "Product Manager" in result.system_message.content

    def test_wrap_model_call_falls_back_to_messages_override(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        request = _RequestWithMessagesOnly(
            state={"current_stage": "INTAKE"},
            messages=[{"role": "user", "content": "hello"}],
        )

        result = mw.wrap_model_call(request, lambda updated: updated)
        assert isinstance(result, _RequestWithMessagesOnly)
        assert result is not request
        assert len(result.messages) == 2
        assert _is_system_message(result.messages[0])

    @pytest.mark.asyncio
    async def test_awrap_model_call_supports_system_prompt_requests(self):
        mw = DynamicSystemPromptMiddleware(
            project_dir="/.agents/pm/projects/test",
            project_id="test-project",
        )
        request = _RequestWithSystemPrompt(
            state={"current_stage": "INTAKE"},
            messages=[{"role": "user", "content": "hello"}],
        )

        async def _handler(updated):
            return updated

        result = await mw.awrap_model_call(request, _handler)
        assert isinstance(result, _RequestWithSystemPrompt)
        assert result is not request
        assert result.system_prompt is not None
        assert "Product Manager" in result.system_prompt


class TestIsSystemMessage:
    """Tests for _is_system_message helper."""

    def test_dict_system(self):
        assert _is_system_message({"role": "system", "content": "x"}) is True

    def test_dict_user(self):
        assert _is_system_message({"role": "user", "content": "x"}) is False

    def test_non_dict(self):
        assert _is_system_message("hello") is False
