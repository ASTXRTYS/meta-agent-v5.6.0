"""SPEC_GENERATION stage wiring."""

from __future__ import annotations

import os
from typing import Any


class SpecGenerationStage:
    """Manages the SPEC_GENERATION stage of the workflow."""

    MAX_FEEDBACK_CYCLES = 3

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        self.prd_path = f"{project_dir}/artifacts/intake/prd.md"
        self.research_bundle_path = f"{project_dir}/artifacts/research/research-bundle.md"
        self.spec_path = f"{project_dir}/artifacts/spec/technical-specification.md"
        self.arch_eval_suite_path = f"{project_dir}/evals/eval-suite-architecture.json"
        self.feedback_cycles = 0

    def check_entry_conditions(self) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.prd_path):
            unmet.append(f"PRD not found at {self.prd_path}")
        if not os.path.isfile(self.research_bundle_path):
            unmet.append(f"Research bundle not found at {self.research_bundle_path}")
        return {"met": len(unmet) == 0, "unmet": unmet}

    def increment_feedback_cycle(self) -> bool:
        self.feedback_cycles += 1
        return self.feedback_cycles <= self.MAX_FEEDBACK_CYCLES

    def check_exit_conditions(self, state: dict[str, Any]) -> dict[str, Any]:
        unmet = []
        if not os.path.isfile(self.spec_path):
            unmet.append(f"Technical spec not found at {self.spec_path}")
        if not os.path.isfile(self.arch_eval_suite_path):
            unmet.append(f"Tier 2 eval suite not found at {self.arch_eval_suite_path}")
        if state.get("current_spec_path") not in {None, self.spec_path}:
            unmet.append(f"current_spec_path points to unexpected artifact: {state.get('current_spec_path')}")
        if not state.get("current_spec_path") and os.path.isfile(self.spec_path):
            unmet.append("current_spec_path not recorded in state")
        verification = state.get("verification_results", {}).get("technical_specification", {})
        status = verification.get("status")
        if status and status != "pass":
            unmet.append(f"Verification did not pass: {status}")
        eval_suites = set(state.get("eval_suites", []))
        if os.path.isfile(self.arch_eval_suite_path) and self.arch_eval_suite_path not in eval_suites:
            unmet.append("Tier 2 eval suite path not recorded in state.eval_suites")
        return {"met": len(unmet) == 0, "unmet": unmet}
