# Middleware Catalog

This document catalogs all middleware used across the meta-agent system, organized by agent and source (SDK vs Custom).
It is extracted from the global `AGENTS.md` file to reduce subagent context footprint while providing an authoritative reference.

## Summary Table

| Middleware | Source | Purpose | Used By | Status |
| --- | --- | --- | --- | --- |
| **SDK Middleware (Explicitly Imported)** |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading | PM, all subagents | ✅ Active |
| SkillsMiddleware | SDK | On-demand SKILL.md loading | PM, all subagents | ✅ Active |
| SummarizationToolMiddleware | SDK | Automatic compaction + compact_conversation tool | PM, research, evaluation, code, plan-writer | ✅ Active |
| CompiledSubAgent, SubAgent | SDK | Subagent delegation support | PM, all subagents | ✅ Active |
| **SDK Middleware (Auto-Attached by create_deep_agent)** |
| TodoListMiddleware | SDK | Provides write_todos tool for task planning | All agents | ✅ Active |
| FilesystemMiddleware | SDK | Provides ls, read_file, write_file, edit_file tools | All agents | ✅ Active |
| SubAgentMiddleware | SDK | Provides task tool for delegation to subagents | All agents | ✅ Active |
| AnthropicPromptCachingMiddleware | SDK | Anthropic cache breakpoints, prompt caching | All agents | ✅ Active |
| PatchToolCallsMiddleware | SDK | Tool call normalization, patches dangling tool calls | All agents | ✅ Active |
| HumanInTheLoopMiddleware | SDK | HITL interrupt handling via interrupt_on parameter | PM (gated tools) | ✅ Active |
| **Custom Middleware** |
| MetaAgentStateMiddleware | Custom | Extends graph state with custom fields (current_stage, decision_log, etc.) | PM only | ✅ Active |
| DynamicSystemPromptMiddleware | Custom | Stage-aware prompt recomposition based on current_stage | PM only | ✅ Active |
| AskUserMiddleware | Custom | Structured user questioning via ask_user tool (ported from CLI) | PM only | ✅ Active |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except, returns structured error JSON | PM, all subagents | ✅ Active |
| AgentDecisionStateMiddleware | Custom | General-purpose decision/assumption state fields (decision_log, assumption_log, approval_history) | Research, verification | ✅ Active |

## PM Orchestrator Middleware Stack

The PM orchestrator (meta_agent/graph.py) uses the following middleware stack:

### Explicit Middleware (Lines 159-168)

| Order | Middleware | Source | Purpose |
| --- | --- | --- | --- |
| 0 | DynamicSystemPromptMiddleware | Custom | Reads current_stage from state, builds stage-aware prompt, strips stale system messages from history. MUST be first in middleware list. |
| 1 | MetaAgentStateMiddleware | Custom | Extends the graph state schema with meta-agent fields (current_stage, decision_log, assumption_log, approval_history, project paths, participation mode). |
| 2 | AskUserMiddleware | Custom | Provides ask_user tool for structured user questioning (free-form text + multiple-choice). Uses LangGraph interrupt() to pause execution. |
| 3 | MemoryMiddleware | SDK | Loads the orchestrator's tiered AGENTS.md files with per-agent isolation. |
| 4 | SkillsMiddleware | SDK | On-demand SKILL.md loading from skills directories (langchain, langsmith, anthropic). |
| 5 | SummarizationToolMiddleware | SDK | Exposes compact_conversation tool for agent-controlled compaction on top of auto-attached summarization layer. |
| 6 | ToolErrorMiddleware | Custom | Wraps tool calls in try/except, converts exceptions to ToolMessage with structured error JSON so LLM can self-correct. |

### Auto-Attached Middleware (Added by SDK)

| Middleware | Source | Purpose |
| --- | --- | --- |
| TodoListMiddleware | SDK | Provides write_todos tool for task planning |
| FilesystemMiddleware | SDK | Provides ls, read_file, write_file, edit_file, glob, grep tools via configured backend |
| SubAgentMiddleware | SDK | Provides task tool for delegation to subagents |
| AnthropicPromptCachingMiddleware | SDK | Anthropic cache breakpoints, prompt caching |
| PatchToolCallsMiddleware | SDK | Tool call normalization, patches dangling tool calls in message history |
| HumanInTheLoopMiddleware | SDK | HITL interrupt handling via interrupt_on parameter (configured for HITL_GATED_TOOLS) |

## Subagent Factory Registration

Each subagent orchestrates its own middleware and tool setup internally via isolated factory functions (e.g., `create_research_agent_subagent()`). 
These factory constructions execute dynamically via the `AGENT_REGISTRY` dictionary in `meta_agent/subagents/configs.py`. The legacy static metadata dictionaries (like `SUBAGENT_CONFIGS` or `SUBAGENT_MIDDLEWARE`) have been removed to assert factories as the single source of truth.

### Research Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| AgentDecisionStateMiddleware | Custom | Provides decision_log, assumption_log, approval_history state fields for decision tracking tools. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |
| SummarizationToolMiddleware | SDK | Agent-controlled compact_conversation tool. |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| SkillsMiddleware | SDK | On-demand SKILL.md loading. |

### Verification Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| AgentDecisionStateMiddleware | Custom | Provides decision_log, assumption_log, approval_history state fields. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Spec Writer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Plan Writer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Code Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Evaluation Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Document Renderer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

## Custom Middleware Deep Dive

### MetaAgentStateMiddleware

**Purpose**: Extends graph state with custom fields specific to the PM orchestrator (current_stage, decision_log, assumption_log, approval_history, project paths, participation mode).

**Why Custom**: The SDK provides TodoListMiddleware for todo lists, but doesn't provide a mechanism for custom state schema extension. This middleware uses the SDK's state_schema merging pattern (same as TodoListMiddleware) to add meta-agent-specific fields directly into the graph state. Tools return Command(update={...}) to update these fields.

**Status**: ✅ Active - Necessary for PM orchestrator state management.

### DynamicSystemPromptMiddleware

**Purpose**: Recomposes the system prompt based on current_stage. Uses wrap_model_call to set the stage-appropriate system prompt on ModelRequest while before_model sanitizes message history to avoid duplicate system messages.

**Why Custom**: The SDK doesn't provide stage-aware prompt recomposition. This is specific to the meta-agent's multi-stage workflow (INTAKE → RESEARCH → DRAFTING → etc.). MUST be first in the explicit middleware list to ensure cache breakpoints are set on the current (not stale) system prompt.

**Status**: ✅ Active - Necessary for multi-stage PM workflow.

### AskUserMiddleware

**Purpose**: Provides an ask_user tool that lets agents pose structured questions with free-form text input and multiple-choice options (always includes an implicit "Other" option). Uses LangGraph interrupt() to pause execution and wait for user input, then parses the response into a formatted ToolMessage.

**Why Custom**: Ported from deepagents_cli (deepagents_cli/ask_user.py). The CLI has this middleware for interactive questioning, but it's not part of the SDK. We ported it to maintain the same pattern for structured user questioning in the meta-agent.

**Status**: ✅ Active - Necessary for structured user questioning in PM orchestrator.

### ToolErrorMiddleware

**Purpose**: Wraps tool calls in try/except to catch exceptions. Converts unhandled exceptions into ToolMessage with status="error" and a structured JSON payload so the LLM can see the failure and self-correct rather than crashing the agent run.

**Why Custom**: The SDK provides PatchToolCallsMiddleware for patching dangling tool calls in message history, but does NOT provide general tool error handling middleware that wraps tool calls in try/except. This fills that gap.

**Status**: ✅ Active - Necessary for robust error handling across all agents.

### AgentDecisionStateMiddleware

**Purpose**: Provides decision_log, assumption_log, and approval_history state fields to ANY agent that needs structured decision tracking. This is the lightweight, reusable counterpart to MetaAgentStateMiddleware (which carries the full PM orchestrator state). Each agent instance gets its own isolated copy of these fields — no collision with the PM agent's state.

**Why Custom**: The SDK doesn't provide a general-purpose decision tracking middleware. This is intentionally lightweight — it only declares state fields. No hooks are needed. Uses the same state_schema merging pattern as TodoListMiddleware.

**Status**: ✅ Active - Necessary for decision tracking in research and verification agents.

## SDK Middleware Reference

### MemoryMiddleware

**Source**: deepagents.middleware.memory

**Purpose**: Loads agent memory from AGENTS.md files. Supports multiple sources that are combined together. Injects memory content into the system prompt via append_to_system_message.

**Why SDK**: This is a core SDK middleware for per-agent instruction loading. We use it for all agents to load their AGENTS.md files with tiered resolution (root → agent-specific → project-local).

### SkillsMiddleware

**Source**: deepagents.middleware.skills

**Purpose**: Loads skills from backend sources and injects them into the system prompt using progressive disclosure (metadata first, full content on demand).

**Why SDK**: This is a core SDK middleware for dynamic skill loading. We use it for all agents to load SKILL.md files from the skills directories (langchain, langsmith, anthropic).

### SummarizationToolMiddleware

**Source**: deepagents.middleware.summarization (via create_summarization_tool_middleware)

**Purpose**: Provides a compact_conversation tool for manual compaction. Composes with SummarizationMiddleware to reuse its summarization engine (model, backend, trigger thresholds) to let the agent compact its own context window.

**Why SDK**: This is an SDK middleware that builds on the auto-attached SummarizationMiddleware. We use it in agents that need agent-controlled compaction (PM, research, evaluation, code, plan-writer).

### FilesystemMiddleware

**Source**: deepagents.middleware.filesystem (auto-attached)

**Purpose**: Provides filesystem and optional execution tools to an agent (ls, read_file, write_file, edit_file, glob, grep, execute). Can evict large tool results to filesystem storage.

**Why SDK**: This is auto-attached by create_deep_agent(). We configure it with a CompositeBackend for the PM orchestrator and bare FilesystemBackend for subagents.

### SubAgentMiddleware

**Source**: deepagents.middleware.subagents (auto-attached)

**Purpose**: Provides a task tool for delegation to subagents. Manages the subagent lifecycle and message routing.

**Why SDK**: This is auto-attached by create_deep_agent(). We configure it with our subagent definitions (research-agent, spec-writer, etc.).

### TodoListMiddleware

**Source**: SDK (auto-attached, not exported in __init__.py)

**Purpose**: Provides a write_todos tool for task planning.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed.

### AnthropicPromptCachingMiddleware

**Source**: SDK (auto-attached)

**Purpose**: Anthropic cache breakpoints, prompt caching.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed.

### PatchToolCallsMiddleware

**Source**: deepagents.middleware.patch_tool_calls (auto-attached)

**Purpose**: Patches dangling tool calls in the messages history. When an AIMessage has tool_calls but no corresponding ToolMessage (e.g., cancelled), it adds a ToolMessage saying the call was cancelled.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed. Note: This is NOT a tool error handler — it's for fixing incomplete message history.
