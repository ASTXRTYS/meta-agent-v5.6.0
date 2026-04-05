"""Code agent prompt composition.

Spec References: Section 7.2.2
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import (
    ARTIFACT_PROTOCOL_SECTION,
    TOOL_USAGE_SECTION,
    TOOL_BEST_PRACTICES_SECTION,
    QUALITY_STANDARDS_SECTION,
    CORE_BEHAVIOR_SECTION,
    HITL_PROTOCOL_SECTION,
    DELEGATION_SECTION,
    COMMUNICATION_SECTION,
    SKILLS_SECTION,
    format_workspace_section,
    format_stage_context,
    format_agents_md_section,
)


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Code_Agent_System_Prompt.md")


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_code_agent_prompt(
    project_dir: str,
    project_id: str = "",
    current_stage: str = "EXECUTION",
    current_task: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the code agent system prompt."""
    sections = [
        _load_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
        format_stage_context(current_stage, project_id),
        ARTIFACT_PROTOCOL_SECTION,
        TOOL_USAGE_SECTION,
        TOOL_BEST_PRACTICES_SECTION,
        QUALITY_STANDARDS_SECTION,
        CORE_BEHAVIOR_SECTION,
        HITL_PROTOCOL_SECTION,
        DELEGATION_SECTION,
        COMMUNICATION_SECTION,
        SKILLS_SECTION,
    ]
    if current_task:
        sections.append(f"## Current Task\n\n{current_task}")
    if agents_md:
        sections.append(format_agents_md_section(agents_md))
    return "\n\n---\n\n".join(sections)
