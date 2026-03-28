"""Plan writer agent prompt composition.

Spec References: Section 7.2.2
"""

from __future__ import annotations

from .sections import (
    ARTIFACT_PROTOCOL_SECTION,
    TOOL_USAGE_SECTION,
    QUALITY_STANDARDS_SECTION,
    CORE_BEHAVIOR_SECTION,
    COMMUNICATION_SECTION,
    SKILLS_SECTION,
    format_workspace_section,
)

PLAN_WRITER_ROLE = """You are the Plan Writer Agent — an expert in development lifecycle planning within the LangChain ecosystem. You create actionable implementation plans with eval-phase mapping, phase gates, and observation criteria. You treat LangSmith as a first-class tool in your plans."""


def construct_plan_writer_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the plan writer agent system prompt."""
    sections = [
        PLAN_WRITER_ROLE,
        format_workspace_section(project_dir, project_id),
        ARTIFACT_PROTOCOL_SECTION,
        TOOL_USAGE_SECTION,
        QUALITY_STANDARDS_SECTION,
        CORE_BEHAVIOR_SECTION,
        COMMUNICATION_SECTION,
        SKILLS_SECTION,
    ]
    return "\n\n---\n\n".join(sections)
