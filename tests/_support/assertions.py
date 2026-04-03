"""Custom assertion helpers for test suite."""

from __future__ import annotations

from typing import Any

from langgraph.types import Command


def assert_command_update(result: Any, expected_keys: set[str]) -> None:
    """Assert result is a Command with expected update keys.

    Args:
        result: The value to check (should be a LangGraph Command).
        expected_keys: Set of key names expected in `result.update`.

    Raises:
        AssertionError: If result is not a Command or is missing keys.
    """
    assert isinstance(result, Command), f"Expected Command, got {type(result)}"
    assert hasattr(result, "update"), "Command missing update"
    actual_keys = set(result.update.keys())
    missing = expected_keys - actual_keys
    assert not missing, f"Missing keys in Command.update: {missing}"


def assert_tool_names(tools: Any, expected_names: set[str]) -> None:
    """Assert a list of tools has exactly the expected `.name` values.

    Args:
        tools: Iterable of tool objects with a `.name` attribute.
        expected_names: Set of tool names that should be present.

    Raises:
        AssertionError: If there are missing or unexpected tool names.
    """
    actual = {t.name for t in tools}
    missing = expected_names - actual
    extra = actual - expected_names
    assert not missing, f"Missing tools: {missing}"
    assert not extra, f"Unexpected tools: {extra}"
