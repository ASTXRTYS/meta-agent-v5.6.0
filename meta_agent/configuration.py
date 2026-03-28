"""Typed configuration for the meta-agent system.

Spec References: Sections 13.4.5, 22.7, 12.1
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MetaAgentConfig:
    """Central configuration consolidating all environment variables."""

    model: str = "anthropic:claude-opus-4-6"
    model_provider: str = "anthropic"
    model_name: str = "claude-opus-4-6"
    langsmith_tracing: bool = True
    langsmith_project: str = "meta-agent"
    max_reflection_passes: int = 3

    @classmethod
    def from_env(cls) -> MetaAgentConfig:
        """Load configuration from environment variables."""
        return cls(
            model=os.getenv("META_AGENT_MODEL", "anthropic:claude-opus-4-6"),
            model_provider=os.getenv("META_AGENT_MODEL_PROVIDER", "anthropic"),
            model_name=os.getenv("META_AGENT_MODEL_NAME", "claude-opus-4-6"),
            langsmith_tracing=os.getenv("LANGSMITH_TRACING", "true").lower() == "true",
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "meta-agent"),
            max_reflection_passes=int(
                os.getenv("META_AGENT_MAX_REFLECTION_PASSES", "3")
            ),
        )
