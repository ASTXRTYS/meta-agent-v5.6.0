"""Subagent specifications for the meta-agent system.

Spec Reference: Sections 22.3, 6, 2.2.1

Defines all 8 subagent configurations with middleware stacks,
tool sets, effort levels, and recursion limits.
"""

from __future__ import annotations

from typing import Any


# Per-agent middleware stacks per Section 2.2.1 and Section 6.x
# All agents: ToolErrorMiddleware
# code-agent, test-agent, observation-agent: + CompletionGuardMiddleware
# research-agent: + SummarizationToolMiddleware, SkillsMiddleware
# Orchestrator: full stack (see graph.py)

SUBAGENT_MIDDLEWARE: dict[str, list[str]] = {
    "research-agent": [
        "ToolErrorMiddleware",
        "SummarizationToolMiddleware",
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
        "tools": [
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
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
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
        ],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    },
    "plan-writer": {
        "type": "deep_agent",
        "effort": "high",
        "recursion_limit": 50,
        "middleware": SUBAGENT_MIDDLEWARE["plan-writer"],
        "tools": [
            "write_file", "read_file", "ls", "edit_file", "glob", "grep",
        ],
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
        "tools": [
            "read_file", "ls", "glob", "grep",
        ],
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
