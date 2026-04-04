"""DynamicToolConfigMiddleware — stage-aware tool choice and filtering.

Spec Reference: Sections 22.4, 8.x

Uses wrap_model_call to dynamically set tool_choice and filter available
tools based on the current workflow stage and agent state. This enables
context-aware tool behavior without per-agent custom code.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Awaitable, Callable

from langchain.agents.middleware.types import AgentMiddleware


class DynamicToolConfigMiddleware(AgentMiddleware):
    """Middleware that dynamically configures tool_choice and tool filtering.

    Uses wrap_model_call to modify ModelRequest before each model call:
    - tool_choice: set to 'auto', 'any', or a specific tool name per-turn
    - tools: filter to a subset based on stage/state

    Configuration is driven by the tool_config dict which maps stages
    to their tool configuration. This keeps the logic declarative and
    generalized — no per-agent custom code needed.
    """

    def __init__(
        self,
        tool_config: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__()
        self.tool_config = tool_config or {}

    def _get_config_for_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Resolve tool config for the current state."""
        stage = state.get("current_stage", "")
        return self.tool_config.get(stage, {})

    def _extract_state(self, request: Any) -> dict[str, Any]:
        """Extract state dict from ModelRequest."""
        if hasattr(request, "state"):
            state = request.state
            if hasattr(state, "items"):
                return dict(state)
            if isinstance(state, dict):
                return state
        return {}

    def _apply_config(self, request: Any, config: dict[str, Any]) -> Any:
        """Apply tool_choice and tool filtering to the request."""
        updates: dict[str, Any] = {}

        # Tool choice
        tool_choice = config.get("tool_choice")
        if tool_choice is not None:
            updates["tool_choice"] = tool_choice

        # Tool filtering by allowlist
        allowed_tools = config.get("allowed_tools")
        if allowed_tools is not None and hasattr(request, "tools"):
            filtered = []
            for tool in request.tools:
                name = None
                if isinstance(tool, dict):
                    name = tool.get("name")
                elif hasattr(tool, "name"):
                    name = tool.name
                if name and name in allowed_tools:
                    filtered.append(tool)
            updates["tools"] = filtered

        if updates:
            return dataclasses.replace(request, **updates)
        return request

    def wrap_model_call(self, request: Any, handler: Callable) -> Any:
        """Apply stage-aware tool config on the request (sync)."""
        state = self._extract_state(request)
        config = self._get_config_for_state(state)
        if config:
            request = self._apply_config(request, config)
        return handler(request)

    async def awrap_model_call(self, request: Any, handler: Callable[..., Awaitable]) -> Any:
        """Apply stage-aware tool config on the request (async)."""
        state = self._extract_state(request)
        config = self._get_config_for_state(state)
        if config:
            request = self._apply_config(request, config)
        return await handler(request)
