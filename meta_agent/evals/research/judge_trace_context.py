"""Trace-context assembly helpers for research judge evaluators.

This module builds a context pack that includes:
1) a raw payload (run-only or LangSmith-fetched tree)
2) a distilled judge view for prompt evidence packing
"""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from langsmith import Client


def _run_get(run: Any, key: str, default: Any = None) -> Any:
    if run is None:
        return default
    if isinstance(run, Mapping):
        return run.get(key, default)
    return getattr(run, key, default)


def _outputs_from_run(run: Any) -> dict[str, Any]:
    value = _run_get(run, "outputs", {}) or {}
    return value if isinstance(value, dict) else {}


def _safe_json(value: Any, *, max_chars: int = 20000) -> str:
    try:
        rendered = json.dumps(value, default=str)
    except Exception:
        rendered = str(value)
    if len(rendered) <= max_chars:
        return rendered
    return f"{rendered[:max_chars]}...<truncated>"


def _short_text(value: Any, *, max_chars: int = 3000) -> str:
    if not isinstance(value, str):
        value = "" if value is None else str(value)
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}...<truncated>"


def _serialize_run(run: Any, *, child_depth: int = 1) -> dict[str, Any]:
    record = {
        "id": str(_run_get(run, "id", "")),
        "trace_id": str(_run_get(run, "trace_id", "")),
        "parent_run_id": str(_run_get(run, "parent_run_id", "")),
        "name": _run_get(run, "name", ""),
        "run_type": _run_get(run, "run_type", ""),
        "start_time": str(_run_get(run, "start_time", "")),
        "end_time": str(_run_get(run, "end_time", "")),
        "error": _run_get(run, "error"),
        "tags": _run_get(run, "tags", []) or [],
        "extra": _run_get(run, "extra", {}) or {},
        "metadata": _run_get(run, "metadata", {}) or {},
        "inputs": _run_get(run, "inputs", {}) or {},
        "outputs": _run_get(run, "outputs", {}) or {},
    }
    if child_depth <= 0:
        return record

    children = _run_get(run, "child_runs", []) or []
    serialized_children: list[dict[str, Any]] = []
    for child in children:
        serialized_children.append(_serialize_run(child, child_depth=child_depth - 1))
    if serialized_children:
        record["child_runs"] = serialized_children
    return record


def _summarize_child_runs(run_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    children = run_payload.get("child_runs", []) or []
    summaries: list[dict[str, Any]] = []
    for child in children[:200]:
        if not isinstance(child, Mapping):
            continue
        summaries.append(
            {
                "id": str(child.get("id", "")),
                "name": child.get("name", ""),
                "run_type": child.get("run_type", ""),
                "error": child.get("error"),
            }
        )
    return summaries


def _build_judge_view(run_payload: Mapping[str, Any]) -> dict[str, Any]:
    outputs = run_payload.get("outputs", {}) or {}
    trace_summary = outputs.get("trace_summary", {}) if isinstance(outputs, Mapping) else {}
    tool_calls = trace_summary.get("tool_calls", []) if isinstance(trace_summary, Mapping) else []
    tool_call_preview = []
    if isinstance(tool_calls, list):
        for call in tool_calls[:120]:
            if not isinstance(call, Mapping):
                continue
            tool_call_preview.append(
                {
                    "name": call.get("name", ""),
                    "timestamp": call.get("timestamp"),
                    "args": call.get("args", {}),
                }
            )

    return {
        "run_id": str(run_payload.get("id", "")),
        "trace_id": str(run_payload.get("trace_id", "")),
        "run_name": run_payload.get("name", ""),
        "run_type": run_payload.get("run_type", ""),
        "error": run_payload.get("error"),
        "bundle_excerpt": _short_text(outputs.get("research_bundle_content", ""), max_chars=8000),
        "decomposition_excerpt": _short_text(outputs.get("decomposition_content", ""), max_chars=4000),
        "hitl_excerpt": _short_text(outputs.get("hitl_cluster_content", ""), max_chars=4000),
        "delegation_excerpt": _short_text(outputs.get("delegation_context", ""), max_chars=4000),
        "gap_remediation_excerpt": _short_text(outputs.get("gap_remediation_context", ""), max_chars=4000),
        "skill_interaction_count": len(outputs.get("skill_interactions", []) or []),
        "trace_summary": trace_summary if isinstance(trace_summary, Mapping) else {},
        "trace_tool_call_preview": tool_call_preview,
        "child_run_summaries": _summarize_child_runs(run_payload),
    }


def _langsmith_client() -> Client | None:
    if not os.getenv("LANGSMITH_API_KEY"):
        return None
    return Client()


def _read_run_with_children(client: Client, run_id: str) -> Any:
    return client.read_run(run_id, load_child_runs=True)


def build_trace_context_pack(
    run: Any,
    *,
    eval_id: str,
    require_full_trace_fetch: bool,
) -> dict[str, Any]:
    """Build a trace context pack for judge prompts and metadata."""
    run_id = str(_run_get(run, "id", "") or _run_get(run, "run_id", "") or "")
    trace_id = str(_run_get(run, "trace_id", "") or "")

    run_payload = _serialize_run(
        {
            "id": run_id,
            "trace_id": trace_id,
            "parent_run_id": str(_run_get(run, "parent_run_id", "") or ""),
            "name": _run_get(run, "name", ""),
            "run_type": _run_get(run, "run_type", ""),
            "start_time": str(_run_get(run, "start_time", "") or ""),
            "end_time": str(_run_get(run, "end_time", "") or ""),
            "error": _run_get(run, "error"),
            "tags": _run_get(run, "tags", []) or [],
            "extra": _run_get(run, "extra", {}) or {},
            "metadata": _run_get(run, "metadata", {}) or {},
            "inputs": _run_get(run, "inputs", {}) or {},
            "outputs": _outputs_from_run(run),
            "child_runs": _run_get(run, "child_runs", []) or [],
        },
        child_depth=1,
    )

    source = "run_only"
    fetch_error = ""
    fetched_payload: dict[str, Any] | None = None

    if require_full_trace_fetch and run_id:
        client = _langsmith_client()
        if client is not None:
            try:
                fetched_run = _read_run_with_children(client, run_id)
                fetched_payload = _serialize_run(fetched_run, child_depth=3)
                source = "langsmith_fetched_trace"
            except Exception as exc:
                fetch_error = str(exc)

    raw_payload = fetched_payload or run_payload
    judge_view = _build_judge_view(raw_payload)
    judge_view["trace_context_source"] = source

    return {
        "eval_id": eval_id,
        "trace_context_source": source,
        "run_id": run_id,
        "trace_id": trace_id,
        "fetch_error": fetch_error,
        "raw_trace_payload": raw_payload,
        "raw_trace_payload_json": _safe_json(raw_payload, max_chars=120000),
        "judge_view": judge_view,
        "judge_view_json": _safe_json(judge_view, max_chars=40000),
    }
