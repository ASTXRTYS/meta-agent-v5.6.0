"""Deterministic evaluators and trace checks for research-agent evals."""

from __future__ import annotations

import os
from typing import Any, Iterable, Mapping

from meta_agent.evals.research.common import (
    CANONICAL_RESEARCH_BUNDLE_PATH,
    CANONICAL_RESEARCH_DECOMPOSITION_PATH,
    RESEARCH_BUNDLE_FRONTMATTER_FIELDS,
    extract_urls,
    extract_yaml_frontmatter,
    get_arg_path,
    get_timestamp,
    make_result,
    missing_research_bundle_frontmatter_fields,
    normalize_url,
)


def _get_outputs(run: Any) -> dict:
    return run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}


def _get_inputs(obj: Any) -> dict:
    return obj.inputs if hasattr(obj, "inputs") else obj.get("inputs", {}) or {}


def _get_trace(run: Any) -> dict:
    outputs = _get_outputs(run)
    return outputs.get("trace_summary", {})


def _get_tool_calls(run: Any) -> list[dict]:
    return _get_trace(run).get("tool_calls", [])


def _tool_order_entries(run: Any) -> list[tuple[int, float, dict]]:
    entries: list[tuple[int, float, dict]] = []
    for idx, tool_call in enumerate(_get_tool_calls(run)):
        timestamp = get_timestamp(tool_call)
        if timestamp is None:
            timestamp = float(idx)
        entries.append((idx, timestamp, tool_call))
    return entries


def _merge_segments(segments: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    ordered = sorted((start, end) for start, end in segments if end > start)
    merged: list[tuple[int, int]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _extract_read_segments(reads: Iterable[Mapping[str, Any]]) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    for read in reads:
        args = read.get("args", {}) or {}
        start = args.get("offset", args.get("start"))
        end = args.get("end")
        length = args.get("length", args.get("limit", args.get("num_chars")))
        if isinstance(start, int) and isinstance(end, int):
            segments.append((start, end))
        elif isinstance(start, int) and isinstance(length, int):
            segments.append((start, start + length))
    return segments


def _coverage_ratio(reads: list[Mapping[str, Any]], total_chars: int) -> float:
    if total_chars <= 0:
        return 0.0
    segments = _merge_segments(_extract_read_segments(reads))
    covered = sum(end - start for start, end in segments)
    return min(covered / total_chars, 1.0)


def _output_state(outputs: Mapping[str, Any]) -> Mapping[str, Any]:
    state = outputs.get("state_out") or outputs.get("output_state")
    return state if isinstance(state, Mapping) else {}


def _search_tool_calls(run: Any, *, name: str | None = None, path_contains: str | None = None) -> list[dict]:
    matches: list[dict] = []
    for tool_call in _get_tool_calls(run):
        if name and tool_call.get("name") != name:
            continue
        if path_contains and path_contains not in get_arg_path(tool_call.get("args", {})).lower():
            continue
        matches.append(tool_call)
    return matches


def _first_research_action(run: Any) -> tuple[int, float, dict] | None:
    for entry in _tool_order_entries(run):
        tool_call = entry[2]
        if tool_call.get("name") in {"web_search", "web_fetch", "task"}:
            return entry
    return None


def _deep_dive_actions(run: Any) -> list[tuple[int, float, dict]]:
    deep_keywords = (
        "github",
        "issue",
        "issues",
        "api",
        "reference",
        "source",
        "repo",
        "langchain-anthropic",
    )
    matches: list[tuple[int, float, dict]] = []
    for entry in _tool_order_entries(run):
        tool_call = entry[2]
        if tool_call.get("name") not in {"web_search", "web_fetch"}:
            continue
        args_text = str(tool_call.get("args", {})).lower()
        if any(keyword in args_text for keyword in deep_keywords):
            matches.append(entry)
    return matches


def _citation_support(outputs: Mapping[str, Any]) -> list[dict]:
    checks = outputs.get("citation_claim_support", [])
    return checks if isinstance(checks, list) else []


def eval_rinfra_001(run: Any, example: Any) -> dict:
    outputs = _get_outputs(run)
    path = str(outputs.get("research_bundle_path", ""))
    if path and os.path.isfile(path):
        return make_result(1, f"RINFRA-001: bundle exists at {path}", evidence=[path])
    has_content = bool(outputs.get("research_bundle_content"))
    trace = outputs.get("trace_summary", {})
    has_writes = trace.get("write_file_calls", 0) > 0
    exists = bool(path) and (has_content or has_writes)
    return make_result(
        1 if exists else 0,
        f"RINFRA-001: path={bool(path)}, content={has_content}, writes={has_writes}",
        evidence=[CANONICAL_RESEARCH_BUNDLE_PATH] if path else [],
    )


def eval_rinfra_002(run: Any, example: Any) -> dict:
    outputs = _get_outputs(run)
    content = outputs.get("research_bundle_content", "")
    if not content:
        return make_result(0, "RINFRA-002: no bundle content available", flags=["missing_bundle"])

    parts = content.split("---", 2)
    if len(parts) < 3:
        return make_result(0, "RINFRA-002: no YAML frontmatter delimiters", flags=["frontmatter_missing"])

    fm = extract_yaml_frontmatter(content)
    if fm is None:
        return make_result(0, "RINFRA-002: frontmatter is not a mapping", flags=["frontmatter_invalid"])
    missing = missing_research_bundle_frontmatter_fields(content)
    return make_result(
        1 if not missing else 0,
        "RINFRA-002: all fields present" if not missing else f"RINFRA-002: missing={missing}",
        evidence=list(RESEARCH_BUNDLE_FRONTMATTER_FIELDS) if not missing else missing,
        flags=[] if not missing else ["frontmatter_incomplete"],
    )


def eval_rs_001(run: Any, example: Any) -> dict:
    inputs = _get_inputs(example)
    has = "prd_path" in inputs or "prd_content" in inputs
    return make_result(1 if has else 0, f"RS-001: prd in state={has}")


def eval_rs_002(run: Any, example: Any) -> dict:
    inputs = _get_inputs(example)
    has = "eval_suite_path" in inputs or "eval_suite_content" in inputs
    return make_result(1 if has else 0, f"RS-002: eval suite in state={has}")


def eval_rs_003(run: Any, example: Any) -> dict:
    inputs = _get_inputs(example)
    fields = ["skills_paths", "twitter_handles", "config"]
    missing = [field for field in fields if field not in inputs]
    return make_result(
        1 if not missing else 0,
        "RS-003: all config fields present" if not missing else f"RS-003: missing={missing}",
        evidence=fields if not missing else missing,
        flags=[] if not missing else ["missing_config_fields"],
    )


def eval_rs_004(run: Any, example: Any) -> dict:
    outputs = _get_outputs(run)
    state_out = _output_state(outputs)
    if not state_out:
        return make_result(0, "RS-004: no explicit output state", flags=["missing_output_state"])
    required = ["research_bundle_path", "trace_summary"]
    missing = [field for field in required if field not in state_out]
    return make_result(
        1 if not missing else 0,
        "RS-004: explicit output state present" if not missing else f"RS-004: missing={missing}",
        evidence=required if not missing else missing,
        flags=[] if not missing else ["output_state_incomplete"],
    )


def eval_rb_001(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    if trace.get("prd_fully_read"):
        return make_result(1, "RB-001: PRD fully read (trace flag)")
    inputs = _get_inputs(example)
    total_chars = int(trace.get("prd_total_chars") or len(inputs.get("prd_content", "")) or 0)
    reads = _search_tool_calls(run, name="read_file", path_contains="prd")
    ratio = _coverage_ratio(reads, total_chars) if reads and total_chars else 0.0
    passed = ratio >= 0.98
    return make_result(
        1 if passed else 0,
        f"RB-001: PRD read coverage={ratio:.2%} across {len(reads)} reads",
        evidence=[f"coverage={ratio:.2%}", f"reads={len(reads)}"],
        flags=[] if passed else ["partial_prd_read"],
        details={"coverage_ratio": ratio, "read_count": len(reads), "total_chars": total_chars},
    )


def eval_rb_002(run: Any, example: Any) -> dict:
    reads = [
        entry for entry in _tool_order_entries(run)
        if entry[2].get("name") == "read_file" and "eval" in get_arg_path(entry[2].get("args", {})).lower()
    ]
    first_read = reads[0] if reads else None
    first_research = _first_research_action(run)
    if not first_read:
        return make_result(0, "RB-002: no eval suite read found", flags=["missing_eval_suite_read"])
    if first_research is None:
        return make_result(1, "RB-002: eval suite read before any research action")
    passed = first_read[0] < first_research[0]
    return make_result(
        1 if passed else 0,
        "RB-002: eval suite read before research started"
        if passed else "RB-002: eval suite read happened after research started",
        evidence=[
            f"first_eval_read_index={first_read[0]}",
            f"first_research_index={first_research[0]}",
        ],
        flags=[] if passed else ["late_eval_suite_read"],
    )


def eval_rb_003(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    if trace.get("decomposition_persisted"):
        return make_result(1, "RB-003: decomposition persisted (trace flag)")
    writes = _search_tool_calls(run, name="write_file", path_contains="decomposition")
    passed = any(CANONICAL_RESEARCH_DECOMPOSITION_PATH in get_arg_path(tc.get("args", {})) for tc in writes) or bool(writes)
    return make_result(
        1 if passed else 0,
        f"RB-003: {len(writes)} decomposition writes",
        evidence=[get_arg_path(tc.get("args", {})) for tc in writes[:3]],
        flags=[] if passed else ["missing_decomposition_write"],
    )


def eval_rb_004(run: Any, example: Any) -> dict:
    web_calls = [tc for tc in _get_tool_calls(run) if tc.get("name") in ("web_search", "web_fetch")]
    return make_result(
        1 if web_calls else 0,
        f"RB-004: {len(web_calls)} web tool calls",
        evidence=[tc.get("name", "") for tc in web_calls[:5]],
        flags=[] if web_calls else ["missing_web_research"],
    )


def eval_rb_006(run: Any, example: Any) -> dict:
    anthropic_related = [
        tc for tc in _get_tool_calls(run)
        if tc.get("name") in ("web_search", "web_fetch")
        and any(keyword in str(tc.get("args", {})).lower() for keyword in ("anthropic", "claude", "opus"))
    ]
    return make_result(
        1 if anthropic_related else 0,
        f"RB-006: {len(anthropic_related)} Anthropic research calls",
        evidence=[str(tc.get("args", {}))[:120] for tc in anthropic_related[:3]],
        flags=[] if anthropic_related else ["missing_anthropic_research"],
    )


def eval_rb_007(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    if trace.get("skills_read", 0) > 0:
        return make_result(1, f"RB-007: {trace['skills_read']} skills read (trace flag)")
    reads = [
        tc for tc in _get_tool_calls(run)
        if tc.get("name") == "read_file"
        and "/skills/" in get_arg_path(tc.get("args", {}))
    ]
    return make_result(
        1 if reads else 0,
        f"RB-007: {len(reads)} skill file reads",
        evidence=[get_arg_path(tc.get("args", {})) for tc in reads[:5]],
        flags=[] if reads else ["missing_skill_reads"],
    )


def eval_rb_008(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    if trace.get("task_calls", 0) > 0:
        return make_result(1, f"RB-008: {trace['task_calls']} task calls (trace flag)")
    tasks = [tc for tc in _get_tool_calls(run) if tc.get("name") == "task"]
    research_tasks = [
        tc for tc in tasks
        if any(keyword in str(tc.get("args", {})).lower() for keyword in ("research", "domain", "source", "finding"))
    ]
    return make_result(
        1 if research_tasks else 0,
        f"RB-008: {len(research_tasks)} research task tool calls",
        evidence=[str(tc.get("args", {}))[:140] for tc in research_tasks[:3]],
        flags=[] if research_tasks else ["missing_research_tasks"],
    )


def eval_rb_009(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    if "sub_agents_parallel" in trace:
        passed = bool(trace.get("sub_agents_parallel"))
        return make_result(
            1 if passed else 0,
            "RB-009: trace explicitly marks sub-agents parallel"
            if passed else "RB-009: trace explicitly marks sub-agents non-parallel",
            details={"source": "trace_flag"},
        )

    task_windows = trace.get("task_windows", [])
    if isinstance(task_windows, list) and task_windows:
        windows = []
        for window in task_windows:
            start = window.get("start")
            end = window.get("end")
            if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                windows.append((float(start), float(end)))
        for idx, (start_a, end_a) in enumerate(windows):
            for start_b, end_b in windows[idx + 1:]:
                if min(end_a, end_b) > max(start_a, start_b):
                    return make_result(1, "RB-009: overlapping task windows detected", details={"source": "task_windows"})
        return make_result(0, "RB-009: task windows do not overlap", details={"source": "task_windows"})

    return make_result(-1, "RB-009: insufficient ordering data for deterministic check", flags=["missing_parallel_timing"])


def eval_rb_010(run: Any, example: Any) -> dict:
    entries = _tool_order_entries(run)
    task_entries = [entry for entry in entries if entry[2].get("name") == "task"]
    if not task_entries:
        return make_result(0, "RB-010: no sub-agents spawned, nothing to aggregate", flags=["missing_subagents"])

    subfinding_reads = [
        entry for entry in entries
        if entry[2].get("name") == "read_file"
        and "sub-findings" in get_arg_path(entry[2].get("args", {})).lower()
    ]
    if not subfinding_reads:
        return make_result(0, "RB-010: no sub-finding reads found", flags=["missing_subfinding_reads"])

    timestamps_available = all(get_timestamp(entry[2]) is not None for entry in task_entries + subfinding_reads)
    if not timestamps_available:
        return make_result(-1, "RB-010: insufficient ordering data for deterministic check", flags=["missing_aggregation_timestamps"])

    latest_task_time = max(entry[1] for entry in task_entries)
    after_task_reads = [entry for entry in subfinding_reads if entry[1] > latest_task_time]
    return make_result(
        1 if after_task_reads else 0,
        "RB-010: sub-findings were read after sub-agents completed"
        if after_task_reads else "RB-010: no sub-finding read occurred after sub-agent completion",
        evidence=[get_arg_path(entry[2].get("args", {})) for entry in after_task_reads[:3]],
        flags=[] if after_task_reads else ["missing_post_subagent_aggregation"],
    )


def eval_rb_011(run: Any, example: Any) -> dict:
    trace = _get_trace(run)
    approval_time = trace.get("hitl_approval_timestamp")
    deep_dive_time = trace.get("deep_dive_start_timestamp")
    if isinstance(approval_time, (int, float)) and isinstance(deep_dive_time, (int, float)):
        passed = float(approval_time) < float(deep_dive_time)
        return make_result(
            1 if passed else 0,
            "RB-011: HITL approval occurred before deep-dive research"
            if passed else "RB-011: deep-dive research started before HITL approval",
            evidence=[f"approval={approval_time}", f"deep_dive={deep_dive_time}"],
            flags=[] if passed else ["late_hitl_gate"],
        )

    if trace.get("hitl_approvals", 0) <= 0:
        return make_result(0, "RB-011: no HITL approvals in trace", flags=["missing_hitl_approval"])

    deep_dive_actions = _deep_dive_actions(run)
    if not deep_dive_actions:
        return make_result(-1, "RB-011: insufficient deep-dive ordering data", flags=["missing_deep_dive_timing"])

    return make_result(-1, "RB-011: ordering data incomplete for deterministic check", flags=["missing_hitl_timing"])


def eval_rb_005_precheck(run: Any, example: Any) -> dict[str, Any]:
    outputs = _get_outputs(run)
    bundle = outputs.get("research_bundle_content", "")
    cited_urls = [normalize_url(url) for url in extract_urls(bundle)]
    fetched_urls = {
        normalize_url(str(tc.get("args", {}).get("url", "")))
        for tc in _get_tool_calls(run)
        if tc.get("name") == "web_fetch" and tc.get("args", {}).get("url")
    }
    support_checks = _citation_support(outputs)
    unsupported = [check for check in support_checks if check.get("supported") is False]
    missing_urls = sorted(url for url in cited_urls if url not in fetched_urls)
    return {
        "cited_urls": cited_urls,
        "fetched_urls": sorted(fetched_urls),
        "missing_urls": missing_urls,
        "unsupported_claims": unsupported,
        "has_verification": bool(support_checks),
        "no_citations": not cited_urls,
    }


def eval_ri_001(run: Any, example: Any) -> dict:
    return make_result(
        -1,
        "RI-001: DEFERRED — awaiting spec-writer agent",
        confidence="LOW",
        flags=["deferred"],
    )
