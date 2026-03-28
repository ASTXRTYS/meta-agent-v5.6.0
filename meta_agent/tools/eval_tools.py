"""Eval tools for the meta-agent system.

Spec Reference: Sections 8.15-8.19, 22.16, 22.17

Implements the first 2 of 5 eval tools needed for INTAKE (Phase 2):
- propose_evals: Two-phase classification flow for eval suite proposal
- create_eval_dataset: Converts eval suite YAML to LangSmith dataset

Remaining 3 tools (run_eval_suite, get_eval_results, compare_eval_runs)
are stubs for Phase 3+.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Eval suite YAML schema template — Section 5.10
# ---------------------------------------------------------------------------

EVAL_SUITE_TEMPLATE = {
    "artifact": "eval-suite-prd",
    "version": "1.0.0",
    "tier": 1,
    "created_by": "orchestrator",
    "status": "draft",
    "lineage": ["intake-prd.md"],
}

VALID_CATEGORIES = {"behavioral", "acceptance", "edge_case", "user_intent"}
VALID_STRATEGIES = {"binary", "likert", "llm-judge", "pairwise"}
REQUIRED_EVAL_FIELDS = {"id", "name", "category", "input", "expected", "scoring"}


# ---------------------------------------------------------------------------
# 8.15 propose_evals — Section 8.15
# ---------------------------------------------------------------------------

def propose_evals(
    requirements: list[dict[str, Any]],
    tier: int,
    project_id: str,
) -> dict[str, Any]:
    """Propose an eval suite based on PRD requirements.

    Two-phase classification flow per Section 8.15:
    Phase 1: Draft requirements without type classification (id + description only)
    Phase 2: Interactive classification with <pm_reasoning> blocks
    Phase 3: Call with confirmed types

    This function implements Phase 3 — it receives requirements with confirmed
    types and generates the structured eval suite proposal.

    Args:
        requirements: List of dicts with id, description, type (deterministic/qualitative).
                     Type must be user-confirmed for ambiguous requirements.
        tier: Eval tier (1 = PRD-derived, 2 = architecture-derived).
        project_id: Project identifier for artifact path scoping.

    Returns:
        Dict with eval suite proposal (YAML content, path, eval count).

    Raises:
        ValueError: If requirements list is empty or tier invalid.
    """
    if not requirements:
        return {"error": "Requirements list is empty", "pass": False}

    if tier not in (1, 2):
        return {"error": f"Invalid tier: {tier}. Must be 1 or 2.", "pass": False}

    # Build eval entries from requirements
    evals: list[dict[str, Any]] = []
    for i, req in enumerate(requirements):
        req_id = req.get("id", f"REQ-{i+1:03d}")
        description = req.get("description", "")
        req_type = req.get("type", "deterministic")

        eval_id = f"EVAL-{i+1:03d}"
        eval_entry = _build_eval_entry(eval_id, req_id, description, req_type)
        evals.append(eval_entry)

    # Build the YAML document
    artifact_name = "eval-suite-prd" if tier == 1 else "eval-suite-architecture"
    dataset_name = f"{project_id}-tier-{tier}-evals"

    frontmatter = {
        "artifact": artifact_name,
        "project_id": project_id,
        "version": "1.0.0",
        "tier": tier,
        "langsmith_dataset_name": dataset_name,
        "created_by": "orchestrator",
        "status": "draft",
        "lineage": ["intake-prd.md"] if tier == 1 else ["technical-specification.md"],
    }

    eval_suite = {"evals": evals}

    # Generate YAML content
    if HAS_YAML:
        fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        evals_yaml = yaml.dump(eval_suite, default_flow_style=False, sort_keys=False)
        yaml_content = f"---\n{fm_yaml}---\n{evals_yaml}"
    else:
        yaml_content = _manual_yaml_dump(frontmatter, evals)

    # Determine output path
    eval_dir = f"evals"
    eval_path = f"{eval_dir}/{artifact_name}.yaml"

    return {
        "yaml_content": yaml_content,
        "path": eval_path,
        "eval_count": len(evals),
        "dataset_name": dataset_name,
        "tier": tier,
        "status": "proposed",
    }


def _build_eval_entry(
    eval_id: str,
    req_id: str,
    description: str,
    req_type: str,
) -> dict[str, Any]:
    """Build a single eval entry from a requirement."""
    # Determine scoring strategy based on type
    if req_type == "deterministic":
        strategy = "binary"
        threshold = 1.0
        rubric = f"Verify: {description}"
    elif req_type == "qualitative":
        strategy = "likert"
        threshold = 3.5
        rubric = f"Rate quality of: {description}"
    else:
        strategy = "binary"
        threshold = 1.0
        rubric = f"Verify: {description}"

    return {
        "id": eval_id,
        "name": f"Validate {req_id}: {description[:50]}",
        "category": "acceptance",
        "input": {
            "scenario": description,
            "preconditions": {},
        },
        "expected": {
            "behavior": description,
        },
        "scoring": {
            "strategy": strategy,
            "threshold": threshold,
            "rubric": rubric,
        },
    }


def _manual_yaml_dump(frontmatter: dict[str, Any], evals: list[dict[str, Any]]) -> str:
    """Fallback YAML generation when PyYAML is not available."""
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("evals:")
    for ev in evals:
        lines.append(f"  - id: {ev['id']}")
        lines.append(f"    name: \"{ev['name']}\"")
        lines.append(f"    category: {ev['category']}")
        lines.append(f"    input:")
        lines.append(f"      scenario: \"{ev['input']['scenario']}\"")
        lines.append(f"      preconditions: {{}}")
        lines.append(f"    expected:")
        lines.append(f"      behavior: \"{ev['expected']['behavior']}\"")
        lines.append(f"    scoring:")
        lines.append(f"      strategy: {ev['scoring']['strategy']}")
        lines.append(f"      threshold: {ev['scoring']['threshold']}")
        lines.append(f"      rubric: \"{ev['scoring']['rubric']}\"")
    return "\n".join(lines) + "\n"


def validate_eval_suite(eval_suite_path: str) -> dict[str, Any]:
    """Validate an eval suite YAML file against the schema.

    Returns dict with 'valid' bool and 'errors' list.
    """
    if not os.path.isfile(eval_suite_path):
        return {"valid": False, "errors": [f"File not found: {eval_suite_path}"]}

    if not HAS_YAML:
        return {"valid": False, "errors": ["yaml package not installed"]}

    try:
        with open(eval_suite_path) as f:
            content = f.read()

        parts = content.split("---", 2)
        if len(parts) > 2:
            data = yaml.safe_load(parts[-1])
        else:
            data = yaml.safe_load(content)

        if not data or "evals" not in data:
            return {"valid": False, "errors": ["No 'evals' key found"]}

        evals = data["evals"]
        if not evals:
            return {"valid": False, "errors": ["Empty evals list"]}

        errors = []
        for ev in evals:
            missing = REQUIRED_EVAL_FIELDS - set(ev.keys())
            if missing:
                errors.append(f"Eval {ev.get('id', '?')}: missing fields {missing}")

            scoring = ev.get("scoring", {})
            if isinstance(scoring, dict):
                strategy = scoring.get("strategy")
                if strategy and strategy not in VALID_STRATEGIES:
                    errors.append(f"Eval {ev.get('id', '?')}: invalid strategy '{strategy}'")

        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}


# ---------------------------------------------------------------------------
# 8.16 create_eval_dataset — Section 8.16
# ---------------------------------------------------------------------------

def create_eval_dataset(
    eval_suite_path: str,
    dataset_name: str,
) -> dict[str, Any]:
    """Create a LangSmith dataset from an approved eval suite YAML.

    Converts eval suite input/expected pairs into LangSmith dataset examples.
    HITL-gated.

    Args:
        eval_suite_path: Path to the eval suite YAML file.
        dataset_name: Name for the LangSmith dataset.

    Returns:
        Dict with dataset_id, example_count, and status.
    """
    # Validate the eval suite file
    validation = validate_eval_suite(eval_suite_path)
    if not validation["valid"]:
        return {
            "error": f"Invalid eval suite: {validation['errors']}",
            "status": "error",
        }

    # Parse the eval suite
    with open(eval_suite_path) as f:
        content = f.read()

    parts = content.split("---", 2)
    data = yaml.safe_load(parts[-1]) if len(parts) > 2 else yaml.safe_load(content)
    evals = data["evals"]

    # Build LangSmith examples from eval entries
    examples = []
    for ev in evals:
        example = {
            "inputs": {
                "eval_id": ev["id"],
                "scenario": ev.get("input", {}).get("scenario", ""),
                "preconditions": ev.get("input", {}).get("preconditions", {}),
            },
            "outputs": {
                "expected_behavior": ev.get("expected", {}).get("behavior", ""),
                "scoring_strategy": ev.get("scoring", {}).get("strategy", "binary"),
                "threshold": ev.get("scoring", {}).get("threshold", 1.0),
            },
        }
        examples.append(example)

    # Try to create LangSmith dataset
    try:
        from langsmith import Client
        client = Client()
        dataset = client.create_dataset(dataset_name)
        for ex in examples:
            client.create_example(
                inputs=ex["inputs"],
                outputs=ex["outputs"],
                dataset_id=dataset.id,
            )
        return {
            "dataset_id": str(dataset.id),
            "dataset_name": dataset_name,
            "example_count": len(examples),
            "status": "created",
        }
    except ImportError:
        # LangSmith not available — return local result
        return {
            "dataset_id": None,
            "dataset_name": dataset_name,
            "example_count": len(examples),
            "examples": examples,
            "status": "local_only",
            "note": "langsmith not installed; dataset stored locally only",
        }
    except Exception as e:
        return {
            "error": str(e),
            "dataset_name": dataset_name,
            "status": "error",
        }


# ---------------------------------------------------------------------------
# 8.17-8.19 Remaining eval tools — stubs for Phase 3+
# ---------------------------------------------------------------------------

def run_eval_suite(
    phase: int,
    eval_map_path: str,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    """Run an eval suite against the current project code. Stub for Phase 3."""
    raise NotImplementedError("run_eval_suite is implemented in Phase 3")


def get_eval_results(
    experiment_id: str | None = None,
    phase: int | None = None,
    project_id: str = "",
) -> dict[str, Any]:
    """Get results from a previous eval run. Stub for Phase 3."""
    raise NotImplementedError("get_eval_results is implemented in Phase 3")


def compare_eval_runs(
    baseline_experiment_id: str,
    comparison_experiment_id: str,
) -> dict[str, Any]:
    """Compare two eval runs. Stub for Phase 3."""
    raise NotImplementedError("compare_eval_runs is implemented in Phase 3")
