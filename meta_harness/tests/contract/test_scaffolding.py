"""Smoke tests verifying that project scaffolding is correct."""

import importlib


def test_meta_harness_importable():
    """meta_harness package is importable with correct version."""
    import meta_harness

    assert meta_harness.__version__ == "0.1.0"


def test_third_party_imports():
    """All required third-party packages are importable."""
    for pkg in ("deepagents", "langgraph", "textual", "langchain_collapse", "pydantic", "langchain", "langsmith"):
        mod = importlib.import_module(pkg)
        assert mod is not None, f"Failed to import {pkg}"


def test_agent_subpackages():
    """All 7 agent role subpackages are importable."""
    roles = [
        "project_manager",
        "harness_engineer",
        "researcher",
        "architect",
        "planner",
        "developer",
        "evaluator",
    ]
    for role in roles:
        mod = importlib.import_module(f"meta_harness.agents.{role}")
        assert mod is not None, f"Failed to import meta_harness.agents.{role}"


def test_top_level_subpackages():
    """All top-level subpackages are importable."""
    for pkg in ("agents", "integrations", "tools", "profiles", "tui"):
        mod = importlib.import_module(f"meta_harness.{pkg}")
        assert mod is not None, f"Failed to import meta_harness.{pkg}"
