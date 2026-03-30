"""Compiled spec-writer-agent runtime and normalization helpers.

Spec Reference: Section 6.2

The spec-writer transforms an approved PRD + research bundle into a
zero-ambiguity technical specification with full PRD traceability and
Tier 2 (architecture-derived) eval proposals.

Key differences from the research-agent runtime:
- Effort level: high (not max)
- Recursion limit: 50 (not 100)
- Tools: filesystem auto + propose_evals (custom); no web_search/web_fetch
- Middleware: 6 auto + ToolErrorMiddleware only (no SubAgentMiddleware)
- No trace normalization or complex tool-call analysis needed
- Supports a feedback loop: can return "needs_additional_research" status
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend as SdkFilesystemBackend
from langchain_core.runnables import RunnableLambda

from meta_agent.backend import create_checkpointer, create_store
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.model import get_model_config
from meta_agent.prompts.spec_writer import construct_spec_writer_prompt
from meta_agent.tools import propose_evals_tool


# ---------------------------------------------------------------------------
# Runtime path helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpecWriterRuntimePaths:
    project_dir: str
    project_id: str
    prd_path: str
    research_bundle_path: str
    eval_suite_path: str
    spec_path: str
    tier2_eval_suite_path: str
    agents_md_path: str


def get_spec_writer_runtime_paths(
    project_dir: str,
    project_id: str,
) -> SpecWriterRuntimePaths:
    """Return canonical absolute runtime paths for the spec-writer stage."""
    return SpecWriterRuntimePaths(
        project_dir=project_dir,
        project_id=project_id,
        prd_path=os.path.join(project_dir, "artifacts", "intake", "research-agent-prd.md"),
        research_bundle_path=os.path.join(project_dir, "artifacts", "research", "research-bundle.md"),
        eval_suite_path=os.path.join(project_dir, "evals", "eval-suite-prd.json"),
        spec_path=os.path.join(project_dir, "artifacts", "spec", "technical-specification.md"),
        tier2_eval_suite_path=os.path.join(project_dir, "evals", "eval-suite-architecture.json"),
        agents_md_path=os.path.join(project_dir, ".agents", "spec-writer", "AGENTS.md"),
    )


def _repo_root() -> str:
    return str(Path(__file__).resolve().parents[2])


def _read_text(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path) as f:
        return f.read()


def _resolve_skills_dirs(skills_paths: list[str] | None) -> list[str]:
    repo_root = _repo_root()
    default_dirs = [
        os.path.join(repo_root, "skills", "langchain", "config", "skills"),
        os.path.join(repo_root, "skills", "anthropic", "skills"),
        os.path.join(repo_root, "skills", "langsmith", "config", "skills"),
    ]
    if not skills_paths:
        return default_dirs

    resolved: list[str] = []
    for path in skills_paths:
        normalized = str(path).rstrip("/")
        if normalized == "/skills/langchain":
            resolved.append(os.path.join(repo_root, "skills", "langchain", "config", "skills"))
        elif normalized == "/skills/anthropic":
            resolved.append(os.path.join(repo_root, "skills", "anthropic", "skills"))
        elif normalized == "/skills/langsmith":
            resolved.append(os.path.join(repo_root, "skills", "langsmith", "config", "skills"))
        else:
            resolved.append(path)
    return resolved


# ---------------------------------------------------------------------------
# Status block extraction
# ---------------------------------------------------------------------------

def _extract_status_block(text: str) -> dict[str, Any]:
    """Extract the JSON status block from the agent's final response.

    The spec-writer prompt instructs the agent to end with a fenced JSON
    block containing status, needs_additional_research, etc.
    """
    # Try ```json ... ``` first
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Try bare ``` ... ```
    match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Try last JSON object in text
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
# Agent memory update
# ---------------------------------------------------------------------------

def update_agent_memory(paths: SpecWriterRuntimePaths, spec_content: str) -> None:
    """Refresh the spec-writer AGENTS.md snapshot after a run."""
    os.makedirs(os.path.dirname(paths.agents_md_path), exist_ok=True)
    summary = [
        "# spec-writer -- Project Memory",
        "",
        "## Latest Spec Snapshot",
        f"- Technical specification: {paths.spec_path}",
        f"- Tier 2 eval suite: {paths.tier2_eval_suite_path}",
        f"- Source PRD: {paths.prd_path}",
        f"- Research bundle: {paths.research_bundle_path}",
    ]
    if spec_content:
        summary.extend(
            [
                "",
                "## Notes",
                "- Maintain PRD traceability matrix completeness.",
                "- Tier 2 evals must derive from architecture decisions, not copy Tier 1.",
                "- If research gaps remain, return needs_additional_research status.",
            ]
        )
    with open(paths.agents_md_path, "w") as f:
        f.write("\n".join(summary) + "\n")


# ---------------------------------------------------------------------------
# Output normalization
# ---------------------------------------------------------------------------

def normalize_spec_writer_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Normalize a raw spec-writer run into the evaluator/orchestrator contract.

    Output shape::

        {
            "spec_path": str,
            "tier2_eval_suite_path": str,
            "status": str,  # "complete" | "needs_additional_research"
            "needs_additional_research": bool,
            "additional_research_request": str,
            "raw_result": dict,
        }
    """
    paths = get_spec_writer_runtime_paths(project_dir, project_id)

    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    assistant_text = _last_assistant_text(messages)
    status_block = _extract_status_block(assistant_text)

    # Read produced artifacts
    spec_content = _read_text(paths.spec_path)
    tier2_content = _read_text(paths.tier2_eval_suite_path)

    # Determine status from the agent's status block
    raw_status = str(status_block.get("status", "")).strip().lower()
    needs_research = (
        status_block.get("needs_additional_research", False) is True
        or raw_status == "needs_additional_research"
    )
    status = "needs_additional_research" if needs_research else "complete"
    additional_request = str(status_block.get("additional_research_request", "")).strip()

    # Resolve paths from status block or defaults
    spec_path = paths.spec_path
    if status_block.get("technical_spec_path"):
        candidate = os.path.join(project_dir, status_block["technical_spec_path"])
        if os.path.isfile(candidate):
            spec_path = candidate

    tier2_path = paths.tier2_eval_suite_path
    if status_block.get("tier2_eval_suite_path"):
        candidate = os.path.join(project_dir, status_block["tier2_eval_suite_path"])
        if os.path.isfile(candidate):
            tier2_path = candidate

    # Update agent memory
    update_agent_memory(paths, spec_content)

    return {
        "spec_path": spec_path,
        "tier2_eval_suite_path": tier2_path,
        "status": status,
        "needs_additional_research": needs_research,
        "additional_research_request": additional_request,
        "raw_result": dict(raw_result) if isinstance(raw_result, Mapping) else {"messages": messages},
    }


# ---------------------------------------------------------------------------
# Graph / Runnable / SubAgent factories
# ---------------------------------------------------------------------------

def create_spec_writer_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the internal spec-writer Deep Agent graph.

    Spec Section 6.2:
    - Effort: high
    - Recursion limit: 50
    - Tools: filesystem auto (read_file, write_file, edit_file) + propose_evals
    - Middleware: 6 auto + ToolErrorMiddleware (no SubAgentMiddleware)
    - No web_search / web_fetch (spec-writer works from provided artifacts)
    """
    cfg = get_model_config("spec-writer")
    repo_root = Path(__file__).resolve().parents[2]
    backend = SdkFilesystemBackend(root_dir=str(repo_root), virtual_mode=True)

    tools = [
        propose_evals_tool,
    ]

    return create_deep_agent(
        model=cfg["model_string"],
        tools=tools,
        system_prompt=construct_spec_writer_prompt(project_dir, project_id),
        middleware=[
            ToolErrorMiddleware(),
        ],
        backend=backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        skills=list(skills_dirs or []),
        name="spec-writer-runtime",
    )


def create_spec_writer_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes spec-writer outputs."""
    graph = create_spec_writer_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = graph.invoke(state, config=config)
        return normalize_spec_writer_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_spec_writer_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_spec_writer_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """Return a CompiledSubAgent-compatible dict for the orchestrator."""
    return {
        "name": "spec-writer",
        "description": (
            "Technical specification author. Transforms an approved PRD and "
            "research bundle into a zero-ambiguity technical specification "
            "with full PRD traceability and Tier 2 eval proposals."
        ),
        "runnable": create_spec_writer_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    }


# ---------------------------------------------------------------------------
# Standalone bridge
# ---------------------------------------------------------------------------

def run_spec_writer_agent(
    *,
    project_dir: str,
    project_id: str,
    prd_path: str | None = None,
    research_bundle_path: str | None = None,
    eval_suite_path: str | None = None,
    prd_content: str | None = None,
    research_bundle_content: str | None = None,
    eval_suite_content: str | None = None,
    skills_paths: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge used by the spec-writer eval runner and experiments.

    Constructs the initial state with PRD, research bundle, and eval suite
    references, then invokes the spec-writer runnable and returns normalized
    outputs.
    """
    paths = get_spec_writer_runtime_paths(project_dir, project_id)

    resolved_prd_path = prd_path or paths.prd_path
    resolved_bundle_path = research_bundle_path or paths.research_bundle_path
    resolved_eval_path = eval_suite_path or paths.eval_suite_path

    runnable = create_spec_writer_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )

    state: dict[str, Any] = {
        "project_id": project_id,
        "current_stage": "SPEC_GENERATION",
        "messages": [],
        "prd_path": resolved_prd_path,
        "research_bundle_path": resolved_bundle_path,
        "eval_suite_path": resolved_eval_path,
        "prd_content": prd_content or _read_text(resolved_prd_path),
        "research_bundle_content": research_bundle_content or _read_text(resolved_bundle_path),
        "eval_suite_content": eval_suite_content or _read_text(resolved_eval_path),
        "skills_paths": list(skills_paths or []),
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)

    return runnable.invoke(state)
