# Closed AD Decisions

> Extracted from `AD.md` §9 on 2026-04-13. These decisions are frozen — they will not be reopened. For active (open) questions, see `AD.md` §9.

---

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

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Three nodes (`receive_user_input`, `process_handoff`, `run_agent`), no conditional edges, linear topology. Phase gates moved to middleware hooks on handoff tools. Routing intelligence owned by calling agents via tool selection. Removed `record_handoff` and `ensure_role_state` as separate nodes (merged into `process_handoff`). Removed `route_after_agent`, `gate_phase`, and `surface_question` (routing is agent-driven, gates are middleware, HITL is SDK `ask_user`).

---

### Q5: Handoff tool use-case matrix

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

19 tools across 5 categories (Pipeline Delivery, Pipeline Return, Stage Review, Phase Review, Specialist Consultation). Naming convention `<verb>_<artifact>_to_<role>` — verb encodes blocking semantics. PM is the pipeline hub: specialists return to PM, PM delivers to next specialist. Direct specialist-to-specialist interactions for stage reviews and consultations. `reason` enum changed from phase-based (`scope_handoff|eval_request|...`) to verb-based (`deliver|return|submit|consult|coordinate|question`) — middleware dispatches on `(source, target, reason)` triple. Agent-scoped tool ownership: each agent only receives relevant tools. Artifact paths are references, not copies.

---

### Q6: Handoff record schema

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Locked field set is `project_id`, `handoff_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`, `langsmith_run_id`, `status`, `created_at`. Removed `project_thread_id` (redundant with `project_id`), `target_role_namespace` (derivable from `target_agent` in v1), and `question` (folded into `reason`). Renamed `artifact_refs` → `artifact_paths` and `run_id` → `langsmith_run_id` for clarity. Added `brief` (was in Handoff Protocol but missing from schema).

---

### Q7: Phase gate enum and approval policy

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Six phases (`scoping`, `research`, `architecture`, `planning`, `development`, `acceptance`). Two transitions require explicit user approval: `scoping→research` (PRD + eval suite review) and `architecture→planning` (design spec review). All others auto-advance. Approval mechanism is a PM-owned tool that presents stakeholder-friendly document packages to the user — prompt-driven, not a PCG interrupt. Autonomous mode toggle auto-advances all gates. Exact tool schema and document rendering delegated to implementation spec.

---

### Q8: Sandbox topology impact

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Sandbox support is backend/runtime configuration for mounted role agents and does not split roles into separate top-level assistants. Separate remotely deployed role assistants are out of scope for v1.

---

### Q9: HE vs Evaluator gate-owner boundary

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

AD owns the boundary definition (which dimension each role gates), Developer system prompt owns the routing (which tool to call when). HE gates target *harness* quality (eval science, trajectory, rubrics); Evaluator gates target *application* quality (code, SDK conventions, UI/UX). HE is conditional — only gates when a target harness exists.

---

### Q10: PCG state growth and parent-to-child context propagation

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

Child agents do not see PCG state — LangGraph maps parent-to-child by shared key names only, and the Deep Agent input schema (`_InputAgentState`) only shares `messages` with the PCG. The `run_agent` node controls what enters the child's `messages`. Unbounded growth is a persistence concern (checkpoint bloat), not a context-flooding concern. v1 mandates a cap on the handoff log (last N records, older summarized into `handoff_summary`). v2 option: move full history to LangGraph `Store`. Child agent message compaction is handled by `SummarizationMiddleware` (already in every agent stack).

---

### Q11: PCG state schema and initialization topology (refined)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-12

(1) **Topology reduced from 3 to 2 nodes** — merged `receive_user_input` into `process_handoff`; `process_handoff` handles both first invocation (no pending handoff → create synthetic handoff for PM) and subsequent invocations. (2) **`messages` redefined as user-facing I/O channel** — accumulates only lifecycle bookends (stakeholder input in, PM's final product response out); never written to during pipeline execution. (3) **`handoff_summary` removed** — cap mitigation is implementation spec territory, not a state key. (4) **`run_agent` constructs child input** — always builds a single `HumanMessage` from `pending_handoff.brief`; child never sees raw PCG `messages` list. (5) **`Command.PARENT` update contract locked** — handoff tools write to `handoff_log`, `current_agent`, `current_phase` (conditional), `pending_handoff`; never write to `messages`. (6) **Acceptance gate pattern** — `return_product_to_pm` gated by `submit_application_acceptance` (Evaluator, always required) and `submit_harness_acceptance` (HE, conditional on HE participation derived from `handoff_log`). (7) **Graph lifecycle is PM-controlled** — PM uses `ask_user` to confirm satisfaction; finishes normally → END. Three new tools added: `return_product_to_pm`, `submit_harness_acceptance`, `submit_application_acceptance`. Total tools: 23 across 6 categories.

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

| Middleware | What it adds | All 7? | Notes |
|---|---|---|---|
| `CollapseMiddleware` | Collapses consecutive read/search tool-call groups into badge summaries | Yes | Free (no LLM call). Reduces context before summarization triggers — benchmarks show 4.2x later triggering when paired with `SummarizationMiddleware`. **Do not reimplement.** Install: `pip install langchain-collapse`. Source: [github.com/johanity/langchain-collapse](https://github.com/johanity/langchain-collapse). Listed on [LangChain middleware integrations](https://docs.langchain.com/oss/python/integrations/middleware) as a community integration. |
| `ContextEditingMiddleware` | Clears old tool results → `[cleared]` when token threshold exceeded | Yes | Free (no LLM call). Mirrors Anthropic's `clear_tool_uses` behavior. **Do not reimplement.** SDK built-in: `from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit`. Pluggable `ContextEdit` strategies — default is `ClearToolUsesEdit`. Docs: [langchain.com/middleware/built-in#context-editing](https://docs.langchain.com/oss/python/langchain/middleware/built-in#context-editing). |
| `SummarizationToolMiddleware` | `compact_conversation` tool (on-demand) | Yes | SDK provides `SummarizationMiddleware` (auto-truncation) as unconditional baseline; this adds the proactive tool. Created via `create_summarization_tool_middleware(model, backend)`. |
| `ModelCallLimitMiddleware` | Hard ceiling on model API calls per thread | Yes | SDK built-in (`langchain.agents.middleware.model_call_limit`). Not included in `create_deep_agent()` by default — must be added explicitly. Counts model API calls (the cost-accruing unit), not graph steps. `exit_behavior="end"` (graceful termination). Per-role `thread_limit` values below. `run_limit` left `None` — single-run ceiling unnecessary with reasonable thread limit. |
| `StagnationGuardMiddleware` | Progress-aware call limiter (two-tier: nudge → hard stop) | Yes | Custom middleware — see design vision below. Per-role thresholds. |
| `AskUserMiddleware` | `ask_user` tool (proactive stakeholder questions) | PM, Architect | PM for stakeholder questions; Architect for interactive spec creation when user toggles the feature. Other agents do not get this. |
| `ShellAllowListMiddleware` | Shell command validation against allow-list | Conditional | Active for sandbox-backed agents. Inert for local-first. |
| Phase gate middleware | Handoff tool gate hooks | Per-agent | Agents that own gated tools receive phase gate middleware. Specifics TBD in Q8 (extended middleware). |
| `interrupt_on={}` | `HumanInTheLoopMiddleware` in tail stack | Yes | Passed as empty dict to all 7 agents — activates the middleware but registers zero interrupt rules. Inert until a future need arises. Cost is negligible (short-circuit on empty config). |

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

| Agent | `thread_limit` | Rationale |
|---|---|---|
| PM | 150 | Decisive, few calls — mostly stakeholder interaction |
| Researcher | 300 | Deep research = many read/search calls |
| Architect | 250 | Design iteration, spec writing |
| Planner | 200 | Structured planning, bounded |
| Developer | 500 | Longest — edit/test/fix cycles, subagent orchestration |
| HE | 300 | Eval design is exploratory, many tool calls |
| Evaluator | 200 | Methodical but bounded |

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

| Provider | Signal source | What it detects | Works without |
|---|---|---|---|
| `TodoProgressSignal` | `todos` state key (from `TodoListMiddleware`) | Todos not being completed or advancing | If `todos` absent → always returns `progressing=True` (no signal = no stagnation claim) |
| `ArtifactProductionSignal` | `messages` (tool call history) | No file writes or artifact-producing tool calls in recent window | If no write-like tools → always returns `progressing=True` |
| `ToolCallDiversitySignal` | `messages` (consecutive tool calls) | Same tool called with similar args repeatedly (edit→read→edit→read on same file) | Always available — reads from `messages` which every agent has |

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

| Agent | `check_interval` (estimated) | Rationale |
|---|---|---|
| PM | 20 | Shorter leash — PM should be decisive, not exploratory |
| Researcher | 40 | Longer — deep research involves many read calls |
| Architect | 35 | Design thinking is iterative |
| Planner | 30 | Planning is structured but not endless |
| Developer | 50 | Longest — coding involves many edit/test cycles |
| HE | 40 | Eval design is exploratory |
| Evaluator | 30 | Evaluation is methodical but bounded |

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

| Middleware | Why deferred |
|---|---|
| `CompactionMiddleware` (compact-middleware) | Strict superset of `SummarizationMiddleware` — 9-section structured summary, hybrid token counting, post-compaction restoration, circuit breaker, partial compaction. Cannot replace `SummarizationMiddleware` without a `disable_summarization` flag in `create_deep_agent()`. v1 uses free pre-summarization optimizers (Collapse + ContextEditing) instead. v2 will contribute the disable flag upstream and switch. **Do not reimplement.** Install: `pip install compact-middleware`. Source: [github.com/emanueleielo/compact-middleware](https://github.com/emanueleielo/compact-middleware). Listed on [LangChain middleware integrations](https://docs.langchain.com/oss/python/integrations/middleware) as a community integration. |

**Explicitly excluded from v1:**

| CLI Middleware | Why excluded |
|---|---|
| `TokenStateMiddleware` | Schema-only middleware that registers `_context_tokens` for CLI status bar. Nothing writes to it in our topology. Token counts are available in LangSmith traces. |
| `ConfigurableModelMiddleware` | Enables mid-conversation model swapping. Q11 locked thread-scoped model config — model selections are immutable for the project/thread lifespan. This middleware exists to enable the behavior we explicitly ruled out. |
| `LocalContextMiddleware` | Injects git info and directory tree into CLI context. Mounted child graphs receive context via handoff briefs, not local context scanning. |

**Backend is not middleware.** The `backend=` param is a separate top-level concern — it determines where files live and whether shell execution works. Middleware *consumes* the backend (e.g., `FilesystemMiddleware(backend=backend)`) but the backend itself is the I/O substrate. The AD already locks dual-modality backend semantics (local-first or sandbox) at §568–571.

**Q8 scope narrowed.** The baseline is now closed. Q8 continues as "extended middleware per agent" — deciding what additional custom middleware each agent requires beyond this universal baseline (e.g., which agents get phase gate middleware, which gate logic each agent enforces).

---

### Q8: Extended middleware per agent (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

The universal baseline (Q12) covers all context management, cost control, and progress-awareness middleware for every agent. Q8 decides what differs by role — specifically, which agents receive phase gate middleware and what it enforces.

**Per-agent `middleware=` slot (complete):**

| Agent | Universal (5) | + Phase Gate | + AskUser | + ShellAllowList | Total custom |
|---|---|---|---|---|---|
| PM | ✓ | ✓ | ✓ | sandbox | 7 |
| Developer | ✓ | ✓ | — | sandbox | 6 |
| Architect | ✓ | ✓ | ✓ | sandbox | 7 |
| HE | ✓ | — | — | sandbox | 5 |
| Researcher | ✓ | — | — | sandbox | 5 |
| Planner | ✓ | — | — | sandbox | 5 |
| Evaluator | ✓ | — | — | sandbox | 5 |

Universal 5 = CollapseMiddleware + ContextEditingMiddleware + SummarizationToolMiddleware + ModelCallLimitMiddleware + StagnationGuardMiddleware

**Phase gate middleware — per-agent gate logic (derived from Q9 dispatch table):**

| Agent | Gated tools owned | Gate type | What the middleware checks before allowing the tool call |
|---|---|---|---|
| PM | `deliver_prd_to_harness_engineer` (D1) | Prerequisite | `artifact_paths` non-empty with PRD artifact |
| PM | `deliver_prd_to_researcher` (D2) | Prerequisite + User Approval | `(HE, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)` |
| PM | `deliver_design_package_to_architect` (D3) | Prerequisite | `(Researcher, PM, return)` in `handoff_log` |
| PM | `deliver_planning_package_to_planner` (D4) | Prerequisite + User Approval | `(Architect, PM, return)` in `handoff_log` AND `(PM, PM, submit, accepted=true)` |
| PM | `deliver_development_package_to_developer` (D5) | Prerequisite | `(Planner, PM, return)` in `handoff_log` |
| PM | User approval recording | Self-referential | PM runs approval tool → creates `(PM, PM, submit, accepted=true/false)` record |
| Developer | `return_product_to_pm` (R5) | Acceptance stamps | `(Evaluator, PM, submit, accepted=true)` in `handoff_log`; if HE participated → also `(HE, PM, submit, accepted=true)` |
| Developer | `submit_phase_to_evaluator` (P3) | Prerequisite | `(Developer, Evaluator, announce)` with matching `phase` in `handoff_log`; `artifact_paths` non-empty |
| Architect | `submit_spec_to_harness_engineer` (S1) | Prerequisite | `artifact_paths` non-empty with spec artifacts |

4 agents (HE, Researcher, Planner, Evaluator) own no gated tools and receive no phase gate middleware.

**No additional per-role middleware beyond the above.** The universal baseline handles context management (Collapse + ContextEditing + SummarizationTool), cost control (ModelCallLimit + StagnationGuard), and SDK infrastructure (Skills, Filesystem, SubAgent, Memory, Permissions, HITL, PromptCaching). The only per-role variation is phase gate enforcement (3 agents) and stakeholder interaction (2 agents).

**Per-role parameter values (all other middleware):**

| Agent | `ModelCallLimitMiddleware.thread_limit` | `StagnationGuardMiddleware.check_interval` |
|---|---|---|
| PM | 150 | 20 |
| Developer | 500 | 50 |
| Architect | 250 | 35 |
| HE | 300 | 40 |
| Researcher | 300 | 40 |
| Planner | 200 | 30 |
| Evaluator | 200 | 30 |

---

### Q10: Tool schema contracts (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

**(1) Common parameter shape — 2 LLM-facing parameters across all 23 tools:**

| Parameter | Type | Required | Default | Source |
|---|---|---|---|---|
| `brief` | `str` | Yes | — | LLM provides: prose summary for receiving agent |
| `artifact_paths` | `list[str]` | No | `[]` | LLM provides: filesystem paths to artifacts |

**Rationale for minimal common shape:** The tool name encodes `source_agent`, `target_agent`, and `reason` (e.g., `deliver_prd_to_harness_engineer` → source=PM, target=HE, reason=deliver). `project_id` is thread-scoped context available at call time, not something the LLM needs to pass. The only decisions the LLM makes are *what to say* (`brief`) and *what to attach* (`artifact_paths`). `artifact_paths` defaults to `[]` because non-blocking tools (`ask_pm`, `announce_*`, `coordinate_qa`) often carry no artifacts. This minimizes per-tool schema variation and keeps tool descriptions focused on *when* to use the tool and *what goes in brief*, not on parameter boilerplate.

**Derived at call time (not LLM parameters):**
- `project_id` — from thread context (root thread_id)
- `source_agent` — from tool ownership (which agent is calling)
- `target_agent` — from tool name suffix (`_to_<role>`)
- `reason` — from tool name verb (`deliver`, `return`, `submit`, `consult`, `announce`, `question`, `coordinate`)

**PCG-filled (by `process_handoff`):** `handoff_id`, `langsmith_run_id`, `status`, `created_at`

**(2) Tools with additional parameters — 6 of 23 require one extra parameter:**

**Acceptance tools** — add `accepted: bool`:

| Tool | Additional param | Rationale |
|---|---|---|
| `submit_harness_acceptance` | `accepted: bool` | Gate must distinguish acceptance from rejection; `true` satisfies gate, `false` is audit record only |
| `submit_application_acceptance` | `accepted: bool` | Same |

**Phase Review tools** — add `phase: str`:

| Tool | Additional param | Rationale |
|---|---|---|
| `announce_phase_to_evaluator` | `phase: str` | QA agent must match announcement against correct plan phase |
| `announce_phase_to_harness_engineer` | `phase: str` | Same |
| `submit_phase_to_evaluator` | `phase: str` | QA agent evaluates deliverables against specific phase criteria |
| `submit_phase_to_harness_engineer` | `phase: str` | Same |

`phase` is a free-form identifier matching a phase in the Planner's implementation plan — not the 6-value PCG phase enum. The Planner defines phase identifiers; Developer and QA agents reference them. This distinction matters: the PCG phase enum (`scoping`, `research`, etc.) tracks project lifecycle; `phase` here tracks implementation plan subsections within the development stage.

**(3) Acceptance stamp contract:**

`submit_harness_acceptance` and `submit_application_acceptance` each take:

| Param | Type | Required | Description |
|---|---|---|---|
| `brief` | `str` | Yes | Reasoning — what was verified, what passed/failed, evidence summary |
| `artifact_paths` | `list[str]` | No | Paths to eval results, test outputs, evidence artifacts |
| `accepted` | `bool` | Yes | `true` = quality verified, `false` = rejected with reasoning in brief |

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

| Category | Tools | Common Only | + `accepted` | + `phase` |
|---|---|---|---|---|
| Pipeline Delivery | 5 | 5 | — | — |
| Pipeline Return | 5 | 5 | — | — |
| Acceptance | 2 | — | 2 | — |
| Stage Review | 2 | 2 | — | — |
| Phase Review | 4 | — | — | 4 |
| Consultation | 5 | 5 | — | — |
| **Total** | **23** | **17** | **2** | **4** |

**Decisions delegated to implementation spec:** Exact Pydantic/InputSchema wire types, tool description text, `phase` identifier format (free-form string vs. structured), `accepted=false` rejection feedback flow (does the agent retry? does it return to Developer?), `artifact_paths` path format conventions (absolute vs. relative, namespace prefix).

---

### Q9: Middleware dispatch table (agent primitives round)

**Status:** Closed · **Approved by:** Jason · **Date:** 2026-04-13

**(1) Complete triple enumeration — 29 distinct `(source, target, reason)` triples from 23 tools:**

**Pipeline Delivery (5 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| D1 | `(PM, HE, deliver)` | `deliver_prd_to_harness_engineer` | Prerequisite |
| D2 | `(PM, Researcher, deliver)` | `deliver_prd_to_researcher` | Prerequisite + User Approval |
| D3 | `(PM, Architect, deliver)` | `deliver_design_package_to_architect` | Prerequisite |
| D4 | `(PM, Planner, deliver)` | `deliver_planning_package_to_planner` | Prerequisite + User Approval |
| D5 | `(PM, Developer, deliver)` | `deliver_development_package_to_developer` | Prerequisite |

**Pipeline Return (5 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| R1 | `(HE, PM, return)` | `return_eval_suite_to_pm` | Ungated |
| R2 | `(Researcher, PM, return)` | `return_research_bundle_to_pm` | Ungated |
| R3 | `(Architect, PM, return)` | `return_design_package_to_pm` | Ungated |
| R4 | `(Planner, PM, return)` | `return_plan_to_pm` | Ungated |
| R5 | `(Developer, PM, return)` | `return_product_to_pm` | Prerequisite (acceptance stamps) |

**Acceptance (2 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| A1 | `(HE, PM, submit)` | `submit_harness_acceptance` | Stamp only (no gate on emission) |
| A2 | `(Evaluator, PM, submit)` | `submit_application_acceptance` | Stamp only (no gate on emission) |

**Stage Review (2 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| S1 | `(Architect, HE, submit)` | `submit_spec_to_harness_engineer` | Prerequisite |
| S2 | `(HE, Architect, return)` | `return_eval_coverage_to_architect` | Ungated |

**Phase Review (4 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| P1 | `(Developer, Evaluator, announce)` | `announce_phase_to_evaluator` | Ungated |
| P2 | `(Developer, HE, announce)` | `announce_phase_to_harness_engineer` | Ungated |
| P3 | `(Developer, Evaluator, submit)` | `submit_phase_to_evaluator` | Prerequisite |
| P4 | `(Developer, HE, submit)` | `submit_phase_to_harness_engineer` | Ungated |

**Consultation (11 triples):**

| # | Triple | Tool | Gate Type |
|---|---|---|---|
| C1 | `(Planner, HE, consult)` | `consult_harness_engineer_on_gates` | Ungated |
| C2 | `(Planner, Evaluator, consult)` | `consult_evaluator_on_gates` | Ungated |
| C3 | `(Architect, Researcher, consult)` | `request_research_from_researcher` | Ungated |
| C4 | `(HE, Researcher, consult)` | `request_research_from_researcher` | Ungated |
| C5 | `(PM, Researcher, consult)` | `request_research_from_researcher` | Ungated |
| C6 | `(HE, PM, question)` | `ask_pm` | Ungated |
| C7 | `(Researcher, PM, question)` | `ask_pm` | Ungated |
| C8 | `(Architect, PM, question)` | `ask_pm` | Ungated |
| C9 | `(Planner, PM, question)` | `ask_pm` | Ungated |
| C10 | `(Developer, PM, question)` | `ask_pm` | Ungated |
| C11 | `(Evaluator, PM, question)` | `ask_pm` | Ungated |
| C12 | `(HE, Evaluator, coordinate)` | `coordinate_qa` | Ungated |
| C13 | `(Evaluator, HE, coordinate)` | `coordinate_qa` | Ungated |

**(2) Summary by gate type:**

| Gate Type | Count | Triples |
|---|---|---|
| Ungated (pass-through) | 19 | R1–R4, S2, P1–P2, P4, C1–C13 |
| Prerequisite only | 6 | D1, D3, D5, R5, S1, P3 |
| Prerequisite + User Approval | 2 | D2, D4 |
| Stamp only (no gate on emission) | 2 | A1, A2 |

**(3) Prerequisite check details — gate logic derived from `handoff_log`, not `current_phase`:**

| Triple | What the gate checks | `handoff_log` condition |
|---|---|---|
| `(PM, HE, deliver)` | PRD finalized + eval criteria exist | `artifact_paths` non-empty with PRD artifact |
| `(PM, Researcher, deliver)` | HE Stage 1 complete + user approved scoping→research transition | `handoff_log` contains `(HE, PM, return)` record AND `(PM, PM, submit, accepted=true)` record |
| `(PM, Architect, deliver)` | Research complete | `handoff_log` contains `(Researcher, PM, return)` record |
| `(PM, Planner, deliver)` | HE Stage 2 complete + user approved architecture→planning transition | `handoff_log` contains `(Architect, PM, return)` record AND `(PM, PM, submit, accepted=true)` record |
| `(PM, Developer, deliver)` | Plan accepted | `handoff_log` contains `(Planner, PM, return)` record |
| `(Developer, PM, return)` | Acceptance stamps present | `handoff_log` contains `(Evaluator, PM, submit, accepted=true)`; if HE participated → also `(HE, PM, submit, accepted=true)` |
| `(Architect, HE, submit)` | Design spec complete | `artifact_paths` non-empty with spec artifacts |
| `(Developer, Evaluator, submit)` | Phase announced + deliverables reference plan | `handoff_log` contains `(Developer, Evaluator, announce)` with matching `phase` identifier; `artifact_paths` non-empty |

**Design decision: `current_phase` is NOT a gate authority.** `current_phase` is a PCG routing field — it tells `process_handoff` which agent to invoke next. It is a derived summary, not a gate authority. The `handoff_log` is the append-only ground truth of what actually happened. Implementation may use `current_phase` as a fast-fail optimization, but the AD does not mandate it as a gate condition.

**(4) User approval gate mechanism:**

Two transitions require explicit user approval (per Q7): `scoping→research` (D2) and `architecture→planning` (D4). The approval is recorded as a self-referential triple:

- **Triple:** `(PM, PM, submit)` — PM is both source and target.
- **`accepted` field:** `true` (user approved) or `false` (user requested revisions).
- **`brief`:** Description of what was reviewed and the decision.

**Rationale for self-referential triple:** `source_agent` is an enum of mounted child graphs. Stakeholder is not a mounted child graph — adding it to the enum pollutes a routing enum with a non-agent entity. The PM runs the approval tool and records the outcome; the `brief` carries the human-readable semantics. The triple is for middleware dispatch, not narrative.

**Prerequisite gates on D2 and D4** check `handoff_log` for `(PM, PM, submit, 