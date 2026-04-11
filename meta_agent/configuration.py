"""Typed environment-backed configuration for the meta-agent runtime."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass


@dataclass
class MetaAgentConfig:
    """Central configuration consolidating environment variables."""

    model_spec: str = 'anthropic:claude-opus-4-6'
    langsmith_tracing: bool = True
    langsmith_project: str = 'meta-agent'
    max_reflection_passes: int = 3

    @property
    def model_provider(self) -> str:
        return self.model_spec.split(':', 1)[0]

    @property
    def model_name(self) -> str:
        return self.model_spec.split(':', 1)[1]

    @classmethod
    def from_env(cls) -> 'MetaAgentConfig':
        raw = os.getenv('META_AGENT_MODEL', 'anthropic:claude-opus-4-6')
        if ':' not in raw:
            raise ValueError(
                "META_AGENT_MODEL must be in 'provider:model_name' format "
                f"(e.g. 'anthropic:claude-opus-4-6'), got {raw!r}"
            )
        for deprecated_var in ('META_AGENT_MODEL_PROVIDER', 'META_AGENT_MODEL_NAME'):
            if os.getenv(deprecated_var):
                warnings.warn(
                    f'{deprecated_var} is deprecated and ignored; set META_AGENT_MODEL instead',
                    DeprecationWarning,
                    stacklevel=2,
                )
        return cls(
            model_spec=raw,
            langsmith_tracing=os.getenv('LANGSMITH_TRACING', 'true').lower() == 'true',
            langsmith_project=os.getenv('LANGSMITH_PROJECT', 'meta-agent'),
            max_reflection_passes=int(os.getenv('META_AGENT_MAX_REFLECTION_PASSES', '3')),
        )
