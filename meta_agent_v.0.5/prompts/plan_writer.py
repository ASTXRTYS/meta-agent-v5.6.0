"""Plan writer agent prompt composition.

Spec References: Section 7.2.2

The plan-writer prompt is monolithic — the .md file is self-contained.
This loader reads it and injects only the workspace context.

See Also:
    - `sections.format_workspace_section()` — shared utility
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from meta_agent.prompts.sections import format_workspace_section


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Plan_Writer_System_Prompt.md")


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_plan_writer_prompt(
    project_dir: str,
    project_id: str = "",
) -> str:
    """Assemble the plan writer agent system prompt.

    The .md file is self-contained.  Only the workspace context
    (project_dir, project_id) is injected at runtime.
    """
    prompt = _load_prompt_markdown()
    return prompt + format_workspace_section(project_dir, project_id)
