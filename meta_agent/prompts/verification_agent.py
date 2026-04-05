"""Verification agent prompt composition."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import format_agents_md_section, format_workspace_section


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Verification_Agent_System_Prompt.md")


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_verification_agent_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the verification agent system prompt."""
    sections = [
        _load_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
    ]
    if agents_md:
        sections.append(format_agents_md_section(agents_md))
    return "\n\n---\n\n".join(sections)
