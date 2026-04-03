"""Drift test: stub allowlist parity with intentional_stubs.yaml.

Ensures every intentional stub is cataloged and every stub found in
meta_agent/ is in the intentional_stubs.yaml catalog.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

import pytest
import yaml

COVERS = []  # Meta-test

pytestmark = pytest.mark.drift

REPO_ROOT = Path(__file__).resolve().parents[2]
STUBS_PATH = REPO_ROOT / "docs" / "testing" / "intentional_stubs.yaml"
META_AGENT_DIR = REPO_ROOT / "meta_agent"

# Current project phase for expiration checks
CURRENT_PHASE = 3


def _load_stubs():
    """Load the intentional stubs catalog, skipping if not found."""
    if not STUBS_PATH.exists():
        pytest.skip("catalog not found")
    with open(STUBS_PATH) as f:
        return yaml.safe_load(f)


def _stub_entries(catalog) -> list[dict]:
    """Flatten all stub entries from the catalog."""
    entries = []
    if isinstance(catalog, list):
        entries.extend(e for e in catalog if isinstance(e, dict))
    elif isinstance(catalog, dict):
        for section in catalog.values():
            if isinstance(section, list):
                entries.extend(e for e in section if isinstance(e, dict))
    return entries


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


def _find_pass_only_functions(root: Path) -> list[tuple[str, str]]:
    """Find functions whose body is just pass (after stripping docstrings)."""
    results = []
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
                if node.name in ("__init__", "__repr__", "__str__"):
                    continue
                stmts = [
                    s for s in node.body
                    if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
                ]
                if len(stmts) == 1 and isinstance(stmts[0], ast.Pass):
                    results.append((rel, node.name))
    return results


def _find_pending_returns(root: Path) -> list[tuple[str, str]]:
    """Find functions returning placeholder values like {"status": "pending"}."""
    results = []
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(root.parent))
        try:
            content = py_file.read_text()
            tree = ast.parse(content, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in node.body:
                    if isinstance(stmt, ast.Return) and stmt.value:
                        src = ast.get_source_segment(content, stmt.value)
                        if src and '"pending"' in str(src):
                            results.append((rel, node.name))
    return results


class TestCatalogedStubsExist:
    """Every stub entry in the catalog should exist in the codebase."""

    def test_all_catalog_stubs_exist(self):
        catalog = _load_stubs()
        entries = _stub_entries(catalog)
        missing = []
        for entry in entries:
            file_path = entry.get("file", "")
            symbol = entry.get("symbol", "")
            if not file_path:
                continue
            src = REPO_ROOT / file_path
            if not src.exists():
                missing.append(f"{file_path}: file does not exist")
            elif symbol:
                content = src.read_text()
                if symbol not in content:
                    missing.append(f"{file_path}::{symbol}: symbol not found")
        assert not missing, f"Missing catalog stubs:\n" + "\n".join(missing)



class TestDiscoveredStubsCataloged:
    """Every stub discovered in meta_agent/ must be in the catalog."""

    def test_not_implemented_stubs_cataloged(self):
        catalog = _load_stubs()
        entries = _stub_entries(catalog)
        # Build set of (file, symbol) from catalog
        cataloged = set()
        for entry in entries:
            f = entry.get("file", "")
            s = entry.get("symbol", "")
            if f and s:
                cataloged.add((f, s))

        found = _find_not_implemented_raises(META_AGENT_DIR)
        uncataloged = []
        for file_path, func_names in found.items():
            for fn in func_names:
                if (file_path, fn) not in cataloged:
                    uncataloged.append(f"{file_path}::{fn}")
        assert not uncataloged, (
            f"Stubs not in intentional_stubs.yaml:\n"
            + "\n".join(f"  - {s}" for s in uncataloged)
        )

    def test_pass_only_stubs_cataloged(self):
        catalog = _load_stubs()
        entries = _stub_entries(catalog)
        cataloged = set()
        for entry in entries:
            f = entry.get("file", "")
            s = entry.get("symbol", "")
            if f and s:
                cataloged.add((f, s))

        pass_stubs = _find_pass_only_functions(META_AGENT_DIR)
        uncataloged = []
        for file_path, fn in pass_stubs:
            if (file_path, fn) not in cataloged:
                uncataloged.append(f"{file_path}::{fn}")
        assert not uncataloged, (
            f"Pass-only stubs not in intentional_stubs.yaml:\n"
            + "\n".join(f"  - {s}" for s in uncataloged)
        )

    def test_pending_return_stubs_cataloged(self):
        catalog = _load_stubs()
        entries = _stub_entries(catalog)
        cataloged = set()
        for entry in entries:
            f = entry.get("file", "")
            s = entry.get("symbol", "")
            if f and s:
                cataloged.add((f, s))

        pending = _find_pending_returns(META_AGENT_DIR)
        uncataloged = []
        for file_path, fn in pending:
            if (file_path, fn) not in cataloged:
                uncataloged.append(f"{file_path}::{fn}")
        assert not uncataloged, (
            f"Pending-return stubs not in intentional_stubs.yaml:\n"
            + "\n".join(f"  - {s}" for s in uncataloged)
        )


class TestStubPhaseExpiration:
    """Stubs past their allowed phase should warn."""

    def test_expired_stubs_warn(self):
        catalog = _load_stubs()
        entries = _stub_entries(catalog)
        expired = []
        for entry in entries:
            allowed_until = entry.get("allowed_until_phase")
            if allowed_until is not None and int(allowed_until) < CURRENT_PHASE:
                expired.append(
                    f"{entry.get('file', '?')}::{entry.get('symbol', '?')} "
                    f"(allowed_until_phase={allowed_until}, current={CURRENT_PHASE})"
                )
        if expired:
            warnings.warn(
                f"Expired stubs (allowed_until_phase < {CURRENT_PHASE}):\n"
                + "\n".join(f"  - {e}" for e in expired),
                stacklevel=1,
            )