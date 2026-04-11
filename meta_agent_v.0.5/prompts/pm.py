"""PM prompt composition function.

Spec References: Sections 7.3, 22.15

Assembles the PM system prompt based on current stage
using stage-aware section loading.  The canonical prompt content
lives in companion Markdown files; this module provides a thin
loader following the gold-standard pattern established by
``research_agent.py``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import (
    format_workspace_section,
    format_stage_context,
    format_agents_md_section,
    format_memory_section,
)

# ---------------------------------------------------------------------------
# Markdown source-of-truth paths (co-located with this module)
# ---------------------------------------------------------------------------

PROMPT_MARKDOWN_PATH = Path(__file__).with_name("PM_System_Prompt.md")
SCORING_STRATEGY_PATH = Path(__file__).with_name("PM_Scoring_Strategy.md")
EVAL_APPROVAL_PATH = Path(__file__).with_name("PM_Eval_Approval_Protocol.md")
DELEGATION_PATH = Path(__file__).with_name("PM_Delegation.md")

# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_pm_base_prompt() -> str:
    """Load the always-included PM system prompt from Markdown."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


@lru_cache(maxsize=1)
def _load_scoring_strategy() -> str:
    return SCORING_STRATEGY_PATH.read_text().strip()


@lru_cache(maxsize=1)
def _load_eval_approval_protocol() -> str:
    return EVAL_APPROVAL_PATH.read_text().strip()


@lru_cache(maxsize=1)
def _load_delegation() -> str:
    return DELEGATION_PATH.read_text().strip()


# ---------------------------------------------------------------------------
# Public API (signature unchanged)
# ---------------------------------------------------------------------------


def construct_pm_prompt(
    stage: str,
    project_dir: str,
    project_id: str,
    agents_md_content: str = "",
) -> str:
    """Assembles the PM system prompt based on current stage.

    Per Section 7.3, sections are loaded conditionally based on stage
    to reduce cognitive load.
    """
    # Always included
    sections = [
        _load_pm_base_prompt(),
        format_workspace_section(project_dir, project_id),
        format_memory_section(project_dir),
    ]

    # Stage-specific context
    sections.append(format_stage_context(stage, project_id))

    # Stage-conditional sections
    if stage in ("INTAKE", "PRD_REVIEW", "SPEC_REVIEW"):
        sections.append(_load_eval_approval_protocol())

    if stage in ("INTAKE", "SPEC_REVIEW"):
        sections.append(_load_scoring_strategy())

    if stage in ("RESEARCH", "SPEC_GENERATION", "PLANNING", "EXECUTION"):
        sections.append(_load_delegation())

    # Runtime-injected memory (always last)
    if agents_md_content:
        sections.append(format_agents_md_section(agents_md_content))

    return "\n\n---\n\n".join(sections)
