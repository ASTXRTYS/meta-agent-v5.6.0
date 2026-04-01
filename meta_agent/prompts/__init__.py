"""Prompt section constants and composition functions.

Spec References: Sections 7.2, 7.3, 22.14-22.21
"""

from .sections import (
    ROLE_SECTION,
    WORKSPACE_SECTION_TEMPLATE,
    ARTIFACT_PROTOCOL_SECTION,
    TOOL_USAGE_SECTION,
    TOOL_BEST_PRACTICES_SECTION,
    QUALITY_STANDARDS_SECTION,
    CORE_BEHAVIOR_SECTION,
    HITL_PROTOCOL_SECTION,
    DELEGATION_SECTION,
    COMMUNICATION_SECTION,
    SKILLS_SECTION,
    MEMORY_SECTION,
    SECTION_MATRIX,
    STAGE_CONTEXTS,
    format_workspace_section,
    format_stage_context,
    format_agents_md_section,
    format_memory_section,
)
from .eval_mindset import EVAL_MINDSET_SECTION
from .eval_engineering import EVAL_ENGINEERING_SECTION
from .scoring_strategy import SCORING_STRATEGY_SECTION
from .eval_approval_protocol import EVAL_APPROVAL_PROTOCOL
from .pm import construct_pm_prompt

__all__ = [
    "ROLE_SECTION",
    "WORKSPACE_SECTION_TEMPLATE",
    "ARTIFACT_PROTOCOL_SECTION",
    "TOOL_USAGE_SECTION",
    "TOOL_BEST_PRACTICES_SECTION",
    "QUALITY_STANDARDS_SECTION",
    "CORE_BEHAVIOR_SECTION",
    "HITL_PROTOCOL_SECTION",
    "DELEGATION_SECTION",
    "COMMUNICATION_SECTION",
    "SKILLS_SECTION",
    "MEMORY_SECTION",
    "SECTION_MATRIX",
    "STAGE_CONTEXTS",
    "EVAL_MINDSET_SECTION",
    "EVAL_ENGINEERING_SECTION",
    "SCORING_STRATEGY_SECTION",
    "EVAL_APPROVAL_PROTOCOL",
    "construct_pm_prompt",
    "format_workspace_section",
    "format_stage_context",
    "format_agents_md_section",
    "format_memory_section",
]
