"""Run a single-input live trace experiment.

Default behavior is a thin wrapper over the generic experiment harness in
`langsmith_experiment.run_experiment`, pinned to:
- mode="trace"
- trace_input_mode="single"
"""

from __future__ import annotations

from typing import Any

from meta_agent.evals.research.langsmith_experiment import run_experiment


DECOMPOSITION_CHECKPOINT_SUMMARY = (
    "Research decomposition ready for review before skills consultation and "
    "outward research."
)


def run_single_trace_experiment(
    *,
    datasets_dir: str = "datasets",
    experiment_prefix: str = "research-live-trace",
    include_deferred: bool = False,
    report_dir: str | None = None,
    trace_scenario: str = "golden_path",
    trace_trials: int = 1,
    pause_after_decomposition: bool = False,
) -> dict[str, Any]:
    """Run a single-input live trace experiment."""
    return run_experiment(
        datasets_dir=datasets_dir,
        dataset_prefix="research-live-trace",
        experiment_prefix=experiment_prefix,
        include_deferred=include_deferred,
        report_dir=report_dir,
        mode="trace",
        trace_input_mode="single",
        trace_scenario=trace_scenario,
        trace_trials=trace_trials,
        trace_pause_after_decomposition=pause_after_decomposition,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Single-input live trace experiment")
    parser.add_argument("--datasets-dir", default="datasets")
    parser.add_argument("--experiment-prefix", default="research-live-trace")
    parser.add_argument("--include-deferred", action="store_true")
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--trace-scenario", default="golden_path")
    parser.add_argument("--trace-trials", type=int, default=1)
    parser.add_argument(
        "--pause-after-decomposition",
        action="store_true",
        help=(
            "Run the single-trace LangSmith experiment with a decomposition "
            "approval checkpoint before outward research."
        ),
    )
    args = parser.parse_args()

    result = run_single_trace_experiment(
        datasets_dir=args.datasets_dir,
        experiment_prefix=args.experiment_prefix,
        include_deferred=args.include_deferred,
        report_dir=args.report_dir,
        trace_scenario=args.trace_scenario,
        trace_trials=args.trace_trials,
        pause_after_decomposition=args.pause_after_decomposition,
    )
    print(result)
