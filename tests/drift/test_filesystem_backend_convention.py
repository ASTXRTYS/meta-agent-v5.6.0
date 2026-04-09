"""Drift test: enforce filesystem backend and workspace scaffolding conventions."""

from __future__ import annotations

from tests.drift import _venv_helper  # noqa: F401
_venv_helper.ensure_venv()

from pathlib import Path

import pytest

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from meta_agent.backend import create_bare_filesystem_backend, create_composite_backend
from meta_agent.project import PROJECT_AGENTS, init_project

COVERS = []  # Meta-test

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ROUTE_KEYS = {
    "/memories/",
    "/large_tool_results/",
    "/conversation_history/",
}


class _DummyRuntime:
    """Minimal runtime object for backend factory instantiation tests."""

    context = None
    store = None


@pytest.mark.drift
class TestFilesystemBackendConvention:
    """Keep backend routing and project filesystem contracts stable."""

    def test_composite_backend_route_map_is_stable(self):
        factory = create_composite_backend(REPO_ROOT)
        backend = factory(_DummyRuntime())

        assert isinstance(backend, CompositeBackend)
        assert isinstance(backend.default, FilesystemBackend)
        assert backend.default.virtual_mode is True
        assert backend.default.cwd == REPO_ROOT.resolve()

        assert set(backend.routes) == EXPECTED_ROUTE_KEYS
        assert isinstance(backend.routes["/memories/"], StoreBackend)
        assert isinstance(backend.routes["/large_tool_results/"], StateBackend)
        assert isinstance(backend.routes["/conversation_history/"], StateBackend)

    def test_bare_filesystem_backend_for_memory_and_skills(self):
        backend = create_bare_filesystem_backend()
        assert isinstance(backend, FilesystemBackend)
        assert backend.virtual_mode is False

    def test_project_scaffolding_layout_is_stable(self, tmp_path):
        project = init_project(
            base_dir=str(tmp_path),
            project_name="Filesystem Convention",
            description="Drift guard scaffolding check",
        )
        project_dir = Path(project["project_dir"])

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
            assert expected_dir.is_dir(), f"Missing expected directory: {expected_dir}"

        for agent_name in PROJECT_AGENTS:
            agents_md = project_dir / ".agents" / agent_name / "AGENTS.md"
            assert agents_md.is_file(), f"Missing expected AGENTS.md: {agents_md}"
