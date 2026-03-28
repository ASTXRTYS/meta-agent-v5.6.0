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
  8. ToolErrorMiddleware (explicit)
  9. HumanInTheLoopMiddleware (auto via interrupt_on parameter)
 10. SkillsMiddleware (explicit via skills= parameter — on-demand SKILL.md loading)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend as SdkFilesystemBackend
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
from meta_agent.middleware.completion_guard import CompletionGuardMiddleware
from meta_agent.middleware.memory_loader import MemoryLoaderMiddleware
from meta_agent.tools import LANGCHAIN_TOOLS
from meta_agent.tools.registry import HITL_GATED_TOOLS
from meta_agent.prompts.orchestrator import construct_orchestrator_prompt


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
    cfg = config or MetaAgentConfig.from_env()

    # Ensure project directory structure exists (creates dirs + AGENTS.md files)
    if project_id and project_dir:
        import os
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

    # ToolErrorMiddleware
    tool_error_mw = ToolErrorMiddleware()

    # Build explicit middleware list (order matters per Section 22.4)
    explicit_middleware = [
        dynamic_prompt_mw,   # 0. Dynamic system prompt
        meta_state_mw,       # 1. Extends state schema
        tool_error_mw,       # 8. ToolError (catches tool exceptions)
    ]

    # Build interrupt_on config for HITL-gated tools
    interrupt_on = {
        tool_name: True
        for tool_name in HITL_GATED_TOOLS
    }

    # Resolve skills directory (Section 11, 22.4)
    # All 31 skills from LangChain, LangSmith, and Anthropic repos are available
    # to the orchestrator via SkillsMiddleware for on-demand SKILL.md loading.
    skills_dir = str(repo_root / "skills")

    # Create the real graph via deepagents SDK
    graph = create_deep_agent(
        model=cfg.model_name,
        tools=LANGCHAIN_TOOLS,
        system_prompt=system_prompt,
        middleware=explicit_middleware,
        checkpointer=checkpointer,
        store=store,
        backend=backend,
        interrupt_on=interrupt_on,
        skills=[skills_dir],
        name="meta-agent-orchestrator",
    )

    return graph
