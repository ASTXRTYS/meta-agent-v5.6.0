"""Plan-writer standalone runtime and output normalization.

Spec References: Sections 6.3, 10.5.3

The plan-writer reads an approved technical spec and eval suites, then
produces a structured implementation plan with task breakdown, milestones,
and phase sequencing.

Output contract:
  - plan_path       -> absolute path to the produced implementation plan
  - status          -> "complete" | "needs_revision" | "blocked"
  - revision_notes  -> non-empty when status == "needs_revision"
  - raw_result      -> full agent output for debugging
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
from meta_agent.prompts.plan_writer import construct_plan_writer_prompt
from meta_agent.subagents.document_renderer import create_document_renderer_subagent
from meta_agent.config.memory import get_memory_sources


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
# Status block extraction
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


_DEFAULT_PLAN_RESULT: dict[str, Any] = {
    "status": "blocked",
    "plan_path": "",
    "revision_notes": "Plan-writer did not produce a parseable status block.",
    "raw_result": {},
}


def normalize_plan_writer_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Extract the structured status from the plan-writer output.

    Searches the agent message stream for a JSON status block from the
    last assistant message.  Falls back to a safe default with
    ``status="blocked"`` if parsing fails.

    Returns the evaluator-contract dict:
        plan_path, status, revision_notes, raw_result.
    """
    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    assistant_text = _last_assistant_text(messages)
    status_block = _extract_status_block(assistant_text)

    default_plan_path = os.path.join(
        project_dir, "artifacts", "plan", "implementation-plan.md"
    )
    plan_path = status_block.get("plan_path", default_plan_path)
    if plan_path and not os.path.isabs(plan_path):
        candidate = os.path.join(project_dir, plan_path)
        if os.path.isfile(candidate):
            plan_path = candidate

    raw_status = str(status_block.get("status", "")).strip().lower()
    if raw_status in ("complete", "needs_revision", "blocked"):
        status = raw_status
    elif os.path.isfile(str(plan_path)):
        status = "complete"
    else:
        status = "blocked"

    revision_notes = str(status_block.get("revision_notes", "")).strip()

    return {
        "plan_path": plan_path,
        "status": status,
        "revision_notes": revision_notes,
        "raw_result": dict(raw_result) if isinstance(raw_result, Mapping) else {"messages": []},
    }


# ---------------------------------------------------------------------------
# Graph / runnable / subagent constructors
# ---------------------------------------------------------------------------


def create_plan_writer_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the plan-writer Deep Agent graph.

    Effort: ``high`` (Section 10.5.3)
    Tools: filesystem auto (read_file, write_file, edit_file) via FilesystemMiddleware
    Middleware: 6 auto + AgentDecisionStateMiddleware, SummarizationToolMiddleware,
               MemoryMiddleware, SkillsMiddleware, ToolErrorMiddleware,
               DynamicToolConfigMiddleware
    Subagents: document-renderer (for plan rendering to DOCX/PDF)
    """
    cfg = get_model_config("plan-writer")
    model = get_configured_model("plan-writer")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    # SummarizationToolMiddleware — agent-controlled compact_conversation
    summarization_tool_mw = create_summarization_tool_middleware(
        cfg["model_string"], composite_backend
    )

    # MemoryMiddleware
    memory_sources = get_memory_sources("plan-writer", project_dir, repo_root)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

    doc_renderer = create_document_renderer_subagent(resolved_skills)

    return create_deep_agent(
        model=model,
        tools=[],  # filesystem tools provided auto via FilesystemMiddleware
        system_prompt=construct_plan_writer_prompt(project_dir, project_id),
        middleware=[
            AgentDecisionStateMiddleware(),
            summarization_tool_mw,
            memory_mw,
            skills_mw,
            ToolErrorMiddleware(),
            DynamicToolConfigMiddleware(tool_config={}),
        ],
        subagents=[doc_renderer],
        backend=composite_backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        name="plan-writer-runtime",
    )


def create_plan_writer_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes plan-writer outputs."""
    graph = create_plan_writer_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = graph.invoke(state, config=config)
        return normalize_plan_writer_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_plan_writer_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_plan_writer_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Return a CompiledSubAgent for the orchestrator."""
    return CompiledSubAgent(
        name="plan-writer",
        description=(
            "Implementation plan author. Reads the approved technical spec and "
            "eval suites, then produces a structured implementation plan with "
            "task breakdown, milestones, and phase sequencing."
        ),
        runnable=create_plan_writer_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    )


# ---------------------------------------------------------------------------
# Standalone bridge
# ---------------------------------------------------------------------------


def run_plan_writer_agent(
    *,
    project_dir: str,
    project_id: str,
    spec_path: str | None = None,
    eval_suite_path: str | None = None,
    skills_paths: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge for running the plan-writer outside the orchestrator.

    Builds the initial state, invokes the plan-writer runnable, and returns
    the normalized evaluator-contract dict.

    Args:
        project_dir: Absolute path to the project workspace.
        project_id: Project identifier (e.g. ``"meta-agent"``).
        spec_path: Path to the technical specification file.
        eval_suite_path: Path to the eval suite JSON file.
        skills_paths: Optional skill directory shorthand paths.
        extra_state: Additional state keys to merge into the initial state.

    Returns:
        Evaluator-contract dict with keys: plan_path, status,
        revision_notes, raw_result.
    """
    runnable = create_plan_writer_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )

    default_spec = os.path.join(project_dir, "artifacts", "spec", "technical-specification.md")
    default_eval = os.path.join(project_dir, "evals", "eval-suite-architecture.json")
    resolved_spec = spec_path or default_spec
    resolved_eval = eval_suite_path or default_eval

    state: dict[str, Any] = {
        "project_id": project_id,
        "current_stage": "PLANNING",
        "messages": [],
        "spec_path": resolved_spec,
        "eval_suite_path": resolved_eval,
        "spec_content": _read_text(resolved_spec),
        "eval_suite_content": _read_text(resolved_eval),
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)

    return runnable.invoke(state)
