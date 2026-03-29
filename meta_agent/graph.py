"""Main graph entry point for the meta-agent system.

Spec Reference: Section 22.4

Creates the orchestrator graph with full middleware stack via create_deep_agent().
Uses real deepagents SDK — no mocks.

Middleware order (per Section 22.4):
  0. DynamicSystemPromptMiddleware (explicit — reads current_stage from state)
  1. MetaAgentStateMiddleware (explicit — extends state schema)
  2. TodoListMiddleware (auto — added by create_deep_agent)
  3. FilesystemMiddleware (auto — added by create_deep_agent)
  4. SubAgentMiddleware (auto — added by create_deep_agent)
  5. SummarizationMiddleware (auto — added by create_deep_agent)
  6. AnthropicPromptCachingMiddleware (auto — added by create_deep_agent)
  7. PatchToolCallsMiddleware (auto — added by create_deep_agent)
  8. SummarizationToolMiddleware (explicit — agent-controlled compact_conversation)
  9. MemoryMiddleware (explicit — per-agent AGENTS.md loading)
 10. ToolErrorMiddleware (explicit)
 11. HumanInTheLoopMiddleware (auto via interrupt_on parameter)
 12. SkillsMiddleware (explicit via skills= parameter — on-demand SKILL.md loading)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend as SdkFilesystemBackend
from deepagents.middleware.summarization import (
    SummarizationMiddleware,
    SummarizationToolMiddleware,
)
from deepagents.middleware.memory import MemoryMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from meta_agent.state import MetaAgentState, create_initial_state
from meta_agent.configuration import MetaAgentConfig
from meta_agent.project import init_project
from meta_agent.backend import create_checkpointer, create_store
from meta_agent.model import get_model_config
from meta_agent.safety import RECURSION_LIMITS
from meta_agent.middleware.meta_state import MetaAgentStateMiddleware
from meta_agent.middleware.dynamic_system_prompt import DynamicSystemPromptMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS
from meta_agent.prompts.orchestrator import construct_orchestrator_prompt
from meta_agent.subagents.configs import build_orchestrator_subagents


def create_graph(
    config: MetaAgentConfig | None = None,
    project_dir: str = "",
    project_id: str = "",
) -> Any:
    """Create the meta-agent orchestrator graph.

    Creates a real Deep Agent with the full middleware stack per Section 22.4.
    Uses create_deep_agent() from the deepagents SDK.

    Args:
        config: MetaAgentConfig (uses defaults if None).
        project_dir: Project directory path.
        project_id: Project identifier.

    Returns:
        Compiled LangGraph StateGraph from create_deep_agent().
    """
    import os

    cfg = config or MetaAgentConfig.from_env()

    # Ensure project directory structure exists (creates dirs + AGENTS.md files)
    if project_id and project_dir:
        base_dir = os.path.dirname(project_dir) if project_dir.endswith(project_id) else project_dir
        # Only init if the project dir doesn't look fully initialized
        agents_md = os.path.join(project_dir, ".agents", "orchestrator", "AGENTS.md")
        if not os.path.exists(agents_md):
            try:
                init_project(base_dir=os.path.dirname(os.path.dirname(project_dir)),
                           project_name=project_id)
            except Exception:
                # Non-fatal — directories may already exist or path may differ
                pass

    # Create backend, checkpointer, store
    repo_root = Path(__file__).resolve().parent.parent
    backend = SdkFilesystemBackend(root_dir=str(repo_root), virtual_mode=True)
    checkpointer = create_checkpointer()
    store = create_store()

    # Build system prompt from orchestrator prompt composer
    system_prompt = construct_orchestrator_prompt(
        stage="INTAKE",
        project_dir=project_dir,
        project_id=project_id,
    )

    # MetaAgentStateMiddleware — extends graph state schema
    meta_state_mw = MetaAgentStateMiddleware()

    # DynamicSystemPromptMiddleware — MUST be first per Section 22.4
    dynamic_prompt_mw = DynamicSystemPromptMiddleware(
        project_dir=project_dir,
        project_id=project_id,
    )

    # SummarizationToolMiddleware — agent-controlled compact_conversation
    # Per Plan 1.2.1 / Spec 8.11: requires a SummarizationMiddleware instance.
    summarization_mw = SummarizationMiddleware(model=cfg.model_name, backend=backend)
    summarization_tool_mw = SummarizationToolMiddleware(summarization_mw)

    # MemoryMiddleware — per-agent AGENTS.md loading (Spec 22.4, Section 13.4.6)
    # Orchestrator loads its own AGENTS.md; isolation rule: no cross-agent memory.
    memory_sources = []
    if project_dir:
        project_agents_md = os.path.join(
            project_dir, ".agents", "orchestrator", "AGENTS.md"
        )
        if os.path.isfile(project_agents_md):
            memory_sources.append(project_agents_md)
    global_agents_md = str(repo_root / ".agents" / "orchestrator" / "AGENTS.md")
    if os.path.isfile(global_agents_md):
        memory_sources.append(global_agents_md)
    memory_mw = MemoryMiddleware(backend=backend, sources=memory_sources)

    # ToolErrorMiddleware
    tool_error_mw = ToolErrorMiddleware()

    # Build explicit middleware list (order matters per Section 22.4)
    explicit_middleware = [
        dynamic_prompt_mw,     # 0. Dynamic system prompt (MUST be first)
        meta_state_mw,         # 1. Extends state schema
        summarization_tool_mw, # 8. Agent-controlled compact_conversation
        memory_mw,             # 9. Per-agent AGENTS.md loading
        tool_error_mw,         # 10. ToolError (catches tool exceptions)
    ]

    # Build interrupt_on config for HITL-gated tools
    interrupt_on = {
        tool_name: True
        for tool_name in HITL_GATED_TOOLS
    }

    # Resolve skills directories (Section 11, 22.4)
    # All 31 skills from LangChain, LangSmith, and Anthropic repos are available
    # to the orchestrator via SkillsMiddleware for on-demand SKILL.md loading.
    # Each repo has a different internal layout, so we point to the directory
    # that contains the skill subdirectories (each with a SKILL.md).
    skills_dirs = [
        str(repo_root / "skills" / "langchain" / "config" / "skills"),  # 11 skills
        str(repo_root / "skills" / "langsmith" / "config" / "skills"),  # 3 skills
        str(repo_root / "skills" / "anthropic" / "skills"),             # 17 skills
    ]

    # Build SDK-compatible subagent definitions (Section 6, 22.3)
    subagents = build_orchestrator_subagents(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    # Create the real graph via deepagents SDK
    graph = create_deep_agent(
        model=cfg.model_name,
        tools=LANGCHAIN_TOOLS,
        system_prompt=system_prompt,
        middleware=explicit_middleware,
        subagents=subagents,
        checkpointer=checkpointer,
        store=store,
        backend=backend,
        interrupt_on=interrupt_on,
        skills=skills_dirs,
        name="meta-agent-orchestrator",
    )

    return graph
