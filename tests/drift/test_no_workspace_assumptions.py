# Drift test: ensure no code assumes /workspace/ paths
"""Drift test to catch hardcoded /workspace/ path references.

These are stale assumptions from an older project layout and must not
appear in production code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

COVERS = []  # Meta-test


# Known /workspace/ references that are intentional or pending removal.
# If you add a new entry here, include a comment explaining why.
_KNOWN_WORKSPACE_FILES = {
    # safety.py: working_dir_restriction config — legacy sandbox constraint
    "meta_agent/safety.py",
    # research_agent.py: /workspace/ path normalization for backward compat
    "meta_agent/subagents/research_agent.py",
    # evals/guardrails: test expectations that reference the sandbox path
    "meta_agent/evals/guardrails/test_guards.py",
    # synthetic trace adapter: eval scenario text mentioning workspace
    "meta_agent/evals/research/synthetic_trace_adapter.py",
}


@pytest.mark.drift
class TestNoWorkspaceAssumptions:
    """Scan meta_agent/ for hardcoded /workspace/ paths."""

    def test_no_new_hardcoded_workspace_paths(self):
        """No NEW production code should reference /workspace/ paths.

        Known exceptions are tracked in _KNOWN_WORKSPACE_FILES.
        This test catches any new files that introduce /workspace/ references.
        """
        meta_agent_dir = Path(__file__).parent.parent.parent / "meta_agent"
        violations = []
        for py_file in meta_agent_dir.rglob("*.py"):
            rel = str(py_file.relative_to(meta_agent_dir.parent))
            if rel in _KNOWN_WORKSPACE_FILES:
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if "/workspace/" in line and not line.strip().startswith("#"):
                    violations.append(f"{rel}:{i}: {line.strip()}")
        assert not violations, (
            f"Found /workspace/ references in new files:\n"
            + "\n".join(violations)
        )
