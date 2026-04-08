"""DynamicToolConfigMiddleware — stage-aware tool choice and filtering.

Spec Reference: Sections 22.4, 8.x

Uses wrap_model_call to dynamically set tool_choice and filter available
tools based on the current workflow stage and agent state. This enables
context-aware tool behavior without per-agent custom code.

⚠️ DEAD CODE — CURRENTLY NON-FUNCTIONAL
This middleware is initialized with tool_config={} in all agents (PM orchestrator,
research-agent, evaluation-agent, code-agent, plan-writer). With an empty config,
the middleware passes through all requests without modification. It exists as a
placeholder for future stage-aware tool policies that have not yet been authored.

IF REMOVING THIS FILE, also remove references from:
- meta_agent/graph.py (import line 55, instantiation line 156, middleware list line 167)
- meta_agent/subagents/research_agent.py (import line 31, middleware list line 697)
- meta_agent/subagents/evaluation_agent_runtime.py (import line 40, middleware list line 249)
- meta_agent/subagents/code_agent_runtime.py (import line 42, middleware list line 253)
- meta_agent/subagents/plan_writer_runtime.py (import line 40, middleware list line 247)
- meta_agent/middleware/__init__.py (import line 12, export line 20)
- tests/contracts/test_claude_api_features.py (import line 145, usage lines 147, 164, 185)
- AGENTS.md (lines 203-204 feature table)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Awaitable, Callable

from langchain.agents.middleware.types import AgentMiddleware

# Developer Note: This imports from the implementation path (...types). Consistent 
# sibling middlewares (e.g. meta_state.py) use the public path (langchain.agents.middleware).
# Consult AGENTS.md Protocol Step 5 for layer verification.


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
        # Maintainer Note: As of Phase 3, this is bootstrapped with an empty dict in 
        # graph.py (L158), serving as a placeholder until stage-aware tool 
        # policies are authored.

    def _get_config_for_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Resolve tool config for the current state.
        
        Implementation Note: Strict exact-match lookup. Does not support regex 
        or prefix-based stage policies.
        """
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

        # Maintainer Note: Use of dataclasses.replace (L76) assumes ModelRequest 
        # is a strict dataclass. Sibling middlewares use request.override() 
        # to preserve SDK-specific internal state or metadata.

        # Tool choice
        tool_choice = config.get("tool_choice")
        if tool_choice is not None:
            updates["tool_choice"] = tool_choice

        # Tool filtering by allowlist
        # Protocol Note: Manual middleware-level filtering is identified in AGENTS.md 
        # as a potential "misidentification" zone where middleware duplicates 
        # or conflicts with native Claude API "Dynamic Filtering" features.
        allowed_tools = config.get("allowed_tools")
        if allowed_tools is not None and hasattr(request, "tools"):
            filtered = []
            # Performance Note: list membership check is O(M). Filtering loop is O(N*M).
            # If allowed_tools is large, consider converting to a set once per call.
            for tool in request.tools:
                name = None
                if isinstance(tool, dict):
                    name = tool.get("name")
                elif hasattr(tool, "name"):
                    name = tool.name
                
                # Implementation Note: Name extraction is naive. It may miss 
                # tools with non-standard name attributes or complex wrapper 
                # objects not covered by this logic.
                if name and name in allowed_tools:
                    filtered.append(tool)
            updates["tools"] = filtered

        if updates:
            return dataclasses.replace(request, **updates)
        return request

    def wrap_model_call(self, request: Any, handler: Callable) -> Any:
        """Apply stage-aware tool config on the request (sync).
        
        Developer Note: Typing is 'Any'. To ensure contract safety with the 
        Deep Agents SDK, this should eventually be typed as ModelRequest[ContextT].
        """
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
