# REPLACES: (no direct legacy equivalent — new enforcement)
"""Contract tests enforcing the intentional stub allowlist.

Scans meta_agent/ for NotImplementedError raises and verifies
each occurrence is in the approved stub ledger.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COVERS = [
    "stub.eval_tools.run_eval_suite",
    "stub.eval_tools.get_eval_results",
    "stub.eval_tools.compare_eval_runs",
    "stub.document_renderer.render_artifact",
]


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Allowlist — intentional stubs that are permitted to exist
# ---------------------------------------------------------------------------

META_AGENT_ROOT = Path(__file__).resolve().parents[2] / "meta_agent"

ALLOWED_STUBS: dict[str, list[str]] = {
    "meta_agent/tools/eval_tools.py": [
        "run_eval_suite",
        "get_eval_results",
        "compare_eval_runs",
    ],
}

# Stub patterns in the allowlist that map to config stubs (not raising NotImplementedError)
ALLOWED_CONFIG_STUBS = {
    "meta_agent/subagents/configs.py": [
        "observation-agent",
        "evaluation-agent",
        "audit-agent",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_not_implemented_raises(root: Path) -> dict[str, list[str]]:
    """Scan Python files for ``raise NotImplementedError`` and return a map.

    Returns:
        Dict mapping relative file paths to list of function/method names
        that contain ``raise NotImplementedError``.
    """
    results: dict[str, list[str]] = {}
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(root.parent))
        try:
            tree = ast.parse(py_file.read_text(), filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Raise) and child.exc is not None:
                        exc = child.exc
                        name = None
                        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                            name = exc.func.id
                        elif isinstance(exc, ast.Name):
                            name = exc.id
                        if name == "NotImplementedError":
                            results.setdefault(rel, []).append(node.name)
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAllowedStubsExist:
    """Verify each allowed stub location actually contains a stub."""

    def test_eval_tools_stubs_exist(self):
        path = META_AGENT_ROOT / "tools" / "eval_tools.py"
        content = path.read_text()
        for func_name in ALLOWED_STUBS["meta_agent/tools/eval_tools.py"]:
            assert f"def {func_name}" in content, f"Missing stub: {func_name}"
            assert "NotImplementedError" in content


class TestNoNewStubs:
    """Verify no NotImplementedError raises exist outside the allowlist."""

    def test_all_not_implemented_in_allowlist(self):
        found = _find_not_implemented_raises(META_AGENT_ROOT)
        violations = []
        for file_path, func_names in found.items():
            allowed = ALLOWED_STUBS.get(file_path, [])
            for fn in func_names:
                if fn not in allowed:
                    violations.append(f"{file_path}::{fn}")
        assert violations == [], (
            f"Found NotImplementedError outside allowlist:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestNoSoftStubs:
    """Catch soft stubs: functions returning placeholder values."""

    def test_no_soft_stubs_outside_allowlist(self):
        """Catch soft stubs: functions that return placeholder values like {"status": "pending"}."""

        SOFT_STUB_ALLOWLIST = {
            # document_renderer.py render_artifact returns {"status": "pending"} — Phase 4 scope
            ("meta_agent/subagents/document_renderer.py", "render_artifact"),
            # BaseStage abstract hooks and telemetry carriers (Requirement 3.7, 8.2)
            ("meta_agent/stages/base.py", "_check_entry_impl"),
            ("meta_agent/stages/base.py", "_check_exit_impl"),
            ("meta_agent/stages/base.py", "sync_from_state"),
            ("meta_agent/stages/base.py", "_span_carrier"),
        }

        meta_agent_dir = Path(__file__).parent.parent.parent / "meta_agent"
        violations = []

        for py_file in meta_agent_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            rel_path = str(py_file.relative_to(meta_agent_dir.parent))
            content = py_file.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check for functions whose body is just "pass" or "return None"
                    body = node.body
                    # Skip if it's a docstring + pass
                    stmts = [s for s in body if not isinstance(s, ast.Expr) or not isinstance(s.value, ast.Constant)]
                    if len(stmts) == 1 and isinstance(stmts[0], ast.Pass):
                        if (rel_path, node.name) not in SOFT_STUB_ALLOWLIST:
                            # Check it's not __init__ or a simple property
                            if node.name not in ("__init__", "__repr__", "__str__"):
                                violations.append(f"{rel_path}:{node.lineno} {node.name}() — body is just pass")

                    # Check for return {"status": "pending"} pattern
                    for stmt in body:
                        if isinstance(stmt, ast.Return) and stmt.value:
                            src_segment = ast.get_source_segment(content, stmt.value)
                            if src_segment and '"pending"' in str(src_segment):
                                if (rel_path, node.name) not in SOFT_STUB_ALLOWLIST:
                                    violations.append(f"{rel_path}:{node.lineno} {node.name}() — returns pending placeholder")

        assert not violations, (
            f"Found soft stubs outside allowlist:\n" + "\n".join(f"  {v}" for v in violations)
        )
