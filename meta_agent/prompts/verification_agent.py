"""Verification agent prompt composition.

The verification-agent prompt is monolithic — the .md file is self-contained.
This loader reads it and injects only the workspace context.

See Also:
    - `sections.format_workspace_section()` — shared utility

Note: Shared utilities consolidation TODO in sections.py lines 611-618.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Verification_Agent_System_Prompt.md")


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_verification_agent_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",  # UNUSED: see module docstring TODO
) -> str:
    """Assemble the verification agent system prompt.

    The .md file is self-contained.  Only the workspace context
    (project_dir, project_id) is injected at runtime.
    """
    prompt = _load_prompt_markdown()

    # NOTE: Inline construction vs. shared sections.format_workspace_section()
    # research_agent.py and spec_writer.py use the shared utility; this loader
    # duplicates the pattern locally. Align or document the divergence.
    workspace_block = (
        f"\n\n---\n\n## Workspace Context\n\n"
        f"- **Project directory:** `{project_dir}`\n"
        f"- **Project ID:** `{project_id}`\n"
    )
    return prompt + workspace_block
