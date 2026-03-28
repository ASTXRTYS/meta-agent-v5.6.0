"""Unit tests for meta_agent.backend module."""

from __future__ import annotations

import os

import pytest

from meta_agent.backend import (
    CompositeBackend,
    FilesystemBackend,
    StateBackend,
    StoreBackend,
    create_checkpointer,
    create_store,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


class TestStateBackend:
    def test_put_get(self):
        backend = StateBackend()
        backend.put("key1", "value1")
        assert backend.get("key1") == "value1"

    def test_get_missing(self):
        backend = StateBackend()
        assert backend.get("nonexistent") is None

    def test_delete(self):
        backend = StateBackend()
        backend.put("key1", "value1")
        backend.delete("key1")
        assert backend.get("key1") is None

    def test_list_keys(self):
        backend = StateBackend()
        backend.put("test/a", 1)
        backend.put("test/b", 2)
        backend.put("other/c", 3)
        assert sorted(backend.list_keys("test/")) == ["test/a", "test/b"]


class TestInMemoryStore:
    def test_basic_operations(self):
        store = StoreBackend()
        store.put("k", "v")
        assert store.get("k") == "v"
        store.delete("k")
        assert store.get("k") is None


class TestFilesystemBackend:
    def test_put_get(self, tmp_path):
        backend = FilesystemBackend(root=str(tmp_path))
        backend.put("/workspace/test.txt", "hello")
        assert backend.get("/workspace/test.txt") == "hello"

    def test_get_missing(self, tmp_path):
        backend = FilesystemBackend(root=str(tmp_path))
        assert backend.get("/workspace/nonexistent.txt") is None

    def test_delete(self, tmp_path):
        backend = FilesystemBackend(root=str(tmp_path))
        backend.put("/workspace/test.txt", "hello")
        backend.delete("/workspace/test.txt")
        assert backend.get("/workspace/test.txt") is None

    def test_has_sdk_backend(self, tmp_path):
        backend = FilesystemBackend(root=str(tmp_path))
        assert backend.sdk_backend is not None


class TestCompositeBackend:
    def test_workspace_routes_to_filesystem(self, tmp_path):
        fs = FilesystemBackend(root=str(tmp_path))
        backend = CompositeBackend(filesystem_backend=fs)
        backend.put("/workspace/test.txt", "data")
        assert backend.get("/workspace/test.txt") == "data"

    def test_memories_routes_to_store(self):
        backend = CompositeBackend()
        backend.put("/memories/agent/key", "value")
        assert backend.get("/memories/agent/key") == "value"

    def test_default_routes_to_state(self):
        backend = CompositeBackend()
        backend.put("some_key", "some_value")
        assert backend.get("some_key") == "some_value"


class TestCheckpointer:
    def test_create_checkpointer_returns_memory_saver(self):
        cp = create_checkpointer()
        assert isinstance(cp, MemorySaver)

    def test_create_store_returns_inmemory(self):
        store = create_store()
        assert isinstance(store, InMemoryStore)
