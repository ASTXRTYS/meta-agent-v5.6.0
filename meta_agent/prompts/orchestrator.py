"""Orchestrator prompt composition function.

Spec References: Sections 7.3, 22.15

Assembles the orchestrator system prompt based on current stage
using stage-aware section loading.
"""

from __future__ import annotations

from .sections import (
    ROLE_SECTION,
    CORE_BEHAVIOR_SECTION,
    ARTIFACT_PROTOCOL_SECTION,
    HITL_PROTOCOL_SECTION,
    COMMUNICATION_SECTION,
    DELEGATION_SECTION,
    MEMORY_SECTION,
    format_workspace_section,
    format_stage_context,
    format_agents_md_section,
    format_memory_section,
)
from .eval_mindset import EVAL_MINDSET_SECTION
from .eval_engineering import EVAL_ENGINEERING_SECTION
from .scoring_strategy import SCORING_STRATEGY_SECTION
from .eval_approval_protocol import EVAL_APPROVAL_PROTOCOL


def construct_orchestrator_prompt(
    stage: str,
    project_dir: str,
    project_id: str,
    agents_md_content: str = "",
) -> str:
    """Assembles the orchestrator system prompt based on current stage.

    Per Section 7.3, sections are loaded conditionally based on stage
    to reduce cognitive load.
    """
    # Always included
    sections = [
        ROLE_SECTION,
        EVAL_MINDSET_SECTION,
        EVAL_ENGINEERING_SECTION,
        CORE_BEHAVIOR_SECTION,
        ARTIFACT_PROTOCOL_SECTION,
        format_workspace_section(project_dir, project_id),
        HITL_PROTOCOL_SECTION,
        COMMUNICATION_SECTION,
        format_memory_section(project_dir),
    ]

    # Stage-specific context
    sections.append(format_stage_context(stage, project_id))

    # Stage-conditional sections
    if stage in ("INTAKE", "PRD_REVIEW", "SPEC_REVIEW"):
        sections.append(EVAL_APPROVAL_PROTOCOL)

    if stage in ("INTAKE", "SPEC_REVIEW"):
        sections.append(SCORING_STRATEGY_SECTION)

    if stage in ("RESEARCH", "SPEC_GENERATION", "PLANNING", "EXECUTION"):
        sections.append(DELEGATION_SECTION)

    # Runtime-injected memory (always last)
    if agents_md_content:
        sections.append(format_agents_md_section(agents_md_content))

    return "\n\n---\n\n".join(sections)
