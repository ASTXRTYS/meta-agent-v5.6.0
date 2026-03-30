"""Markdown experiment report generator for research-agent evals.

Accepts results from either:
- runner.py run_suite() return dict (full make_result() dicts with reasoning/evidence)
- langsmith.evaluate() ExperimentResults (EvaluationResult objects with .key, .score, .comment)

Persists structured markdown reports to disk for human review and code-agent consumption.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any


def _timestamp_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_str(value: Any, max_len: int = 200) -> str:
    s = str(value or "")
    return s[:max_len] + "..." if len(s) > max_len else s


def _classify_result(result: dict) -> str:
    """Classify a result as pass, fail, below_threshold, or deferred."""
    score = result.get("score", -1)
    eval_id = result.get("eval_id", result.get("key", ""))

    if score == -1:
        return "deferred"

    # Likert evals (RINFRA-003, RINFRA-004, RQ-*, RR-*)
    is_likert = any(
        eval_id.startswith(prefix)
        for prefix in ("RINFRA-003", "RINFRA-004", "RQ-", "RR-")
    )
    if is_likert:
        return "pass" if score >= 4 else "below_threshold"

    # Binary evals
    return "pass" if score >= 1 else "fail"


def _format_failure_block(result: dict) -> str:
    """Format a single failure with full judge reasoning and evidence."""
    eval_id = result.get("eval_id", result.get("key", ""))
    score = result.get("score", -1)
    classification = _classify_result(result)

    if classification == "below_threshold":
        score_label = f"{score} (BELOW THRESHOLD, need >= 4)"
    elif classification == "fail":
        score_label = f"{score} (FAIL)"
    else:
        score_label = str(score)

    lines = [f"### {eval_id}"]
    lines.append(f"- **Score:** {score_label}")

    reasoning = result.get("reasoning", result.get("comment", ""))
    if reasoning:
        lines.append(f"- **Reasoning:** {reasoning}")

    evidence = result.get("evidence", [])
    if evidence:
        evidence_str = ", ".join(f'"{e}"' for e in evidence[:5])
        lines.append(f"- **Evidence:** [{evidence_str}]")

    confidence = result.get("confidence", "")
    if confidence:
        lines.append(f"- **Confidence:** {confidence}")

    flags = result.get("flags", [])
    if flags:
        lines.append(f"- **Flags:** {', '.join(str(f) for f in flags)}")

    return "\n".join(lines)


def _format_passing_row(result: dict) -> str:
    """Format a single passing eval as a table row."""
    eval_id = result.get("eval_id", result.get("key", ""))
    score = result.get("score", -1)
    confidence = result.get("confidence", "")
    comment = _safe_str(result.get("comment", result.get("reasoning", "")), 80)
    return f"| {eval_id} | {score} | {confidence} | {comment} |"


def generate_report(
    results: list[dict],
    *,
    experiment_name: str = "",
    scenario: str = "golden_path",
    mode: str = "trace",
    report_dir: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> str:
    """Generate a markdown experiment report from eval results.

    Args:
        results: List of result dicts. Each must have at least 'eval_id'/'key' and 'score'.
                 Optionally: 'reasoning', 'evidence', 'confidence', 'flags', 'comment', 'details'.
        experiment_name: Name for this experiment run.
        scenario: Calibration scenario name.
        mode: 'trace' or 'calibration'.
        report_dir: Directory to save the report. If None, report is returned but not saved.
        extra_metadata: Additional metadata to include in the report header.

    Returns:
        The full markdown report as a string.
    """
    timestamp = _timestamp_str()
    if not experiment_name:
        experiment_name = f"experiment-{int(time.time())}"

    # Classify results
    failures = []
    below_threshold = []
    passing = []
    deferred = []

    for result in results:
        classification = _classify_result(result)
        if classification == "fail":
            failures.append(result)
        elif classification == "below_threshold":
            below_threshold.append(result)
        elif classification == "deferred":
            deferred.append(result)
        else:
            passing.append(result)

    # Summary stats
    binary_results = [r for r in results if _classify_result(r) != "deferred" and not any(
        r.get("eval_id", r.get("key", "")).startswith(p)
        for p in ("RINFRA-003", "RINFRA-004", "RQ-", "RR-")
    )]
    likert_results = [r for r in results if any(
        r.get("eval_id", r.get("key", "")).startswith(p)
        for p in ("RINFRA-003", "RINFRA-004", "RQ-", "RR-")
    )]

    binary_pass = sum(1 for r in binary_results if r.get("score", 0) >= 1)
    binary_total = len(binary_results)

    likert_scores = [r.get("score", 0) for r in likert_results if r.get("score", -1) > 0]
    likert_mean = sum(likert_scores) / len(likert_scores) if likert_scores else 0
    likert_min = min(likert_scores) if likert_scores else 0
    likert_max = max(likert_scores) if likert_scores else 0
    likert_below = sum(1 for s in likert_scores if s < 4)

    all_failures = failures + below_threshold
    overall = "PASSED" if not all_failures else "FAILED"

    # Build report
    lines = [
        f"# Research Agent Experiment Report",
        f"",
        f"- **Experiment:** {experiment_name}",
        f"- **Timestamp:** {timestamp}",
        f"- **Scenario:** {scenario}",
        f"- **Mode:** {mode}",
    ]

    if extra_metadata:
        for key, value in extra_metadata.items():
            lines.append(f"- **{key}:** {value}")

    lines.extend([
        f"",
        f"## Summary",
        f"",
        f"- **Binary:** {binary_pass}/{binary_total} passed",
        f"- **Likert:** mean {likert_mean:.1f}, min {likert_min}, max {likert_max}, below threshold: {likert_below}",
        f"- **Overall:** {overall}",
        f"- **Total evals:** {len(results)} ({len(failures)} failed, {len(below_threshold)} below threshold, {len(passing)} passed, {len(deferred)} deferred)",
    ])

    # Failures section
    if all_failures:
        lines.extend([
            f"",
            f"## Failures (action required)",
            f"",
        ])
        for result in sorted(all_failures, key=lambda r: r.get("score", 99)):
            lines.append(_format_failure_block(result))
            lines.append("")

    # Passing evals
    if passing:
        lines.extend([
            f"## Passing Evals",
            f"",
            f"| Eval ID | Score | Confidence | Key finding |",
            f"|---------|-------|------------|-------------|",
        ])
        for result in sorted(passing, key=lambda r: r.get("eval_id", r.get("key", ""))):
            lines.append(_format_passing_row(result))
        lines.append("")

    # Deferred evals
    if deferred:
        lines.extend([
            f"## Deferred Evals",
            f"",
        ])
        for result in deferred:
            eval_id = result.get("eval_id", result.get("key", ""))
            comment = _safe_str(result.get("comment", ""), 120)
            lines.append(f"- **{eval_id}:** {comment}")
        lines.append("")

    # Judge backend info (from first result that has details)
    for result in results:
        details = result.get("details", {})
        backend = details.get("judge_backend", {})
        if backend:
            provider = backend.get("provider", "unknown")
            model = backend.get("model", "unknown")
            lines.extend([
                f"## Judge Backend",
                f"",
                f"- **Provider:** {provider}",
                f"- **Model:** {model}",
                f"",
            ])
            break

    report = "\n".join(lines)

    # Save to disk
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
    report_dir: str | None = None,
) -> str:
    """Generate a report from LangSmith ExperimentResults.

    Iterates the ExperimentResults object (blocking=True) and extracts
    result["evaluation_results"]["results"] per the LangSmith SDK contract.

    Each EvaluationResult has: .key, .score, .comment, .source_run_id
    """
    results: list[dict] = []

    for result in experiment_results:
        eval_results = result.get("evaluation_results", {}).get("results", [])
        for eval_result in eval_results:
            key = getattr(eval_result, "key", None) or eval_result.get("key", "unknown")
            score = getattr(eval_result, "score", None)
            if score is None:
                score = eval_result.get("score", -1)
            comment = getattr(eval_result, "comment", None) or eval_result.get("comment", "")

            results.append({
                "eval_id": key,
                "score": score if score is not None else -1,
                "comment": comment or "",
                "reasoning": comment or "",
                "evidence": [],
                "confidence": "",
                "flags": [],
            })

    if not experiment_name:
        exp_name = getattr(experiment_results, "experiment_name", None)
        experiment_name = exp_name or f"langsmith-experiment-{int(time.time())}"

    return generate_report(
        results,
        experiment_name=experiment_name,
        mode="langsmith",
        report_dir=report_dir,
    )
