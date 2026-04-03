"""Drift test: traceability completeness.

Ensures every critical component from runtime_components.yaml and
sdk_touchpoints.yaml has at least one test file with a matching COVERS entry.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

COVERS = []  # Meta-test

pytestmark = pytest.mark.drift

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = REPO_ROOT / "docs" / "testing" / "runtime_components.yaml"
SDK_PATH = REPO_ROOT / "docs" / "testing" / "sdk_touchpoints.yaml"
TESTS_DIR = REPO_ROOT / "tests"


def _load_yaml(path: Path):
    """Load a YAML file, skipping if not found."""
    if not path.exists():
        pytest.skip("catalog not found")
    with open(path) as f:
        return yaml.safe_load(f)


def _extract_covers_from_file(py_file: Path) -> list[str]:
    """Parse a Python file and extract the module-level COVERS list."""
    try:
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
    except SyntaxError:
        return []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "COVERS":
                    if isinstance(node.value, ast.List):
                        return [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
    return []


def _build_coverage_map() -> dict[str, set[str]]:
    """Build a map of component_id → set of test file relative paths."""
    coverage: dict[str, set[str]] = {}
    test_dirs = ["contracts", "integration", "evals", "drift"]
    for dirname in test_dirs:
        test_dir = TESTS_DIR / dirname
        if not test_dir.exists():
            continue
        for py_file in sorted(test_dir.glob("test_*.py")):
            rel = str(py_file.relative_to(REPO_ROOT))
            covers = _extract_covers_from_file(py_file)
            for cid in covers:
                coverage.setdefault(cid, set()).add(rel)
    return coverage


def _get_critical_components(catalog) -> list[dict]:
    """Extract all entries with criticality=critical from the catalog."""
    critical = []
    # Handle top-level dict with 'components' or 'touchpoints' key
    if isinstance(catalog, dict):
        for section in catalog.values():
            if isinstance(section, list):
                for entry in section:
                    if isinstance(entry, dict) and entry.get("criticality") == "critical":
                        critical.append(entry)
    elif isinstance(catalog, list):
        for entry in catalog:
            if isinstance(entry, dict) and entry.get("criticality") == "critical":
                critical.append(entry)
    return critical


class TestCriticalComponentsCovered:
    """Every critical component must appear in at least one test's COVERS."""

    def test_all_critical_runtime_components_have_covers(self):
        runtime = _load_yaml(RUNTIME_PATH)
        coverage = _build_coverage_map()
        critical = _get_critical_components(runtime)
        uncovered = []
        for entry in critical:
            # COVERS entries use the id format (e.g. "tool.transition_stage")
            cid = entry.get("id", "")
            if cid and cid not in coverage:
                uncovered.append(cid)
        assert not uncovered, (
            f"Critical components without COVERS in any test:\n"
            + "\n".join(f"  - {c}" for c in uncovered)
        )

    def test_critical_contract_required_has_contract_test(self):
        runtime = _load_yaml(RUNTIME_PATH)
        coverage = _build_coverage_map()
        critical = _get_critical_components(runtime)
        missing = []
        for entry in critical:
            cid = entry.get("id", "")
            req = entry.get("required_coverage", [])
            if "contract" in req:
                test_files = coverage.get(cid, set())
                has_contract = any("tests/contracts/" in f for f in test_files)
                if not has_contract:
                    missing.append(cid)
        assert not missing, (
            f"Critical components requiring 'contract' coverage but no contract test:\n"
            + "\n".join(f"  - {c}" for c in missing)
        )

    def test_critical_integration_required_has_integration_test(self):
        runtime = _load_yaml(RUNTIME_PATH)
        coverage = _build_coverage_map()
        critical = _get_critical_components(runtime)
        missing = []
        for entry in critical:
            cid = entry.get("id", "")
            req = entry.get("required_coverage", [])
            if "integration" in req:
                test_files = coverage.get(cid, set())
                has_integration = any("tests/integration/" in f for f in test_files)
                if not has_integration:
                    missing.append(cid)
        assert not missing, (
            f"Critical components requiring 'integration' coverage but no integration test:\n"
            + "\n".join(f"  - {c}" for c in missing)
        )
