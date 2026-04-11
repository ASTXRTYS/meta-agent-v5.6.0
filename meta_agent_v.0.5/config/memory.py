"""Memory configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path


def get_memory_sources(
    agent_name: str,
    project_dir: str | None = None,
    repo_root: Path | None = None,
) -> list[str]:
    """Resolve AGENTS.md paths for an agent.

    Returns candidate absolute paths for:
    1. Project-specific memory (`{project_dir}/.agents/{agent_name}/AGENTS.md`)
    2. Global/fallback memory (`{repo_root}/.agents/{agent_name}/AGENTS.md`)

    the agent can "know" where its memory would be stored if it chooses to
    initialize it later.

    Args:
        agent_name: Name of the agent (e.g., "pm", "research-agent").
        project_dir: Absolute path to the active project directory.
        repo_root: Absolute path to the repository root.

    Returns:
        List of absolute path strings.
    """
    sources: list[str] = []

    # 1. Project-specific memory (highest precedence)
    if project_dir:
        sources.append(os.path.join(project_dir, ".agents", agent_name, "AGENTS.md"))

    # 2. Global/fallback memory
    if repo_root:
        sources.append(str(repo_root / ".agents" / agent_name / "AGENTS.md"))
    else:
        # Fallback to current directory relative if repo_root not provided
        sources.append(os.path.abspath(os.path.join(".agents", agent_name, "AGENTS.md")))

    return sources
