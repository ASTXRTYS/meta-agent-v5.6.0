"""Code-agent standalone runtime and output normalization.

Spec References: Sections 6.5, 10.5.3

The code-agent executes the implementation plan: writes code, runs tests,
manages the LangGraph dev server, and interacts with the LangSmith CLI.
All shell command execution is HITL-gated via execute_command_tool.

Output contract:
  - status          -> "complete" | "in_progress" | "blocked"
  - tasks_completed -> list of task descriptions completed this run
  - artifacts_written -> list of file paths written or modified
  - raw_result      -> full agent output for debugging
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping

from deepagents import create_deep_agent
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.subagents import CompiledSubAgent
from langchain_core.runnables import RunnableLambda

from meta_agent.backend import (
    create_bare_filesystem_backend,
    create_checkpointer,
    create_composite_backend,
    create_store,
)
from meta_agent.middleware.completion_guard import CompletionGuardMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.model import get_configured_model, get_model_config
from meta_agent.prompts.code_agent import construct_code_agent_prompt
from meta_agent.safety import RECURSION_LIMITS
from meta_agent.subagents.document_renderer import build_document_renderer_subagent
from meta_agent.tools import (
    execute_command_tool,
    langgraph_dev_server_tool,
    langsmith_cli_tool,
)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _repo_root() -> str:
    return str(Path(__file__).resolve().parents[2])


def _read_text(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path) as f:
        return f.read()


def _resolve_skills_dirs(skills_paths: list[str] | None) -> list[str]:
    """Resolve skill shorthand paths to absolute directories."""
    repo_root = _repo_root()
    default_dirs = [
        os.path.join(repo_root, ".agents", "skills", "langchain", "config", "skills"),
        os.path.join(repo_root, ".agents", "skills", "anthropic", "skills"),
        os.path.join(repo_root, ".agents", "skills", "langsmith", "config", "skills"),
    ]
    if not skills_paths:
        return default_dirs

    resolved: list[str] = []
    for path in skills_paths:
        normalized = str(path).rstrip("/")
        if normalized == "/skills/langchain":
            resolved.append(os.path.join(repo_root, ".agents", "skills", "langchain", "config", "skills"))
        elif normalized == "/skills/anthropic":
            resolved.append(os.path.join(repo_root, ".agents", "skills", "anthropic", "skills"))
        elif normalized == "/skills/langsmith":
            resolved.append(os.path.join(repo_root, ".agents", "skills", "langsmith", "config", "skills"))
        else:
            resolved.append(path)
    return resolved


# ---------------------------------------------------------------------------
# Output normalization helpers
# ---------------------------------------------------------------------------


def _extract_status_block(text: str) -> dict[str, Any]:
    """Extract the JSON status block from the agent's final response."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    for m in reversed(list(re.finditer(r"\{[^{}]*\}", text))):
        try:
            parsed = json.loads(m.group(0))
            if "status" in parsed:
                return parsed
        except (json.JSONDecodeError, ValueError):
            continue

    return {}


def _last_assistant_text(messages: list[Any]) -> str:
    """Return the text content of the last assistant message."""
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or (msg.get("type") if isinstance(msg, dict) else None)
        if role == "ai":
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
    return ""


# ---------------------------------------------------------------------------
# Output normalization
# ---------------------------------------------------------------------------


def normalize_code_agent_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Extract the execution summary from the code-agent output.

    Searches the agent message stream for a JSON status block from the
    last assistant message.  Extracts tasks_completed and artifacts_written
    lists.  Falls back to empty collections and ``status="blocked"`` if
    parsing fails.

    Returns the evaluator-contract dict:
        status, tasks_completed, artifacts_written, raw_result.
    """
    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    assistant_text = _last_assistant_text(messages)
    status_block = _extract_status_block(assistant_text)

    raw_status = str(status_block.get("status", "")).strip().lower()
    if raw_status in ("complete", "in_progress", "blocked"):
        status = raw_status
    else:
        status = "blocked"

    tasks_completed: list[str] = []
    raw_tasks = status_block.get("tasks_completed", [])
    if isinstance(raw_tasks, list):
        tasks_completed = [str(t) for t in raw_tasks]

    artifacts_written: list[str] = []
    raw_artifacts = status_block.get("artifacts_written", [])
    if isinstance(raw_artifacts, list):
        artifacts_written = [str(a) for a in raw_artifacts]

    return {
        "status": status,
        "tasks_completed": tasks_completed,
        "artifacts_written": artifacts_written,
        "raw_result": dict(raw_result) if isinstance(raw_result, Mapping) else {"messages": []},
    }


# ---------------------------------------------------------------------------
# Graph / runnable / subagent constructors
# ---------------------------------------------------------------------------


def create_code_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the code-agent Deep Agent graph.

    Effort: ``high`` (Section 10.5.3)
    Tools: filesystem auto + execute_command, langgraph_dev_server, langsmith_cli
    Middleware: 6 auto + MemoryMiddleware, SkillsMiddleware,
                CompletionGuardMiddleware, ToolErrorMiddleware
    Subagents: document-renderer
    interrupt_on: execute_command (HITL required for all shell execution)
    """
    model = get_configured_model("code-agent")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    # MemoryMiddleware: project-specific + global AGENTS.md
    memory_sources: list[str] = []
    project_agents_md = os.path.join(project_dir, ".agents", "code-agent", "AGENTS.md")
    if os.path.isfile(project_agents_md):
        memory_sources.append(project_agents_md)
    global_agents_md = str(repo_root / ".agents" / "code-agent" / "AGENTS.md")
    if os.path.isfile(global_agents_md):
        memory_sources.append(global_agents_md)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

    tools = [
        execute_command_tool,
        langgraph_dev_server_tool,
        langsmith_cli_tool,
    ]

    doc_renderer = build_document_renderer_subagent(resolved_skills)

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=construct_code_agent_prompt(project_dir, project_id),
        middleware=[
            memory_mw,
            skills_mw,
            CompletionGuardMiddleware(),
            ToolErrorMiddleware(),
        ],
        subagents=[doc_renderer],
        backend=composite_backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        interrupt_on={"execute_command": True},
        name="code-agent-runtime",
    )



def create_code_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes code-agent outputs."""
    graph = create_code_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        if config is None:
            config = {}
        config.setdefault("recursion_limit", RECURSION_LIMITS["code-agent"])
        raw_result = graph.invoke(state, config=config)
        return normalize_code_agent_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        if config is None:
            config = {}
        config.setdefault("recursion_limit", RECURSION_LIMITS["code-agent"])
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_code_agent_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_code_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Return a CompiledSubAgent for the orchestrator."""
    return CompiledSubAgent(
        name="code-agent",
        description=(
            "Implementation executor. Writes code, runs tests, manages the "
            "LangGraph dev server, and interacts with LangSmith CLI. "
            "All shell commands require HITL approval."
        ),
        runnable=create_code_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    )


# ---------------------------------------------------------------------------
# Standalone bridge
# ---------------------------------------------------------------------------


def run_code_agent(
    *,
    project_dir: str,
    project_id: str,
    plan_path: str | None = None,
    current_task: str | None = None,
    skills_paths: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge for running the code-agent outside the orchestrator.

    Builds the initial state, invokes the code-agent runnable, and returns
    the normalized evaluator-contract dict.

    Args:
        project_dir: Absolute path to the project workspace.
        project_id: Project identifier (e.g. ``"meta-agent"``).
        plan_path: Path to the implementation plan file.
        current_task: Description of the specific task to execute.
        skills_paths: Optional skill directory shorthand paths.
        extra_state: Additional state keys to merge into the initial state.

    Returns:
        Evaluator-contract dict with keys: status, tasks_completed,
        artifacts_written, raw_result.
    """
    runnable = create_code_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )

    default_plan = os.path.join(project_dir, "artifacts", "plan", "implementation-plan.md")
    resolved_plan = plan_path or default_plan

    state: dict[str, Any] = {
        "project_id": project_id,
        "current_stage": "EXECUTION",
        "messages": [],
        "plan_path": resolved_plan,
        "plan_content": _read_text(resolved_plan),
        "current_task": current_task or "",
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)

    thread_id = f"code-agent-{uuid.uuid4()}"
    config: dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": RECURSION_LIMITS["code-agent"],
    }

    return runnable.invoke(state, config=config)
