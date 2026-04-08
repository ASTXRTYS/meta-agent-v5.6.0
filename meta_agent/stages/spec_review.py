"""SPEC_REVIEW stage wiring.

Spec References: Sections 3.2, 7.3

The SPEC_REVIEW stage handles user review of the technical specification and
Tier 2 eval suite. Both approvals are HARD GATES — process does not proceed
without explicit user approval.

See stages/__init__.py for consolidated TODOs on:
- Helper function duplication (_get_field)
- Path construction inconsistency
- Method signature inconsistency
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
        # Note: Revision cycle tracking consolidation TODO in stages/__init__.py

    def check_entry_conditions(self) -> dict[str, Any]:
        """Check SPEC_REVIEW entry conditions.

        Entry: Technical spec and Tier 2 eval suite must exist.

        Note: Method signature inconsistency consolidation TODO in stages/__init__.py.
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

        Note: Validation helpers, user interaction helpers, and revision cycle tracking
        consolidation TODOs in stages/__init__.py.
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
