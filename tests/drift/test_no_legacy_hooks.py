# Drift test: ensure invented middleware hooks don't creep back in
"""Drift tests for legacy/invented patterns.

Catches reintroduction of:
- Invented middleware hook methods (wrap_tool_call_legacy, etc.)
- State fields not declared in MetaAgentState.__annotations__
- Direct monkey-patching of deepagents SDK internals
"""

from __future__ import annotations

from tests.drift import _venv_helper  # noqa: F401
_venv_helper.ensure_venv()

from pathlib import Path

import pytest

from meta_agent.state import MetaAgentState

COVERS = []  # Meta-test


@pytest.mark.drift
class TestNoLegacyHooks:
    """Ensure invented middleware hooks don't creep back into the codebase."""

    BANNED_METHODS = {
        "wrap_tool_call_legacy",
        "before_model_legacy",
        "after_model_legacy",
        "wrap_tool_call_hook",
    }

    # Pre-existing legacy hook references awaiting cleanup.
    # Each entry is a relative path fragment.  Do NOT add new files here.
    _KNOWN_LEGACY_FILES = {
        # dynamic_system_prompt.py still defines before_model_legacy wrapper
        "meta_agent/middleware/dynamic_system_prompt.py",
        # tool_error_handler.py still defines wrap_tool_call_legacy wrapper
        "meta_agent/middleware/tool_error_handler.py",
        # evals/infrastructure/test_infra.py calls before_model_legacy
        "meta_agent/evals/infrastructure/test_infra.py",
    }

    def _scan_python_files(self, directory: Path) -> list[tuple[str, int, str]]:
        """Scan all .py files for banned method definitions or calls."""
        violations = []
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for banned in self.BANNED_METHODS:
                    if banned in line:
                        violations.append((
                            str(py_file.relative_to(directory.parent.parent)),
                            i,
                            stripped,
                        ))
        return violations

    def test_no_legacy_hooks_in_production_code(self):
        """No NEW production code should define or call legacy middleware hooks.

        Known pre-existing references are tracked in _KNOWN_LEGACY_FILES.
        This test catches any *new* files that introduce legacy hook usage.
        """
        meta_agent_dir = Path(__file__).parent.parent.parent / "meta_agent"
        violations = self._scan_python_files(meta_agent_dir)
        # Filter out known pre-existing legacy files
        violations = [
            (f, l, s)
            for f, l, s in violations
            if not any(known in f for known in self._KNOWN_LEGACY_FILES)
        ]
        assert not violations, (
            f"Found legacy hook references in production code:\n"
            + "\n".join(f"  {f}:{l}: {s}" for f, l, s in violations)
        )

    def test_no_legacy_hooks_in_new_tests(self):
        """New test suite should not test legacy hooks."""
        tests_dir = Path(__file__).parent.parent
        new_dirs = [
            tests_dir / "contracts",
            tests_dir / "integration",
            tests_dir / "evals",
            tests_dir / "drift",
        ]
        violations = []
        for d in new_dirs:
            if d.exists():
                violations.extend(self._scan_python_files(d))

        # Filter out this file's own references to BANNED_METHODS
        violations = [
            (f, l, s) for f, l, s in violations if "test_no_legacy_hooks" not in f
        ]

        assert not violations, (
            f"New tests reference legacy hooks:\n"
            + "\n".join(f"  {f}:{l}: {s}" for f, l, s in violations)
        )


@pytest.mark.drift
class TestNoInventedStateFields:
    """Ensure code only references fields declared in MetaAgentState."""

    # Canonical field set from MetaAgentState.__annotations__
    CANONICAL_FIELDS = set(MetaAgentState.__annotations__.keys())

    # Known invented fields that must NOT appear as state accesses
    INVENTED_FIELDS = {
        "workflow_history",
        "agent_memory",
        "tool_call_log",
        "conversation_summary",
        "user_preferences",
    }

    def test_canonical_fields_are_nonempty(self):
        """Sanity: MetaAgentState has annotations we can inspect."""
        assert len(self.CANONICAL_FIELDS) >= 10, (
            f"Expected >=10 state fields, got {len(self.CANONICAL_FIELDS)}"
        )

    def test_no_invented_fields_in_production(self):
        """Production code should not reference invented state field names."""
        meta_agent_dir = Path(__file__).parent.parent.parent / "meta_agent"
        violations = []
        for py_file in meta_agent_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for field in self.INVENTED_FIELDS:
                    # Look for dict-style access: ["field"] or .get("field")
                    if f'["{field}"]' in line or f"['{field}']" in line:
                        rel = str(py_file.relative_to(meta_agent_dir.parent))
                        violations.append(f"{rel}:{i}: {stripped}")
                    elif f'.get("{field}"' in line or f".get('{field}'" in line:
                        rel = str(py_file.relative_to(meta_agent_dir.parent))
                        violations.append(f"{rel}:{i}: {stripped}")
        assert not violations, (
            f"Found invented state field references:\n"
            + "\n".join(f"  {v}" for v in violations)
        )


@pytest.mark.drift
class TestNoSDKMonkeyPatching:
    """Ensure no code monkey-patches deepagents SDK internals."""

    PATCH_PATTERNS = [
        "deepagents.",          # setattr on SDK module
        "monkeypatch",          # pytest monkeypatch of SDK in prod code
    ]

    def test_no_setattr_on_deepagents(self):
        """Production code must not setattr on deepagents modules."""
        meta_agent_dir = Path(__file__).parent.parent.parent / "meta_agent"
        violations = []
        for py_file in meta_agent_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "setattr" in line and "deepagents" in line:
                    rel = str(py_file.relative_to(meta_agent_dir.parent))
                    violations.append(f"{rel}:{i}: {stripped}")
        assert not violations, (
            f"Found SDK monkey-patching:\n"
            + "\n".join(f"  {v}" for v in violations)
        )
