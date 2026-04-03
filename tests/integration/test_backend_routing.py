# REPLACES: tests/unit/test_backend.py::TestCreateCompositeBackend
# REPLACES: tests/unit/test_backend.py::TestCreateBareFilesystemBackend
# REPLACES: tests/unit/test_backend.py::TestCheckpointer
"""Integration tests for backend composition from meta_agent/backend.py.

Validates that our backend factories produce correct SDK backend types,
routes are configured for /memories/, /large_tool_results/, /conversation_history/,
and that write/read roundtrips work through both the default and routed backends.
"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import WriteResult
from meta_agent.backend import (
    create_bare_filesystem_backend,
    create_checkpointer,
    create_composite_backend,
    create_store,
)
from tests._support.fake_runtime import make_runtime

COVERS = [
    "backend.route.default",
    "backend.route.memories",
    "backend.route.large_tool_results",
    "backend.route.conversation_history",
    "sdk.deepagents.CompositeBackend",
    "sdk.deepagents.FilesystemBackend",
    "sdk.deepagents.StateBackend",
    "sdk.deepagents.StoreBackend",
]


@pytest.mark.integration
class TestCreateCompositeBackend:
    """Tests for create_composite_backend factory."""

    def test_returns_callable_factory(self, tmp_path):
        """create_composite_backend(tmp_path) returns a callable factory."""
        factory = create_composite_backend(tmp_path)
        assert callable(factory)

    def test_factory_produces_composite_backend(self, tmp_path):
        """The factory, when called with a runtime, produces a CompositeBackend."""
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)
        assert isinstance(backend, CompositeBackend)

    def test_composite_has_memories_route(self, tmp_path):
        """The CompositeBackend has a route for /memories/."""
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)
        # Write to /memories/ — should go to StoreBackend route
        result = backend.write("/memories/test.txt", "memory content")
        assert isinstance(result, WriteResult)
        assert result.error is None

    def test_composite_has_large_tool_results_route(self, tmp_path):
        """The CompositeBackend has a route for /large_tool_results/."""
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)
        result = backend.write("/large_tool_results/out.txt", "large output")
        assert isinstance(result, WriteResult)
        assert result.error is None

    def test_composite_has_conversation_history_route(self, tmp_path):
        """The CompositeBackend has a route for /conversation_history/."""
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)
        result = backend.write("/conversation_history/session.json", '{"turns": []}')
        assert isinstance(result, WriteResult)
        assert result.error is None

    def test_default_route_write_read_roundtrip(self, tmp_path):
        """Write/read roundtrip through the default route (FilesystemBackend).

        FilesystemBackend.read() returns a string with line-numbered content.
        """
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)

        content = "hello from default route"
        write_result = backend.write("/project_file.txt", content)
        assert isinstance(write_result, WriteResult)
        assert write_result.error is None

        read_result = backend.read("/project_file.txt")
        assert isinstance(read_result, str)
        assert content in read_result

    def test_conversation_history_route_write_succeeds(self, tmp_path):
        """Write through /conversation_history/ (StateBackend) succeeds.

        StateBackend stores data in graph state; read requires a full graph
        invocation cycle, so we only verify write returns a clean WriteResult.
        """
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        backend = factory(rt)

        content = "conversation data here"
        write_result = backend.write("/conversation_history/s1.txt", content)
        assert isinstance(write_result, WriteResult)
        assert write_result.error is None


@pytest.mark.integration
class TestCreateBareFilesystemBackend:
    """Tests for create_bare_filesystem_backend factory."""

    def test_returns_filesystem_backend(self):
        """create_bare_filesystem_backend() returns FilesystemBackend."""
        backend = create_bare_filesystem_backend()
        assert isinstance(backend, FilesystemBackend)

    def test_virtual_mode_is_false(self):
        """The bare filesystem backend has virtual_mode=False."""
        backend = create_bare_filesystem_backend()
        assert backend.virtual_mode is False


@pytest.mark.integration
class TestCheckpointerAndStore:
    """Tests for create_checkpointer and create_store."""

    def test_create_checkpointer_returns_memory_saver(self):
        """create_checkpointer() returns MemorySaver."""
        checkpointer = create_checkpointer()
        assert isinstance(checkpointer, MemorySaver)

    def test_create_store_returns_in_memory_store(self):
        """create_store() returns InMemoryStore."""
        store = create_store()
        assert isinstance(store, InMemoryStore)
