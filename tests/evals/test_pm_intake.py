"""Live eval tests for PM agent INTAKE stage behavior.

REPLACES: tests/unit/test_evals.py (partial — behavioral coverage)
REPLACES: tests/unit/test_phase1_evals.py (partial — intake behavior)
REPLACES: tests/unit/test_phase2_evals.py (partial — intake behavior)

These tests call the real Anthropic API via create_graph().
They are auto-skipped when ANTHROPIC_API_KEY is not set (see conftest.py).
"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage


@pytest.mark.eval
class TestPMIntake:
    """INTAKE stage behavioral evals — real model calls."""

    @pytest.fixture
    def graph(self):
        from meta_agent.graph import create_graph

        return create_graph()

    @pytest.fixture
    def initial_state(self):
        from meta_agent.state import create_initial_state

        return create_initial_state(project_id="test-pm-intake")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _invoke_safely(graph, state, config):
        """Invoke graph, handling API errors and HITL interrupts."""
        try:
            return graph.invoke(state, config=config)
        except Exception as exc:  # noqa: BLE001
            # GraphInterrupt means HITL gate fired — still a valid result
            # but we don't have a final state to inspect.
            from langgraph.types import Interrupt

            if isinstance(exc, BaseException) and "interrupt" in type(exc).__name__.lower():
                pytest.skip(f"Graph interrupted (HITL gate): {exc}")
            msg = str(exc).lower()
            if "api" in msg or "rate" in msg or "timeout" in msg:
                pytest.skip(f"API error: {exc}")
            raise

    # ------------------------------------------------------------------
    # Test 1 — Agent responds to initial product idea
    # ------------------------------------------------------------------

    @pytest.mark.timeout(120)
    def test_intake_responds_to_product_idea(self, graph, initial_state):
        """PM agent should respond to a product idea with clarifying questions."""
        initial_state["messages"] = [
            HumanMessage(content="I want to build a task management app for remote teams")
        ]

        config = {"configurable": {"thread_id": "test-intake-1"}}
        result = self._invoke_safely(graph, initial_state, config)

        # Must have at least one AI response
        ai_messages = [m for m in result["messages"] if m.type == "ai" and m.content]
        assert len(ai_messages) >= 1, "Agent should respond to product idea"

        # Should still be in INTAKE stage
        assert result["current_stage"] == "INTAKE"

        # Response should contain question marks (clarifying questions)
        response_text = ai_messages[-1].content
        assert "?" in response_text, "Agent should ask clarifying questions during intake"

    # ------------------------------------------------------------------
    # Test 2 — Agent does NOT advance stage prematurely
    # ------------------------------------------------------------------

    @pytest.mark.timeout(120)
    def test_intake_stays_in_intake_stage(self, graph, initial_state):
        """PM agent should NOT advance past INTAKE on first message."""
        initial_state["messages"] = [
            HumanMessage(content="Build me a simple todo list app")
        ]

        config = {"configurable": {"thread_id": "test-intake-2"}}
        result = self._invoke_safely(graph, initial_state, config)

        assert result["current_stage"] == "INTAKE", (
            f"Expected INTAKE but got {result['current_stage']}. "
            "Agent should not advance stage on first message."
        )

    # ------------------------------------------------------------------
    # Test 3 — Agent gives substantive response
    # ------------------------------------------------------------------

    @pytest.mark.timeout(120)
    def test_intake_response_is_substantive(self, graph, initial_state):
        """PM agent response should be substantive, not just an acknowledgment."""
        initial_state["messages"] = [
            HumanMessage(
                content=(
                    "I need a platform that helps data scientists collaborate on "
                    "ML experiments, track model versions, and share results with "
                    "stakeholders"
                )
            )
        ]

        config = {"configurable": {"thread_id": "test-intake-3"}}
        result = self._invoke_safely(graph, initial_state, config)

        ai_messages = [m for m in result["messages"] if m.type == "ai" and m.content]
        assert len(ai_messages) >= 1, "Agent should produce at least one AI message"

        response_text = ai_messages[-1].content
        assert len(response_text) > 100, (
            f"Response too short ({len(response_text)} chars). "
            "PM should give a substantive intake response."
        )
