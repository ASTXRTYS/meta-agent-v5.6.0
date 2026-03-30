"""RESEARCH stage wiring."""

from __future__ import annotations

import os
from typing import Any


def _get_field(obj: Any, field: str) -> Any:
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None


class ResearchStage:
    """Manages the RESEARCH stage of the workflow."""

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = f"{project_dir}/artifacts/intake/prd.md"
        self.eval_suite_path = f"{project_dir}/evals/eval-suite-prd.json"
        self.decomposition_path = f"{project_dir}/artifacts/research/research-decomposition.md"
        self.research_bundle_path = f"{project_dir}/artifacts/research/research-bundle.md"
        self.research_clusters_path = f"{project_dir}/artifacts/research/research-clusters.md"

    def check_entry_conditions(self) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")
        if not os.path.isfile(self.eval_suite_path):
            unmet.append(f"Eval suite not found at {self.eval_suite_path}")
        return {"met": len(unmet) == 0, "unmet": unmet}

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.decomposition_path):
            unmet.append(f"Research decomposition not found at {self.decomposition_path}")
        if not os.path.isfile(self.research_bundle_path):
            unmet.append(f"Research bundle not found at {self.research_bundle_path}")

        current_path = state.get("current_research_path")
        if current_path and current_path != self.research_bundle_path:
            unmet.append(f"current_research_path points to unexpected artifact: {current_path}")
        if not current_path and os.path.isfile(self.research_bundle_path):
            unmet.append("current_research_path not recorded in state")

        verification = state.get("verification_results", {}).get("research_bundle", {})
        status = verification.get("status")
        if status and status != "pass":
            unmet.append(f"Verification did not pass: {status}")

        approvals = state.get("approval_history", [])
        approved = any(
            _get_field(a, "artifact") in {"research_bundle", self.research_bundle_path}
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        if not approved:
            unmet.append("Research bundle not approved by user")

        return {"met": len(unmet) == 0, "unmet": unmet}
