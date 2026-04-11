# REPLACES: (no direct legacy equivalent — gap identified by audit)
"""Integration tests for the summarization tool middleware setup.

Validates that create_summarization_tool_middleware produces a correctly
configured SummarizationToolMiddleware from a prebuilt model instance and backend,
matching how graph.py and the provisioner now instantiate it.
"""

from __future__ import annotations

import pytest
from langchain.agents.middleware.types import AgentMiddleware

from deepagents.middleware.summarization import (
    SummarizationToolMiddleware,
    create_summarization_tool_middleware,
)
from meta_agent.backend import create_composite_backend
from tests._support.fake_models import GenericFakeChatModel
from tests._support.fake_runtime import make_runtime

COVERS = [
    'middleware.summarization_tool',
    'sdk.deepagents.SummarizationToolMW',
]


def _fake_model() -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(['stub']))


@pytest.mark.integration
class TestSummarizationToolMiddleware:
    """Tests for create_summarization_tool_middleware factory."""

    @pytest.fixture
    def backend(self, tmp_path):
        """Create a real CompositeBackend instance for tests."""
        factory = create_composite_backend(tmp_path)
        rt = make_runtime()
        return factory(rt)

    def test_returns_summarization_tool_middleware(self, tmp_path):
        """Factory returns a SummarizationToolMiddleware instance."""
        factory = create_composite_backend(tmp_path)
        mw = create_summarization_tool_middleware(_fake_model(), factory)
        assert isinstance(mw, SummarizationToolMiddleware)

    def test_accepts_prebuilt_model_instance(self, tmp_path):
        """Factory accepts a BaseChatModel instance without re-resolving a string."""
        factory = create_composite_backend(tmp_path)
        mw = create_summarization_tool_middleware(_fake_model(), factory)
        assert mw is not None

    def test_is_agent_middleware_subclass(self, tmp_path):
        """The returned middleware is an AgentMiddleware subclass."""
        factory = create_composite_backend(tmp_path)
        mw = create_summarization_tool_middleware(_fake_model(), factory)
        assert isinstance(mw, AgentMiddleware)

    def test_provides_compact_conversation_tool(self, tmp_path):
        """The middleware provides a 'compact_conversation' tool."""
        factory = create_composite_backend(tmp_path)
        mw = create_summarization_tool_middleware(_fake_model(), factory)
        assert hasattr(mw, 'tools')
        tool_names = [t.name for t in mw.tools]
        assert 'compact_conversation' in tool_names
