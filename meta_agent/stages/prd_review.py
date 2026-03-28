"""PRD_REVIEW stage wiring.

Spec References: Sections 3.2, 7.3, 9.2

The PRD_REVIEW stage handles user review of the PRD and eval suite.
Eval suite approval is a HARD GATE — process does not proceed without
explicit user approval of BOTH the PRD AND the eval suite.

All 7 user response branches per EVAL_APPROVAL_PROTOCOL:
1. "approved"/"looks good"/"yes" -> confirm, mark approved
2. "modify EVAL-XXX" -> ask what, present modified, re-present table
3. "add an eval for X" -> clarify, propose, add
4. "remove EVAL-XXX" -> confirm consequences, remove
5. Remove ALL evals -> push back firmly
6. Unclear/off-topic -> gently redirect
7. Change scoring strategy -> discuss tradeoff
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from meta_agent.state import ApprovalEntry


# Maximum revision cycles before direct question
MAX_REVISION_CYCLES = 5

# Approval intent patterns
APPROVAL_PATTERNS = [
    "approved", "looks good", "yes", "lgtm", "ship it",
    "approve", "good to go", "proceed",
]


class PrdReviewStage:
    """Manages the PRD_REVIEW stage of the workflow.

    Implements the eval approval hard gate and all 7 response branches
    per EVAL_APPROVAL_PROTOCOL (Section 7.3).
    """

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = f"{project_dir}/artifacts/intake/prd.md"
        self.eval_suite_path = f"{project_dir}/evals/eval-suite-prd.yaml"
        self.revision_count = 0

    def check_entry_conditions(self) -> dict[str, Any]:
        """Check PRD_REVIEW entry conditions.

        Entry: Draft PRD and eval suite exist.
        """
        unmet = []
        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")

        return {
            "met": len(unmet) == 0,
            "unmet": unmet,
        }

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check PRD_REVIEW exit conditions.

        ALL required:
        1. User explicitly approves BOTH PRD AND eval suite
        2. Approval recorded in approval_history
        3. Ready for transition to RESEARCH
        """
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

        unmet = []
        if not prd_approved:
            unmet.append("PRD not approved")
        if not eval_approved:
            unmet.append("Eval suite not approved (HARD GATE)")

        return {
            "met": len(unmet) == 0,
            "unmet": unmet,
            "prd_approved": prd_approved,
            "eval_approved": eval_approved,
        }

    def classify_user_response(self, content: str) -> str:
        """Classify user response into one of 7 EVAL_APPROVAL_PROTOCOL branches.

        Returns one of: 'approval', 'modify', 'add', 'remove', 'remove_all',
        'unclear', 'change_scoring'
        """
        lower = content.lower().strip()

        # Branch 1: Approval
        if any(p in lower for p in APPROVAL_PATTERNS):
            return "approval"

        # Branch 2: Modify specific eval
        if "modify" in lower and "eval" in lower:
            return "modify"
        if "change" in lower and "eval-" in lower:
            return "modify"

        # Branch 3: Add an eval
        if "add" in lower and "eval" in lower:
            return "add"

        # Branch 4: Remove specific eval
        if "remove" in lower and "eval-" in lower:
            return "remove"

        # Branch 5: Remove ALL evals
        if "remove" in lower and "all" in lower and "eval" in lower:
            return "remove_all"
        if "skip" in lower and "eval" in lower:
            return "remove_all"
        if "no eval" in lower or "don't need eval" in lower:
            return "remove_all"

        # Branch 7: Change scoring strategy
        if "scoring" in lower or "binary" in lower or "likert" in lower:
            if "change" in lower or "switch" in lower or "use" in lower:
                return "change_scoring"

        # Branch 6: Unclear/off-topic
        return "unclear"

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

    def increment_revision_count(self) -> bool:
        """Increment revision counter. Returns True if still under limit."""
        self.revision_count += 1
        return self.revision_count < MAX_REVISION_CYCLES

    def at_revision_limit(self) -> bool:
        """Check if max revision cycles have been reached."""
        return self.revision_count >= MAX_REVISION_CYCLES


def _get_field(obj: Any, field: str) -> Any:
    """Get a field from either a dataclass or a dict."""
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None
