"""ToolErrorMiddleware — wraps all tool calls in try/except.

Spec References: Sections 22.12, 2.2.1

Converts unhandled exceptions into ToolMessage(status="error") with
a structured JSON payload so the LLM can see the failure and self-correct
rather than crashing the agent run.

Required on ALL agents (orchestrator and all subagents).
"""

from __future__ import annotations

import json
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage


class ToolErrorMiddleware(AgentMiddleware):
    """Middleware that wraps tool calls in try/except.

    On error, produces a ToolMessage with ``status="error"`` and
    a JSON payload: ``{"error": "<message>", "error_type": "<class>",
    "status": "error", "name": "<tool_name>"}``.
    """

    def __init__(self) -> None:
        super().__init__()

    def _extract_tool_info(self, request: Any) -> tuple[str, str]:
        """Extract tool name and call ID from a request."""
        tool_call = request.tool_call if hasattr(request, "tool_call") else {}
        tool_name = tool_call.get("name", "unknown") if isinstance(tool_call, dict) else "unknown"
        tool_call_id = tool_call.get("id", "unknown") if isinstance(tool_call, dict) else "unknown"
        return tool_name, tool_call_id

    def _make_error_message(self, e: Exception, tool_name: str, tool_call_id: str) -> ToolMessage:
        """Create a ToolMessage with structured error payload."""
        error_payload = json.dumps({
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "error",
            "name": tool_name,
        })
        return ToolMessage(
            content=error_payload,
            name=tool_name,
            tool_call_id=tool_call_id,
            status="error",
        )

    def wrap_tool_call(
        self, request: Any, handler: Any,
    ) -> Any:
        """Execute a tool call with error handling (sync)."""
        try:
            return handler(request)
        except Exception as e:
            tool_name, tool_call_id = self._extract_tool_info(request)
            return self._make_error_message(e, tool_name, tool_call_id)

    async def awrap_tool_call(
        self, request: Any, handler: Any,
    ) -> Any:
        """Execute a tool call with error handling (async).

        Required for LangGraph Studio / astream() / ainvoke() compatibility.
        """
        try:
            return await handler(request)
        except Exception as e:
            tool_name, tool_call_id = self._extract_tool_info(request)
            return self._make_error_message(e, tool_name, tool_call_id)

    # --- Legacy convenience methods (used by tests & internal code) ---

    @staticmethod
    def wrap_tool_call_legacy(
        tool_name: str, tool_fn: Any, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute a tool call with error handling (legacy interface).

        Returns the tool result on success, or a structured error
        payload on failure.
        """
        try:
            result = tool_fn(*args, **kwargs)
            return {"result": result, "status": "success", "name": tool_name}
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "error",
                "name": tool_name,
            }

    @staticmethod
    def format_error_message(
        tool_name: str, error: Exception
    ) -> dict[str, str]:
        """Format an exception as a structured JSON error payload."""
        return {
            "error": str(error),
            "error_type": type(error).__name__,
            "status": "error",
            "name": tool_name,
        }

    @staticmethod
    def create_tool_message(tool_name: str, error: Exception) -> dict[str, Any]:
        """Create a ToolMessage-compatible dict with error status."""
        return {
            "type": "tool",
            "name": tool_name,
            "content": json.dumps({
                "error": str(error),
                "error_type": type(error).__name__,
                "status": "error",
                "name": tool_name,
            }),
            "status": "error",
        }
