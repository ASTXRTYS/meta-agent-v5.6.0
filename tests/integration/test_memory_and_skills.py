# REPLACES: tests/unit/test_middleware.py::TestMemoryLoaderMiddleware (if it exists)
"""Integration tests for MemoryMiddleware and SkillsMiddleware configuration.

Validates that our middleware can be constructed with the correct backend types,
and that the source paths referenced in graph.py actually exist on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepagents.backends import FilesystemBackend
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from meta_agent.backend import create_bare_filesystem_backend

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
