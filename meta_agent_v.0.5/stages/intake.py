"""INTAKE stage wiring.

Spec References: Sections 3.1, 3.1.1, 7.3, 15.11 

The INTAKE stage handles requirements gathering, PRD authoring (by the
orchestrator directly — NOT delegated), and eval suite creation.

Key behaviors:
- Orchestrator writes PRD DIRECTLY using write_file
- Interactive eval creation experience (Section 15.11)
- PRD at {project_dir}/artifacts/intake/prd.md with YAML frontmatter
- Tier 1 eval suite at {project_dir}/evals/eval-suite-prd.json
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from .base import BaseStage, ConditionResult
from .common import _get_field
from meta_agent.state import WorkflowStage

try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False


# ---------------------------------------------------------------------------
# PRD frontmatter template — Section 5.2
# ---------------------------------------------------------------------------

PRD_FRONTMATTER_TEMPLATE = {
    "artifact": "prd",
    "version": "1.0.0",
    "status": "draft",
    "stage": "INTAKE",
    "authors": ["pm"],
    "lineage": [],
}

# Required PRD sections per Section 5.2
REQUIRED_PRD_SECTIONS = [
    "Product Summary",
    "Goals",
    "Non-Goals",
    "Constraints",
    "Target User",
    "Core User Workflows",
    "Functional Requirements",
    "Acceptance Criteria",
    "Risks",
    "Unresolved Questions",
]

# Maximum clarifying questions before drafting PRD
MIN_CLARIFYING_QUESTIONS = 3 ## would like to make this configurable eventually in UI
MAX_CLARIFYING_QUESTIONS = 7 ## would like to make this configurable eventually in UI


class IntakeStage(BaseStage):
    """Manages the INTAKE stage of the workflow.

    Implements the Interactive Eval Creation Experience (Section 15.11):
    1. User describes project idea
    2. Orchestrator asks `N` clarifying questions (where N is configurable)
    3. Orchestrator confirms requirements
    4. Orchestrator writes PRD via write_file
    5. Orchestrator proposes eval suite with scoring strategies
    6. Explains scoring choices with <pm_reasoning>
    7. Hard gate: eval approval
    """

    STAGE_NAME = WorkflowStage.INTAKE.value

    def __init__(self, project_dir: str, project_id: str) -> None:
        super().__init__(project_dir, project_id)
        self.prd_path = self.resolve_path("artifacts", "intake", "prd.md")
        self.eval_suite_path = self.resolve_path("evals", "eval-suite-prd.json")

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check INTAKE entry conditions.

        Entry: User initiated a new conversation with a product idea.
        """
        return {
            **self._pass(),
            "reason": "INTAKE has no prerequisites — always enterable",
        }

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check INTAKE exit conditions per Section 3.1.

        ALL required:
        1. PRD artifact written to correct path
        2. Eval suite written to correct path
        3. User has explicitly approved BOTH
        4. Document-renderer has produced DOCX/PDF versions
        """
        unmet = []

        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")

        if not os.path.isfile(self.eval_suite_path):
            unmet.append(f"Eval suite not found at {self.eval_suite_path}")

        # Check approval
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
            unmet.append("PRD not approved by user")
        if not eval_approved:
            unmet.append("Eval suite not approved by user")

        if unmet:
            return self._fail(unmet)
        return self._pass()

    def build_prd_frontmatter(
        self,
        title: str,
        project_id: str | None = None,
    ) -> str:
        """Build YAML frontmatter for a PRD artifact per Section 5.2."""
        fm = {
            **PRD_FRONTMATTER_TEMPLATE,
            "project_id": project_id or self.project_id,
            "title": title,
        }

        if HAS_YAML:
            return f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---\n"
        else:
            # Fallback for environments without PyYAML
            lines = ["---"]
            for k, v in fm.items():
                if isinstance(v, list):
                    lines.append(f"{k}:")
                    for item in v:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{k}: {v}")
            lines.append("---")
            return "\n".join(lines) + "\n"

    def validate_prd_sections(self, content: str) -> dict[str, Any]:
        """Validate that a PRD contains all 10 required sections."""
        content_lower = content.lower()
        missing = [s for s in REQUIRED_PRD_SECTIONS if s.lower() not in content_lower]
        return {
            "valid": len(missing) == 0,
            "missing_sections": missing,
        }


