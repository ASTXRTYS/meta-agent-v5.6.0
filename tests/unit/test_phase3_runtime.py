"""Unit tests for Phase 3 runtime helpers and stage gates."""

from __future__ import annotations

import json
import os

import pytest

from meta_agent.stages import ResearchStage, SpecGenerationStage, SpecReviewStage
from meta_agent.subagents.research_agent import (
    get_research_runtime_paths,
    normalize_research_outputs,
)
from meta_agent.subagents.verification_agent import parse_verification_verdict
from meta_agent.subagents.verification_agent_runtime import normalize_verification_outputs
from meta_agent.subagents.spec_writer_agent import (
    _extract_status_block,
    normalize_spec_writer_outputs,
    get_spec_writer_runtime_paths,
)
from meta_agent.evals.phase3_gate import (
    eval_research_001,
    eval_research_002,
    eval_research_003,
    eval_spec_001,
    eval_spec_002,
    eval_spec_003,
    eval_spec_004,
    RESEARCH_BUNDLE_REQUIRED_SECTIONS,
    SPEC_REQUIRED_SECTIONS,
)


pytestmark = pytest.mark.legacy


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
    _write(stage.research_clusters_path, "clusters")
    _write(stage.research_bundle_path, (
        "# Research Bundle\n\n"
        "## PRD Coverage Matrix\n\ncoverage here\n\n"
        "## Unresolved Research Gaps\n\ngaps here\n\n"
        "## Citation Index\n\ncitations here\n"
    ))
    _write(stage.agents_md_path, "# research-agent memory")
    os.makedirs(stage.sub_findings_dir, exist_ok=True)
    _write(os.path.join(stage.sub_findings_dir, "finding-1.md"), "finding")
    state = {
        "current_research_path": stage.research_bundle_path,
        "approval_history": [
            {"artifact": stage.research_clusters_path, "action": "approved"},
            {"artifact": stage.research_bundle_path, "action": "approved"},
        ],
        "verification_results": {"research_bundle": {"status": "pass"}},
    }
    result = stage.check_exit_conditions(state)
    assert result["met"] is True


def test_spec_generation_stage_exit_conditions(tmp_path):
    stage = SpecGenerationStage(str(tmp_path), "demo")
    _write(stage.prd_path, "prd")
    _write(stage.research_bundle_path, "bundle")
    _write(stage.spec_path, "spec")
    _write(stage.tier1_eval_suite_path, json.dumps({"metadata": {"tier": 1}, "evals": []}))
    _write(stage.arch_eval_suite_path, json.dumps({
        "metadata": {"artifact": "eval-suite-architecture", "tier": 2, "created_by": "spec-writer"},
        "evals": [],
    }))
    state = {
        "current_spec_path": stage.spec_path,
        "eval_suites": [stage.tier1_eval_suite_path, stage.arch_eval_suite_path],
        "verification_results": {"technical_specification": {"status": "pass"}},
        "spec_generation_feedback_cycles": 0,
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


# ---------------------------------------------------------------------------
# Verification-agent runtime normalization
# ---------------------------------------------------------------------------


def test_verification_agent_normalize_outputs_valid_verdict(tmp_path):
    """normalize_verification_outputs extracts a valid JSON verdict from messages."""
    verdict_json = json.dumps({
        "artifact_type": "research_bundle",
        "source_path": "artifacts/intake/prd.md",
        "status": "pass",
        "coverage_summary": "All areas covered",
        "gaps": [],
        "recommended_action": "none",
    })
    raw_result = {
        "messages": [
            {"content": "Analyzing the research bundle..."},
            {"content": f"```json\n{verdict_json}\n```"},
        ],
    }
    outputs = normalize_verification_outputs(
        raw_result,
        project_dir=str(tmp_path),
        project_id="demo",
    )
    assert outputs["status"] == "pass"
    assert outputs["artifact_type"] == "research_bundle"
    assert outputs["source_path"] == "artifacts/intake/prd.md"
    assert outputs["coverage_summary"] == "All areas covered"
    assert outputs["gaps"] == []
    assert outputs["recommended_action"] == "none"
    assert "raw_result" in outputs


def test_verification_agent_normalize_outputs_no_verdict(tmp_path):
    """normalize_verification_outputs falls back to blocked when no parseable verdict."""
    raw_result = {
        "messages": [
            {"content": "I could not complete verification."},
        ],
    }
    outputs = normalize_verification_outputs(
        raw_result,
        project_dir=str(tmp_path),
        project_id="demo",
    )
    assert outputs["status"] == "blocked"
    assert outputs["artifact_type"] == "unknown"
    assert len(outputs["gaps"]) > 0


# ---------------------------------------------------------------------------
# Spec-writer normalization
# ---------------------------------------------------------------------------


def test_spec_writer_normalize_outputs_complete(tmp_path):
    """normalize_spec_writer_outputs detects 'complete' status from fenced JSON."""
    project_dir = str(tmp_path)
    paths = get_spec_writer_runtime_paths(project_dir, "demo")

    # Create the artifacts the normalizer will read
    _write(paths.spec_path, "# Technical Specification\ncontent here")
    _write(paths.tier2_eval_suite_path, json.dumps({"evals": []}))

    status_block = json.dumps({"status": "complete"})
    raw_result = {
        "messages": [
            {"type": "ai", "content": f"Here is the spec.\n\n```json\n{status_block}\n```"},
        ],
    }
    outputs = normalize_spec_writer_outputs(
        raw_result,
        project_dir=project_dir,
        project_id="demo",
    )
    assert outputs["status"] == "complete"
    assert outputs["needs_additional_research"] is False
    assert outputs["spec_path"] == paths.spec_path
    assert outputs["tier2_eval_suite_path"] == paths.tier2_eval_suite_path
    # Agent memory file should be written
    assert os.path.isfile(paths.agents_md_path)


def test_spec_writer_normalize_outputs_needs_research(tmp_path):
    """normalize_spec_writer_outputs detects 'needs_additional_research' status."""
    project_dir = str(tmp_path)
    paths = get_spec_writer_runtime_paths(project_dir, "demo")

    _write(paths.spec_path, "# Partial spec")

    status_block = json.dumps({
        "status": "needs_additional_research",
        "needs_additional_research": True,
        "additional_research_request": "Need more info on auth flows",
    })
    raw_result = {
        "messages": [
            {"type": "ai", "content": f"```json\n{status_block}\n```"},
        ],
    }
    outputs = normalize_spec_writer_outputs(
        raw_result,
        project_dir=project_dir,
        project_id="demo",
    )
    assert outputs["status"] == "needs_additional_research"
    assert outputs["needs_additional_research"] is True
    assert outputs["additional_research_request"] == "Need more info on auth flows"


def test_spec_writer_normalize_outputs_missing_status(tmp_path):
    """normalize_spec_writer_outputs handles missing status block gracefully."""
    project_dir = str(tmp_path)
    paths = get_spec_writer_runtime_paths(project_dir, "demo")

    _write(paths.spec_path, "# Spec content")

    raw_result = {
        "messages": [
            {"type": "ai", "content": "Here is the specification. No JSON status block."},
        ],
    }
    outputs = normalize_spec_writer_outputs(
        raw_result,
        project_dir=project_dir,
        project_id="demo",
    )
    # With no status block, status defaults to "complete" (not needs_research)
    assert outputs["status"] == "complete"
    assert outputs["needs_additional_research"] is False
    # Agent memory file should still be created
    assert os.path.isfile(paths.agents_md_path)


# ---------------------------------------------------------------------------
# Phase 3 gate evals — binary
# ---------------------------------------------------------------------------


def test_phase3_gate_evals_binary_research_001(tmp_path):
    """RESEARCH-001: passes when bundle exists, fails when missing."""
    project_dir = str(tmp_path)

    # Fail case: no bundle
    result = eval_research_001(project_dir)
    assert result["pass"] is False
    assert result["score"] == 0.0

    # Pass case: bundle exists
    bundle_path = os.path.join(project_dir, "artifacts", "research", "research-bundle.md")
    _write(bundle_path, "# Research Bundle\n")
    result = eval_research_001(project_dir)
    assert result["pass"] is True
    assert result["score"] == 1.0


def test_phase3_gate_evals_binary_research_002(tmp_path):
    """RESEARCH-002: passes when bundle has PRD Coverage Matrix heading."""
    project_dir = str(tmp_path)
    bundle_path = os.path.join(project_dir, "artifacts", "research", "research-bundle.md")

    # Fail case: bundle without the heading
    _write(bundle_path, "# Research Bundle\n\n## Some Other Section\ncontent\n")
    result = eval_research_002(project_dir)
    assert result["pass"] is False
    assert result["score"] == 0.0

    # Pass case: bundle with the heading
    _write(bundle_path, "# Research Bundle\n\n## PRD Coverage Matrix\ncoverage content\n")
    result = eval_research_002(project_dir)
    assert result["pass"] is True
    assert result["score"] == 1.0


def test_phase3_gate_evals_binary_spec_001(tmp_path):
    """SPEC-001: passes when spec exists, fails when missing."""
    project_dir = str(tmp_path)

    # Fail case
    result = eval_spec_001(project_dir)
    assert result["pass"] is False
    assert result["score"] == 0.0

    # Pass case
    spec_path = os.path.join(project_dir, "artifacts", "spec", "technical-specification.md")
    _write(spec_path, "# Technical Specification\n")
    result = eval_spec_001(project_dir)
    assert result["pass"] is True
    assert result["score"] == 1.0


def test_phase3_gate_evals_binary_spec_002(tmp_path):
    """SPEC-002: passes when spec has PRD Traceability Matrix with 100% coverage text."""
    project_dir = str(tmp_path)
    spec_path = os.path.join(project_dir, "artifacts", "spec", "technical-specification.md")

    # Fail case: no traceability matrix heading
    _write(spec_path, "# Technical Specification\n\n## Architecture\ncontent\n")
    result = eval_spec_002(project_dir)
    assert result["pass"] is False

    # Fail case: heading present but no 100% coverage assertion
    _write(spec_path, (
        "# Technical Specification\n\n"
        "## PRD Traceability Matrix\n\nPartial coverage only.\n"
    ))
    result = eval_spec_002(project_dir)
    assert result["pass"] is False

    # Pass case: heading + 100% coverage assertion
    _write(spec_path, (
        "# Technical Specification\n\n"
        "## PRD Traceability Matrix\n\nAll requirements mapped. 100% coverage achieved.\n"
    ))
    result = eval_spec_002(project_dir)
    assert result["pass"] is True
    assert result["score"] == 1.0


def test_phase3_gate_evals_binary_spec_003(tmp_path):
    """SPEC-003: passes when eval-suite-architecture.json exists and is valid JSON."""
    project_dir = str(tmp_path)
    eval_path = os.path.join(project_dir, "evals", "eval-suite-architecture.json")

    # Fail case: file missing
    result = eval_spec_003(project_dir)
    assert result["pass"] is False
    assert result["score"] == 0.0

    # Fail case: file exists but invalid JSON
    _write(eval_path, "not valid json {{{")
    result = eval_spec_003(project_dir)
    assert result["pass"] is False
    assert result["score"] == 0.0

    # Pass case: valid JSON
    _write(eval_path, json.dumps({"metadata": {"tier": 2}, "evals": []}))
    result = eval_spec_003(project_dir)
    assert result["pass"] is True
    assert result["score"] == 1.0


# ---------------------------------------------------------------------------
# Phase 3 gate evals — Likert
# ---------------------------------------------------------------------------


def test_phase3_gate_evals_likert_research_003(tmp_path):
    """RESEARCH-003: score=5 when all 17 sections + 3 PRD req IDs present."""
    project_dir = str(tmp_path)
    bundle_path = os.path.join(project_dir, "artifacts", "research", "research-bundle.md")

    # Build a bundle with all 17 required sections and 3 PRD requirement IDs
    sections = "\n\n".join(
        f"## {section}\ncontent for {section}" for section in RESEARCH_BUNDLE_REQUIRED_SECTIONS
    )
    prd_refs = "\nFR-A FR-B FR-C\n"
    _write(bundle_path, f"# Research Bundle\n\n{sections}\n{prd_refs}\n")

    result = eval_research_003(project_dir)
    assert result["score"] == 5.0
    assert result["pass"] is True


def test_phase3_gate_evals_likert_spec_004(tmp_path):
    """SPEC-004: score=5 when all 17 sections + YAML frontmatter present."""
    project_dir = str(tmp_path)
    spec_path = os.path.join(project_dir, "artifacts", "spec", "technical-specification.md")

    # Build a spec with YAML frontmatter and all required sections
    frontmatter = "---\nartifact: technical-specification\nversion: 1.0.0\n---\n\n"
    sections = "\n\n".join(
        f"## {section}\ncontent for {section}" for section in SPEC_REQUIRED_SECTIONS
    )
    _write(spec_path, f"{frontmatter}# Technical Specification\n\n{sections}\n")

    result = eval_spec_004(project_dir)
    assert result["score"] == 5.0
    assert result["pass"] is True


# ---------------------------------------------------------------------------
# _extract_status_block helper
# ---------------------------------------------------------------------------


def test_spec_writer_extract_status_block_fenced_json():
    """_extract_status_block extracts JSON from a ```json ... ``` block."""
    text = 'Some preamble.\n\n```json\n{"status": "complete", "notes": "all done"}\n```\n\nEpilogue.'
    result = _extract_status_block(text)
    assert result["status"] == "complete"
    assert result["notes"] == "all done"


def test_spec_writer_extract_status_block_bare_fence():
    """_extract_status_block extracts JSON from a bare ``` ... ``` block."""
    text = 'Preamble.\n\n```\n{"status": "needs_additional_research"}\n```\n'
    result = _extract_status_block(text)
    assert result["status"] == "needs_additional_research"


def test_spec_writer_extract_status_block_none():
    """_extract_status_block returns empty dict when no status block found."""
    text = "There is no JSON here at all. Just plain prose."
    result = _extract_status_block(text)
    assert result == {}


def test_run_research_agent_live_injects_auto_approve_hitl():
    """run_research_agent_live() must inject auto_approve_hitl=True via extra_state."""
    from unittest.mock import patch, MagicMock

    from meta_agent.subagents.research_agent import run_research_agent_live

    captured_kwargs = {}

    def _capture_run(**kwargs):
        captured_kwargs.update(kwargs)
        return {"messages": []}

    with patch("meta_agent.subagents.research_agent.run_research_agent", side_effect=_capture_run):
        try:
            run_research_agent_live({"project_id": "test", "project_dir": "/tmp/test"})
        except Exception:
            pass  # normalization may fail on empty result; we only need the captured call

    assert "extra_state" in captured_kwargs
    assert captured_kwargs["extra_state"].get("auto_approve_hitl") is True


def test_run_research_agent_live_preserves_caller_extra_state():
    """run_research_agent_live() must preserve caller-provided extra_state keys."""
    from unittest.mock import patch

    from meta_agent.subagents.research_agent import run_research_agent_live

    captured_kwargs = {}

    def _capture_run(**kwargs):
        captured_kwargs.update(kwargs)
        return {"messages": []}

    inputs = {
        "project_id": "test",
        "project_dir": "/tmp/test",
        "extra_state": {"custom_key": "custom_value"},
    }

    with patch("meta_agent.subagents.research_agent.run_research_agent", side_effect=_capture_run):
        try:
            run_research_agent_live(inputs)
        except Exception:
            pass

    assert captured_kwargs["extra_state"]["auto_approve_hitl"] is True
    assert captured_kwargs["extra_state"]["custom_key"] == "custom_value"



# ---------------------------------------------------------------------------
# CRITICAL-2: Server-side tools validation
# ---------------------------------------------------------------------------

class TestServerSideToolsValidation:
    """Validate SERVER_SIDE_TOOLS dict uses _20260209 versions (CRITICAL-2)."""

    def test_server_side_tools_use_20260209(self):
        from meta_agent.tools import SERVER_SIDE_TOOLS
        assert SERVER_SIDE_TOOLS["web_search"]["type"] == "web_search_20260209"
        assert SERVER_SIDE_TOOLS["web_fetch"]["type"] == "web_fetch_20260209"

    def test_get_server_side_tools_returns_list_of_dicts(self):
        from meta_agent.tools import get_server_side_tools
        tools = get_server_side_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2
        for t in tools:
            assert isinstance(t, dict)
            assert "type" in t
            assert "name" in t

    def test_server_side_tools_names(self):
        from meta_agent.tools import get_server_side_tools
        tools = get_server_side_tools()
        names = {t["name"] for t in tools}
        assert names == {"web_search", "web_fetch"}


# ---------------------------------------------------------------------------
# CRITICAL-3: AgentDecisionStateMiddleware tests
# ---------------------------------------------------------------------------

class TestAgentDecisionStateMiddleware:
    """Tests for AgentDecisionStateMiddleware (CRITICAL-3)."""

    def test_middleware_creates(self):
        from meta_agent.middleware.agent_decision_state import AgentDecisionStateMiddleware
        mw = AgentDecisionStateMiddleware()
        assert mw is not None

    def test_state_schema_has_decision_log(self):
        from meta_agent.middleware.agent_decision_state import AgentDecisionStateSchema
        assert "decision_log" in AgentDecisionStateSchema.__annotations__

    def test_state_schema_has_assumption_log(self):
        from meta_agent.middleware.agent_decision_state import AgentDecisionStateSchema
        assert "assumption_log" in AgentDecisionStateSchema.__annotations__

    def test_state_schema_has_approval_history(self):
        from meta_agent.middleware.agent_decision_state import AgentDecisionStateSchema
        assert "approval_history" in AgentDecisionStateSchema.__annotations__

    def test_middleware_exports_from_package(self):
        from meta_agent.middleware import AgentDecisionStateMiddleware
        mw = AgentDecisionStateMiddleware()
        assert hasattr(mw, "state_schema")

    def test_configs_include_middleware_for_research(self):
        from meta_agent.subagents.configs import SUBAGENT_MIDDLEWARE
        assert "AgentDecisionStateMiddleware" in SUBAGENT_MIDDLEWARE["research-agent"]

    def test_configs_include_middleware_for_verification(self):
        from meta_agent.subagents.configs import SUBAGENT_MIDDLEWARE
        assert "AgentDecisionStateMiddleware" in SUBAGENT_MIDDLEWARE["verification-agent"]

    def test_resolve_middleware_instances_includes_decision_state(self):
        from meta_agent.subagents.configs import _resolve_middleware_instances
        instances = _resolve_middleware_instances()
        assert "AgentDecisionStateMiddleware" in instances
