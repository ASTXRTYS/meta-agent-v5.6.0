from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from meta_agent.evals.research import evaluators as research_evaluators
from meta_agent.evals.research.common import (
    extract_functional_requirements,
    extract_markdown_section,
    get_canonical_eval_ids,
    missing_research_bundle_sections,
    present_research_bundle_sections,
)
from meta_agent.evals.research.dataset_builder import build_dataset
from meta_agent.evals.research.evaluators import (
    RESEARCH_EVAL_REGISTRY,
    eval_rb_005,
    eval_rinfra_003,
    eval_ri_002,
    eval_ri_003,
)
from meta_agent.evals.research.langsmith_experiment import _make_langsmith_evaluator
from meta_agent.evals.research.langsmith_ui_profiles import EVALUATOR_PROFILES
from meta_agent.evals.research.report import generate_report_from_experiment_results, normalize_eval_id
from meta_agent.evals.research.runner import _check_gate, run_suite
from meta_agent.evals.research.synthetic_trace_adapter import load_calibration_dataset


DATASETS_DIR = "/Users/Jason/2026/v4/meta-agent-v5.6.0/datasets"


def _mock_run(outputs: dict) -> SimpleNamespace:
    return SimpleNamespace(outputs=outputs)


def _mock_example(inputs: dict, outputs: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(inputs=inputs, outputs=outputs or {})


def test_registry_matches_canonical_eval_suite_ids():
    assert set(RESEARCH_EVAL_REGISTRY) == set(get_canonical_eval_ids())
    assert "RB-005a" not in RESEARCH_EVAL_REGISTRY
    assert "RB-005b" not in RESEARCH_EVAL_REGISTRY


def test_extract_functional_requirements_returns_a_through_k():
    requirements = extract_functional_requirements()
    labels = [requirement["label"] for requirement in requirements]
    assert labels == list("ABCDEFGHIJK")


def test_calibration_dataset_uses_json_paths_and_five_examples():
    examples = load_calibration_dataset(DATASETS_DIR)
    assert len(examples) == 5
    assert {example["metadata"]["scenario_type"] for example in examples} == {
        "golden_path",
        "silver_path",
        "bronze_path",
        "citation_hallucination_failure",
        "hitl_subagent_failure",
    }
    for example in examples:
        assert example["inputs"]["eval_suite_path"].endswith(".json")
        assert example["inputs"]["prd_path"].endswith("research-agent-prd.md")
        assert set(example["outputs"]["expected_evals"]) == set(get_canonical_eval_ids())
        assert example["outputs"]["expected_evals"]["RI-001"] == "deferred"
        state_out = example["outputs"]["state_out"]
        assert "research_bundle_path" in state_out
        assert "trace_summary" in state_out
    golden = next(example for example in examples if example["metadata"]["scenario_type"] == "golden_path")
    assert golden["outputs"]["delegation_context"]
    assert golden["outputs"]["gap_remediation_context"]
    hitl_failure = next(example for example in examples if example["metadata"]["scenario_type"] == "hitl_subagent_failure")
    assert hitl_failure["outputs"]["hitl_cluster_content"]
    silver = next(example for example in examples if example["metadata"]["scenario_type"] == "silver_path")
    assert silver["outputs"]["citation_claim_support"] == []
    assert silver["outputs"]["expected_evals"]["RB-005"] == "fail"
    assert hitl_failure["outputs"]["expected_evals"]["RI-002"] == "fail"
    golden = next(example for example in examples if example["metadata"]["scenario_type"] == "golden_path")
    assert golden["outputs"]["expected_evals"]["RQ-012"] == 4
    bronze = next(example for example in examples if example["metadata"]["scenario_type"] == "bronze_path")
    assert bronze["outputs"]["expected_evals"]["RB-001"] == "fail"


def test_dataset_builder_returns_raw_example_array():
    examples = build_dataset(DATASETS_DIR)
    assert len(examples) == 5
    assert isinstance(examples[0]["inputs"], dict)
    assert isinstance(examples[0]["outputs"], dict)


def test_golden_bundle_uses_v561_section_contract():
    bundle = Path(DATASETS_DIR, "golden-path", "stage6-research-bundle.md").read_text()
    present = present_research_bundle_sections(bundle)

    assert missing_research_bundle_sections(bundle) == []
    assert len(present) == 13
    assert "dataset, evaluator, trace, and experiment" in extract_markdown_section(
        bundle,
        "Research Methodology",
    )


def test_rinfra_003_fails_old_bundle_shape_before_judge():
    old_bundle = """---
artifact: research-bundle
project_id: meta-agent
title: Old Bundle
version: "1.0.0"
status: complete
stage: RESEARCH
authors:
  - research-agent
lineage:
  - artifacts/intake/research-agent-prd.md
---

## Executive Summary

Summary.

## 1. Orchestration Architecture

Old content.

## 2. State Management & Persistence

Old content.
"""
    result = asyncio.run(eval_rinfra_003(_mock_run({"research_bundle_content": old_bundle}), _mock_example({})))
    assert result["score"] in {1, 2}
    assert "missing_required_sections" in result["flags"]


def test_rinfra_003_accepts_v561_bundle_shape(monkeypatch: pytest.MonkeyPatch):
    bundle = Path(DATASETS_DIR, "golden-path", "stage6-research-bundle.md").read_text()

    async def fake_run_likert_judge(**kwargs):
        assert "13/13 canonical sections found" in kwargs["specific_instructions"]
        return {"score": 5, "comment": "schema looks complete"}

    monkeypatch.setattr(research_evaluators, "run_likert_judge", fake_run_likert_judge)

    result = asyncio.run(eval_rinfra_003(_mock_run({"research_bundle_content": bundle}), _mock_example({})))
    assert result["score"] == 5


def test_langsmith_wrapper_emits_canonical_key_and_metadata():
    def evaluator(_run, _example):
        return {
            "score": 4,
            "comment": "Good enough",
            "reasoning": "Detailed judge reasoning",
            "evidence": ["specific evidence"],
            "confidence": "HIGH",
            "flags": ["minor_gap"],
            "details": {"judge_backend": {"provider": "anthropic", "model": "claude"}},
        }

    wrapped = _make_langsmith_evaluator("RQ-001", evaluator)
    result = wrapped(SimpleNamespace(outputs={}), SimpleNamespace(outputs={}))

    assert result["key"] == "RQ-001"
    assert result["metadata"]["eval_id"] == "RQ-001"
    assert result["metadata"]["reasoning"] == "Detailed judge reasoning"
    assert result["metadata"]["details"]["judge_backend"]["provider"] == "anthropic"


def test_report_from_langsmith_results_preserves_metadata_and_normalizes_legacy_keys():
    fake_results = [
        {
            "evaluation_results": {
                "results": [
                    SimpleNamespace(
                        key="eval_rq_001",
                        score=3,
                        comment="Needs more depth",
                        metadata={
                            "reasoning": "Detailed judge reasoning",
                            "evidence": ["missing tradeoff analysis"],
                            "confidence": "MEDIUM",
                            "flags": ["needs_depth"],
                            "details": {"judge_backend": {"provider": "anthropic", "model": "claude"}},
                        },
                    )
                ]
            }
        }
    ]

    report = generate_report_from_experiment_results(
        fake_results,
        experiment_name="langsmith-test",
        scenario="multi_scenario_calibration",
    )

    assert normalize_eval_id("eval_rq_001") == "RQ-001"
    assert "### RQ-001" in report
    assert "BELOW THRESHOLD" in report
    assert "Detailed judge reasoning" in report
    assert "missing tradeoff analysis" in report
    assert "Provider:** anthropic" in report


def test_rb_001_requires_full_coverage_or_flag():
    from meta_agent.evals.research.deterministic import eval_rb_001

    partial_run = _mock_run(
        {
            "trace_summary": {
                "tool_calls": [
                    {"name": "read_file", "args": {"file_path": "/workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md", "offset": 0, "length": 100}}
                ],
                "prd_fully_read": False,
                "prd_total_chars": 1000,
            }
        }
    )
    example = _mock_example({"prd_content": "x" * 1000})
    result = eval_rb_001(partial_run, example)
    assert result["score"] == 0
    assert {"score", "comment", "reasoning", "evidence", "confidence", "flags"} <= set(result)

    full_run = _mock_run(
        {
            "trace_summary": {
                "tool_calls": [
                    {"name": "read_file", "args": {"file_path": "/workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md", "offset": 0, "length": 1000}}
                ],
                "prd_fully_read": False,
                "prd_total_chars": 1000,
            }
        }
    )
    assert eval_rb_001(full_run, example)["score"] == 1


def test_rb_002_fails_when_eval_suite_read_happens_after_research():
    from meta_agent.evals.research.deterministic import eval_rb_002

    run = _mock_run(
        {
            "trace_summary": {
                "tool_calls": [
                    {"name": "web_search", "args": {"query": "langsmith evaluators"}, "timestamp": 1},
                    {"name": "read_file", "args": {"file_path": "/workspace/projects/meta-agent/evals/eval-suite-prd.json"}, "timestamp": 2},
                ]
            }
        }
    )
    result = eval_rb_002(run, _mock_example({}))
    assert result["score"] == 0


def test_rb_005_fails_for_missing_cited_fetches():
    run = _mock_run(
        {
            "research_bundle_content": "Finding with citation https://example.com/missing-source",
            "trace_summary": {
                "tool_calls": [
                    {"name": "web_fetch", "args": {"url": "https://example.com/other-source"}}
                ]
            },
            "citation_claim_support": [],
        }
    )
    result = asyncio.run(eval_rb_005(run, _mock_example({})))
    assert result["score"] == 0
    assert "missing_trace_fetch" in result["flags"]


def test_hitl_and_subagent_failure_scenario_trips_targeted_binary_metrics():
    examples = load_calibration_dataset(DATASETS_DIR)
    example = next(example for example in examples if example["metadata"]["scenario_type"] == "hitl_subagent_failure")
    run = _mock_run(example["outputs"])
    mock_example = _mock_example(example["inputs"], example["outputs"])

    rb_009 = asyncio.run(RESEARCH_EVAL_REGISTRY["RB-009"]["fn"](run, mock_example))
    rb_010 = asyncio.run(RESEARCH_EVAL_REGISTRY["RB-010"]["fn"](run, mock_example))
    rb_011 = asyncio.run(RESEARCH_EVAL_REGISTRY["RB-011"]["fn"](run, mock_example))

    assert rb_009["score"] == 0
    assert rb_010["score"] == 0
    assert rb_011["score"] == 0


def test_integration_hybrids_pass_on_golden_path():
    examples = load_calibration_dataset(DATASETS_DIR)
    example = next(example for example in examples if example["metadata"]["scenario_type"] == "golden_path")
    run = _mock_run(example["outputs"])
    mock_example = _mock_example(example["inputs"], example["outputs"])

    ri_002 = asyncio.run(eval_ri_002(run, mock_example))
    ri_003 = asyncio.run(eval_ri_003(run, mock_example))

    assert ri_002["score"] == 1
    assert ri_003["score"] == 1


def test_phase_c_gate_is_strict_per_eval():
    results = [
        {"eval_id": "RINFRA-003", "score": 5},
        {"eval_id": "RINFRA-004", "score": 5},
        {"eval_id": "RQ-001", "score": 3},
        {"eval_id": "RQ-002", "score": 5},
        {"eval_id": "RQ-003", "score": 5},
        {"eval_id": "RQ-004", "score": 5},
        {"eval_id": "RQ-005", "score": 5},
        {"eval_id": "RQ-006", "score": 5},
        {"eval_id": "RQ-007", "score": 5},
        {"eval_id": "RQ-008", "score": 5},
        {"eval_id": "RQ-009", "score": 5},
        {"eval_id": "RQ-010", "score": 5},
        {"eval_id": "RQ-011", "score": 5},
        {"eval_id": "RQ-012", "score": 5},
        {"eval_id": "RQ-013", "score": 5},
        {"eval_id": "RR-001", "score": 5},
        {"eval_id": "RR-002", "score": 5},
        {"eval_id": "RR-003", "score": 5},
    ]
    assert _check_gate("C", results, evaluation_mode="trace") is False


def test_runner_executes_phase_a_on_generated_scenarios():
    summary = asyncio.run(
        run_suite(
            DATASETS_DIR,
            phases=["A"],
            scenario="silver_path",
            evaluation_mode="calibration",
            verbose=False,
        )
    )
    assert summary["passed"] is True
    assert len(summary["results"]) == len(PHASE_GATES_A())


def PHASE_GATES_A() -> list[str]:
    return ["RINFRA-001", "RINFRA-002", "RS-001", "RS-002", "RS-003", "RS-004"]


def test_langsmith_ui_profiles_only_emit_canonical_ids():
    profile_ids = {profile["eval_id"] for profile in EVALUATOR_PROFILES}
    assert "RB-005" in profile_ids
    assert "RB-005a" not in profile_ids
    assert "RB-005b" not in profile_ids
