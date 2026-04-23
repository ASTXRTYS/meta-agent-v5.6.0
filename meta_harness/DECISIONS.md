# Closed AD Decisions

> Extracted from `AD.md` decision index. These decisions are frozen — they will not be reopened. For active (open) questions, see the Open Questions section in `AD.md`.

## Decision Index


| Decision                                                                        | Theme                          | Summary                                                                                                                                                                                                                                                                                                                                                                              | Details               |
| ------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| [Q1: Repo structure naming](#decision-q1)                                       | Architecture Foundations       | Standardize the repo layout around the PCG entrypoint, peer-role modules, and the sandbox integration shape so the codebase matches the runtime contract.                                                                                                                                                                                                                            | [Jump](#decision-q1)  |
| [Q2: Production checkpointer and store backend](#decision-q2)                   | Architecture Foundations       | Use different persistence paths for local dev, shipped CLI, and platform-managed deployment so runtime state lands in the right backend without branching the graph factory.                                                                                                                                                                                                         | [Jump](#decision-q2)  |
| [Q3: Handoff wrapper implementation](#decision-q3)                              | Architecture Foundations       | Make handoffs explicit tools that bubble to the parent graph with `Command.PARENT`, keeping orchestration in the graph rather than in middleware.                                                                                                                                                                                                                                    | [Jump](#decision-q3)  |
| [Q4: PCG node set (first version)](#decision-q4)                                | Architecture Foundations       | **[Superseded 2026-04-22 by `OQ-HO`]** Originally: keep the coordination graph linear and small so routing stays easy to reason about while handoff tools and middleware own the real branching behavior. Current: 1-node dispatcher (`dispatch_handoff`) routing among mounted role subgraphs.                                                                                      | [Jump](#decision-q4)  |
| [Q5: Handoff tool use-case matrix](#decision-q5)                                | Agent Roles & Communication    | Define a verb-driven handoff matrix so every role knows when to deliver, return, consult, or question without inventing new routing semantics.                                                                                                                                                                                                                                       | [Jump](#decision-q5)  |
| [Q6: Handoff record schema](#decision-q6)                                       | Agent Roles & Communication    | Lock the handoff record to a compact field set and reserve `accepted` for later acceptance stamps so audit data stays stable.                                                                                                                                                                                                                                                        | [Jump](#decision-q6)  |
| [Q7: Phase gate enum and approval policy](#decision-q7)                         | Agent Roles & Communication    | Use six lifecycle phases with only two explicit approval gates, and keep approval as a PM-owned document review rather than a graph interrupt.                                                                                                                                                                                                                                       | [Jump](#decision-q7)  |
| [Q8: Sandbox topology impact](#decision-q8)                                     | Middleware Systems             | Treat sandboxing as an execution-mode concern for mounted role agents, not as a separate assistant topology.                                                                                                                                                                                                                                                                         | [Jump](#decision-q8)  |
| [Q9: HE vs Evaluator gate-owner boundary](#decision-q9)                         | Middleware Systems             | Split harness-science authority from application-quality authority so HE and Evaluator gate different dimensions of the workflow.                                                                                                                                                                                                                                                    | [Jump](#decision-q9)  |
| [Q10: PCG state growth and parent-to-child context propagation](#decision-q10)  | Tool & Contract Specifications | **[Superseded 2026-04-22 by `OQ-HO`]** Originally: bound what parent state reaches child graphs and cap handoff history so persistence stays manageable without flooding child context. Current: child isolation is structural via mounted Deep Agent subgraphs' declared schemas plus terminal-exit discipline; gate dispatch reads `acceptance_stamps` channel, not `handoff_log`. | [Jump](#decision-q10) |
| [Q11: PCG state schema and initialization topology (refined)](#decision-q11)    | Tool & Contract Specifications | **[Superseded 2026-04-22 by `OQ-HO`]** Originally: narrow user-facing PCG state surface + deterministic child input construction. Current: 1-node dispatcher, typed `operator.add` reducer on `handoff_log`, first-class `acceptance_stamps` channel, `pending_handoff` removed, Store-backed `artifact_manifest` / `optimization_trendline` / `projects_registry`.                  | [Jump](#decision-q11) |
| [Q12: Universal agent middleware baseline](#decision-q12)                       | Middleware Systems             | Give every agent the same baseline stack and vary only parameter values so the harness stays consistent across roles.                                                                                                                                                                                                                                                                | [Jump](#decision-q12) |
| [Q13: Anthropic provider-specific middleware integration](#decision-q13)        | Provider Integrations          | Add Anthropic-native bash, memory, and server-side tools through provider profiles so Anthropic gets native affordances without polluting shared factories.                                                                                                                                                                                                                          | [Jump](#decision-q13) |
| [Q14: User interface surface](#decision-q14)                                    | Product Surface & Runtime      | Ship a Textual TUI that surfaces pipeline state, approvals, and model selection without turning the UI into the primary runtime.                                                                                                                                                                                                                                                     | [Jump](#decision-q14) |
| [Q15: Headless PM session, thread identity, and source surfaces](#decision-q15) | Product Surface & Runtime      | Separate PM-session threads from project threads so headless ingress, source presence, and execution identity stay distinct.                                                                                                                                                                                                                                                         | [Jump](#decision-q15) |
| [Q16: Project-scoped execution environment / agent computer](#decision-q16)     | Product Surface & Runtime      | Bind each project thread to a real execution environment so coding, evaluation, and publication happen inside the project computer.                                                                                                                                                                                                                                                  | [Jump](#decision-q16) |
| [Q17: Concrete handoff tool definition spec](#decision-q17)                     | Tool & Contract Specifications | Concrete handoff tool definitions are specified before implementation/code generation and are not delegated to the Developer or codegen pass. The implementation spec locks the model-visible API for all 23 handoff tools plus PM's terminal `finish_to_user` tool.                                                                                       | [Jump](#decision-q17) |


---

## 🚩 Flagged Items Requiring Droid Attention

The following items are **high-urgency** and must be scoped into the current droid implementation plan. These represent course corrections or clarifications to prior decisions:


| Flag          | Question                                                                                                                                     | Location | Status                                              |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------- |
| 🚩 **URGENT** | Anthropic server-side tools (web_search, web_fetch, code_execution, tool_search) — previously deferred to v2, now **required for v1 launch** | Q13 §(5) | **REVISED 2026-04-15** — See updated decision below |


---

## Architecture Foundations

### Q1: Repo structure naming

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-11

Adopt the section 4 repo-structure naming decision that uses root `graph.py` for the LangGraph Project Coordination Graph entrypoint, uses `agents/` for peer role modules, reserves `task_agents/` only for future role-owned ephemeral SDK `SubAgent` helpers, uses `developer/` as the canonical Developer module name, and follows the Deep Agents CLI `integrations/` sandbox convention.

---

### Q2: Production checkpointer and store backend

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Three runtime modes, two code paths. (1) **Local dev** (`langgraph dev`): `SqliteSaver` checkpointer and managed store are auto-injected by the dev server — factory passes neither. (2) **CLI TUI shipped to end users**: `SqliteSaver` (from `langgraph-checkpoint-sqlite`) at a user-local path (e.g. `~/.metaharness/state.db`) explicitly passed to the Project Coordination Graph factory; `InMemoryStore()` for store (no `StoreBackend` needed — `FilesystemBackend` owns disk persistence). (3) **Web app / LangGraph Platform**: managed Postgres-backed checkpointer and store are auto-injected by the platform — factory passes neither. `StoreBackend()` with no args resolves from the LangGraph execution context via `get_store()` in all platform-managed modes. `langgraph-checkpoint-sqlite` is a required production dependency.

---

### Q3: Handoff wrapper implementation

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

v1 handoffs are explicit Deep Agent tools that return `Command(graph=Command.PARENT, goto=<coordination_node>, update=<handoff_payload>)`; Project Coordination Graph nodes record and route the handoff; custom handoff middleware is out of v1.

---

### Q4: PCG node set (first version)

**Status:** Superseded 2026-04-22 by `OQ-HO` resolution · **Originally approved by:** Jason · **Date:** 2026-04-12

> **Supersession note.** Node count collapsed from 3 (`receive_user_input`, `process_handoff`, `run_agent`) → 2 (`process_handoff`, `run_agent` via Q11) → a 1-node coordinator (`dispatch_handoff`) plus 7 mounted role Deep Agent subgraph nodes. The dispatcher emits `Command(goto=<target_agent>)`; role handoff tools emit `Command(graph=PARENT, goto="dispatch_handoff", update={...})`, which bubbles through Pregel's namespace hierarchy natively. The `pending_handoff` cursor is eliminated; `handoff_log[-1]` is authoritative. See `AD.md §4 LangGraph Project Coordination Graph` (current) and `docs/specs/pcg-data-contracts.md` (current).

> **Original decision (preserved for historical context):** Keep the coordination graph intentionally small and let handoff tools plus middleware own the real orchestration. This preserves a clean runtime boundary and keeps routing behavior easy to audit.

> Three nodes (`receive_user_input`, `process_handoff`, `run_agent`), no conditional edges, linear topology. Phase gates moved to middleware hooks on handoff tools. Routing intelligence owned by calling agents via tool selection. Removed `record_handoff` and `ensure_role_state` as separate nodes (merged into `process_handoff`). Removed `route_after_agent`, `gate_phase`, and `surface_question` (routing is agent-driven, gates are middleware, HITL is SDK `ask_user`).

---

## Agent Roles & Communication

### Q5: Handoff tool use-case matrix

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

19 tools across 5 categories (Pipeline Delivery, Pipeline Return, Stage Review, Phase Review, Specialist Consultation). Naming convention `<verb>_<artifact>_to_<role>` — verb encodes blocking semantics. PM is the pipeline hub: specialists return to PM, PM delivers to next specialist. Direct specialist-to-specialist interactions for stage reviews and consultations. `reason` enum changed from phase-based (`scope_handoff|eval_request|...`) to verb-based (`deliver|return|submit|consult|coordinate|question`) — middleware dispatches on `(source, target, reason)` triple. Agent-scoped tool ownership: each agent only receives relevant tools. Artifact paths are references, not copies.

---

### Q6: Handoff record schema

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Locked field set is `project_id`, `handoff_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`, `langsmith_run_id`, `status`, `created_at`. Removed `project_thread_id` (redundant with `project_id`), `target_role_namespace` (derivable from `target_agent` in v1), and `question` (folded into `reason`). Renamed `artifact_refs` → `artifact_paths` and `run_id` → `langsmith_run_id` for clarity. Added `brief` (was in Handoff Protocol but missing from schema).

**Amendment (2026-04-20, Q15):** `project_thread_id` is now canonical runtime identity for project execution and is not globally redundant with `project_id`. Local/dev may set `project_thread_id = project_id` by convention only. Handoff/project contracts may include both identities where runtime correlation requires it.

---

### Q7: Phase gate enum and approval policy

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

> **Decision Summary:** Only two lifecycle transitions need explicit approval, and that approval belongs to the PM as a document-review step rather than as a graph interrupt. Everything else auto-advances.

Six phases (`scoping`, `research`, `architecture`, `planning`, `development`, `acceptance`). Two transitions require explicit user approval: `scoping→research` (PRD + eval suite review) and `architecture→planning` (design spec review). All others auto-advance. Approval mechanism is a PM-owned tool that presents stakeholder-friendly document packages to the user — prompt-driven, not a PCG interrupt. Autonomous mode toggle auto-advances all gates. Exact tool schema and document rendering delegated to implementation spec.

---

## Middleware Systems

### Q8: Sandbox topology impact

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

> **Decision Summary:** Sandbox support changes how role agents execute, not how the project is modeled. Keep the topology mounted; do not split roles into separate assistants. See [Q16](#q16-project-scoped-execution-environment-agent-computer) for the execution-environment invariant.

Sandbox support is backend/runtime configuration for mounted role agents and does not split roles into separate top-level assistants. Separate remotely deployed role assistants are out of scope for v1.

**Amendment (2026-04-20, Q16):** Sandbox semantics are now anchored to a project-scoped execution environment invariant: `project_thread_id -> execution_environment_id -> provider root`. This clarifies topology stays mounted while execution environment remains a first-class project contract.

---

### Q9: HE vs Evaluator gate-owner boundary

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

> **Decision Summary:** HE owns harness science and Evaluator owns application quality. The two roles gate different dimensions so the workflow has a clear technical boundary.

AD owns the boundary definition (which dimension each role gates), Developer system prompt owns the routing (which tool to call when). HE gates target *harness* quality (eval science, trajectory, rubrics); Evaluator gates target *application* quality (code, SDK conventions, UI/UX). HE is conditional — only gates when a target harness exists.

---

### Tool & Contract Specifications

### Q10: PCG state growth and parent-to-child context propagation

**Status:** Superseded 2026-04-22 by `OQ-HO` resolution · **Originally approved by:** Jason · **Date:** 2026-04-12

> **Supersession note.** Child isolation is now **structural** via mounted Deep Agent subgraphs' declared `_InputAgentState` / `_OutputAgentState` schemas, which LangGraph respects automatically on `add_node(role_name, role_graph)`. Output isolation is enforced by terminal-exit discipline: every role turn ends with `Command(graph=PARENT, ...)`, so child conversation history does not merge into parent `messages`. Gate dispatch no longer scans `handoff_log`; acceptance stamps live on a first-class `acceptance_stamps` channel. Handoff-log cap is deferred to implementation (v1: bounded via `operator.add` with implementation cap; v2: migrate to `Store`). See `AD.md §4 LangGraph Project Coordination Graph` (current).

> **Original decision (preserved for historical context):** Parent state does not flow wholesale into children. Keep child inputs narrow, keep handoff history bounded, and treat growth as a persistence problem rather than a context-flooding problem.

> Child agents do not see PCG state — LangGraph maps parent-to-child by shared key names only, and the Deep Agent input schema (`_InputAgentState`) only shares `messages` with the PCG. The `run_agent` node controls what enters the child's `messages`. Unbounded growth is a persistence concern (checkpoint bloat), not a context-flooding concern. v1 mandates a cap on the handoff log (last N records, older summarized into `handoff_summary`). v2 option: move full history to LangGraph `Store`. Child agent message compaction is handled by `SummarizationMiddleware` (already in every agent stack).

---

### Q11: PCG state schema and initialization topology (refined)

**Status:** Superseded 2026-04-22 by `OQ-HO` resolution · **Originally approved by:** Jason · **Date:** 2026-04-12

> **Supersession note.** Four substantive problems with the original decision, verified against local SDK source:
>
> 1. `**add_messages` reducer on `handoff_log` is structurally broken.** `add_messages` coerces both inputs through `convert_to_messages` (`.venv/lib/python3.11/site-packages/langgraph/graph/message.py:194-201`), which raises `NotImplementedError` for non-message types (`.venv/lib/python3.11/site-packages/langchain_core/messages/utils.py:727-730`). A `HandoffRecord` dataclass / `TypedDict` / Pydantic model with an `id` field does not satisfy `MessageLikeRepresentation`. `handoff_log` now uses a typed `operator.add` append reducer.
> 2. `**pending_handoff` cursor does not pay rent.** With the 1-node dispatcher topology (superseding Q4), `handoff_log[-1]` is the authoritative active handoff. The cursor was an artifact of the two-node split.
> 3. `**messages` lifecycle-bookend invariant is too restrictive for headless ingress.** The `messages` channel now documents as the user-facing I/O conduit (LangGraph convention), written only by the PM's `finish_to_user` terminal tool. Child agents still never see it (now enforced structurally via mounted subgraphs' declared schemas plus `Command.PARENT` exit discipline).
> 4. **Acceptance-stamp gate scans `handoff_log`.** Couples gate logic to audit log structure. Acceptance stamps now live on a first-class `acceptance_stamps` channel keyed by stamp type (`application` / `harness`). Gates read the channel.
>
> Folded in during the rewrite: `OQ-H1` (PM-session project visibility) via a `projects_registry` `Store` namespace; `OQ-H3` (Developer-blind optimization trendline) via an HE-owned `optimization_trendline` `Store` namespace. See `AD.md §4 LangGraph Project Coordination Graph` (current), `docs/specs/pcg-data-contracts.md` (current), and `local-docs/pcg-state-schema-rewrite-working.md` (working analysis, temporary).

> **Original decision (preserved for historical context):** The PCG owns a narrow, user-facing state surface and the child graph only receives a single constructed `HumanMessage`. This keeps routing deterministic and prevents accidental state leakage.

> (1) **Topology reduced from 3 to 2 nodes** — merged `receive_user_input` into `process_handoff`; `process_handoff` handles both first invocation (no pending handoff → create synthetic handoff for PM) and subsequent invocations. (2) `**messages` redefined as user-facing I/O channel** — accumulates only lifecycle bookends (stakeholder input in, PM's final product response out); never written to during pipeline execution. (3) `**handoff_summary` removed** — cap mitigation is implementation spec territory, not a state key. (4) `**run_agent` constructs child input** — always builds a single `HumanMessage` from `pending_handoff.brief`; child never sees raw PCG `messages` list. (5) `**Command.PARENT` update contract locked** — handoff tools write to `handoff_log`, `current_agent`, `current_phase` (conditional), `pending_handoff`; never write to `messages`. (6) **Acceptance gate pattern** — `return_product_to_pm` gated by `submit_application_acceptance` (Evaluator, always required) and `submit_harness_acceptance` (HE, conditional on HE participation derived from `handoff_log`). (7) **Graph lifecycle is PM-controlled** — PM uses `ask_user` to confirm satisfaction; finishes normally → END. Three new tools added: `return_product_to_pm`, `submit_harness_acceptance`, `submit_application_acceptance`. Total tools: 23 across 6 categories.

---

### Q11: Model selection per agent (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

(1) **Model-agnostic architecture** — no provider lock-in. The harness must support any model provider (Anthropic, OpenAI, GLM, etc.). Users choose models per agent role; the system cannot assume a single provider. (2) **Per-agent model selection** — each of the 7 agent roles can use a different model. Selection is configurable, not hardcoded. (3) **Thread-scoped model config** — model selections are made at project start and remain immutable for the lifespan of that project/thread. Changing models requires starting a new project. (4) **Model-specific server-side tools** — when a particular model is selected for an agent, that agent must receive any provider-specific tools and capabilities the model supports (e.g., Anthropic prompt caching, OpenAI Codex subagent delegation, GPT 5.4 Pro extended thinking). The implementation spec owns how to route provider-specific tool injection based on the selected model. (5) **v1 experimental defaults** (subject to change based on deployment-level experimentation):

- PM: Opus 4.6
- Researcher: Opus 4.6
- Architect: TBD — experiment between Opus 4.6, GPT 5.4 (extra-high thinking), GPT 5.4 Pro
- Planner: Opus 4.6
- Harness Engineer: TBD — likely GPT 5.4 Pro
- Evaluator: Opus 4.6
- Developer: TBD — experiment between Opus 4.6 (strong server-side tools), GPT 5.4 extra-high thinking + Codex worker subagents, GPT 5.4 Pro

(6) **Model routing implementation** — delegated to design spec. The AD locks the architectural constraints (model-agnostic, per-agent, thread-scoped, provider-specific tool injection); the spec owns the implementation of model routing, provider adapter patterns, and how `create_deep_agent(model=...)` resolves at runtime based on project config.

---

### Q12: Universal agent middleware baseline

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

> **Decision Summary:** Every agent starts from the same baseline stack. Differences are parameter values and role-specific middleware, not separate runtime shapes.

The universal baseline is identical for all 7 agents. Every agent receives the same `create_deep_agent()` call shape with all conditional params activated — per-agent variation is in the *values*, not in *presence*.

**Universal `create_deep_agent()` call shape:**

```python
create_deep_agent(
    model=<per Q11>,
    backend=<per deployment mode>,
    checkpointer=<project-scoped>,
    store=<if StoreBackend used>,
    system_prompt=<per Q12 (behavioral contracts)>,
    tools=<handoff tools + role tools>,
    middleware=[
        CollapseMiddleware(...),             # free: collapse consecutive read/search groups
        ContextEditingMiddleware(...),       # free: clear stale tool results at token threshold
        SummarizationToolMiddleware(...),    # on-demand compact_conversation
        ModelCallLimitMiddleware(...),       # hard ceiling on model API calls (cost control)
        StagnationGuardMiddleware(...),      # progress-aware call limiter (nudge → hard stop)
        <phase gate middleware>,              # per-agent, TBD
        ShellAllowListMiddleware(...),       # conditional on sandbox mode
    ],
    skills=[<role skills path>],
    memory=[<role AGENTS.md path>],
    interrupt_on={},                         # baked in, inert — future-proofing
    permissions=[<role filesystem rules>],
    subagents=[<role subagent specs>],
    name=<role identifier>,
)
```

**Effective middleware stack (same for all 7, values differ):**

```
Base:     TodoList → Skills → Filesystem → SubAgent → Summarization → PatchToolCalls
User:     [middleware param — custom per role]
Tail:     [Profile extras] → [ToolExclusion] → PromptCaching → Memory → HITL → Permissions
```

**Custom middleware in the `middleware=` slot:**


| Middleware                    | What it adds                                                            | All 7?        | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------- | ----------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CollapseMiddleware`          | Collapses consecutive read/search tool-call groups into badge summaries | Yes           | Free (no LLM call). Reduces context before summarization triggers — benchmarks show 4.2x later triggering when paired with `SummarizationMiddleware`. **Do not reimplement.** Install: `pip install langchain-collapse`. Source: [github.com/johanity/langchain-collapse](https://github.com/johanity/langchain-collapse). Listed on [LangChain middleware integrations](https://docs.langchain.com/oss/python/integrations/middleware) as a community integration. |
| `ContextEditingMiddleware`    | Clears old tool results → `[cleared]` when token threshold exceeded     | Yes           | Free (no LLM call). Mirrors Anthropic's `clear_tool_uses` behavior. **Do not reimplement.** SDK built-in: `from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit`. Pluggable `ContextEdit` strategies — default is `ClearToolUsesEdit`. Docs: [langchain.com/middleware/built-in#context-editing](https://docs.langchain.com/oss/python/langchain/middleware/built-in#context-editing).                                               |
| `SummarizationToolMiddleware` | `compact_conversation` tool (on-demand)                                 | Yes           | SDK provides `SummarizationMiddleware` (auto-truncation) as unconditional baseline; this adds the proactive tool. Created via `create_summarization_tool_middleware(model, backend)`.                                                                                                                                                                                                                                                                               |
| `ModelCallLimitMiddleware`    | Hard ceiling on model API calls per thread                              | Yes           | SDK built-in (`langchain.agents.middleware.model_call_limit`). Not included in `create_deep_agent()` by default — must be added explicitly. Counts model API calls (the cost-accruing unit), not graph steps. `exit_behavior="end"` (graceful termination). Per-role `thread_limit` values below. `run_limit` left `None` — single-run ceiling unnecessary with reasonable thread limit.                                                                            |
| `StagnationGuardMiddleware`   | Progress-aware call limiter (two-tier: nudge → hard stop)               | Yes           | Custom middleware — see design vision below. Per-role thresholds.                                                                                                                                                                                                                                                                                                                                                                                                   |
| `AskUserMiddleware`           | `ask_user` tool (proactive stakeholder questions)                       | PM, Architect | PM for stakeholder questions; Architect for interactive spec creation when user toggles the feature. Other agents do not get this.                                                                                                                                                                                                                                                                                                                                  |
| `ShellAllowListMiddleware`    | Shell command validation against allow-list                             | Conditional   | Active for sandbox-backed agents. Inert for local-first.                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase gate middleware         | Handoff tool gate hooks                                                 | Per-agent     | Agents that own gated tools receive phase gate middleware. Specifics TBD in Q8 (extended middleware).                                                                                                                                                                                                                                                                                                                                                               |
| `interrupt_on={}`             | `HumanInTheLoopMiddleware` in tail stack                                | Yes           | Passed as empty dict to all 7 agents — activates the middleware but registers zero interrupt rules. Inert until a future need arises. Cost is negligible (short-circuit on empty config).                                                                                                                                                                                                                                                                           |


#### Context management strategy — layered pipeline

The effective context management stack is a layered pipeline where each layer reduces context pressure before the next, more expensive layer fires:

```
Layer 0 (free, every turn):   CollapseMiddleware      — groups consecutive reads into badge summaries
Layer 1 (free, every turn):   ContextEditingMiddleware — clears old tool results at token threshold
Layer 2 (1 LLM call, at threshold): SummarizationMiddleware (SDK built-in, unconditional) — generic conversation summary
Layer 3 (on-demand):          SummarizationToolMiddleware — agent-initiated compact_conversation
```

Layers 0–1 are free (string operations, no LLM calls). They delay when Layer 2 fires by keeping context lean. Layer 2 is the SDK's built-in auto-summarization — it cannot be disabled without patching `create_deep_agent()`. Layer 3 gives the agent proactive control.

**Why not replace `SummarizationMiddleware` with `CompactionMiddleware` (compact-middleware)?** `CompactionMiddleware` is a strict superset of `SummarizationMiddleware` — 9-section structured summary, hybrid token counting, post-compaction file/plan restoration, circuit breaker, partial compaction. However, `SummarizationMiddleware` is hardcoded into `create_deep_agent()` at `graph.py:560` with no disable flag. Replacing it requires either (a) patching the SDK (contribute a `disable_summarization` param upstream) or (b) stacking both (wasteful — two LLM summarization layers). v1 uses the unmodified SDK with free pre-summarization optimizers (Collapse + ContextEditing) to delay when the built-in summarization fires. v2 will pursue the SDK contribution path to replace `SummarizationMiddleware` with `CompactionMiddleware`.

**Stack ordering rationale.** `CollapseMiddleware` runs first because it reduces message count (groups consecutive reads), which reduces the input that `ContextEditingMiddleware` scans. Both run before `SummarizationToolMiddleware` so that on-demand compaction also benefits from the free layers. The SDK's built-in `SummarizationMiddleware` sits in the base stack (before user middleware), so it fires before all of these — the free layers reduce how often it needs to fire.

#### `ModelCallLimitMiddleware` — Per-role thread limits

`recursion_limit` (graph steps) is NOT a cost control — the SDK sets it to 9,999 (effectively unlimited). `ModelCallLimitMiddleware` counts model API calls directly, which is the cost-accruing unit. One model call = one count. A single model call + tool execution = 2–3 graph steps, so `recursion_limit=100` ≈ only 30–50 model calls — which caused issues in v0.5.


| Agent      | `thread_limit` | Rationale                                              |
| ---------- | -------------- | ------------------------------------------------------ |
| PM         | 150            | Decisive, few calls — mostly stakeholder interaction   |
| Researcher | 300            | Deep research = many read/search calls                 |
| Architect  | 250            | Design iteration, spec writing                         |
| Planner    | 200            | Structured planning, bounded                           |
| Developer  | 500            | Longest — edit/test/fix cycles, subagent orchestration |
| HE         | 300            | Eval design is exploratory, many tool calls            |
| Evaluator  | 200            | Methodical but bounded                                 |


`run_limit` is `None` for all agents — a single run shouldn't need a separate ceiling when the thread limit is reasonable. `exit_behavior="end"` — graceful termination with an `AIMessage` explaining the limit was reached, matching `StagnationGuardMiddleware`'s hard stop behavior.

**Composability with `StagnationGuardMiddleware`.** `ModelCallLimitMiddleware` is a hard ceiling (fires regardless of progress). `StagnationGuardMiddleware` is progress-aware (fires when the agent is spinning). They compose: StagnationGuard nudges or stops a spinning agent well before the ceiling; ModelCallLimit catches the legitimate-but-expensive case where the agent is making real progress but has consumed too many calls. Neither subsumes the other.

#### `StagnationGuardMiddleware` — Design Vision

**Problem.** An agent can make successful model calls — hitting the API, receiving responses, executing tools — while making zero real progress. The model never errors; the API never rate-limits; the agent just spins. `ModelCallLimitMiddleware` provides a hard stop, but it cannot distinguish deep thinking from spinning. `recursion_limit` counts graph steps, not cost-accruing model calls. Neither detects *stagnation* — the agent is running, not stuck, but running in place.

**Rationale.** Cost guardrails for long-running agents must be progress-aware. A hard call limit terminates an agent that is 90% through a complex task because it hit an arbitrary ceiling. A progress-unaware limit is a blunt instrument. The guard must answer: *is the agent still moving forward, or has it stopped producing value while continuing to consume resources?*

**Core insight — the nudge is free.** Instead of calling an external reviewer LLM (which costs money and adds latency), inject a `SystemMessage` into the agent's state. The next model call — which was already going to happen — sees the nudge and self-reflects. Zero additional model calls. The agent leverages its own intelligence to self-correct, at zero marginal cost.

**Two-tier mechanism:**

- **Tier 1 — Nudge (at `check_interval` boundary):** `before_model` collects progress signals from pluggable signal providers. If any signal indicates stagnation, inject a `SystemMessage` prompting the agent to self-assess. The agent's next model call sees this and (usually) self-corrects — completes a todo, writes a file, or concludes its work.
- **Tier 2 — Hard stop (after `grace_after_nudge` additional calls):** If the agent continues past the nudge and the signals still show stagnation, `before_model` returns `{"jump_to": "end"}` with an `AIMessage` explaining the termination. No second chances — the deterministic signals don't lie, even if the agent *thinks* it's making progress.

**Signal providers — the pluggable progress abstraction:**

The middleware does not hardcode what "progress" means. It accepts a list of `ProgressSignal` providers, each of which reads from agent state and returns a `SignalVerdict`:

```python
class ProgressSignal(ABC):
    @abstractmethod
    def assess(self, state: AgentState) -> SignalVerdict:
        """Assess whether the agent is making progress based on state."""

@dataclass
class SignalVerdict:
    progressing: bool    # True = making progress, False = stagnant
    confidence: float    # 0.0–1.0, for weighted aggregation
    detail: str           # Human-readable explanation (used in nudge message)
```

**Built-in signal providers (general-purpose, model-agnostic):**


| Provider                   | Signal source                                 | What it detects                                                                  | Works without                                                                           |
| -------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `TodoProgressSignal`       | `todos` state key (from `TodoListMiddleware`) | Todos not being completed or advancing                                           | If `todos` absent → always returns `progressing=True` (no signal = no stagnation claim) |
| `ArtifactProductionSignal` | `messages` (tool call history)                | No file writes or artifact-producing tool calls in recent window                 | If no write-like tools → always returns `progressing=True`                              |
| `ToolCallDiversitySignal`  | `messages` (consecutive tool calls)           | Same tool called with similar args repeatedly (edit→read→edit→read on same file) | Always available — reads from `messages` which every agent has                          |


**Graceful absence.** If a signal provider's state key is missing (e.g., no `todos` because `TodoListMiddleware` isn't in the stack), the provider returns `progressing=True` with `confidence=0.0`. It contributes no signal rather than a false stagnation claim. This makes the middleware safe for any agent configuration — it degrades gracefully.

**Constructor signature (follows SDK conventions):**

```python
class StagnationGuardMiddleware(AgentMiddleware):
    def __init__(
        self,
        *,
        check_interval: int = 25,        # check every N model calls
        grace_after_nudge: int = 10,      # hard stop after N more calls post-nudge
        signals: list[ProgressSignal] | None = None,  # None = use built-in defaults
        nudge_template: str | None = None,  # custom nudge message; None = default
        exit_behavior: Literal["end", "error"] = "end",  # matches ModelCallLimitMiddleware
    ): ...
```

**Why this is generalizable for LangChain:**

1. **Model-agnostic.** No model-specific APIs, no provider assumptions. Reads from `AgentState` — a dict of strings, lists, and dicts. Works with Anthropic, OpenAI, GLM, any provider.
2. **Middleware-agnostic.** Gracefully handles missing state keys. Works with or without `TodoListMiddleware`, `FilesystemMiddleware`, or any other middleware in the stack.
3. **Domain-agnostic.** Built-in signals cover the common case (todos, file writes, tool repetition). Domain-specific users implement `ProgressSignal` for their state (e.g., "no database rows inserted," "no API calls made," "no test results produced").
4. **Zero additional cost.** The nudge rides on the next model call. No external reviewer, no LangSmith SDK calls during inference, no secondary model invocation.
5. **Composable with `ModelCallLimitMiddleware`.** `StagnationGuardMiddleware` is progress-aware; `ModelCallLimitMiddleware` is a hard ceiling. They serve different purposes and can coexist in the same stack. `StagnationGuard` fires at intervals; `ModelCallLimit` fires at a ceiling.
6. **Follows SDK naming and parameter conventions.** `exit_behavior` matches `ModelCallLimitMiddleware`. `check_interval` follows the interval pattern. `signals` follows the pluggable-provider pattern used by `ContextEditingMiddleware` edits.

**Per-role thresholds for Meta Harness (implementation spec owns exact values):**


| Agent      | `check_interval` (estimated) | Rationale                                              |
| ---------- | ---------------------------- | ------------------------------------------------------ |
| PM         | 20                           | Shorter leash — PM should be decisive, not exploratory |
| Researcher | 40                           | Longer — deep research involves many read calls        |
| Architect  | 35                           | Design thinking is iterative                           |
| Planner    | 30                           | Planning is structured but not endless                 |
| Developer  | 50                           | Longest — coding involves many edit/test cycles        |
| HE         | 40                           | Eval design is exploratory                             |
| Evaluator  | 30                           | Evaluation is methodical but bounded                   |


**State schema extension:**

```python
class StagnationGuardState(AgentState):
    _model_call_count: Annotated[NotRequired[int], PrivateStateAttr]
    _nudge_issued_at: Annotated[NotRequired[int | None], PrivateStateAttr]
    _last_progress_check: Annotated[NotRequired[dict[str, SignalVerdict] | None], PrivateStateAttr]
```

Private state attrs — not passed to the model, not visible to other middleware, but checkpointed for cross-invocation persistence.

**Implementation status.** The above is a reference prototype and design vision — not a completed implementation. The AD locks the architectural intent (two-tier nudge→stop, pluggable signals, graceful absence, per-role thresholds). The implementation spec and development team must: complete the full middleware file with all method bodies (`before_model`, `after_model`, signal provider implementations, nudge message templates); validate that the `ProgressSignal.assess()` contract works correctly against real `AgentState` shapes from `create_deep_agent()`; test the middleware in isolation and in composition with the full baseline stack; and verify that graceful absence behaves correctly when optional state keys (`todos`, write-like tools) are missing. The design vision is the contract; the implementation must prove it works.

**Deferred to v2 (requires SDK modification):**


| Middleware                                  | Why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CompactionMiddleware` (compact-middleware) | Strict superset of `SummarizationMiddleware` — 9-section structured summary, hybrid token counting, post-compaction restoration, circuit breaker, partial compaction. Cannot replace `SummarizationMiddleware` without a `disable_summarization` flag in `create_deep_agent()`. v1 uses free pre-summarization optimizers (Collapse + ContextEditing) instead. v2 will contribute the disable flag upstream and switch. **Do not reimplement.** Install: `pip install compact-middleware`. Source: [github.com/emanueleielo/compact-middleware](https://github.com/emanueleielo/compact-middleware). Listed on [LangChain middleware integrations](https://docs.langchain.com/oss/python/integrations/middleware) as a community integration. |


**Explicitly excluded from v1:**


| CLI Middleware                | Why excluded                                                                                                                                                                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TokenStateMiddleware`        | Schema-only middleware that registers `_context_tokens` for CLI status bar. Nothing writes to it in our topology. Token counts are available in LangSmith traces.                                                       |
| `ConfigurableModelMiddleware` | Enables mid-conversation model swapping. Q11 locked thread-scoped model config — model selections are immutable for the project/thread lifespan. This middleware exists to enable the behavior we explicitly ruled out. |
| `LocalContextMiddleware`      | Injects git info and directory tree into CLI context. Mounted child graphs receive context via handoff briefs, not local context scanning.                                                                              |


**Backend is not middleware.** The `backend=` param is a separate top-level concern — it determines where files live and whether shell execution works. Middleware *consumes* the backend (e.g., `FilesystemMiddleware(backend=backend)`) but the backend itself is the I/O substrate. The AD already locks dual-modality backend semantics (local-first or sandbox) at §568–571.

**Q8 scope narrowed.** The baseline is now closed. Q8 continues as "extended middleware per agent" — deciding what additional custom middleware each agent requires beyond this universal baseline (e.g., which agents get phase gate middleware, which gate logic each agent enforces).

---

### Q8: Extended middleware per agent (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

The universal baseline (Q12) covers all context management, cost control, and progress-awareness middleware for every agent. Q8 decides what differs by role — specifically, which agents receive phase gate middleware and what it enforces.

**Per-agent `middleware=` slot (complete):**


| Agent      | Universal (5) | + Phase Gate | + AskUser | + ShellAllowList | Total custom |
| ---------- | ------------- | ------------ | --------- | ---------------- | ------------ |
| PM         | ✓             | ✓            | ✓         | sandbox          | 7            |
| Developer  | ✓             | ✓            | —         | sandbox          | 6            |
| Architect  | ✓             | ✓            | ✓         | sandbox          | 7            |
| HE         | ✓             | —            | —         | sandbox          | 5            |
| Researcher | ✓             | —            | —         | sandbox          | 5            |
| Planner    | ✓             | —            | —         | sandbox          | 5            |
| Evaluator  | ✓             | —            | —         | sandbox          | 5            |


Universal 5 = CollapseMiddleware + ContextEditingMiddleware + SummarizationToolMiddleware + ModelCallLimitMiddleware + StagnationGuardMiddleware

**Phase gate middleware — per-agent gate logic (derived from Q9 dispatch table):**


| Agent     | Gated tools owned                               | Gate type                    | What the middleware checks before allowing the tool call                                                               |
| --------- | ----------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| PM        | `deliver_prd_to_harness_engineer` (D1)          | Prerequisite                 | `artifact_paths` non-empty with PRD artifact                                                                           |
| PM        | `deliver_prd_to_researcher` (D2)                | Prerequisite + User Approval | `(HE, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)`                                              |
| PM        | `deliver_design_package_to_architect` (D3)      | Prerequisite                 | `(Researcher, PM, return)` in `handoff_log`                                                                            |
| PM        | `deliver_planning_package_to_planner` (D4)      | Prerequisite + User Approval | `(Architect, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)`                                       |
| PM        | `deliver_development_package_to_developer` (D5) | Prerequisite                 | `(Planner, PM, return)` in `handoff_log`                                                                               |
| PM        | User approval recording                         | Self-referential             | PM runs approval tool → creates `(PM, PM, submit, accepted=true/false)` record                                         |
| Developer | `return_product_to_pm` (R5)                     | Acceptance stamps            | `(Evaluator, PM, submit, accepted=true)` in `handoff_log`; if HE participated → also `(HE, PM, submit, accepted=true)` |
| Developer | `submit_phase_to_evaluator` (P3)                | Prerequisite                 | `(Developer, Evaluator, announce)` with matching `phase` in `handoff_log`; `artifact_paths` non-empty                  |
| Architect | `submit_spec_to_harness_engineer` (S1)          | Prerequisite                 | `artifact_paths` non-empty with spec artifacts                                                                         |


4 agents (HE, Researcher, Planner, Evaluator) own no gated tools and receive no phase gate middleware.

**No additional per-role middleware beyond the above.** The universal baseline handles context management (Collapse + ContextEditing + SummarizationTool), cost control (ModelCallLimit + StagnationGuard), and SDK infrastructure (Skills, Filesystem, SubAgent, Memory, Permissions, HITL, PromptCaching). The only per-role variation is phase gate enforcement (3 agents) and stakeholder interaction (2 agents).

**Per-role parameter values (all other middleware):**


| Agent      | `ModelCallLimitMiddleware.thread_limit` | `StagnationGuardMiddleware.check_interval` |
| ---------- | --------------------------------------- | ------------------------------------------ |
| PM         | 150                                     | 20                                         |
| Developer  | 500                                     | 50                                         |
| Architect  | 250                                     | 35                                         |
| HE         | 300                                     | 40                                         |
| Researcher | 300                                     | 40                                         |
| Planner    | 200                                     | 30                                         |
| Evaluator  | 200                                     | 30                                         |


---

### Q10: Tool schema contracts (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

**(1) Common parameter shape — 2 LLM-facing parameters across all 23 tools:**


| Parameter        | Type        | Required | Default | Source                                          |
| ---------------- | ----------- | -------- | ------- | ----------------------------------------------- |
| `brief`          | `str`       | Yes      | —       | LLM provides: prose summary for receiving agent |
| `artifact_paths` | `list[str]` | No       | `[]`    | LLM provides: filesystem paths to artifacts     |


**Rationale for minimal common shape:** The tool name encodes `source_agent`, `target_agent`, and `reason` (e.g., `deliver_prd_to_harness_engineer` → source=PM, target=HE, reason=deliver). `project_id` is thread-scoped context available at call time, not something the LLM needs to pass. The only decisions the LLM makes are *what to say* (`brief`) and *what to attach* (`artifact_paths`). `artifact_paths` defaults to `[]` because non-blocking tools (`ask_pm`, `announce_`*, `coordinate_qa`) often carry no artifacts. This minimizes per-tool schema variation and keeps tool descriptions focused on *when* to use the tool and *what goes in brief*, not on parameter boilerplate.

**Derived at call time (not LLM parameters):**

- `project_id` — from thread context (root thread_id)
- `source_agent` — from tool ownership (which agent is calling)
- `target_agent` — from tool name suffix (`_to_<role>`)
- `reason` — from tool name verb (`deliver`, `return`, `submit`, `consult`, `announce`, `question`, `coordinate`)

**PCG-filled (by `process_handoff`):** `handoff_id`, `langsmith_run_id`, `status`, `created_at`

**(2) Tools with additional parameters — 6 of 23 require one extra parameter:**

**Acceptance tools** — add `accepted: bool`:


| Tool                            | Additional param | Rationale                                                                                            |
| ------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| `submit_harness_acceptance`     | `accepted: bool` | Gate must distinguish acceptance from rejection; `true` satisfies gate, `false` is audit record only |
| `submit_application_acceptance` | `accepted: bool` | Same                                                                                                 |


**Phase Review tools** — add `phase: str`:


| Tool                                 | Additional param | Rationale                                                       |
| ------------------------------------ | ---------------- | --------------------------------------------------------------- |
| `announce_phase_to_evaluator`        | `phase: str`     | QA agent must match announcement against correct plan phase     |
| `announce_phase_to_harness_engineer` | `phase: str`     | Same                                                            |
| `submit_phase_to_evaluator`          | `phase: str`     | QA agent evaluates deliverables against specific phase criteria |
| `submit_phase_to_harness_engineer`   | `phase: str`     | Same                                                            |


`phase` is a free-form identifier matching a phase in the Planner's implementation plan — not the 6-value PCG phase enum. The Planner defines phase identifiers; Developer and QA agents reference them. This distinction matters: the PCG phase enum (`scoping`, `research`, etc.) tracks project lifecycle; `phase` here tracks implementation plan subsections within the development stage.

**(3) Acceptance stamp contract:**

`submit_harness_acceptance` and `submit_application_acceptance` each take:


| Param            | Type        | Required | Description                                                           |
| ---------------- | ----------- | -------- | --------------------------------------------------------------------- |
| `brief`          | `str`       | Yes      | Reasoning — what was verified, what passed/failed, evidence summary   |
| `artifact_paths` | `list[str]` | No       | Paths to eval results, test outputs, evidence artifacts               |
| `accepted`       | `bool`      | Yes      | `true` = quality verified, `false` = rejected with reasoning in brief |


**HandoffRecord extension:** Acceptance stamps add `accepted: bool | None` to the HandoffRecord (default `None`). Normal handoff records have `accepted=None`; acceptance stamps have `accepted=true` or `accepted=false`. This is a Q10 extension to the Q6 base field set, not a Q6 reopening — Q6 locked the base fields; Q10 defines the acceptance-specific field that the gate logic requires.

**Gate logic for `return_product_to_pm`:** Scan `handoff_log` for records where:

- `(source_agent="evaluator", target_agent="pm", reason="submit", accepted=true)` — always required
- `(source_agent="harness_engineer", target_agent="pm", reason="submit", accepted=true)` — required only if HE participated (derived from `handoff_log` scan per Q11/PCG decision)

A stamp with `accepted=false` is recorded for audit but does **not** satisfy the gate. The absence of a stamp also does not satisfy the gate.

**(4) `return_product_to_pm` contract — common shape only:**

Parameters: `brief` + `artifact_paths` (no additional parameters).

- `brief`: Summary of the completed product — what was built, which phases completed, known limitations
- `artifact_paths`: Paths to finished product artifacts (code, docs, test results, deliverables)

**Rationale:** The acceptance gate is middleware logic, not a tool parameter. The Developer doesn't self-certify acceptance; the middleware checks `handoff_log` for QA stamps. Adding an `accepted` parameter here would let the Developer claim acceptance, which defeats the purpose of independent QA verification.

**(5) Model-specific tool considerations:**

**(5a)** Handoff tool schemas are provider-agnostic. All parameters use standard JSON Schema types (`string`, `boolean`, `array of string`). No `anyOf`, `oneOf`, `$ref`, or recursive schemas. Verified against SDK: `Command` extends `ToolOutputMixin` (tools returning `Command.PARENT` is a first-class SDK pattern), and `Command.update` accepts `dict` natively. All three types (`string`, `boolean`, `array of string`) are supported by Anthropic, OpenAI, and GLM tool-use APIs.

**(5b)** Provider-specific tools are additive. When an agent uses an Anthropic model, the model profile may inject Anthropic server-side tools (prompt caching, `computer_use`). When using OpenAI, Codex subagent delegation may be available. These coexist alongside handoff tools — they do not modify handoff tool schemas. The model profile layer (per Q11) owns provider-specific tool injection.

**(5c)** No model-specific handoff tools in v1. All 23 tools are identical regardless of which model the agent uses. If a future provider capability requires a modified handoff schema, that's a v2 extension requiring an AD amendment.

**(5d)** Tool description sufficiency is a cross-provider constraint. Different models interpret tool descriptions with varying fidelity. The AD locks the constraint: handoff tool descriptions must be explicit enough for *any* supported model to correctly invoke the tool (when to use, what goes in `brief`, what artifacts to reference). Exact description text is spec territory.

**(5e)** Tool count is within provider limits. The most tool-rich agent (Developer: 1 return + 4 phase review + 1 consultation + ~10 SDK baseline + provider-specific ≈ 16–17) is well within Anthropic and OpenAI limits (128 each). No count mitigation needed in v1.

**(6) Summary:**


| Category          | Tools  | Common Only | + `accepted` | + `phase` |
| ----------------- | ------ | ----------- | ------------ | --------- |
| Pipeline Delivery | 5      | 5           | —            | —         |
| Pipeline Return   | 5      | 5           | —            | —         |
| Acceptance        | 2      | —           | 2            | —         |
| Stage Review      | 2      | 2           | —            | —         |
| Phase Review      | 4      | —           | —            | 4         |
| Consultation      | 5      | 5           | —            | —         |
| **Total**         | **23** | **17**      | **2**        | **4**     |


**Decisions delegated to implementation spec:** Exact Pydantic/InputSchema wire types, tool description text, `phase` identifier format (free-form string vs. structured), `accepted=false` rejection feedback flow (does the agent retry? does it return to Developer?), `artifact_paths` path format conventions (absolute vs. relative, namespace prefix).

---

### Q9: Middleware dispatch table (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

**(1) Complete triple enumeration — 29 distinct `(source, target, reason)` triples from 23 tools:**

> **Decision Summary:** Gate logic is derived from the handoff log, not from `current_phase`. See [Q8](#archived-q8-per-agent-middleware) for the per-role middleware split.

**Pipeline Delivery (5 triples):**


| #   | Triple                      | Tool                                       | Gate Type                    |
| --- | --------------------------- | ------------------------------------------ | ---------------------------- |
| D1  | `(PM, HE, deliver)`         | `deliver_prd_to_harness_engineer`          | Prerequisite                 |
| D2  | `(PM, Researcher, deliver)` | `deliver_prd_to_researcher`                | Prerequisite + User Approval |
| D3  | `(PM, Architect, deliver)`  | `deliver_design_package_to_architect`      | Prerequisite                 |
| D4  | `(PM, Planner, deliver)`    | `deliver_planning_package_to_planner`      | Prerequisite + User Approval |
| D5  | `(PM, Developer, deliver)`  | `deliver_development_package_to_developer` | Prerequisite                 |


**Pipeline Return (5 triples):**


| #   | Triple                     | Tool                           | Gate Type                        |
| --- | -------------------------- | ------------------------------ | -------------------------------- |
| R1  | `(HE, PM, return)`         | `return_eval_suite_to_pm`      | Ungated                          |
| R2  | `(Researcher, PM, return)` | `return_research_bundle_to_pm` | Ungated                          |
| R3  | `(Architect, PM, return)`  | `return_design_package_to_pm`  | Ungated                          |
| R4  | `(Planner, PM, return)`    | `return_plan_to_pm`            | Ungated                          |
| R5  | `(Developer, PM, return)`  | `return_product_to_pm`         | Prerequisite (acceptance stamps) |


**Acceptance (2 triples):**


| #   | Triple                    | Tool                            | Gate Type                        |
| --- | ------------------------- | ------------------------------- | -------------------------------- |
| A1  | `(HE, PM, submit)`        | `submit_harness_acceptance`     | Stamp only (no gate on emission) |
| A2  | `(Evaluator, PM, submit)` | `submit_application_acceptance` | Stamp only (no gate on emission) |


**Stage Review (2 triples):**


| #   | Triple                    | Tool                                | Gate Type    |
| --- | ------------------------- | ----------------------------------- | ------------ |
| S1  | `(Architect, HE, submit)` | `submit_spec_to_harness_engineer`   | Prerequisite |
| S2  | `(HE, Architect, return)` | `return_eval_coverage_to_architect` | Ungated      |


**Phase Review (4 triples):**


| #   | Triple                             | Tool                                 | Gate Type    |
| --- | ---------------------------------- | ------------------------------------ | ------------ |
| P1  | `(Developer, Evaluator, announce)` | `announce_phase_to_evaluator`        | Ungated      |
| P2  | `(Developer, HE, announce)`        | `announce_phase_to_harness_engineer` | Ungated      |
| P3  | `(Developer, Evaluator, submit)`   | `submit_phase_to_evaluator`          | Prerequisite |
| P4  | `(Developer, HE, submit)`          | `submit_phase_to_harness_engineer`   | Ungated      |


**Consultation (11 triples):**


| #   | Triple                             | Tool                                | Gate Type |
| --- | ---------------------------------- | ----------------------------------- | --------- |
| C1  | `(Planner, HE, consult)`           | `consult_harness_engineer_on_gates` | Ungated   |
| C2  | `(Planner, Evaluator, consult)`    | `consult_evaluator_on_gates`        | Ungated   |
| C3  | `(Architect, Researcher, consult)` | `request_research_from_researcher`  | Ungated   |
| C4  | `(HE, Researcher, consult)`        | `request_research_from_researcher`  | Ungated   |
| C5  | `(PM, Researcher, consult)`        | `request_research_from_researcher`  | Ungated   |
| C6  | `(HE, PM, question)`               | `ask_pm`                            | Ungated   |
| C7  | `(Researcher, PM, question)`       | `ask_pm`                            | Ungated   |
| C8  | `(Architect, PM, question)`        | `ask_pm`                            | Ungated   |
| C9  | `(Planner, PM, question)`          | `ask_pm`                            | Ungated   |
| C10 | `(Developer, PM, question)`        | `ask_pm`                            | Ungated   |
| C11 | `(Evaluator, PM, question)`        | `ask_pm`                            | Ungated   |
| C12 | `(HE, Evaluator, coordinate)`      | `coordinate_qa`                     | Ungated   |
| C13 | `(Evaluator, HE, coordinate)`      | `coordinate_qa`                     | Ungated   |


**(2) Summary by gate type:**


| Gate Type                        | Count | Triples                      |
| -------------------------------- | ----- | ---------------------------- |
| Ungated (pass-through)           | 19    | R1–R4, S2, P1–P2, P4, C1–C13 |
| Prerequisite only                | 6     | D1, D3, D5, R5, S1, P3       |
| Prerequisite + User Approval     | 2     | D2, D4                       |
| Stamp only (no gate on emission) | 2     | A1, A2                       |


**(3) Prerequisite check details — gate logic derived from `handoff_log`, not `current_phase`:**


| Triple                           | What the gate checks                                                 | `handoff_log` condition                                                                                                      |
| -------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `(PM, HE, deliver)`              | PRD finalized + eval criteria exist                                  | `artifact_paths` non-empty with PRD artifact                                                                                 |
| `(PM, Researcher, deliver)`      | HE Stage 1 complete + user approved scoping→research transition      | `handoff_log` contains `(HE, PM, return)` record AND `(PM, PM, submit, accepted=true)` record                                |
| `(PM, Architect, deliver)`       | Research complete                                                    | `handoff_log` contains `(Researcher, PM, return)` record                                                                     |
| `(PM, Planner, deliver)`         | HE Stage 2 complete + user approved architecture→planning transition | `handoff_log` contains `(Architect, PM, return)` record AND `(PM, PM, submit, accepted=true)` record                         |
| `(PM, Developer, deliver)`       | Plan accepted                                                        | `handoff_log` contains `(Planner, PM, return)` record                                                                        |
| `(Developer, PM, return)`        | Acceptance stamps present                                            | `handoff_log` contains `(Evaluator, PM, submit, accepted=true)`; if HE participated → also `(HE, PM, submit, accepted=true)` |
| `(Architect, HE, submit)`        | Design spec complete                                                 | `artifact_paths` non-empty with spec artifacts                                                                               |
| `(Developer, Evaluator, submit)` | Phase announced + deliverables reference plan                        | `handoff_log` contains `(Developer, Evaluator, announce)` with matching `phase` identifier; `artifact_paths` non-empty       |


**Design decision: `current_phase` is NOT a gate authority.** `current_phase` is a PCG routing field — it tells `process_handoff` which agent to invoke next. It is a derived summary, not a gate authority. The `handoff_log` is the append-only ground truth of what actually happened. Implementation may use `current_phase` as a fast-fail optimization, but the AD does not mandate it as a gate condition.

**(4) User approval gate mechanism:**

Two transitions require explicit user approval (per Q7): `scoping→research` (D2) and `architecture→planning` (D4). The approval is recorded as a self-referential triple:

- **Triple:** `(PM, PM, submit)` — PM is both source and target.
- `**accepted` field:** `true` (user approved) or `false` (user requested revisions).
- `**brief`:** Description of what was reviewed and the decision.

**Rationale for self-referential triple:** `source_agent` is an enum of mounted child graphs. Stakeholder is not a mounted child graph — adding it to the enum pollutes a routing enum with a non-agent entity. The PM runs the approval tool and records the outcome; the `brief` carries the human-readable semantics. The triple is for middleware dispatch, not narrative.

**Prerequisite gates on D2 and D4** check `handoff_log` for `(PM, PM, submit, accepted=true)` before allowing delivery through.

**Autonomous mode override:** When autonomous mode is enabled, the middleware auto-creates a `(PM, PM, submit, accepted=true)` record, bypassing the user approval step.

**(5) Acceptance stamp vs normal handoff record:**

Both use the same `HandoffRecord` type. The `accepted` field (added per Q10) is the discriminator:


| Field            | Normal Record  | Acceptance Stamp (pass)           | Acceptance Stamp (fail)            |
| ---------------- | -------------- | --------------------------------- | ---------------------------------- |
| `accepted`       | `None`         | `true`                            | `false`                            |
| `reason`         | any            | `submit`                          | `submit`                           |
| `brief`          | work summary   | verification reasoning + evidence | rejection reasoning + deficiencies |
| `artifact_paths` | work artifacts | eval results, test outputs        | eval results, failure evidence     |


**Gate semantics:**

- `accepted=true` → satisfies the acceptance gate on `return_product_to_pm`
- `accepted=false` → audit record only; does NOT satisfy the gate
- `accepted=None` → not an acceptance stamp; ignored by acceptance gate logic

**Phase gate approval records** use the same `accepted` field:

- `(PM, PM, submit, accepted=true)` → satisfies the user-approval gate on D2/D4
- `(PM, PM, submit, accepted=false)` → user requested revisions; PM must revise and re-present

**(6) P4 ungated — design rationale:**

`submit_phase_to_harness_engineer` is ungated because HE phase review is advisory (EBDR-1 feedback packet, no pass/fail authority). Adding a prerequisite would make announce→submit mandatory for HE, contradicting the non-blocking design intent. The Evaluator (P3) requires announcement because it has blocking authority — it can hard-fail a phase. HE cannot. The asymmetry is intentional: P3 gated (blocking authority), P4 ungated (advisory only). If the Developer submits without announcing, the HE processes it with less context — that's a quality issue for the Developer's prompt to discourage, not a gate for middleware to enforce.

**(7) Cascade to Q8 (extended middleware per agent):**

The dispatch table determines which agents need phase gate middleware. Agents that own gated tools (gates fire on the calling agent's side):


| Agent      | Gated tools owned                                               | Needs phase gate middleware? |
| ---------- | --------------------------------------------------------------- | ---------------------------- |
| PM         | D1, D2, D3, D4, D5 (prerequisite/approval) + approval recording | Yes                          |
| Developer  | R5 (acceptance stamps), P3 (prerequisite)                       | Yes                          |
| Architect  | S1 (prerequisite)                                               | Yes                          |
| HE         | A1 (stamp only — no gate logic)                                 | No                           |
| Researcher | None                                                            | No                           |
| Planner    | None                                                            | No                           |
| Evaluator  | None                                                            | No                           |


This partially answers Q8 but does not close it — Q8 also covers any other role-specific middleware beyond phase gate middleware.

---

## Provider Integrations

### Q13: Anthropic provider-specific middleware integration

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

> **Decision Summary:** Anthropic gets native tools and memory through provider-profile injection, and server-side tools are now required for v1. Keep that logic out of shared factories.

**(1) Decision — two Anthropic middleware adopted, three rejected:**


| Middleware                                                                 | Decision   | Rationale                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ClaudeBashToolMiddleware`                                                 | **Adopt**  | Provides Anthropic's native `bash_20250124` tool descriptor that Claude was trained on. Extends `ShellToolMiddleware` (same execution logic, same `self.tools`). Only swaps the generic shell tool descriptor for Anthropic's native one via `wrap_model_call`. No overlap with `FilesystemMiddleware` tools. Zero cost, measurable tool-use accuracy gain.                     |
| `FilesystemClaudeMemoryMiddleware`                                         | **Adopt**  | Provides Anthropic's native `memory_20250818` tool with dedicated `/memories/` scratchpad. Complements (does not overlap) the SDK's `MemoryMiddleware` — see §(2) below. Uses disk persistence (survives across threads), which aligns with the agent-learning vision. Default `MEMORY_SYSTEM_PROMPT` is accepted for v1; per-role tuning deferred to Q12 behavioral contracts. |
| `StateClaudeTextEditorMiddleware` / `FilesystemClaudeTextEditorMiddleware` | **Reject** | Overlaps with `FilesystemMiddleware`'s `edit_file` tool. Two editing tools on the same model creates ambiguity — which one does the model pick? `FilesystemMiddleware` tools are model-agnostic and consistent across all providers. The marginal accuracy gain from Anthropic's native `text_editor_20250728` schema is not worth the cross-provider inconsistency cost.       |
| `StateFileSearchMiddleware`                                                | **Reject** | Overlaps with `FilesystemMiddleware`'s `glob`/`grep` tools. Same reasoning as text editor — our tools already provide this capability model-agnostically.                                                                                                                                                                                                                       |


**(2) Two-layer memory architecture — SDK `MemoryMiddleware` and Anthropic `memory` tool are complementary, not overlapping:**


| Dimension             | SDK `MemoryMiddleware`                                                                                            | Anthropic `memory` tool (via `FilesystemClaudeMemoryMiddleware`)                                      |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Mechanism**         | System prompt injection (no tool)                                                                                 | Native tool + system prompt injection                                                                 |
| **Write path**        | Uses `edit_file` (from `FilesystemMiddleware`)                                                                    | Dedicated `memory` tool (view/create/str_replace/insert/delete/rename)                                |
| **Storage**           | AGENTS.md files on backend                                                                                        | `/memories/` directory on disk                                                                        |
| **Persistence**       | Survives across threads (backend-backed)                                                                          | Survives across threads (disk-backed)                                                                 |
| **Prompt philosophy** | "Learn from user feedback, update your instructions" (long-term)                                                  | "Assume interruption, always persist progress" (short-term)                                           |
| **Scope**             | High-signal persistent context — project overviews, cross-project learnings, style guidelines, architecture notes | Short-term procedural working memory — what was tried, what failed, what worked on this specific task |
| **Access pattern**    | Passive — loaded into system prompt every turn, agent doesn't choose to read it                                   | Active — agent decides when to write progress and when to check prior state                           |
| **Creates folder?**   | No — reads existing AGENTS.md files                                                                               | Yes — `FilesystemClaudeMemoryMiddleware.__init`__ creates `root_path` directory on disk               |


**Design intent.** `MemoryMiddleware` (AGENTS.md) is the long-horizon knowledge base — cross-project learnings that eventually get synthesized into reusable skills. The Anthropic `memory` tool (`/memories/`) is the short-horizon working scratchpad — procedural learnings from the current and recent projects that improve agent precision over time (e.g., Developer learning SDK patterns, Architect learning design patterns). The two layers serve different memory horizons and different access patterns. They are additive, not redundant.

**Canonical source references for the overlap analysis:**

- SDK `MemoryMiddleware`: `.reference/libs/deepagents/deepagents/middleware/memory.py` — `before_agent` loads AGENTS.md content into `state.memory_contents`; `wrap_model_call` injects `<agent_memory>` block into system prompt; no tool provided; write path is `edit_file` from `FilesystemMiddleware`.
- Anthropic `memory` middleware: `.venv/lib/python3.11/site-packages/langchain_anthropic/middleware/anthropic_tools.py` lines 37–44 (`MEMORY_SYSTEM_PROMPT`), lines 611–654 (`StateClaudeMemoryMiddleware`), lines 1110–1161 (`FilesystemClaudeMemoryMiddleware`) — provides `memory` tool with commands view/create/str_replace/insert/delete/rename; enforces `/memories` path prefix; injects `MEMORY_SYSTEM_PROMPT` via `wrap_model_call`.
- Anthropic `bash` middleware: `.venv/lib/python3.11/site-packages/langchain_anthropic/middleware/bash.py` — extends `ShellToolMiddleware`; `wrap_model_call` replaces generic shell descriptor with `{"type": "bash_20250124", "name": "bash"}`; does NOT touch `FilesystemMiddleware` tools.

**(3) Injection mechanism — Anthropic provider profile via `_HarnessProfile.extra_middleware`:**

**Two-path distinction — how Anthropic middleware reaches the stack:**

`AnthropicPromptCachingMiddleware` and the new provider-specific middleware enter the stack through **different mechanisms**:


| Middleware                                                      | Path                                                                                                                                                                                    | Why                                                                                                                                                                           |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AnthropicPromptCachingMiddleware`                              | **Hardcoded** in `graph.py` (lines 450, 508, 579) — appended unconditionally to every stack for every model. No-ops for non-Anthropic models via `unsupported_model_behavior="ignore"`. | Considered universal infrastructure. Even if it only benefits Anthropic models, the no-op cost is negligible and it avoids a special-case code path.                          |
| `ClaudeBashToolMiddleware` + `FilesystemClaudeMemoryMiddleware` | **Provider profile** via `_register_harness_profile("anthropic", ...)` — only injected when model provider resolves to `"anthropic"`. Non-Anthropic models never see these.             | These are genuinely provider-specific (Anthropic-native tool descriptors). They would error or behave incorrectly on non-Anthropic models. Conditional injection is required. |


Anthropic server-side tools middleware (`AnthropicServerSideToolsMiddleware`) follows the same profile path — added as an entry to the `extra_middleware` factory lambda. No `graph.py` changes needed. See §(5) below for the v1 integration decision.

**Resolution chain — how `create_deep_agent()` finds and applies the profile:**

```
create_deep_agent(model="anthropic:claude-opus-4-6")
  1. resolve_model() → creates ChatAnthropic instance
  2. _harness_profile_for_model(model, spec="anthropic:claude-opus-4-6")
  3. _get_harness_profile("anthropic:claude-opus-4-6")   # exact match first (per-model overrides)
  4. _get_harness_profile("anthropic")                    # provider fallback ← our registration key
  5. profile.extra_middleware factory called → fresh instances appended to tail stack
```

For pre-built model instances (`model=ChatAnthropic(model="claude-opus-4-6")`), the chain uses `get_model_provider(model)` which reads `model._get_ls_params()["ls_provider"]` — `ChatAnthropic` returns `"anthropic"`. Same result.

Canonical source: `.reference/libs/deepagents/deepagents/graph.py` lines 132–159 (`_harness_profile_for_model`), `.reference/libs/deepagents/deepagents/_models.py` lines 65–85 (`get_model_provider`).

**File placement — provider profile module, NOT agent factory files:**

The `_register_harness_profile` call is a one-time, import-time side effect. It is **provider-level** configuration, not agent-level. It must NOT live in agent factory files (`architect.py`, `developer.py`, etc.) — those just call `create_deep_agent(model="anthropic:claude-opus-4-6", ...)` and never reference the profile or Anthropic middleware directly.

The correct location is a **provider profile module**, following the exact pattern the SDK already uses:

- SDK's OpenAI profile: `.reference/libs/deepagents/deepagents/profiles/_openai.py`
- SDK's OpenRouter profile: `.reference/libs/deepagents/deepagents/profiles/_openrouter.py`
- Our Anthropic profile: `agents/profiles/_anthropic.py` (implementation spec owns exact path)

The profile module is imported at application startup (as a side-effect import, same as the SDK's `_openai.py` is imported in `.reference/libs/deepagents/deepagents/profiles/__init__.py`). Once registered, every `create_deep_agent()` call with an Anthropic model automatically receives the middleware — no per-agent wiring needed.

**The Anthropic profile registration:**

```python
# agents/profiles/_anthropic.py
from deepagents.profiles._harness_profiles import _HarnessProfile, _register_harness_profile
from langchain_anthropic.middleware import (
    ClaudeBashToolMiddleware,
    FilesystemClaudeMemoryMiddleware,
    MEMORY_SYSTEM_PROMPT,
)

_register_harness_profile(
    "anthropic",
    _HarnessProfile(
        extra_middleware=lambda: [
            ClaudeBashToolMiddleware(workspace_root=<workspace_root>),
            FilesystemClaudeMemoryMiddleware(
                root_path=<memory_root>,
                system_prompt=MEMORY_SYSTEM_PROMPT,  # v1: default; v2: per-role override
            ),
        ],
    ),
)
```

**Why a factory (lambda) instead of a static list?** The `_HarnessProfile` docs (`.reference/libs/deepagents/deepagents/profiles/_harness_profiles.py` line 103–109) state: "May be a static sequence or a zero-arg factory that returns one (use a factory when the middleware instances should not be shared/reused across stacks)." Each agent (main + subagents) needs its own middleware instances — sharing a single `ClaudeBashToolMiddleware` across stacks would cause session state conflicts.

**Why `FilesystemClaudeMemoryMiddleware` over `StateClaudeMemoryMiddleware`?** `StateClaudeMemoryMiddleware` stores in `state.memory_files` — per-thread, dies with the thread. This defeats the agent-learning vision where the Architect accumulates design patterns across projects, the Developer accumulates SDK familiarity across projects, etc. `FilesystemClaudeMemoryMiddleware` writes to disk under `root_path`, which survives across threads and works with both backend modes (sandbox and local-first). The `root_path` must be configured per deployment mode — implementation spec owns the exact path resolution.

**No changes to `graph.py`.** The profile system handles injection automatically. `AnthropicPromptCachingMiddleware` remains hardcoded in the tail stack (it's unconditional and model-agnostic in behavior — `unsupported_model_behavior="ignore"` means it no-ops for non-Anthropic models). The two new middleware enter via the profile's `extra_middleware` slot, which the SDK already places in the tail stack before `AnthropicPromptCachingMiddleware`.

**Agent factory files remain clean:**

```python
# agents/architect.py — no Anthropic-specific imports or middleware references
agent = create_deep_agent(
    model="anthropic:claude-opus-4-6",   # profile system handles Anthropic middleware automatically
    backend=...,
    middleware=[...],                      # only role-specific custom middleware here
    ...
)
```

**(4) `MEMORY_SYSTEM_PROMPT` caveat — default accepted for v1, per-role tuning in Q12:**

The Anthropic `MEMORY_SYSTEM_PROMPT` (`.venv/lib/python3.11/site-packages/langchain_anthropic/middleware/anthropic_tools.py` lines 37–44) has a very strong directive: *"ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE."* This is designed for Claude Code's single-agent, single-task context. In our multi-agent pipeline, this could cause friction — an agent receiving a handoff brief might waste its first turn checking `/memories/` instead of acting on the brief.

This is not a blocker — `FilesystemClaudeMemoryMiddleware.__init__` accepts `system_prompt=` as a parameter (line 1138), so we can override it. v1 accepts the default prompt. Per-role prompt tuning (e.g., "check memory after processing the handoff brief" vs. "check memory first") belongs in **Q12 behavioral contracts** — the prompt steers behavior through the capabilities that middleware provides.

**(5) Anthropic server-side tools — REQUIRED for v1 launch (revised 2026-04-15):**

> 🚩 **FLAGGED:** This item was previously marked "deferred to v2" but is now **required for the v1 production launch**. There is no v2 — this is the launching version. All subsequent work is refinement of the production application.

The Anthropic API `ToolUnionParam` (`.venv/lib/python3.11/site-packages/anthropic/types/tool_union_param.py`) includes server-side tools that execute on Anthropic's infrastructure (model emits `server_tool_use` → Anthropic executes → result returns inline in same response, no turn break, no `ToolMessage`). These have NO middleware in `langchain_anthropic` yet, but **must be integrated for v1**.


| Server-side tool         | Type constants                                                                  | What it does                                                   | Target Agents                                                           |
| ------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `web_search`             | `web_search_20250305`, `web_search_20260209`                                    | Web search with domain filtering, location awareness, max_uses | **Researcher, Architect** (primary); HE, Planner, Evaluator (secondary) |
| `web_fetch`              | `web_fetch_20250910`, `web_fetch_20260209`, `web_fetch_20260309`                | URL content fetching with citations, caching control           | **Researcher** (primary); Architect (secondary)                         |
| `code_execution`         | `code_execution_20250522`, `code_execution_20250825`, `code_execution_20260120` | Server-side REPL with daemon mode + gVisor checkpoint          | **Developer, HE, Evaluator** (tool-heavy agents)                        |
| `tool_search_tool_bm25`  | `tool_search_tool_bm25_20251119`                                                | BM25-based tool discovery (for `defer_loading` pattern)        | **Developer** (tool-heavy agent)                                        |
| `tool_search_tool_regex` | `tool_search_tool_regex_20251119`                                               | Regex-based tool discovery                                     | **Developer**                                                           |


**Options weighed:**


| Option                                              | Description                                                                                                                                                                                                                            | Verdict                                                                                             |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| (a) **Lightweight descriptor-injection middleware** | Create middleware that detects Anthropic models and appends server-side tool descriptors to `request.tools`. Follows the existing `AnthropicPromptCachingMiddleware` pattern where middleware gracefully ignores non-Anthropic models. | **RECOMMENDED** — Clean, testable, follows SDK conventions                                          |
| (b) Pass descriptors via `tools=[]` param           | Add dict-style tool descriptors directly to agent factory `tools` lists.                                                                                                                                                               | Rejected — pollutes agent factories with provider-specific concerns; violates model-agnostic design |
| (c) Contribute upstream to `langchain-anthropic`    | Wait for SDK to provide official server-side tool middleware.                                                                                                                                                                          | Rejected — timeline unknown; v1 cannot block on upstream                                            |
| (d) Hardcode into `create_deep_agent()`             | Add server-side tool injection directly into SDK's `graph.py`.                                                                                                                                                                         | Rejected — requires SDK fork/contribution; out of scope for Meta Harness                            |


**Selected approach (signal intent for droids):**

Implement a lightweight middleware (e.g., `AnthropicServerSideToolsMiddleware`) that:

- Detects Anthropic models via `isinstance(request.model, ChatAnthropic)` check
- Appends server-side tool descriptors to `request.tools` before model invocation
- Gracefully ignores non-Anthropic models (mirrors `AnthropicPromptCachingMiddleware` pattern)
- Is injected via the **Anthropic provider profile** (`agents/profiles/_anthropic.py`) alongside `ClaudeBashToolMiddleware` and `FilesystemClaudeMemoryMiddleware`

**Droid implementation authority:** The droids own the final implementation spec. This decision provides signal intent and constraints, not a complete technical specification. The droids should evaluate whether the recommended middleware pattern aligns with their architecture and adjust as needed to achieve an elegant, production-grade solution.

**Agent-specific tool provisioning:** The droids should determine which agents receive which server-side tools. Initial guidance: Researcher receives `web_search` 2026 + `web_fetch`2026; Architect receives `web_search`; Developer receives `code_execution` + `tool_search`_*; HE and Evaluator receive subsets based on their tool-usage patterns but ideally are allocated tool search, code execution etc.

**Beta-only tools (not in stable API union, out of scope):** `computer_use` (3 versions), `mcp_toolset`.

**(6) `ClaudeBashToolMiddleware` does not overlap `FilesystemMiddleware` — confirmed:**

`ClaudeBashToolMiddleware` (`.venv/lib/python3.11/site-packages/langchain_anthropic/middleware/bash.py`) extends `ShellToolMiddleware` and provides exactly one tool: `bash`. It does NOT touch any of the `FilesystemMiddleware` tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`). Those remain unchanged from the SDK's base stack. The bash tool is purely additive — it gives Claude a native shell execution tool that it was specifically trained on, replacing the generic `ShellToolMiddleware` descriptor with Anthropic's `bash_20250124` descriptor.

For non-Anthropic models (OpenAI, GLM, etc.), the SDK's default `ShellToolMiddleware` (or no shell tool, depending on backend) applies — the Anthropic profile's `extra_middleware` is only injected when the model provider is `"anthropic"`.

**(7) Summary of Anthropic middleware integration:**

```
Anthropic agent effective middleware stack:

Base:     TodoList → Skills → Filesystem → SubAgent → Summarization → PatchToolCalls
User:     [role-specific custom middleware per Q8]
Tail:     ClaudeBashToolMiddleware*        ← NEW (from profile extra_middleware)
          FilesystemClaudeMemoryMiddleware* ← NEW (from profile extra_middleware)
          [ToolExclusion] → PromptCaching → Memory → HITL → Permissions

* Only present when model provider is "anthropic"
```

The two-layer memory system for Anthropic agents:

```
Layer 1 (passive, every turn):    MemoryMiddleware (AGENTS.md → system prompt)
                                   Long-horizon: project overviews, cross-project learnings, skill pointers
Layer 2 (active, on-demand):      FilesystemClaudeMemoryMiddleware (/memories/ → memory tool)
                                   Short-horizon: procedural working memory, progress persistence, SDK familiarity
```

**Decisions delegated to implementation spec:** Exact `workspace_root` and `root_path` values for `ClaudeBashToolMiddleware` and `FilesystemClaudeMemoryMiddleware` per deployment mode (sandbox vs. local-first); per-role `MEMORY_SYSTEM_PROMPT` overrides (Q12 owns the behavioral contracts); whether to register the Anthropic profile in our codebase or contribute it upstream to `deepagents`; `AnthropicServerSideToolsMiddleware` implementation details (exact per-agent tool provisioning, descriptor format, graceful degradation for non-Anthropic models).

---

### Q12: System prompt behavioral contracts

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

**(1) System prompts live in external markdown files, NOT hardcoded in agent factory files:**

Each agent's system prompt is authored in a standalone `.md` file colocated next to the agent's factory module. The factory loads the prompt at init time and passes it to `create_deep_agent(system_prompt=...)`.

**File convention:**

```
agents/
  architect/
    __init__.py          # factory: create_deep_agent(system_prompt=load("system_prompt.md"), ...)
    system_prompt.md     # behavioral contract for Architect
  developer/
    __init__.py
    system_prompt.md
  pm/
    __init__.py
    system_prompt.md
  ... (7 agents total)
```

**Precedent.** This follows the same pattern as:

- v0.5 reference implementation: `meta_agent_v.0.5/prompts/` directory with external markdown prompt files
- Deep Agent CLI: `.reference/libs/cli/deepagents_cli/agent.py` loads system prompts from files
- The `MEMORY_SYSTEM_PROMPT` override pattern from Q13 — even Anthropic's middleware accepts `system_prompt=` as a parameter, decoupling prompt content from code

**Why external files over hardcoded strings:**

- **Maintainer-friendly**: prompt iteration is a content concern, not an engineering concern — no code changes, no PRs, no deployments to update a prompt
- **Debuggable**: the exact prompt the agent received is inspectable as a file, not buried in a Python string literal
- **Spec-team-friendly**: the design team can author and iterate prompts without touching Python code
- **Diff-friendly**: prompt changes are single-file markdown diffs, not interleaved with code changes

**(2) The AD locks behavioral invariants, not prompt text:**

The AD defines *what each agent must recognize and must not do* — the behavioral invariants that the system prompt must encode. The actual prompt text that fulfills those invariants is spec territory and lives in the `.md` files.

**Per-agent behavioral invariants (locked by the AD):**


| Agent      | Must Recognize                                                                                                                                                                           | Must Not Do                                                                                                                 | Self-Awareness Trigger                                                                    |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| PM         | PRD finalization → invoke `deliver_prd_to_harness_engineer`; HE return → invoke next delivery tool; user approval requirement for scoping→research and architecture→planning transitions | Must NOT perform research, design, or coding work directly                                                                  | "I have the full PRD, eval criteria, and datasets. Time to bring in the expert."          |
| HE         | PRD delivery → begin eval design; Architect spec → evaluate new tools/prompts; Developer phase submission → run advisory review                                                          | Must NOT make business decisions or override PM scope                                                                       | "I've received the PRD. My job is the science of evaluation."                             |
| Researcher | PM delivery → begin research; Architect consultation request → targeted research                                                                                                         | Must NOT design solutions or make architectural decisions                                                                   | "I've found what the Architect needs. Time to return the bundle."                         |
| Architect  | Research bundle + PRD → begin design; knowledge gap → request research from Researcher                                                                                                   | Must NOT research (that's Researcher's domain) or plan implementation (that's Planner's domain)                             | "I have a knowledge gap on X SDK. I need targeted research before I can finalize design." |
| Planner    | Design spec + eval criteria → begin planning                                                                                                                                             | Must NOT design (that's Architect) or implement (that's Developer)                                                          | "I have the full design. My job is to decompose it into an executable plan."              |
| Developer  | Plan + eval criteria → begin implementation; phase completion → announce to Evaluator/HE                                                                                                 | Must NOT self-certify acceptance (that's Evaluator/HE); must NOT call `submit_phase_to_evaluator` for eval-science concerns | "Phase N complete. Time to submit for evaluation."                                        |
| Evaluator  | Developer phase submission → evaluate against spec/plan; final product → acceptance stamp                                                                                                | Must NOT modify code or design; must NOT gate on eval-science concerns (that's HE)                                          | "I've verified the deliverable against the spec. Here's my assessment."                   |


**Boundary enforcement principle:** Each agent's system prompt must encode the boundary between its expertise and the next agent's. The PM/HE boundary is the canonical example: PM scopes *what* success looks like; HE owns *how* to evaluate. Neither crosses into the other's domain.

**(3) Autonomous mode behavior changes:**

When autonomous mode is enabled, the PM's system prompt must instruct it to auto-approve the two user-approval gates (scoping→research, architecture→planning) by creating `(PM, PM, submit, accepted=true)` records without presenting to the stakeholder. All other behavioral invariants remain unchanged — autonomous mode does not bypass acceptance stamps, phase gates, or role boundaries.

**(4) `MEMORY_SYSTEM_PROMPT` per-role tuning (carries from Q13):**

The Anthropic `MEMORY_SYSTEM_PROMPT` default ("ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE") is too aggressive for our multi-agent pipeline. Per-role overrides belong in the system prompt `.md` files, not in the profile registration. The recommended tuning:

- **PM, HE, Planner, Evaluator**: "After processing the handoff brief, check your memory directory for relevant context from prior work."
- **Researcher, Architect**: "Before beginning research/design work, check your memory directory for relevant learnings from prior projects."
- **Developer**: "Before writing code, check your memory directory for SDK patterns and learnings from prior implementations."

This tuning ensures the agent acts on the handoff brief first (the urgent, context-rich input) and then consults memory for accumulated knowledge (the slower, broader context).

**(5) Prompt authoring is a continuous process, not a gate:**

The `.md` files are placeholders at project start. The design team authors initial versions based on the behavioral invariants above. Prompt quality improves through iteration (observation → diagnosis → prompt edit → re-observation). The AD does not gate development on prompt perfection — the external file pattern ensures prompts can be updated independently of code.

**Decisions delegated to implementation spec:** Exact loading mechanism (file path resolution, `Path.read_text()` vs. backend-based loading, caching behavior); prompt template variable injection (e.g., `{{role_name}}` interpolation); whether prompts are loaded once at graph compilation time or per-invocation; exact prompt text for each agent (spec territory, not AD territory).

---

## Product Surface & Runtime

### Q14: User interface surface

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

> **Decision Summary:** The web/TUI surface is an observer of pipeline state, not the system of record. It should surface the current role, phase, approvals, and trace links without owning execution.

**(1) v1 ships a Textual TUI, launched via `langgraph dev`:**

The v1 user interface is a terminal TUI built on the Textual framework, launched via the standard `langgraph dev` server. This is the fastest path to a working, interactive prototype — no custom server, no deployment pipeline, just `langgraph dev` pointing at our `langgraph.json` with a Textual app as the client.

**Deployment evolution:**

- **v1 (prototyping):** `langgraph dev` + Textual TUI + LangGraph Studio for dev-time inspection
- **v2 (product):** LangGraph Platform deployment + `pip install meta-harness` (standalone CLI product, like Claude Code or Codex — provide an API key and go)

The v1 path is not throwaway work — the Textual TUI and `langgraph.json` entrypoint carry forward into v2. The only change is the server backend (local `langgraph dev` → LangGraph Platform) and the distribution mechanism (source → pip package).

**(2) Adopt the Deep Agents CLI TUI as the base layer:**

The Deep Agents CLI (`deepagents_cli/`) ships a production-quality Textual TUI with widgets, theme system, and interaction patterns that map directly to our needs. We adopt it as the base layer — same framework (Textual), same brand theme (`theme.py`), same widget patterns — and extend it for our multi-agent pipeline.

**Widget mapping — CLI → Meta Harness:**


| Meta Harness need                                      | CLI widget                                                | Source file                               | Reuse verdict                                                  |
| ------------------------------------------------------ | --------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| `ask_user` interrupt UX                                | `AskUserMenu`                                             | `widgets/ask_user.py`                     | Direct reuse — PM and Architect both use `ask_user` middleware |
| Shell / tool approval gates                            | `ApprovalMenu`                                            | `widgets/approval.py`                     | Direct reuse — maps to our phase gate approval UX              |
| Chat input with autocomplete                           | `ChatInput`                                               | `widgets/chat_input.py`                   | Direct reuse                                                   |
| Message rendering (assistant, tool calls, errors)      | `AppMessage`, `AssistantMessage`, `ToolCallMessage`, etc. | `widgets/messages.py`                     | Direct reuse                                                   |
| Status bar / spinners / loading                        | `StatusBar`, `LoadingWidget`                              | `widgets/status.py`, `widgets/loading.py` | Direct reuse                                                   |
| Thread / project selector                              | `ThreadSelector`                                          | `widgets/thread_selector.py`              | Adapt — maps to project selection (our `project_id`)           |
| Theme system (dark/light, brand colors, custom themes) | `Theme`, `ThemeSelector`                                  | `theme.py`, `widgets/theme_selector.py`   | Direct reuse                                                   |
| Model selector                                         | `ModelSelector`                                           | `widgets/model_selector.py`               | Adapt — maps to per-agent model config at project start        |
| Welcome banner                                         | `WelcomeBanner`                                           | `widgets/welcome.py`                      | Adapt — Meta Harness branding                                  |


**The gap — pipeline awareness:**

The CLI TUI is built for a single agent talking to a user. Meta Harness runs a 7-agent pipeline where the user only directly interacts with the PM. The TUI must surface pipeline state that the CLI does not currently display:

- **Active agent indicator:** Which role is currently running (PM, HE, Researcher, etc.)
- **Phase progress:** Current phase in the pipeline (scoping → research → architecture → planning → development → acceptance)
- **Handoff progress:** Visual indication of handoffs flowing through the pipeline (who handed off to whom, what artifact is moving)
- **Approval gate status:** When the PM is presenting a document package for user approval, the TUI must render the approval interaction clearly
- **Autonomous mode toggle:** Visual indicator and control for autonomous mode (auto-advances approval gates)

This pipeline awareness extension is the novel design work. No reference implementation exists — it's ours to invent. The AD defines *what the TUI must surface* (the information requirements above); the spec team owns *how it renders* (widget layout, animations, information density).

**(3) AD locks what the TUI must surface, not how it renders:**

Following the same pattern as Q12 (AD locks behavioral invariants, spec owns prompt text), the AD locks the information requirements the TUI must surface. The visual design, widget layout, animation choices, and interaction patterns are spec territory.

**Locked information requirements (the TUI must surface these):**


| Surface                                   | Source                                | Already in AD             |
| ----------------------------------------- | ------------------------------------- | ------------------------- |
| Active agent name                         | `current_agent` in PCG state          | §4 PCG State Schema       |
| Current phase                             | `current_phase` in PCG state          | §4 PCG State Schema       |
| Handoff log (recent entries)              | `handoff_log` in PCG state            | §4 PCG State Schema       |
| User-facing messages (lifecycle bookends) | `messages` in PCG state               | §4 PCG State Schema       |
| `ask_user` prompts (PM, Architect)        | `AskUserMiddleware` interrupt         | §4 Agent Primitives (Q8)  |
| Approval gate interactions (2 gates)      | Phase gate middleware                 | §4 Phase Gates            |
| Autonomous mode status                    | Runtime toggle                        | §4 Phase Gates            |
| Model selections per agent                | Project config                        | §4 Agent Primitives (Q11) |
| LangSmith trace links                     | `langsmith_run_id` in handoff records | §6 Observability          |


**(4) `langgraph.json` is the single server entrypoint:**

The TUI connects to the LangGraph server defined by `langgraph.json`. For v1, that server is `langgraph dev`. The TUI does not embed or manage the server — it is a client. This keeps the TUI thin and aligned with the LangGraph deployment model.

**Precedent.** The Deep Agents CLI follows the same pattern: `langgraph.json` defines the graph, `langgraph dev` runs it, and the Textual app connects as a client. The CLI's `server_graph.py` and `server_manager.py` handle the server lifecycle; our TUI will follow the same convention.

**Decisions delegated to implementation spec:** Exact pipeline awareness widget design and layout; how handoff progress is visualized (timeline, status panel, inline indicators, etc.); approval gate document rendering format (markdown preview, rendered docx, summary card); autonomous mode toggle UX; whether to fork CLI widgets or import them as a dependency; exact `langgraph.json` configuration; TUI module structure within `src/meta_harness/`; welcome banner content and branding; non-interactive / headless mode for CI and scripting.

---

### Q15: Headless PM session, thread identity, and source surfaces

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-20

> **Decision Summary:** PM intake and project execution are separate thread kinds with separate identities. Headless channels can talk to both, but they must not collapse them into one runtime.

**(1) Agent Server is the headless runtime boundary:**

LangGraph/LangSmith Agent Server owns assistants, threads, runs, Store, auth,
persistence, and queueing. Meta Harness must not introduce a separate runtime for
headless channels. Headless adapters normalize source events and submit Agent
Server runs against the correct LangGraph thread.

**(2) Two product-level thread kinds:**

Meta Harness defines exactly two base `thread_kind` values:


| `thread_kind` | Meaning                                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------------------------- |
| `pm_session`  | Projectless or cross-project PM conversation used for intake, discovery, status questions, and pre-seed scoping |
| `project`     | Canonical project execution thread that runs the Project Coordination Graph                                     |


No base `utility` thread kind is adopted. Utility/background work is modeled as
tools, subagent tasks, artifacts, Store records, or implementation-specific runs
owned by a `pm_session` or `project` thread.

**(3) Identifier contract:**


| Identifier             | Definition                                                     |
| ---------------------- | -------------------------------------------------------------- |
| `thread_id`            | LangGraph checkpoint/conversation identity                     |
| `project_id`           | Durable Meta Harness project identity                          |
| `project_thread_id`    | Canonical LangGraph thread for one executable project          |
| `pm_session_thread_id` | LangGraph thread for non-project/cross-project PM conversation |


`project_thread_id` may equal `project_id` in local/dev, but that is a
convention, not the definition of `project_id`.

**(4) PM product identity:**

`pm_session` is not a second PM and not a `ProjectCoordinationState` key. It is a
LangGraph thread whose metadata has `thread_kind = "pm_session"`. The PM is one
Deep Agent — one `create_deep_agent()` call, one identity, one memory source.
Its tool set adapts at runtime via middleware that reads `thread_kind` from
thread metadata and conditionally includes session tools or project tools. No
separate graph compilation or graph ID is required for this distinction.

**(5) PM session to project lifecycle:**

> **Supersession note (2026-04-22):** The field names `parent_pm_thread_id`,
> `active_project_id`, and `active_project_thread_id` in this subsection were
> drifted from Jason's original intent during documentation migration. The
> canonical naming is locked in `AD.md §4 PM Session And Project Entry Model → Identity Linkage and Cardinality`: primary identifiers are `pm_session_thread_id`
> and `project_thread_id` with **no** `parent_`*, `active_`*, `source_*`, or
> `origin_*` prefix; the link from a project back to its originating pm_session
> lives as a nullable `pm_session_thread_id` field on the project's
> `projects_registry` Store entry; there is no active-project pointer in
> `pm_session` checkpoint state (the `projects_registry` Store is the source of
> truth for spawn lineage, and a single pm_session may spawn many projects over
> its lifetime). AD is canonical; this Q15(5) subtext is retained for historical
> record only.

PM session threads do not mutate into project threads. Project creation from a
PM session creates a separate project thread with `thread_kind = "project"` and
records parent/active links such as `parent_pm_thread_id`,
`active_project_id`, and `active_project_thread_id`. PM session can inspect,
continue, or consult projects through tools, Store, registry records, project
memory, artifact indexes, or project-thread runs. It must not merge checkpoint
threads.

**(6) Headless ingress vs source presence:**

Headless is a UI/ingress/source-presence paradigm over the same core app, not a
different agent application.


| Layer            | Responsibility                                                                         |
| ---------------- | -------------------------------------------------------------------------------------- |
| Headless ingress | External event -> source identity -> LangGraph thread -> Agent Server run              |
| Source presence  | Tools/middleware that let PM act inside Slack/email/Discord/GitHub/Linear during a run |


Core project lifecycle, project thread, execution environment, repository
binding, contribution policy, and PR publication flow remain the same across
web, TUI, Slack, email, Discord, GitHub, Linear, and API. Source-specific Slack
UI/UX is explicitly deferred.

**Decisions delegated to implementation spec:** exact graph IDs, exact metadata
wire schema, deterministic vs Store-backed source conversation mapping per
source, source-specific adapter routes, source-presence tool schemas, and
which PM-session tools may read live project execution-environment files versus
only project memory/artifact indexes. The live-file access boundary remains the
single high-priority open question in `AD.md`.

---

### Q16: Project-scoped execution environment / agent computer

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-20

> **Decision Summary:** Every project thread that does real work must resolve a real execution environment. That environment is where code changes, checks, commits, and PRs happen.

**(1) Execution environment is a core product invariant:**

Meta Harness must provide a project-scoped execution environment as the agent's
computer. A project memory/artifact filesystem is not enough for autonomous
coding. For code-producing projects, the project thread resolves a shell-capable
workspace where agents can clone repositories, install dependencies, run
commands, modify files, commit, push, and open pull requests.

```txt
project_thread_id -> execution_environment_id -> provider sandbox/devbox/local root
```

**(2) Execution modes:**


| Mode              | Decision                                                                                                        |
| ----------------- | --------------------------------------------------------------------------------------------------------------- |
| `managed_sandbox` | Default for v1 production, web app, headless/autonomous work, client repos, and untrusted code                  |
| `external_devbox` | Customer/enterprise-managed provider, image, network policy, secrets policy, and lifecycle                      |
| `local_workspace` | Explicit opt-in local-first mode; local shell access must be guarded because commands run on the user's machine |


Daytona is the default managed sandbox/devbox provider for v1. LangSmith sandbox
may be supported as an optional/future/beta provider, not as the default.

**(3) Project thread ownership:**

PM session threads do not get an execution environment by default. Project
threads get an execution environment when the project requires implementation,
evaluation, or publication. Developer is the primary writer. Evaluator and
Harness Engineer can read and execute checks/evals against the candidate
workspace during review phases. Handoff gates serialize write/evaluation moments
so roles do not concurrently mutate the same repository workspace.

**(4) Brownfield contribution path:**

For existing client repositories, Meta Harness must support:

```txt
resolve repo -> resolve/create execution environment -> configure credentials
-> clone/refresh repo -> create/check out working branch
-> implement and run checks/evals -> commit -> push -> open/update draft PR
-> attach PR/check evidence to project memory and PM handoff
```

GitHub credentials follow the Open SWE architecture pattern: GitHub App/OAuth
style resolution and short-lived/auth-proxied credentials for sandbox work. Do
not write long-lived secrets into the sandbox.

**(5) Greenfield persistence path:**

Greenfield projects do not require immediate GitHub repo creation. Supported
persistence modes are:


| Mode                        | Meaning                                                                          |
| --------------------------- | -------------------------------------------------------------------------------- |
| `vm_only`                   | Keep work inside the execution environment and expose previews/artifacts/exports |
| `meta_harness_staging_repo` | Push to a Meta Harness-owned staging repository                                  |
| `client_repo`               | Create or push to a client-owned repository when approved                        |
| `archive_artifact`          | Export a bundle without remote git publication                                   |


**(6) Native web app invariant:**

From day one, the native web app must expose the same project-scoped computer
used by Developer, Evaluator, and Harness Engineer: repo binding, branch state,
file tree, selected file contents, diffs, staged changes, command/check/eval
logs, previews or artifact exports, commit SHA, PR URL/status, and environment
health/reconnect status.

**Decisions delegated to implementation spec:** exact Daytona integration
boundary, sandbox image defaults, workspace path conventions, environment
health/reconnect protocol, PR approval gates, local shell allow-list policy,
file browser route shape, and which PM-session tools may read live project
execution-environment files versus only memory/artifact indexes.

---

## Archived Agent Primitives Round (Q8–Q13, 2026-04-13)

> Migrated from `AD.md` §4 Agent Primitive Decisions on 2026-04-21. These tables were previously in the AD; they are now archived here as closed decision records.

### Middleware Systems

### Q8: Per-Agent Middleware (Archived)

> **Decision Summary:** Keep the middleware stack identical across roles except where a role explicitly owns gate or stakeholder interaction logic. This preserves a single mental model for stack composition.

All 7 agents share the same `create_deep_agent()` call shape. Per-agent variation is in values, not presence.

See [Q9](#archived-q9-middleware-dispatch-table) for gate logic derivation.

**Custom middleware in the `middleware=` slot:**


| Middleware                  | PM      | HE      | Researcher | Architect | Planner | Developer | Evaluator |
| --------------------------- | ------- | ------- | ---------- | --------- | ------- | --------- | --------- |
| CollapseMiddleware          | ✓       | ✓       | ✓          | ✓         | ✓       | ✓         | ✓         |
| ContextEditingMiddleware    | ✓       | ✓       | ✓          | ✓         | ✓       | ✓         | ✓         |
| SummarizationToolMiddleware | ✓       | ✓       | ✓          | ✓         | ✓       | ✓         | ✓         |
| ModelCallLimitMiddleware    | ✓       | ✓       | ✓          | ✓         | ✓       | ✓         | ✓         |
| StagnationGuardMiddleware   | ✓       | ✓       | ✓          | ✓         | ✓       | ✓         | ✓         |
| Phase gate middleware       | ✓       | —       | —          | ✓         | —       | ✓         | —         |
| AskUserMiddleware           | ✓       | —       | —          | ✓         | —       | —         | —         |
| ShellAllowListMiddleware    | sandbox | sandbox | sandbox    | sandbox   | sandbox | sandbox   | sandbox   |


**Per-agent parameter values:**


| Agent      | `thread_limit` | `check_interval` |
| ---------- | -------------- | ---------------- |
| PM         | 150            | 20               |
| Developer  | 500            | 50               |
| Architect  | 250            | 35               |
| HE         | 300            | 40               |
| Researcher | 300            | 40               |
| Planner    | 200            | 30               |
| Evaluator  | 200            | 30               |


**Phase gate middleware — per-agent gate logic:**


| Agent     | Gated tools                                     | Gate type                    | What middleware checks                                                                                |
| --------- | ----------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| PM        | `deliver_prd_to_harness_engineer` (D1)          | Prerequisite                 | `artifact_paths` non-empty with PRD                                                                   |
| PM        | `deliver_prd_to_researcher` (D2)                | Prerequisite + User Approval | `(HE, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)`                             |
| PM        | `deliver_design_package_to_architect` (D3)      | Prerequisite                 | `(Researcher, PM, return)` in `handoff_log`                                                           |
| PM        | `deliver_planning_package_to_planner` (D4)      | Prerequisite + User Approval | `(Architect, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)`                      |
| PM        | `deliver_development_package_to_developer` (D5) | Prerequisite                 | `(Planner, PM, return)` in `handoff_log`                                                              |
| Developer | `return_product_to_pm` (R5)                     | Acceptance stamps            | `(Evaluator, PM, submit, accepted=true)`; if HE participated → also `(HE, PM, submit, accepted=true)` |
| Developer | `submit_phase_to_evaluator` (P3)                | Prerequisite                 | `(Developer, Evaluator, announce)` with matching `phase`; `artifact_paths` non-empty                  |
| Architect | `submit_spec_to_harness_engineer` (S1)          | Prerequisite                 | `artifact_paths` non-empty with spec artifacts                                                        |


4 agents (HE, Researcher, Planner, Evaluator) own no gated tools and receive no phase gate middleware.

### Q9: Middleware Dispatch Table (Archived)

29 distinct `(source, target, reason)` triples from 23 tools:


| Gate Type                        | Count | Triples                      |
| -------------------------------- | ----- | ---------------------------- |
| Ungated (pass-through)           | 19    | R1–R4, S2, P1–P2, P4, C1–C13 |
| Prerequisite only                | 6     | D1, D3, D5, R5, S1, P3       |
| Prerequisite + User Approval     | 2     | D2, D4                       |
| Stamp only (no gate on emission) | 2     | A1, A2                       |


`current_phase` is NOT a gate authority — `handoff_log` is the append-only ground truth. Implementation may use `current_phase` as a fast-fail optimization, but the AD does not mandate it as a gate condition. User approval is recorded as `(PM, PM, submit, accepted=true/false)` — PM is both source and target.

### Tool & Contract Specifications

### Q10: Tool Schema Contracts (Archived)

> **Decision Summary:** Every handoff tool shares the same base schema, and only a small subset gets an extra field (`accepted` or `phase`). This keeps the tool surface simple enough for every model to use correctly.

**Common parameter shape — 2 LLM-facing parameters across all 23 tools:**


| Parameter        | Type        | Required | Default |
| ---------------- | ----------- | -------- | ------- |
| `brief`          | `str`       | Yes      | —       |
| `artifact_paths` | `list[str]` | No       | `[]`    |


`source_agent`, `target_agent`, `reason`, and `project_id` are derived at call time — not LLM parameters.

**6 of 23 tools require one extra parameter:**

- Acceptance tools (2): add `accepted: bool`
- Phase Review tools (4): add `phase: str` (free-form plan phase identifier, not the 6-value PCG phase enum)

**Acceptance stamp contract:** `HandoffRecord` extended with `accepted: bool | None` (default `None`). Normal records: `accepted=None`. Acceptance stamps: `accepted=true` or `accepted=false`.

### Q11: Model Selection Per Agent (Archived)

Model-agnostic architecture — no provider lock-in. Per-agent model selection, thread-scoped (immutable for project lifespan). Provider-specific tools injected based on selected model.

> **Decision Summary:** Model choice is per role, per project, and immutable for that project lifetime. The provider layer adds capabilities; the core graph stays model-agnostic.

**v1 experimental defaults:**


| Agent      | Default model | Notes                                                                      |
| ---------- | ------------- | -------------------------------------------------------------------------- |
| PM         | Opus 4.6      | —                                                                          |
| Researcher | Opus 4.6      | —                                                                          |
| Architect  | TBD           | Experiment: Opus 4.6 vs GPT 5.4 extra-high thinking vs GPT 5.4 Pro         |
| Planner    | Opus 4.6      | —                                                                          |
| HE         | TBD           | Likely GPT 5.4 Pro                                                         |
| Evaluator  | Opus 4.6      | —                                                                          |
| Developer  | TBD           | Experiment: Opus 4.6 (server-side tools) vs GPT 5.4 + Codex vs GPT 5.4 Pro |


### Q12: System Prompt Behavioral Contracts (Archived)

System prompts live in external `.md` files next to each agent factory (not hardcoded in Python). The AD locks behavioral invariants; prompt text is spec territory.

> **Decision Summary:** Prompt files are the behavioral contract surface, while the AD only locks what each role must recognize and avoid. This keeps prompt iteration outside code changes.

**Per-agent behavioral invariants:**


| Agent      | Must Recognize                                                                                                                        | Must Not Do                                                                         | Self-Awareness Trigger                                            |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| PM         | PRD finalization → invoke HE delivery; HE return → invoke next delivery; user approval for scoping→research and architecture→planning | Research, design, or code directly                                                  | "I have the full PRD. Time to bring in the expert."               |
| HE         | PRD delivery → begin eval design; Architect spec → evaluate new tools; Developer phase → advisory review                              | Make business decisions or override PM scope                                        | "I've received the PRD. My job is the science of evaluation."     |
| Researcher | PM delivery → begin research; Architect consultation → targeted research                                                              | Design solutions or make architectural decisions                                    | "I've found what the Architect needs. Time to return the bundle." |
| Architect  | Research bundle + PRD → begin design; knowledge gap → request research                                                                | Research (Researcher's domain) or plan implementation (Planner's domain)            | "I have a knowledge gap on X. I need targeted research."          |
| Planner    | Design spec + eval criteria → begin planning                                                                                          | Design (Architect) or implement (Developer)                                         | "I have the full design. My job is to decompose it."              |
| Developer  | Plan + eval criteria → begin implementation; phase completion → announce to QA                                                        | Self-certify acceptance; call `submit_phase_to_evaluator` for eval-science concerns | "Phase N complete. Time to submit for evaluation."                |
| Evaluator  | Developer phase submission → evaluate against spec/plan; final product → acceptance stamp                                             | Modify code or design; gate on eval-science concerns (HE's domain)                  | "I've verified against the spec. Here's my assessment."           |


Autonomous mode: PM auto-approves the two user-approval gates by creating `(PM, PM, submit, accepted=true)` records. All other invariants unchanged. `MEMORY_SYSTEM_PROMPT` per-role tuning: act on handoff brief first, then check memory directory.

### Provider Integrations

### Q13: Anthropic Provider-Specific Middleware (Archived)

> **Decision Summary:** Anthropic-specific middleware belongs in provider profiles, not in shared agent factories, and server-side tools are injected the same way. The profile handles the provider-specific surface; the agent factories stay generic.

**Adopted** (via Anthropic provider profile `extra_middleware`):

- `ClaudeBashToolMiddleware` — native `bash` tool for Anthropic models (additive, no overlap with `FilesystemMiddleware`)
- `FilesystemClaudeMemoryMiddleware` — `/memories/` tool for short-horizon working memory (two-layer memory: AGENTS.md = long-term, `/memories/` = short-term)

**Rejected** (overlap with `FilesystemMiddleware`):

- Text editor middleware — `FilesystemMiddleware` already provides `edit_file`
- File search middleware — `FilesystemMiddleware` already provides `glob` + `grep`

**Required for v1 (revised 2026-04-15):** Anthropic server-side tools (`web_search`, `web_fetch`, `code_execution`, `tool_search_tool_bm25`, `tool_search_tool_regex`) execute on Anthropic's infrastructure (model emits `server_tool_use` → Anthropic executes → result returns inline, no turn break). Integrated via lightweight descriptor-injection middleware (`AnthropicServerSideToolsMiddleware`) in the Anthropic provider profile. Per-agent assignment:


| Server-side tool         | Type constants                                                                  | Target Agents                                                           |
| ------------------------ | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `web_search`             | `web_search_20250305`, `web_search_20260209`                                    | **Researcher, Architect** (primary); HE, Planner, Evaluator (secondary) |
| `web_fetch`              | `web_fetch_20250910`, `web_fetch_20260209`, `web_fetch_20260309`                | **Researcher** (primary); Architect (secondary)                         |
| `code_execution`         | `code_execution_20250522`, `code_execution_20250825`, `code_execution_20260120` | **Developer, HE, Evaluator**                                            |
| `tool_search_tool_bm25`  | `tool_search_tool_bm25_20251119`                                                | **Developer**                                                           |
| `tool_search_tool_regex` | `tool_search_tool_regex_20251119`                                               | **Developer**                                                           |


**Injection mechanism:** Provider profile registered via `_register_harness_profile()` in a provider profile module (e.g., `agents/profiles/_anthropic.py`). Profile is resolved automatically by `create_deep_agent()` when model provider is `"anthropic"`. Agent factory files remain clean — they only call `create_deep_agent(model=<string>)`.