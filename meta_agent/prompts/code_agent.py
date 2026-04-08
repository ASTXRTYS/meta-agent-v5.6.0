"""Code agent prompt composition.

Spec References: Section 7.2.2

The code-agent prompt is monolithic — the .md file is self-contained.
This loader reads it and injects only the workspace context and current task.

See Also:
    - `sections.format_workspace_section()` — shared utility
    - `sections.format_agents_md_section()` — shared utility

Note: Shared utilities consolidation TODO in sections.py lines 611-618.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


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
    agents_md: str = "",  # TODO: Unused parameter. Either wire up via format_agents_md_section() or remove.
) -> str:
    """Assemble the code agent system prompt.

    The .md file is self-contained.  Only runtime context
    (project_dir, project_id, current_task) is injected.
    """
    prompt = _load_prompt_markdown()

    # TODO: Use sections.format_workspace_section(project_dir, project_id)
    # instead of inline f-string construction. See research_agent.py pattern.
    workspace_block = (
        f"\n\n---\n\n## Workspace Context\n\n"
        f"- **Project directory:** `{project_dir}`\n"
        f"- **Project ID:** `{project_id}`\n"
        f"- **Current stage:** `{current_stage}`\n"
    )
    prompt += workspace_block

    # TODO: Use list-based assembly: sections = [..., current_task_section]
    # then "\n\n---\n\n".join(sections) for consistent separators
    if current_task:
        prompt += f"\n\n---\n\n## Current Task\n\n{current_task}"

    return prompt
