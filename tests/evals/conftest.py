"""Eval-specific pytest fixtures and hooks."""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-skip eval tests when ANTHROPIC_API_KEY is not set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        skip_marker = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
        for item in items:
            if "evals" in str(item.fspath):
                item.add_marker(skip_marker)
