# REPLACES: tests/unit/test_middleware.py::TestMemoryLoaderMiddleware (if it exists)
"""Integration tests for MemoryMiddleware and SkillsMiddleware configuration.

Validates that our middleware can be constructed with the correct backend types,
and that the source paths referenced in graph.py actually exist on disk.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from deepagents.backends import FilesystemBackend
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from meta_agent.backend import create_bare_filesystem_backend
from meta_agent.config.memory import get_memory_sources
from meta_agent.project import PROJECT_AGENTS, init_project
from meta_agent.subagents.provisioner import PROFILE_REGISTRY
from meta_agent.subagents.evaluation_agent_runtime import create_evaluation_agent_graph

COVERS = [
    "middleware.memory",
    "middleware.skills",
    "middleware.dynamic_system_prompt",
    "middleware.meta_state",
    "middleware.tool_error",
    "sdk.deepagents.MemoryMiddleware",
    "sdk.deepagents.SkillsMiddleware",
]


# Repo root — same derivation as graph.py uses
REPO_ROOT = Path(__file__).resolve().parents[2]


PROJECT_SCOPED_MEMORY_CALL_RE = re.compile(
    r'get_memory_sources\("(?P<agent>[^"]+)"\s*,\s*project_dir\s*,\s*repo_root\)'
)
BASELINE_SCAFFOLDED_AGENTS = [
    "pm",
    "research-agent",
    "spec-writer",
    "plan-writer",
    "code-agent",
    "verification-agent",
]


def _discover_project_scoped_runtime_agents() -> set[str]:
    """Discover project-scoped subagents across legacy and provisioned layouts."""
    subagents_dir = REPO_ROOT / "meta_agent" / "subagents"
    discovered: set[str] = set()
    for runtime_file in sorted(subagents_dir.glob("*.py")):
        content = runtime_file.read_text()
        discovered.update(match.group("agent") for match in PROJECT_SCOPED_MEMORY_CALL_RE.finditer(content))
    if discovered:
        return discovered

    # Track B fallback: derive project-scoped agents from centralized profiles.
    return {
        agent_name
        for agent_name, profile in PROFILE_REGISTRY.items()
        if profile.use_project_memory
    }


@pytest.mark.integration
class TestMemoryMiddlewareConstruction:
    """MemoryMiddleware can be constructed with a FilesystemBackend and sources."""

    def test_construct_with_bare_fs_backend(self):
        """MemoryMiddleware accepts a FilesystemBackend and source paths."""
        backend = create_bare_filesystem_backend()
        mw = MemoryMiddleware(backend=backend, sources=["/tmp/test/AGENTS.md"])
        assert mw is not None

    def test_bare_fs_backend_virtual_mode_false(self):
        """graph.py uses create_bare_filesystem_backend() — virtual_mode=False."""
        backend = create_bare_filesystem_backend()
        assert isinstance(backend, FilesystemBackend)
        assert backend.virtual_mode is False


@pytest.mark.integration
class TestSkillsMiddlewareConstruction:
    """SkillsMiddleware can be constructed with source directories."""

    def test_construct_with_bare_fs_backend(self):
        """SkillsMiddleware accepts a FilesystemBackend and source dirs."""
        backend = create_bare_filesystem_backend()
        mw = SkillsMiddleware(backend=backend, sources=["/tmp/test/skills"])
        assert mw is not None


@pytest.mark.integration
class TestMemorySourcesExistOnDisk:
    """AGENTS.md files at configured source paths actually exist."""

    def test_global_agents_md_exists(self):
        """The global PM AGENTS.md referenced in graph.py exists on disk."""
        global_agents_md = REPO_ROOT / ".agents" / "pm" / "AGENTS.md"
        assert global_agents_md.is_file(), (
            f"Expected global AGENTS.md at {global_agents_md}"
        )


@pytest.mark.integration
class TestSkillsDirectoriesExistOnDisk:
    """Skills directories at configured paths exist on disk."""

    SKILLS_DIRS = [
        REPO_ROOT / ".agents" / "skills" / "langchain" / "config" / "skills",
        REPO_ROOT / ".agents" / "skills" / "langsmith" / "config" / "skills",
        REPO_ROOT / ".agents" / "skills" / "anthropic" / "skills",
    ]

    @pytest.mark.parametrize(
        "skills_dir",
        [
            REPO_ROOT / ".agents" / "skills" / "langchain" / "config" / "skills",
            REPO_ROOT / ".agents" / "skills" / "langsmith" / "config" / "skills",
            REPO_ROOT / ".agents" / "skills" / "anthropic" / "skills",
        ],
        ids=["langchain", "langsmith", "anthropic"],
    )
    def test_skills_directory_exists(self, skills_dir):
        """Each skills directory referenced in graph.py exists on disk."""
        assert skills_dir.is_dir(), (
            f"Expected skills directory at {skills_dir}"
        )


@pytest.mark.integration
class TestProjectMemoryScaffoldingAlignment:
    """Regression tests for project-memory scaffolding vs runtime wiring."""

    def test_evaluation_agent_scaffolding_and_runtime_coverage(self, tmp_path):
        """Bug-condition test: evaluation-agent must be scaffolded and covered."""
        project = init_project(
            base_dir=str(tmp_path),
            project_name="Evaluation Agent Coverage",
            description="Scaffolding coverage test",
        )
        project_dir = Path(project["project_dir"])

        evaluation_dir = project_dir / ".agents" / "evaluation-agent"
        evaluation_agents_md = evaluation_dir / "AGENTS.md"
        assert evaluation_dir.is_dir(), f"Expected directory at {evaluation_dir}"
        assert evaluation_agents_md.is_file(), f"Expected AGENTS.md at {evaluation_agents_md}"

        runtime_agents = _discover_project_scoped_runtime_agents()
        assert "evaluation-agent" in runtime_agents
        assert set(PROJECT_AGENTS) == runtime_agents | {"pm"}

    @pytest.mark.parametrize(
        "project_name",
        ["Preserve One", "Preserve_2", "Preserve--Three 123"],
    )
    def test_existing_agent_scaffolding_is_preserved(self, project_name, tmp_path):
        """Existing agent scaffolding behavior must remain stable."""
        project = init_project(
            base_dir=str(tmp_path),
            project_name=project_name,
            description="Preservation baseline",
        )
        project_dir = Path(project["project_dir"])

        for agent in BASELINE_SCAFFOLDED_AGENTS:
            agents_md = project_dir / ".agents" / agent / "AGENTS.md"
            assert agents_md.is_file(), f"Missing AGENTS.md for {agent}: {agents_md}"
            assert agents_md.read_text().startswith(f"# {agent}"), (
                f"Unexpected AGENTS.md header for {agent}: {agents_md}"
            )

        expected_dirs = [
            project_dir / "artifacts" / "intake",
            project_dir / "artifacts" / "research",
            project_dir / "artifacts" / "spec",
            project_dir / "artifacts" / "planning",
            project_dir / "artifacts" / "audit",
            project_dir / "evals",
            project_dir / "logs",
        ]
        for expected_dir in expected_dirs:
            assert expected_dir.is_dir(), f"Missing directory: {expected_dir}"

    def test_all_runtime_agents_have_scaffolding(self):
        """Every project-scoped runtime subagent must be scaffolded."""
        runtime_agents = _discover_project_scoped_runtime_agents()
        assert runtime_agents, "No project-scoped runtime agents discovered"
        assert runtime_agents.issubset(set(PROJECT_AGENTS))
        assert set(PROJECT_AGENTS) == runtime_agents | {"pm"}

    def test_evaluation_agent_loads_project_memory(self, tmp_path):
        """Evaluation-agent should load non-empty project AGENTS.md memory."""
        project = init_project(
            base_dir=str(tmp_path),
            project_name="Evaluation Agent Memory Load",
            description="Behavioral memory load test",
        )
        project_dir = project["project_dir"]
        project_id = project["project_id"]
        evaluation_agents_md = Path(project_dir) / ".agents" / "evaluation-agent" / "AGENTS.md"
        assert evaluation_agents_md.is_file(), f"Missing AGENTS.md: {evaluation_agents_md}"

        memory_sources = get_memory_sources(
            "evaluation-agent",
            project_dir=project_dir,
            repo_root=REPO_ROOT,
        )
        memory_mw = MemoryMiddleware(
            backend=create_bare_filesystem_backend(),
            sources=memory_sources,
        )
        update = memory_mw.before_agent({}, None, {})
        assert update is not None and "memory_contents" in update

        memory_contents = update["memory_contents"]
        eval_memory_path = str(evaluation_agents_md)
        assert eval_memory_path in memory_contents
        assert memory_contents[eval_memory_path].strip() != ""

        graph = create_evaluation_agent_graph(project_dir=project_dir, project_id=project_id)
        assert graph is not None
