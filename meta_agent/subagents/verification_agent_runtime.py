"""Verification-agent standalone runtime and output normalization.

Spec References: Sections 6.8, 10.5.3

The verification-agent is an external quality gate that cross-checks
artifacts against source requirements.  It runs AFTER an authoring agent
has submitted an artifact (research bundle, spec, or plan) and produces
a structured verdict with pass/needs_revision/blocked status.

Cross-check protocol:
  - research bundle  -> verify against PRD
  - spec             -> verify against PRD + research bundle
  - plan             -> verify against spec
"""

from __future__ import annotations

import json
import os
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
from meta_agent.middleware.agent_decision_state import AgentDecisionStateMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.model import get_configured_model, get_model_config
from meta_agent.prompts.verification_agent import construct_verification_agent_prompt
from meta_agent.subagents.verification_agent import (
    REQUIRED_VERDICT_FIELDS,
    VERIFICATION_STATUSES,
    parse_verification_verdict,
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
# Output normalization
# ---------------------------------------------------------------------------


_DEFAULT_VERDICT: dict[str, Any] = {
    "artifact_type": "unknown",
    "source_path": "",
    "status": "blocked",
    "coverage_summary": "Verification agent did not produce a parseable verdict.",
    "gaps": ["Unable to extract structured verdict from agent output."],
    "recommended_action": "Re-run verification or inspect raw agent output.",
}


def normalize_verification_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
) -> dict[str, Any]:
    """Extract the structured verdict from the verification agent output.

    Searches the agent message stream for a JSON verdict matching the
    ``REQUIRED_VERDICT_FIELDS`` contract.  Falls back to a safe default
    with ``status="blocked"`` if parsing fails.

    Returns the evaluator-contract dict:
        artifact_type, source_path, status, coverage_summary,
        gaps, recommended_action, raw_result.
    """
    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []

    # Walk messages in reverse -- the verdict is typically the last assistant
    # message containing a JSON block.
    verdict: dict[str, Any] | None = None
    for message in reversed(messages):
        text = ""
        if isinstance(message, dict):
            text = str(message.get("content", ""))
        elif hasattr(message, "content"):
            text = str(message.content)
        if not text.strip():
            continue

        try:
            verdict = parse_verification_verdict(text)
            break
        except (json.JSONDecodeError, ValueError, KeyError):
            continue

    if verdict is None:
        verdict = dict(_DEFAULT_VERDICT)

    return {
        "artifact_type": verdict.get("artifact_type", "unknown"),
        "source_path": verdict.get("source_path", ""),
        "status": verdict.get("status", "blocked"),
        "coverage_summary": verdict.get("coverage_summary", ""),
        "gaps": verdict.get("gaps", []),
        "recommended_action": verdict.get("recommended_action", ""),
        "raw_result": dict(raw_result) if isinstance(raw_result, Mapping) else {"messages": []},
    }


# ---------------------------------------------------------------------------
# Graph / runnable / subagent constructors
# ---------------------------------------------------------------------------


def create_verification_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the verification-agent Deep Agent graph.

    Effort: ``max`` (Section 10.5.3)
    Recursion limit: 50
    Tools: ``read_file`` (auto via FilesystemMiddleware)
    Middleware: 6 auto + SkillsMiddleware, ToolErrorMiddleware, MemoryMiddleware
    """
    cfg = get_model_config("verification-agent")
    model = get_configured_model("verification-agent")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    # MemoryMiddleware: project-specific + global AGENTS.md
    memory_sources: list[str] = []
    project_agents_md = os.path.join(project_dir, ".agents", "verification-agent", "AGENTS.md")
    if os.path.isfile(project_agents_md):
        memory_sources.append(project_agents_md)
    global_agents_md = str(repo_root / ".agents" / "verification-agent" / "AGENTS.md")
    if os.path.isfile(global_agents_md):
        memory_sources.append(global_agents_md)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

    return create_deep_agent(
        model=model,
        tools=[],  # read_file provided auto via FilesystemMiddleware
        system_prompt=construct_verification_agent_prompt(project_dir, project_id),
        middleware=[
            AgentDecisionStateMiddleware(),
            memory_mw,
            skills_mw,
            ToolErrorMiddleware(),
        ],
        backend=composite_backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        name="verification-agent-runtime",
    )


def create_verification_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes verification outputs.

    Wraps ``create_verification_agent_graph`` with output normalization
    so the caller receives the evaluator-contract dict directly.
    """
    graph = create_verification_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = graph.invoke(state, config=config)
        return normalize_verification_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_verification_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_verification_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Return a CompiledSubAgent for the orchestrator."""
    return CompiledSubAgent(
        name="verification-agent",
        description=(
            "Artifact verifier. Cross-checks produced artifacts against their "
            "source requirements to confirm completeness before user review."
        ),
        runnable=create_verification_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    )


# ---------------------------------------------------------------------------
# Standalone bridge
# ---------------------------------------------------------------------------


def run_verification_agent(
    *,
    project_dir: str,
    project_id: str,
    artifact_type: str,
    artifact_path: str,
    source_path: str,
    skills_paths: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge for running verification outside the orchestrator.

    Builds the initial state, invokes the verification-agent runnable,
    and returns the normalized evaluator-contract dict.

    Args:
        project_dir: Absolute path to the project workspace.
        project_id: Project identifier (e.g. ``"meta-agent"``).
        artifact_type: Type of artifact being verified
            (``"research_bundle"``, ``"spec"``, or ``"plan"``).
        artifact_path: Path to the artifact file under verification.
        source_path: Path to the source requirements file
            (PRD for research/spec, spec for plan).
        skills_paths: Optional skill directory shorthand paths.
        extra_state: Additional state keys to merge into the initial state.

    Returns:
        Evaluator-contract dict with keys: artifact_type, source_path,
        status, coverage_summary, gaps, recommended_action, raw_result.
    """
    runnable = create_verification_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )

    artifact_content = _read_text(artifact_path)
    source_content = _read_text(source_path)

    state: dict[str, Any] = {
        "project_id": project_id,
        "current_stage": "VERIFICATION",
        "messages": [],
        "artifact_type": artifact_type,
        "artifact_path": artifact_path,
        "artifact_content": artifact_content,
        "source_path": source_path,
        "source_content": source_content,
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)

    return runnable.invoke(state)
