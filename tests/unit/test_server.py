"""Unit tests for meta_agent.server runtime guards."""

from __future__ import annotations

from importlib import metadata as importlib_metadata

import pytest

from meta_agent import server


pytestmark = pytest.mark.legacy


class TestVersionTuple:
    """Tests for simple version parsing helper."""

    def test_parses_simple_semver(self):
        assert server._version_tuple("1.2.3") == (1, 2, 3)

    def test_parses_short_version(self):
        assert server._version_tuple("0.4") == (0, 4, 0)

    def test_parses_prerelease_suffix(self):
        assert server._version_tuple("1.0.8rc1") == (1, 0, 8)


class TestRuntimeDependencyValidation:
    """Tests for runtime dependency fail-fast checks."""

    def test_accepts_compatible_versions(self, monkeypatch):
        monkeypatch.setattr(
            server,
            "REQUIRED_RUNTIME_VERSIONS",
            {
                "deepagents": "0.4.3",
                "langgraph-cli": "0.4.12",
            },
        )

        def _fake_version(package_name: str) -> str:
            return {
                "deepagents": "0.4.12",
                "langgraph-cli": "0.5.9",
            }[package_name]

        monkeypatch.setattr(server.importlib_metadata, "version", _fake_version)

        server._validate_runtime_dependencies()

    def test_rejects_outdated_versions(self, monkeypatch):
        monkeypatch.setattr(
            server,
            "REQUIRED_RUNTIME_VERSIONS",
            {
                "deepagents": "0.4.3",
            },
        )

        monkeypatch.setattr(server.importlib_metadata, "version", lambda _pkg: "0.2.7")

        with pytest.raises(RuntimeError) as exc_info:
            server._validate_runtime_dependencies()

        assert "deepagents==0.2.7" in str(exc_info.value)

    def test_rejects_missing_packages(self, monkeypatch):
        monkeypatch.setattr(
            server,
            "REQUIRED_RUNTIME_VERSIONS",
            {
                "langchain-anthropic": "1.3.0",
            },
        )

        def _raise_missing(_pkg: str) -> str:
            raise importlib_metadata.PackageNotFoundError("langchain-anthropic")

        monkeypatch.setattr(server.importlib_metadata, "version", _raise_missing)

        with pytest.raises(RuntimeError) as exc_info:
            server._validate_runtime_dependencies()

        assert "langchain-anthropic is not installed" in str(exc_info.value)
