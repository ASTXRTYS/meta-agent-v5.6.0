"""SPEC_REVIEW stage wiring.

Spec References: Sections 3.2, 7.3

The SPEC_REVIEW stage handles user review of the technical specification and
Tier 2 eval suite. Both approvals are HARD GATES — process does not proceed
without explicit user approval.
"""

import os
from typing import Any
from .base import BaseStage, ConditionResult
from meta_agent.state import WorkflowStage
from .common import _get_field


class SpecReviewStage(BaseStage):
    """Manages the SPEC_REVIEW stage of the workflow."""

    STAGE_NAME = WorkflowStage.SPEC_REVIEW.value

    def __init__(self, project_dir: str, project_id: str) -> None:
        super().__init__(project_dir, project_id)
        self.spec_path = self.resolve_path("artifacts", "spec", "technical-specification.md")
        self.arch_eval_suite_path = self.resolve_path("evals", "eval-suite-architecture.json")

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check SPEC_REVIEW entry conditions.

        Entry: Technical spec and Tier 2 eval suite must exist.
        """
        unmet = []
        if not os.path.isfile(self.spec_path):
            unmet.append(f"Technical spec not found at {self.spec_path}")
        if not os.path.isfile(self.arch_eval_suite_path):
            unmet.append(f"Tier 2 eval suite not found at {self.arch_eval_suite_path}")
        
        if unmet:
            return self._fail(unmet)
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check SPEC_REVIEW exit conditions.

        ALL required:
        1. User explicitly approves BOTH technical spec AND Tier 2 eval suite
        2. Approval recorded in approval_history
        3. Ready for transition to next stage
        """
        unmet = []
        
        ok, reason = self._artifact_is_proven(self.spec_path, state, require_approval=True, approval_alias="technical_specification")
        if not ok:
            unmet.append(f"Provenance check failed for {self.spec_path}: {reason}")
            
        ok, reason = self._artifact_is_proven(self.arch_eval_suite_path, state, require_approval=True, approval_alias="eval_suite_architecture")
        if not ok:
            unmet.append(f"Provenance check failed for {self.arch_eval_suite_path}: {reason}")

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
        
        if not spec_approved:
            unmet.append("Technical spec not approved")
        if not eval_approved:
            unmet.append("Tier 2 eval suite not approved")
        
        if unmet:
            return {
                **self._fail(unmet),
                "spec_approved": spec_approved,
                "eval_approved": eval_approved,
            }
        
        return {
            **self._pass(),
            "spec_approved": spec_approved,
            "eval_approved": eval_approved,
        }

