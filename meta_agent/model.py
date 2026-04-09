"""Model selection and configuration.

Spec References: Sections 22.5, 10.5
"""

from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_anthropic import ChatAnthropic


def get_model_config(effort: str | None = None) -> dict[str, Any]:
    """Return model configuration.

    Uses ``META_AGENT_MODEL`` env var (format: ``provider:model_name``).
    Default: ``anthropic:claude-opus-4-6``.

    Adaptive thinking is configured per Section 10.5.1:
    ``thinking={"type": "adaptive"}``.  NO ``budget_tokens`` —
    deprecated on Opus 4.6 and Sonnet 4.6 (Section 10.5.4).

    Effort level is set via ``output_config`` when explicitly requested.
    """
    model_string = os.getenv("META_AGENT_MODEL", "anthropic:claude-opus-4-6")
    parts = model_string.split(":", 1)
    provider = parts[0] if len(parts) == 2 else "anthropic"
    model_name = parts[1] if len(parts) == 2 else model_string

    config: dict[str, Any] = {
        "provider": provider,
        "model_name": model_name,
        "model_string": model_string,
        "thinking": {"type": "adaptive"},
    }
    if effort is not None:
        config["output_config"] = {"effort": effort}

    return config


def get_configured_model(effort: str | None = None, max_tokens: int | None = None) -> "ChatAnthropic":
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

    cfg = get_model_config(effort=effort)
    output_config = cfg.get("output_config", {})
    resolved_effort = output_config.get("effort")

    # max_tokens is required when thinking is enabled.
    # Higher effort levels get more headroom unless an explicit override is provided.
    if max_tokens is None:
        max_tokens_map = {"max": 16000, "high": 12000, "medium": 8000, "low": 4096}
        max_tokens = max_tokens_map.get(resolved_effort, 8000)

    kwargs: dict[str, Any] = {
        "model": cfg["model_name"],
        "thinking": cfg["thinking"],
        "max_tokens": max_tokens,
        "streaming": True,
        "stream_usage": True,
    }
    if resolved_effort is not None:
        kwargs["effort"] = resolved_effort

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
