"""Phased runner for the canonical 38 research-agent evaluators."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import sys
import time
from typing import Any

from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
from meta_agent.evals.research.report import generate_report
from meta_agent.evals.research.synthetic_trace_adapter import load_calibration_dataset


# ---------------------------------------------------------------------------
# Trace-mode phase slices (per development plan section 3.2.8)
# ---------------------------------------------------------------------------
# Phase A: after protocol phases 1-2  (PRD consumption + decomposition) — 9 evals
# Phase B: after protocol phases 3-4  (skills + sub-agent delegation) — 9 evals
# Phase C: after protocol phases 5-8  (gap remediation + HITL + deep-dive + SME) — 9 evals
# Phase all: after protocol phases 9-10 (full suite)
# Per development plan Section 3.2.8
EVAL_PHASE_SLICES: dict[str, list[str]] = {
    "A": [
        "RS-001", "RS-002", "RS-003", "RS-004",
        "RINFRA-001", "RINFRA-002",
        "RB-001", "RB-002", "RB-003",
    ],
    "B": [
        "RB-004", "RB-007", "RB-008", "RB-009", "RB-010",
        "RQ-007", "RQ-008", "RQ-009", "RQ-010",
    ],
    "C": [
        "RB-005", "RB-006", "RB-011",
        "RQ-006", "RQ-012", "RQ-013",
        "RR-001", "RR-002", "RR-003",
    ],
}

# Convenience aliases
PHASE_A_EVALS = EVAL_PHASE_SLICES["A"]
PHASE_B_EVALS = EVAL_PHASE_SLICES["B"]


def _get_phase_slice_eval_ids(phase_slice: str) -> set[str] | None:
    """Return the eval IDs for a trace-mode phase slice, or None for 'all'."""
    if phase_slice.upper() == "ALL":
        return None
    phase_slice = phase_slice.upper()
    if phase_slice == "C":
        return set(EVAL_PHASE_SLICES["C"])
    ids = EVAL_PHASE_SLICES.get(phase_slice)
    if ids is not None:
        return set(ids)
    return None


class MockRun:
    def __init__(self, outputs: dict):
        self.outputs = outputs


class MockExample:
    def __init__(self, inputs: dict, outputs: dict):
        self.inputs = inputs
        self.outputs = outputs


PHASE_GATES = {
    "A": {
        "description": "Infrastructure / State gates",
        "gate": "all_binary_pass",
        "required_evals": ["RINFRA-001", "RINFRA-002", "RS-001", "RS-002", "RS-003", "RS-004"],
    },
    "B": {
        "description": "Behavioral gates",
        "gate": "all_binary_pass",
        "required_evals": [
            "RB-001",
            "RB-002",
            "RB-003",
            "RB-004",
            "RB-005",
            "RB-006",
            "RB-007",
            "RB-008",
            "RB-009",
            "RB-010",
            "RB-011",
        ],
    },
    "C": {
        "description": "Quality / Reasoning Likert evals",
        "gate": "all_likert_gte_4",
        "required_evals": [
            "RINFRA-003",
            "RINFRA-004",
            "RQ-001",
            "RQ-002",
            "RQ-003",
            "RQ-004",
            "RQ-005",
            "RQ-006",
            "RQ-007",
            "RQ-008",
            "RQ-009",
            "RQ-010",
            "RQ-011",
            "RQ-012",
            "RQ-013",
            "RR-001",
            "RR-002",
            "RR-003",
        ],
    },
    "D": {
        "description": "Integration evals",
        "gate": "informational",
        "required_evals": ["RI-001", "RI-002", "RI-003"],
    },
}


def _registry_counts() -> dict[str, int]:
    deferred = sum(1 for meta in RESEARCH_EVAL_REGISTRY.values() if meta["type"] == "deferred")
    defined = len(RESEARCH_EVAL_REGISTRY)
    return {
        "defined_eval_count": defined,
        "active_eval_count": defined - deferred,
        "deferred_eval_count": deferred,
    }


async def _run_eval(eval_id: str, fn: Any, run: MockRun, example: MockExample) -> dict:
    try:
        if inspect.iscoroutinefunction(fn):
            result = await fn(run, example)
        else:
            result = fn(run, example)
        return {"eval_id": eval_id, **result}
    except Exception as exc:
        return {
            "eval_id": eval_id,
            "score": -1,
            "comment": f"Error: {exc}",
            "reasoning": f"Error: {exc}",
            "evidence": [],
            "confidence": "LOW",
            "flags": ["runner_error"],
        }


def _print_result(result: dict, eval_type: str) -> None:
    eval_id = result["eval_id"]
    score = result["score"]
    comment = result.get("comment", "")[:120]
    if score == -1:
        status = "DEFER"
    elif eval_type == "llm_likert" or eval_id == "RQ-004":
        status = f"SCORE={score}" + (" PASS" if score >= 4 else " FAIL")
    else:
        status = "PASS" if score >= 1 else "FAIL"
    print(f"  {eval_id:12s} [{eval_type:12s}] {status:12s}  {comment}")


def _expected_match(result: dict, expected: Any) -> bool:
    score = result.get("score", -1)
    if expected == "deferred":
        return score == -1
    if isinstance(expected, int):
        return score == expected
    if expected == "pass":
        return score >= 1
    if expected == "fail":
        return score == 0
    return False


def _phase_required_results(phase: str, results: list[dict]) -> list[dict]:
    required = set(PHASE_GATES.get(phase, {}).get("required_evals", []))
    return [result for result in results if result["eval_id"] in required]


def _check_gate(phase: str, results: list[dict], *, evaluation_mode: str) -> bool:
    if evaluation_mode == "calibration":
        return True

    gate_info = PHASE_GATES.get(phase, {})
    gate_type = gate_info.get("gate", "informational")
    required_results = _phase_required_results(phase, results)

    if gate_type == "informational":
        return True
    if not required_results:
        return False
    if gate_type == "all_binary_pass":
        return all(result["score"] >= 1 for result in required_results)
    if gate_type == "all_likert_gte_4":
        return all(result["score"] >= 4 for result in required_results)
    return True


async def run_phase(
    phase: str,
    run: MockRun,
    example: MockExample,
    *,
    verbose: bool = True,
    evaluation_mode: str = "calibration",
    slice_filter: set[str] | None = None,
) -> tuple[list[dict], bool]:
    evals_in_phase = {
        eval_id: meta for eval_id, meta in RESEARCH_EVAL_REGISTRY.items() if meta["phase"] == phase
    }
    # Apply trace-mode phase slice filter when provided
    if slice_filter is not None:
        evals_in_phase = {eid: m for eid, m in evals_in_phase.items() if eid in slice_filter}

    if verbose:
        gate_info = PHASE_GATES.get(phase, {})
        print(f"\n{'=' * 60}")
        print(f"PHASE {phase}: {gate_info.get('description', 'Unknown')} ({len(evals_in_phase)} evals)")
        print(f"{'=' * 60}")

    deterministic = {eval_id: meta for eval_id, meta in evals_in_phase.items() if meta["type"] == "deterministic"}
    nondeterministic = {eval_id: meta for eval_id, meta in evals_in_phase.items() if meta["type"] != "deterministic"}

    results: list[dict] = []
    for eval_id, meta in sorted(deterministic.items()):
        result = await _run_eval(eval_id, meta["fn"], run, example)
        results.append(result)
        if verbose:
            _print_result(result, meta["type"])

    if nondeterministic:
        tasks = [_run_eval(eval_id, meta["fn"], run, example) for eval_id, meta in sorted(nondeterministic.items())]
        for result in await asyncio.gather(*tasks):
            results.append(result)
            if verbose:
                _print_result(result, nondeterministic[result["eval_id"]]["type"])

    gate_passed = _check_gate(phase, results, evaluation_mode=evaluation_mode)
    if verbose:
        status = "PASSED" if gate_passed else "FAILED"
        print(f"\n  Phase {phase} gate: {status}")
    return results, gate_passed


def _calibration_summary(all_results: list[dict], example_data: dict[str, Any]) -> dict[str, Any]:
    expected = example_data.get("outputs", {}).get("expected_evals", {})
    comparisons = []
    for result in all_results:
        eval_id = result["eval_id"]
        if eval_id not in expected:
            continue
        matched = _expected_match(result, expected[eval_id])
        comparisons.append({"eval_id": eval_id, "expected": expected[eval_id], "actual": result["score"], "matched": matched})
    matched_count = sum(1 for comparison in comparisons if comparison["matched"])
    return {
        "expected_total": len(comparisons),
        "matched": matched_count,
        "mismatches": [comparison for comparison in comparisons if not comparison["matched"]],
        "passed": matched_count == len(comparisons),
    }


def _build_trace_mode_example(inputs: dict[str, Any]) -> tuple[MockRun, MockExample]:
    """Invoke the live research-agent runtime and build evaluator inputs."""
    from meta_agent.subagents.research_agent import run_research_agent_live

    live_outputs = run_research_agent_live(inputs)
    return MockRun(live_outputs), MockExample(inputs, live_outputs)


async def run_suite(
    data_dir: str,
    *,
    phases: list[str] | None = None,
    single_eval: str | None = None,
    verbose: bool = True,
    scenario: str = "golden_path",
    evaluation_mode: str = "calibration",
    phase_slice: str = "all",
) -> dict:
    dataset = load_calibration_dataset(data_dir)
    if not dataset:
        return {"error": "No calibration data found", "passed": False}

    example_data = next((example for example in dataset if example["metadata"].get("scenario_type") == scenario), dataset[0])

    if evaluation_mode == "trace":
        # Trace mode: invoke the live research-agent runtime
        if verbose:
            print(f"Scenario inputs: {scenario}")
            print(f"Mode: trace (live runtime)")
        run, example = _build_trace_mode_example(example_data["inputs"])
    else:
        # Calibration mode: use synthetic replay (UNCHANGED)
        run = MockRun(example_data["outputs"])
        example = MockExample(example_data["inputs"], example_data["outputs"])

    if verbose:
        print(f"Scenario: {example_data['metadata'].get('scenario_name', 'unknown')}")
        print(f"Mode: {evaluation_mode}")
        print(f"Expected Likert range: {example_data['metadata'].get('expected_likert_range', 'N/A')}")
        print(f"Expected binary pass rate: {example_data['metadata'].get('expected_binary_pass_rate', 'N/A')}")

    # Resolve phase slice filter for trace mode
    slice_filter = _get_phase_slice_eval_ids(phase_slice) if evaluation_mode == "trace" else None

    if single_eval:
        meta = RESEARCH_EVAL_REGISTRY.get(single_eval)
        if not meta:
            return {"error": f"Unknown eval: {single_eval}", "passed": False}
        if slice_filter is not None and single_eval not in slice_filter:
            return {"error": f"Eval {single_eval} not in phase slice {phase_slice}", "passed": False}
        result = await _run_eval(single_eval, meta["fn"], run, example)
        if verbose:
            _print_result(result, meta["type"])
        passed = result["score"] >= 1 if evaluation_mode == "trace" else _expected_match(
            result, example_data["outputs"].get("expected_evals", {}).get(single_eval)
        )
        return {"results": [result], "passed": passed}

    target_phases = phases or ["A", "B", "C", "D"]
    all_results: list[dict] = []
    overall_passed = True

    start = time.time()
    for phase in target_phases:
        results, gate_passed = await run_phase(
            phase,
            run,
            example,
            verbose=verbose,
            evaluation_mode=evaluation_mode,
            slice_filter=slice_filter,
        )
        all_results.extend(results)
        if evaluation_mode == "trace" and not gate_passed:
            overall_passed = False
            if phase in ("A", "B"):
                if verbose:
                    print(f"\n  ABORTING: Phase {phase} gate failed. Downstream phases skipped.")
                break
    elapsed = time.time() - start

    summary: dict[str, Any] = {
        "results": all_results,
        "elapsed_seconds": elapsed,
    }

    if evaluation_mode == "calibration":
        calibration = _calibration_summary(all_results, example_data)
        overall_passed = calibration["passed"]
        summary["calibration"] = calibration
    else:
        integration_failures = [
            result
            for result in all_results
            if result["eval_id"] in {"RI-002", "RI-003"} and result["score"] == 0
        ]
        if integration_failures:
            overall_passed = False
        summary["integration_failures"] = integration_failures
        summary["phase_slice"] = phase_slice

    summary["passed"] = overall_passed

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"SUMMARY ({elapsed:.1f}s)")
        print(f"{'=' * 60}")
        if evaluation_mode == "calibration":
            calibration = summary["calibration"]
            print(f"  Calibration agreement: {calibration['matched']}/{calibration['expected_total']}")
            if calibration["mismatches"]:
                print("  Mismatches:")
                for mismatch in calibration["mismatches"][:10]:
                    print(f"    - {mismatch['eval_id']}: expected {mismatch['expected']} got {mismatch['actual']}")
        else:
            deterministic_pass = sum(
                1
                for result in all_results
                if result["score"] >= 1 and RESEARCH_EVAL_REGISTRY.get(result["eval_id"], {}).get("type") == "deterministic"
            )
            deterministic_total = sum(
                1 for result in all_results if RESEARCH_EVAL_REGISTRY.get(result["eval_id"], {}).get("type") == "deterministic"
            )
            print(f"  Deterministic: {deterministic_pass}/{deterministic_total} passed")
            if phase_slice != "all":
                print(f"  Phase slice: {phase_slice}")
        print(f"  Overall: {'PASSED' if overall_passed else 'FAILED'}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Research agent eval suite runner")
    parser.add_argument("--data", default="datasets", help="Path to datasets directory")
    parser.add_argument("--phase", default="all", help="Phase to run: A, B, C, D, or all")
    parser.add_argument("--eval", default=None, help="Run a single eval by ID")
    parser.add_argument(
        "--scenario",
        default="golden_path",
        choices=[
            "golden_path",
            "silver_path",
            "bronze_path",
            "citation_hallucination_failure",
            "hitl_subagent_failure",
        ],
    )
    parser.add_argument("--mode", default="calibration", choices=["calibration", "trace"])
    parser.add_argument(
        "--phase-slice",
        default="all",
        choices=["A", "B", "C", "all"],
        help="Trace-mode phase slice: A, B, C, or all (default: all). Only used when --mode=trace.",
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory to save markdown experiment report (default: .agents/pm/projects/meta-agent/evals/reports/)",
    )
    args = parser.parse_args()

    phases = None if args.phase == "all" else [args.phase.upper()]

    result = asyncio.run(
        run_suite(
            args.data,
            phases=phases,
            single_eval=args.eval,
            scenario=args.scenario,
            evaluation_mode=args.mode,
            phase_slice=args.phase_slice if args.mode == "trace" else "all",
            verbose=not args.quiet,
        )
    )

    report_dir = args.report_dir
    if report_dir is None:
        repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        report_dir = os.path.join(repo_root, "workspace", "projects", "meta-agent", "evals", "reports")

    results_list = result.get("results", [])
    if results_list:
        phase_label = args.phase if args.phase != "all" else "all"
        experiment_name = f"research-{args.mode}-phase-{phase_label}-{args.scenario}"
        registry_counts = _registry_counts()
        generate_report(
            results_list,
            experiment_name=experiment_name,
            scenario=args.scenario,
            mode=args.mode,
            report_dir=report_dir,
            extra_metadata={
                "phase_number": 3,
                "phase_name": "RESEARCH",
                "phases": phase_label,
                "data_dir": args.data,
                "dataset_source": "local_synthetic_trace_adapter",
                **registry_counts,
            },
        )

    if not result.get("passed", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
