"""CompletionGuardMiddleware — prevents premature session termination.

Spec References: Sections 22.13, 2.2.1

An @after_model middleware that checks if the model response
suggests premature completion and injects nudge/confirmation messages.

Required on: code-agent.

⚠️ NAIVE IMPLEMENTATION — CONSIDER REMOVAL
This middleware has multiple technical issues and does not align with SDK/CLI patterns:

1. Logic duplication (lines 53-66): has_tool_calls/has_text computed but never used;
   real logic lives in check_response(), duplicating the same checks.

2. Hard to read (line 67): Response dict built on one massive line.

3. Type assumptions (lines 53-54, 78): Assumes content is strip()-able string, but
   AIMessage content can be blocks/multimodal shapes. str(content) vs .strip() can
   disagree on what counts as "text".

4. No SDK/CLI precedent: Neither the SDK nor deepagents_cli use @after_model hooks.
   This is a custom pattern not aligned with upstream conventions.

5. Only used on code-agent: The should_apply() method restricts it to "code-agent"
   only, but the implementation doesn't actually check which agent it's running on.

6. No test coverage: Grep found no test coverage for this middleware.

BETTER APPROACH: The problem (preventing premature completion) is better solved through:
- System prompt instructions (e.g., "Always call at least one tool per turn unless complete")
- Task state tracking in the agent's own logic
- Not middleware that blindly injects messages based on surface-level checks

IF REMOVING THIS FILE, also remove references from:
- meta_agent/subagents/code_agent_runtime.py (import line 41, middleware list line 252)
- meta_agent/subagents/configs.py (SUBAGENT_MIDDLEWARE dict line 49, _resolve_middleware_instances line 250, 254)
- meta_agent/middleware/__init__.py (import line 8, export line 17)
- Full-Development-Plan.md (multiple references)
- Full-Spec.md (multiple references)
- docs/testing/runtime_components.yaml (line 283)
- datasets/golden-path/research-decomposition.md (line 204)
- datasets/golden-path/stage3-skill-interactions.yaml (line 484)
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
        # Note (review): empty __init__ only forwards to super — no issue, just noise unless the base requires it.
        super().__init__()

    def after_model(self, state: Any, runtime: Any = None) -> dict[str, Any] | None:
        """Check last AI message for premature completion."""
        messages = state.get("messages", [])
        if not messages:
            return None

        last_msg = messages[-1]
        # Check if it's an AIMessage
        if isinstance(last_msg, AIMessage):
            # Note (review): for AIMessage, content may be non-string (e.g. blocks); str(content) here vs .strip() on the
            # string passed into check_response can disagree on what counts as "text".
            has_tool_calls = bool(last_msg.tool_calls)
            has_text = bool(last_msg.content and str(last_msg.content).strip())
        elif isinstance(last_msg, dict):
            has_tool_calls = bool(last_msg.get("tool_calls"))
            has_text = bool(last_msg.get("content", "").strip())
        else:
            return None

        # Note (review): has_tool_calls / has_text above are never used; the real rules live in check_response below.
        # That duplicates logic and can drift if one path is edited without the other.
        #
        # Note (review): this response dict is built on one long line — harder to read and change than small assignments or a helper.
        injection = self.check_response({"content": str(last_msg.content) if hasattr(last_msg, "content") else last_msg.get("content", ""), "tool_calls": last_msg.tool_calls if hasattr(last_msg, "tool_calls") else last_msg.get("tool_calls", [])})
        if injection:
            return {"messages": [HumanMessage(content=injection["content"])]}
        return None

    def check_response(self, response: dict[str, Any]) -> dict[str, Any] | None:
        """Check a model response and return an injection message if needed.

        Returns None if no intervention needed, otherwise a dict with
        the message to inject.
        """
        # Note (review): assumes content is strip()-able string; if callers pass list/multimodal shapes, behavior may not match after_model's AIMessage branch.
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
        return agent_name in {"code-agent"}
