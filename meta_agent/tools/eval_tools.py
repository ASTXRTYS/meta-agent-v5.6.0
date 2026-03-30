"""Eval tools for the meta-agent system.

Spec Reference: Sections 5.10-5.12, 8.15-8.19, 22.16, 22.17

Implements the first 2 of 5 eval tools needed for INTAKE / SPEC_GENERATION:
- propose_evals: draft Tier 1 or Tier 2 eval suites in canonical JSON format
- create_eval_dataset: convert eval suite JSON to LangSmith dataset examples

Remaining 3 tools (run_eval_suite, get_eval_results, compare_eval_runs)
are stubs for Phase 3+.
"""

from __future__ import annotations

import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Eval suite JSON schema template — Sections 5.10, 5.11
# ---------------------------------------------------------------------------

EVAL_SUITE_TEMPLATE = {
    "metadata": {
        "artifact": "eval-suite-prd",
        "project_id": "",
        "version": "1.0.0",
        "tier": 1,
        "langsmith_dataset_name": "",
        "created_by": "orchestrator",
        "status": "draft",
        "lineage": ["intake-prd.md"],
    },
    "evals": [],
}

VALID_CATEGORIES = {"behavioral", "acceptance", "edge_case", "user_intent"}
VALID_STRATEGIES = {"binary", "likert", "llm-judge", "pairwise"}
REQUIRED_EVAL_FIELDS = {"id", "name", "category", "input", "expected", "scoring"}
REQUIRED_METADATA_FIELDS = {
    "artifact",
    "project_id",
    "version",
    "tier",
    "langsmith_dataset_name",
    "created_by",
    "status",
    "lineage",
}


# ---------------------------------------------------------------------------
# 8.15 propose_evals — Section 8.15
# ---------------------------------------------------------------------------

def propose_evals(
    requirements: list[dict[str, Any]],
    tier: int,
    project_id: str,
    created_by: str | None = None,
    lineage: list[str] | None = None,
) -> dict[str, Any]:
    """Propose an eval suite based on requirements.

    Args:
        requirements: List of dicts with id, description, type
            (deterministic/qualitative).
        tier: Eval tier (1 = PRD-derived, 2 = architecture-derived).
        project_id: Project identifier for artifact path scoping.
        created_by: Optional author override.
        lineage: Optional lineage override.

    Returns:
        Dict with eval suite proposal (JSON content, path, eval count).
    """
    if not requirements:
        return {"error": "Requirements list is empty", "pass": False}

    if tier not in (1, 2):
        return {"error": f"Invalid tier: {tier}. Must be 1 or 2.", "pass": False}

    evals: list[dict[str, Any]] = []
    for i, req in enumerate(requirements):
        req_id = req.get("id", f"REQ-{i+1:03d}")
        description = req.get("description", "")
        req_type = req.get("type", "deterministic")

        eval_id = f"EVAL-{i+1:03d}" if tier == 1 else f"ARCH-{i+1:03d}"
        evals.append(_build_eval_entry(eval_id, req_id, description, req_type, tier=tier, requirement=req))

    artifact_name = "eval-suite-prd" if tier == 1 else "eval-suite-architecture"
    dataset_name = f"{project_id}-tier-{tier}-evals"
    default_lineage = (
        ["intake-prd.md"]
        if tier == 1
        else ["eval-suite-prd.json", "technical-specification.md"]
    )
    creator = created_by or ("orchestrator" if tier == 1 else "spec-writer")

    document = {
        "metadata": {
            "artifact": artifact_name,
            "project_id": project_id,
            "version": "1.0.0",
            "tier": tier,
            "langsmith_dataset_name": dataset_name,
            "created_by": creator,
            "status": "draft",
            "lineage": lineage or default_lineage,
        },
        "evals": evals,
    }

    json_content = json.dumps(document, indent=2) + "\n"
    eval_path = f"evals/{artifact_name}.json"

    return {
        "json_content": json_content,
        "content": json_content,
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
    *,
    tier: int = 1,
    requirement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single eval entry from a requirement."""
    if req_type == "qualitative":
        scoring: dict[str, Any] = {
            "strategy": "likert",
            "threshold": 3.5,
            "rubric": f"Rate quality of: {description}",
            "anchors": {
                "1": f"Fails to satisfy {req_id}: {description}",
                "3": f"Partially satisfies {req_id}: {description}",
                "5": f"Fully satisfies {req_id}: {description}",
            },
        }
    else:
        scoring = {
            "strategy": "binary",
            "threshold": 1.0,
            "rubric": f"Verify: {description}",
        }

    entry = {
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
        "scoring": scoring,
    }

    if tier == 2:
        entry["architecture_decision"] = (
            (requirement or {}).get("architecture_decision")
            or description
        )

    return entry


def _load_eval_suite_document(eval_suite_path: str) -> dict[str, Any]:
    with open(eval_suite_path) as f:
        return json.load(f)


def validate_eval_suite(eval_suite_path: str) -> dict[str, Any]:
    """Validate an eval suite JSON file against the schema."""
    if not os.path.isfile(eval_suite_path):
        return {"valid": False, "errors": [f"File not found: {eval_suite_path}"]}

    try:
        data = _load_eval_suite_document(eval_suite_path)
        if not isinstance(data, dict):
            return {"valid": False, "errors": ["Top-level JSON document must be an object"]}

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return {"valid": False, "errors": ["Missing or invalid 'metadata' object"]}

        metadata_missing = REQUIRED_METADATA_FIELDS - set(metadata.keys())
        if metadata_missing:
            return {
                "valid": False,
                "errors": [f"Metadata missing fields {sorted(metadata_missing)}"],
            }

        evals = data.get("evals")
        if not isinstance(evals, list):
            return {"valid": False, "errors": ["No 'evals' list found"]}
        if not evals:
            return {"valid": False, "errors": ["Empty evals list"]}

        errors = []
        for ev in evals:
            if not isinstance(ev, dict):
                errors.append("Eval entry must be an object")
                continue

            missing = REQUIRED_EVAL_FIELDS - set(ev.keys())
            if missing:
                errors.append(f"Eval {ev.get('id', '?')}: missing fields {missing}")

            category = ev.get("category")
            if category and category not in VALID_CATEGORIES:
                errors.append(f"Eval {ev.get('id', '?')}: invalid category '{category}'")

            scoring = ev.get("scoring", {})
            if not isinstance(scoring, dict):
                errors.append(f"Eval {ev.get('id', '?')}: scoring must be an object")
                continue

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
    """Create a LangSmith dataset from an approved eval suite JSON file."""
    validation = validate_eval_suite(eval_suite_path)
    if not validation["valid"]:
        return {
            "error": f"Invalid eval suite: {validation['errors']}",
            "status": "error",
        }

    data = _load_eval_suite_document(eval_suite_path)
    evals = data["evals"]

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
