"""CLI runner for the orchestrator eval suite.

Spec References: Sections 15.14.6, 15.14.7

Supports:
- --all: Run all evals
- --category {infrastructure|pm_behavioral|stage_transitions|guardrails}
- --priority {P0|P1|P2}
- --eval {EVAL_ID}: Single eval
- --experiment "name": LangSmith experiment tracking
- --phase {0|1|2}: Run evals for a specific phase
- --data: Path to local synthetic data file
- --langsmith-dataset: LangSmith dataset name
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from meta_agent.evals.infrastructure.test_infra import (
    eval_infra_001_project_directory_structure,
    eval_infra_002_prd_artifact_path,
    eval_infra_003_prd_frontmatter_valid,
    eval_infra_004_prd_required_sections,
    eval_infra_005_eval_suite_artifact_exists,
    eval_infra_006_eval_suite_schema_valid,
    eval_infra_007_agents_md_created,
    eval_infra_008_dynamic_prompt_after_transition,
)
from meta_agent.evals.stage_transitions.test_stages import (
    eval_stage_001_valid_transitions_only,
    eval_stage_002_exit_conditions_met,
    eval_stage_003_eval_approval_is_hard_gate,
)
from meta_agent.evals.pm_behavioral.test_pm import (
    eval_pm_001_asks_clarifying_questions,
    eval_pm_002_does_not_delegate_prd,
    eval_pm_003_proposes_evals_with_rationale,
    eval_pm_004_pushes_back_on_no_evals,
    eval_pm_005_confirms_before_transition,
    eval_pm_006_no_premature_prd,
    eval_pm_007_evals_proposed_during_intake,
    eval_pm_008_elicitation_quality,
)
from meta_agent.evals.guardrails.test_guards import (
    eval_guard_001_no_eval_modification_during_execution,
    eval_guard_002_hitl_gates_enforced,
    eval_guard_003_agent_memory_isolation,
    eval_guard_004_file_operations_within_workspace,
)


# Eval registry organized by category and phase
EVAL_REGISTRY: dict[str, dict[str, Any]] = {
    # Phase 0 evals
    "INFRA-001": {
        "name": "Project Directory Structure Created Correctly",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 0,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_001_project_directory_structure,
        "input_type": "project_dir",
    },
    "INFRA-002": {
        "name": "PRD Artifact Written to Correct Path",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 0,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_002_prd_artifact_path,
        "input_type": "project_dir",
    },
    "INFRA-003": {
        "name": "PRD Has Valid YAML Frontmatter",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 0,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_003_prd_frontmatter_valid,
        "input_type": "project_dir",
    },
    "INFRA-004": {
        "name": "PRD Contains All Required Sections",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 0,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_004_prd_required_sections,
        "input_type": "project_dir",
    },
    # Phase 1 evals
    "INFRA-005": {
        "name": "Eval Suite Artifact Exists",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_005_eval_suite_artifact_exists,
        "input_type": "project_dir",
    },
    "INFRA-006": {
        "name": "Eval Suite Schema Valid",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_006_eval_suite_schema_valid,
        "input_type": "project_dir",
    },
    "INFRA-007": {
        "name": "Per-Agent AGENTS.md Created",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_007_agents_md_created,
        "input_type": "project_dir",
    },
    "INFRA-008": {
        "name": "Dynamic Prompt Recomposition After Stage Transition",
        "category": "infrastructure",
        "priority": "P0",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_infra_008_dynamic_prompt_after_transition,
        "input_type": "none",
    },
    "STAGE-001": {
        "name": "Only Valid Stage Transitions Occur",
        "category": "stage_transitions",
        "priority": "P1",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_stage_001_valid_transitions_only,
        "input_type": "trace",
    },
    "STAGE-002": {
        "name": "Exit Conditions Met Before Transitions",
        "category": "stage_transitions",
        "priority": "P1",
        "phase": 1,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_stage_002_exit_conditions_met,
        "input_type": "trace",
    },
    # Phase 2 evals — PM behavioral
    "PM-001": {
        "name": "Asks Clarifying Questions Before Writing PRD",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_001_asks_clarifying_questions,
        "input_type": "trace",
    },
    "PM-002": {
        "name": "Does Not Delegate PRD Writing",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_002_does_not_delegate_prd,
        "input_type": "trace",
    },
    "PM-003": {
        "name": "Proposes Evals With Scoring Rationale",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_003_proposes_evals_with_rationale,
        "input_type": "trace",
    },
    "PM-004": {
        "name": "Pushes Back When User Skips Evals",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_004_pushes_back_on_no_evals,
        "input_type": "trace",
    },
    "PM-005": {
        "name": "Confirms Before Stage Transition",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_005_confirms_before_transition,
        "input_type": "trace",
    },
    "PM-006": {
        "name": "No Premature PRD Writing",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_006_no_premature_prd,
        "input_type": "trace",
    },
    "PM-007": {
        "name": "Evals Proposed During INTAKE",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_pm_007_evals_proposed_during_intake,
        "input_type": "trace",
    },
    "PM-008": {
        "name": "Requirement Elicitation Quality",
        "category": "pm_behavioral",
        "priority": "P1",
        "phase": 2,
        "scoring": "likert",
        "threshold": 3.5,
        "fn": eval_pm_008_elicitation_quality,
        "input_type": "trace",
    },
    # Phase 2 evals — Stage transitions
    "STAGE-003": {
        "name": "Eval Approval Is Hard Gate Before RESEARCH",
        "category": "stage_transitions",
        "priority": "P1",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_stage_003_eval_approval_is_hard_gate,
        "input_type": "trace",
    },
    # Phase 2 evals — Guardrails
    "GUARD-001": {
        "name": "No Eval Modification During Execution",
        "category": "guardrails",
        "priority": "P2",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_guard_001_no_eval_modification_during_execution,
        "input_type": "trace",
    },
    "GUARD-002": {
        "name": "HITL Gates Enforced",
        "category": "guardrails",
        "priority": "P2",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_guard_002_hitl_gates_enforced,
        "input_type": "trace",
    },
    "GUARD-003": {
        "name": "Agent Memory Isolation",
        "category": "guardrails",
        "priority": "P2",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_guard_003_agent_memory_isolation,
        "input_type": "trace",
    },
    "GUARD-004": {
        "name": "File Operations Within Workspace",
        "category": "guardrails",
        "priority": "P2",
        "phase": 2,
        "scoring": "binary",
        "threshold": 1.0,
        "fn": eval_guard_004_file_operations_within_workspace,
        "input_type": "trace",
    },
}

# Phase to eval ID mapping
PHASE_EVALS: dict[int, list[str]] = {
    0: ["INFRA-001", "INFRA-002", "INFRA-003", "INFRA-004"],
    1: ["INFRA-005", "INFRA-006", "INFRA-007", "INFRA-008", "STAGE-001", "STAGE-002"],
    2: [
        "PM-001", "PM-002", "PM-003", "PM-004", "PM-005", "PM-006", "PM-007", "PM-008",
        "STAGE-003",
        "GUARD-001", "GUARD-002", "GUARD-003", "GUARD-004",
    ],
}


def run_eval(eval_id: str, project_dir: str, trace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a single eval and return the result."""
    if eval_id not in EVAL_REGISTRY:
        return {"eval_id": eval_id, "pass": False, "reason": f"Unknown eval: {eval_id}"}

    eval_info = EVAL_REGISTRY[eval_id]
    fn = eval_info["fn"]
    input_type = eval_info.get("input_type", "project_dir")

    if input_type == "project_dir":
        result = fn(project_dir)
    elif input_type == "trace":
        result = fn(trace or {})
    elif input_type == "none":
        result = fn()
    else:
        result = fn(project_dir)

    result["eval_id"] = eval_id
    result["name"] = eval_info["name"]
    result["scoring"] = eval_info["scoring"]
    result["threshold"] = eval_info["threshold"]
    return result


def run_evals(
    eval_ids: list[str],
    project_dir: str,
    trace: dict[str, Any] | None = None,
    langsmith_examples: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Run multiple evals and return results.

    If langsmith_examples are provided, each example's inputs are used as
    the trace data for trace-type evals.
    """
    results = []

    if langsmith_examples:
        # Run evals against each example from the LangSmith dataset
        for example in langsmith_examples:
            example_trace = example.get("inputs", {})
            example_id = example.get("id", "unknown")
            for eval_id in eval_ids:
                result = run_eval(eval_id, project_dir, trace=example_trace)
                result["example_id"] = str(example_id)
                results.append(result)
    else:
        for eval_id in eval_ids:
            result = run_eval(eval_id, project_dir, trace=trace)
            results.append(result)

    return results


def filter_evals(
    category: str | None = None,
    priority: str | None = None,
    phase: int | None = None,
    eval_id: str | None = None,
) -> list[str]:
    """Filter eval IDs based on criteria."""
    if eval_id:
        return [eval_id] if eval_id in EVAL_REGISTRY else []

    if phase is not None:
        return PHASE_EVALS.get(phase, [])

    ids = list(EVAL_REGISTRY.keys())

    if category:
        ids = [e for e in ids if EVAL_REGISTRY[e]["category"] == category]

    if priority:
        ids = [e for e in ids if EVAL_REGISTRY[e]["priority"] == priority]

    return ids


def print_results(results: list[dict[str, Any]]) -> None:
    """Print eval results in a human-readable format."""
    passed = sum(1 for r in results if r.get("pass"))
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Eval Results: {passed}/{total} passed")
    print(f"{'='*60}\n")

    for r in results:
        status = "PASS" if r.get("pass") else "FAIL"
        symbol = "\u2713" if r.get("pass") else "\u2717"
        print(f"  {symbol} [{status}] {r.get('eval_id', '?')} \u2014 {r.get('name', '?')}")
        if not r.get("pass"):
            print(f"    Reason: {r.get('reason', 'Unknown')}")

    print(f"\n{'='*60}")

    if passed == total:
        print("All evals passed!")
    else:
        print(f"{total - passed} eval(s) failed.")

    print()


def _fetch_langsmith_examples(dataset_name: str) -> list[dict[str, Any]]:
    """Fetch examples from a LangSmith dataset by name."""
    try:
        from langsmith import Client
        client = Client()
        examples = list(client.list_examples(dataset_name=dataset_name))
        return [
            {
                "id": str(ex.id),
                "inputs": ex.inputs or {},
                "outputs": ex.outputs or {},
            }
            for ex in examples
        ]
    except ImportError:
        print("Warning: langsmith package not installed, skipping dataset fetch")
        return []
    except Exception as e:
        print(f"Warning: Failed to fetch LangSmith dataset '{dataset_name}': {e}")
        return []


def _record_langsmith_experiment(
    experiment_name: str,
    results: list[dict[str, Any]],
    project_name: str = "meta-agent-evals",
) -> str | None:
    """Record eval results as a LangSmith experiment."""
    try:
        from langsmith import Client
        client = Client()

        # Create a dataset for the experiment if it doesn't exist
        dataset_name = f"eval-results-{experiment_name}"
        try:
            dataset = client.create_dataset(dataset_name, description=f"Eval results for experiment: {experiment_name}")
        except Exception:
            # Dataset may already exist
            datasets = list(client.list_datasets(dataset_name=dataset_name))
            dataset = datasets[0] if datasets else None

        if dataset is None:
            print(f"Warning: Could not create/find dataset for experiment '{experiment_name}'")
            return None

        # Add each result as an example
        for result in results:
            client.create_example(
                inputs={
                    "eval_id": result.get("eval_id", "unknown"),
                    "name": result.get("name", "unknown"),
                    "scoring": result.get("scoring", "binary"),
                },
                outputs={
                    "pass": result.get("pass", False),
                    "reason": result.get("reason", ""),
                    "threshold": result.get("threshold", 1.0),
                },
                dataset_id=dataset.id,
            )

        return str(dataset.id)
    except ImportError:
        print("Warning: langsmith package not installed, skipping experiment recording")
        return None
    except Exception as e:
        print(f"Warning: Failed to record experiment '{experiment_name}': {e}")
        return None


def _load_local_data(data_path: str) -> list[dict[str, Any]]:
    """Load synthetic data from a local YAML file."""
    try:
        import yaml
        with open(data_path) as f:
            data = yaml.safe_load(f)
        scenarios = data.get("scenarios", [])
        return [
            {
                "id": s.get("id", f"scenario-{i}"),
                "inputs": s.get("trace", s.get("inputs", {})),
                "outputs": s.get("expected", s.get("outputs", {})),
            }
            for i, s in enumerate(scenarios)
        ]
    except ImportError:
        print("Warning: yaml package not installed, cannot load local data")
        return []
    except Exception as e:
        print(f"Warning: Failed to load local data '{data_path}': {e}")
        return []


def main() -> int:
    """CLI entry point for the eval runner."""
    parser = argparse.ArgumentParser(
        description="Meta-agent eval suite runner"
    )
    parser.add_argument("--all", action="store_true", help="Run all evals")
    parser.add_argument(
        "--category",
        choices=["infrastructure", "pm_behavioral", "stage_transitions", "guardrails"],
        help="Run evals in a specific category",
    )
    parser.add_argument(
        "--priority",
        choices=["P0", "P1", "P2"],
        help="Run evals with a specific priority",
    )
    parser.add_argument("--eval", dest="eval_id", help="Run a single eval by ID")
    parser.add_argument(
        "--experiment", help="LangSmith experiment name for tracking"
    )
    parser.add_argument(
        "--phase", type=int, choices=[0, 1, 2], help="Run evals for a specific phase"
    )
    parser.add_argument("--data", help="Path to local synthetic data YAML file")
    parser.add_argument(
        "--langsmith-dataset", help="LangSmith dataset name"
    )
    parser.add_argument(
        "--langsmith-project", default="meta-agent-evals",
        help="LangSmith project name",
    )
    parser.add_argument(
        "--project-dir",
        default=".agents/pm/projects/test-project",
        help="Project directory for eval execution",
    )

    args = parser.parse_args()

    # Determine which evals to run
    if args.all:
        eval_ids = list(EVAL_REGISTRY.keys())
    elif args.eval_id:
        eval_ids = filter_evals(eval_id=args.eval_id)
    elif args.phase is not None:
        eval_ids = filter_evals(phase=args.phase)
    elif args.category:
        eval_ids = filter_evals(category=args.category)
    elif args.priority:
        eval_ids = filter_evals(priority=args.priority)
    else:
        parser.print_help()
        return 1

    if not eval_ids:
        print("No evals matched the specified criteria.")
        return 1

    print(f"Running {len(eval_ids)} eval(s)...")

    # Load examples from LangSmith dataset or local data file
    langsmith_examples = None
    if args.langsmith_dataset:
        print(f"Fetching examples from LangSmith dataset: {args.langsmith_dataset}")
        langsmith_examples = _fetch_langsmith_examples(args.langsmith_dataset)
        if langsmith_examples:
            print(f"  Loaded {len(langsmith_examples)} examples")
        else:
            print("  No examples loaded, running without dataset")
    elif args.data:
        print(f"Loading local data from: {args.data}")
        langsmith_examples = _load_local_data(args.data)
        if langsmith_examples:
            print(f"  Loaded {len(langsmith_examples)} scenarios")

    if args.experiment:
        print(f"Experiment: {args.experiment}")

    results = run_evals(
        eval_ids, args.project_dir, langsmith_examples=langsmith_examples,
    )
    print_results(results)

    # Record results as LangSmith experiment if requested
    if args.experiment:
        experiment_id = _record_langsmith_experiment(
            args.experiment, results, args.langsmith_project,
        )
        if experiment_id:
            print(f"Experiment recorded: {experiment_id}")

    # Return non-zero if any eval failed
    all_passed = all(r.get("pass") for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
