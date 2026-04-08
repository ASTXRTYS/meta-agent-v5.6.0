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
from datetime import datetime, timezone
from typing import Any

from meta_agent.state import ApprovalEntry


# Maximum revision cycles before direct question
MAX_REVISION_CYCLES = 5 ## would like to make this configurable eventually in UI


class PrdReviewStage:
    """Manages the PRD_REVIEW stage of the workflow.

    Implements the eval approval hard gate per Section 7.3.
    The 7 EVAL_APPROVAL_PROTOCOL response branches are handled by the LLM
    via system prompt instructions — no code-side classification is needed.
    """

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = f"{project_dir}/artifacts/intake/prd.md"
        self.eval_suite_path = f"{project_dir}/evals/eval-suite-prd.json"
        self.revision_count = 0

    def check_entry_conditions(self) -> dict[str, Any]:
        """Check PRD_REVIEW entry conditions.

        Entry: Draft PRD and eval suite exist.
        """
        unmet = []
        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")
        # FIXME: Eval suite path is not validated here despite docstring claiming
        # "Draft PRD and eval suite exist" as entry condition. Add check for
        # self.eval_suite_path to match the documented hard gate semantics.

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
    """Get a field from either a dataclass or a dict.
    
    Note: Helper duplication consolidation TODO in stages/__init__.py.
    """
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None
