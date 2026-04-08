"""Subagent specifications for the meta-agent system.

Spec Reference: Sections 22.3, 6, 2.2.1

Defines all 8 subagent configurations with middleware stacks,
tool sets, effort levels, and recursion limits.

Provides build_pm_subagents() to produce SDK-compatible SubAgent
dicts for the create_deep_agent(subagents=...) parameter.

TODO: Extract duplicated helper functions to shared module
ISSUE: Helper functions _resolve_skills_dirs(), _repo_root(), and _read_text()
are duplicated across multiple subagent runtime files (research_agent.py,
verification_agent_runtime.py, evaluation_agent_runtime.py, code_agent_runtime.py,
plan_writer_runtime.py). These perform common operations like resolving skills
directories, getting repository root, and reading text files.
RECOMMENDED ACTION: Extract these helpers to meta_agent/subagents/common.py
and import them in all runtime files. This reduces duplication and centralizes
common utilities for easier maintenance.
"""

from __future__ import annotations

from typing import Any

from deepagents.middleware.subagents import CompiledSubAgent, SubAgent



SUBAGENT_MIDDLEWARE: dict[str, list[str]] = {
    "research-agent": [
        "AgentDecisionStateMiddleware",
        "ToolErrorMiddleware",
        "SummarizationToolMiddleware",
        "MemoryMiddleware",
        "SkillsMiddleware",
    ],
    "spec-writer": [
        "MemoryMiddleware",
        "ToolErrorMiddleware",
    ],
    "plan-writer": [
        "MemoryMiddleware",
        "ToolErrorMiddleware",
    ],
    "code-agent": [
        "MemoryMiddleware",
        "ToolErrorMiddleware",
        "CompletionGuardMiddleware",
    ],
    "verification-agent": [
        "MemoryMiddleware",
        "AgentDecisionStateMiddleware",
        "ToolErrorMiddleware",
    ],
    "document-renderer": [
        "MemoryMiddleware",
        "ToolErrorMiddleware",
    ],
    "evaluation-agent": [
        "MemoryMiddleware",
        "ToolErrorMiddleware",
    ],
}


# Subagent configurations per Section 6 with full details
#
# ⚠️ URGENT: CONFIGURATION DRIFT — DEAD METADATA
# This dictionary is NOT used by runtime agent factories. It exists only for test
# validation in tests/integration/test_subagent_delegation.py. Runtime agents
# construct their configs inline in their respective create_*_agent files.
#
# If you update this, you MUST also update:
#   - meta_agent/subagents/research_agent.py (lines ~680-710)
#   - meta_agent/subagents/spec_writer_agent.py (lines ~290-310)
#   - meta_agent/subagents/verification_agent_runtime.py (lines ~200-230)
#   - meta_agent/subagents/plan_writer_runtime.py
#   - meta_agent/subagents/code_agent_runtime.py
#   - meta_agent/subagents/evaluation_agent_runtime.py
#
# TODO: Resolve SUBAGENT_CONFIGS duplication with factory methods
# ISSUE: SUBAGENT_CONFIGS is defined here but runtime agents construct their
# configs inline in their respective create_*_agent files (research_agent.py,
# spec_writer_agent.py, verification_agent_runtime.py, plan_writer_runtime.py,
# code_agent_runtime.py, evaluation_agent_runtime.py). This creates a single
# source of truth problem - updates must be synchronized across 7 files.
# RECOMMENDED ACTION: Either make SUBAGENT_CONFIGS authoritative by having
# factory methods read from it, or delete this dict and test runtime behavior
# directly. Choose one approach and remove the duplication.
SUBAGENT_CONFIGS: dict[str, dict[str, Any]] = {
    "research-agent": {
        "type": "deep_agent",
        "recursion_limit": 1000,
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
    },
    "spec-writer": {
        "type": "deep_agent",
        "effort": "high",
        "recursion_limit": 1000,
        "middleware": SUBAGENT_MIDDLEWARE["spec-writer"],
        "tools": [
            "propose_evals",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "plan-writer": {
        "type": "compiled_subagent",
        "effort": "high",
        "recursion_limit": 1000,
        "middleware": SUBAGENT_MIDDLEWARE["plan-writer"],
        "tools": [],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "code-agent": {
        "type": "compiled_subagent",
        "effort": "high",
        "recursion_limit": 1000,
        "middleware": SUBAGENT_MIDDLEWARE["code-agent"],
        "tools": [
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
            "execute_command", "langgraph_dev_server", "langsmith_cli",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "verification-agent": {
        "type": "deep_agent",
        "effort": "max",
        "recursion_limit": 1000,
        "middleware": SUBAGENT_MIDDLEWARE["verification-agent"],
        "tools": [],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "max"},
    },
    "evaluation-agent": {
        "type": "compiled_subagent",
        "effort": "high",
        "recursion_limit": 1000,
        "middleware": SUBAGENT_MIDDLEWARE["evaluation-agent"],
        "tools": [
            "langsmith_trace_list", "langsmith_trace_get",
            "langsmith_dataset_create", "langsmith_eval_run",
            "propose_evals", "create_eval_dataset",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "document-renderer": {
        "type": "deep_agent",
        "effort": "low",
        "recursion_limit": 1000,
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
# TODO: Consolidate to a single source of truth (either here or in factories).
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
        "LangGraph dev server, and iterates on implementation during the "
        "EXECUTION phase."
    ),
    "verification-agent": (
        "Artifact verifier. Cross-checks produced artifacts against their "
        "source requirements to confirm completeness before user review."
    ),
    "evaluation-agent": (
        "Scientific evaluation engineer. Designs and calibrates LLM judges, "
        "runs LangSmith experiments, enforces phase gate thresholds, and "
        "provides feedback for the code-agent optimization loop."
    ),
    "document-renderer": (
        "Document formatter. Converts Markdown artifacts into "
        "professionally formatted DOCX and PDF files."
    ),
}


# ⚠️ URGENT: DEAD CODE — MIDDLEWARE NOT RESOLVED
# This only resolves 3 middleware classes but SUBAGENT_MIDDLEWARE references
# additional ones (SummarizationToolMiddleware, MemoryMiddleware, SkillsMiddleware,
# CompletionGuardMiddleware) that are instantiated inline by agent factories.
#
# TODO: Complete this resolver or remove if factories remain self-contained.
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
    # ⚠️ URGENT: NAIVE SEQUENTIAL LOGIC — MAINTENANCE HAZARD
    # This function uses a repetitive if/elif chain to dispatch to agent factories.
    # Each new agent requires editing this function. Prefer a registry pattern:
    #
    #   AGENT_REGISTRY: dict[str, Callable] = {
    #       "research-agent": create_research_agent_subagent,
    #       "spec-writer": create_spec_writer_agent_subagent,
    #       ...
    #   }
    #
    # TODO: Refactor to registry pattern to eliminate the 80-line if/elif chain below.
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
    from meta_agent.subagents.research_agent import create_research_agent_subagent
    from meta_agent.subagents.verification_agent_runtime import create_verification_agent_subagent
    from meta_agent.subagents.spec_writer_agent import create_spec_writer_agent_subagent
    from meta_agent.subagents.plan_writer_runtime import create_plan_writer_agent_subagent
    from meta_agent.subagents.code_agent_runtime import create_code_agent_subagent
    from meta_agent.subagents.evaluation_agent_runtime import create_evaluation_agent_subagent
    from meta_agent.subagents.document_renderer import create_document_renderer_subagent

    subagents = []

    for agent_name in [
        "research-agent", "spec-writer", "plan-writer", "code-agent",
        "verification-agent", "evaluation-agent", "document-renderer",
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

        if agent_name == "plan-writer":
            subagents.append(
                create_plan_writer_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        if agent_name == "code-agent":
            subagents.append(
                create_code_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        if agent_name == "evaluation-agent":
            subagents.append(
                create_evaluation_agent_subagent(
                    project_dir=project_dir,
                    project_id=project_id,
                    skills_dirs=skills_dirs,
                )
            )
            continue

        # Use shared builder for document-renderer
        if agent_name == "document-renderer":
            subagents.append(create_document_renderer_subagent(skills_dirs))
            continue

    return subagents
