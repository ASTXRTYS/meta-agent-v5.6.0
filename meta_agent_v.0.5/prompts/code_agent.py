"""Code agent prompt composition.

Spec References: Section 7.2.2

The code-agent prompt is monolithic — the .md file is self-contained.
This loader reads it and injects only the workspace context and current task.

See Also:
    - `sections.format_workspace_section()` — shared utility
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from meta_agent.prompts.sections import format_workspace_section


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
) -> str:
    """Assemble the code agent system prompt.

    The .md file is self-contained.  Only runtime context
    (project_dir, project_id, current_task) is injected.
    """
    prompt = _load_prompt_markdown()
    prompt += format_workspace_section(project_dir, project_id)

    if current_task:
        prompt += f"\n\n---\n\n## Current Task\n\n{current_task}"

    return prompt
