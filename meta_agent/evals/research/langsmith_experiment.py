"""Run research-eval calibration experiments in LangSmith via the Python SDK."""

from __future__ import annotations

import argparse
import asyncio
import inspect
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


def _run_target(inputs: dict[str, Any]) -> dict[str, Any]:
    """Calibration target: passthrough synthetic outputs."""
    return inputs["_target_outputs"]


def _run_target_live(inputs: dict[str, Any]) -> dict[str, Any]:
    """Trace target: invoke the real research-agent runtime."""
    from meta_agent.subagents.research_agent import run_research_agent_live

    return run_research_agent_live(inputs)


def _make_langsmith_evaluator(eval_id: str, fn: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
    async def _ainvoke(run: Any, example: Any) -> dict[str, Any]:
        if inspect.iscoroutinefunction(fn):
            result = await fn(run, example)
        else:
            result = fn(run, example)
        details = result.get("details", {})
        judge_backend = details.get("judge_backend", {}) if isinstance(details, dict) else {}
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
) -> dict[str, Any]:
    _load_env()
    client = Client()

    timestamp = str(int(time.time()))
    mode_label = "trace" if mode == "trace" else "calibration"
    experiment_name = f"{experiment_prefix}-{mode_label}-{timestamp}"

    examples = _canonical_examples(datasets_dir)
    scenario_types = sorted({example["metadata"].get("scenario_type", "unknown") for example in examples})
    if dataset_name:
        dataset_source = "existing_langsmith_dataset"
    else:
        dataset_name = f"{dataset_prefix}-{mode_label}-{timestamp}"
        dataset_source = "local_synthetic_materialization" if mode == "calibration" else "live_runtime_materialization"
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
        mode_metadata = {"mode": "trace", "source": "live_runtime"}
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
    target_fn = _run_target_live if mode == "trace" else _run_target

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
            "defined_eval_count": registry_counts["defined_eval_count"],
        },
    )

    return {
        "dataset_name": dataset_name,
        "experiment_name": results.experiment_name,
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
        "--report-dir",
        default=None,
        help="Directory to save markdown experiment report (default: workspace/projects/meta-agent/evals/reports/)",
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
    )
    print(result)


if __name__ == "__main__":
    main()
