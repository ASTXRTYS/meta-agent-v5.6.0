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
MIN_CLARIFYING_QUESTIONS = 3
MAX_CLARIFYING_QUESTIONS = 7

# Maximum revision cycles in PRD_REVIEW
MAX_REVISION_CYCLES = 5


class IntakeStage:
    """Manages the INTAKE stage of the workflow.

    Implements the Interactive Eval Creation Experience (Section 15.11):
    1. User describes project idea
    2. Orchestrator asks 3-7 clarifying questions
    3. Orchestrator confirms requirements
    4. Orchestrator writes PRD via write_file
    5. Orchestrator proposes eval suite with scoring strategies
    6. Explains scoring choices with <pm_reasoning>
    7. Hard gate: eval approval
    """

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = f"{project_dir}/artifacts/intake/prd.md"
        self.eval_suite_path = f"{project_dir}/evals/eval-suite-prd.json"

    def check_entry_conditions(self) -> dict[str, Any]:
        """Check INTAKE entry conditions.

        Entry: User initiated a new conversation with a product idea.
        """
        return {
            "met": True,
            "reason": "INTAKE has no prerequisites — always enterable",
        }

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
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

        return {
            "met": len(unmet) == 0,
            "unmet": unmet,
        }

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


def _get_field(obj: Any, field: str) -> Any:
    """Get a field from either a dataclass or a dict."""
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field)
    return None
