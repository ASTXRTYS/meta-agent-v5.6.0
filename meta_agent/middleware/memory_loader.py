"""MemoryLoaderMiddleware stub — per-agent AGENTS.md memory loading.

===============================================================================
HIGH URGENCY — DEVELOPER ACTION
===============================================================================

Runtime memory is handled by MemoryMiddleware from the Deep Agents SDK (see
meta_agent/graph.py and subagent runtimes). This module is not wired into any
graph and appears to be DEAD CODE, kept only as a placeholder and for
contract/stub listings.

Before the next release: run one more confirmation pass — repo-wide search for
MemoryLoaderMiddleware, memory_loader, and any external imports of
meta_agent.middleware.MemoryLoaderMiddleware — and verify nothing depends on
this file.

After explicit maintainer approval: delete this file and remove it from the app
by updating meta_agent/middleware/__init__.py, tests/contracts/test_stub_allowlist.py,
docs/testing/intentional_stubs.yaml, and any spec or dataset text that still
names MemoryLoaderMiddleware.
===============================================================================

Spec References: Sections 22.18, 13.4.6

Stub implementation for Phase 0. Full implementation in Phase 1.
"""

from __future__ import annotations

import os
from typing import Any


class MemoryLoaderMiddleware:
    """Stub middleware for loading per-agent AGENTS.md memory.

    Each agent has its own memory file at:
    - Global: .agents/{agent-name}/AGENTS.md
    - Per-project: .agents/pm/projects/{project_id}/.agents/{agent-name}/AGENTS.md

    Isolation rule: each agent sees ONLY its own memory file.
    """

    def __init__(self, agent_name: str, project_dir: str = "") -> None:
        self.agent_name = agent_name
        self.project_dir = project_dir

    def load_memory(self) -> str:
        """Load the agent's AGENTS.md content.

        Checks per-project memory first, falls back to global memory.
        Returns empty string if no memory file exists.
        """
        # Per-project memory
        if self.project_dir:
            project_path = os.path.join(
                self.project_dir, ".agents", self.agent_name, "AGENTS.md"
            )
            if os.path.isfile(project_path):
                with open(project_path) as f:
                    return f.read()

        # Global memory
        global_path = os.path.join(".agents", self.agent_name, "AGENTS.md")
        if os.path.isfile(global_path):
            with open(global_path) as f:
                return f.read()

        return ""

    def save_memory(self, content: str) -> None:
        """Save content to the agent's AGENTS.md file (stub)."""
        if self.project_dir:
            path = os.path.join(
                self.project_dir, ".agents", self.agent_name, "AGENTS.md"
            )
        else:
            path = os.path.join(".agents", self.agent_name, "AGENTS.md")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
