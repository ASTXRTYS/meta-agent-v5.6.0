"""Unit tests for meta_agent.backend module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from meta_agent.backend import (
    create_composite_backend,
    create_bare_filesystem_backend,
    create_checkpointer,
    create_store,
)
from deepagents.backends import (
    CompositeBackend as SdkCompositeBackend,
    FilesystemBackend as SdkFilesystemBackend,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


pytestmark = pytest.mark.legacy


class TestCreateCompositeBackend:
    def test_returns_callable(self):
        factory = create_composite_backend("/tmp/test")
        assert callable(factory)

    def test_factory_produces_composite_backend(self):
        factory = create_composite_backend("/tmp/test")
        rt = MagicMock()
        backend = factory(rt)
        assert isinstance(backend, SdkCompositeBackend)


class TestCreateBareFilesystemBackend:
    def test_returns_filesystem_backend(self):
        backend = create_bare_filesystem_backend()
        assert isinstance(backend, SdkFilesystemBackend)


class TestCheckpointer:
    def test_create_checkpointer_returns_memory_saver(self):
        cp = create_checkpointer()
        assert isinstance(cp, MemorySaver)

    def test_create_store_returns_inmemory(self):
        store = create_store()
        assert isinstance(store, InMemoryStore)
