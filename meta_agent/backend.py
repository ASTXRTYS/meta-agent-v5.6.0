"""CompositeBackend and Checkpointer for the meta-agent system.

Spec References: Sections 4.2, 4.3

Uses real deepagents SDK backends:
- FilesystemBackend from deepagents.backends
- InMemoryStore from langgraph.store.memory
- MemorySaver (InMemorySaver) from langgraph.checkpoint.memory
"""

from __future__ import annotations

import os
from typing import Any

from deepagents.backends import FilesystemBackend as SdkFilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


class StateBackend:
    """Ephemeral state backend tied to the current thread."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        return [k for k in self._store if k.startswith(prefix)]


class FilesystemBackend:
    """Backend that wraps the real deepagents FilesystemBackend for /workspace/ paths."""

    def __init__(self, root: str = ".", virtual_mode: bool = True) -> None:
        self.root = root
        self.virtual_mode = virtual_mode
        self._sdk_backend = SdkFilesystemBackend(
            root_dir=root,
            virtual_mode=virtual_mode,
        )

    @property
    def sdk_backend(self) -> SdkFilesystemBackend:
        """Access the underlying SDK backend for create_deep_agent()."""
        return self._sdk_backend

    def resolve_path(self, key: str) -> str:
        """Convert a virtual key to a real filesystem path."""
        relative = key
        if relative.startswith("/workspace/"):
            relative = relative[len("/workspace/"):]
        return os.path.join(self.root, relative)

    def get(self, key: str) -> str | None:
        path = self.resolve_path(key)
        if os.path.isfile(path):
            with open(path) as f:
                return f.read()
        return None

    def put(self, key: str, value: str) -> None:
        path = self.resolve_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(value)

    def delete(self, key: str) -> None:
        path = self.resolve_path(key)
        if os.path.isfile(path):
            os.remove(path)


class StoreBackend:
    """Backend wrapping InMemoryStore for /memories/ paths."""

    def __init__(self, store: InMemoryStore | None = None) -> None:
        self.store = store or InMemoryStore()
        self._kv: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._kv.get(key)

    def put(self, key: str, value: Any) -> None:
        self._kv[key] = value

    def delete(self, key: str) -> None:
        self._kv.pop(key, None)


class CompositeBackend:
    """Routes storage requests by path prefix.

    - /workspace/ -> FilesystemBackend (maps to real disk)
    - /memories/  -> StoreBackend (InMemoryStore for V1)
    - default     -> StateBackend (ephemeral, tied to current thread)
    """

    def __init__(
        self,
        filesystem_backend: FilesystemBackend | None = None,
        store_backend: StoreBackend | None = None,
        state_backend: StateBackend | None = None,
    ) -> None:
        self.filesystem = filesystem_backend or FilesystemBackend()
        self.store = store_backend or StoreBackend()
        self.state = state_backend or StateBackend()

    def _route(self, key: str) -> FilesystemBackend | StoreBackend | StateBackend:
        if key.startswith("/workspace/"):
            return self.filesystem
        if key.startswith("/memories/"):
            return self.store
        return self.state

    def get(self, key: str) -> Any:
        return self._route(key).get(key)

    def put(self, key: str, value: Any) -> None:
        self._route(key).put(key, value)

    def delete(self, key: str) -> None:
        self._route(key).delete(key)


def create_checkpointer() -> MemorySaver:
    """Create a development checkpointer (InMemorySaver / MemorySaver).

    For production, migrate to PostgresSaver.
    """
    return MemorySaver()


def create_store() -> InMemoryStore:
    """Create an InMemoryStore for agent memory."""
    return InMemoryStore()
