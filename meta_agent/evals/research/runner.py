"""Phased runner for the canonical 38 research-agent evaluators."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import sys
import time
from typing import Any

from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
from meta_agent.evals.research.synthetic_trace_adapter import load_calibration_dataset


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
) -> tuple[list[dict], bool]:
    evals_in_phase = {
        eval_id: meta for eval_id, meta in RESEARCH_EVAL_REGISTRY.items() if meta["phase"] == phase
    }

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


async def run_suite(
    data_dir: str,
    *,
    phases: list[str] | None = None,
    single_eval: str | None = None,
    verbose: bool = True,
    scenario: str = "golden_path",
    evaluation_mode: str = "calibration",
) -> dict:
    dataset = load_calibration_dataset(data_dir)
    if not dataset:
        return {"error": "No calibration data found", "passed": False}

    example_data = next((example for example in dataset if example["metadata"].get("scenario_type") == scenario), dataset[0])
    run = MockRun(example_data["outputs"])
    example = MockExample(example_data["inputs"], example_data["outputs"])

    if verbose:
        print(f"Scenario: {example_data['metadata'].get('scenario_name', 'unknown')}")
        print(f"Mode: {evaluation_mode}")
        print(f"Expected Likert range: {example_data['metadata'].get('expected_likert_range', 'N/A')}")
        print(f"Expected binary pass rate: {example_data['metadata'].get('expected_binary_pass_rate', 'N/A')}")

    if single_eval:
        meta = RESEARCH_EVAL_REGISTRY.get(single_eval)
        if not meta:
            return {"error": f"Unknown eval: {single_eval}", "passed": False}
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
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    phases = None if args.phase == "all" else [args.phase.upper()]

    result = asyncio.run(
        run_suite(
            args.data,
            phases=phases,
            single_eval=args.eval,
            scenario=args.scenario,
            evaluation_mode=args.mode,
            verbose=not args.quiet,
        )
    )
    if not result.get("passed", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
