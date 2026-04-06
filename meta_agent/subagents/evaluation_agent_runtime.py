"""Evaluation-agent standalone runtime and output normalization.

Spec References: Sections 6.7, 10.5.3

The evaluation-agent designs and runs LangSmith evaluations. It uses the
LangSmith SDK tools to list traces, create datasets, run evaluations, and
propose eval suites.

Output contract:
  - status        -> "complete" | "in_progress" | "failed"
  - eval_summary  -> human-readable summary of evaluation results
  - eval_results  -> structured dict of evaluation outcomes
  - raw_result    -> full agent output for debugging
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from deepagents import create_deep_agent
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.subagents import CompiledSubAgent
from deepagents.middleware.summarization import (
    create_summarization_tool_middleware,
)
from langchain_core.runnables import RunnableLambda

from meta_agent.backend import (
    create_bare_filesystem_backend,
    create_checkpointer,
    create_composite_backend,
    create_store,
)
from meta_agent.middleware.agent_decision_state import AgentDecisionStateMiddleware
from meta_agent.middleware.dynamic_tool_config import DynamicToolConfigMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.model import get_configured_model, get_model_config
from meta_agent.prompts.evaluation_agent import construct_evaluation_agent_prompt
from meta_agent.tools import (
    create_eval_dataset_tool,
    langsmith_dataset_create_tool,
    langsmith_eval_run_tool,
    langsmith_trace_get_tool,
    langsmith_trace_list_tool,
    propose_evals_tool,
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


def normalize_evaluation_agent_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Extract the structured eval results from the evaluation-agent output.

    Searches the agent message stream for a JSON status block from the
    last assistant message.  Falls back to ``status="failed"`` if parsing
    fails.

    Returns the evaluator-contract dict:
        status, eval_summary, eval_results, raw_result.
    """
    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    assistant_text = _last_assistant_text(messages)
    status_block = _extract_status_block(assistant_text)

    raw_status = str(status_block.get("status", "")).strip().lower()
    if raw_status in ("complete", "in_progress", "failed"):
        status = raw_status
    else:
        status = "failed"

    eval_summary = str(status_block.get("eval_summary", "")).strip()
    eval_results: dict[str, Any] = {}
    raw_results = status_block.get("eval_results", {})
    if isinstance(raw_results, dict):
        eval_results = raw_results

    return {
        "status": status,
        "eval_summary": eval_summary,
        "eval_results": eval_results,
        "raw_result": dict(raw_result) if isinstance(raw_result, Mapping) else {"messages": []},
    }


# ---------------------------------------------------------------------------
# Graph / runnable / subagent constructors
# ---------------------------------------------------------------------------


def create_evaluation_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the evaluation-agent Deep Agent graph.

    Effort: ``high`` (Section 10.5.3)
    Tools: LangSmith tools — trace list/get, dataset create, eval run,
           propose_evals, create_eval_dataset
    Middleware: 6 auto + AgentDecisionStateMiddleware, SummarizationToolMiddleware,
               MemoryMiddleware, SkillsMiddleware, ToolErrorMiddleware,
               DynamicToolConfigMiddleware
    Subagents: None (may be extended in Phase 5)
    System prompt: Placeholder — full prompt comes in Phase 2 of evaluation stack
    """
    cfg = get_model_config("evaluation-agent")
    model = get_configured_model("evaluation-agent")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    # SummarizationToolMiddleware — agent-controlled compact_conversation
    summarization_tool_mw = create_summarization_tool_middleware(
        cfg["model_string"], composite_backend
    )

    # MemoryMiddleware: project-specific + global AGENTS.md
    memory_sources: list[str] = []
    project_agents_md = os.path.join(project_dir, ".agents", "evaluation-agent", "AGENTS.md")
    if os.path.isfile(project_agents_md):
        memory_sources.append(project_agents_md)
    global_agents_md = str(repo_root / ".agents" / "evaluation-agent" / "AGENTS.md")
    if os.path.isfile(global_agents_md):
        memory_sources.append(global_agents_md)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

    tools = [
        langsmith_trace_list_tool,
        langsmith_trace_get_tool,
        langsmith_dataset_create_tool,
        langsmith_eval_run_tool,
        propose_evals_tool,
        create_eval_dataset_tool,
    ]

    system_prompt = construct_evaluation_agent_prompt(project_dir, project_id)

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            AgentDecisionStateMiddleware(),
            summarization_tool_mw,
            memory_mw,
            skills_mw,
            ToolErrorMiddleware(),
            DynamicToolConfigMiddleware(tool_config={}),
        ],
        backend=composite_backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        name="evaluation-agent-runtime",
    )



def create_evaluation_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes evaluation-agent outputs."""
    graph = create_evaluation_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = graph.invoke(state, config=config)
        return normalize_evaluation_agent_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_evaluation_agent_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_evaluation_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Return a CompiledSubAgent for the orchestrator."""
    return CompiledSubAgent(
        name="evaluation-agent",
        description=(
            "Evaluation harness. Designs and runs LangSmith evaluations: "
            "lists and retrieves traces, creates datasets, runs evaluators, "
            "and proposes eval suites from requirements."
        ),
        runnable=create_evaluation_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    )


# ---------------------------------------------------------------------------
# Standalone bridge
# ---------------------------------------------------------------------------


def run_evaluation_agent(
    *,
    project_dir: str,
    project_id: str,
    eval_suite_path: str | None = None,
    langsmith_project: str | None = None,
    skills_paths: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge for running the evaluation-agent outside the orchestrator.

    Builds the initial state, invokes the evaluation-agent runnable, and
    returns the normalized evaluator-contract dict.

    Args:
        project_dir: Absolute path to the project workspace.
        project_id: Project identifier (e.g. ``"meta-agent"``).
        eval_suite_path: Path to the eval suite JSON/YAML file.
        langsmith_project: LangSmith project name to query for traces.
        skills_paths: Optional skill directory shorthand paths.
        extra_state: Additional state keys to merge into the initial state.

    Returns:
        Evaluator-contract dict with keys: status, eval_summary,
        eval_results, raw_result.
    """
    runnable = create_evaluation_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )

    state: dict[str, Any] = {
        "project_id": project_id,
        "current_stage": "EVALUATION",
        "messages": [],
        "eval_suite_path": eval_suite_path or "",
        "langsmith_project": langsmith_project or project_id,
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)

    return runnable.invoke(state)
