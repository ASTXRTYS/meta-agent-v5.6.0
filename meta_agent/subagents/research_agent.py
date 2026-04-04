"""Compiled research-agent runtime and normalization helpers."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

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
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.middleware.dynamic_tool_config import DynamicToolConfigMiddleware
from meta_agent.model import get_configured_model, get_model_config
from meta_agent.prompts.research_agent import construct_research_agent_prompt
from meta_agent.safety import RECURSION_LIMITS
from meta_agent.tracing import traceable
from meta_agent.subagents.document_renderer import build_document_renderer_subagent
from meta_agent.tools import (
    get_server_side_tools,
    record_assumption_tool,
    record_decision_tool,
    request_approval_tool,
)


@dataclass(frozen=True)
class ResearchRuntimePaths:
    project_dir: str
    project_id: str
    prd_path: str
    eval_suite_path: str
    decomposition_path: str
    clusters_path: str
    bundle_path: str
    sub_findings_dir: str
    agents_md_path: str


def get_research_runtime_paths(project_dir: str, project_id: str) -> ResearchRuntimePaths:
    """Return canonical absolute runtime paths for the research stage."""
    return ResearchRuntimePaths(
        project_dir=project_dir,
        project_id=project_id,
        prd_path=os.path.join(project_dir, "artifacts", "intake", "research-agent-prd.md"),
        eval_suite_path=os.path.join(project_dir, "evals", "eval-suite-prd.json"),
        decomposition_path=os.path.join(project_dir, "artifacts", "research", "research-decomposition.md"),
        clusters_path=os.path.join(project_dir, "artifacts", "research", "research-clusters.md"),
        bundle_path=os.path.join(project_dir, "artifacts", "research", "research-bundle.md"),
        sub_findings_dir=os.path.join(project_dir, "artifacts", "research", "sub-findings"),
        agents_md_path=os.path.join(project_dir, ".agents", "research-agent", "AGENTS.md"),
    )


def _repo_root() -> str:
    return str(Path(__file__).resolve().parents[2])


def _to_workspace_path(path: str, *, project_dir: str, project_id: str) -> str:
    normalized = os.path.normpath(path)
    repo_root = os.path.normpath(_repo_root())
    if normalized.startswith(repo_root):
        relative = os.path.relpath(normalized, repo_root).replace(os.sep, "/")
        return f"/{relative}"

    marker = f"{os.sep}projects{os.sep}{project_id}{os.sep}"
    if marker in normalized:
        suffix = normalized.split(marker, 1)[1].replace(os.sep, "/")
        return f"/.agents/pm/projects/{project_id}/{suffix}"

    return normalized.replace(os.sep, "/")


def _read_text(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path) as f:
        return f.read()


def _default_eval_project_dir(project_id: str) -> str:
    return os.path.join(_repo_root(), ".agents", "pm", "projects", project_id)


def _localize_workspace_path(path: str | None, *, project_dir: str, project_id: str) -> str:
    if not path:
        return path or ""
    workspace_prefix = f"/.agents/pm/projects/{project_id}/"
    normalized = path.replace("\\", "/")
    if normalized.startswith(workspace_prefix):
        suffix = normalized[len(workspace_prefix) :]
        return os.path.join(project_dir, suffix)
    if normalized.startswith("/workspace/"):
        return os.path.join(_repo_root(), normalized[len("/workspace/") :])
    return path


def _materialize_if_missing(path: str, content: str) -> None:
    if not path or os.path.isfile(path) or not content:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _resolve_skills_dirs(skills_paths: list[str] | None) -> list[str]:
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


def _message_tool_calls(message: Any) -> list[dict[str, Any]]:
    if hasattr(message, "tool_calls") and isinstance(message.tool_calls, list):
        return list(message.tool_calls)
    if isinstance(message, dict):
        tool_calls = message.get("tool_calls", [])
        if isinstance(tool_calls, list):
            return list(tool_calls)
    return []


def _normalize_arg_paths(value: Any, *, project_dir: str, project_id: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize_arg_paths(item, project_dir=project_dir, project_id=project_id)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_arg_paths(item, project_dir=project_dir, project_id=project_id)
            for item in value
        ]
    if isinstance(value, str) and (value.startswith("/") or value.startswith(project_dir)):
        return _to_workspace_path(value, project_dir=project_dir, project_id=project_id)
    return value


def collect_tool_calls(
    messages: Iterable[Any],
    *,
    project_dir: str,
    project_id: str,
) -> list[dict[str, Any]]:
    """Extract ordered tool calls from agent messages."""
    tool_calls: list[dict[str, Any]] = []
    timestamp = 1.0
    for message in messages:
        calls = _message_tool_calls(message)
        for call in calls:
            args = call.get("args", {}) if isinstance(call, dict) else {}
            tool_calls.append(
                {
                    "name": call.get("name", "unknown"),
                    "args": _normalize_arg_paths(
                        args if isinstance(args, dict) else {},
                        project_dir=project_dir,
                        project_id=project_id,
                    ),
                    "timestamp": float(call.get("timestamp", timestamp)),
                }
            )
        timestamp += 1.0
    return tool_calls


def collect_tool_calls_from_events(
    events: Iterable[Mapping[str, Any]],
    *,
    project_dir: str,
    project_id: str,
) -> list[dict[str, Any]]:
    """Extract ordered tool calls from live LangGraph events."""
    tool_calls: list[dict[str, Any]] = []
    fallback_timestamp = 1.0
    for event in events:
        if event.get("event") != "on_tool_start":
            continue
        data = event.get("data", {}) or {}
        raw_args = data.get("input", data.get("kwargs", {}))
        args = raw_args if isinstance(raw_args, dict) else {"input": raw_args}
        tool_calls.append(
            {
                "name": str(event.get("name") or "unknown"),
                "args": _normalize_arg_paths(args, project_dir=project_dir, project_id=project_id),
                "timestamp": float(event.get("metadata", {}).get("observed_at", fallback_timestamp)),
            }
        )
        fallback_timestamp += 1.0
    return tool_calls


def _merge_segments(segments: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted((start, end) for start, end in segments if end > start):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _coverage_ratio(reads: list[Mapping[str, Any]], total_chars: int) -> float:
    if total_chars <= 0:
        return 0.0
    segments: list[tuple[int, int]] = []
    for read in reads:
        args = read.get("args", {}) or {}
        start = args.get("offset", args.get("start"))
        end = args.get("end")
        length = args.get("length", args.get("limit", args.get("num_chars")))
        if isinstance(start, int) and isinstance(end, int):
            segments.append((start, end))
        elif isinstance(start, int) and isinstance(length, int):
            segments.append((start, start + length))
        elif isinstance(length, int) and length >= total_chars:
            segments.append((0, length))
        elif not args:
            segments.append((0, total_chars))
    merged = _merge_segments(segments)
    covered = sum(end - start for start, end in merged)
    return min(covered / total_chars, 1.0)


def build_trace_summary(
    tool_calls: list[dict[str, Any]],
    *,
    prd_path: str,
    prd_content: str,
    eval_suite_path: str,
    approval_history: list[Any] | None = None,
) -> dict[str, Any]:
    """Normalize a tool-call trace into the evaluator contract."""
    prd_markers = {
        prd_path.replace(os.sep, "/") if prd_path else "",
        os.path.basename(prd_path) if prd_path else "",
        "research-agent-prd.md",
        "artifacts/intake/prd.md",
    }
    eval_markers = {
        eval_suite_path.replace(os.sep, "/") if eval_suite_path else "",
        os.path.basename(eval_suite_path) if eval_suite_path else "",
        "eval-suite-prd.json",
    }

    prd_reads = [
        tc for tc in tool_calls
        if tc.get("name") == "read_file"
        and any(marker and marker in json.dumps(tc.get("args", {}), default=str) for marker in prd_markers)
    ]
    eval_reads = [
        tc for tc in tool_calls
        if tc.get("name") == "read_file"
        and any(marker and marker in json.dumps(tc.get("args", {}), default=str) for marker in eval_markers)
    ]
    task_calls = [tc for tc in tool_calls if tc.get("name") == "task"]
    same_time_buckets: dict[float, int] = {}
    for tc in task_calls:
        ts = float(tc.get("timestamp", 0.0))
        same_time_buckets[ts] = same_time_buckets.get(ts, 0) + 1
    task_windows = [
        {
            "start": float(tc.get("timestamp", 0.0)),
            "end": float(tc.get("timestamp", 0.0)) + 1.0,
        }
        for tc in task_calls
    ]
    sub_agents_parallel = any(count > 1 for count in same_time_buckets.values())
    if not sub_agents_parallel and len(task_windows) > 1:
        for idx, window in enumerate(task_windows):
            for other in task_windows[idx + 1 :]:
                if min(window["end"], other["end"]) > max(window["start"], other["start"]):
                    sub_agents_parallel = True
                    break
            if sub_agents_parallel:
                break

    request_approval_calls = [tc for tc in tool_calls if tc.get("name") == "request_approval"]
    approval_count = len(request_approval_calls) or len(approval_history or [])
    approval_timestamp = None
    if request_approval_calls:
        approval_timestamp = float(request_approval_calls[0].get("timestamp", 0.0)) + 0.5

    deep_dive_keywords = ("github", "issue", "repo", "source", "reference", "api", "langchain-anthropic")
    deep_dive_start = None
    for tc in tool_calls:
        if tc.get("name") not in {"web_search", "web_fetch"}:
            continue
        args_text = json.dumps(tc.get("args", {}), default=str).lower()
        if any(keyword in args_text for keyword in deep_dive_keywords):
            deep_dive_start = float(tc.get("timestamp", 0.0))
            break

    prd_total_chars = len(prd_content or "")
    prd_fully_read = bool(prd_reads) and _coverage_ratio(prd_reads, prd_total_chars) >= 0.98

    return {
        "tool_calls": tool_calls,
        "total_tool_calls": len(tool_calls),
        "write_file_calls": sum(1 for tc in tool_calls if tc.get("name") == "write_file"),
        "web_fetches": sum(1 for tc in tool_calls if tc.get("name") == "web_fetch"),
        "task_calls": len(task_calls),
        "skills_read": sum(
            1
            for tc in tool_calls
            if tc.get("name") == "read_file"
            and "/skills/" in json.dumps(tc.get("args", {}), default=str)
        ),
        "prd_total_chars": prd_total_chars,
        "prd_fully_read": prd_fully_read,
        "eval_suite_read": bool(eval_reads),
        "decomposition_persisted": any(
            tc.get("name") == "write_file" and "research-decomposition" in json.dumps(tc.get("args", {}), default=str)
            for tc in tool_calls
        ),
        "sub_agents_parallel": sub_agents_parallel,
        "task_windows": task_windows,
        "hitl_approvals": approval_count,
        "hitl_approval_timestamp": approval_timestamp,
        "deep_dive_start_timestamp": deep_dive_start,
    }


def extract_skill_interactions(tool_calls: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Derive structured skill interactions from skill file reads."""
    interactions: list[dict[str, str]] = []
    seen: set[str] = set()
    for tc in tool_calls:
        if tc.get("name") != "read_file":
            continue
        args_text = json.dumps(tc.get("args", {}), default=str)
        if "/skills/" not in args_text:
            continue
        match = re.search(r"/skills/([^/]+)/SKILL\.md", args_text)
        skill = match.group(1) if match else "unknown-skill"
        if skill in seen:
            continue
        seen.add(skill)
        interactions.append(
            {
                "skill": skill,
                "domain": "research",
                "trigger_reasoning": f"Loaded {skill} because the current research domain required baseline guidance.",
                "reflection": f"{skill} provided the initial framework for this domain before external verification.",
                "internalization": f"The {skill} guidance was converted into concrete research questions and validation targets.",
                "guides_next_action": "Use the skill as a baseline, then verify or refine the finding with primary sources.",
            }
        )
    return interactions


def _extract_urls(text: str) -> list[str]:
    return [url.rstrip("/").rstrip(".").rstrip(",") for url in re.findall(r'https?://[^\s\)>\]"\']+', text or "")]


def extract_api_citations(messages: list[Any]) -> list[dict[str, Any]]:
    """Extract first-class API citations from AIMessage content blocks.

    When web_search_20260209 is used, Claude automatically generates
    citations of type 'web_search_result_location' on text blocks.
    LangChain preserves these in AIMessage.content as list[dict].

    Returns a list of citation dicts with: type, url, title, cited_text,
    and the source text block index.
    """
    citations: list[dict[str, Any]] = []
    for message in messages:
        content = None
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, dict):
            content = message.get("content")

        if not isinstance(content, list):
            continue

        for block_idx, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            block_citations = block.get("citations", [])
            if not block_citations:
                continue
            for citation in block_citations:
                if not isinstance(citation, dict):
                    continue
                citations.append({
                    "type": citation.get("type", "unknown"),
                    "url": citation.get("url", ""),
                    "title": citation.get("title", ""),
                    "cited_text": citation.get("cited_text", ""),
                    "encrypted_index": citation.get("encrypted_index"),
                    "block_index": block_idx,
                    "source": "api",
                })
    return citations


def build_citation_support(bundle_content: str, tool_calls: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Post-hoc citation support via URL matching.

    DEPRECATED: Prefer api_citations from extract_api_citations() which uses
    first-class Claude API citation metadata (web_search_result_location).
    This function is retained as a fallback when API citations are unavailable.
    """
    cited_urls = _extract_urls(bundle_content)
    fetched_urls = {
        str(tc.get("args", {}).get("url", "")).rstrip("/").rstrip(".").rstrip(",")
        for tc in tool_calls
        if tc.get("name") == "web_fetch"
    }
    support = [
        {
            "url": url,
            "supported": url in fetched_urls,
            "support_type": "web_fetch_trace" if url in fetched_urls else "missing_fetch",
        }
        for url in cited_urls
    ]
    return support, cited_urls


def build_delegation_context(tool_calls: list[dict[str, Any]]) -> str:
    tasks = [tc for tc in tool_calls if tc.get("name") == "task"]
    if not tasks:
        return "No delegated research tasks were captured in the trace."
    lines = [
        f"Delegation topology selected dynamically with {len(tasks)} task call(s).",
        "Each task was expected to cover a distinct research slice and return a sub-finding artifact.",
    ]
    for idx, task in enumerate(tasks, start=1):
        args = task.get("args", {}) or {}
        lines.append(
            f"{idx}. subagent_type={args.get('subagent_type', 'general-purpose')} "
            f"description={str(args.get('description', ''))[:160]}"
        )
    return "\n".join(lines)


def build_gap_remediation_context(bundle_content: str, decomposition_content: str) -> str:
    sections = []
    for title in (
        "## Unresolved Questions for Spec-Writer",
        "## Unresolved Research Gaps",
        "## Gap and Contradiction Remediation Log",
    ):
        if title in bundle_content:
            parts = bundle_content.split(title, 1)[1]
            next_heading = re.search(r"\n##\s+", parts)
            sections.append(title + parts[: next_heading.start()] if next_heading else title + parts)
    if sections:
        return "\n\n".join(section.strip() for section in sections)
    if decomposition_content:
        return "Remediation context was derived from the research decomposition and subsequent synthesis."
    return ""


def update_agent_memory(paths: ResearchRuntimePaths, bundle_content: str) -> None:
    """Refresh the research-agent AGENTS.md snapshot after a run."""
    os.makedirs(os.path.dirname(paths.agents_md_path), exist_ok=True)
    summary = [
        "# research-agent — Project Memory",
        "",
        "## Latest Research Snapshot",
        f"- Research bundle: {paths.bundle_path}",
        f"- Decomposition: {paths.decomposition_path}",
    ]
    if bundle_content:
        summary.extend(
            [
                "",
                "## Notes",
                "- Keep the research bundle organized by decision topic, not by source dump.",
                "- Preserve unresolved gaps explicitly for the spec-writer feedback loop.",
                "- Do not reactivate RI-001 unless the integration contract is intentionally expanded.",
            ]
        )
    with open(paths.agents_md_path, "w") as f:
        f.write("\n".join(summary) + "\n")


def normalize_research_outputs(
    raw_result: Mapping[str, Any],
    *,
    project_dir: str,
    project_id: str,
    input_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a raw research-agent run into the evaluator contract."""
    paths = get_research_runtime_paths(project_dir, project_id)
    input_state = input_state or {}

    prd_path = str(input_state.get("prd_path") or paths.prd_path)
    eval_suite_path = str(input_state.get("eval_suite_path") or paths.eval_suite_path)
    prd_content = str(input_state.get("prd_content") or _read_text(prd_path))
    eval_suite_content = str(input_state.get("eval_suite_content") or _read_text(eval_suite_path))

    messages = list(raw_result.get("messages", [])) if isinstance(raw_result, Mapping) else []
    tool_calls = collect_tool_calls(messages, project_dir=project_dir, project_id=project_id)

    bundle_content = _read_text(paths.bundle_path)
    decomposition_content = _read_text(paths.decomposition_path)
    hitl_cluster_content = _read_text(paths.clusters_path)
    trace_summary = build_trace_summary(
        tool_calls,
        prd_path=prd_path,
        prd_content=prd_content,
        eval_suite_path=eval_suite_path,
        approval_history=list(raw_result.get("approval_history", [])),
    )
    skill_interactions = extract_skill_interactions(tool_calls)
    delegation_context = build_delegation_context(tool_calls)
    gap_remediation_context = build_gap_remediation_context(bundle_content, decomposition_content)
    citation_claim_support, citation_urls = build_citation_support(bundle_content, tool_calls)

    # Prefer first-class API citations over post-hoc URL matching
    api_citations = extract_api_citations(messages)

    update_agent_memory(paths, bundle_content)

    state_out = {
        "research_bundle_path": paths.bundle_path,
        "decomposition_path": paths.decomposition_path,
        "trace_summary": trace_summary,
    }

    artifacts_written = [
        path
        for path in (
            paths.decomposition_path,
            paths.clusters_path,
            paths.bundle_path,
            paths.agents_md_path,
        )
        if os.path.exists(path)
    ]

    return {
        "messages": messages,
        "research_bundle_path": paths.bundle_path,
        "research_bundle_content": bundle_content,
        "decomposition_path": paths.decomposition_path,
        "decomposition_content": decomposition_content,
        "trace_summary": trace_summary,
        "skill_interactions": skill_interactions,
        "delegation_context": delegation_context,
        "gap_remediation_context": gap_remediation_context,
        "hitl_cluster_content": hitl_cluster_content,
        "citation_claim_support": citation_claim_support,
        "citation_urls": citation_urls,
        "api_citations": api_citations,
        "state_out": state_out,
        "output_state": dict(state_out),
        "current_research_path": paths.bundle_path if bundle_content else None,
        "artifacts_written": artifacts_written,
        "project_id": project_id,
        "prd_path": prd_path,
        "prd_content": prd_content,
        "eval_suite_path": eval_suite_path,
        "eval_suite_content": eval_suite_content,
    }


def create_research_agent_graph(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create the internal research-agent graph."""
    cfg = get_model_config("research-agent")
    model = get_configured_model("research-agent")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()

    # SummarizationToolMiddleware — agent-controlled compact_conversation
    # Uses composite_backend for /conversation_history/ offloading
    summarization_tool_mw = create_summarization_tool_middleware(
        cfg["model_string"], composite_backend
    )

    memory_sources = []
    project_agents_md = os.path.join(project_dir, ".agents", "research-agent", "AGENTS.md")
    if os.path.isfile(project_agents_md):
        memory_sources.append(project_agents_md)
    global_agents_md = str(repo_root / ".agents" / "research-agent" / "AGENTS.md")
    if os.path.isfile(global_agents_md):
        memory_sources.append(global_agents_md)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    resolved_skills = _resolve_skills_dirs(skills_dirs)
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

    tools = [
        request_approval_tool,
        record_decision_tool,
        record_assumption_tool,
        *get_server_side_tools(),
    ]

    # Make document-renderer available as a named subagent so the
    # research-agent can delegate rendering via task(agent="document-renderer")
    doc_renderer = build_document_renderer_subagent(resolved_skills)

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=construct_research_agent_prompt(project_dir, project_id),
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
        interrupt_on={"request_approval": True},
        name="research-agent-runtime",
    )


def create_research_agent_runnable(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> Any:
    """Create a compiled runnable that normalizes research outputs."""
    graph = create_research_agent_graph(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    def _invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        # Apply recursion limit per spec Section 19.5
        if config is None:
            config = {}
        config["recursion_limit"] = RECURSION_LIMITS["research-agent"]
        
        raw_result = graph.invoke(state, config=config)
        return normalize_research_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
            input_state=state,
        )

    async def _ainvoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        # Apply recursion limit per spec Section 19.5
        if config is None:
            config = {}
        config["recursion_limit"] = RECURSION_LIMITS["research-agent"]
        
        raw_result = await graph.ainvoke(state, config=config)
        return normalize_research_outputs(
            raw_result,
            project_dir=project_dir,
            project_id=project_id,
            input_state=state,
        )

    return RunnableLambda(_invoke, afunc=_ainvoke)


def create_research_agent_subagent(
    *,
    project_dir: str,
    project_id: str,
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Return a CompiledSubAgent for the orchestrator."""
    return CompiledSubAgent(
        name="research-agent",
        description=(
            "Deep ecosystem researcher. Performs multi-pass research, parallel delegation, "
            "HITL deep-dive verification, and produces the canonical research bundle."
        ),
        runnable=create_research_agent_runnable(
            project_dir=project_dir,
            project_id=project_id,
            skills_dirs=skills_dirs,
        ),
    )


def run_research_agent_live(inputs: dict[str, Any]) -> dict[str, Any]:
    """Live-run adapter from dataset inputs to normalized evaluator outputs.

    Used by the eval runner in trace mode and LangSmith trace experiments.
    Invokes the real research-agent runtime instead of synthetic replay.
    """
    project_id = str(inputs.get("project_id", "meta-agent"))
    project_dir = str(
        inputs.get("project_dir")
        or inputs.get("config", {}).get("project_dir")
        or _default_eval_project_dir(project_id)
    )
    prd_path = inputs.get("prd_path")
    if prd_path:
        prd_path = _localize_workspace_path(str(prd_path), project_dir=project_dir, project_id=project_id) or None
    eval_suite_path = inputs.get("eval_suite_path")
    if eval_suite_path:
        eval_suite_path = _localize_workspace_path(str(eval_suite_path), project_dir=project_dir, project_id=project_id) or None

    return run_research_agent(
        project_dir=project_dir,
        project_id=project_id,
        prd_path=prd_path,
        eval_suite_path=eval_suite_path,
        prd_content=inputs.get("prd_content"),
        eval_suite_content=inputs.get("eval_suite_content"),
        skills_paths=inputs.get("skills_paths"),
        twitter_handles=inputs.get("twitter_handles"),
        extra_state={**(inputs.get("extra_state") or {}), "auto_approve_hitl": True},
    )


def run_research_agent(
    *,
    project_dir: str,
    project_id: str,
    prd_path: str | None = None,
    eval_suite_path: str | None = None,
    prd_content: str | None = None,
    eval_suite_content: str | None = None,
    skills_paths: list[str] | None = None,
    twitter_handles: list[str] | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standalone bridge used by the research eval runner and experiments."""
    runnable = create_research_agent_runnable(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_paths,
    )
    resolved_prd = prd_path or get_research_runtime_paths(project_dir, project_id).prd_path
    resolved_eval = eval_suite_path or get_research_runtime_paths(project_dir, project_id).eval_suite_path
    initial_message = {
        "role": "user",
        "content": (
            f"You are the research agent. An approved PRD exists at "
            f"{resolved_prd} and the Tier 1 eval suite is at "
            f"{resolved_eval}. The project ID is {project_id}. "
            f"Execute the full 10-phase research protocol. "
            f"Produce all 5 required output artifacts."
        ),
    }
    state = {
        "project_id": project_id,
        "current_stage": "RESEARCH",
        "messages": [initial_message],
        "prd_path": resolved_prd,
        "eval_suite_path": resolved_eval,
        "prd_content": prd_content or "",
        "eval_suite_content": eval_suite_content or "",
        "skills_paths": list(skills_paths or []),
        "twitter_handles": list(twitter_handles or []),
        "config": {
            "project_dir": project_dir,
            "project_id": project_id,
        },
    }
    if extra_state:
        state.update(extra_state)
    thread_id = f"eval-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
    return runnable.invoke(state, config=config)
