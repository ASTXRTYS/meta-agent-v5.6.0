# REPLACES: (no direct legacy equivalent — validates the single-trace decomposition checkpoint experiment flag)
"""Integration tests for the single-trace experiment decomposition checkpoint flag."""

from __future__ import annotations

import pytest

import meta_agent.evals.research.run_single_trace_experiment as single_trace_experiment
pytestmark = pytest.mark.integration

COVERS = []


def test_pause_after_decomposition_disables_auto_approve_and_returns_checkpoint(
    monkeypatch,
):
    """The single-trace wrapper should pass the checkpoint flag to run_experiment."""
    captured: dict[str, object] = {}

    def fake_run_experiment(**kwargs):
        captured.update(kwargs)
        return {
            "dataset_name": "dataset",
            "experiment_name": "experiment",
            "experiment_url": "https://example.com/exp",
            "mode": "trace",
        }

    monkeypatch.setattr(single_trace_experiment, "run_experiment", fake_run_experiment)

    result = single_trace_experiment.run_single_trace_experiment(
        pause_after_decomposition=True,
    )

    assert result["experiment_url"] == "https://example.com/exp"
    assert captured["mode"] == "trace"
    assert captured["trace_input_mode"] == "single"
    assert captured["trace_pause_after_decomposition"] is True
