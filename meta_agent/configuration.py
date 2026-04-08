"""Typed configuration for the meta-agent system.

Spec References: Sections 13.4.5, 22.7, 12.1

DESIGN INTENT (per Section 12.1, 13.4.5):
This module should consolidate ALL environment variable access following the
enterprise-deep-research pattern. Model configuration (META_AGENT_MODEL, 
META_AGENT_MODEL_PROVIDER, META_AGENT_MODEL_NAME) was moved here in v5.5 to
centralize what was previously scattered inline os.environ.get() calls.

CURRENT REALITY:
This module does NOT own model configuration. model.py's get_configured_model()
reads META_AGENT_MODEL directly from os.environ and constructs ChatAnthropic
instances. The model fields below are loaded but UNUSED at runtime.

TODO - Consolidation Required:
Option A: Refactor model.py to use MetaAgentConfig.from_env() as the single
source of truth for model configuration (aligns with spec intent).
Option B: Remove model fields from this class and concede model configuration
to model.py (requires updating Section 12.1, 13.4.5 in Full-Spec.md).

KNOWN DUPLICATION:
- Defaults exist in both dataclass field defaults AND os.getenv() fallbacks
- META_AGENT_MODEL parsing logic exists in both this file AND model.py
- max_reflection_passes is used; model fields are NOT used

NOTE: Eval infrastructure (judge_infra.py) maintains its own env handling for
RESEARCH_EVAL_JUDGE_* vars and does not use this config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MetaAgentConfig:
    """Central configuration consolidating all environment variables."""

    # DESIGN FLAW: These model fields are defined but UNUSED.
    # model.py's get_configured_model() bypasses this config entirely.
    # See module docstring for consolidation TODO.
    model: str = "anthropic:claude-opus-4-6"  # UNUSED - model.py reads env directly
    model_provider: str = "anthropic"         # UNUSED - model.py parses from META_AGENT_MODEL
    model_name: str = "claude-opus-4-6"       # UNUSED - model.py parses from META_AGENT_MODEL
    langsmith_tracing: bool = True
    langsmith_project: str = "meta-agent"
    max_reflection_passes: int = 3
    # NOTE: This field IS used (by orchestrator reflection logic).
    # int() cast will raise ValueError on invalid input.

    @classmethod
    def from_env(cls) -> MetaAgentConfig:
        """Load configuration from environment variables.

        WARNING: Model env vars (META_AGENT_MODEL, etc.) are loaded here but
        model.py ignores them and reads from os.environ directly. This creates
        a divergence risk: config values may differ from runtime values.
        """
        return cls(
            model=os.getenv("META_AGENT_MODEL", "anthropic:claude-opus-4-6"),
            model_provider=os.getenv("META_AGENT_MODEL_PROVIDER", "anthropic"),
            model_name=os.getenv("META_AGENT_MODEL_NAME", "claude-opus-4-6"),
            langsmith_tracing=os.getenv("LANGSMITH_TRACING", "true").lower() == "true",
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "meta-agent"),
            max_reflection_passes=int(
                # NOTE: This is the ONLY field here that IS used at runtime.
                # Compare to judge_infra.py's _bool_env() for safe parsing.
                os.getenv("META_AGENT_MAX_REFLECTION_PASSES", "3")
            ),
        )
