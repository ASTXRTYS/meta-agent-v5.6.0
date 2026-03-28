"""DynamicSystemPromptMiddleware — stage-aware prompt recomposition.

Spec References: Sections 7.3, 22.4

This middleware fires its wrap_model_call hook to replace the system message
with the stage-appropriate orchestrator prompt. It MUST be ordered BEFORE
AnthropicPromptCachingMiddleware so that cache breakpoints are set on the
current (not stale) system prompt.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import SystemMessage

from meta_agent.prompts.orchestrator import construct_orchestrator_prompt


class DynamicSystemPromptMiddleware(AgentMiddleware):
    """Middleware that recomposes the system prompt based on current_stage.

    Uses wrap_model_call to set the stage-appropriate system prompt on
    ModelRequest while before_model sanitizes message history to avoid
    duplicate system messages.

    Must be first in the explicit middleware list per Section 22.4.
    """

    def __init__(
        self,
        project_dir: str = "",
        project_id: str = "",
        agents_md_content: str = "",
    ) -> None:
        super().__init__()
        self.project_dir = project_dir
        self.project_id = project_id
        self.agents_md_content = agents_md_content

    def _extract_state_dict(self, source: Any) -> dict[str, Any]:
        """Extract a plain dict view of state from request/state inputs."""
        state = source.state if hasattr(source, "state") else source
        state_dict = dict(state) if hasattr(state, "items") else {}
        return state_dict

    def _build_prompt_text(self, source: Any) -> str:
        """Build stage-appropriate prompt text from request/state inputs."""
        state_dict = self._extract_state_dict(source)

        current_stage = state_dict.get("current_stage", "INTAKE")
        project_dir = self.project_dir or state_dict.get("project_dir", "")
        project_id = self.project_id or state_dict.get("project_id", "")
        agents_md = self.agents_md_content or state_dict.get("agents_md_content", "")

        return construct_orchestrator_prompt(
            stage=current_stage,
            project_dir=project_dir,
            project_id=project_id,
            agents_md_content=agents_md,
        )

    def _replace_or_prepend_system_message(
        self,
        messages: list[Any],
        new_system_message: SystemMessage,
    ) -> list[Any]:
        """Replace first system message or prepend if no system message exists."""
        new_messages: list[Any] = []
        replaced = False
        for msg in messages:
            if _is_system_message(msg):
                if not replaced:
                    new_messages.append(new_system_message)
                    replaced = True
                continue
            new_messages.append(msg)

        if not replaced:
            new_messages.insert(0, new_system_message)

        return new_messages

    def _strip_system_messages(self, messages: list[Any]) -> list[Any]:
        """Remove all system messages from a message sequence."""
        return [msg for msg in messages if not _is_system_message(msg)]

    def _override_request_with_prompt(self, request: Any, prompt_text: str) -> Any:
        """Override ModelRequest across old/new LangChain API shapes.

        LangChain 1.0.x expects ``system_prompt: str`` while newer versions use
        ``system_message: SystemMessage``. We also strip system messages from
        request.messages to avoid provider errors about duplicate/non-consecutive
        system prompts.
        """
        new_system_message = SystemMessage(content=prompt_text)
        sanitized_messages = self._strip_system_messages(
            list(getattr(request, "messages", []))
        )

        for field_name, value in (
            ("system_message", new_system_message),
            ("system_prompt", prompt_text),
        ):
            try:
                return request.override(messages=sanitized_messages, **{field_name: value})
            except TypeError as exc:
                if "unexpected keyword argument" not in str(exc):
                    raise

        updated_messages = self._replace_or_prepend_system_message(
            sanitized_messages,
            new_system_message,
        )
        return request.override(messages=updated_messages)

    def before_model(self, state: Any, runtime: Any = None) -> dict[str, Any] | None:
        """Sanitize state messages before model call.

        System prompt is applied in wrap_model_call/awrap_model_call. Here we
        remove system messages from state history to prevent duplicate prompt
        injection across middleware and model-request fields.
        """
        state_dict = self._extract_state_dict(state)
        messages = list(state_dict.get("messages", []))
        updated_messages = self._strip_system_messages(messages)
        return {"messages": updated_messages}

    def wrap_model_call(self, request: Any, handler: Callable) -> Any:
        """Apply stage-aware system prompt on the request (sync)."""
        prompt_text = self._build_prompt_text(request)
        updated_request = self._override_request_with_prompt(request, prompt_text)
        return handler(updated_request)

    async def awrap_model_call(self, request: Any, handler: Callable[..., Awaitable]) -> Any:
        """Apply stage-aware system prompt on the request (async)."""
        prompt_text = self._build_prompt_text(request)
        updated_request = self._override_request_with_prompt(request, prompt_text)
        return await handler(updated_request)

    def before_model_legacy(self, state: Any, runtime: Any = None) -> dict[str, Any] | None:
        """Legacy before_model for backward compatibility with tests.

        NOT registered as a before_model hook (name differs intentionally to
        avoid SDK auto-detection). Tests that call before_model() are redirected
        here.
        """
        state_dict = self._extract_state_dict(state)
        prompt = self._build_prompt_text(state_dict)

        messages = list(state_dict.get("messages", []))
        system_msg = {"role": "system", "content": prompt}

        new_messages = []
        replaced = False
        for msg in messages:
            if _is_system_message(msg):
                new_messages.append(system_msg)
                replaced = True
            else:
                new_messages.append(msg)

        if not replaced:
            new_messages.insert(0, system_msg)

        return {"messages": new_messages}

    def get_prompt_for_stage(self, stage: str) -> str:
        """Get the composed prompt for a specific stage (utility method)."""
        return construct_orchestrator_prompt(
            stage=stage,
            project_dir=self.project_dir,
            project_id=self.project_id,
            agents_md_content=self.agents_md_content,
        )


def _is_system_message(msg: Any) -> bool:
    """Check if a message is a system message (dict or object)."""
    if isinstance(msg, dict):
        return msg.get("role") == "system"
    if hasattr(msg, "type"):
        return msg.type == "system"
    if hasattr(msg, "role"):
        return msg.role == "system"
    return type(msg).__name__ == "SystemMessage"
