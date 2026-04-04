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

AGENT_EFFORT_LEVELS: dict[str, str] = {
    "pm": "high",
    "research-agent": "max",
    "verification-agent": "max",
    "spec-writer": "high",
    "plan-writer": "high",
    "code-agent": "high",
    "test-agent": "medium",
    "document-renderer": "low",
    "observation-agent": "medium",
    "evaluation-agent": "medium",
    "audit-agent": "medium",
}


def get_model_config(agent_name: str = "pm") -> dict[str, Any]:
    """Return model configuration for a given agent.

    Uses ``META_AGENT_MODEL`` env var (format: ``provider:model_name``).
    Default: ``anthropic:claude-opus-4-6``.

    Adaptive thinking is configured per Section 10.5.1:
    ``thinking={"type": "adaptive"}``.  NO ``budget_tokens`` —
    deprecated on Opus 4.6 and Sonnet 4.6 (Section 10.5.4).

    Effort level is set per-agent via ``output_config``.
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
        "output_config": {"effort": effort},
    }

    # Fallback for non-Opus models — Section 10.5.4
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
    - ``max_tokens``: required when thinking is enabled
    """
    from langchain_anthropic import ChatAnthropic as _ChatAnthropic

    cfg = get_model_config(agent_name)
    effort = cfg["output_config"]["effort"]

    # max_tokens is required when thinking is enabled.
    # Higher effort levels get more headroom.
    max_tokens_map = {"max": 16000, "high": 12000, "medium": 8000, "low": 4096}
    max_tokens = max_tokens_map.get(effort, 8000)

    return _ChatAnthropic(
        model=cfg["model_name"],
        thinking=cfg["thinking"],
        effort=effort,
        max_tokens=max_tokens,
        streaming=True,
        stream_usage=True,
    )


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse ``provider:model_name`` into a (provider, model_name) tuple."""
    parts = model_string.split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "anthropic", model_string
