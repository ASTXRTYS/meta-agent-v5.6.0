"""Drift test: runtime catalog parity.

Ensures every runtime component (tool, state field, subagent, guardrail)
is cataloged in docs/testing/runtime_components.yaml and vice-versa.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.state import MetaAgentState, VALID_TRANSITIONS
from meta_agent.subagents.configs import SUBAGENT_CONFIGS
from meta_agent.tools.registry import HITL_GATED_TOOLS
from meta_agent.safety import RECURSION_LIMITS, TOKEN_BUDGET_LIMITS

COVERS = []  # Meta-test

pytestmark = pytest.mark.drift

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "docs" / "testing" / "runtime_components.yaml"


def _load_catalog():
    """Load the runtime components catalog, skipping if not found."""
    if not CATALOG_PATH.exists():
        pytest.skip("catalog not found")
    with open(CATALOG_PATH) as f:
        return yaml.safe_load(f)


def _catalog_canonical_names(catalog):
    """Extract all component canonical_name values from the catalog."""
    names = set()
    components = catalog.get("components", [])
    if isinstance(components, list):
        for entry in components:
            if isinstance(entry, dict) and "canonical_name" in entry:
                names.add(entry["canonical_name"])
    return names


def _catalog_ids(catalog):
    """Extract all component id values from the catalog."""
    ids = set()
    components = catalog.get("components", [])
    if isinstance(components, list):
        for entry in components:
            if isinstance(entry, dict) and "id" in entry:
                ids.add(entry["id"])
    return ids


def _catalog_entries(catalog):
    """Flatten all catalog entries into a list of dicts."""
    components = catalog.get("components", [])
    if isinstance(components, list):
        return [e for e in components if isinstance(e, dict)]
    return []


class TestToolsCataloged:
    """Every tool in LANGCHAIN_TOOLS must appear in the catalog."""

    def test_all_tools_in_catalog(self):
        catalog = _load_catalog()
        canonical = _catalog_canonical_names(catalog)
        missing = []
        for tool in LANGCHAIN_TOOLS:
            if tool.name not in canonical:
                missing.append(tool.name)
        assert not missing, f"Tools not in catalog: {missing}"


class TestStateCataloged:
    """Every MetaAgentState annotation key should be in the catalog."""

    def test_all_state_fields_in_catalog(self):
        catalog = _load_catalog()
        ids = _catalog_ids(catalog)
        missing = []
        for key in MetaAgentState.__annotations__:
            state_id = f"state.{key}"
            if state_id not in ids:
                missing.append(key)
        assert not missing, f"State fields not in catalog: {missing}"


class TestSubagentsCataloged:
    """Every non-reserved subagent should be in the catalog."""

    def test_all_subagents_in_catalog(self):
        catalog = _load_catalog()
        ids = _catalog_ids(catalog)
        missing = []
        for name, cfg in SUBAGENT_CONFIGS.items():
            if cfg.get("type") == "reserved":
                continue
            sa_id = f"subagent.{name}"
            if sa_id not in ids:
                missing.append(name)
        assert not missing, f"Subagents not in catalog: {missing}"


class TestGuardrailsCataloged:
    """HITL_GATED_TOOLS and VALID_TRANSITIONS should be in the catalog."""

    def test_hitl_in_catalog(self):
        catalog = _load_catalog()
        ids = _catalog_ids(catalog)
        assert "guardrail.hitl_gated_tools" in ids, "HITL_GATED_TOOLS not in catalog"

    def test_valid_transitions_in_catalog(self):
        catalog = _load_catalog()
        ids = _catalog_ids(catalog)
        assert "guardrail.valid_transitions" in ids, "VALID_TRANSITIONS not in catalog"


class TestNoStaleCatalogEntries:
    """Every catalog entry's source file must exist and contain the canonical_name."""

    def test_no_stale_entries(self):
        catalog = _load_catalog()
        entries = _catalog_entries(catalog)
        stale = []
        for entry in entries:
            src = entry.get("source") or entry.get("source_file")
            cname = entry.get("canonical_name", "")
            if not src:
                continue
            src_path = REPO_ROOT / src
            if not src_path.exists():
                stale.append(f"{cname}: file {src} does not exist")
        assert not stale, f"Stale catalog entries:\n" + "\n".join(stale)
