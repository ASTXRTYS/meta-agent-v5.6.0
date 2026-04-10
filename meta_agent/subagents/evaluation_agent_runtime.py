"""Evaluation-agent standalone runtime and output normalization.

Spec References: Sections 6.7, 10.5.3

The evaluation-agent designs and runs LangSmith evaluations. It uses the
LangSmith SDK tools to list traces, create datasets, run evaluations, and
propose eval suites.

Output contract:
  - status        -> "complete" | "in_progress" | "failed" | "parse_error"
  - eval_summary  -> human-readable summary of evaluation results
  - eval_results  -> structured dict of evaluation outcomes
  - raw_result    -> full agent output for debugging
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Mapping

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from langchain_core.runnables import RunnableLambda

from meta_agent.backend import (
    create_bare_filesystem_backend,
    create_checkpointer,
    create_composite_backend,
    create_store,
)
from meta_agent.model import get_configured_model
from meta_agent.prompts.evaluation_agent import construct_evaluation_agent_prompt
from meta_agent.subagents.provisioner import build_provisioning_plan
from meta_agent.tools import (
    create_eval_dataset_tool,
    langsmith_dataset_create_tool,
    langsmith_eval_run_tool,
    langsmith_trace_get_tool,
    langsmith_trace_list_tool,
    propose_evals_tool,
)
from meta_agent.utils.parsing import ParseError, parse_status_block


logger = logging.getLogger(__name__)
VALID_STATUSES = frozenset({"complete", "in_progress", "failed"})


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
    last assistant message.  Falls back to ``status="parse_error"`` if parsing
    fails.

    Returns the evaluator-contract dict:
        status, eval_summary, eval_results, raw_result.
    """
    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    assistant_text = _last_assistant_text(messages)
    try:
        status_block = parse_status_block(assistant_text)
        raw_status = str(status_block.get("status", "")).strip().lower()
        if raw_status not in VALID_STATUSES:
            logger.warning(
                "schema_violation: unrecognized status %r",
                raw_status,
                extra={
                    "reason": "schema_violation",
                    "actual_status": raw_status,
                },
            )
            status = "parse_error"
            eval_summary = ""
            eval_results = {}
        else:
            status = raw_status
            eval_summary = str(status_block.get("eval_summary", "")).strip()
            eval_results: dict[str, Any] = {}
            raw_results = status_block.get("eval_results", {})
            if isinstance(raw_results, dict):
                eval_results = raw_results
    except ParseError as error:
        logger.warning(
            "ParseError extracting status block: reason=%s char_offset=%d msg=%r lineno=%r colno=%r",
            error.reason,
            error.char_offset,
            error.msg,
            error.lineno,
            error.colno,
            extra={
                "parse_error_reason": error.reason,
                "parse_error_char_offset": error.char_offset,
                "parse_error_msg": error.msg,
                "parse_error_lineno": error.lineno,
                "parse_error_colno": error.colno,
            },
        )
        status = "parse_error"
        eval_summary = ""
        eval_results = {}

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
               MemoryMiddleware, SkillsMiddleware, ToolErrorMiddleware
    Subagents: None (may be extended in Phase 5)
    System prompt: Placeholder — full prompt comes in Phase 2 of evaluation stack
    """
    model = get_configured_model(effort="high")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    provisioning_plan = build_provisioning_plan(
        agent_name="evaluation-agent",
        project_dir=project_dir,
        repo_root=repo_root,
        composite_backend=composite_backend,
        bare_fs=bare_fs,
        skills_dirs=resolved_skills,
    )

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
        middleware=provisioning_plan.middleware,
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
