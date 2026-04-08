"""Main graph entry point for the meta-agent system.

Spec Reference: Section 22.4

Creates the orchestrator graph with full middleware stack via create_deep_agent().
Uses real deepagents SDK — no mocks.

Middleware order (per Section 22.4):
  0. DynamicSystemPromptMiddleware (explicit — reads current_stage from state)
  1. MetaAgentStateMiddleware (explicit — extends state schema)
  2. AskUserMiddleware (explicit — structured user questioning)
  3. MemoryMiddleware (explicit — per-agent AGENTS.md loading)
  4. SkillsMiddleware (explicit — on-demand SKILL.md loading)
  5. SummarizationToolMiddleware (explicit — automatic compaction + compact_conversation tool)
  6. ToolErrorMiddleware (explicit)
  7. DynamicToolConfigMiddleware (explicit — stage-aware tool choice and filtering)
  8. TodoListMiddleware (auto — added by create_deep_agent)
  9. FilesystemMiddleware (auto — added by create_deep_agent)
 10. SubAgentMiddleware (auto — added by create_deep_agent)
 11. AnthropicPromptCachingMiddleware (auto — added by create_deep_agent)
 12. PatchToolCallsMiddleware (auto — added by create_deep_agent)
 13. HumanInTheLoopMiddleware (auto via interrupt_on parameter)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.middleware.summarization import (
    create_summarization_tool_middleware,
)
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from meta_agent.state import MetaAgentState, create_initial_state
from meta_agent.configuration import MetaAgentConfig
from meta_agent.project import init_project
from meta_agent.backend import (
    create_composite_backend,
    create_bare_filesystem_backend,
    create_checkpointer,
    create_store,
)
from meta_agent.model import get_model_config, get_configured_model
from meta_agent.safety import RECURSION_LIMITS
from meta_agent.middleware.meta_state import MetaAgentStateMiddleware
from meta_agent.middleware.dynamic_system_prompt import DynamicSystemPromptMiddleware
from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware
from meta_agent.middleware.ask_user import AskUserMiddleware
from meta_agent.config.memory import get_memory_sources
from meta_agent.middleware.dynamic_tool_config import DynamicToolConfigMiddleware
from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS
from meta_agent.prompts.pm import construct_pm_prompt
from meta_agent.subagents.configs import build_pm_subagents
from meta_agent.tracing import prepare_agent_state


def create_graph(
    config: MetaAgentConfig | None = None,
    project_dir: str = "",
    project_id: str = "",
) -> Any:
    """Create the meta-agent PM graph.

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
        agents_md = os.path.join(project_dir, ".agents", "pm", "AGENTS.md")
        if not os.path.exists(agents_md):
            try:
                init_project(base_dir=os.path.dirname(os.path.dirname(project_dir)),
                           project_name=project_id)
            except Exception:
                # Non-fatal — directories may already exist or path may differ
                pass

    # Create backend, checkpointer, store
    repo_root = Path(__file__).resolve().parent.parent
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend(root_dir=repo_root)
    checkpointer = create_checkpointer()
    store = create_store()

    # Build system prompt from PM prompt composer
    system_prompt = construct_pm_prompt(
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
    # Uses composite_backend for /conversation_history/ offloading
    summarization_tool_mw = create_summarization_tool_middleware(
        cfg.model_name, composite_backend
    )

    # MemoryMiddleware
    memory_sources = get_memory_sources("pm", project_dir, repo_root)
    memory_mw = MemoryMiddleware(backend=bare_fs, sources=memory_sources)

    # Resolve skills directories (Section 11, 22.4)
    # All skills from LangChain, LangSmith, and Anthropic repositories are
    # sourced from the canonical .agents/skills mirror for runtime loading.
    # Each repo has a different internal layout, so we point to the directory
    # that contains the skill subdirectories (each with a SKILL.md).
    skills_dirs = [
        str(repo_root / ".agents" / "skills" / "langchain" / "config" / "skills"),
        str(repo_root / ".agents" / "skills" / "langsmith" / "config" / "skills"),
        str(repo_root / ".agents" / "skills" / "anthropic" / "skills"),
    ]

    # SkillsMiddleware — explicit, with bare FS for absolute SKILL.md paths
    # Per CLI pattern: SkillsMiddleware uses its own bare FilesystemBackend
    skills_mw = SkillsMiddleware(backend=bare_fs, sources=skills_dirs)

    # ToolErrorMiddleware
    tool_error_mw = ToolErrorMiddleware()

    # AskUserMiddleware — structured user questioning (ported from CLI)
    # Provides `ask_user` tool for multiple-choice + free-text questions.
    # The tool calls interrupt() internally, no interrupt_on entry needed.
    ask_user_mw = AskUserMiddleware()

    # DynamicToolConfigMiddleware — stage-aware tool choice and filtering
    # Configuration can be extended as stage-specific tool policies are defined.
    dynamic_tool_config_mw = DynamicToolConfigMiddleware(tool_config={})

    # Build explicit middleware list (order matters per Section 22.4)
    explicit_middleware = [
        dynamic_prompt_mw,     # 0. Dynamic system prompt (MUST be first)
        meta_state_mw,         # 1. Extends state schema
        ask_user_mw,           # 2. Structured user questioning
        memory_mw,             # 3. Per-agent AGENTS.md loading
        skills_mw,             # 4. Skills loading from SKILL.md files
        summarization_tool_mw, # 5. Agent-controlled compact_conversation
        tool_error_mw,         # 6. ToolError (catches tool exceptions)
        dynamic_tool_config_mw, # 7. Stage-aware tool choice and filtering
    ]

    # Build interrupt_on config for HITL-gated tools
    interrupt_on = {
        tool_name: True
        for tool_name in HITL_GATED_TOOLS
    }

    # Build SDK-compatible subagent definitions (Section 6, 22.3)
    subagents = build_pm_subagents(
        project_dir=project_dir,
        project_id=project_id,
        skills_dirs=skills_dirs,
    )

    # Emit prepare_agent_state spans (Spec 18.5.1, Gap 1)
    # Documents what each agent was provisioned with at graph creation time.
    prepare_agent_state(
        agent_name="pm",
        state_keys=list(MetaAgentState.__annotations__.keys()),
        artifact_paths=[project_dir] if project_dir else [],
        skill_dirs=skills_dirs,
        tools=[t.name for t in LANGCHAIN_TOOLS],
    )
    for sa in subagents:
        prepare_agent_state(
            agent_name=sa["name"],
            skill_dirs=sa.get("skills", []),
            tools=[t.name for t in sa.get("tools", []) if hasattr(t, "name")],
        )

    # Create the real graph via deepagents SDK
    graph = create_deep_agent(
        model=get_configured_model("pm"),
        tools=LANGCHAIN_TOOLS,
        system_prompt=system_prompt,
        middleware=explicit_middleware,
        subagents=subagents,
        checkpointer=checkpointer,
        store=store,
        backend=composite_backend,
        interrupt_on=interrupt_on,
        name="meta-agent-pm",
    )

    return graph
