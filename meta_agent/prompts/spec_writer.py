"""Spec writer agent prompt composition."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import format_workspace_section


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Spec_Writer_System_Prompt.md")


RUNTIME_NOTES = """## Runtime Notes

- Use the concrete paths supplied in runtime state for PRD, research bundle, and eval suite.
- Persist the technical specification under the project workspace paths shown above."""


@lru_cache(maxsize=1)
def _load_spec_writer_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


def construct_spec_writer_prompt(
    project_dir: str,
    project_id: str = "",
) -> str:
    """Assemble the spec-writer system prompt from the markdown source of truth."""
    sections = [
        _load_spec_writer_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
        RUNTIME_NOTES,
    ]
    return "\n\n---\n\n".join(sections)
