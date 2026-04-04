"""Eval-specific pytest fixtures and hooks.

Model fixture adapted from the Deep Agents SDK reference:
  .reference/libs/evals/tests/evals/conftest.py
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help=(
            "Model to run evals against "
            "(e.g. 'anthropic:claude-sonnet-4-6'). "
            "Defaults to anthropic:claude-sonnet-4-6."
        ),
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item],
) -> None:
    """Auto-skip eval tests when ANTHROPIC_API_KEY is not set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        skip_marker = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
        for item in items:
            if "evals" in str(item.fspath):
                item.add_marker(skip_marker)


@pytest.fixture
def model(request: pytest.FixtureRequest) -> BaseChatModel:
    """Create a chat model for eval tests.

    Override the default model via ``--model`` CLI option::

        pytest --model anthropic:claude-opus-4-6 tests/evals/
    """
    from langchain.chat_models import init_chat_model

    model_name = request.config.getoption("--model") or "anthropic:claude-sonnet-4-6"
    return init_chat_model(model_name)
