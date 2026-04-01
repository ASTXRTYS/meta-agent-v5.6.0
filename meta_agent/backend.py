"""CompositeBackend and Checkpointer for the meta-agent system.

Spec References: Sections 4.2, 4.3

Uses SDK-native backends from deepagents.backends:
- CompositeBackend: routes file operations by path prefix
- FilesystemBackend: real disk access with virtual_mode security
- StateBackend: thread-scoped ephemeral storage
- StoreBackend: cross-session persistent storage via LangGraph Store

Also provides:
- MemorySaver from langgraph.checkpoint.memory (dev checkpointer)
- InMemoryStore from langgraph.store.memory (dev store)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from deepagents.backends import (
    CompositeBackend as SdkCompositeBackend,
    FilesystemBackend as SdkFilesystemBackend,
    StateBackend as SdkStateBackend,
    StoreBackend as SdkStoreBackend,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


def create_composite_backend(
    repo_root: Path | str,
) -> Callable[..., SdkCompositeBackend]:
    """Create a CompositeBackend factory lambda for create_deep_agent().

    Returns a callable that accepts runtime context and produces a
    CompositeBackend with four routes:
    - (default) -> FilesystemBackend: real disk under repo_root
    - /memories/ -> StoreBackend: cross-session persistent memory
    - /large_tool_results/ -> StateBackend: ephemeral large output offloading
    - /conversation_history/ -> StateBackend: conversation history offloading

    Args:
        repo_root: Absolute path to the project root directory.

    Returns:
        A lambda suitable for backend= parameter of create_deep_agent().
    """
    root_str = str(repo_root)

    def _factory(rt: Any) -> SdkCompositeBackend:
        return SdkCompositeBackend(
            default=SdkFilesystemBackend(root_dir=root_str, virtual_mode=True),
            routes={
                "/memories/": SdkStoreBackend(rt),
                "/large_tool_results/": SdkStateBackend(rt),
                "/conversation_history/": SdkStateBackend(rt),
            },
        )

    return _factory


def create_bare_filesystem_backend() -> SdkFilesystemBackend:
    """Create a bare FilesystemBackend for middleware (Memory, Skills).

    Returns a FilesystemBackend with no root_dir restriction and no
    virtual_mode, allowing it to read files from absolute disk paths.
    This is needed by MemoryMiddleware and SkillsMiddleware to read
    AGENTS.md and SKILL.md files from their absolute locations.

    This matches the production deepagents-cli pattern.
    """
    return SdkFilesystemBackend(virtual_mode=False)


def create_checkpointer() -> MemorySaver:
    """Create a development checkpointer (InMemorySaver / MemorySaver).

    For production, migrate to PostgresSaver.
    """
    return MemorySaver()


def create_store() -> InMemoryStore:
    """Create an InMemoryStore for agent memory."""
    return InMemoryStore()
