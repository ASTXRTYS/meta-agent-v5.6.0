"""SPEC_REVIEW stage wiring.

Spec References: Sections 3.2, 7.3

The SPEC_REVIEW stage handles user review of the technical specification and
Tier 2 eval suite. Both approvals are HARD GATES — process does not proceed
without explicit user approval.

FIXME: No spec reference header explaining stage requirements per project convention.
FIXME: Inconsistent method signature — check_entry_conditions() takes no state parameter,
       but research.py:53 and spec_generation.py:49 both accept state: dict[str, Any] | None.
       This breaks the polymorphic stage interface pattern.
FIXME: _get_field helper is duplicated from research.py, prd_review.py, etc.
       Consider extracting to a shared utility module to eliminate duplication.
FIXME: Path construction uses f-string concatenation instead of os.path.join
       for cross-platform compatibility (Windows uses backslashes).
"""

from __future__ import annotations

import os
from typing import Any


def _get_field(obj: Any, field: str) -> Any:
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None


class SpecReviewStage:
    """Manages the SPEC_REVIEW stage of the workflow."""

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        # FIXME: Path construction is inconsistent — research.py uses os.path.join,
        # but these use f-string concatenation. Should standardize for cross-platform compatibility.
        self.spec_path = f"{project_dir}/artifacts/spec/technical-specification.md"
        self.arch_eval_suite_path = f"{project_dir}/evals/eval-suite-architecture.json"
        # FIXME: No revision cycle tracking — prd_review.py has MAX_REVISION_CYCLES and
        # increment_revision_count() to prevent infinite loops. This stage lacks any
        # iteration limits, making it vulnerable to infinite revision loops.

    def check_entry_conditions(self) -> dict[str, Any]:
        """Check SPEC_REVIEW entry conditions.

        FIXME: Method signature inconsistent with sibling stages — research.py and
        spec_generation.py both accept optional state parameter for path overrides.
        This breaks polymorphic stage interface expectations.

        Entry: Technical spec and Tier 2 eval suite must exist.
        """
        unmet = []
        if not os.path.isfile(self.spec_path):
            unmet.append(f"Technical spec not found at {self.spec_path}")
        if not os.path.isfile(self.arch_eval_suite_path):
            unmet.append(f"Tier 2 eval suite not found at {self.arch_eval_suite_path}")
        return {"met": len(unmet) == 0, "unmet": unmet}

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check SPEC_REVIEW exit conditions.

        ALL required:
        1. User explicitly approves BOTH technical spec AND Tier 2 eval suite
        2. Approval recorded in approval_history
        3. Ready for transition to next stage

        FIXME: No content validation helper — research.py:30-36 validates required
        sections in the bundle. This stage blindly trusts file existence without
        validating spec structure or required sections.
        FIXME: No user interaction helpers — prd_review.py:103-143 has
        classify_user_response() for the 7-branch EVAL_APPROVAL_PROTOCOL.
        This stage assumes approvals appear magically in state without any
        classification logic for revision requests, rejection flows, etc.
        FIXME: No revision cycle tracking or limit enforcement — unlike
        prd_review.py and spec_generation.py which have MAX_REVISION_CYCLES
        and increment methods, this stage has no iteration guardrails.
        """
        approvals = state.get("approval_history", [])
        spec_approved = any(
            _get_field(a, "artifact") in {"technical_specification", self.spec_path}
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        eval_approved = any(
            _get_field(a, "artifact") in {"eval_suite_architecture", self.arch_eval_suite_path}
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        unmet = []
        if not spec_approved:
            unmet.append("Technical spec not approved")
        if not eval_approved:
            unmet.append("Tier 2 eval suite not approved")
        return {
            "met": len(unmet) == 0,
            "unmet": unmet,
            "spec_approved": spec_approved,
            "eval_approved": eval_approved,
        }
