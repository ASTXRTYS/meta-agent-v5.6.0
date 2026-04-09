"""PRD_REVIEW stage wiring.

Spec References: Sections 3.2, 7.3, 9.2

The PRD_REVIEW stage handles user review of the PRD and eval suite.
Eval suite approval is a HARD GATE — process does not proceed without
explicit user approval of BOTH the PRD AND the eval suite.

Intent classification for the 7 EVAL_APPROVAL_PROTOCOL branches is handled
entirely by the LLM via the system prompt (see prompts/eval_approval_protocol.py).
The AskUserMiddleware provides a structured `ask_user` tool so the agent can
pose multiple-choice questions during review (see middleware/ask_user.py).
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from meta_agent.utils.artifact_validator import validate
from .base import BaseStage, ConditionResult
from meta_agent.state import ApprovalEntry, WorkflowStage
from .common import _get_field


class PrdReviewStage(BaseStage):
    """Manages the PRD_REVIEW stage of the workflow.

    Implements the eval approval hard gate per Section 7.3.
    The 7 EVAL_APPROVAL_PROTOCOL response branches are handled by the LLM
    via system prompt instructions — no code-side classification is needed.
    """

    STAGE_NAME = WorkflowStage.PRD_REVIEW.value

    def __init__(self, project_dir: str, project_id: str) -> None:
        super().__init__(project_dir, project_id)
        self.prd_path = self.resolve_path("artifacts", "intake", "prd.md")
        self.eval_suite_path = self.resolve_path("evals", "eval-suite-prd.json")

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check PRD_REVIEW entry conditions.

        Entry: Draft PRD and eval suite exist.
        """
        unmet = []
        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")
        if not os.path.isfile(self.eval_suite_path):
            unmet.append(f"Eval suite not found at {self.eval_suite_path}")

        if unmet:
            return self._fail(unmet)
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check PRD_REVIEW exit conditions.

        ALL required:
        1. User explicitly approves BOTH PRD AND eval suite
        2. Approval recorded in approval_history
        3. Ready for transition to RESEARCH
        """
        unmet = []
        ok, reason = self._artifact_is_proven(self.prd_path, state, require_approval=True, approval_alias="prd")
        if not ok:
            unmet.append(f"Provenance check failed for {self.prd_path}: {reason}")
        else:
            val_ok, val_reason = self._run_artifact_validation(self.prd_path, "prd", state)
            if not val_ok:
                unmet.append(f"Protocol validation failed for PRD: {val_reason}")
            
        ok, reason = self._artifact_is_proven(self.eval_suite_path, state, require_approval=True, approval_alias="eval_suite")
        if not ok:
            unmet.append(f"Provenance check failed for {self.eval_suite_path}: {reason}")
        else:
            val_ok, val_reason = self._run_artifact_validation(self.eval_suite_path, "eval-suite", state)
            if not val_ok:
                unmet.append(f"Protocol validation failed for Eval Suite: {val_reason}")

        approvals = state.get("approval_history", [])

        prd_approved = any(
            _get_field(a, "artifact") == "prd"
            and _get_field(a, "action") == "approved"
            for a in approvals
        )
        eval_approved = any(
            _get_field(a, "artifact") == "eval_suite"
            and _get_field(a, "action") == "approved"
            for a in approvals
        )

        if not prd_approved:
            unmet.append("PRD not approved")
        if not eval_approved:
            unmet.append("Eval suite not approved (HARD GATE)")

        if unmet:
            return {
                **self._fail(unmet),
                "prd_approved": prd_approved,
                "eval_approved": eval_approved,
            }
        
        return {
            **self._pass(),
            "prd_approved": prd_approved,
            "eval_approved": eval_approved,
        }

    def record_approval(
        self,
        artifact: str,
        reviewer: str = "user",
        comments: str = "",
    ) -> ApprovalEntry:
        """Record an approval in approval_history."""
        return ApprovalEntry.create(
            stage="PRD_REVIEW",
            artifact=artifact,
            action="approved",
            reviewer=reviewer,
        )

    def _run_artifact_validation(self, artifact_path: str, protocol_id: str, state: dict[str, Any]) -> tuple[bool, str]:
        """Run structural validation against the registered YAML protocol."""
        protocols = state.get("artifact_protocols", {}) or {}
        protocol = protocols.get(protocol_id)
        if not protocol:
            # If no protocol is registered, we can't strict-validate, so pass.
            return True, ""
            
        if not os.path.isfile(artifact_path):
            return False, "File not found"
            
        with open(artifact_path, "r") as f:
            content = f.read()
            
        result = validate(content, protocol)
        if not result.passed:
            details = ", ".join(v.detail for v in result.violations)
            return False, details
            
        return True, ""



