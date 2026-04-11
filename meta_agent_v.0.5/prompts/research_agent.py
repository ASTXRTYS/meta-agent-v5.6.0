"""Research agent prompt composition."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import format_workspace_section


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Research_Agent_System_Prompt.md")


RUNTIME_NOTES = """## Runtime Notes

- Use the concrete PRD path and Tier 1 eval suite path supplied in runtime state.
- Persist artifacts under the project workspace paths shown above.
- Update `.agents/research-agent/AGENTS.md` after the final bundle is written."""


@lru_cache(maxsize=1)
def _load_research_agent_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_research_agent_prompt(
    project_dir: str,
    project_id: str = "",
) -> str:
    """Assemble the research-agent system prompt from the markdown source of truth."""
    sections = [
        _load_research_agent_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
        RUNTIME_NOTES,
    ]
    return "\n\n---\n\n".join(sections)
