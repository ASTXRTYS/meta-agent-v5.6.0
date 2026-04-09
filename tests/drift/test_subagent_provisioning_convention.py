"""Drift test: enforce centralized subagent middleware provisioning convention."""

from __future__ import annotations

from tests.drift import _venv_helper  # noqa: F401
_venv_helper.ensure_venv()

import ast
from pathlib import Path

import pytest

from meta_agent.project import PROJECT_AGENTS
from meta_agent.subagents.configs import AGENT_REGISTRY
from meta_agent.subagents.provisioner import PROFILE_REGISTRY

COVERS = []  # Meta-test

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = {
    "research-agent": REPO_ROOT / "meta_agent" / "subagents" / "research_agent.py",
    "spec-writer": REPO_ROOT / "meta_agent" / "subagents" / "spec_writer_agent.py",
    "plan-writer": REPO_ROOT / "meta_agent" / "subagents" / "plan_writer_runtime.py",
    "code-agent": REPO_ROOT / "meta_agent" / "subagents" / "code_agent_runtime.py",
    "verification-agent": REPO_ROOT / "meta_agent" / "subagents" / "verification_agent_runtime.py",
    "evaluation-agent": REPO_ROOT / "meta_agent" / "subagents" / "evaluation_agent_runtime.py",
    "document-renderer": REPO_ROOT / "meta_agent" / "subagents" / "document_renderer.py",
}

BANNED_MANUAL_CALLS = {
    "MemoryMiddleware",
    "SkillsMiddleware",
    "create_summarization_tool_middleware",
    "AskUserMiddleware",
    "ArtifactProtocolMiddleware",
    "AgentDecisionStateMiddleware",
    "ToolErrorMiddleware",
    "get_memory_sources",
}


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _called_symbols(tree: ast.AST) -> set[str]:
    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                symbols.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                symbols.add(node.func.attr)
    return symbols


@pytest.mark.drift
class TestSubagentProvisioningConvention:
    """Ensure middleware assembly remains centralized in provisioner.py."""

    def test_profile_registry_matches_agent_registry(self):
        assert set(PROFILE_REGISTRY) == set(AGENT_REGISTRY)

    def test_project_agents_align_to_project_memory_profiles(self):
        project_memory_agents = {
            name for name, profile in PROFILE_REGISTRY.items() if profile.use_project_memory
        }
        assert set(PROJECT_AGENTS) == project_memory_agents | {"pm"}

    @pytest.mark.parametrize("agent_name,path", sorted(RUNTIME_FILES.items()))
    def test_runtime_uses_central_provisioner(self, agent_name: str, path: Path):
        tree = _parse_module(path)
        called = _called_symbols(tree)
        assert "build_provisioning_plan" in called, (
            f"{agent_name} runtime must call build_provisioning_plan(): {path}"
        )

    @pytest.mark.parametrize("agent_name,path", sorted(RUNTIME_FILES.items()))
    def test_runtime_does_not_manually_build_middleware(self, agent_name: str, path: Path):
        tree = _parse_module(path)
        called = _called_symbols(tree)
        manual_calls = sorted(called & BANNED_MANUAL_CALLS)
        assert not manual_calls, (
            f"{agent_name} runtime has manual middleware construction calls {manual_calls}. "
            f"Use build_provisioning_plan() instead: {path}"
        )
