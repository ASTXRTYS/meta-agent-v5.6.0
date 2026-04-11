"""Plan-writer standalone runtime and output normalization.

Spec References: Sections 6.3, 10.5.3

The plan-writer reads an approved technical spec and eval suites, then
produces a structured implementation plan with task breakdown, milestones,
and phase sequencing.

Output contract:
  - plan_path       -> absolute path to the produced implementation plan
  - status          -> "complete" | "needs_revision" | "blocked" | "parse_error"
  - revision_notes  -> non-empty when status == "needs_revision"
  - raw_result      -> full agent output for debugging
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
from meta_agent.model_config import resolve_agent_model
from meta_agent.prompts.plan_writer import construct_plan_writer_prompt
from meta_agent.subagents.document_renderer import create_document_renderer_subagent
from meta_agent.subagents.provisioner import build_provisioning_plan
from meta_agent.utils.parsing import ParseError, parse_status_block


logger = logging.getLogger(__name__)
VALID_STATUSES = frozenset({"complete", "needs_revision", "blocked"})


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


def normalize_plan_writer_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Extract the structured status from the plan-writer output.

    Searches the agent message stream for a JSON status block from the
    last assistant message.  Falls back to a safe default with
    ``status="parse_error"`` if parsing fails.

    Returns the evaluator-contract dict:
        plan_path, status, revision_notes, raw_result.
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
            plan_path = ""
            revision_notes = ""
        else:
            default_plan_path = os.path.join(
                project_dir, "artifacts", "plan", "implementation-plan.md"
            )
            plan_path = str(status_block.get("plan_path", default_plan_path))
            if plan_path and not os.path.isabs(plan_path):
                candidate = os.path.join(project_dir, plan_path)
                if os.path.isfile(candidate):
                    plan_path = candidate
            status = raw_status
            revision_notes = str(status_block.get("revision_notes", "")).strip()
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
        plan_path = ""
        revision_notes = ""

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
               MemoryMiddleware, SkillsMiddleware, ToolErrorMiddleware
    Subagents: document-renderer (for plan rendering to DOCX/PDF)
    """
    resolution = resolve_agent_model('plan-writer')
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    provisioning_plan = build_provisioning_plan(
        agent_name="plan-writer",
        model_spec=resolution.model_spec,
        summarization_model=resolution.model,
        project_dir=project_dir,
        repo_root=repo_root,
        composite_backend=composite_backend,
        bare_fs=bare_fs,
        skills_dirs=resolved_skills,
    )

    doc_renderer = create_document_renderer_subagent(resolved_skills)

    return create_deep_agent(
        model=resolution.model,
        tools=[],  # filesystem tools provided auto via FilesystemMiddleware
        system_prompt=construct_plan_writer_prompt(project_dir, project_id),
        middleware=provisioning_plan.middleware,
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
