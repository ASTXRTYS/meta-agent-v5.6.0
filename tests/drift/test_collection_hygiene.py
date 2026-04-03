# Drift test: ensure test suite structure stays clean
"""Drift tests for test collection hygiene.

Catches:
- Test files sneaking into _support/
- Missing pytest markers on new test files
- Missing REPLACES: provenance comments
- unittest.mock usage in contract tests
- Unknown marker warnings during collection
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

COVERS = []  # Meta-test, doesn't cover specific components


@pytest.mark.drift
class TestCollectionHygiene:
    """Ensure test suite structure stays clean."""

    def test_no_test_files_in_support(self):
        """tests/_support/ should only have helpers, not test files."""
        support_dir = Path(__file__).parent.parent / "_support"
        if not support_dir.exists():
            pytest.skip("No _support directory")
        test_files = list(support_dir.glob("test_*.py"))
        assert not test_files, (
            f"Found test files in _support/ (helpers only):\n"
            + "\n".join(str(f.name) for f in test_files)
        )

    def test_all_new_tests_have_markers(self):
        """Every test in contracts/ integration/ evals/ drift/ should have a marker."""
        tests_dir = Path(__file__).parent.parent
        new_dirs = {
            "contracts": "contract",
            "integration": "integration",
            "evals": "eval",
            "drift": "drift",
        }

        violations = []
        for dirname, expected_marker in new_dirs.items():
            test_dir = tests_dir / dirname
            if not test_dir.exists():
                continue
            for py_file in test_dir.glob("test_*.py"):
                content = py_file.read_text()
                # Check for pytestmark or @pytest.mark.<marker>
                has_marker = (
                    f"pytest.mark.{expected_marker}" in content
                    or "pytestmark" in content
                )
                if not has_marker:
                    violations.append(
                        f"{dirname}/{py_file.name} missing "
                        f"@pytest.mark.{expected_marker}"
                    )

        assert not violations, (
            f"Test files missing required markers:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    # Files that predate the REPLACES: convention.  Each entry must have
    # a comment explaining why it is exempt.  Do NOT add new files here —
    # new test files MUST include a REPLACES: comment.
    _REPLACES_EXEMPT = {
        # Phase 4 contract tests written before provenance convention
        "contracts/test_graph_runtime.py",
        "contracts/test_state_schema.py",
        "contracts/test_tool_registry_parity.py",
    }

    def test_all_new_tests_have_replaces_comment(self):
        """Every test file in contracts/ integration/ should have REPLACES: comments."""
        tests_dir = Path(__file__).parent.parent
        check_dirs = ["contracts", "integration"]

        violations = []
        for dirname in check_dirs:
            test_dir = tests_dir / dirname
            if not test_dir.exists():
                continue
            for py_file in test_dir.glob("test_*.py"):
                rel = f"{dirname}/{py_file.name}"
                if rel in self._REPLACES_EXEMPT:
                    continue
                content = py_file.read_text()
                if "REPLACES:" not in content:
                    violations.append(rel)

        assert not violations, (
            f"Test files missing REPLACES: comment:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_no_tests_import_unittest_mock_in_contracts(self):
        """Contract tests should not use unittest.mock — they test real code."""
        contracts_dir = Path(__file__).parent.parent / "contracts"
        if not contracts_dir.exists():
            pytest.skip("No contracts directory")

        violations = []
        for py_file in contracts_dir.glob("test_*.py"):
            content = py_file.read_text()
            if "unittest.mock" in content or "from mock import" in content:
                violations.append(py_file.name)

        assert not violations, (
            f"Contract tests should not use mocks:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def test_collection_produces_no_warnings(self):
        """pytest --co should not produce any warnings about missing markers."""
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "tests/", "--ignore=tests/unit",
                "--co", "-q", "--no-header",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        # Filter for "PytestUnknownMarkWarning"
        warnings = [
            line for line in result.stderr.splitlines()
            if "PytestUnknownMarkWarning" in line
        ]
        assert not warnings, (
            f"Unknown marker warnings:\n" + "\n".join(warnings)
        )
