"""Subagent specifications for the meta-agent system.

Spec Reference: Sections 22.3, 6, 2.2.1

Provides build_pm_subagents() to produce SDK-compatible SubAgent
dicts for the create_deep_agent(subagents=...) parameter using a dynamic registry.
"""

from __future__ import annotations

from typing import Any, Callable

from deepagents.middleware.subagents import CompiledSubAgent, SubAgent


def _lazy_research_agent(**kwargs):
    from meta_agent.subagents.research_agent import create_research_agent_subagent
    return create_research_agent_subagent(**kwargs)

def _lazy_verification_agent(**kwargs):
    from meta_agent.subagents.verification_agent_runtime import create_verification_agent_subagent
    return create_verification_agent_subagent(**kwargs)

def _lazy_spec_writer_agent(**kwargs):
    from meta_agent.subagents.spec_writer_agent import create_spec_writer_agent_subagent
    return create_spec_writer_agent_subagent(**kwargs)

def _lazy_plan_writer_agent(**kwargs):
    from meta_agent.subagents.plan_writer_runtime import create_plan_writer_agent_subagent
    return create_plan_writer_agent_subagent(**kwargs)

def _lazy_code_agent(**kwargs):
    from meta_agent.subagents.code_agent_runtime import create_code_agent_subagent
    return create_code_agent_subagent(**kwargs)

def _lazy_evaluation_agent(**kwargs):
    from meta_agent.subagents.evaluation_agent_runtime import create_evaluation_agent_subagent
    return create_evaluation_agent_subagent(**kwargs)

def _lazy_document_renderer(**kwargs):
    from meta_agent.subagents.document_renderer import create_document_renderer_subagent
    return create_document_renderer_subagent(kwargs.get("skills_dirs"))

AGENT_REGISTRY: dict[str, Callable] = {
    "research-agent": _lazy_research_agent,
    "spec-writer": _lazy_spec_writer_agent,
    "plan-writer": _lazy_plan_writer_agent,
    "code-agent": _lazy_code_agent,
    "verification-agent": _lazy_verification_agent,
    "evaluation-agent": _lazy_evaluation_agent,
    "document-renderer": _lazy_document_renderer,
}

def build_pm_subagents(
    project_dir: str = "",
    project_id: str = "",
    skills_dirs: list[str] | None = None,
) -> list[SubAgent | CompiledSubAgent]:
    """Build SDK-compatible SubAgent dicts for create_deep_agent(subagents=...).

    Iterates over the AGENT_REGISTRY dynamically stringing together all agent
    configurations defined by their distinct runtime files.

    Args:
        project_dir: Project directory for prompt composition.
        project_id: Project identifier for prompt composition.
        skills_dirs: Resolved skill directory paths from graph.py.

    Returns:
        List of SubAgent-compatible dicts ready for create_deep_agent().
    """
    subagents = []

    for agent_name, factory in AGENT_REGISTRY.items():
        subagents.append(
            factory(
                project_dir=project_dir,
                project_id=project_id,
                skills_dirs=skills_dirs,
            )
        )

    return subagents
