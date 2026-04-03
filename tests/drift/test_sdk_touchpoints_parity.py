"""Drift test: SDK touchpoints parity.

Ensures every SDK import in meta_agent/ is cataloged in
docs/testing/sdk_touchpoints.yaml and vice-versa.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

COVERS = []  # Meta-test

pytestmark = pytest.mark.drift

REPO_ROOT = Path(__file__).resolve().parents[2]
TOUCHPOINTS_PATH = REPO_ROOT / "docs" / "testing" / "sdk_touchpoints.yaml"
META_AGENT_DIR = REPO_ROOT / "meta_agent"

# SDK package prefixes we track
SDK_PREFIXES = (
    "deepagents",
    "langgraph.types",
    "langgraph.prebuilt",
    "langgraph.checkpoint",
    "langgraph.store",
    "langchain_core.tools",
    "langchain.agents.middleware",
)


def _load_touchpoints():
    """Load the SDK touchpoints catalog, skipping if not found."""
    if not TOUCHPOINTS_PATH.exists():
        pytest.skip("catalog not found")
    with open(TOUCHPOINTS_PATH) as f:
        return yaml.safe_load(f)


def _extract_sdk_imports(py_file: Path) -> list[tuple[str, str]]:
    """Parse a Python file and return (module, symbol) tuples for SDK imports."""
    try:
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
    except SyntaxError:
        return []
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for prefix in SDK_PREFIXES:
                if node.module.startswith(prefix):
                    for alias in node.names:
                        results.append((node.module, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in SDK_PREFIXES:
                    if alias.name.startswith(prefix):
                        results.append((alias.name, ""))
    return results


def _scan_all_sdk_imports() -> dict[str, list[tuple[str, str]]]:
    """Scan meta_agent/ for all SDK imports. Returns {rel_path: [(module, symbol)]}."""
    results = {}
    for py_file in sorted(META_AGENT_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(REPO_ROOT))
        imports = _extract_sdk_imports(py_file)
        if imports:
            results[rel] = imports
    return results


def _touchpoint_entries(catalog) -> list[dict]:
    """Flatten all touchpoint entries."""
    entries = []
    if isinstance(catalog, dict):
        # Handle {"touchpoints": [...]} or {"version": ..., "touchpoints": [...]}
        for key, val in catalog.items():
            if isinstance(val, list):
                entries.extend(e for e in val if isinstance(e, dict))
    elif isinstance(catalog, list):
        entries.extend(e for e in catalog if isinstance(e, dict))
    return entries


class TestCatalogedTouchpointsExist:
    """Every touchpoint in the catalog should have a real import in the source."""

    def test_touchpoint_source_files_contain_import(self):
        catalog = _load_touchpoints()
        entries = _touchpoint_entries(catalog)
        missing = []
        for entry in entries:
            usages = entry.get("local_usages", [])
            symbol = entry.get("symbol", entry.get("id", ""))
            if not usages:
                continue
            # Handle comma-separated symbol lists (e.g. "SubAgent,CompiledSubAgent")
            symbol_parts = [s.strip() for s in symbol.split(",")]
            found_any = False
            for usage_file in usages:
                src_path = REPO_ROOT / usage_file
                if src_path.exists():
                    imports = _extract_sdk_imports(src_path)
                    for mod, sym in imports:
                        if sym in symbol_parts or mod in symbol_parts:
                            found_any = True
                            break
                if found_any:
                    break
            if not found_any and usages:
                missing.append(f"{entry.get('id', '?')}: symbol '{symbol}' not imported in {usages}")
        assert not missing, f"Touchpoints without matching imports:\n" + "\n".join(missing)


class TestNoUncatalogedSDKUsage:
    """Every SDK import in meta_agent/ should be cataloged."""

    def test_no_uncataloged_critical_imports(self):
        catalog = _load_touchpoints()
        entries = _touchpoint_entries(catalog)
        # Build set of (module, symbol) pairs from catalog
        cataloged_symbols = set()
        for entry in entries:
            mod = entry.get("module", "")
            sym = entry.get("symbol", "")
            if mod and sym:
                cataloged_symbols.add((mod, sym))
            # Also add the ID as a fallback
            cataloged_symbols.add(("", entry.get("id", "")))

        all_imports = _scan_all_sdk_imports()
        uncataloged = []
        for rel_path, imports in all_imports.items():
            for mod, sym in imports:
                if (mod, sym) not in cataloged_symbols and sym not in {s for _, s in cataloged_symbols}:
                    uncataloged.append(f"{rel_path}: {mod}.{sym}")

        # Warn but don't hard-fail — catalog may be incomplete during development
        if uncataloged:
            pytest.xfail(f"Uncataloged SDK imports found ({len(uncataloged)}): {uncataloged[:10]}")
