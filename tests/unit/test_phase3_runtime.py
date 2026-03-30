"""Unit tests for Phase 3 runtime helpers and stage gates."""

from __future__ import annotations

import json
import os

from meta_agent.stages import ResearchStage, SpecGenerationStage, SpecReviewStage
from meta_agent.subagents.research_agent import (
    get_research_runtime_paths,
    normalize_research_outputs,
)
from meta_agent.subagents.verification_agent import parse_verification_verdict


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def test_research_runtime_paths(tmp_path):
    paths = get_research_runtime_paths(str(tmp_path), "demo")
    assert paths.bundle_path.endswith("artifacts/research/research-bundle.md")
    assert paths.decomposition_path.endswith("artifacts/research/research-decomposition.md")
    assert paths.eval_suite_path.endswith("evals/eval-suite-prd.json")


def test_normalize_research_outputs(tmp_path):
    project_dir = str(tmp_path)
    project_id = "meta-agent"
    prd_path = os.path.join(project_dir, "artifacts", "intake", "research-agent-prd.md")
    eval_path = os.path.join(project_dir, "evals", "eval-suite-prd.json")
    decomposition_path = os.path.join(project_dir, "artifacts", "research", "research-decomposition.md")
    clusters_path = os.path.join(project_dir, "artifacts", "research", "research-clusters.md")
    bundle_path = os.path.join(project_dir, "artifacts", "research", "research-bundle.md")

    _write(prd_path, "# PRD\n" + ("A" * 200))
    _write(eval_path, json.dumps({"metadata": {"artifact": "eval-suite-prd"}, "evals": [{"id": "EVAL-001"}]}))
    _write(decomposition_path, "---\nartifact: research-decomposition\n---\n## Domain 1\n")
    _write(clusters_path, "---\nartifact: research-clusters\n---\n## Cluster 1\n")
    _write(
        bundle_path,
        """---
artifact: research-bundle
project_id: meta-agent
title: Research Bundle
version: "1.0.0"
status: complete
stage: RESEARCH
authors:
  - research-agent
lineage:
  - artifacts/intake/research-agent-prd.md
---

## Ecosystem Options with Tradeoffs
https://docs.example.com/guide

## Rejected Alternatives with Rationale
content

## Model Capability Matrix
content

## SME Perspectives
content

## Risks and Caveats
content

## Confidence Assessment per Domain
content

## Research Methodology
content

## Unresolved Questions for Spec-Writer
content

## PRD Coverage Matrix
content

## Unresolved Research Gaps
content

## Skills Baseline Summary
content

## Gap and Contradiction Remediation Log
content

## Citation Index
https://docs.example.com/guide
""",
    )

    raw_result = {
        "messages": [
            {
                "tool_calls": [
                    {"name": "read_file", "args": {"file_path": prd_path, "offset": 0, "length": 250}},
                    {"name": "read_file", "args": {"file_path": eval_path}},
                    {"name": "read_file", "args": {"file_path": "/Users/Jason/.agents/skills/deep-agents-core/SKILL.md"}},
                ]
            },
            {
                "tool_calls": [
                    {"name": "task", "args": {"subagent_type": "general-purpose", "description": "Research runtime foundations"}},
                    {"name": "task", "args": {"subagent_type": "general-purpose", "description": "Research Anthropic model capabilities"}},
                ]
            },
            {
                "tool_calls": [
                    {"name": "write_file", "args": {"file_path": decomposition_path}},
                    {"name": "request_approval", "args": {"artifact_path": clusters_path, "summary": "approve deep-dive"}},
                    {"name": "web_fetch", "args": {"url": "https://docs.example.com/guide"}},
                ]
            },
        ],
        "approval_history": [{"artifact": clusters_path, "action": "approved"}],
    }

    outputs = normalize_research_outputs(
        raw_result,
        project_dir=project_dir,
        project_id=project_id,
        input_state={"prd_path": prd_path, "eval_suite_path": eval_path},
    )

    assert outputs["research_bundle_path"] == bundle_path
    assert outputs["decomposition_path"] == decomposition_path
    assert outputs["state_out"]["research_bundle_path"] == bundle_path
    assert outputs["trace_summary"]["prd_fully_read"] is True
    assert outputs["trace_summary"]["eval_suite_read"] is True
    assert outputs["trace_summary"]["decomposition_persisted"] is True
    assert outputs["trace_summary"]["sub_agents_parallel"] is True
    assert outputs["skill_interactions"]
    assert outputs["citation_urls"] == ["https://docs.example.com/guide", "https://docs.example.com/guide"]
    assert outputs["citation_claim_support"][0]["supported"] is True
    assert os.path.isfile(os.path.join(project_dir, ".agents", "research-agent", "AGENTS.md"))


def test_parse_verification_verdict():
    verdict = parse_verification_verdict(
        """```json
{"artifact_type":"research_bundle","source_path":"artifacts/research/research-bundle.md","status":"needs_revision","coverage_summary":"missing one area","gaps":["gap-a"],"recommended_action":"revise"}
```"""
    )
    assert verdict["status"] == "needs_revision"
    assert verdict["gaps"] == ["gap-a"]


def test_research_stage_exit_conditions(tmp_path):
    stage = ResearchStage(str(tmp_path), "demo")
    _write(stage.decomposition_path, "decomposition")
    _write(stage.research_bundle_path, "bundle")
    state = {
        "current_research_path": stage.research_bundle_path,
        "approval_history": [{"artifact": stage.research_bundle_path, "action": "approved"}],
        "verification_results": {"research_bundle": {"status": "pass"}},
    }
    result = stage.check_exit_conditions(state)
    assert result["met"] is True


def test_spec_generation_stage_exit_conditions(tmp_path):
    stage = SpecGenerationStage(str(tmp_path), "demo")
    _write(stage.prd_path, "prd")
    _write(stage.research_bundle_path, "bundle")
    _write(stage.spec_path, "spec")
    _write(stage.arch_eval_suite_path, json.dumps({"metadata": {}, "evals": []}))
    state = {
        "current_spec_path": stage.spec_path,
        "eval_suites": [stage.arch_eval_suite_path],
        "verification_results": {"technical_specification": {"status": "pass"}},
    }
    result = stage.check_exit_conditions(state)
    assert result["met"] is True


def test_spec_review_stage_exit_conditions(tmp_path):
    stage = SpecReviewStage(str(tmp_path), "demo")
    _write(stage.spec_path, "spec")
    _write(stage.arch_eval_suite_path, json.dumps({"metadata": {}, "evals": []}))
    state = {
        "approval_history": [
            {"artifact": stage.spec_path, "action": "approved"},
            {"artifact": stage.arch_eval_suite_path, "action": "approved"},
        ]
    }
    result = stage.check_exit_conditions(state)
    assert result["met"] is True
