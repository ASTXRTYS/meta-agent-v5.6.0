"""Research agent prompt composition.

Spec References: Section 7.2.2
"""

from __future__ import annotations

from .sections import (
    WORKSPACE_SECTION_TEMPLATE,
    ARTIFACT_PROTOCOL_SECTION,
    TOOL_USAGE_SECTION,
    TOOL_BEST_PRACTICES_SECTION,
    QUALITY_STANDARDS_SECTION,
    CORE_BEHAVIOR_SECTION,
    COMMUNICATION_SECTION,
    SKILLS_SECTION,
    format_agents_md_section,
    format_workspace_section,
)

RESEARCH_AGENT_ROLE = """You are the Research Agent — a deep ecosystem researcher specializing in the LangChain ecosystem. Your expertise is in finding implementation approaches, evaluating libraries, and understanding architectural patterns.

You perform multi-pass research: first broad discovery, then focused deep-dives on the most promising approaches. You synthesize findings into a structured research bundle with evidence citations."""


def construct_research_agent_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the research agent system prompt."""
    sections = [
        RESEARCH_AGENT_ROLE,
        format_workspace_section(project_dir, project_id),
        ARTIFACT_PROTOCOL_SECTION,
        TOOL_USAGE_SECTION,
        TOOL_BEST_PRACTICES_SECTION,
        QUALITY_STANDARDS_SECTION,
        CORE_BEHAVIOR_SECTION,
        COMMUNICATION_SECTION,
        SKILLS_SECTION,
    ]
    if agents_md:
        sections.append(format_agents_md_section(agents_md))
    return "\n\n---\n\n".join(sections)
