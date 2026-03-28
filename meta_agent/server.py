"""Dynamic graph factory for langgraph.json registration.

Spec Reference: Section 22.6

This module exports ``get_agent()`` which is referenced in langgraph.json
as the graph entry point. Follows the Section 13.4.3 server.py pattern.
"""

from __future__ import annotations

from importlib import metadata as importlib_metadata
import os
from typing import Any

from meta_agent.graph import create_graph
from meta_agent.configuration import MetaAgentConfig


REQUIRED_RUNTIME_VERSIONS: dict[str, str] = {
    "deepagents": "0.4.3",
    "langgraph-cli": "0.4.12",
    "langchain-anthropic": "1.3.0",
}


def _version_tuple(version_text: str) -> tuple[int, int, int]:
    """Parse a version string into a numeric tuple for simple comparisons."""
    parts: list[int] = []
    for token in version_text.split("."):
        digits = ""
        for ch in token:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            break
        parts.append(int(digits))

    while len(parts) < 3:
        parts.append(0)

    return tuple(parts[:3])


def _validate_runtime_dependencies() -> None:
    """Fail fast if runtime package versions are below project minimums."""
    errors: list[str] = []

    for package_name, min_version in REQUIRED_RUNTIME_VERSIONS.items():
        try:
            installed = importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            errors.append(f"{package_name} is not installed (requires >= {min_version})")
            continue

        if _version_tuple(installed) < _version_tuple(min_version):
            errors.append(
                f"{package_name}=={installed} is below required minimum {min_version}"
            )

    if errors:
        details = "; ".join(errors)
        raise RuntimeError(
            "Incompatible runtime dependencies detected. "
            f"{details}. Run `pip install -e \".[dev]\"` from the repo root "
            "and relaunch `langgraph dev`."
        )


def _load_env() -> None:
    """Load .env file at startup if dotenv is available."""
    try:
        from dotenv import load_dotenv
        # Look for .env in the package root and parent dirs
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.isfile(env_path):
            load_dotenv(env_path)
        elif os.path.isfile(".env"):
            load_dotenv(".env")
    except ImportError:
        # dotenv not installed — env vars must be set externally
        pass


# Load .env on module import
_load_env()


def get_agent() -> Any:
    """Dynamic graph factory for LangGraph dev server.

    Called by langgraph.json to create the meta-agent graph.
    Uses environment configuration via MetaAgentConfig.from_env().

    Returns:
        A compiled LangGraph StateGraph from create_deep_agent().
    """
    _validate_runtime_dependencies()
    config = MetaAgentConfig.from_env()
    return create_graph(config=config)
