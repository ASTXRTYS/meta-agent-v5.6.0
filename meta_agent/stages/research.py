"""RESEARCH stage wiring."""

from __future__ import annotations

import os
from typing import Any


def _get_field(obj: Any, field: str) -> Any:
    """Get a field from either a dataclass or a dict.
    
    Note: Helper duplication consolidation TODO in stages/__init__.py.
    """
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None


def _default_prd_path(project_dir: str, project_id: str) -> str:
    fixture = os.path.join(project_dir, "artifacts", "intake", "research-agent-prd.md")
    generic = os.path.join(project_dir, "artifacts", "intake", "prd.md")
    if project_id == "meta-agent" and os.path.isfile(fixture):
        return fixture
    return generic


def _contains_required_bundle_sections(bundle_content: str) -> bool:
    required = (
        "## PRD Coverage Matrix",
        "## Unresolved Research Gaps",
        "## Citation Index",
    )
    return all(section in bundle_content for section in required)


class ResearchStage:
    """Manages the RESEARCH stage of the workflow."""

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = _default_prd_path(project_dir, project_id)
        self.eval_suite_path = f"{project_dir}/evals/eval-suite-prd.json"
        self.decomposition_path = f"{project_dir}/artifacts/research/research-decomposition.md"
        self.research_bundle_path = f"{project_dir}/artifacts/research/research-bundle.md"
        self.research_clusters_path = f"{project_dir}/artifacts/research/research-clusters.md"
        self.sub_findings_dir = f"{project_dir}/artifacts/research/sub-findings"
        self.agents_md_path = f"{project_dir}/.agents/research-agent/AGENTS.md"

    def check_entry_conditions(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        """Check RESEARCH entry conditions.
        
        NOTE: Unlike intake.py which takes no state parameter, this method accepts
        optional state to allow override of current_prd_path. This inconsistency
        should be aligned across all stage classes for consistency.
        """
        state = state or {}
        prd_path = state.get("current_prd_path") or self.prd_path
        eval_suite_path = self.eval_suite_path
        unmet = []
        if not os.path.isfile(prd_path):
            unmet.append(f"PRD not found at {prd_path}")
        if not os.path.isfile(eval_suite_path):
            unmet.append(f"Eval suite not found at {eval_suite_path}")
        return {"met": len(unmet) == 0, "unmet": unmet}

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.decomposition_path):
            unmet.append(f"Research decomposition not found at {self.decomposition_path}")
        if not os.path.isfile(self.research_clusters_path):
            unmet.append(f"Research clusters not found at {self.research_clusters_path}")
        if not os.path.isfile(self.research_bundle_path):
            unmet.append(f"Research bundle not found at {self.research_bundle_path}")
        if not os.path.isfile(self.agents_md_path):
            unmet.append(f"Research-agent memory not found at {self.agents_md_path}")
        if not os.path.isdir(self.sub_findings_dir) or not any(
            name.endswith(".md") for name in os.listdir(self.sub_findings_dir)
        ):
            unmet.append(f"No sub-findings were written under {self.sub_findings_dir}")

        current_path = state.get("current_research_path")
        if current_path and current_path != self.research_bundle_path:
            unmet.append(f"current_research_path points to unexpected artifact: {current_path}")
        if not current_path and os.path.isfile(self.research_bundle_path):
            unmet.append("current_research_path not recorded in state")

        verification = state.get("verification_results", {}).get("research_bundle", {})
        status = verification.get("status")
        if status != "pass":
            unmet.append(f"Verification did not pass: {status}")

        approvals = state.get("approval_history", [])
        clusters_approved = any(
            _get_field(a, "artifact") in {"research_clusters", self.research_clusters_path}
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        approved = any(
            _get_field(a, "artifact") in {"research_bundle", self.research_bundle_path}
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        if not clusters_approved:
            unmet.append("Research clusters were not approved by user")
        if not approved:
            unmet.append("Research bundle not approved by user")

        if os.path.isfile(self.research_bundle_path):
            with open(self.research_bundle_path) as f:
                bundle_content = f.read()
            if not _contains_required_bundle_sections(bundle_content):
                unmet.append("Research bundle is missing required Phase 3 sections")

        return {"met": len(unmet) == 0, "unmet": unmet}
