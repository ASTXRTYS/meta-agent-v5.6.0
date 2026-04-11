import os
from .base import BaseStage, ConditionResult
from typing import Any
from meta_agent.state import WorkflowStage
from .common import _get_field


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


class ResearchStage(BaseStage):
    """Manages the RESEARCH stage of the workflow."""

    STAGE_NAME = WorkflowStage.RESEARCH.value

    def __init__(self, project_dir: str, project_id: str) -> None:
        super().__init__(project_dir, project_id)
        self.prd_path = _default_prd_path(project_dir, project_id)
        self.eval_suite_path = self.resolve_path("evals", "eval-suite-prd.json")
        self.decomposition_path = self.resolve_path("artifacts", "research", "research-decomposition.md")
        self.research_bundle_path = self.resolve_path("artifacts", "research", "research-bundle.md")
        self.research_clusters_path = self.resolve_path("artifacts", "research", "research-clusters.md")
        self.sub_findings_dir = self.resolve_path("artifacts", "research", "sub-findings")
        self.agents_md_path = self.resolve_path(".agents", "research-agent", "AGENTS.md")

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check RESEARCH entry conditions.
        
        Entry: PRD and eval suite exist. Supports current_prd_path override.
        """
        prd_path = state.get("current_prd_path") or self.prd_path
        eval_suite_path = self.eval_suite_path
        unmet = []
        if not os.path.isfile(prd_path):
            unmet.append(f"PRD not found at {prd_path}")
        if not os.path.isfile(eval_suite_path):
            unmet.append(f"Eval suite not found at {eval_suite_path}")
        
        if unmet:
            return self._fail(unmet)
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check RESEARCH exit conditions."""
        unmet = []
        
        ok, reason = self._artifact_is_proven(self.decomposition_path, state, require_approval=False)
        if not ok:
            unmet.append(f"Provenance check failed for {self.decomposition_path}: {reason}")
            
        ok, reason = self._artifact_is_proven(self.research_clusters_path, state, require_approval=True, approval_alias="research_clusters")
        if not ok:
            unmet.append(f"Provenance check failed for {self.research_clusters_path}: {reason}")
            
        ok, reason = self._artifact_is_proven(self.research_bundle_path, state, require_approval=True, approval_alias="research_bundle")
        if not ok:
            unmet.append(f"Provenance check failed for {self.research_bundle_path}: {reason}")

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

        if unmet:
            return self._fail(unmet)
        return self._pass()

