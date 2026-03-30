"""Infrastructure evals: INFRA-001 through INFRA-008.

Spec References: Sections 15.14.2, 0.3.2, 1.3.2

Phase 0 evals:
- INFRA-001: Project directory structure
- INFRA-002: PRD artifact path
- INFRA-003: PRD frontmatter validation
- INFRA-004: PRD required sections

Phase 1 evals:
- INFRA-005: Eval suite artifact exists
- INFRA-006: Eval suite schema valid
- INFRA-007: Per-agent AGENTS.md created
- INFRA-008: Dynamic prompt recomposition after stage transition
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Phase 0 evals (INFRA-001 through INFRA-004)
# ---------------------------------------------------------------------------

def eval_infra_001_project_directory_structure(project_dir: str) -> dict[str, Any]:
    """INFRA-001: Project directory structure is created correctly.

    Verifies the orchestrator creates the full expected directory tree
    for a new project, including artifacts, evals, logs, and .agents directories.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    required_dirs = [
        project_dir,
        f"{project_dir}/artifacts/",
        f"{project_dir}/artifacts/intake/",
        f"{project_dir}/artifacts/research/",
        f"{project_dir}/artifacts/spec/",
        f"{project_dir}/artifacts/planning/",
        f"{project_dir}/evals/",
        f"{project_dir}/logs/",
        f"{project_dir}/.agents/orchestrator/",
    ]
    missing = [d for d in required_dirs if not os.path.isdir(d)]
    return {
        "pass": len(missing) == 0,
        "reason": f"Missing directories: {missing}" if missing else "All directories present",
    }


def eval_infra_002_prd_artifact_path(project_dir: str) -> dict[str, Any]:
    """INFRA-002: PRD artifact written to correct path.

    Verifies the PRD markdown file exists at the canonical path:
    {project_dir}/artifacts/intake/prd.md

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    expected_path = f"{project_dir}/artifacts/intake/prd.md"
    exists = os.path.isfile(expected_path)
    return {
        "pass": exists,
        "reason": f"PRD exists at {expected_path}" if exists else f"PRD not found at {expected_path}",
    }


def eval_infra_003_prd_frontmatter_valid(project_dir: str) -> dict[str, Any]:
    """INFRA-003: PRD has valid YAML frontmatter with required fields.

    Verifies the PRD begins with valid YAML frontmatter (--- delimited)
    and contains all required metadata fields.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    prd_path = f"{project_dir}/artifacts/intake/prd.md"
    required_fields = [
        "artifact", "project_id", "title", "version",
        "status", "stage", "authors", "lineage",
    ]
    try:
        with open(prd_path) as f:
            content = f.read()
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {
                "pass": False,
                "reason": "No YAML frontmatter found (missing --- delimiters)",
            }
        if yaml is not None:
            frontmatter = yaml.safe_load(parts[1])
        else:
            # Basic fallback parsing
            frontmatter = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key = line.split(":", 1)[0].strip()
                    frontmatter[key] = True
        if not isinstance(frontmatter, dict):
            return {"pass": False, "reason": "Frontmatter is not a valid YAML mapping"}
        missing = [f for f in required_fields if f not in frontmatter]
        if missing:
            return {"pass": False, "reason": f"Missing required fields: {missing}"}
        return {"pass": True, "reason": "All required frontmatter fields present"}
    except Exception as e:
        return {"pass": False, "reason": f"Error parsing PRD: {e}"}


def eval_infra_004_prd_required_sections(project_dir: str) -> dict[str, Any]:
    """INFRA-004: PRD contains all required sections.

    Verifies the PRD body contains all mandatory sections as
    H2 (##) or H3 (###) headers.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    prd_path = f"{project_dir}/artifacts/intake/prd.md"
    required_sections = [
        "Product Summary", "Goals", "Non-Goals", "Constraints",
        "Target User", "Core User Workflows", "Functional Requirements",
        "Acceptance Criteria", "Risks", "Unresolved Questions",
    ]
    try:
        with open(prd_path) as f:
            content = f.read().lower()
        missing = [s for s in required_sections if s.lower() not in content]
        return {
            "pass": len(missing) == 0,
            "reason": f"Missing sections: {missing}" if missing else "All required sections present",
        }
    except Exception as e:
        return {"pass": False, "reason": f"Error reading PRD: {e}"}


# ---------------------------------------------------------------------------
# Phase 1 evals (INFRA-005 through INFRA-008)
# ---------------------------------------------------------------------------

def eval_infra_005_eval_suite_artifact_exists(project_dir: str) -> dict[str, Any]:
    """INFRA-005: Eval suite artifact created alongside PRD.

    Verifies the orchestrator creates a proposed eval suite JSON file
    in the evals directory.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    eval_path = f"{project_dir}/evals/eval-suite-prd.json"
    exists = os.path.isfile(eval_path)
    return {
        "pass": exists,
        "reason": f"Eval suite exists at {eval_path}" if exists else f"Eval suite not found at {eval_path}",
    }


def eval_infra_006_eval_suite_schema_valid(project_dir: str) -> dict[str, Any]:
    """INFRA-006: Each eval in proposed suite has required fields.

    Verifies every eval entry in eval-suite-prd.json contains
    all required structural fields.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    eval_path = f"{project_dir}/evals/eval-suite-prd.json"
    required_per_eval = ["id", "name", "category", "input", "expected", "scoring"]
    try:
        with open(eval_path) as f:
            data = json.load(f)
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            return {"pass": False, "reason": "Missing metadata object"}
        evals = data.get("evals", [])
        if not evals:
            return {"pass": False, "reason": "No evals found in suite"}
        for ev in evals:
            missing = [f for f in required_per_eval if f not in ev]
            if missing:
                return {"pass": False, "reason": f"Eval {ev.get('id', 'unknown')} missing fields: {missing}"}
        return {"pass": True, "reason": f"All {len(evals)} evals have required fields"}
    except Exception as e:
        return {"pass": False, "reason": f"Error parsing eval suite: {e}"}


def eval_infra_007_agents_md_created(project_dir: str) -> dict[str, Any]:
    """INFRA-007: Per-agent AGENTS.md files are created for orchestrator.

    Verifies the orchestrator's project-specific AGENTS.md file
    is created during project initialization.

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    agents_md_path = f"{project_dir}/.agents/orchestrator/AGENTS.md"
    exists = os.path.isfile(agents_md_path)
    return {
        "pass": exists,
        "reason": "Orchestrator AGENTS.md exists" if exists else f"Not found: {agents_md_path}",
    }


def eval_infra_008_dynamic_prompt_after_transition(
    agent: Any = None,
    config: dict[str, Any] | None = None,
    project_dir: str = "",
    project_id: str = "",
) -> dict[str, Any]:
    """INFRA-008: System prompt changes after stage transition.

    When called with a real agent and config, invokes the agent and verifies
    dynamic prompt recomposition end-to-end (makes real LLM calls).

    When called without an agent, falls back to middleware-only testing.

    Tests that:
    1. During INTAKE, the prompt contains SCORING_STRATEGY_SECTION
    2. After transition to RESEARCH, the prompt contains DELEGATION_SECTION
       and does NOT contain SCORING_STRATEGY_SECTION

    Priority: P0 (every build)
    Scoring: Binary pass/fail
    """
    if agent is not None and config is not None:
        return _infra_008_real_agent(agent, config)
    return _infra_008_middleware_only(project_dir, project_id)


def _infra_008_real_agent(agent: Any, config: dict[str, Any]) -> dict[str, Any]:
    """INFRA-008 real agent version — invokes agent, checks state, updates stage."""
    from langchain_core.messages import SystemMessage

    try:
        # Step 1: Invoke in INTAKE stage and capture system message
        agent.invoke(
            {"messages": [{"role": "user", "content": "Starting a new project"}]},
            config=config,
        )
        intake_state = agent.get_state(config)
        intake_messages = intake_state.values.get("messages", [])
        intake_system = next(
            (m for m in intake_messages if isinstance(m, SystemMessage)), None
        )

        if intake_system is None:
            return {"pass": False, "reason": "No SystemMessage found during INTAKE"}

        if "Scoring Strategy Selection" not in intake_system.content:
            return {"pass": False, "reason": "SCORING_STRATEGY_SECTION missing during INTAKE"}
        if "Delegation Protocol" in intake_system.content:
            return {"pass": False, "reason": "DELEGATION_SECTION should NOT be present during INTAKE"}

        # Step 2: Simulate transition to RESEARCH
        agent.update_state(config, {"current_stage": "RESEARCH"})

        # Step 3: Invoke again and capture new system message
        agent.invoke(
            {"messages": [{"role": "user", "content": "Continue"}]},
            config=config,
        )
        research_state = agent.get_state(config)
        research_messages = research_state.values.get("messages", [])
        research_system = next(
            (m for m in research_messages if isinstance(m, SystemMessage)), None
        )

        if research_system is None:
            return {"pass": False, "reason": "No SystemMessage found during RESEARCH"}

        if "Delegation Protocol" not in research_system.content:
            return {"pass": False, "reason": "DELEGATION_SECTION missing during RESEARCH"}
        if "Scoring Strategy Selection" in research_system.content:
            return {"pass": False, "reason": "SCORING_STRATEGY_SECTION should NOT be present during RESEARCH"}

        if intake_system.content == research_system.content:
            return {"pass": False, "reason": "System prompt did NOT change between INTAKE and RESEARCH"}

        return {
            "pass": True,
            "reason": "System prompt correctly recomposed: INTAKE has SCORING_STRATEGY, RESEARCH has DELEGATION",
        }
    except Exception as e:
        return {"pass": False, "reason": f"Real agent invocation failed: {e}"}


def _infra_008_middleware_only(
    project_dir: str = "",
    project_id: str = "",
) -> dict[str, Any]:
    """INFRA-008 middleware-only fallback — no LLM calls."""
    from meta_agent.middleware.dynamic_system_prompt import DynamicSystemPromptMiddleware

    mw = DynamicSystemPromptMiddleware(
        project_dir=project_dir or "/workspace/projects/test",
        project_id=project_id or "test-project",
    )

    intake_state = {"current_stage": "INTAKE", "messages": []}
    intake_result = mw.before_model_legacy(intake_state)
    intake_messages = intake_result.get("messages", [])
    intake_system = None
    for msg in intake_messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            intake_system = msg["content"]
            break

    if intake_system is None:
        return {"pass": False, "reason": "No system message found during INTAKE"}
    if "Scoring Strategy Selection" not in intake_system:
        return {"pass": False, "reason": "SCORING_STRATEGY_SECTION missing during INTAKE"}
    if "Delegation Protocol" in intake_system:
        return {"pass": False, "reason": "DELEGATION_SECTION should NOT be present during INTAKE"}

    research_state = {"current_stage": "RESEARCH", "messages": []}
    research_result = mw.before_model_legacy(research_state)
    research_messages = research_result.get("messages", [])
    research_system = None
    for msg in research_messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            research_system = msg["content"]
            break

    if research_system is None:
        return {"pass": False, "reason": "No system message found during RESEARCH"}
    if "Delegation Protocol" not in research_system:
        return {"pass": False, "reason": "DELEGATION_SECTION missing during RESEARCH"}
    if "Scoring Strategy Selection" in research_system:
        return {"pass": False, "reason": "SCORING_STRATEGY_SECTION should NOT be present during RESEARCH"}

    if intake_system == research_system:
        return {"pass": False, "reason": "System prompt did NOT change between INTAKE and RESEARCH"}

    return {
        "pass": True,
        "reason": "System prompt correctly recomposed: INTAKE has SCORING_STRATEGY, RESEARCH has DELEGATION",
    }
