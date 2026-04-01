"""Model selection and configuration.

Spec References: Sections 22.5, 10.5
"""

from __future__ import annotations

import os
from typing import Any


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


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse ``provider:model_name`` into a (provider, model_name) tuple."""
    parts = model_string.split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "anthropic", model_string
