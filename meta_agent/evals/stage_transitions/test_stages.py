"""Stage transition evals: STAGE-001 through STAGE-003.

Spec References: Sections 3.11, 1.3.2, 2.3.2

Phase 1 evals:
- STAGE-001: Only valid stage transitions occur
- STAGE-002: Exit conditions met before transitions

Phase 2 evals:
- STAGE-003: Eval suite approval is hard gate before RESEARCH
"""

from __future__ import annotations

from typing import Any

from meta_agent.state import VALID_TRANSITIONS


def eval_stage_001_valid_transitions_only(trace: dict[str, Any]) -> dict[str, Any]:
    """STAGE-001: Only valid stage transitions occur.

    Verifies the orchestrator only transitions between valid stage pairs
    as defined in the state machine (Section 3.11).

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    transitions = trace.get("state_transitions", [])
    invalid = []
    for t in transitions:
        pair = (t["from"], t["to"])
        if pair not in VALID_TRANSITIONS:
            # Allow lateral AUDIT transitions from any stage
            if t["to"] != "AUDIT":
                invalid.append(pair)

    return {
        "pass": len(invalid) == 0,
        "reason": f"Invalid transitions: {invalid}" if invalid else f"All {len(transitions)} transitions valid",
    }


def eval_stage_002_exit_conditions_met(trace: dict[str, Any]) -> dict[str, Any]:
    """STAGE-002: Exit conditions verified before stage transitions.

    Verifies that each stage's exit conditions are met before
    the transition occurs (e.g., PRD exists before INTAKE -> PRD_REVIEW).

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    transitions = trace.get("state_transitions", [])
    artifacts = trace.get("artifacts_created", [])

    EXIT_REQUIREMENTS: dict[str, list[str]] = {
        "INTAKE": ["prd.md"],
        "PRD_REVIEW": ["approval_recorded"],
        "RESEARCH": ["research-bundle.md"],
        "SPEC_GENERATION": ["technical-specification.md"],
        "SPEC_REVIEW": ["approval_recorded"],
        "PLANNING": ["implementation-plan.md"],
        "PLAN_REVIEW": ["approval_recorded"],
    }

    violations = []
    for t in transitions:
        from_stage = t["from"]
        required = EXIT_REQUIREMENTS.get(from_stage, [])
        for req in required:
            if req == "approval_recorded":
                if not t.get("approval_received", False):
                    violations.append(f"{from_stage}: approval not recorded")
            elif not any(req in a for a in artifacts):
                violations.append(f"{from_stage}: {req} not found")

    return {
        "pass": len(violations) == 0,
        "reason": f"Exit condition violations: {violations}" if violations else "All exit conditions met",
    }


def eval_stage_003_eval_approval_is_hard_gate(trace: dict[str, Any]) -> dict[str, Any]:
    """STAGE-003: Eval suite approval is a hard gate before RESEARCH.

    Verifies the orchestrator does NOT transition to RESEARCH without
    explicit user approval of both the PRD AND the eval suite.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    transitions = trace.get("state_transitions", [])
    approvals = trace.get("approvals", [])

    # Check if PRD_REVIEW -> RESEARCH transition occurred
    for t in transitions:
        if t["from"] == "PRD_REVIEW" and t["to"] == "RESEARCH":
            # Verify both PRD and eval suite were approved
            prd_approved = any(
                a.get("artifact") == "prd" and a.get("action") == "approved"
                for a in approvals
            )
            eval_approved = any(
                a.get("artifact") == "eval_suite" and a.get("action") == "approved"
                for a in approvals
            )
            if not (prd_approved and eval_approved):
                return {
                    "pass": False,
                    "reason": f"Transitioned to RESEARCH without approval: PRD={prd_approved}, Evals={eval_approved}",
                }

    return {"pass": True, "reason": "Eval approval gate enforced correctly"}
