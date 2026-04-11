"""Centralized subagent middleware provisioning with profile-driven assembly.

This module standardizes middleware construction across runtime agents while
preserving per-agent ordering and configuration differences.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.summarization import create_summarization_tool_middleware
from langchain_core.language_models import BaseChatModel

from meta_agent.config.memory import get_memory_sources
from meta_agent.middleware.agent_decision_state import AgentDecisionStateMiddleware
from meta_agent.middleware.artifact_protocol import ArtifactProtocolMiddleware
from meta_agent.middleware.ask_user import AskUserMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware

MiddlewareToken = Literal[
    'decision_state',
    'ask_user',
    'artifact_protocol',
    'summarization_tool',
    'memory',
    'skills',
    'tool_error',
]


@dataclass(frozen=True)
class SubagentProvisioningProfile:
    middleware_sequence: tuple[MiddlewareToken, ...]
    use_project_memory: bool
    use_skills_middleware: bool
    use_create_deep_agent_skills_arg: bool


@dataclass(frozen=True)
class ProvisioningPlan:
    middleware: list[object]
    deep_agent_skills: list[str] | None
    fingerprint: list[tuple[str, tuple[tuple[str, str], ...]]]


PROFILE_REGISTRY: dict[str, SubagentProvisioningProfile] = {
    'research-agent': SubagentProvisioningProfile(
        middleware_sequence=(
            'decision_state',
            'ask_user',
            'artifact_protocol',
            'summarization_tool',
            'memory',
            'skills',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'plan-writer': SubagentProvisioningProfile(
        middleware_sequence=(
            'decision_state',
            'ask_user',
            'artifact_protocol',
            'summarization_tool',
            'memory',
            'skills',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'verification-agent': SubagentProvisioningProfile(
        middleware_sequence=(
            'decision_state',
            'ask_user',
            'artifact_protocol',
            'memory',
            'skills',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'spec-writer': SubagentProvisioningProfile(
        middleware_sequence=(
            'ask_user',
            'artifact_protocol',
            'skills',
            'memory',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'code-agent': SubagentProvisioningProfile(
        middleware_sequence=(
            'decision_state',
            'summarization_tool',
            'memory',
            'skills',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'evaluation-agent': SubagentProvisioningProfile(
        middleware_sequence=(
            'decision_state',
            'summarization_tool',
            'memory',
            'skills',
            'tool_error',
        ),
        use_project_memory=True,
        use_skills_middleware=True,
        use_create_deep_agent_skills_arg=False,
    ),
    'document-renderer': SubagentProvisioningProfile(
        middleware_sequence=('memory', 'tool_error'),
        use_project_memory=False,
        use_skills_middleware=False,
        use_create_deep_agent_skills_arg=True,
    ),
}


def _token_to_middleware(
    *,
    token: MiddlewareToken,
    agent_name: str,
    model_spec: str,
    summarization_model: BaseChatModel,
    project_dir: str,
    repo_root: Path,
    composite_backend: object,
    bare_fs: object,
    skills_dirs: list[str] | None,
    profile: SubagentProvisioningProfile,
) -> object:
    if token == 'decision_state':
        return AgentDecisionStateMiddleware()
    if token == 'ask_user':
        return AskUserMiddleware()
    if token == 'artifact_protocol':
        return ArtifactProtocolMiddleware(backend=bare_fs)
    if token == 'summarization_tool':
        _ = model_spec
        return create_summarization_tool_middleware(summarization_model, composite_backend)
    if token == 'memory':
        memory_sources = get_memory_sources(
            agent_name,
            project_dir if profile.use_project_memory else None,
            repo_root,
        )
        return MemoryMiddleware(backend=bare_fs, sources=memory_sources)
    if token == 'skills':
        if not profile.use_skills_middleware:
            raise ValueError(
                f"Profile '{agent_name}' does not allow skills middleware, "
                "but token sequence requested 'skills'."
            )
        return SkillsMiddleware(backend=bare_fs, sources=skills_dirs or [])
    if token == 'tool_error':
        return ToolErrorMiddleware()

    raise ValueError(f'Unknown middleware token: {token}')


def _anthropic_skills_only(skills_dirs: list[str] | None) -> list[str]:
    anthropic_dir = next((path for path in (skills_dirs or []) if 'anthropic' in path), None)
    return [anthropic_dir] if anthropic_dir else []


def _serialize_stable_fields(middleware_obj: object) -> tuple[tuple[str, str], ...]:
    if isinstance(middleware_obj, MemoryMiddleware):
        return (('sources', '|'.join(middleware_obj.sources)),)
    if isinstance(middleware_obj, SkillsMiddleware):
        return (('sources', '|'.join(middleware_obj.sources)),)
    if isinstance(middleware_obj, ArtifactProtocolMiddleware):
        return (('protocols_path', middleware_obj.protocols_path),)
    return ()


def build_fingerprint(middleware: list[object]) -> list[tuple[str, tuple[tuple[str, str], ...]]]:
    return [
        (middleware_obj.__class__.__name__, _serialize_stable_fields(middleware_obj))
        for middleware_obj in middleware
    ]


def build_provisioning_plan(
    *,
    agent_name: str,
    model_spec: str,
    summarization_model: BaseChatModel,
    project_dir: str,
    repo_root: Path,
    composite_backend: object,
    bare_fs: object,
    skills_dirs: list[str] | None,
) -> ProvisioningPlan:
    """Assemble middleware in profile order and return plan + fingerprint."""
    profile = PROFILE_REGISTRY.get(agent_name)
    if profile is None:
        raise ValueError(
            f"Unknown subagent provisioning profile '{agent_name}'. "
            f'Known agents: {sorted(PROFILE_REGISTRY)}'
        )

    middleware = [
        _token_to_middleware(
            token=token,
            agent_name=agent_name,
            model_spec=model_spec,
            summarization_model=summarization_model,
            project_dir=project_dir,
            repo_root=repo_root,
            composite_backend=composite_backend,
            bare_fs=bare_fs,
            skills_dirs=skills_dirs,
            profile=profile,
        )
        for token in profile.middleware_sequence
    ]

    deep_agent_skills = (
        _anthropic_skills_only(skills_dirs)
        if profile.use_create_deep_agent_skills_arg
        else None
    )

    return ProvisioningPlan(
        middleware=middleware,
        deep_agent_skills=deep_agent_skills,
        fingerprint=build_fingerprint(middleware),
    )
