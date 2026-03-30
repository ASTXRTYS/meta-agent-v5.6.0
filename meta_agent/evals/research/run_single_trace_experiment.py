"""Run a single-input live trace experiment via LangSmith.

Unlike the calibration experiment (which tests 5 synthetic scenarios with
different outputs), this script runs the real research-agent exactly ONCE
against the canonical inputs and evaluates the live output with all 37
active evaluators.
"""

from __future__ import annotations

import os
import subprocess
import time
import tomllib
from typing import Any

from dotenv import load_dotenv
from langsmith import Client, evaluate

from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
from meta_agent.evals.research.langsmith_experiment import _make_langsmith_evaluator
from meta_agent.evals.research.report import generate_report_from_experiment_results
from meta_agent.evals.research.synthetic_trace_adapter import load_calibration_dataset


PHASE_NUMBER = 3
PHASE_NAME = "RESEARCH"


def _load_env() -> None:
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    load_dotenv(os.path.join(repo_root, ".env"))


def _repo_root() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "..")


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


def _run_target_live(inputs: dict[str, Any]) -> dict[str, Any]:
    """Invoke the real research-agent runtime."""
    from meta_agent.subagents.research_agent import run_research_agent_live

    return run_research_agent_live(inputs)


def run_single_trace_experiment(
    *,
    datasets_dir: str = "datasets",
    experiment_prefix: str = "research-live-trace",
    include_deferred: bool = False,
    report_dir: str | None = None,
) -> dict[str, Any]:
    """Run a single-input live trace experiment."""
    _load_env()
    client = Client()

    timestamp = str(int(time.time()))
    experiment_name = f"{experiment_prefix}-{timestamp}"

    # Load dataset and take ONLY the first example (inputs are identical)
    dataset = load_calibration_dataset(datasets_dir)
    if not dataset:
        raise RuntimeError("No calibration data found in datasets/")

    example = dataset[0]  # golden_path — inputs are the same across all scenarios
    inputs = dict(example["inputs"])

    # Create a single-example LangSmith dataset
    dataset_name = f"research-live-trace-{timestamp}"
    client.create_dataset(dataset_name, description="Single-input research agent live trace")
    client.create_examples(
        dataset_name=dataset_name,
        inputs=[inputs],
        outputs=[{}],  # No expected outputs — evaluators judge the live output
        metadata=[{"scenario_type": "live_trace", "source_scenario": "golden_path"}],
    )

    # Build evaluator list
    evaluators = []
    for eval_id, meta in RESEARCH_EVAL_REGISTRY.items():
        if meta["type"] == "deferred" and not include_deferred:
            continue
        evaluators.append(_make_langsmith_evaluator(eval_id, meta["fn"]))

    deferred_count = sum(1 for m in RESEARCH_EVAL_REGISTRY.values() if m["type"] == "deferred")
    active_count = len(RESEARCH_EVAL_REGISTRY) - deferred_count

    metadata = {
        "phase_number": PHASE_NUMBER,
        "phase_name": PHASE_NAME,
        "timestamp": timestamp,
        "commit_hash": _current_commit_hash(),
        "agent_version": _project_version(),
        "dataset_name": dataset_name,
        "dataset_source": "single_input_live_trace",
        "mode": "trace",
        "source": "live_runtime",
        "active_eval_count": active_count,
        "deferred_eval_count": deferred_count,
        "include_deferred": include_deferred,
    }

    print(f"Dataset: {dataset_name} (1 example)")
    print(f"Evaluators: {active_count} active, {deferred_count} deferred")
    print(f"Experiment: {experiment_name}")
    print("Invoking real research-agent runtime...")

    results = evaluate(
        _run_target_live,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_name,
        metadata=metadata,
        blocking=True,
    )

    if report_dir is None:
        report_dir = os.path.join(_repo_root(), "workspace", "projects", "meta-agent", "evals", "reports")

    generate_report_from_experiment_results(
        results,
        experiment_name=experiment_name,
        scenario="live_trace",
        report_dir=report_dir,
        extra_metadata={
            **metadata,
            "defined_eval_count": len(RESEARCH_EVAL_REGISTRY),
        },
    )

    return {
        "dataset_name": dataset_name,
        "experiment_name": results.experiment_name,
        "mode": "trace",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Single-input live trace experiment")
    parser.add_argument("--datasets-dir", default="datasets")
    parser.add_argument("--experiment-prefix", default="research-live-trace")
    parser.add_argument("--include-deferred", action="store_true")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    result = run_single_trace_experiment(
        datasets_dir=args.datasets_dir,
        experiment_prefix=args.experiment_prefix,
        include_deferred=args.include_deferred,
        report_dir=args.report_dir,
    )
    print(result)
