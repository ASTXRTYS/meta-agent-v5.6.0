"""Run research-eval calibration experiments in LangSmith via the Python SDK."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import time
from typing import Any, Callable

from dotenv import load_dotenv
from langsmith import Client, evaluate

from meta_agent.evals.research.dataset_builder import build_dataset
from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
from meta_agent.evals.research.report import generate_report_from_experiment_results


def _load_env() -> None:
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    load_dotenv(os.path.join(repo_root, ".env"))


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
    return inputs["_target_outputs"]


def _make_langsmith_evaluator(eval_id: str, fn: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
    async def _ainvoke(run: Any, example: Any) -> dict[str, Any]:
        if inspect.iscoroutinefunction(fn):
            result = await fn(run, example)
        else:
            result = fn(run, example)
        return {
            "score": result.get("score"),
            "comment": result.get("comment", ""),
        }

    def _wrapper(run: Any, example: Any) -> dict[str, Any]:
        return asyncio.run(_ainvoke(run, example))

    _wrapper.__name__ = f"eval_{eval_id.lower().replace('-', '_')}"
    return _wrapper


def run_experiment(
    *,
    datasets_dir: str,
    dataset_prefix: str = "research-agent-eval-calibration",
    experiment_prefix: str = "research-eval-calibration",
    include_deferred: bool = False,
    report_dir: str | None = None,
) -> dict[str, Any]:
    _load_env()
    client = Client()

    timestamp = str(int(time.time()))
    dataset_name = f"{dataset_prefix}-{timestamp}"
    experiment_name = f"{experiment_prefix}-{timestamp}"

    examples = _canonical_examples(datasets_dir)
    client.create_dataset(dataset_name, description="Research agent calibration dataset")
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

    results = evaluate(
        _run_target,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_name,
        blocking=True,
    )

    if report_dir is None:
        repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        report_dir = os.path.join(repo_root, "workspace", "projects", "meta-agent", "evals", "reports")

    generate_report_from_experiment_results(
        results,
        experiment_name=experiment_name,
        report_dir=report_dir,
    )

    return {
        "dataset_name": dataset_name,
        "experiment_name": results.experiment_name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LangSmith calibration experiment for research evaluators")
    parser.add_argument("--datasets-dir", default="datasets")
    parser.add_argument("--dataset-prefix", default="research-agent-eval-calibration")
    parser.add_argument("--experiment-prefix", default="research-eval-calibration")
    parser.add_argument("--include-deferred", action="store_true")
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
        include_deferred=args.include_deferred,
        report_dir=args.report_dir,
    )
    print(result)


if __name__ == "__main__":
    main()
