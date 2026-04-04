"""Subagent specifications for the meta-agent system.

Spec Reference: Sections 22.3, 6, 2.2.1

Defines all 8 subagent configurations with middleware stacks,
tool sets, effort levels, and recursion limits.

Provides build_pm_subagents() to produce SDK-compatible SubAgent
dicts for the create_deep_agent(subagents=...) parameter.
"""

from __future__ import annotations

from typing import Any

from deepagents.middleware.subagents import CompiledSubAgent, SubAgent


# Explicit middleware only. Deep Agents auto-attach TodoList, Filesystem,
# SubAgent, Summarization, prompt caching, and patch-call middleware.
# Skills are provisioned through the `skills=` parameter, not listed here as
# explicit middleware. These metadata entries should describe only the
# additional, explicitly configured runtime pieces.

SUBAGENT_MIDDLEWARE: dict[str, list[str]] = {
    "research-agent": [
        "AgentDecisionStateMiddleware",
        "ToolErrorMiddleware",
        "SummarizationToolMiddleware",
        "MemoryMiddleware",
        "SkillsMiddleware",
    ],
    "spec-writer": [
        "ToolErrorMiddleware",
    ],
    "plan-writer": [
        "ToolErrorMiddleware",
    ],
    "code-agent": [
        "ToolErrorMiddleware",
        "CompletionGuardMiddleware",
    ],
    "verification-agent": [
        "AgentDecisionStateMiddleware",
        "ToolErrorMiddleware",
    ],
    "test-agent": [
        "ToolErrorMiddleware",
        "CompletionGuardMiddleware",
    ],
    "document-renderer": [
        "ToolErrorMiddleware",
    ],
    "observation-agent": [
        "ToolErrorMiddleware",
        "CompletionGuardMiddleware",
    ],
    "evaluation-agent": [
        "ToolErrorMiddleware",
    ],
    "audit-agent": [
        "ToolErrorMiddleware",
    ],
}


# Subagent configurations per Section 6 with full details
SUBAGENT_CONFIGS: dict[str, dict[str, Any]] = {
    "research-agent": {
        "type": "deep_agent",
        "effort": "max",
        "recursion_limit": 100,
        "middleware": SUBAGENT_MIDDLEWARE["research-agent"],
        "auto_tools": [
            "write_todos", "read_file", "write_file", "edit_file",
            "ls", "glob", "grep", "task", "compact_conversation",
        ],
        "tools": [
            "request_approval", "record_decision", "record_assumption",
            "web_search", "web_fetch",
        ],
        "server_side_tools": ["web_search", "web_fetch"],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "max"},
    },
    "spec-writer": {
        "type": "deep_agent",
        "effort": "high",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["spec-writer"],
        "tools": [
            "propose_evals",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "plan-writer": {
        "type": "deep_agent",
        "effort": "high",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["plan-writer"],
        "tools": [],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "code-agent": {
        "type": "deep_agent",
        "effort": "high",
        "recursion_limit": 150,
        "middleware": SUBAGENT_MIDDLEWARE["code-agent"],
        "tools": [
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
            "execute_command", "langgraph_dev_server", "langsmith_cli",
        ],
        "sub_agents": ["observation-agent", "evaluation-agent", "audit-agent"],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "verification-agent": {
        "type": "deep_agent",
        "effort": "max",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["verification-agent"],
        "tools": [],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "max"},
    },
    "eval-agent": {
        "type": "reserved",
        "note": "Reserved for future first-class LangSmith agent (Section 6.6)",
    },
    "test-agent": {
        "type": "dict_based",
        "effort": "medium",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["test-agent"],
        "tools": [
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
            "execute_command",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "medium"},
    },
    "document-renderer": {
        "type": "dict_based",
        "effort": "low",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["document-renderer"],
        "tools": [
            "read_file", "write_file", "ls",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "low"},
    },
}


def get_subagent_config(agent_name: str) -> dict[str, Any] | None:
    """Get the configuration for a specific subagent."""
    return SUBAGENT_CONFIGS.get(agent_name)


def get_subagent_middleware(agent_name: str) -> list[str]:
    """Get the middleware stack names for a specific subagent."""
    return SUBAGENT_MIDDLEWARE.get(agent_name, ["ToolErrorMiddleware"])


def get_all_subagent_names() -> list[str]:
    """Get list of all configured subagent names."""
    return list(SUBAGENT_CONFIGS.keys())


# ---------------------------------------------------------------------------
# SDK-compatible SubAgent builder (Spec Sections 6, 22.3, 22.4)
#
# Converts the metadata configs above into dicts matching the deepagents
# SubAgent TypedDict: {name, description, system_prompt, tools?, middleware?,
# skills?}.  Filesystem tools (read_file, write_file, ls, edit_file, glob,
# grep) are provided automatically by FilesystemMiddleware on each subagent
# and must NOT be passed again in tools=[].
# ---------------------------------------------------------------------------

# Descriptions per spec Section 6.x — used by SubAgentMiddleware's task tool
# to let the PM know what each agent can do.
SUBAGENT_DESCRIPTIONS: dict[str, str] = {
    "research-agent": (
        "Deep ecosystem researcher. Performs multi-pass web research, "
        "loads skills, and produces structured research bundles with "
        "evidence citations and PRD coverage matrices."
    ),
    "spec-writer": (
        "Technical specification author. Transforms an approved PRD and "
        "research bundle into a zero-ambiguity technical specification "
        "with full PRD traceability and Tier 2 eval proposals."
    ),
    "plan-writer": (
        "Development lifecycle planner. Creates actionable implementation "
        "plans with eval-phase mapping, phase gates, observation "
        "checkpoints, and spec coverage matrices."
    ),
    "code-agent": (
        "Implementation engineer. Writes code, runs tests, manages the "
        "LangGraph dev server, and coordinates observation/evaluation/audit "
        "sub-agents during the EXECUTION phase."
    ),
    "verification-agent": (
        "Artifact verifier. Cross-checks produced artifacts against their "
        "source requirements to confirm completeness before user review."
    ),
    "test-agent": (
        "Test engineer. Writes and runs tests to validate the "
        "implementation against the specification."
    ),
    "document-renderer": (
        "Document formatter. Converts Markdown artifacts into "
        "professionally formatted DOCX and PDF files."
    ),  # Canonical copy lives in document_renderer.DOCUMENT_RENDERER_DESCRIPTION
}


def _resolve_middleware_instances() -> dict[str, Any]:
    """Lazily import and return middleware class instances by name."""
    from meta_agent.middleware.agent_decision_state import AgentDecisionStateMiddleware
    from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
    from meta_agent.middleware.completion_guard import CompletionGuardMiddleware
    return {
        "AgentDecisionStateMiddleware": AgentDecisionStateMiddleware(),
        "ToolErrorMiddleware": ToolErrorMiddleware(),
        "CompletionGuardMiddleware": CompletionGuardMiddleware(),
    }


def build_pm_subagents(
    project_dir: str = "",
    project_id: str = "",
    skills_dirs: list[str] | None = None,
) -> list[SubAgent | CompiledSubAgent]:
    """Build SDK-compatible SubAgent dicts for create_deep_agent(subagents=...).

    Each subagent gets:
    - name, description, system_prompt (required by SDK)
    - middleware instances resolved from the string names in SUBAGENT_MIDDLEWARE
    - skills paths (all agents except document-renderer get full skill set)

    Filesystem tools (read_file, write_file, etc.) are NOT passed in tools=[]
    because FilesystemMiddleware is auto-attached on each subagent and provides
    them. Only custom tools specific to each agent are included.

    Args:
        project_dir: Project directory for prompt composition.
        project_id: Project identifier for prompt composition.
        skills_dirs: Resolved skill directory paths from graph.py.

    Returns:
        List of SubAgent-compatible dicts ready for create_deep_agent().
    """
    from meta_agent.prompts.research_agent import construct_research_agent_prompt
    from meta_agent.prompts.spec_writer import construct_spec_writer_prompt
    from meta_agent.prompts.verification_agent import construct_verification_agent_prompt
    from meta_agent.prompts.plan_writer import construct_plan_writer_prompt
    from meta_agent.prompts.code_agent import construct_code_agent_prompt
    from meta_agent.subagents.research_agent import create_research_agent_subagent
    from meta_agent.subagents.verification_agent_runtime import create_verification_agent_subagent
    from meta_agent.subagents.spec_writer_agent import create_spec_writer_agent_subagent
    from meta_agent.subagents.document_renderer import build_document_renderer_subagent

    mw_instances = _resolve_middleware_instances()

    # Custom tools that are NOT provided by FilesystemMiddleware.
    # Import only the @tool instances that subagents need beyond filesystem.
    from meta_agent.tools import (
        execute_command_tool,
        langgraph_dev_server_tool,
        langsmith_cli_tool,
        propose_evals_tool,
    )

    # Prompt builders keyed by agent name
    prompt_builders: dict[str, str] = {
        "research-agent": construct_research_agent_prompt(project_dir, project_id),
        "spec-writer": construct_spec_writer_prompt(project_dir, project_id),
        "plan-writer": construct_plan_writer_prompt(project_dir, project_id),
        "code-agent": construct_code_agent_prompt(project_dir, project_id),
        "verification-agent": construct_verification_agent_prompt(project_dir, project_id),
        "test-agent": construct_plan_writer_prompt(project_dir, project_id),
    }

    # Custom (non-filesystem) tools per agent
    custom_tools: dict[str, list[Any]] = {
        "research-agent": [],
        "spec-writer": [propose_evals_tool],
        "plan-writer": [],
        "code-agent": [execute_command_tool, langgraph_dev_server_tool, langsmith_cli_tool],
        "verification-agent": [],
        "test-agent": [execute_command_tool],
    }

    subagents

    for agent_name in [
        "research-agent", "spec-writer", "plan-writer", "code-agent",
        "verification-agent", "test-agent", "document-renderer",
    ]:
        config = SUBAGENT_CONFIGS.get(agent_name)
        if not config or config.get("type") == "reserved":
            continue

        if agent_name == "research-agent":
            subagents.append(
                create_research_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        if agent_name == "verification-agent":
            subagents.append(
                create_verification_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        if agent_name == "spec-writer":
            subagents.append(
                create_spec_writer_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        # Use shared builder for document-renderer (reused by research-agent)
        if agent_name == "document-renderer":
            subagents.append(build_document_renderer_subagent(skills_dirs))
            continue

        # Resolve middleware string names to instances
        mw_names = SUBAGENT_MIDDLEWARE.get(agent_name, ["ToolErrorMiddleware"])
        middleware = [mw_instances[n] for n in mw_names if n in mw_instances]

        # All remaining agents get the full skill set
        agent_skills = list(skills_dirs or [])

        entry: dict[str, Any] = {
            "name": agent_name,
            "description": SUBAGENT_DESCRIPTIONS.get(agent_name, ""),
            "system_prompt": prompt_builders.get(agent_name, ""),
            "middleware": middleware,
        }

        agent_tools = custom_tools.get(agent_name, [])
        if agent_tools:
            entry["tools"] = agent_tools

        if agent_skills:
            entry["skills"] = agent_skills

        subagents.append(entry)

    return subagents
