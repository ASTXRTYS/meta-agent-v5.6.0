"""SPEC_REVIEW stage wiring."""

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
        self.spec_path = f"{project_dir}/artifacts/spec/technical-specification.md"
        self.arch_eval_suite_path = f"{project_dir}/evals/eval-suite-architecture.json"

    def check_entry_conditions(self) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.spec_path):
            unmet.append(f"Technical spec not found at {self.spec_path}")
        if not os.path.isfile(self.arch_eval_suite_path):
            unmet.append(f"Tier 2 eval suite not found at {self.arch_eval_suite_path}")
        return {"met": len(unmet) == 0, "unmet": unmet}

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
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
