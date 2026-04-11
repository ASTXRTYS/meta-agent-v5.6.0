"""SPEC_GENERATION stage wiring.

Spec References: Sections 3.2, 3.2.1, 7.3

The SPEC_GENERATION stage handles technical specification authoring.
- spec-writer agent produces technical-specification.md
- Creates Tier 2 eval suite (eval-suite-architecture.json)
- Up to 5 feedback cycles (standardized across BaseStage)
"""

import json
import os
from typing import Any
from .base import BaseStage, ConditionResult
from meta_agent.state import WorkflowStage


class SpecGenerationStage(BaseStage):
    """Manages the SPEC_GENERATION stage of the workflow.

    The SPEC_GENERATION stage handles technical specification authoring.
    - spec-writer agent produces technical-specification.md
    - Creates Tier 2 eval suite (eval-suite-architecture.json)
    - Up to 5 revision cycles (standardized across BaseStage)
    """

    STAGE_NAME = WorkflowStage.SPEC_GENERATION.value

    def __init__(self, project_dir: str, project_id: str) -> None:
        super().__init__(project_dir, project_id)
        research_fixture = self.resolve_path("artifacts", "intake", "research-agent-prd.md")
        generic_prd = self.resolve_path("artifacts", "intake", "prd.md")
        self.prd_path = (
            research_fixture 
            if project_id == "meta-agent" and os.path.isfile(research_fixture) 
            else generic_prd
        )
        self.research_bundle_path = self.resolve_path("artifacts", "research", "research-bundle.md")
        self.spec_path = self.resolve_path("artifacts", "spec", "technical-specification.md")
        self.arch_eval_suite_path = self.resolve_path("evals", "eval-suite-architecture.json")
        self.tier1_eval_suite_path = self.resolve_path("evals", "eval-suite-prd.json")

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check SPEC_GENERATION entry conditions."""
        prd_path = state.get("current_prd_path") or self.prd_path
        unmet = []
        if not os.path.isfile(prd_path):
            unmet.append(f"PRD not found at {prd_path}")
        if not os.path.isfile(self.research_bundle_path):
            unmet.append(f"Research bundle not found at {self.research_bundle_path}")
        if not os.path.isfile(self.tier1_eval_suite_path):
            unmet.append(f"Tier 1 eval suite not found at {self.tier1_eval_suite_path}")
        
        if unmet:
            return self._fail(unmet)
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Check SPEC_GENERATION exit conditions per Section 3.2.

        ALL required:
        1. Technical spec written to correct path
        2. Tier 2 eval suite written and recorded in state
        3. Verification passed
        4. Feedback cycles not exceeded (enforced via BaseStage logic)
        """
        # Ensure we check against persisted feedback cycles
        self.sync_from_state(state)

        unmet = []
        
        ok, reason = self._artifact_is_proven(self.spec_path, state, require_approval=False)
        if not ok:
            unmet.append(f"Provenance check failed for {self.spec_path}: {reason}")
            
        ok, reason = self._artifact_is_proven(self.arch_eval_suite_path, state, require_approval=False)
        if not ok:
            unmet.append(f"Provenance check failed for {self.arch_eval_suite_path}: {reason}")

        # Standard artifact state tracking validation
        current_spec_path = state.get("current_spec_path")
        if current_spec_path and current_spec_path != self.spec_path:
            unmet.append(f"current_spec_path points to unexpected artifact: {current_spec_path}")
        if not current_spec_path and os.path.isfile(self.spec_path):
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

        # Standardized revision count check inherited from BaseStage strategy
        if self.at_revision_limit():
            unmet.append("Spec-generation feedback loop exceeded maximum cycles")

        if os.path.isfile(self.arch_eval_suite_path):
            try:
                with open(self.arch_eval_suite_path) as f:
                    tier2 = json.load(f)
                metadata = tier2.get("metadata", {})
                if metadata.get("artifact") != "eval-suite-architecture":
                    unmet.append("Tier 2 eval suite metadata.artifact is incorrect")
                if metadata.get("tier") != 2:
                    unmet.append("Tier 2 eval suite metadata.tier must equal 2")
                if metadata.get("created_by") != "spec-writer":
                    unmet.append("Tier 2 eval suite metadata.created_by must equal spec-writer")
            except (json.JSONDecodeError, IOError):
                unmet.append(f"Failed to read or parse Tier 2 eval suite at {self.arch_eval_suite_path}")

        if unmet:
            return self._fail(unmet)
        return self._pass()

