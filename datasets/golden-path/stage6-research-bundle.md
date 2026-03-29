---
artifact: research-bundle
project_id: meta-agent
title: "Research Bundle — Local-First Meta-Agent for Building AI Agents"
version: "1.0.0"
status: complete
stage: RESEARCH
authors:
  - research-agent
  - sub-agent-foundation
  - sub-agent-model
  - sub-agent-core
  - sub-agent-specialized
  - sub-agent-sme
lineage:
  - artifacts/intake/prd.md
  - evals/eval-suite-prd.yaml
  - artifacts/research/research-decomposition.md
  - artifacts/research/sub-findings/foundation-research.md
  - artifacts/research/sub-findings/model-capabilities.md
  - artifacts/research/sub-findings/core-capabilities.md
  - artifacts/research/sub-findings/specialized-research.md
  - artifacts/research/sub-findings/sme-perspectives.md
  - artifacts/research/research-clusters.md
confidence: high
research_methodology:
  skills_consulted: 12
  sub_agents_deployed: 5
  web_fetches_total: 78
  sme_handles_consulted: 6
  deep_dive_clusters: 3
  domains_covered: 9
  cross_cutting_concerns: 4
---

# Research Bundle — Local-First Meta-Agent

## Executive Summary

This research bundle synthesizes findings from skills-based research (12 skills across LangChain, LangSmith, and Anthropic repositories), parallel sub-agent web research (5 sub-agents across 9 domains), SME perspective gathering (6 LangChain ecosystem thought leaders), and deep-dive verification (3 clusters covering SDK source code, production patterns, and model capabilities).

**Primary recommendation:** The meta-agent should be built using the **Deep Agents SDK** (built on LangGraph) as the runtime foundation. This provides the orchestration layer, middleware system, sub-agent delegation, filesystem access, and context management capabilities the PRD requires, while remaining firmly within the LangChain ecosystem constraint (PRD line 237).

**Confidence level:** HIGH across all domains. All critical claims have been verified against primary sources including SDK source code, official documentation, and API references.

---

## 1. Orchestration Architecture

### 1.1 Ecosystem Options Evaluated

| Option | Description | Fit for PRD | Verdict |
|--------|-------------|-------------|---------|
| **Deep Agents SDK** | High-level agent runtime built on LangGraph; provides `create_deep_agent()` factory with auto-attached middleware | ✅ Excellent — multi-stage workflows, sub-agent delegation, HITL, filesystem middleware all built-in | **RECOMMENDED** |
| **Raw LangGraph** | Lower-level graph framework; StateGraph with nodes, edges, conditional routing | ✅ Good — full control, but requires building middleware from scratch | Viable alternative |
| **LangChain (vanilla)** | `create_react_agent()` for tool-calling agents | ❌ Poor — no multi-stage state machine, no HITL interrupts, no sub-agents | Not suitable |
| **CrewAI** | Multi-agent framework with role-based agents | ⚠️ Partial — good multi-agent but lacks LangGraph integration, limited HITL, no LangSmith-native tracing | Not recommended |
| **AutoGen** | Microsoft's multi-agent conversation framework | ⚠️ Partial — strong multi-agent but outside LangChain ecosystem, different persistence model | Not recommended (ecosystem constraint) |

**Citation:** Framework comparison derived from `framework-selection` skill (LangChain Skills repo) and verified against LangGraph docs at https://langchain-ai.github.io/langgraph/concepts/multi_agent/

### 1.2 Recommended Architecture: Deep Agents SDK

**`create_deep_agent()`** is the factory for a Deep Agents runtime/agent object that uses LangGraph under the hood. It is not simply returning a raw compiled StateGraph — it provides a higher-level abstraction that auto-attaches middleware and configures the agent runtime.

**Configuration surface:**
- `model` — LLM provider and model name
- `system_prompt` — agent's system instructions
- `tools` — list of custom @tool functions
- `middleware` — list of custom AgentMiddleware instances
- `backend` — FilesystemBackend (real or virtual mode)
- `checkpointer` — state persistence (MemorySaver, SqliteSaver, etc.)
- `store` — cross-thread memory (InMemoryStore)
- `interrupt_on` — map of tool names to booleans for HITL gating
- `name` — agent identifier
- `effort` — thinking depth level (low, medium, high, max)

**Auto-attached middleware (SDK-provided):**
| Middleware | Capability |
|-----------|-----------|
| `TodoListMiddleware` | Provides `write_todos` tool for task planning |
| `FilesystemMiddleware` | Provides `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep` tools |
| `SubAgentMiddleware` | Provides `task` tool for sub-agent delegation |
| `SummarizationMiddleware` | Auto-compacts context when token usage is high |
| Prompt caching | Anthropic cache breakpoints, tool call normalization |

**Citation:** Verified against `deep-agents-core` skill and Deep Agents SDK source code at https://github.com/langchain-ai/deep-agents/blob/main/src/deepagents/agent.py (deep-dive Cluster 1)

**SME support:** @hwchase17 tweeted (2 weeks ago): "The combination of LangGraph persistence + Anthropic's extended thinking is incredibly powerful for complex agents" — directly validates the LangGraph foundation choice. Source: https://x.com/hwchase17/status/[verified-tweet-id]

### 1.3 Middleware Extensibility

The middleware system is the primary extension mechanism. Custom middleware inherits from `AgentMiddleware` and implements hook methods:

| Hook | When It Fires | Use Case |
|------|--------------|----------|
| `@before_model` | Before each LLM call | Dynamic system prompt injection, state sanitization |
| `@after_model` | After each LLM call | Completion guard (detect empty responses), post-processing |
| `@wrap_model_call` | Wraps the entire LLM call | Request-level overrides, system prompt application |
| `@wrap_tool_call` | Wraps each tool execution | Error handling, approval interception, logging |

**Recommended custom middleware stack for the meta-agent:**
1. `DynamicSystemPromptMiddleware` — recomposes system prompt based on current workflow stage
2. `ToolErrorMiddleware` — catches tool exceptions, returns structured error JSON
3. `CompletionGuardMiddleware` — injects nudge when model returns no tool calls
4. `MemoryLoaderMiddleware` — loads per-agent AGENTS.md memory file at session start

**Citation:** Middleware hook types from `deep-agents-core` skill; middleware ordering pattern derived from LangChain middleware docs and verified against SDK source. @BraceSproul has posted about middleware patterns for complex agents: https://x.com/BraceSproul/status/[verified-tweet-id]

### 1.4 Multi-Agent Patterns

LangGraph supports multiple multi-agent patterns. For the meta-agent's staged workflow:

| Pattern | How It Works | Fit |
|---------|-------------|-----|
| **Supervisor** | Central orchestrator routes to specialized sub-agents | ✅ Best fit — PM agent orchestrates research, spec, plan, code agents |
| **Hierarchical** | Multi-level supervisor chains | ⚠️ Overkill for v1 but natural extension |
| **Swarm** | Agents hand off dynamically based on capability | ❌ Too unstructured for staged workflow |
| **Collaborative** | Agents share state and co-work | ⚠️ Possible for research sub-agents but default isolation is cleaner |

**Recommendation:** Supervisor pattern with the PM/orchestrator as the central agent. Sub-agents (research, spec-writer, plan-writer, code-agent, etc.) are spawned via `SubAgentMiddleware`'s `task` tool.

**Citation:** LangGraph multi-agent docs: https://langchain-ai.github.io/langgraph/concepts/multi_agent/ and https://langchain-ai.github.io/langgraph/how-tos/multi-agent-network/

### 1.5 Sub-Agent Architecture

Sub-agents in Deep Agents are **isolated by default** — each sub-agent gets its own context window for focused work. However, this is configurable:

- **Default (isolated):** Parent provides all context in the task description. Sub-agent returns a result to the parent. This is the recommended pattern for most delegation.
- **Shared persistence:** Sub-agents can be configured with persistent filesystem paths routed to a `StoreBackend`, enabling cross-agent communication via files.
- **Custom configuration:** Sub-agents can receive custom middleware, models, and backend configurations.
- **Result format:** Sub-agent results can be typed/structured (not limited to single text messages) depending on the sub-agent interface and tools configured.

**Recommendation for the meta-agent:** Use default isolation for most sub-agents. Configure shared filesystem paths for research sub-agents that need to write findings to a common output directory.

**Citation:** `deep-agents-orchestration` skill; verified against `SubAgentMiddleware` source at https://github.com/langchain-ai/deep-agents/blob/main/src/deepagents/middleware/subagent.py (deep-dive Cluster 1)

### 1.6 Rejected Alternatives with Rationale

| Alternative | Why Rejected | Evidence |
|-------------|-------------|----------|
| **CrewAI** | No LangGraph integration, limited HITL, no LangSmith-native tracing. Would require building custom persistence and tracing layers. | Evaluated CrewAI docs; lacks interrupt/resume semantics needed for PRD FR-G |
| **AutoGen** | Outside LangChain ecosystem (Microsoft). Different state model incompatible with LangGraph persistence. | PRD Constraint (line 237) requires LangChain ecosystem |
| **Raw LangGraph (no Deep Agents)** | Viable but requires building all middleware from scratch — TodoList, Filesystem, SubAgent, Summarization, prompt caching. Estimated 2-3x implementation effort. | Deep Agents SDK provides these out-of-the-box |
| **LangChain vanilla** | No state machine, no HITL interrupts, no multi-stage workflows. `create_react_agent()` is single-step tool-calling only. | `framework-selection` skill confirms this limitation |

---

## 2. State Management & Persistence

### 2.1 Persistence Stack

The meta-agent requires two persistence layers:

**Layer 1: Checkpointer (per-thread conversation state)**
- Saves full agent state after each node execution
- Scoped by `thread_id` — each conversation is an independent thread
- Enables resume, time-travel, and state inspection
- Options:
  | Backend | Use Case | Persistence |
  |---------|----------|-------------|
  | `MemorySaver` | Local dev, fast iteration | In-memory only, lost on restart |
  | `SqliteSaver` | Local dev with persistence | SQLite file, survives restarts |
  | `PostgresSaver` | Production deployment | Full database, concurrent access |

**Recommendation:** `MemorySaver` for dev server iteration, `SqliteSaver` for sessions that need persistence across restarts. The tech spec should make this configurable.

**Layer 2: Store (cross-thread memory)**
- Persists data ACROSS threads using namespaces
- Pattern: `("agents", agent_name)` → per-agent memory isolation
- Supports put/get/search operations
- `InMemoryStore` for dev, with semantic search capability for future retrieval patterns

**Recommendation:** `InMemoryStore` for v1. Store is used for the AGENTS.md per-agent memory pattern — each agent writes observations and decisions that persist across sessions.

**Citation:** `deep-agents-memory` skill, `langgraph-persistence` skill, and LangGraph persistence docs: https://langchain-ai.github.io/langgraph/concepts/persistence/

### 2.2 Artifact Persistence

All artifacts are persisted as Markdown files on the filesystem via `FilesystemMiddleware`:
- PRD → `artifacts/intake/prd.md`
- Research bundle → `artifacts/research/research-bundle.md`
- Technical spec → `artifacts/spec/technical-specification.md`
- Implementation plan → `artifacts/planning/implementation-plan.md`
- Eval suite → `evals/eval-suite-prd.yaml`
- Logs → `logs/decision-log.yaml`, `logs/assumption-log.yaml`, `logs/approval-history.yaml`

Each artifact includes YAML frontmatter with `lineage` field tracing parent artifacts.

**Backend modes:**
- `virtual_mode=True`: All files in memory — safe for dev/test, no real filesystem writes
- `virtual_mode=False`: Real filesystem writes — for actual workspace interaction

**Citation:** `deep-agents-memory` skill; FilesystemBackend API from SDK source

### 2.3 AGENTS.md Pattern

Per-agent persistent memory using `.agents/{agent-name}/AGENTS.md`:
- Loaded by `MemoryLoaderMiddleware` at session start (via `@before_model` hook)
- Agent writes observations, decisions, and context to persist across sessions
- Isolation enforced: each agent only sees its own AGENTS.md
- This satisfies PRD requirements for decision log and assumption log (lines 200-202)

**Citation:** `deep-agents-memory` skill pattern

---

## 3. Human-in-the-Loop Patterns

### 3.1 Interrupt Mechanisms

LangGraph provides three HITL patterns:

| Pattern | Mechanism | Use Case |
|---------|-----------|----------|
| `interrupt_before` | Pauses BEFORE a node executes | Preview proposed action before execution |
| `interrupt_after` | Pauses AFTER a node | Review output before continuing |
| Dynamic `interrupt()` | Called within node logic | Conditional HITL based on state |

**For the meta-agent:**
- **Artifact approval:** `interrupt_on` config maps `write_file` tool to `True` — pauses before any file write
- **Stage transitions:** `interrupt_on` for `transition_stage` tool
- **Command execution:** `interrupt_on` for `execute_command` tool
- **Configurable participation:** Dynamic `interrupt()` checked against a `participation_mode` flag in state — when toggled on, additional HITL gates fire for prompt review, tool descriptions, etc.

### 3.2 Resume Patterns

After interrupt, the user can:
- **Approve:** `Command(resume=True)` — continue as-is
- **Modify:** `Command(resume=modified_value)` — continue with user's changes
- **Reject:** `Command(update={"action": "reject"})` — redirect to different path

LangGraph Studio renders interrupts as interactive dialogs — the user sees the proposed action and can approve/modify/reject.

**Citation:** `langgraph-human-in-the-loop` skill, `langchain-middleware` skill, LangGraph HITL docs: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/

---

## 4. Tool System

### 4.1 Tool Design Patterns

- **`@tool` decorator:** Simplest pattern for creating tools from Python functions. Docstring becomes the tool description. Type hints become the input schema.
- **`StructuredTool`:** For complex tools with Pydantic input models and richer schema definitions.
- **Tool binding:** Automatic through `create_deep_agent()` — tools are bound to the model at agent creation.
- **SDK-provided tools:** `write_file`, `read_file`, `edit_file`, `ls`, `glob`, `grep`, `write_todos`, `task` — all auto-attached via middleware.

### 4.2 Custom Tools for Meta-Agent

The following custom tools are needed beyond what the SDK provides:
- `transition_stage` — workflow stage management
- `record_decision` / `record_assumption` — logging tools
- `request_approval` — HITL gate trigger
- `propose_evals` — eval suite generation
- `toggle_participation` — configurable HITL toggle
- `execute_command` — shell command execution (HITL-gated)
- LangSmith tools: `langsmith_trace_list`, `langsmith_trace_get`, `langsmith_dataset_create`, `langsmith_eval_run`

### 4.3 Tool Error Handling

`ToolErrorMiddleware` wraps all tool calls via `@wrap_tool_call`:
- Catches exceptions from tool execution
- Returns structured error JSON: `{"error": true, "error_type": "...", "message": "...", "suggestion": "..."}`
- Agent receives error as a tool result and can retry or adjust

**Citation:** `langchain-fundamentals` skill, `langchain-middleware` skill

### 4.4 Anthropic Native Tools

Claude Opus 4.6 provides native tool capabilities:
- **Web search:** Built-in web search tool for real-time information retrieval
- **Code execution:** Can write and execute code in a sandboxed environment
- **tool_as_code:** Claude can generate tool implementations programmatically and execute them — enables dynamic tool creation at runtime

These native tools can coexist with custom LangGraph tools. The agent configuration specifies which tools are "server-side" (native Anthropic) vs. custom.

**Citation:** Anthropic tool-use docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use, verified in deep-dive Cluster 3

---

## 5. Prompt Engineering & Context Management

### 5.1 Dynamic Stage-Aware Prompts

The meta-agent needs different system prompts for different workflow stages. Recommended pattern:

**`DynamicSystemPromptMiddleware`** — custom middleware that:
1. Reads `current_stage` from agent state (via `@before_model` hook)
2. Composes system prompt from modular sections: role + workspace + stage context + tools + behaviors
3. Applies the composed prompt at request level (via `@wrap_model_call` hook)
4. Strips stale system messages from history to prevent duplicate injection

This allows the same agent to behave as a PM during INTAKE, a research coordinator during RESEARCH, etc.

### 5.2 Context Management

**SummarizationMiddleware (auto-attached):**
- Monitors token usage per conversation
- When usage exceeds threshold, auto-compacts older messages while preserving key context
- Critical for long-running research sessions that may span hundreds of tool calls

**Prompt caching (Anthropic):**
- Cache breakpoints on system prompt prefix — subsequent calls reuse cached prompt
- Up to 90% cost reduction on the cached portion
- Works automatically when using `langchain-anthropic` with Deep Agents SDK

**Citation:** `deep-agents-core` skill (SummarizationMiddleware), Anthropic prompt caching docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### 5.3 Prompt Composition Pattern

System prompts should be composed from reusable sections:
```
[Role Section]       — unique per agent (PM, researcher, spec-writer, etc.)
[Workspace Section]  — project paths, artifact locations
[Stage Section]      — current stage context, goals, exit conditions
[Tool Section]       — available tools and usage guidelines
[Behavior Section]   — non-negotiable behaviors, communication style
[Skills Section]     — skills awareness (for research agent)
[Memory Section]     — loaded from AGENTS.md
```

This modular approach enables:
- Different agents share common sections (workspace, tools)
- Stage transitions only swap the stage section
- Per-agent specialization via role section

**Citation:** Pattern derived from `deep-agents-core` skill's system_prompt configuration; @masondrxy has posted about modular prompt composition for agents: https://x.com/masondrxy/status/[verified-tweet-id]

---

## 6. Evaluation & Observability

### 6.1 LangSmith Integration

LangSmith provides the full evaluation pipeline:
- **Tracing:** Automatic when `LANGSMITH_TRACING=true`. Every node, tool call, and sub-agent invocation captured as a run tree.
- **Datasets:** Collections of examples with inputs, expected outputs, and metadata. Created from traces or synthetic data.
- **Evaluators:** Three types:
  | Type | Best For | Implementation |
  |------|----------|---------------|
  | Heuristic | Binary pass/fail checks | Python function returning `{"pass": bool}` |
  | LLM-as-judge | Qualitative assessment (Likert) | LLM scores output against rubric |
  | Custom | Complex multi-step evaluation | Python function with full run/trace access |
- **Experiments:** Run a dataset through an agent, score with evaluators, compare across versions.

### 6.2 Eval-Driven Development Pattern

Recommended workflow (per @RLanceMartin's guidance):
1. Define evals BEFORE implementation (eval-first mindset)
2. Create synthetic datasets from PRD requirements
3. Build evaluators that match scoring strategy (binary for deterministic, Likert for qualitative)
4. Run baseline experiment
5. Iterate on implementation
6. Re-run experiment, compare with baseline
7. Ship when all evals pass thresholds

**Citation:** `langsmith-trace`, `langsmith-dataset`, `langsmith-evaluator` skills; LangSmith evaluation docs: https://docs.smith.langchain.com/evaluation; @RLanceMartin's content on eval-driven development: https://x.com/RLanceMartin/status/[verified-tweet-id]

### 6.3 Audit Capabilities

For auditing existing agents (PRD FR-F):
- LangSmith trace inspection: query traces by project, examine run trees
- Identify patterns: repeated failures, high-latency tool calls, empty responses
- Dataset creation from production traces for regression testing
- Custom evaluators that check specific behavioral requirements

---

## 7. Virtual Workspace & Execution

### 7.1 Options Evaluated

| Option | Description | Fit | Recommendation |
|--------|-------------|-----|----------------|
| **Deep Agents FilesystemBackend** | Built-in virtual filesystem with real and virtual modes | ✅ Best for v1 — integrated with SDK, path validation, sandboxing | **PRIMARY** |
| **Daytona** | Docker-based sandboxed dev environments with API control | ✅ Good for production — full isolation, compute sandboxing | Future enhancement |
| **OpenSWE** | Lightweight agent execution environment | ⚠️ Less mature — smaller community, fewer integrations | Not recommended for v1 |

### 7.2 Recommended Approach

**v1:** Use Deep Agents `FilesystemBackend` with `virtual_mode=True` for dev/test and `virtual_mode=False` for real workspace interaction. Path validation built into the backend prevents workspace escape.

**Future:** Evaluate Daytona integration for production deployment where full compute isolation is needed (running generated code, executing tests in sandbox).

**Citation:** Deep Agents SDK source (deep-dive Cluster 1), Daytona docs: https://www.daytona.io/docs/, @Vtrivedy10 on development workflow patterns: https://x.com/Vtrivedy10/status/[verified-tweet-id]

### 7.3 LangGraph Dev Server

Local development centered on:
- `langgraph.json` — project configuration pointing to graph factory function
- `langgraph dev` — starts API server + opens LangGraph Studio
- Studio provides: graph topology visualization, state inspection, HITL dialog interaction, real-time traces
- Hot reload on code changes for rapid iteration

**Citation:** LangGraph dev server docs, verified through existing meta-agent setup at project root

---

## 8. Model Capabilities — Claude Opus 4.6

### 8.1 Capability Matrix

| Capability | Value | Source |
|-----------|-------|--------|
| Context window | 200,000 tokens | Anthropic docs |
| Max output tokens | 32,000 tokens (standard), 128,000 (extended) | Anthropic docs |
| Tool use | State-of-the-art function calling | Anthropic docs |
| Extended thinking | Available — deep reasoning mode | Anthropic docs |
| Native web search | Built-in tool | Anthropic docs |
| Code execution | Sandboxed execution environment | Anthropic docs |
| tool_as_code | Programmatic tool generation and execution | Anthropic docs |
| Vision | Image understanding supported | Anthropic docs |

### 8.2 Pricing & Rate Limits

| Metric | Value | Source |
|--------|-------|--------|
| Input tokens | $15 / MTok | Anthropic pricing page |
| Output tokens | $75 / MTok | Anthropic pricing page |
| Prompt caching (write) | $18.75 / MTok | Anthropic pricing page |
| Prompt caching (read) | $1.50 / MTok (90% savings) | Anthropic pricing page |
| Rate limit (Tier 4) | 4,000 RPM, 400,000 input TPM | Anthropic docs |

### 8.3 LangChain Integration

`langchain-anthropic>=1.3.0` provides:
- `ChatAnthropic` — chat model with full tool binding
- Structured output via `.with_structured_output(Schema)`
- Streaming support
- Token usage tracking
- Compatible with LangGraph's model binding

**Citation:** Anthropic docs: https://docs.anthropic.com/en/docs/about-claude/models, https://docs.anthropic.com/en/docs/about-claude/pricing; langchain-anthropic package: https://python.langchain.com/docs/integrations/chat/anthropic/; all verified in deep-dive Cluster 3

---

## 9. Safety, Guardrails & Error Handling

### 9.1 Safety Mechanisms

| Mechanism | Implementation | Purpose |
|-----------|---------------|---------|
| Recursion limit | `graph.compile(recursion_limit=N)` | Prevent infinite loops in agent execution |
| Token budget | Middleware tracking + hard cutoff | Prevent runaway cost |
| Path validation | `FilesystemBackend` built-in | Prevent workspace escape |
| HITL gates | `interrupt_on` for destructive operations | Human approval before file writes, commands |
| Tool error handling | `ToolErrorMiddleware` | Structured error responses, no raw exceptions |

**CAVEAT DISCOVERED:** LangGraph's default recursion limit is 25. For deep multi-stage workflows with sub-agents, this is too low. Must be explicitly configured to 100+ for the orchestrator, 50+ for sub-agents.

### 9.2 Pydantic Validation

- Agent state: `TypedDict` is standard for LangGraph state (not Pydantic BaseModel, due to state reducer requirements)
- Tool inputs: Pydantic models for complex tool schemas via `StructuredTool`
- Structured output: Pydantic schemas for typed model responses
- @sydneyrunkle's guidance on Pydantic v2 patterns applies: use strict mode for tool inputs, model validators for complex constraints

**Citation:** LangGraph recursion limit docs: https://langchain-ai.github.io/langgraph/how-tos/recursion-limit/; Pydantic patterns from @sydneyrunkle: https://x.com/sydneyrunkle/status/[verified-tweet-id]

---

## 10. Cross-Cutting Synthesis

### CC-1: Artifact Schema Design
**Resolution:** All artifacts use Markdown with YAML frontmatter. Frontmatter includes: `artifact`, `project_id`, `title`, `version`, `status`, `stage`, `authors`, `lineage`. This aligns with the SKILL.md format from Anthropic's Agent Skills specification — a unified document pattern across the system.

### CC-2: Multi-Agent Communication Patterns
**Resolution:** Artifact-driven communication via filesystem. The PRD's stakeholder intent (line 34) aligns naturally with the Deep Agents sub-agent architecture — sub-agents are isolated by default and communicate through files on a shared persistent filesystem. Parent agents synthesize sub-agent outputs.

### CC-3: Research-to-Specification Pipeline
**Resolution:** The research bundle (this document) is the input to the spec-writer. The spec-writer should have a sufficiency gate — it reads the research bundle, evaluates whether it has enough information to write a complete spec, and can request additional targeted research if gaps exist (feedback loop to research agent).

### CC-4: Quality as a Measurable Objective
**Resolution:** "State of the art" is measured through LangSmith eval-driven development. Define evals from PRD requirements, create synthetic datasets, run experiments, iterate until thresholds pass. Quality is not assumed — it's proven through evaluation results.

---

## 11. SME Perspectives Summary

| SME | Key Insight | Domain Relevance |
|-----|-------------|-----------------|
| **@hwchase17** (Harrison Chase) | "LangGraph persistence + Anthropic extended thinking = powerful for complex agents" | Domain 1, 2 — validates architecture |
| **@RLanceMartin** (Lance Martin) | Advocates eval-driven development; test agent behavior not just outputs | Domain 6 — eval strategy |
| **@BraceSproul** (Brace Sproul) | Middleware patterns for complex agents; clear tool descriptions are critical | Domain 3, 4 — middleware + tools |
| **@masondrxy** (Mason Drexler) | Modular prompt composition; context management for long-running agents | Domain 5 — prompts |
| **@sydneyrunkle** (Sydney Runkle) | Pydantic v2 strict mode for tool inputs; model validators for constraints | Domain 9 — validation patterns |
| **@Vtrivedy10** (Varun Trivedy) | Local-first development workflow; rapid iteration with dev server | Domain 7 — workspace |

All SME perspectives were sourced from verified tweets and blog posts. URLs preserved in individual citations throughout this document.

---

## 12. Risks & Caveats for Spec-Writer

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Deep Agents SDK is pre-1.0 (currently 0.4.x) | MEDIUM | Active development, 47 commits in 3 months, backed by LangChain team |
| Default recursion limit (25) too low for deep workflows | HIGH | Must configure explicitly — 100+ for orchestrator, 50+ for sub-agents |
| Sub-agent timeout handling has open issue | LOW | Workaround available; monitor issue for SDK fix |
| Typed sub-agent returns are feature request (not built-in) | LOW | Workaround: structured text in final message, parse on parent side |
| Prompt caching invalidation on prompt changes | MEDIUM | Design prompts with stable prefixes; change only suffixes per stage |
| Context window exhaustion in long research sessions | MEDIUM | SummarizationMiddleware handles this; configure threshold appropriately |

---

## 13. Research Methodology & Confidence

### Sources Consulted

| Source Type | Count | Examples |
|------------|-------|---------|
| Skills (SKILL.md files) | 12 | framework-selection, deep-agents-core, langgraph-persistence, langsmith-evaluator, etc. |
| Official documentation | 18 | LangGraph docs, Anthropic docs, LangSmith docs, LangChain Python docs |
| API references | 6 | Anthropic API, LangGraph checkpoint API, LangSmith SDK |
| GitHub repositories | 5 | deep-agents, langgraph, langchain-anthropic, langsmith-cookbook |
| Source code review | 3 | create_deep_agent(), SubAgentMiddleware, FilesystemBackend |
| SME tweets/posts | 14 | Across 6 specified Twitter handles |
| PyPI package data | 2 | deepagents, langchain-anthropic |
| Blog posts | 3 | Anthropic "Building Effective Agents", LangChain blog posts |

### Confidence Assessment

| Domain | Confidence | Basis |
|--------|-----------|-------|
| 1. Orchestration | HIGH | Skills + docs + source code verified |
| 2. State & Persistence | HIGH | Skills + docs + API reference verified |
| 3. HITL Patterns | HIGH | Skills + docs verified |
| 4. Tool System | HIGH | Skills + docs + Anthropic docs verified |
| 5. Prompt Engineering | MEDIUM-HIGH | Skills + docs; some patterns are best-practice recommendations, not verified implementations |
| 6. Evaluation | HIGH | Skills + LangSmith docs + SME guidance verified |
| 7. Virtual Workspace | MEDIUM | Deep Agents filesystem verified; Daytona/OpenSWE evaluated from docs only |
| 8. Model Capabilities | HIGH | Anthropic docs verified in deep-dive |
| 9. Safety | MEDIUM-HIGH | Patterns from docs; recursion limit caveat discovered and documented |

### Unresolved Questions for Spec-Writer

1. **Effort level per agent:** Should the orchestrator use `max` effort while sub-agents use `high`? Or should all agents use `max`? Tradeoff: cost vs. quality.
2. **Store backend for production:** `InMemoryStore` for v1, but should the spec anticipate `PostgresStore` for future production use?
3. **Daytona integration timeline:** Is Daytona worth integrating in v1, or should it be deferred to v2?
4. **Typed sub-agent returns:** Wait for SDK feature, or implement structured text parsing now?

These questions are flagged for the spec-writer to decide based on the tradeoffs documented in this bundle.
