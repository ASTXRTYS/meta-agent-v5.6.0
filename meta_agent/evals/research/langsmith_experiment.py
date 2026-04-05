"""Run research-agent experiments in LangSmith via the Python SDK.

This module supports two distinct use cases:

1. calibration mode
   - Replays synthetic outputs to validate evaluator behavior.
2. trace mode
   - Invokes the live research-agent runtime on synthetic *inputs* and scores
     the resulting trajectory/output.

Trace mode defaults to a single live input run (`trace_input_mode="single"`),
because replaying identical inputs across all synthetic scenarios is wasteful
unless repeated trials are explicitly intended.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import subprocess
import time
import tomllib
from typing import Any, Callable

from dotenv import load_dotenv
from langsmith import Client, evaluate

from meta_agent.evals.research.dataset_builder import build_dataset
from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
from meta_agent.evals.research.report import generate_report_from_experiment_results


PHASE_NUMBER = 3
PHASE_NAME = "RESEARCH"
DEFAULT_RESEARCH_EVAL_PROJECT = "meta-agent-research-evals"


def _load_env() -> None:
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    load_dotenv(os.path.join(repo_root, ".env"))


def _repo_root() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "..")


def _canonical_examples(datasets_dir: str) -> list[dict[str, Any]]:
    examples = build_dataset(datasets_dir)
    canonical: list[dict[str, Any]] = []
    for example in examples:
        inputs = dict(example["inputs"])
        inputs["_target_outputs"] = example["outputs"]
        canonical.append(
            {
                "inputs": inputs,
                "outputs": {
                    "expected_evals": example["outputs"].get("expected_evals", {}),
                    "scenario_type": example["metadata"].get("scenario_type"),
                },
                "metadata": example.get("metadata", {}),
            }
        )
    return canonical


def _example_key_by_inputs(example: dict[str, Any]) -> str:
    """Return a deterministic key for input payload deduplication."""
    return json.dumps(example.get("inputs", {}), sort_keys=True, separators=(",", ":"), default=str)


def _trace_examples(
    datasets_dir: str,
    *,
    trace_input_mode: str = "single",
    trace_scenario: str = "golden_path",
    trace_trials: int = 1,
) -> list[dict[str, Any]]:
    """Build trace-mode examples from synthetic inputs only.

    Unlike calibration mode, trace mode does not need synthetic expected
    outputs. This function produces examples with empty outputs so evaluators
    score live runtime behavior only.
    """
    if trace_trials < 1:
        raise ValueError(f"trace_trials must be >= 1 (got {trace_trials})")

    base_examples = build_dataset(datasets_dir)
    if not base_examples:
        return []

    selected: list[dict[str, Any]]
    if trace_input_mode == "single":
        selected = [
            next(
                (ex for ex in base_examples if ex.get("metadata", {}).get("scenario_type") == trace_scenario),
                base_examples[0],
            )
        ]
    elif trace_input_mode == "dedup":
        seen: set[str] = set()
        selected = []
        for example in base_examples:
            key = _example_key_by_inputs(example)
            if key in seen:
                continue
            seen.add(key)
            selected.append(example)
    elif trace_input_mode == "all":
        selected = list(base_examples)
    else:
        raise ValueError(f"Unknown trace_input_mode: {trace_input_mode}")

    trace_examples: list[dict[str, Any]] = []
    for example in selected:
        metadata = dict(example.get("metadata", {}))
        source_scenario = metadata.get("scenario_type", "unknown")
        for trial_index in range(1, trace_trials + 1):
            run_metadata = {
                **metadata,
                "source_scenario_type": source_scenario,
                "trace_input_mode": trace_input_mode,
                "trace_trial_index": trial_index,
                "trace_total_trials": trace_trials,
            }
            trace_examples.append(
                {
                    "inputs": dict(example.get("inputs", {})),
                    "outputs": {},
                    "metadata": run_metadata,
                }
            )
    return trace_examples


def _run_target(inputs: dict[str, Any]) -> dict[str, Any]:
    """Calibration target: passthrough synthetic outputs."""
    return inputs["_target_outputs"]


def _run_target_live(inputs: dict[str, Any]) -> dict[str, Any]:
    """Trace target: invoke the real research-agent runtime."""
    from meta_agent.subagents.research_agent import run_research_agent_live

    return run_research_agent_live(inputs)


def _is_hitl_interrupt(exc: BaseException) -> bool:
    """Return True when an exception represents a LangGraph HITL interrupt."""
    return "interrupt" in type(exc).__name__.lower()


def _run_target_live_pause_after_decomposition(inputs: dict[str, Any]) -> dict[str, Any]:
    """Trace target that pauses after decomposition while still using LangSmith evaluate."""
    from meta_agent.evals.research.run_single_trace_experiment import (
        DECOMPOSITION_CHECKPOINT_SUMMARY,
    )
    from meta_agent.subagents.research_agent import (
        _default_eval_project_dir,
        _localize_workspace_path,
        build_research_agent_initial_message,
        get_research_runtime_paths,
        run_research_agent,
    )

    project_id = str(inputs.get("project_id", "meta-agent"))
    project_dir = str(
        inputs.get("project_dir")
        or inputs.get("config", {}).get("project_dir")
        or _default_eval_project_dir(project_id)
    )
    prd_path = inputs.get("prd_path")
    if prd_path:
        prd_path = _localize_workspace_path(
            str(prd_path),
            project_dir=project_dir,
            project_id=project_id,
        ) or None
    eval_suite_path = inputs.get("eval_suite_path")
    if eval_suite_path:
        eval_suite_path = _localize_workspace_path(
            str(eval_suite_path),
            project_dir=project_dir,
            project_id=project_id,
        ) or None

    paths = get_research_runtime_paths(project_dir, project_id)
    resolved_prd = prd_path or paths.prd_path
    resolved_eval = eval_suite_path or paths.eval_suite_path
    extra_state = {
        **(inputs.get("extra_state") or {}),
        "auto_approve_hitl": False,
        "messages": [
            build_research_agent_initial_message(
                project_dir=project_dir,
                project_id=project_id,
                prd_path=resolved_prd,
                eval_suite_path=resolved_eval,
                checkpoint_artifact_path=paths.decomposition_path,
                checkpoint_summary=DECOMPOSITION_CHECKPOINT_SUMMARY,
            )
        ],
    }

    try:
        return run_research_agent(
            project_dir=project_dir,
            project_id=project_id,
            prd_path=resolved_prd,
            eval_suite_path=resolved_eval,
            prd_content=inputs.get("prd_content"),
            eval_suite_content=inputs.get("eval_suite_content"),
            skills_paths=inputs.get("skills_paths"),
            twitter_handles=inputs.get("twitter_handles"),
            extra_state=extra_state,
        )
    except BaseException as exc:  # noqa: BLE001
        if _is_hitl_interrupt(exc):
            return {
                "status": "interrupted",
                "trace_mode": "pause_after_decomposition",
                "project_id": project_id,
                "project_dir": project_dir,
                "artifact_path": paths.decomposition_path,
                "artifact_exists": os.path.isfile(paths.decomposition_path),
            }
        raise


def _make_langsmith_evaluator(eval_id: str, fn: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
    async def _ainvoke(run: Any, example: Any) -> dict[str, Any]:
        if inspect.iscoroutinefunction(fn):
            result = await fn(run, example)
        else:
            result = fn(run, example)
        details = result.get("details", {})
        judge_backend = details.get("judge_backend", {}) if isinstance(details, dict) else {}
        judge_trace = details.get("judge_trace", {}) if isinstance(details, dict) else {}
        return {
            "key": eval_id,
            "score": result.get("score"),
            "comment": result.get("comment", ""),
            "metadata": {
                "eval_id": eval_id,
                "eval_type": RESEARCH_EVAL_REGISTRY.get(eval_id, {}).get("type", "unknown"),
                "reasoning": result.get("reasoning", result.get("comment", "")),
                "evidence": result.get("evidence", []),
                "confidence": result.get("confidence", ""),
                "flags": result.get("flags", []),
                "details": details if isinstance(details, dict) else {},
                "judge_backend": judge_backend if isinstance(judge_backend, dict) else {},
                "judge_trace": judge_trace if isinstance(judge_trace, dict) else {},
                "judge_model": judge_trace.get("judge_model", "") if isinstance(judge_trace, dict) else "",
                "judge_category": judge_trace.get("category", "") if isinstance(judge_trace, dict) else "",
                "judge_scoring": judge_trace.get("scoring", "") if isinstance(judge_trace, dict) else "",
                "judge_evaluation_method": judge_trace.get("evaluation_method", "") if isinstance(judge_trace, dict) else "",
                "judge_thinking_type": judge_trace.get("thinking_type", "") if isinstance(judge_trace, dict) else "",
                "judge_streaming_used": judge_trace.get("streaming_used") if isinstance(judge_trace, dict) else None,
                "judge_tools_enabled": judge_trace.get("tools_enabled") if isinstance(judge_trace, dict) else None,
                "trace_context_source": details.get("trace_context_source", "") if isinstance(details, dict) else "",
            },
        }

    def _wrapper(run: Any, example: Any) -> dict[str, Any]:
        return asyncio.run(_ainvoke(run, example))

    _wrapper.__name__ = f"eval_{eval_id.lower().replace('-', '_')}"
    return _wrapper


def _current_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=_repo_root(),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _project_version() -> str:
    try:
        with open(os.path.join(_repo_root(), "pyproject.toml"), "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return "unknown"
    return str(data.get("project", {}).get("version", "unknown"))


def _registry_counts() -> dict[str, int]:
    deferred = sum(1 for meta in RESEARCH_EVAL_REGISTRY.values() if meta["type"] == "deferred")
    defined = len(RESEARCH_EVAL_REGISTRY)
    return {
        "defined_eval_count": defined,
        "active_eval_count": defined - deferred,
        "deferred_eval_count": deferred,
    }


def run_experiment(
    *,
    datasets_dir: str,
    dataset_prefix: str = "research-agent-eval-calibration",
    experiment_prefix: str = "research-eval-calibration",
    dataset_name: str | None = None,
    include_deferred: bool = False,
    report_dir: str | None = None,
    mode: str = "calibration",
    trace_input_mode: str = "single",
    trace_scenario: str = "golden_path",
    trace_trials: int = 1,
    trace_pause_after_decomposition: bool = False,
) -> dict[str, Any]:
    _load_env()
    if not os.getenv("LANGSMITH_PROJECT"):
        os.environ["LANGSMITH_PROJECT"] = os.getenv(
            "RESEARCH_EVAL_LANGSMITH_PROJECT",
            DEFAULT_RESEARCH_EVAL_PROJECT,
        )
    client = Client()

    timestamp = str(int(time.time()))
    mode_label = "trace" if mode == "trace" else "calibration"
    experiment_name = f"{experiment_prefix}-{mode_label}-{timestamp}"

    if mode == "trace":
        examples = _trace_examples(
            datasets_dir,
            trace_input_mode=trace_input_mode,
            trace_scenario=trace_scenario,
            trace_trials=trace_trials,
        )
    else:
        examples = _canonical_examples(datasets_dir)
    if not examples:
        raise RuntimeError(f"No examples found for mode={mode} in datasets_dir={datasets_dir}")

    scenario_types = sorted({example["metadata"].get("scenario_type", "unknown") for example in examples})
    source_scenarios = sorted({example["metadata"].get("source_scenario_type", "unknown") for example in examples})
    if dataset_name:
        dataset_source = "existing_langsmith_dataset"
    else:
        dataset_name = f"{dataset_prefix}-{mode_label}-{timestamp}"
        dataset_source = (
            "local_synthetic_materialization"
            if mode == "calibration"
            else "live_runtime_materialization"
        )
        client.create_dataset(dataset_name, description=f"Research agent {mode_label} dataset")
        client.create_examples(
            dataset_name=dataset_name,
            inputs=[example["inputs"] for example in examples],
            outputs=[example["outputs"] for example in examples],
            metadata=[example["metadata"] for example in examples],
        )

    evaluators = []
    for eval_id, meta in RESEARCH_EVAL_REGISTRY.items():
        if meta["type"] == "deferred" and not include_deferred:
            continue
        evaluators.append(_make_langsmith_evaluator(eval_id, meta["fn"]))

    registry_counts = _registry_counts()

    # Metadata distinguishes calibration from live runtime
    if mode == "trace":
        mode_metadata = {
            "mode": "trace",
            "source": "live_runtime",
            "trace_input_mode": trace_input_mode,
            "trace_scenario": trace_scenario,
            "trace_trials": trace_trials,
            "trace_example_count": len(examples),
            "trace_source_scenarios": ", ".join(source_scenarios),
            "trace_pause_after_decomposition": trace_pause_after_decomposition,
        }
    else:
        mode_metadata = {"mode": "calibration", "source": "synthetic"}

    evaluate_metadata = {
        "phase_number": PHASE_NUMBER,
        "phase_name": PHASE_NAME,
        "timestamp": timestamp,
        "commit_hash": _current_commit_hash(),
        "agent_version": _project_version(),
        "dataset_name": dataset_name,
        "dataset_source": dataset_source,
        "include_deferred": include_deferred,
        "active_eval_count": registry_counts["active_eval_count"],
        "deferred_eval_count": registry_counts["deferred_eval_count"],
        **mode_metadata,
    }

    # Select target function based on mode
    if mode == "trace":
        target_fn = (
            _run_target_live_pause_after_decomposition
            if trace_pause_after_decomposition
            else _run_target_live
        )
    else:
        target_fn = _run_target

    results = evaluate(
        target_fn,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_name,
        metadata=evaluate_metadata,
        blocking=True,
    )

    if report_dir is None:
        report_dir = os.path.join(_repo_root(), "workspace", "projects", "meta-agent", "evals", "reports")

    generate_report_from_experiment_results(
        results,
        experiment_name=experiment_name,
        scenario="multi_scenario_calibration" if mode == "calibration" else "live_trace",
        report_dir=report_dir,
        extra_metadata={
            **evaluate_metadata,
            "scenario_types": ", ".join(scenario_types),
            "source_scenarios": ", ".join(source_scenarios),
            "defined_eval_count": registry_counts["defined_eval_count"],
        },
    )

    return {
        "dataset_name": dataset_name,
        "experiment_name": results.experiment_name,
        "experiment_url": results.url,
        "mode": mode_label,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LangSmith calibration experiment for research evaluators")
    parser.add_argument("--datasets-dir", default="datasets")
    parser.add_argument("--dataset-prefix", default="research-agent-eval-calibration")
    parser.add_argument(
        "--dataset-name",
        default=None,
        help="Reuse an existing LangSmith dataset instead of materializing a timestamped dataset",
    )
    parser.add_argument("--experiment-prefix", default="research-eval-calibration")
    parser.add_argument("--include-deferred", action="store_true")
    parser.add_argument(
        "--mode",
        default="calibration",
        choices=["calibration", "trace"],
        help="Experiment mode: calibration (synthetic replay) or trace (live runtime).",
    )
    parser.add_argument(
        "--trace-input-mode",
        default="single",
        choices=["single", "dedup", "all"],
        help=(
            "Trace-mode input selection strategy: single=one scenario input "
            "(default), dedup=one run per unique input payload, all=all rows."
        ),
    )
    parser.add_argument(
        "--trace-scenario",
        default="golden_path",
        help="When --trace-input-mode=single, pick this scenario's input (defaults to golden_path).",
    )
    parser.add_argument(
        "--trace-trials",
        type=int,
        default=1,
        help="Repeat each selected trace input this many times (for variance studies).",
    )
    parser.add_argument(
        "--trace-pause-after-decomposition",
        action="store_true",
        help=(
            "In trace mode, instruct the research agent to request approval "
            "immediately after writing the decomposition while still running "
            "through the LangSmith experiment harness."
        ),
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory to save markdown experiment report (default: .agents/pm/projects/meta-agent/evals/reports/)",
    )
    args = parser.parse_args()

    result = run_experiment(
        datasets_dir=args.datasets_dir,
        dataset_prefix=args.dataset_prefix,
        experiment_prefix=args.experiment_prefix,
        dataset_name=args.dataset_name,
        include_deferred=args.include_deferred,
        report_dir=args.report_dir,
        mode=args.mode,
        trace_input_mode=args.trace_input_mode,
        trace_scenario=args.trace_scenario,
        trace_trials=args.trace_trials,
        trace_pause_after_decomposition=args.trace_pause_after_decomposition,
    )
    print(result)


if __name__ == "__main__":
    main()
