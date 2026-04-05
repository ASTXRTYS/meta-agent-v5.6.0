"""Plan writer agent prompt composition.

Spec References: Section 7.2.2
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import (
    ARTIFACT_PROTOCOL_SECTION,
    TOOL_USAGE_SECTION,
    QUALITY_STANDARDS_SECTION,
    CORE_BEHAVIOR_SECTION,
    COMMUNICATION_SECTION,
    SKILLS_SECTION,
    format_workspace_section,
)


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Plan_Writer_System_Prompt.md")


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_plan_writer_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the plan writer agent system prompt."""
    sections = [
        _load_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
        ARTIFACT_PROTOCOL_SECTION,
        TOOL_USAGE_SECTION,
        QUALITY_STANDARDS_SECTION,
        CORE_BEHAVIOR_SECTION,
        COMMUNICATION_SECTION,
        SKILLS_SECTION,
    ]
    return "\n\n---\n\n".join(sections)
