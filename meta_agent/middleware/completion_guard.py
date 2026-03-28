"""CompletionGuardMiddleware — prevents premature session termination.

Spec References: Sections 22.13, 2.2.1

An @after_model middleware that checks if the model response
suggests premature completion and injects nudge/confirmation messages.

Required on: code-agent, test-agent, observation-agent.
"""

from __future__ import annotations

from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import AIMessage, HumanMessage


NUDGE_MESSAGE = (
    "No tool was called. Please continue with the task, ensuring you call "
    "at least one tool in every turn unless you are certain the task is complete."
)

CONFIRMATION_MESSAGE = (
    "You did not call a tool, which would end the task. If the task is truly "
    "complete, confirm by calling write_file to update the progress log. "
    "Otherwise, continue working."
)


class CompletionGuardMiddleware(AgentMiddleware):
    """Middleware that prevents premature session termination.

    After the model returns a response:
    - If no tool calls AND no text content: inject nudge message
    - If text but no tool calls (potential premature completion):
      inject confirmation check
    """

    def __init__(self) -> None:
        super().__init__()

    def after_model(self, state: Any, runtime: Any = None) -> dict[str, Any] | None:
        """Check last AI message for premature completion."""
        messages = state.get("messages", [])
        if not messages:
            return None

        last_msg = messages[-1]
        # Check if it's an AIMessage
        if isinstance(last_msg, AIMessage):
            has_tool_calls = bool(last_msg.tool_calls)
            has_text = bool(last_msg.content and str(last_msg.content).strip())
        elif isinstance(last_msg, dict):
            has_tool_calls = bool(last_msg.get("tool_calls"))
            has_text = bool(last_msg.get("content", "").strip())
        else:
            return None

        injection = self.check_response({"content": str(last_msg.content) if hasattr(last_msg, "content") else last_msg.get("content", ""), "tool_calls": last_msg.tool_calls if hasattr(last_msg, "tool_calls") else last_msg.get("tool_calls", [])})
        if injection:
            return {"messages": [HumanMessage(content=injection["content"])]}
        return None

    def check_response(self, response: dict[str, Any]) -> dict[str, Any] | None:
        """Check a model response and return an injection message if needed.

        Returns None if no intervention needed, otherwise a dict with
        the message to inject.
        """
        has_tool_calls = bool(response.get("tool_calls"))
        has_text = bool(response.get("content", "").strip())

        if not has_tool_calls and not has_text:
            return {
                "type": "nudge",
                "content": NUDGE_MESSAGE,
            }

        if has_text and not has_tool_calls:
            return {
                "type": "confirmation",
                "content": CONFIRMATION_MESSAGE,
            }

        return None

    @staticmethod
    def should_apply(agent_name: str) -> bool:
        """Check if this middleware should be applied to the given agent."""
        return agent_name in {"code-agent", "test-agent", "observation-agent"}
