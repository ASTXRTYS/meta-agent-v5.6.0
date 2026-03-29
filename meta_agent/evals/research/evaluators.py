"""Canonical research-agent evaluator registry and hybrid wrappers."""

from __future__ import annotations

import json
from typing import Any

from meta_agent.evals.research.common import (
    extract_markdown_section,
    extract_functional_requirements,
    format_fr_checklist,
    make_result,
    validate_registry_ids,
)
from meta_agent.evals.research.deterministic import (
    eval_rinfra_001,
    eval_rinfra_002,
    eval_rs_001,
    eval_rs_002,
    eval_rs_003,
    eval_rs_004,
    eval_rb_001,
    eval_rb_002,
    eval_rb_003,
    eval_rb_004,
    eval_rb_005_precheck,
    eval_rb_006,
    eval_rb_007,
    eval_rb_008,
    eval_rb_009 as eval_rb_009_deterministic,
    eval_rb_010 as eval_rb_010_deterministic,
    eval_rb_011 as eval_rb_011_deterministic,
    eval_ri_001,
)
from meta_agent.evals.research.judge_infra import (
    _get_outputs,
    run_binary_judge,
    run_likert_judge,
)
from meta_agent.evals.research.rubrics import (
    RESEARCH_EVAL_RUBRICS,
    get_anchors,
    get_eval_meta,
)


def _get_inputs(example: Any) -> dict:
    return example.inputs if hasattr(example, "inputs") else example.get("inputs", {}) or {}


def _get_anchors(eval_id: str) -> dict:
    rubric = RESEARCH_EVAL_RUBRICS.get(eval_id)
    if rubric and rubric.get("anchors"):
        return rubric["anchors"]
    return get_anchors(eval_id)


def _get_instructions(eval_id: str) -> str:
    rubric = RESEARCH_EVAL_RUBRICS.get(eval_id)
    if rubric and rubric.get("specific_instructions"):
        return rubric["specific_instructions"]
    meta = get_eval_meta(eval_id)
    return meta.get("description", "")


def _bundle_content(run: Any) -> str:
    return _get_outputs(run).get("research_bundle_content", "")


def _decomposition_content(run: Any) -> str:
    return _get_outputs(run).get("decomposition_content", "")


def _skill_interactions_text(run: Any) -> str:
    sis = _get_outputs(run).get("skill_interactions", [])
    if not sis:
        return "(No skill interactions recorded)"
    parts = []
    for si in sis:
        parts.append(
            f"Skill: {si.get('skill', 'unknown')}\n"
            f"Domain: {si.get('domain', '')}\n"
            f"Trigger reasoning: {si.get('trigger_reasoning', '')}\n"
            f"Reflection: {si.get('reflection', '')}\n"
            f"Internalization: {si.get('internalization', '')}\n"
            f"Guides next: {si.get('guides_next_action', '')}\n"
        )
    return "\n---\n".join(parts)


def _trace_summary_text(run: Any) -> str:
    trace = _get_outputs(run).get("trace_summary", {})
    tool_calls = trace.get("tool_calls", [])
    lines = [f"Total tool calls: {trace.get('total_tool_calls', len(tool_calls))}"]
    for tc in tool_calls[:80]:
        args_str = json.dumps(tc.get("args", {}), default=str)[:120]
        lines.append(f"  [{tc.get('timestamp', '?')}] {tc.get('name', '?')}({args_str})")
    return "\n".join(lines)


def _hitl_content(run: Any) -> str:
    return _get_outputs(run).get("hitl_cluster_content", "(No HITL cluster)")


def _fr_checklist_text(example: Any) -> str:
    prd_text = _get_inputs(example).get("prd_content")
    return format_fr_checklist(prd_text)


def _verification_context(run: Any) -> str:
    outputs = _get_outputs(run)
    support = outputs.get("citation_claim_support", [])
    if not support:
        return "No structured citation verification records provided."
    return "Citation verification records:\n" + json.dumps(support[:10], indent=2, default=str)


def _join_sections(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if isinstance(part, str) and part.strip())


def _delegation_content(run: Any) -> str:
    outputs = _get_outputs(run)
    return _join_sections(
        outputs.get("delegation_context", ""),
        _delegation_text(run),
    )


def _gap_remediation_content(run: Any) -> str:
    bundle = _bundle_content(run)
    outputs = _get_outputs(run)
    return _join_sections(
        outputs.get("gap_remediation_context", ""),
        extract_markdown_section(bundle, "## 12. Risks & Caveats for Spec-Writer"),
        extract_markdown_section(bundle, "### Unresolved Questions for Spec-Writer", level=3),
    )


def _evaluation_implications_content(run: Any) -> str:
    bundle = _bundle_content(run)
    outputs = _get_outputs(run)
    return _join_sections(
        extract_markdown_section(bundle, "## 6. Evaluation & Observability"),
        outputs.get("delegation_context", ""),
        _trace_summary_text(run),
    )


def _fr_coverage_details(run: Any, example: Any) -> dict[str, dict[str, Any]]:
    outputs = _get_outputs(run)
    inputs = _get_inputs(example)
    trace = outputs.get("trace_summary", {})
    bundle = _bundle_content(run)
    bundle_lower = bundle.lower()
    decomposition = _decomposition_content(run)
    skills = outputs.get("skill_interactions", [])
    hitl = _hitl_content(run)
    delegation = _delegation_content(run)
    gap_text = _gap_remediation_content(run)
    cited_urls = outputs.get("citation_urls") or []

    def _signal(met: bool, summary: str) -> dict[str, Any]:
        return {"met": met, "summary": summary}

    details = {
        "FR-A": _signal(
            bool(trace.get("prd_fully_read"))
            and bool(trace.get("eval_suite_read") or inputs.get("eval_suite_content")),
            "PRD and eval suite consumption evidenced in trace/state",
        ),
        "FR-B": _signal(
            bool(decomposition)
            and ("line " in decomposition.lower() or "prd" in decomposition.lower()),
            "Research decomposition artifact present with PRD-linked detail",
        ),
        "FR-C": _signal(
            bool(skills) or int(trace.get("skills_read") or 0) > 0,
            "Skills usage evidenced in trace or skill interaction records",
        ),
        "FR-D": _signal(
            int(trace.get("task_calls") or 0) > 0 and bool(delegation),
            "Sub-agent delegation evidenced in trace and Stage 4 planning",
        ),
        "FR-E": _signal(
            any(handle in bundle for handle in ("@hwchase17", "@Vtrivedy10", "@sydneyrunkle", "@masondrxy", "@BraceSproul", "@RLanceMartin"))
            or "sme" in bundle_lower,
            "SME consultation evidenced in bundle content",
        ),
        "FR-F": _signal(
            "anthropic" in bundle_lower or "claude opus" in bundle_lower or int(trace.get("web_fetches") or 0) > 0 and "anthropic" in _trace_summary_text(run).lower(),
            "Anthropic model research evidenced in bundle or trace",
        ),
        "FR-G": _signal(
            bool(cited_urls),
            "Citation/source tracking evidenced by cited URLs in bundle",
        ),
        "FR-H": _signal(
            bool(gap_text),
            "Gap/contradiction remediation evidenced by Stage 4 analysis or bundle caveats",
        ),
        "FR-I": _signal(
            bool(hitl.strip()) and int(trace.get("hitl_approvals") or 0) > 0,
            "HITL cluster artifact and approval trace both present",
        ),
        "FR-J": _signal(
            bool(bundle.strip()),
            "Research bundle artifact present",
        ),
        "FR-K": _signal(
            "spec-writer" in bundle_lower
            and any(keyword in bundle_lower for keyword in ("additional research", "feedback loop", "unresolved questions", "sufficiency gate")),
            "Spec-writer feedback loop evidenced in bundle",
        ),
    }
    return details


REQUIRED_SECTIONS = [
    "Executive Summary",
    "Orchestration",
    "State Management",
    "Human-in-the-Loop",
    "Tool System",
    "Prompt",
    "Model Capabilities",
    "Evaluation",
    "Safety",
    "Rejected Alternatives",
    "Risks",
    "Unresolved Questions",
]


async def eval_rinfra_003(run: Any, example: Any) -> dict:
    content = _bundle_content(run)
    if not content:
        return make_result(1, "RINFRA-003: no bundle content", flags=["missing_bundle"])
    content_lower = content.lower()
    found = [section for section in REQUIRED_SECTIONS if section.lower() in content_lower]
    if len(found) < 4:
        return make_result(
            1 if not found else 2,
            f"RINFRA-003: only {len(found)}/{len(REQUIRED_SECTIONS)} sections found",
            evidence=found,
            flags=["missing_required_sections"],
        )
    return await run_likert_judge(
        eval_id="RINFRA-003",
        eval_name="Research bundle schema completeness and quality",
        anchors=_get_anchors("RINFRA-003"),
        specific_instructions=_get_instructions("RINFRA-003")
        + f"\nPre-check: {len(found)}/{len(REQUIRED_SECTIONS)} sections found. Missing: {sorted(set(REQUIRED_SECTIONS) - set(found))}",
        agent_output=content,
    )


async def eval_rinfra_004(run: Any, example: Any) -> dict:
    content = _bundle_content(run)
    if not content:
        return make_result(1, "RINFRA-004: no bundle content", flags=["missing_bundle"])
    urls = _get_outputs(run).get("citation_urls")
    if not isinstance(urls, list):
        from meta_agent.evals.research.common import extract_urls

        urls = extract_urls(content)
    if not urls:
        return make_result(1, "RINFRA-004: zero URLs found in bundle", flags=["missing_citations"])
    return await run_likert_judge(
        eval_id="RINFRA-004",
        eval_name="Citation quality across all findings",
        anchors=_get_anchors("RINFRA-004"),
        specific_instructions=_get_instructions("RINFRA-004")
        + f"\nPre-check: {len(urls)} URLs found in bundle.",
        agent_output=content,
    )


async def eval_rb_005(run: Any, example: Any) -> dict:
    precheck = eval_rb_005_precheck(run, example)
    if precheck["no_citations"]:
        return make_result(
            0,
            "RB-005: bundle contains no citations",
            evidence=[],
            flags=["missing_citations"],
            details=precheck,
        )
    if precheck["missing_urls"]:
        return make_result(
            0,
            f"RB-005: {len(precheck['missing_urls'])} cited URLs were never fetched",
            evidence=precheck["missing_urls"][:5],
            flags=["missing_trace_fetch"],
            details=precheck,
        )
    if precheck["unsupported_claims"]:
        evidence = [
            str(claim.get("claim", claim))[:200] for claim in precheck["unsupported_claims"][:5]
        ]
        return make_result(
            0,
            f"RB-005: {len(precheck['unsupported_claims'])} citation-backed claims are unsupported",
            evidence=evidence,
            flags=["unsupported_claims"],
            details=precheck,
        )
    if precheck["has_verification"]:
        return make_result(
            1,
            "RB-005: citations were fetched and structured claim checks found no unsupported claims",
            evidence=precheck["cited_urls"][:5],
            details=precheck,
        )
    judge_result = await run_binary_judge(
        eval_id="RB-005",
        eval_name="Citation integrity and content verification",
        pass_criteria=(
            "Every URL cited in the research bundle was actually fetched by the agent and the bundle's cited claims are plausibly faithful to those fetched sources."
        ),
        trace_data=_trace_summary_text(run),
        additional_context=f"RESEARCH BUNDLE:\n{_bundle_content(run)[:6000]}\n\n{_verification_context(run)}",
    )
    judge_result["details"] = {**precheck, **judge_result.get("details", {})}
    return judge_result


async def eval_rb_009(run: Any, example: Any) -> dict:
    deterministic = eval_rb_009_deterministic(run, example)
    if deterministic["score"] != -1:
        return deterministic
    judge_result = await run_binary_judge(
        eval_id="RB-009",
        eval_name="Sub-agents execute in parallel",
        pass_criteria="Multiple sub-agent tasks overlap in execution or the trace otherwise clearly indicates true parallel execution.",
        trace_data=_trace_summary_text(run),
    )
    judge_result["details"] = {"fallback": "llm_binary", **judge_result.get("details", {})}
    return judge_result


async def eval_rb_010(run: Any, example: Any) -> dict:
    deterministic = eval_rb_010_deterministic(run, example)
    if deterministic["score"] != -1:
        return deterministic
    judge_result = await run_binary_judge(
        eval_id="RB-010",
        eval_name="Main agent aggregates sub-agent findings after completion",
        pass_criteria="The main agent reads sub-agent outputs after those sub-agents finish and uses them as synthesis input.",
        trace_data=_trace_summary_text(run),
        additional_context=f"RESEARCH BUNDLE:\n{_bundle_content(run)[:4000]}",
    )
    judge_result["details"] = {"fallback": "llm_binary", **judge_result.get("details", {})}
    return judge_result


async def eval_rb_011(run: Any, example: Any) -> dict:
    deterministic = eval_rb_011_deterministic(run, example)
    if deterministic["score"] != -1:
        return deterministic
    judge_result = await run_binary_judge(
        eval_id="RB-011",
        eval_name="HITL gate fires before deep-dive research",
        pass_criteria="An HITL approval or interrupt occurs before the agent performs deep-dive verification research.",
        trace_data=_trace_summary_text(run),
        additional_context=f"HITL cluster content:\n{_hitl_content(run)[:3000]}",
    )
    judge_result["details"] = {"fallback": "llm_binary", **judge_result.get("details", {})}
    return judge_result


async def eval_rq_001(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-001",
        eval_name="PRD decomposition quality",
        anchors=_get_anchors("RQ-001"),
        specific_instructions=_get_instructions("RQ-001"),
        agent_output=_decomposition_content(run),
    )


async def eval_rq_002(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-002",
        eval_name="Research breadth",
        anchors=_get_anchors("RQ-002"),
        specific_instructions=_get_instructions("RQ-002"),
        agent_output=_bundle_content(run),
    )


async def eval_rq_003(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-003",
        eval_name="Research depth",
        anchors=_get_anchors("RQ-003"),
        specific_instructions=_get_instructions("RQ-003"),
        agent_output=_bundle_content(run) + "\n\nTRACE:\n" + _trace_summary_text(run),
    )


async def eval_rq_004(run: Any, example: Any) -> dict:
    precheck = eval_rb_005_precheck(run, example)
    if precheck["no_citations"]:
        return make_result(1, "RQ-004: no citations available to verify", flags=["missing_citations"], details=precheck)
    if precheck["missing_urls"]:
        return make_result(
            2,
            "RQ-004: citations reference URLs that were not fetched",
            evidence=precheck["missing_urls"][:5],
            flags=["missing_trace_fetch"],
            details=precheck,
        )
    if precheck["unsupported_claims"]:
        return make_result(
            2,
            "RQ-004: citation-backed claims include unsupported content",
            evidence=[str(claim.get("claim", claim))[:200] for claim in precheck["unsupported_claims"][:5]],
            flags=["unsupported_claims"],
            details=precheck,
        )
    result = await run_likert_judge(
        eval_id="RQ-004",
        eval_name="Citation accuracy (content verified)",
        anchors=_get_anchors("RQ-004"),
        specific_instructions=_get_instructions("RQ-004")
        + f"\nVerification context:\n{_verification_context(run)}",
        agent_output=_bundle_content(run),
    )
    if not precheck["has_verification"] and result["score"] > 3:
        result["score"] = 3
        result["comment"] = "RQ-004: score capped at 3 because structured citation verification is missing"
        result["reasoning"] = result["comment"]
        result["flags"] = list(result.get("flags", [])) + ["verification_missing_cap"]
    result["details"] = {**precheck, **result.get("details", {})}
    return result


async def eval_rq_005(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-005",
        eval_name="Research bundle utility for spec-writer",
        anchors=_get_anchors("RQ-005"),
        specific_instructions=_get_instructions("RQ-005"),
        agent_output=_bundle_content(run),
    )


async def eval_rq_006(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-006",
        eval_name="Twitter/SME consultation quality",
        anchors=_get_anchors("RQ-006"),
        specific_instructions=_get_instructions("RQ-006"),
        agent_output=_bundle_content(run) + "\n\nTRACE:\n" + _trace_summary_text(run),
    )


async def eval_rq_007(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-007",
        eval_name="Skill trigger relevance and timing",
        anchors=_get_anchors("RQ-007"),
        specific_instructions=_get_instructions("RQ-007"),
        agent_output=_skill_interactions_text(run) + "\n\nTRACE:\n" + _trace_summary_text(run),
    )


async def eval_rq_008(run: Any, example: Any) -> dict:
    outputs = _get_outputs(run)
    sis = outputs.get("skill_interactions", [])
    if not sis:
        return make_result(1, "RQ-008: no skill interactions recorded", flags=["missing_skill_interactions"])
    return await run_likert_judge(
        eval_id="RQ-008",
        eval_name="Skill reflection and internalization quality",
        anchors=_get_anchors("RQ-008"),
        specific_instructions=_get_instructions("RQ-008"),
        agent_output=_skill_interactions_text(run),
    )


async def eval_rq_009(run: Any, example: Any) -> dict:
    outputs = _get_outputs(run)
    sis = outputs.get("skill_interactions", [])
    if not sis:
        return make_result(1, "RQ-009: no skill interactions recorded", flags=["missing_skill_interactions"])
    return await run_likert_judge(
        eval_id="RQ-009",
        eval_name="Skill-to-research-decision influence",
        anchors=_get_anchors("RQ-009"),
        specific_instructions=_get_instructions("RQ-009"),
        agent_output=_skill_interactions_text(run) + "\n\nBUNDLE:\n" + _bundle_content(run)[:4000],
    )


def _delegation_text(run: Any) -> str:
    outputs = _get_outputs(run)
    parts = []
    for si in outputs.get("skill_interactions", []):
        reflection = str(si.get("reflection", ""))
        if "delegat" in reflection.lower() or "sub-agent" in reflection.lower():
            parts.append(f"Reflection: {reflection}")
    task_calls = [tc for tc in outputs.get("trace_summary", {}).get("tool_calls", []) if tc.get("name") == "task"]
    parts.append(f"\nSub-agents spawned: {len(task_calls)}")
    for tc in task_calls:
        parts.append(f"  Task: {json.dumps(tc.get('args', {}), default=str)[:300]}")
    parts.append(f"\nFull trace summary:\n{_trace_summary_text(run)}")
    return "\n".join(parts)


async def eval_rq_010(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-010",
        eval_name="Sub-agent task delegation quality",
        anchors=_get_anchors("RQ-010"),
        specific_instructions=_get_instructions("RQ-010"),
        agent_output=_delegation_content(run),
    )


async def eval_rq_011(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-011",
        eval_name="Research findings synthesis quality",
        anchors=_get_anchors("RQ-011"),
        specific_instructions=_get_instructions("RQ-011"),
        agent_output=_bundle_content(run),
    )


async def eval_rq_012(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RQ-012",
        eval_name="HITL research cluster quality",
        anchors=_get_anchors("RQ-012"),
        specific_instructions=_get_instructions("RQ-012"),
        agent_output=_hitl_content(run),
    )


async def eval_rq_013(run: Any, example: Any) -> dict:
    gap_text = _gap_remediation_content(run)
    if not gap_text:
        return make_result(1, "RQ-013: no explicit gap remediation evidence found", flags=["missing_gap_analysis"])
    return await run_likert_judge(
        eval_id="RQ-013",
        eval_name="Gap and contradiction remediation quality",
        anchors=_get_anchors("RQ-013"),
        specific_instructions=_get_instructions("RQ-013"),
        agent_output=_join_sections(gap_text, "TRACE:\n" + _trace_summary_text(run)),
    )


async def eval_rr_001(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RR-001",
        eval_name="Reflection quality at decision points",
        anchors=_get_anchors("RR-001"),
        specific_instructions=_get_instructions("RR-001"),
        agent_output=_skill_interactions_text(run) + "\n\nTRACE:\n" + _trace_summary_text(run),
    )


async def eval_rr_002(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RR-002",
        eval_name="Relationship-building between sources",
        anchors=_get_anchors("RR-002"),
        specific_instructions=_get_instructions("RR-002"),
        agent_output=_bundle_content(run),
    )


async def eval_rr_003(run: Any, example: Any) -> dict:
    return await run_likert_judge(
        eval_id="RR-003",
        eval_name="Self-correction and course adjustment",
        anchors=_get_anchors("RR-003"),
        specific_instructions=_get_instructions("RR-003"),
        agent_output=_skill_interactions_text(run) + "\n\nTRACE:\n" + _trace_summary_text(run),
    )


async def eval_ri_002(run: Any, example: Any) -> dict:
    bundle = _bundle_content(run)
    if not bundle:
        return make_result(0, "RI-002: no bundle content", flags=["missing_bundle"])

    prd_text = _get_inputs(example).get("prd_content", "")
    requirements = extract_functional_requirements(prd_text)
    if not requirements:
        return make_result(0, "RI-002: no functional requirements extracted from PRD", flags=["missing_fr_checklist"])

    checklist = _fr_checklist_text(example)
    coverage = _fr_coverage_details(run, example)
    quick_missing = [fr_id for fr_id, detail in coverage.items() if not detail["met"]]
    evidence_lines = [f"{fr_id}: {detail['summary']}" for fr_id, detail in coverage.items() if detail["met"]]
    if not quick_missing:
        return make_result(
            1,
            "RI-002: all PRD functional areas are evidenced across bundle, trace, decomposition, and HITL artifacts",
            evidence=evidence_lines,
            details={"fr_checklist": checklist, "fr_coverage": coverage},
        )
    if len(quick_missing) >= 3:
        return make_result(
            0,
            f"RI-002: missing evidence for {', '.join(quick_missing)}",
            evidence=[f"{fr_id}: {coverage[fr_id]['summary']}" for fr_id in quick_missing],
            flags=["missing_fr_coverage"],
            details={"fr_checklist": checklist, "fr_coverage": coverage, "quick_missing": quick_missing},
        )

    record = _join_sections(
        "RESEARCH BUNDLE:\n" + bundle,
        "DECOMPOSITION:\n" + _decomposition_content(run),
        "HITL CLUSTER:\n" + _hitl_content(run),
        "SKILL INTERACTIONS:\n" + _skill_interactions_text(run),
        "TRACE SUMMARY:\n" + _trace_summary_text(run),
    )
    result = await run_binary_judge(
        eval_id="RI-002",
        eval_name="Research covers all PRD functional requirements",
        pass_criteria=(
            "The full research record addresses every PRD functional requirement area listed below. Missing even one area is a failure.\n\n"
            f"{checklist}"
        ),
        trace_data=record[:20000],
        additional_context=(
            f"PRD functional requirement checklist:\n{checklist}\n\n"
            f"Programmatic coverage signals:\n" + "\n".join(
                f"- {fr_id}: {'met' if detail['met'] else 'missing'} — {detail['summary']}"
                for fr_id, detail in coverage.items()
            )
        ),
    )
    result["details"] = {
        "fr_checklist": checklist,
        "fr_coverage": coverage,
        "quick_missing": quick_missing,
        **result.get("details", {}),
    }
    if quick_missing and result["score"] >= 1:
        result["score"] = 0
        result["comment"] = f"RI-002: judge was positive, but programmatic coverage is still missing {', '.join(quick_missing)}"
        result["reasoning"] = result["comment"]
        result["flags"] = list(result.get("flags", [])) + ["quick_missing_cap"]
    return result


async def eval_ri_003(run: Any, example: Any) -> dict:
    bundle = _bundle_content(run)
    if not bundle:
        return make_result(0, "RI-003: no bundle content", flags=["missing_bundle"])
    eval_text = _evaluation_implications_content(run)
    eval_lower = eval_text.lower()
    required_terms = ("langsmith", "dataset", "evaluator", "trace", "experiment")
    matched_terms = [term for term in required_terms if term in eval_lower]
    if len(matched_terms) == len(required_terms):
        return make_result(
            1,
            "RI-003: eval implementation considerations are explicitly covered",
            evidence=matched_terms,
            details={"matched_terms": matched_terms},
        )
    if len(matched_terms) <= 1:
        return make_result(
            0,
            "RI-003: eval implementation considerations are not substantively covered",
            evidence=matched_terms,
            flags=["missing_eval_implications"],
            details={"matched_terms": matched_terms},
        )
    return await run_binary_judge(
        eval_id="RI-003",
        eval_name="Research covers eval implications",
        pass_criteria=(
            "The research bundle addresses tooling, patterns, or considerations relevant to implementing the eval suite, such as LangSmith evaluation workflows, dataset creation, evaluator design, or trace instrumentation."
        ),
        trace_data=eval_text[:16000],
    )


RESEARCH_EVAL_REGISTRY: dict[str, dict[str, Any]] = {
    "RINFRA-001": {"fn": eval_rinfra_001, "phase": "A", "type": "deterministic"},
    "RINFRA-002": {"fn": eval_rinfra_002, "phase": "A", "type": "deterministic"},
    "RINFRA-003": {"fn": eval_rinfra_003, "phase": "C", "type": "llm_likert"},
    "RINFRA-004": {"fn": eval_rinfra_004, "phase": "C", "type": "llm_likert"},
    "RS-001": {"fn": eval_rs_001, "phase": "A", "type": "deterministic"},
    "RS-002": {"fn": eval_rs_002, "phase": "A", "type": "deterministic"},
    "RS-003": {"fn": eval_rs_003, "phase": "A", "type": "deterministic"},
    "RS-004": {"fn": eval_rs_004, "phase": "A", "type": "deterministic"},
    "RB-001": {"fn": eval_rb_001, "phase": "B", "type": "deterministic"},
    "RB-002": {"fn": eval_rb_002, "phase": "B", "type": "deterministic"},
    "RB-003": {"fn": eval_rb_003, "phase": "B", "type": "deterministic"},
    "RB-004": {"fn": eval_rb_004, "phase": "B", "type": "deterministic"},
    "RB-005": {"fn": eval_rb_005, "phase": "B", "type": "hybrid"},
    "RB-006": {"fn": eval_rb_006, "phase": "B", "type": "deterministic"},
    "RB-007": {"fn": eval_rb_007, "phase": "B", "type": "deterministic"},
    "RB-008": {"fn": eval_rb_008, "phase": "B", "type": "deterministic"},
    "RB-009": {"fn": eval_rb_009, "phase": "B", "type": "hybrid"},
    "RB-010": {"fn": eval_rb_010, "phase": "B", "type": "hybrid"},
    "RB-011": {"fn": eval_rb_011, "phase": "B", "type": "hybrid"},
    "RQ-001": {"fn": eval_rq_001, "phase": "C", "type": "llm_likert"},
    "RQ-002": {"fn": eval_rq_002, "phase": "C", "type": "llm_likert"},
    "RQ-003": {"fn": eval_rq_003, "phase": "C", "type": "llm_likert"},
    "RQ-004": {"fn": eval_rq_004, "phase": "C", "type": "hybrid"},
    "RQ-005": {"fn": eval_rq_005, "phase": "C", "type": "llm_likert"},
    "RQ-006": {"fn": eval_rq_006, "phase": "C", "type": "llm_likert"},
    "RQ-007": {"fn": eval_rq_007, "phase": "C", "type": "llm_likert"},
    "RQ-008": {"fn": eval_rq_008, "phase": "C", "type": "llm_likert"},
    "RQ-009": {"fn": eval_rq_009, "phase": "C", "type": "llm_likert"},
    "RQ-010": {"fn": eval_rq_010, "phase": "C", "type": "llm_likert"},
    "RQ-011": {"fn": eval_rq_011, "phase": "C", "type": "llm_likert"},
    "RQ-012": {"fn": eval_rq_012, "phase": "C", "type": "llm_likert"},
    "RQ-013": {"fn": eval_rq_013, "phase": "C", "type": "llm_likert"},
    "RR-001": {"fn": eval_rr_001, "phase": "C", "type": "llm_likert"},
    "RR-002": {"fn": eval_rr_002, "phase": "C", "type": "llm_likert"},
    "RR-003": {"fn": eval_rr_003, "phase": "C", "type": "llm_likert"},
    "RI-001": {"fn": eval_ri_001, "phase": "D", "type": "deferred"},
    "RI-002": {"fn": eval_ri_002, "phase": "D", "type": "hybrid"},
    "RI-003": {"fn": eval_ri_003, "phase": "D", "type": "hybrid"},
}

validate_registry_ids(RESEARCH_EVAL_REGISTRY)
