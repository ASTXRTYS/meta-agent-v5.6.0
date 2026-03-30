"""Markdown experiment report generator for research-agent evals.

Accepts results from either:
- runner.py run_suite() return dict (full make_result() dicts with reasoning/evidence)
- langsmith.evaluate() ExperimentResults (EvaluationResult objects with .key, .score,
  .comment, and optional .metadata)

Persists structured markdown reports to disk for human review and code-agent consumption.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Mapping

from meta_agent.evals.research.common import get_canonical_eval_ids
from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY

_CANONICAL_BY_CASEFOLD = {eval_id.casefold(): eval_id for eval_id in RESEARCH_EVAL_REGISTRY}
_DEFERRED_EVAL_IDS = {
    eval_id for eval_id, meta in RESEARCH_EVAL_REGISTRY.items() if meta["type"] == "deferred"
}
_LIKERT_EVAL_IDS = {
    eval_id for eval_id, meta in RESEARCH_EVAL_REGISTRY.items() if meta["type"] == "llm_likert"
}
_EVAL_PREFIX_MAP = {
    "rb": "RB",
    "ri": "RI",
    "rq": "RQ",
    "rr": "RR",
    "rs": "RS",
    "rinfra": "RINFRA",
}


def _timestamp_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_str(value: Any, max_len: int = 200) -> str:
    s = str(value or "")
    return s[:max_len] + "..." if len(s) > max_len else s


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def normalize_eval_id(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    direct = _CANONICAL_BY_CASEFOLD.get(raw.casefold())
    if direct:
        return direct

    match = re.fullmatch(r"(?:eval_)?([a-z]+)[\-_](\d{3})", raw.casefold())
    if match:
        prefix = _EVAL_PREFIX_MAP.get(match.group(1))
        if prefix:
            return f"{prefix}-{match.group(2)}"

    cleaned = raw.replace("_", "-").upper()
    return _CANONICAL_BY_CASEFOLD.get(cleaned.casefold(), cleaned)


def _registry_counts() -> dict[str, int]:
    defined = len(get_canonical_eval_ids())
    deferred = len(_DEFERRED_EVAL_IDS)
    return {
        "defined_eval_count": defined,
        "active_eval_count": defined - deferred,
        "deferred_eval_count": deferred,
    }


def _result_type(eval_id: str) -> str:
    meta = RESEARCH_EVAL_REGISTRY.get(eval_id)
    if meta:
        return str(meta.get("type", "deterministic"))
    if eval_id in _LIKERT_EVAL_IDS:
        return "llm_likert"
    if eval_id in _DEFERRED_EVAL_IDS:
        return "deferred"
    return "deterministic"


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    metadata = _as_mapping(normalized.get("metadata"))
    details = _as_mapping(normalized.get("details")) or _as_mapping(metadata.get("details"))

    eval_id = normalize_eval_id(
        normalized.get("eval_id") or normalized.get("key") or metadata.get("eval_id")
    )
    comment = str(normalized.get("comment") or metadata.get("comment") or "")
    reasoning = str(normalized.get("reasoning") or metadata.get("reasoning") or comment)
    evidence = _as_list(normalized.get("evidence") or metadata.get("evidence"))
    confidence = str(normalized.get("confidence") or metadata.get("confidence") or "")
    flags = [str(flag) for flag in _as_list(normalized.get("flags") or metadata.get("flags"))]

    judge_backend = _as_mapping(metadata.get("judge_backend"))
    if judge_backend:
        details = {**details, "judge_backend": judge_backend}

    score = normalized.get("score", -1)
    if score is None:
        score = -1

    normalized.update(
        {
            "eval_id": eval_id,
            "key": eval_id or normalized.get("key", ""),
            "score": score,
            "comment": comment,
            "reasoning": reasoning,
            "evidence": evidence,
            "confidence": confidence,
            "flags": flags,
            "metadata": metadata,
        }
    )
    if details:
        normalized["details"] = details
    return normalized


def _classify_result(result: dict[str, Any]) -> str:
    """Classify a result as pass, fail, below_threshold, or deferred."""
    normalized = _normalize_result(result)
    score = normalized.get("score", -1)
    eval_id = normalized.get("eval_id", "")
    eval_type = _result_type(eval_id)

    if score == -1 or eval_type == "deferred":
        return "deferred"

    if eval_type == "llm_likert":
        return "pass" if score >= 4 else "below_threshold"

    return "pass" if score >= 1 else "fail"


def _format_failure_block(result: dict[str, Any]) -> str:
    """Format a single failure with full judge reasoning and evidence."""
    normalized = _normalize_result(result)
    eval_id = normalized.get("eval_id", normalized.get("key", ""))
    score = normalized.get("score", -1)
    classification = _classify_result(normalized)

    if classification == "below_threshold":
        score_label = f"{score} (BELOW THRESHOLD, need >= 4)"
    elif classification == "fail":
        score_label = f"{score} (FAIL)"
    else:
        score_label = str(score)

    lines = [f"### {eval_id}"]
    lines.append(f"- **Score:** {score_label}")

    reasoning = normalized.get("reasoning", normalized.get("comment", ""))
    if reasoning:
        lines.append(f"- **Reasoning:** {reasoning}")

    evidence = normalized.get("evidence", [])
    if evidence:
        evidence_str = ", ".join(f'"{e}"' for e in evidence[:5])
        lines.append(f"- **Evidence:** [{evidence_str}]")

    confidence = normalized.get("confidence", "")
    if confidence:
        lines.append(f"- **Confidence:** {confidence}")

    flags = normalized.get("flags", [])
    if flags:
        lines.append(f"- **Flags:** {', '.join(str(f) for f in flags)}")

    return "\n".join(lines)


def _format_passing_row(result: dict[str, Any]) -> str:
    """Format a single passing eval as a table row."""
    normalized = _normalize_result(result)
    eval_id = normalized.get("eval_id", normalized.get("key", ""))
    score = normalized.get("score", -1)
    confidence = normalized.get("confidence", "")
    comment = _safe_str(normalized.get("comment", normalized.get("reasoning", "")), 80)
    return f"| {eval_id} | {score} | {confidence} | {comment} |"


def generate_report(
    results: list[dict[str, Any]],
    *,
    experiment_name: str = "",
    scenario: str = "golden_path",
    mode: str = "trace",
    report_dir: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> str:
    """Generate a markdown experiment report from eval results."""
    timestamp = _timestamp_str()
    if not experiment_name:
        experiment_name = f"experiment-{int(time.time())}"

    normalized_results = [_normalize_result(result) for result in results]
    failures: list[dict[str, Any]] = []
    below_threshold: list[dict[str, Any]] = []
    passing: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    for result in normalized_results:
        classification = _classify_result(result)
        if classification == "fail":
            failures.append(result)
        elif classification == "below_threshold":
            below_threshold.append(result)
        elif classification == "deferred":
            deferred.append(result)
        else:
            passing.append(result)

    binary_results = [
        result
        for result in normalized_results
        if _classify_result(result) != "deferred"
        and _result_type(result.get("eval_id", "")) != "llm_likert"
    ]
    likert_results = [
        result
        for result in normalized_results
        if _result_type(result.get("eval_id", "")) == "llm_likert"
    ]

    binary_pass = sum(1 for result in binary_results if result.get("score", 0) >= 1)
    binary_total = len(binary_results)

    likert_scores = [result.get("score", 0) for result in likert_results if result.get("score", -1) > 0]
    likert_mean = sum(likert_scores) / len(likert_scores) if likert_scores else 0
    likert_min = min(likert_scores) if likert_scores else 0
    likert_max = max(likert_scores) if likert_scores else 0
    likert_below = sum(1 for score in likert_scores if score < 4)

    all_failures = failures + below_threshold
    overall = "PASSED" if not all_failures else "FAILED"

    registry_counts = _registry_counts()
    metadata = {
        **registry_counts,
        **(extra_metadata or {}),
    }

    lines = [
        "# Research Agent Experiment Report",
        "",
        f"- **Experiment:** {experiment_name}",
        f"- **Timestamp:** {timestamp}",
        f"- **Scenario:** {scenario}",
        f"- **Mode:** {mode}",
    ]

    for key, value in metadata.items():
        lines.append(f"- **{key}:** {value}")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- **Binary:** {binary_pass}/{binary_total} passed",
            f"- **Likert:** mean {likert_mean:.1f}, min {likert_min}, max {likert_max}, below threshold: {likert_below}",
            f"- **Overall:** {overall}",
            f"- **Registry coverage:** {metadata['defined_eval_count']} defined, {metadata['active_eval_count']} active, {metadata['deferred_eval_count']} deferred",
            f"- **Reported evals:** {len(normalized_results)} ({len(failures)} failed, {len(below_threshold)} below threshold, {len(passing)} passed, {len(deferred)} deferred)",
        ]
    )

    if all_failures:
        lines.extend(
            [
                "",
                "## Failures (action required)",
                "",
            ]
        )
        for result in sorted(all_failures, key=lambda item: item.get("score", 99)):
            lines.append(_format_failure_block(result))
            lines.append("")

    if passing:
        lines.extend(
            [
                "## Passing Evals",
                "",
                "| Eval ID | Score | Confidence | Key finding |",
                "|---------|-------|------------|-------------|",
            ]
        )
        for result in sorted(passing, key=lambda item: item.get("eval_id", item.get("key", ""))):
            lines.append(_format_passing_row(result))
        lines.append("")

    if deferred:
        lines.extend(
            [
                "## Deferred Evals",
                "",
            ]
        )
        for result in deferred:
            eval_id = result.get("eval_id", result.get("key", ""))
            comment = _safe_str(result.get("comment", ""), 120)
            lines.append(f"- **{eval_id}:** {comment}")
        lines.append("")

    for result in normalized_results:
        details = _as_mapping(result.get("details"))
        backend = _as_mapping(details.get("judge_backend"))
        if backend:
            provider = backend.get("provider", "unknown")
            model = backend.get("model", "unknown")
            lines.extend(
                [
                    "## Judge Backend",
                    "",
                    f"- **Provider:** {provider}",
                    f"- **Model:** {model}",
                    "",
                ]
            )
            break

    report = "\n".join(lines)

    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
        safe_name = experiment_name.replace("/", "-").replace(" ", "-")
        filename = f"{safe_name}-{int(time.time())}.md"
        filepath = os.path.join(report_dir, filename)
        with open(filepath, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {filepath}")

    return report


def generate_report_from_experiment_results(
    experiment_results: Any,
    *,
    experiment_name: str = "",
    scenario: str = "multi_scenario_calibration",
    report_dir: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> str:
    """Generate a report from LangSmith ExperimentResults."""
    results: list[dict[str, Any]] = []

    for result in experiment_results:
        eval_results = result.get("evaluation_results", {}).get("results", [])
        for eval_result in eval_results:
            metadata = _as_mapping(getattr(eval_result, "metadata", None))
            details = _as_mapping(metadata.get("details"))
            key = getattr(eval_result, "key", None) or _as_mapping(eval_result).get("key", "unknown")
            score = getattr(eval_result, "score", None)
            if score is None:
                score = _as_mapping(eval_result).get("score", -1)
            comment = getattr(eval_result, "comment", None) or _as_mapping(eval_result).get("comment", "")

            results.append(
                {
                    "eval_id": key,
                    "score": score if score is not None else -1,
                    "comment": comment or "",
                    "reasoning": metadata.get("reasoning", comment or ""),
                    "evidence": _as_list(metadata.get("evidence")),
                    "confidence": metadata.get("confidence", ""),
                    "flags": [str(flag) for flag in _as_list(metadata.get("flags"))],
                    "details": details,
                    "metadata": metadata,
                }
            )

    if not experiment_name:
        exp_name = getattr(experiment_results, "experiment_name", None)
        experiment_name = exp_name or f"langsmith-experiment-{int(time.time())}"

    return generate_report(
        results,
        experiment_name=experiment_name,
        scenario=scenario,
        mode="langsmith",
        report_dir=report_dir,
        extra_metadata=extra_metadata,
    )
