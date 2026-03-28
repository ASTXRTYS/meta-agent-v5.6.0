"""Spec writer agent prompt composition.

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

SPEC_WRITER_ROLE = """You are the Spec Writer Agent — an expert in translating product requirements and research findings into implementation-ready technical specifications. You produce detailed architecture documents, identify every design decision, and ensure full PRD traceability."""


def construct_spec_writer_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the spec writer agent system prompt."""
    sections = [
        SPEC_WRITER_ROLE,
        format_workspace_section(project_dir, project_id),
        ARTIFACT_PROTOCOL_SECTION,
        TOOL_USAGE_SECTION,
        QUALITY_STANDARDS_SECTION,
        CORE_BEHAVIOR_SECTION,
        COMMUNICATION_SECTION,
        SKILLS_SECTION,
    ]
    return "\n\n---\n\n".join(sections)
