from __future__ import annotations

import asyncio
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from meta_agent.evals.research.judge_infra import (
    _build_anthropic_call_kwargs,
    run_binary_judge,
    run_likert_judge,
)
from meta_agent.evals.research.judge_trace_context import build_trace_context_pack
from meta_agent.evals.research.langsmith_experiment import _make_langsmith_evaluator
from meta_agent.evals.research.langsmith_ui_profiles import EVALUATOR_PROFILES


pytestmark = pytest.mark.legacy


def test_anthropic_judge_kwargs_use_adaptive_thinking_without_temp_or_effort():
    kwargs = _build_anthropic_call_kwargs(
        model="claude-opus-4-6",
        system_prompt="system",
        user_prompt="user",
    )
    assert kwargs["model"] == "claude-opus-4-6"
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert "temperature" not in kwargs
    assert "output_config" not in kwargs
    assert kwargs["messages"] == [{"role": "user", "content": "user"}]


def test_trace_context_pack_assembles_from_run_only():
    run = SimpleNamespace(
        id="run-1",
        trace_id="trace-1",
        outputs={
            "research_bundle_content": "bundle",
            "trace_summary": {"tool_calls": [{"name": "web_fetch", "args": {"url": "https://example.com"}}]},
        },
    )
    pack = build_trace_context_pack(run, eval_id="RQ-001", require_full_trace_fetch=False)
    assert pack["trace_context_source"] == "run_only"
    assert pack["run_id"] == "run-1"
    assert pack["trace_id"] == "trace-1"
    assert pack["judge_view"]["trace_tool_call_preview"][0]["name"] == "web_fetch"


def test_trace_context_pack_prefers_langsmith_fetched_trace(monkeypatch: pytest.MonkeyPatch):
    class DummyClient:
        pass

    fetched = SimpleNamespace(
        id="run-fetched",
        trace_id="trace-fetched",
        name="root-run",
        run_type="chain",
        outputs={"trace_summary": {"tool_calls": [{"name": "task", "args": {"description": "parallel"}}]}},
        child_runs=[SimpleNamespace(id="child-1", trace_id="trace-fetched", name="child", run_type="tool", outputs={})],
    )

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    from meta_agent.evals.research import judge_trace_context

    monkeypatch.setattr(judge_trace_context, "_langsmith_client", lambda: DummyClient())
    monkeypatch.setattr(judge_trace_context, "_read_run_with_children", lambda client, run_id: fetched)

    run = SimpleNamespace(id="run-raw", trace_id="trace-raw", outputs={"trace_summary": {}})
    pack = build_trace_context_pack(run, eval_id="RB-009", require_full_trace_fetch=True)
    assert pack["trace_context_source"] == "langsmith_fetched_trace"
    assert pack["judge_view"]["run_id"] == "run-fetched"
    assert pack["judge_view"]["child_run_summaries"][0]["id"] == "child-1"


def test_langsmith_evaluator_metadata_includes_judge_trace_fields():
    def evaluator(_run, _example):
        return {
            "score": 1,
            "comment": "pass",
            "reasoning": "reasoning",
            "details": {
                "judge_backend": {"provider": "anthropic", "model": "claude-opus-4-6"},
                "judge_trace": {
                    "category": "RESEARCH-BEHAVIORAL",
                    "scoring": "binary_pass_fail",
                    "evaluation_method": "anthropic_messages_stream",
                    "judge_model": "claude-opus-4-6",
                    "thinking_type": "adaptive",
                    "streaming_used": True,
                    "tools_enabled": False,
                },
                "trace_context_source": "langsmith_fetched_trace",
            },
        }

    wrapped = _make_langsmith_evaluator("RB-009", evaluator)
    result = wrapped(SimpleNamespace(outputs={}), SimpleNamespace(outputs={}))
    metadata = result["metadata"]
    assert metadata["judge_category"] == "RESEARCH-BEHAVIORAL"
    assert metadata["judge_scoring"] == "binary_pass_fail"
    assert metadata["judge_evaluation_method"] == "anthropic_messages_stream"
    assert metadata["judge_thinking_type"] == "adaptive"
    assert metadata["trace_context_source"] == "langsmith_fetched_trace"


def test_langsmith_ui_profiles_recommend_opus_and_trace_policy_alignment():
    assert EVALUATOR_PROFILES
    for profile in EVALUATOR_PROFILES:
        assert profile["recommended_model"] == "claude-opus-4-6"
        prompt = profile["prompt"]
        assert "Category Policy" in prompt
        assert "trace_context" in prompt


def test_run_likert_judge_returns_structured_failure_on_stream_error(
    monkeypatch: pytest.MonkeyPatch,
):
    class FailingMessages:
        def stream(self, **_kwargs):
            raise anthropic.APIConnectionError(
                message="simulated stream failure",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

        async def create(self, **_kwargs):
            raise AssertionError("create should not be called when streaming is enabled")

    monkeypatch.delenv("RESEARCH_EVAL_JUDGE_STREAMING", raising=False)
    monkeypatch.setattr(
        "meta_agent.evals.research.judge_infra._judge_client",
        lambda: SimpleNamespace(messages=FailingMessages()),
    )

    result = asyncio.run(
        run_likert_judge(
            eval_id="RQ-001",
            eval_name="Research Quality",
            anchors={
                1: "poor",
                2: "weak",
                3: "adequate",
                4: "good",
                5: "excellent",
            },
            specific_instructions="Score for quality.",
            agent_output="Test output payload.",
        )
    )

    assert result["score"] == -1
    assert "judge_error" in result["flags"]
    assert "Judge invocation failed" in result["reasoning"]
    backend = result["details"]["judge_backend"]
    assert backend["evaluation_method"] == "anthropic_messages_stream"
    assert backend["errors"] == ["simulated stream failure"]


def test_run_binary_judge_returns_structured_failure_on_create_error(
    monkeypatch: pytest.MonkeyPatch,
):
    class FailingMessages:
        def stream(self, **_kwargs):
            raise AssertionError("stream should not be called when streaming is disabled")

        async def create(self, **_kwargs):
            raise anthropic.APIConnectionError(
                message="simulated create failure",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

    monkeypatch.setenv("RESEARCH_EVAL_JUDGE_STREAMING", "0")
    monkeypatch.setattr(
        "meta_agent.evals.research.judge_infra._judge_client",
        lambda: SimpleNamespace(messages=FailingMessages()),
    )

    result = asyncio.run(
        run_binary_judge(
            eval_id="RB-001",
            eval_name="Behavioral Gate",
            pass_criteria="Must satisfy criterion.",
            trace_data='{"steps":[]}',
            additional_context="",
        )
    )

    assert result["score"] == -1
    assert "judge_error" in result["flags"]
    assert "Judge invocation failed" in result["reasoning"]
    backend = result["details"]["judge_backend"]
    assert backend["evaluation_method"] == "anthropic_messages_create"
    assert backend["errors"] == ["simulated create failure"]
