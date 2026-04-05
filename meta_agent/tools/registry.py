"""Central tool registry for the meta-agent system.

Spec Reference: Section 22.8

Maps agent roles to their available tools. Custom tools (glob, grep) are
registered via the tools=[] parameter on create_deep_agent(), NOT via middleware
(Section 8.14.1).

Provides both raw function references (TOOL_FUNCTIONS) and @tool-decorated
LangChain tool instances (LANGCHAIN_TOOLS) for create_deep_agent().
"""

from __future__ import annotations

from typing import Any, Callable

from meta_agent.tools import (
    transition_stage,
    record_decision,
    record_assumption,
    request_approval,
    request_eval_approval,
    toggle_participation,
    execute_command,
    langgraph_dev_server,
    langsmith_cli,
    glob_tool,
    grep_tool,
    langsmith_trace_list,
    langsmith_trace_get,
    langsmith_dataset_create,
    langsmith_eval_run,
    get_server_side_tools,
    LANGCHAIN_TOOLS,
    # @tool decorated versions
    transition_stage_tool,
    record_decision_tool,
    record_assumption_tool,
    request_approval_tool,
    request_eval_approval_tool,
    toggle_participation_tool,
    execute_command_tool,
    langgraph_dev_server_tool,
    langsmith_cli_tool,
    glob_search,
    grep_search,
    langsmith_trace_list_tool,
    langsmith_trace_get_tool,
    langsmith_dataset_create_tool,
    langsmith_eval_run_tool,
    propose_evals_tool,
    create_eval_dataset_tool,
)
from meta_agent.tools.eval_tools import (
    propose_evals,
    create_eval_dataset,
)


# Tool function registry — maps tool names to their raw implementations
TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "transition_stage": transition_stage,
    "record_decision": record_decision,
    "record_assumption": record_assumption,
    "request_approval": request_approval,
    "request_eval_approval": request_eval_approval,
    "toggle_participation": toggle_participation,
    "execute_command": execute_command,
    "langgraph_dev_server": langgraph_dev_server,
    "langsmith_cli": langsmith_cli,
    "glob": glob_tool,
    "grep": grep_tool,
    "langsmith_trace_list": langsmith_trace_list,
    "langsmith_trace_get": langsmith_trace_get,
    "langsmith_dataset_create": langsmith_dataset_create,
    "langsmith_eval_run": langsmith_eval_run,
    "propose_evals": propose_evals,
    "create_eval_dataset": create_eval_dataset,
}

# Tool registry organized by agent role — maps names to tool name lists
TOOL_REGISTRY: dict[str, list[str]] = {
    "pm": [
        # SDK-provided (FilesystemMiddleware auto-attaches these):
        "write_file", "read_file", "ls", "edit_file",
        # Custom tools registered via tools=[]:
        "glob", "grep",
        "transition_stage", "record_decision", "record_assumption",
        "request_approval", "request_eval_approval", "toggle_participation",
        "execute_command",
        "propose_evals", "create_eval_dataset",
        # Phase 5 stubs — not yet implemented as @tool instances:
        # "run_eval_suite", "get_eval_results", "compare_eval_runs",
    ],
    "research-agent": [
        # SDK-provided:
        "write_file", "read_file", "ls", "edit_file",
        # Custom:
        "glob", "grep",
        "web_search", "web_fetch",
    ],
    "spec-writer": [
        # SDK-provided:
        "write_file", "read_file", "ls", "edit_file",
        # Custom:
        "glob", "grep",
        "propose_evals",
    ],
    "plan-writer": [
        # SDK-provided:
        "write_file", "read_file", "ls", "edit_file",
        # Custom:
        "glob", "grep",
    ],
    "code-agent": [
        # SDK-provided:
        "write_file", "read_file", "ls", "edit_file",
        # Custom:
        "glob", "grep",
        "execute_command", "langgraph_dev_server", "langsmith_cli",
    ],
    "verification-agent": [
        # SDK-provided:
        "read_file", "ls",
        # Custom:
        "glob", "grep",
    ],
    "evaluation-agent": [
        # SDK-provided:
        "write_file", "read_file", "ls", "edit_file",
        # Custom:
        "langsmith_trace_list", "langsmith_trace_get",
        "langsmith_dataset_create", "langsmith_eval_run",
        "propose_evals", "create_eval_dataset",
    ],
    "document-renderer": [
        # SDK-provided:
        "read_file", "write_file", "ls",
    ],
}

# Tools that are HITL-gated
HITL_GATED_TOOLS: set[str] = {
    "execute_command",
    "transition_stage",
    "request_eval_approval",
    "langsmith_dataset_create",
    "langsmith_eval_run",
    "create_eval_dataset",
}


def get_tools_for_agent(agent_name: str) -> list[str]:
    """Get the list of tool names available to an agent."""
    return TOOL_REGISTRY.get(agent_name, [])


def get_tool_function(tool_name: str) -> Callable[..., Any] | None:
    """Get the implementation function for a tool by name."""
    return TOOL_FUNCTIONS.get(tool_name)


def get_custom_tools_for_agent(agent_name: str) -> list[Callable[..., Any]]:
    """Get custom tool functions for an agent (for tools=[] parameter).

    Returns only the custom tools that should be registered via
    create_deep_agent(tools=[...]). Filesystem tools come from middleware.
    """
    tool_names = get_tools_for_agent(agent_name)
    custom_tools = []
    for name in tool_names:
        fn = TOOL_FUNCTIONS.get(name)
        if fn is not None:
            custom_tools.append(fn)
    return custom_tools


def get_langchain_tools() -> list[Any]:
    """Get all @tool-decorated LangChain tool instances for create_deep_agent."""
    return list(LANGCHAIN_TOOLS)


def is_hitl_gated(tool_name: str) -> bool:
    """Check if a tool requires HITL approval."""
    return tool_name in HITL_GATED_TOOLS
