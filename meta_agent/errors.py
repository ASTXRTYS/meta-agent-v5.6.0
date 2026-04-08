"""Error handling foundation for the meta-agent system.

Spec References: Sections 17.1-17.4

DEAD CODE NOTICE (2025-04-07): This module is currently unused.
The actual error handling is implemented via:
- ToolErrorMiddleware (meta_agent/middleware/tool_error_handler.py) for Tier 2 LLM-recoverable errors
- LangGraph's built-in retry policies (langgraph.pregel._retry) for Tier 1 transient failures
- Deep Agents SDK native patterns for HITL (Tier 3) and exception bubbling (Tier 4)

Four-tier error strategy (spec only - not implemented here):
- Tier 1: Retry (ConnectionError, TimeoutError, RateLimitError)
- Tier 2: LLM-recoverable (handle_tool_errors=True)
- Tier 3: User-fixable (interrupt() with structured error context)
- Tier 4: Unexpected (bubble up with structured error report)
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# RetryPolicy — Section 17.1 Tier 1
# ---------------------------------------------------------------------------

@dataclass
class RetryPolicy:
    """Configuration for automatic retry on transient errors."""

    max_attempts: int = 3
    initial_interval: float = 1.0
    backoff_factor: float = 2.0
    max_interval: float = 10.0
    retry_on: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
    )


# Default retry policy
DEFAULT_RETRY_POLICY = RetryPolicy()


# ---------------------------------------------------------------------------
# Structured Error Context — Section 17.4
# ---------------------------------------------------------------------------

@dataclass
class StructuredErrorContext:
    """Structured context for error reporting with all required fields."""

    error_type: str
    error_message: str
    timestamp: str
    current_stage: str
    stack_trace: str
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    recovery_suggestion: str = ""


def structured_error_context(
    error: Exception,
    current_stage: str,
    state_snapshot: dict[str, Any] | None = None,
    recovery_suggestion: str = "",
) -> StructuredErrorContext:
    """Create a structured error context from an exception.

    Contains: error_type, error_message, timestamp, current_stage,
    stack_trace, state_snapshot, recovery_suggestion.
    """
    return StructuredErrorContext(
        error_type=type(error).__name__,
        error_message=str(error),
        timestamp=datetime.now(timezone.utc).isoformat(),
        current_stage=current_stage,
        stack_trace=traceback.format_exc(),
        state_snapshot=state_snapshot or {},
        recovery_suggestion=recovery_suggestion,
    )


# ---------------------------------------------------------------------------
# Error classification helpers
# ---------------------------------------------------------------------------

def is_retryable(error: Exception) -> bool:
    """Check if an error should be retried (Tier 1)."""
    return isinstance(error, DEFAULT_RETRY_POLICY.retry_on)


def is_llm_recoverable(error: Exception) -> bool:
    """Check if an error can be recovered by the LLM (Tier 2).

    Tool errors with handle_tool_errors=True fall into this category.
    """
    return hasattr(error, "tool_name") or "tool" in type(error).__name__.lower()


def classify_error(error: Exception) -> str:
    """Classify an error into one of the four tiers.

    Returns: 'retry', 'llm_recoverable', 'user_fixable', or 'unexpected'.
    """
    if is_retryable(error):
        return "retry"
    if is_llm_recoverable(error):
        return "llm_recoverable"
    if isinstance(error, (PermissionError, FileNotFoundError, ValueError)):
        return "user_fixable"
    return "unexpected"
