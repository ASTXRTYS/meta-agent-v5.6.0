"""Custom middleware package for the meta-agent system.

Spec Reference: Section 22.11
"""

from .agent_decision_state import AgentDecisionStateMiddleware
from .tool_error_handler import ToolErrorMiddleware
from .completion_guard import CompletionGuardMiddleware
# MemoryLoaderMiddleware: likely dead — see urgent note in memory_loader.py before removing.
from .memory_loader import MemoryLoaderMiddleware
from .dynamic_system_prompt import DynamicSystemPromptMiddleware
from .dynamic_tool_config import DynamicToolConfigMiddleware

__all__ = [
    "AgentDecisionStateMiddleware",
    "ToolErrorMiddleware",
    "CompletionGuardMiddleware",
    "MemoryLoaderMiddleware",
    "DynamicSystemPromptMiddleware",
    "DynamicToolConfigMiddleware",
]
