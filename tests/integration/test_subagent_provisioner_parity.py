# REPLACES: N/A — new Track B parity gate for centralized provisioner migration.
"""Parity gate for centralized subagent middleware provisioning.

Track B cutover guard:
- Middleware sequence must match legacy runtime construction per agent.
- Stable middleware config fields must match legacy behavior.
- document-renderer special behavior must remain intact.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from meta_agent.backend import create_bare_filesystem_backend, create_composite_backend
from meta_agent.middleware.artifact_protocol import ArtifactProtocolMiddleware
from meta_agent.project import init_project
from meta_agent.subagents.provisioner import PROFILE_REGISTRY, build_provisioning_plan
from tests._support.fake_models import GenericFakeChatModel

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS_DIRS = [
    str(REPO_ROOT / '.agents' / 'skills' / 'langchain' / 'config' / 'skills'),
    str(REPO_ROOT / '.agents' / 'skills' / 'anthropic' / 'skills'),
    str(REPO_ROOT / '.agents' / 'skills' / 'langsmith' / 'config' / 'skills'),
]
DEFAULT_MODEL_SPEC = 'anthropic:claude-opus-4-6'

# Legacy middleware class order baselines captured from pre-provisioner runtimes.
LEGACY_CLASS_SEQUENCES: dict[str, list[str]] = {
    'research-agent': [
        'AgentDecisionStateMiddleware',
        'AskUserMiddleware',
        'ArtifactProtocolMiddleware',
        'SummarizationToolMiddleware',
        'MemoryMiddleware',
        'SkillsMiddleware',
        'ToolErrorMiddleware',
    ],
    'plan-writer': [
        'AgentDecisionStateMiddleware',
        'AskUserMiddleware',
        'ArtifactProtocolMiddleware',
        'SummarizationToolMiddleware',
        'MemoryMiddleware',
        'SkillsMiddleware',
        'ToolErrorMiddleware',
    ],
    'verification-agent': [
        'AgentDecisionStateMiddleware',
        'AskUserMiddleware',
        'ArtifactProtocolMiddleware',
        'MemoryMiddleware',
        'SkillsMiddleware',
        'ToolErrorMiddleware',
    ],
    'spec-writer': [
        'AskUserMiddleware',
        'ArtifactProtocolMiddleware',
        'SkillsMiddleware',
        'MemoryMiddleware',
        'ToolErrorMiddleware',
    ],
    'code-agent': [
        'AgentDecisionStateMiddleware',
        'SummarizationToolMiddleware',
        'MemoryMiddleware',
        'SkillsMiddleware',
        'ToolErrorMiddleware',
    ],
    'evaluation-agent': [
        'AgentDecisionStateMiddleware',
        'SummarizationToolMiddleware',
        'MemoryMiddleware',
        'SkillsMiddleware',
        'ToolErrorMiddleware',
    ],
    'document-renderer': [
        'MemoryMiddleware',
        'ToolErrorMiddleware',
    ],
}

MIGRATED_RUNTIME_FILES = {
    'evaluation-agent': REPO_ROOT / 'meta_agent' / 'subagents' / 'evaluation_agent_runtime.py',
    'code-agent': REPO_ROOT / 'meta_agent' / 'subagents' / 'code_agent_runtime.py',
    'plan-writer': REPO_ROOT / 'meta_agent' / 'subagents' / 'plan_writer_runtime.py',
    'verification-agent': REPO_ROOT / 'meta_agent' / 'subagents' / 'verification_agent_runtime.py',
    'research-agent': REPO_ROOT / 'meta_agent' / 'subagents' / 'research_agent.py',
    'spec-writer': REPO_ROOT / 'meta_agent' / 'subagents' / 'spec_writer_agent.py',
    'document-renderer': REPO_ROOT / 'meta_agent' / 'subagents' / 'document_renderer.py',
}


def _fake_model() -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(['stub']))


def _class_sequence(middleware: list[object]) -> list[str]:
    return [mw.__class__.__name__ for mw in middleware]


def _get_memory_middleware(middleware: list[object]) -> MemoryMiddleware:
    for mw in middleware:
        if isinstance(mw, MemoryMiddleware):
            return mw
    raise AssertionError('Missing MemoryMiddleware')


def _get_skills_middleware(middleware: list[object]) -> SkillsMiddleware:
    for mw in middleware:
        if isinstance(mw, SkillsMiddleware):
            return mw
    raise AssertionError('Missing SkillsMiddleware')


def _has_artifact_protocol_middleware(middleware: list[object]) -> bool:
    return any(isinstance(mw, ArtifactProtocolMiddleware) for mw in middleware)


@pytest.mark.integration
def test_profile_registry_contains_all_migrated_agents():
    expected_agents = set(LEGACY_CLASS_SEQUENCES)
    assert set(PROFILE_REGISTRY) == expected_agents


@pytest.mark.integration
@pytest.mark.parametrize('agent_name', sorted(LEGACY_CLASS_SEQUENCES))
def test_provisioner_matches_legacy_middleware_sequence(agent_name, tmp_path):
    project = init_project(str(tmp_path), 'Provisioner Parity', 'Track B parity sequence')
    plan = build_provisioning_plan(
        agent_name=agent_name,
        model_spec=DEFAULT_MODEL_SPEC,
        summarization_model=_fake_model(),
        project_dir=project['project_dir'],
        repo_root=REPO_ROOT,
        composite_backend=create_composite_backend(REPO_ROOT),
        bare_fs=create_bare_filesystem_backend(),
        skills_dirs=DEFAULT_SKILLS_DIRS,
    )
    assert _class_sequence(plan.middleware) == LEGACY_CLASS_SEQUENCES[agent_name]


@pytest.mark.integration
@pytest.mark.parametrize('agent_name', sorted(LEGACY_CLASS_SEQUENCES))
def test_provisioner_matches_legacy_stable_config(agent_name, tmp_path):
    project = init_project(str(tmp_path), 'Provisioner Stable Config', 'Track B parity stable config')
    project_dir = project['project_dir']

    plan = build_provisioning_plan(
        agent_name=agent_name,
        model_spec=DEFAULT_MODEL_SPEC,
        summarization_model=_fake_model(),
        project_dir=project_dir,
        repo_root=REPO_ROOT,
        composite_backend=create_composite_backend(REPO_ROOT),
        bare_fs=create_bare_filesystem_backend(),
        skills_dirs=DEFAULT_SKILLS_DIRS,
    )

    memory_mw = _get_memory_middleware(plan.middleware)
    expected_project_source = str(Path(project_dir) / '.agents' / agent_name / 'AGENTS.md')
    expected_repo_source = str(REPO_ROOT / '.agents' / agent_name / 'AGENTS.md')

    if agent_name == 'document-renderer':
        assert memory_mw.sources == [expected_repo_source]
    else:
        assert memory_mw.sources == [expected_project_source, expected_repo_source]

    if agent_name == 'document-renderer':
        assert not any(isinstance(mw, SkillsMiddleware) for mw in plan.middleware)
        assert plan.deep_agent_skills == [str(REPO_ROOT / '.agents' / 'skills' / 'anthropic' / 'skills')]
    else:
        skills_mw = _get_skills_middleware(plan.middleware)
        assert skills_mw.sources == DEFAULT_SKILLS_DIRS
        assert plan.deep_agent_skills is None

    if agent_name in {'research-agent', 'plan-writer', 'verification-agent', 'spec-writer'}:
        assert _has_artifact_protocol_middleware(plan.middleware)
        artifact_mw = next(
            mw for mw in plan.middleware if isinstance(mw, ArtifactProtocolMiddleware)
        )
        assert artifact_mw.protocols_path == '.agents/protocols/artifacts.yaml'
    else:
        assert not _has_artifact_protocol_middleware(plan.middleware)


@pytest.mark.integration
def test_project_memory_smoke_parity(tmp_path):
    project = init_project(str(tmp_path), 'Provisioner Memory Smoke', 'Track B behavior smoke')
    project_dir = project['project_dir']

    for agent_name, profile in PROFILE_REGISTRY.items():
        plan = build_provisioning_plan(
            agent_name=agent_name,
            model_spec=DEFAULT_MODEL_SPEC,
            summarization_model=_fake_model(),
            project_dir=project_dir,
            repo_root=REPO_ROOT,
            composite_backend=create_composite_backend(REPO_ROOT),
            bare_fs=create_bare_filesystem_backend(),
            skills_dirs=DEFAULT_SKILLS_DIRS,
        )
        memory_mw = _get_memory_middleware(plan.middleware)
        if profile.use_project_memory:
            assert Path(memory_mw.sources[0]).is_file()
            assert str(memory_mw.sources[0]).startswith(project_dir)
        else:
            assert memory_mw.sources == [
                str(REPO_ROOT / '.agents' / 'document-renderer' / 'AGENTS.md')
            ]


@pytest.mark.integration
def test_runtimes_are_migrated_to_central_provisioner():
    """Migration gate: runtime constructors must call build_provisioning_plan()."""
    for runtime_file in MIGRATED_RUNTIME_FILES.values():
        content = runtime_file.read_text()
        assert 'build_provisioning_plan(' in content, (
            f'Expected centralized provisioner usage in {runtime_file}'
        )
