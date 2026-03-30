"""SPEC_GENERATION stage wiring."""

from __future__ import annotations

import json
import os
from typing import Any


class SpecGenerationStage:
    """Manages the SPEC_GENERATION stage of the workflow."""

    MAX_FEEDBACK_CYCLES = 3

    def __init__(self, project_dir: str, project_id: str) -> None:
        self.project_dir = project_dir
        self.project_id = project_id
        research_fixture = os.path.join(project_dir, "artifacts", "intake", "research-agent-prd.md")
        generic_prd = os.path.join(project_dir, "artifacts", "intake", "prd.md")
        self.prd_path = research_fixture if project_id == "meta-agent" and os.path.isfile(research_fixture) else generic_prd
        self.research_bundle_path = f"{project_dir}/artifacts/research/research-bundle.md"
        self.spec_path = f"{project_dir}/artifacts/spec/technical-specification.md"
        self.arch_eval_suite_path = f"{project_dir}/evals/eval-suite-architecture.json"
        self.tier1_eval_suite_path = f"{project_dir}/evals/eval-suite-prd.json"
        self.feedback_cycles = 0

    def check_entry_conditions(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        state = state or {}
        prd_path = state.get("current_prd_path") or self.prd_path
        unmet = []
        if not os.path.isfile(prd_path):
            unmet.append(f"PRD not found at {prd_path}")
        if not os.path.isfile(self.research_bundle_path):
            unmet.append(f"Research bundle not found at {self.research_bundle_path}")
        if not os.path.isfile(self.tier1_eval_suite_path):
            unmet.append(f"Tier 1 eval suite not found at {self.tier1_eval_suite_path}")
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
        if status != "pass":
            unmet.append(f"Verification did not pass: {status}")
        eval_suites = set(state.get("eval_suites", []))
        if self.tier1_eval_suite_path not in eval_suites:
            unmet.append("Tier 1 eval suite path not recorded in state.eval_suites")
        if os.path.isfile(self.arch_eval_suite_path) and self.arch_eval_suite_path not in eval_suites:
            unmet.append("Tier 2 eval suite path not recorded in state.eval_suites")
        if int(state.get("spec_generation_feedback_cycles", 0)) > self.MAX_FEEDBACK_CYCLES:
            unmet.append("Spec-generation feedback loop exceeded maximum cycles")

        if os.path.isfile(self.arch_eval_suite_path):
            with open(self.arch_eval_suite_path) as f:
                tier2 = json.load(f)
            metadata = tier2.get("metadata", {})
            if metadata.get("artifact") != "eval-suite-architecture":
                unmet.append("Tier 2 eval suite metadata.artifact is incorrect")
            if metadata.get("tier") != 2:
                unmet.append("Tier 2 eval suite metadata.tier must equal 2")
            if metadata.get("created_by") != "spec-writer":
                unmet.append("Tier 2 eval suite metadata.created_by must equal spec-writer")
        return {"met": len(unmet) == 0, "unmet": unmet}
