"""Model selection and configuration.

Spec References: Sections 22.5, 10.5
"""

from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_anthropic import ChatAnthropic


# ---------------------------------------------------------------------------
# Per-agent effort levels — Section 10.5.3
# ---------------------------------------------------------------------------

AGENT_EFFORT_LEVELS: dict[str, str | None] = {
    "pm": "high",
    "research-agent": None,
    "verification-agent": "max",
    "spec-writer": "high",
    "plan-writer": "high",
    "code-agent": "high",
    "document-renderer": "low",
    "evaluation-agent": "high",
}

AGENT_MAX_TOKENS: dict[str, int] = {
    "research-agent": 16000,
}


def get_model_config(agent_name: str = "pm") -> dict[str, Any]:
    """Return model configuration for a given agent.

    Uses ``META_AGENT_MODEL`` env var (format: ``provider:model_name``).
    Default: ``anthropic:claude-opus-4-6``.

    Adaptive thinking is configured per Section 10.5.1:
    ``thinking={"type": "adaptive"}``.  NO ``budget_tokens`` —
    deprecated on Opus 4.6 and Sonnet 4.6 (Section 10.5.4).

    Effort level is set per-agent via ``output_config`` when configured.
    The research-agent intentionally omits explicit effort so Opus 4.6 runs
    with adaptive thinking alone and the API default effort behavior.
    """
    model_string = os.getenv("META_AGENT_MODEL", "anthropic:claude-opus-4-6")
    parts = model_string.split(":", 1)
    provider = parts[0] if len(parts) == 2 else "anthropic"
    model_name = parts[1] if len(parts) == 2 else model_string

    effort = AGENT_EFFORT_LEVELS.get(agent_name, "medium")

    config: dict[str, Any] = {
        "provider": provider,
        "model_name": model_name,
        "model_string": model_string,
        "thinking": {"type": "adaptive"},
    }
    if effort is not None:
        config["output_config"] = {"effort": effort}

    # TODO: Complete fallback_model implementation
    # ISSUE: fallback_model flag is set (line 69) but never read elsewhere in the codebase.
    # This suggests an incomplete implementation for handling non-Opus/Sonnet models
    # that may need budget_tokens instead of effort parameter.
    # RECOMMENDED ACTION: Either implement the fallback logic that reads this flag,
    # or remove the flag if the fallback mechanism is not needed.
    if "opus" not in model_name.lower() and "sonnet" not in model_name.lower():
        # Older models may need budget_tokens instead of effort
        config["fallback_model"] = True

    return config


def get_configured_model(agent_name: str = "pm") -> "ChatAnthropic":
    """Return a ``ChatAnthropic`` instance with adaptive thinking & effort.

    Uses :func:`get_model_config` to determine thinking config and effort
    level, then passes them directly to the ``ChatAnthropic`` constructor
    so that ``create_deep_agent(model=...)`` receives a fully-configured
    model instance rather than a bare string.

    ``ChatAnthropic`` (langchain-anthropic ≥ 1.4.0) accepts:
    - ``thinking``: ``{"type": "adaptive"}`` (Section 10.5.1)
    - ``effort``: ``"max" | "high" | "medium" | "low"`` (Section 10.5.3)
      when the agent config opts in to an explicit effort level
    - ``max_tokens``: required when thinking is enabled
    """
    from langchain_anthropic import ChatAnthropic as _ChatAnthropic

    cfg = get_model_config(agent_name)
    output_config = cfg.get("output_config", {})
    effort = output_config.get("effort")

    # max_tokens is required when thinking is enabled.
    # Higher effort levels get more headroom unless an agent-specific override
    # is configured.
    max_tokens_map = {"max": 16000, "high": 12000, "medium": 8000, "low": 4096}
    max_tokens = AGENT_MAX_TOKENS.get(agent_name, max_tokens_map.get(effort, 8000))

    kwargs: dict[str, Any] = {
        "model": cfg["model_name"],
        "thinking": cfg["thinking"],
        "max_tokens": max_tokens,
        "streaming": True,
        "stream_usage": True,
    }
    if effort is not None:
        kwargs["effort"] = effort

    return _ChatAnthropic(
        **kwargs,
    )


# DEAD CODE: This function is never called. The parsing logic is duplicated inline
# in get_model_config() (lines 50-52). Remove this function or wire it up.
def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse ``provider:model_name`` into a (provider, model_name) tuple."""
    parts = model_string.split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "anthropic", model_string
