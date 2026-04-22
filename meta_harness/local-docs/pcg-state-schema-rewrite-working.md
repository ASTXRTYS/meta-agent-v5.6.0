# PCG State Schema Rewrite — Working Analysis (OQ-HO)

> **Owner:** Cascade · **Status:** Working analysis · **Date:** 2026-04-22  
> **Purpose:** Record of reasoning for the clean-slate rewrite of `docs/specs/pcg-data-contracts.md` per `AD.md` Open Question `OQ-HO`. This is a `local-docs/` coding-agent reference, not a shipped spec. Intended to be archived (or deleted) once the Phase 2 AD + spec pass lands.  
> **Consumers:** Jason (review), future Cascade sessions (audit of trajectory).
> **Historical note:** Sections §1–§10 preserve the initial pre-review reasoning, including the explicit-invocation hypothesis that was later corrected. Section §11 records the same-day correction that replaced that hypothesis with the mounted-subgraph `Command.PARENT` architecture now reflected in `AD.md` and the Phase 2 specs. Treat §11 and the canonical docs as authoritative for current design.

## 0. Executive Summary

The current `pcg-data-contracts.md` spec has a structurally broken invariant (`add_messages` does not admit `HandoffRecord` objects), inherits a two-node topology whose coordination key (`pending_handoff`) doesn't pay its rent, and expresses none of the Vision-era headless / artifact / optimization requirements. The **initial** chosen direction in this working analysis was a thin dispatcher, Store-first, typed-channel PCG with explicit child invocation. Same-day review later invalidated the explicit-invocation part; §11 records the correction to a 1-node dispatcher plus 7 mounted role subgraphs, while preserving the reducer/channel/Store conclusions that still stand. `Q6` keeps its schema.

## 1. SDK Pre-Work Findings (source-verified)

### 1.1 `add_messages` is message-only — current spec's invariant is false

`add_messages` (`.venv/lib/python3.11/site-packages/langgraph/graph/message.py:61-244`) coerces both `left` and `right` through `convert_to_messages` at lines 194-201:

```python
left = [message_chunk_to_message(cast(BaseMessageChunk, m)) for m in convert_to_messages(left)]
right = [message_chunk_to_message(cast(BaseMessageChunk, m)) for m in convert_to_messages(right)]
```

`_convert_to_message` (`.venv/lib/python3.11/site-packages/langchain_core/messages/utils.py:675-730`) accepts only:

- `BaseMessage` (passed through unchanged)
- `Sequence` of `(role, template)` (coerced to message)
- `str` (treated as `human` message content)
- `dict` with mandatory `role`/`type` and `content` keys (coerced)

Any other type raises:

```python
else:
    msg = f"Unsupported message type: {type(message)}"
    raise NotImplementedError(msg)
```

**Consequence.** `pcg-data-contracts.md §3 Invariant 4` — "`handoff_log` uses `add_messages` for append-only semantics … `HandoffRecord` objects implement the message protocol (have an `id` field)" — is structurally false. A `HandoffRecord` dataclass / `TypedDict` / Pydantic model will raise `NotImplementedError` on the first append. The `id` field on its own is not sufficient to pass `convert_to_messages`. This alone is sufficient to require a rewrite.

### 1.2 `Command.PARENT` is a dict-keyed update applied via channel reducers

`Command` (`.venv/lib/python3.11/site-packages/langgraph/types.py:652-702`) holds `graph`, `update`, `goto`, `resume`. `_update_as_tuples` (lines 687-700) decomposes the update into `(channel_name, value)` tuples; Pregel applies each value to the parent state channel via that channel's reducer. The PARENT sentinel is `"__parent__"` (line 702).

**Consequence.** Custom reducers (`operator.add`, merge-dict, overwrite) are fully valid for non-message channels. A plain `Annotated[list[HandoffRecord], operator.add]` append-only reducer is the idiomatic choice for `handoff_log`.

### 1.3 `_InputAgentState` is minimal and message-only

Defined at `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`:

```python
class _InputAgentState(TypedDict):
    """Input state schema for the agent."""
    messages: Required[Annotated[list[AnyMessage | dict[str, Any]], add_messages]]
```

Deep Agents imports it at `.reference/libs/deepagents/deepagents/graph.py:14` and uses it as the input schema of every `create_deep_agent()`-returned compiled graph.

**Initial consequence (later corrected in §11.2).** At this point in the analysis, I treated mounted-subgraph input filtering as a convention risk. The same-day correction later established that the Deep Agent's declared `_InputAgentState` / `_OutputAgentState` schemas make mounted subgraphs structurally isolating for this use case.

### 1.4 `SubAgentMiddleware` is an explicit-invocation pattern, not a peer-handoff topology

`SubAgentMiddleware` (`.reference/libs/deepagents/deepagents/middleware/subagents.py:335-391`) does not add subagents as `StateGraph` nodes. It builds a `task` tool whose handler calls `subagent.invoke(subagent_state)` (line 375) or `await subagent.ainvoke(subagent_state)` (line 390) with an explicitly-constructed input dict, then packages the last message into a `ToolMessage` inside a `Command(update=...)` for the parent.

This is the **production-reference explicit-invocation pattern in the SDK itself**: parent invokes child explicitly, parent state never structurally flows, child I/O is controlled at the invocation site.

**Initial consequence (later corrected in §11.1–§11.2).** I treated this as evidence against mount-as-subgraph. The corrected conclusion is narrower: `SubAgentMiddleware` is the right reference for ephemeral stateless subagent-as-tool dispatch, but not for persistent peer handoff between mounted role graphs that rely on `Command.PARENT`.

### 1.5 Open SWE is a single Deep Agent — no multi-agent PCG exists as a production mirror

`get_agent()` at `.reference/open-swe/agent/server.py:190-318` returns `create_deep_agent(...).with_config(config)`. No PCG, no subgraph mounting, no `Command.PARENT`. Thread metadata (sandbox_id, github_token_encrypted, linear_project_id) rides on `config["configurable"]` and `config["metadata"]`, consumed by agent tools.

**Consequence.** Meta Harness's PCG is net-new — no production multi-agent-PCG reference to mirror. But Open SWE's thread-metadata pattern (identity and cross-ingress context on `config`, not in graph state) is the right mental model for ingress-source identity in the headless-ready-infra policy.

### 1.6 No `langgraph-supervisor` / `langgraph-swarm` installed

`.venv/lib/python3.11/site-packages/` has no supervisor/swarm packages. The multi-agent pattern is hand-rolled.

## 2. Honest Defense — What Q10 / Q11 Got Right

Credit where due. The closed decisions (`DECISIONS.md` Q10, Q11) correctly established:

1. **Deterministic coordination, no LLM in coordination nodes.** Correct structural choice; preserved.
2. **Handoff tools return `Command.PARENT`; no direct peer invocation.** Correct; preserved.
3. **Phase gates as middleware hooks on handoff tools, not conditional edges.** Correct; preserved.
4. **Each role has a stable checkpoint namespace.** Correct; preserved.
5. **`messages` as user-facing I/O channel (lifecycle bookends), not a conversation buffer.** Correct principle; preserved, but the mechanism (using `messages` key at PCG level) needs reconsideration given headless-ready policy.
6. **Acceptance-stamp pattern (Evaluator always, HE conditional).** Correct policy; the mechanism (`handoff_log` scanning) is what's wrong, not the policy.
7. **PM-controlled graph lifecycle (`ask_user` + natural finish).** Correct; preserved.
8. **Handoff brief as the ONLY thing the child sees; child constructs its own context from `artifact_paths`.** Correct; preserved and strengthened by structural dispatcher isolation.

The rewrite keeps all of these. The pieces that need replacement are the mechanisms that implement principles 5 and 6, plus the `add_messages`-on-handoff-log mistake, plus the coordination-cursor (`pending_handoff`) that is an artifact of the two-node topology rather than a structural necessity.

## 3. Diagnosis — Each Weak Point Validated

| # | Weak point | SDK verification | Verdict |
|---|---|---|---|
| 1 | `handoff_log` uses `add_messages` reducer on `HandoffRecord` objects | `convert_to_messages` raises `NotImplementedError` for non-message types (see §1.1) | **Broken — must replace with `operator.add` or typed append reducer.** |
| 2 | `pending_handoff` is an execution cursor | With one dispatcher node, `handoff_log[-1]` is authoritative; no cursor needed | **Dead weight — remove.** |
| 3 | Child input isolation via `input_schema=_InputAgentState` on `add_node` | Works but is invocation-time filtering, convention-enforced, trivially forgettable | **Replace with structural dispatcher (invoke-from-function); see §1.4.** |
| 4 | `current_phase` as `Literal[...]` denormalizes `handoff_log` | Spec does not state the denormalization relationship; latent divergence risk | **Keep as a first-class channel with explicit documentation that it is derived from `handoff_log`; invariant added.** |
| 5 | `messages` channel carrying only lifecycle bookends | Inherits LangChain convention with non-standard semantics; headless ingress can produce multiple user-facing messages per project | **Keep the `messages` channel (LangGraph I/O conduit), drop the "lifecycle bookend" invariant as too restrictive for headless use. Document it as "the surfaced user↔PM channel." Child agents still do not see it.** |
| 6 | Acceptance gates scan `handoff_log` for stamps | Couples gate logic to audit log structure; v2 "move handoff_log to Store" silently breaks gates | **First-class `acceptance_stamps` channel keyed by stamp type. Gates read the channel, not the log.** |
| 7 | No artifact manifest / trendline / project-registry surfaces | Vision D1/D10/D12 + headless-ready policy demand cross-surface artifact legibility that the current schema cannot express | **Introduce Store-backed namespaces for artifact manifest, HE-owned optimization trendline, project registry. PCG state stays thin.** |

## 4. Requirements (Vision + Headless-Ready Infra)

1. **Cross-modality continuity.** `project_thread_id` is the canonical handle that a TUI / web / Slack / Discord / email / GitHub / Linear surface can resolve to the same project state. Ingress source identity lives in `config["metadata"]`, not in PCG state. Open SWE's pattern (§1.5) is the model.
2. **Artifact-first legibility.** Any surface — including a headless observer with no PCG state access — must be able to enumerate artifacts for a project by type, owner, and timestamp. This requires a durable, queryable artifact index.
3. **Optimization loop visibility without info leakage.** During the Developer phase, a public trendline must exist for web / headless consumption. Developer must remain blind to rubrics, judge configs, held-out data. This means the trendline is a HE-owned Store namespace with permissions excluding the Developer's filesystem.
4. **PM-session observability into active projects.** A `pm_session` thread must be able to render "project X is in phase Y, last handoff was Z, artifact count is N" without joining the project thread. This is a Store query on a `project_registry` namespace, updated by PCG on each handoff.
5. **Source-neutral audit trail.** `HandoffRecord` metadata must be renderable by any surface without UI assumptions. No UI-specific fields in the record; ingress source lives on `config["metadata"]`.
6. **Approval gates degrade to any ingress adapter.** `AskUserMiddleware` + the two approval-gate document-review tools must work over Slack interactive blocks, email reply threading, Discord slash commands, not just web-client interrupts. This is an `interrupt()` contract concern, not a PCG-state concern — but the schema must not assume a web client is present.
7. **Headless infra exists but default-off.** All ingress adapters (Slack, Discord, email, GitHub, Linear) are scaffolded in v1; the feature flag gates public exposure. PCG state and `HandoffRecord` schema must be complete for headless use even if headless ingress is not wired on day-one.

## 5. Internal Hill-Climb — Candidate Topologies Considered

For completeness, the alternatives weighed internally before committing.

**Historical note.** Candidate B and §6 preserve the initial pre-review design and are retained as trajectory record only. They are superseded by §11 Phase 2 Correction; do not implement from §5–§6 without reading §11.

**Candidate A — 2-node topology (`process_handoff` + `run_agent`), tightened.** Fixes reducer abuse (§3 row 1) and child-isolation convention (§3 row 3) but keeps `pending_handoff` alive as an inter-node signaling channel. Lowest migration cost; highest ceiling of "this is still clearly ceremonial." Rejected: `pending_handoff` is an artifact of the topology, not a requirement of the problem. The topology itself is the problem.

**Candidate B — 1-node dispatcher + typed channels + Store-first.** Single `dispatch_handoff` node reads `handoff_log[-1]`, invokes child via explicit `role_graph.ainvoke(constructed_input, config)`, writes state updates on return. `pending_handoff` eliminated. `acceptance_stamps` as first-class channel. Store holds artifact manifest, trendline, registry. **Chosen.** Rationale: (a) matches Deep Agents' own SubAgentMiddleware pattern (§1.4); (b) eliminates convention-enforced invariants in favor of structural ones; (c) Store-first naturally expresses headless-ready-infra policy without contorting PCG state; (d) lowest cognitive overhead for a future peer developer reading the graph.

**Candidate C — 0-node "tool-routed" topology, child commands drive everything.** Parent is a minimal shell; child `Command.PARENT` commands route between children directly. Rejected: loses the deterministic recording of handoffs, loses the middleware-friendly central choke point for gates, and the LangGraph runtime still requires at least one node to execute. Candidate B is the minimal viable topology.

**Candidate D — Reinstate mount-as-subgraph with strict input filtering.** Use `builder.add_node("pm", pm_compiled, input_schema=_InputAgentState)` for each role. Rejected: (a) invocation-time filter is a convention; (b) harder to inject per-role runtime config (checkpoint namespace, LangSmith metadata); (c) Deep Agents' own SubAgentMiddleware does not use this pattern — we should inherit the canonical production shape.

## 6. Chosen Direction — Full Specification

### 6.1 Topology

```txt
START → dispatch_handoff
          │
          ├─ on first invocation (empty handoff_log):
          │     synthesize initial handoff from user input → invoke PM
          │
          ├─ on child's Command(graph=PARENT, goto="dispatch_handoff", update={...}):
          │     parent state absorbs the update (handoff_log append, current_*,
          │     acceptance_stamps), dispatch_handoff re-enters with fresh state,
          │     reads handoff_log[-1], invokes target role graph
          │
          └─ on child natural termination (no handoff):
                dispatch_handoff receives child's final messages, writes to PCG
                messages channel, returns with no goto → graph ENDs
```

One node. Zero conditional edges. One edge (`START → dispatch_handoff`). Re-entry is driven by child-emitted `Command.PARENT`. Graph termination is driven by a child returning without firing a handoff tool (natural PM completion).

### 6.2 `ProjectCoordinationState` (typed channels)

```python
class ProjectCoordinationState(TypedDict):
    # User-facing I/O conduit (LangGraph convention). Child agents NEVER read this.
    messages: Annotated[list[AnyMessage], add_messages]

    # Immutable project identity
    project_id: str
    project_thread_id: str

    # Append-only audit trail, typed reducer, idiomatic
    handoff_log: Annotated[list[HandoffRecord], operator.add]

    # Current-state denormalization (derived from handoff_log; fast-path for middleware)
    current_agent: Literal[
        "project_manager", "harness_engineer", "researcher",
        "architect", "planner", "developer", "evaluator",
    ]
    current_phase: Literal[
        "scoping", "research", "architecture",
        "planning", "development", "acceptance",
    ]

    # First-class acceptance channel (no more handoff_log scanning)
    acceptance_stamps: Annotated[
        dict[Literal["harness", "application"], HandoffRecord],
        _merge_stamps_reducer,
    ]
```

### 6.3 What moves to `Store` (durable, cross-thread)

| Store namespace | Owner | Consumers | Purpose |
|---|---|---|---|
| `projects/{project_id}/artifact_manifest` | Any agent (via middleware or tool) on artifact production | Web app, TUI, headless ingress, PM session | Single queryable index of artifacts: type, owner, path, created_at, public/private. Replaces walking role filesystems + `handoff_log.artifact_paths`. |
| `projects/{project_id}/optimization_trendline` | Harness Engineer exclusively | Web app, headless ingress, PM session. **NOT the Developer** (permissions exclude this namespace from Developer's filesystem scope). | Sanitized iteration-by-iteration trend data for Vision D10/D12 visibility without leaking rubrics/judges/held-out data. Addresses `OQ-H3`. |
| `projects_registry` | PCG `dispatch_handoff` on each handoff | PM session threads, web app project list, any ingress adapter | Compact record per project: `project_id`, `project_thread_id`, `current_phase`, `current_agent`, `last_handoff_at`, `artifact_count`. Addresses `OQ-H1`. |

Store access goes through the LangGraph runtime boundary (`langgraph.store.base.BaseStore`); in local dev `SqliteSaver`-backed checkpointer pairs with `InMemoryStore`, in LangGraph Platform the managed store auto-resolves.

### 6.4 `HandoffRecord` wire format

Retained almost unchanged from `AD.md §4 Data Contracts` / `DECISIONS.md` Q6, with one addition pulled up from Q8 extension:

```python
class HandoffRecord(TypedDict):
    project_id: str
    project_thread_id: str
    handoff_id: str
    source_agent: AgentName
    target_agent: AgentName
    reason: Literal["deliver", "return", "submit", "consult", "announce", "coordinate", "question"]
    brief: str
    artifact_paths: list[str]
    langsmith_run_id: str | None
    status: Literal["queued", "running", "completed", "failed"]
    created_at: str  # RFC3339
    accepted: NotRequired[bool | None]  # only populated on acceptance/approval records
    phase: NotRequired[Literal[...]]    # only populated on phase-transitioning records
```

Implementation may use a Pydantic model instead of a TypedDict; either satisfies this contract. The `phase` field is NEW (added to disambiguate phase transitions from coordination records without walking the reason enum; supports `current_phase` denormalization safely).

### 6.5 `Command.PARENT` update contract

Every handoff tool returns:

```python
Command(
    graph=Command.PARENT,
    goto="dispatch_handoff",
    update={
        "handoff_log": [handoff_record],       # append via operator.add
        "current_agent": target_agent,          # overwrite
        "current_phase": new_phase_if_any,      # overwrite; omit if no transition
        # Acceptance-stamp tools additionally write:
        # "acceptance_stamps": {"application": stamp_record} or {"harness": ...}
    }
)
```

No `pending_handoff`. No writes to `messages`. Artifact manifest updates are a Store write, not a state update.

### 6.6 Child input isolation — structural

`dispatch_handoff` is a plain python function:

```python
async def dispatch_handoff(
    state: ProjectCoordinationState,
    config: RunnableConfig,
    runtime: Runtime[ProjectCoordinationContext],
) -> dict | None:
    # 1. Synthesize initial handoff on first entry, else read from handoff_log
    handoff = state["handoff_log"][-1] if state["handoff_log"] else _synthesize_initial(state)

    # 2. Select role graph from in-process registry
    role_graph = ROLE_GRAPHS[handoff["target_agent"]]

    # 3. Construct child input explicitly (structural isolation)
    child_input = {"messages": [HumanMessage(content=handoff["brief"])]}

    # 4. Propagate checkpoint namespace + LangSmith metadata via config
    child_config = {
        **config,
        "configurable": {
            **config["configurable"],
            "checkpoint_ns": handoff["target_agent"],
        },
    }

    # 5. Invoke child graph. Its Command.PARENT emissions bubble back automatically.
    result = await role_graph.ainvoke(child_input, child_config)

    # 6. If we reach here without a PARENT command having already routed us back,
    #    the child finished naturally (PM completing). Write its last message to
    #    the user-facing messages channel and terminate.
    if result.get("messages"):
        last = result["messages"][-1]
        if isinstance(last, AIMessage):
            # Project-registry update
            await _update_project_registry(state, runtime.store)
            return {"messages": [last]}

    return None
```

**Why this eliminates `OQ-H4`.** Parent `ProjectCoordinationState` is never passed to the child. The child receives a freshly-constructed dict with only a `messages` key. There is no `input_schema` filter to forget, no convention to enforce, no invariant to document — the isolation is structural.

### 6.7 Trace hierarchy preservation

LangGraph Pregel's callback manager (`pregel/_algo.py:694-698`) propagates child run context via `RunnableConfig`. Passing `config` into `role_graph.ainvoke(child_input, child_config)` preserves the run-tree relationship — the child's run appears nested under `dispatch_handoff`'s run in LangSmith. `AD.md §4 Local Development Tracing — Configuration and Architecture` still holds unchanged.

## 7. Resolutions by Open Question

| OQ | Resolution |
|---|---|
| `OQ-HO` | Entire rewrite; chosen direction in §6. |
| `OQ-H2` | `pending_handoff` removed. With one dispatcher node, `handoff_log[-1]` is authoritative. |
| `OQ-H4` | Child isolation is now structural (§6.6). The convention-enforced `input_schema=_InputAgentState` invariant is retired. |
| `OQ-H1` | Folded in. `projects_registry` Store namespace (§6.3) provides PM-session visibility without per-thread joining. |
| `OQ-H3` | Folded in. `optimization_trendline` Store namespace (§6.3) is HE-owned, Developer-blind, web/headless consumable. |

## 8. Downstream Impact

### `docs/specs/handoff-tools.md`

- Uniform tool return shape: all 23 tools return `Command(graph=PARENT, goto="dispatch_handoff", update={...})`.
- Acceptance tools (`submit_application_acceptance`, `submit_harness_acceptance`) additionally include `acceptance_stamps` in their update dict, not implicit handoff_log stamp records.
- Acceptance gate logic on `return_product_to_pm`: reads `state.acceptance_stamps`, checks `"application"` always and `"harness"` conditionally via a helper that scans `handoff_log` for HE participation (no `has_target_harness` key, as currently).
- Artifact-producing tools additionally write to `artifact_manifest` Store namespace. Recommended: this is a Store-write side-effect at the tool implementation layer or encapsulated in a thin middleware, not a per-tool contract.
- Tool matrix + ownership tables unchanged.

### `docs/specs/repo-and-workspace-layout.md`

- `graph.py` factory simpler: one `StateGraph`, one node, one edge (`START → dispatch_handoff`).
- Role graphs held in a dispatch registry (`ROLE_GRAPHS: dict[AgentName, Pregel]`) — **not** mounted as nodes.
- Role factories unchanged at their own module boundaries.

### `AD.md §4`

- `LangGraph Project Coordination Graph` section: topology changes from "2 nodes" to "1 node + registry," sequence diagram updated accordingly.
- `PCG State Schema (decisions)`: bullet list updated to reflect chosen channels, drop `pending_handoff`, add `acceptance_stamps`, reference Store namespaces.
- `Handoff Protocol → Command.PARENT Update Contract (decisions)`: drop `pending_handoff` from update shape, document `acceptance_stamps`.
- `Data Contracts (decisions)`: add `phase` field, add `accepted: NotRequired[bool|None]`.
- `Observability, Tracing, and Studio` unchanged.

### `DECISIONS.md`

Supersede (do not delete):

- **Q4 (PCG node set).** Mark superseded 2026-04-22 by `OQ-HO` resolution. Node count: 3 → 2 → 1. Dispatcher topology inherited from Deep Agents' `SubAgentMiddleware` invocation pattern (`subagents.py:335-391`).
- **Q10 (PCG state growth + parent-to-child context propagation).** Mark superseded. Child-isolation now structural (dispatcher-constructed input, no schema-filter convention). Handoff-log cap strategy deferred: v1 retains the in-state `handoff_log` with a cap; v2 migration to Store is a performance concern, not a correctness concern, because gates now read `acceptance_stamps` not `handoff_log`.
- **Q11 (PCG state schema + initialization topology).** Mark superseded. New state schema in §6.2, new init topology in §6.1.

Keep (unchanged):

- **Q3 (Handoff wrapper implementation).** `Command.PARENT` is still the mechanism.
- **Q5 (Handoff tool use-case matrix).** Tool ownership and routing unchanged.
- **Q6 (HandoffRecord schema).** Core field set unchanged; adds `phase` and promotes `accepted` from Q8 extension to first-class `NotRequired` field.
- **Q7 (Phase gate enum + approval policy).** Phase enum and approval gates unchanged.
- **Q8 (Sandbox topology impact), Q9 (HE vs Evaluator boundary).** Unchanged.

## 9. Governance Compliance

- Phase 1 artifact is this file at `meta_harness/local-docs/pcg-state-schema-rewrite-working.md`. Requires a one-line `AGENTS.md` pointer if retained past Phase 2. After Phase 2 lands, this file is archived (moved to `docs/archive/` with a pointer stub) or deleted per co-modification rule.
- AD lands first (Phase 2 step 2). Specs follow (steps 3–5). §9 Decision Index + CHANGELOG bump co-modified (steps 6–7).
- Closed decisions in `DECISIONS.md` are superseded in-place with status notes pointing to the new AD sections — not deleted — per deprecation rule.
- No silent renames: every touched spec gets `last_synced: 2026-04-22` bumped.

## 10. Phase 2 Checklist

1. [x] Add `AGENTS.md` one-line pointer to this working file.
2. [x] Supersede `DECISIONS.md` Q4 / Q10 / Q11 entries.
3. [x] Rewrite `AD.md §4` sub-sections.
4. [x] Rewrite `docs/specs/pcg-data-contracts.md`.
5. [x] Update `docs/specs/handoff-tools.md`.
6. [x] Update `docs/specs/repo-and-workspace-layout.md`.
7. [x] Close `OQ-HO` / `OQ-H1` / `OQ-H2` / `OQ-H3` / `OQ-H4` in `AD.md` §Open Questions.
8. [x] Update `AD.md §9 Decision Index → Derived Specs` `last_synced`.
9. [x] Append `CHANGELOG.md` entry.
10. [x] Present at Phase 2 review gate.

## 11. Phase 2 Correction (2026-04-22 — post review)

> **Why this section exists.** Jason asked whether the Phase 2 rewrite accounted for role agents being `create_deep_agent()` graphs. That question surfaced a real hole in Candidate B: the dispatcher-invokes-child pattern I borrowed from `SubAgentMiddleware` is structurally incompatible with our peer-handoff protocol. Below is the verified SDK evidence, the corrected architecture, and the surgical changes required to repair Phase 2 without re-doing the whole rewrite.

### 11.1 What I got wrong

Candidate B's `dispatch_handoff` invokes role graphs via `role_graph.ainvoke(child_input, child_config)` from inside a plain Python node, then claims "parent state physically cannot reach the child" and "Command.PARENT bubbles back through the parent Pregel loop." Both claims were unsound:

1. **`.ainvoke()` breaks `Command.PARENT` bubbling.** `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:56-59`:
   ```python
   def map_command(cmd: Command) -> Iterator[tuple[str, str, Any]]:
       if cmd.graph == Command.PARENT:
           raise InvalidUpdateError("There is no parent graph")
   ```
   And `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_retry.py:136-138`:
   ```python
   elif cmd.graph == Command.PARENT:
       exc.args = (replace(cmd, graph=_checkpoint_ns_for_parent_command(ns)),)
   # bubble up
   ```
   `Command.PARENT` is handled by re-raising `ParentCommand` from the child Pregel so the parent Pregel can catch it at the next checkpoint-namespace level. That path **only exists when the child is running as a subgraph node inside a parent Pregel's namespace hierarchy.** A child invoked via `.ainvoke()` runs in its own top-level Pregel context — there is no parent to bubble to, so `map_command` raises `InvalidUpdateError` immediately.

2. **The cited canonical pattern doesn't apply.** `SubAgentMiddleware` at `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/subagents.py:335-376` uses `subagent.invoke(state)` from inside a tool and packages the result as a `ToolMessage` in a plain `Command(update=...)` back to the caller. It is an **ephemeral-stateless-subagent-as-tool** pattern, equivalent to Option A in `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:86-90` which Jason already rejected for Meta Harness. It gives no persistent per-role checkpoint state and no peer-to-peer handoff semantics.

3. **Structural isolation via dispatcher was a category error.** There is no in-Pregel mechanism that lets a plain Python node invoke a compiled child and have the child emit `Command.PARENT` back. The mechanism is subgraph mounting, full stop.

### 11.2 What the SDK actually gives us (verified)

Two compile-time facts make the corrected architecture clean:

1. **`create_deep_agent()` declares its own input/output schemas.** `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/graph.py:236`:
   ```python
   ) -> CompiledStateGraph[AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT]]:
   ```
   - **Input schema** is `_InputAgentState` (messages only, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`).
   - **Output schema** is `_OutputAgentState` (`messages` + optional `structured_response` only, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:364-368`). `todos`, `files`, `jump_to`, `StagnationGuardState._model_call_count`, skills/memory middleware state — all marked `PrivateStateAttr` or `OmitFromOutput` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:346-347`) and dropped structurally at compile time.

2. **LangGraph respects the subgraph's declared input schema on `add_node`.** `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1306-1314`:
   ```python
   elif node is not None:
       input_schema = node.input_schema if node else self.builder.state_schema
       input_channels = list(self.builder.schemas[input_schema])
   ```
   When we `builder.add_node("project_manager", pm_compiled_graph)`, LangGraph reads the subgraph's own `input_schema` (`_InputAgentState`) and only passes the shared `messages` channel from parent to child. The `input_schema=_InputAgentState` parameter on `add_node` that Candidate D worried about is not a convention we have to remember to pass — it's already baked into the compiled Deep Agent.

Taken together: **mount-as-subgraph is actually structurally isolating in the way Candidate B claimed its dispatcher pattern would be, because the Deep Agent SDK itself does the filtering at its own compile time.** My rejection of Candidate D in §5 was based on a false premise about how `input_schema` propagates.

### 11.3 One residual concern: `messages` parent↔child overlap

The Deep Agent's `_OutputAgentState` includes `messages` as `Required`. When a mounted child natural-completes, its final state projection (just `messages` + optional `structured_response`) is applied to parent state via parent's reducers. Parent has `messages` with `add_messages`. Child's full conversation history would append to parent's `messages`.

This is the only remaining leakage path after mounting. The fix is a small extension of the handoff protocol, not a state-schema change:

**Invariant: every role turn terminates by emitting `Command(graph=Command.PARENT, ...)`. Natural completion is an error condition that middleware catches.**

Specialists already satisfy this trivially — their final tool call is a handoff tool which emits `Command.PARENT`. The PM needs one new tool for the terminal case:

- **`finish_to_user(final_response: str)`** (Category 7 in `docs/specs/handoff-tools.md`, new). PM-only. Returns `Command(graph=Command.PARENT, goto=END, update={"messages": [AIMessage(final_response)]})`. Does not append to `handoff_log` — lifecycle bookend, not a handoff record.

With this rule, the child's in-progress `messages` state remains in the child's checkpoint namespace; only the explicit `Command.PARENT.update` fields reach the PCG. The `messages` append that lands on PCG state is specifically the PM's final AIMessage, delivered intentionally through `finish_to_user`.

Natural completion protection can be enforced by a thin final-turn-guard middleware: if the agent's last AIMessage has no tool call, re-prompt. This is a prompt hygiene safety net, not an architectural pillar. Verified once in `docs/specs/handoff-tools.md §1.3` (new).

### 11.4 Corrected topology

```
START → dispatch_handoff ──┐
                           │ Command(goto="project_manager")
                           ▼
         ┌──── project_manager (mounted Deep Agent subgraph) ────┐
         │                                                        │
         │ child-emitted Command(graph=PARENT, goto="dispatch_handoff", update={...})
         │                                                        │
         └────────────────────────────────────────────────────────┘
                           │
                           ▼
                    dispatch_handoff (re-entered)
                           │ Command(goto=next_role)
                           ▼
                   (same pattern for all 7 roles)

        Terminal case: PM calls finish_to_user →
        Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})
        → PCG absorbs messages, terminates.
```

- **8 nodes**: `dispatch_handoff` + 7 mounted role subgraph nodes (`project_manager`, `harness_engineer`, `researcher`, `architect`, `planner`, `developer`, `evaluator`).
- **Zero conditional edges.** All routing is driven by `Command(goto=...)` emissions. Dispatcher reads `handoff_log[-1].target_agent` and routes.
- `ROLE_GRAPHS: dict[str, CompiledStateGraph]` registry still exists, but is now consumed at graph construction time (`builder.add_node(name, role_graph)`) rather than at dispatcher invocation time.

### 11.5 Corrected dispatcher signature

```python
async def dispatch_handoff(
    state: ProjectCoordinationState,
    runtime: Runtime[ProjectCoordinationContext],
) -> Command:
    """Coordination node — only emits Command(goto=...). Never invokes children directly."""

    # First invocation: synthesize initial handoff from stakeholder input on messages channel.
    if not state["handoff_log"]:
        initial = _synthesize_initial_handoff(state, runtime)
        await _upsert_projects_registry(state, initial, runtime.store)
        return Command(
            goto=initial["target_agent"],
            update={
                "handoff_log": [initial],
                "current_agent": initial["target_agent"],
                "current_phase": initial.get("phase", "scoping"),
            },
        )

    # Re-entry after a child emitted Command.PARENT: handoff_log[-1] is authoritative.
    active = state["handoff_log"][-1]
    await _upsert_projects_registry(state, active, runtime.store)
    return Command(goto=active["target_agent"])
```

The dispatcher is a pure routing function. It never invokes role graphs — LangGraph does that through the normal Pregel loop once `Command(goto=<role>)` is emitted. Role graphs' own `input_schema=_InputAgentState` declares only `messages` flows in from parent.

### 11.6 What survives from the Phase 2 rewrite

Everything from §6.2 (state schema), §6.3 (Store namespaces), §6.4 (HandoffRecord wire format), §6.5 (Command.PARENT update contract) is unchanged. The delta is strictly topology + terminal-exit rule:

| Survives unchanged | Corrected |
|---|---|
| `handoff_log: Annotated[list[HandoffRecord], operator.add]` | — |
| `acceptance_stamps: Annotated[dict[...], _merge_stamps_reducer]` first-class channel | — |
| Gate on `return_product_to_pm` reads `acceptance_stamps`, not `handoff_log` scan | — |
| `pending_handoff` removed | — |
| `HandoffRecord.phase` / `.accepted` optional fields | — |
| `Store` namespaces: `artifact_manifest`, `optimization_trendline`, `projects_registry` | — |
| Developer excluded from `optimization_trendline` via filesystem permissions | — |
| — | PCG is 8 nodes (1 dispatcher + 7 mounted role subgraphs), not 1 node + registry |
| — | Dispatcher emits `Command(goto=<role>)`; never calls `.ainvoke()` on a role graph |
| — | Child isolation is structural via `create_deep_agent()`-declared `_InputAgentState` / `_OutputAgentState`, not via `input_schema=` on `add_node` nor via dispatcher-constructed inputs |
| — | New Category 7 (Terminal Emission) tool: `finish_to_user` (PM-only; 24th tool total) |
| — | New middleware requirement: final-turn-guard — every role's last AIMessage must have a tool call (handoff tool or `finish_to_user`) |

### 11.7a Architecture Watch-List (Frontier Work, Requires Periodic Revisit)

This architecture is frontier work. No public production reference class exists for multi-agent peer-handoff coordination with persistent per-role checkpoint state, Command.PARENT bubbling, and QA-gate acceptance enforcement. Production examples exist behind enterprise NDAs at LangChain, Anthropic, and OpenAI solutions teams. Public references (`deepagents_cli`, `open-swe`, `langgraph-supervisor`, `langgraph-swarm`) are adjacent but shallower than our coordination depth.

The discipline: treat this architecture as "best-we-have-at-this-moment." When any of the following signals hit, STOP and schedule a deliberate architecture review against the current design. Do NOT defend the current design out of ego or sunk cost.

**Framework-release signals.**

1. **LangGraph ships a "private shared channel" or "terminal-only-emission" subgraph mode.** Would obsolete the `finish_to_user` + final-turn-guard pair. Migrate and consider upstreaming the final-turn-guard pattern as a LangChain contribution.
2. **Deep Agents SDK changes `_InputAgentState` / `_OutputAgentState` type parameters or `PrivateStateAttr` semantics.** Load-bearing for our structural isolation claim. Re-verify on every `deepagents` upgrade.
3. **LangChain publishes production multi-agent peer-handoff guidance** (blog posts from Harrison Chase, conference talks, `langgraph-supervisor` / `langgraph-swarm` feature releases). Cross-read line-by-line against our design. If they've solved a problem more elegantly, steal the pattern.

**Scaling / runtime signals.**

4. **PM token cost or response latency balloons.** Hub-and-spoke coordination has known limits (bottleneck, context bloat). If PM becomes a friction point, evaluate decentralization patterns: event-bus coordination, topic-based subscriptions, CRDT-like state merging.
5. **`handoff_log` grows past ~1000 entries in long-running projects.** Trim-to-Store migration (v2 option noted in `pcg-data-contracts.md §9`) becomes necessary. Confirm checkpoint serialization cost is the actual bottleneck before migrating.
6. **LangSmith trace hierarchy becomes unreadable at 3-level nesting** (user → PCG → role subgraph → role's internal agent-loop nodes). If traces are noisy, evaluate flattening the coordination layer or adding span-grouping metadata.

**Requirement-shift signals.**

7. **Concurrent handoffs become necessary** — e.g., PM dispatches to Planner AND Researcher in parallel, or multiple sandboxed Developers running concurrently for the optimization loop (hinted at by Vision D10/D12). Current `handoff_log` linearity breaks. Need Send-based fanout + revised acceptance-gate mechanism + `role:instance_id` namespace scheme.
8. **A non-Deep-Agent role is proposed** — e.g., a pure code-formatter role that doesn't need memory/skills/HITL. Mount-as-subgraph accepts any `CompiledStateGraph`, so architecturally fine; but validate the first time it comes up.
9. **Multi-dimensional QA gates needed** beyond binary pass/fail (e.g., "passed performance but failed security review" as separate dimensions). Current `acceptance_stamps` dict with two keys would need richer typing. Watch for Evaluator role wanting richer semantics.

**Production-learning signals.**

10. **Our own running system shows friction we didn't predict.** The first real execution of the PCG in anger is the most valuable learning opportunity. Log everything, capture anomalies, revisit design with empirical evidence.
11. **A production post-mortem from someone else hits our architecture's weakness.** Anthropic/LangChain/OpenAI engineers occasionally publish post-mortems or lessons-learned. Actively read these; map observations back to our design.
12. **Confluence moments from unrelated domains.** A distributed-systems paper, compiler pattern, actor-model primitive, workflow orchestrator that reframes our coordination problem more cleanly. When it hits, write it down immediately — don't let the insight evaporate.

**Cadence.** Re-read this list at: (a) every `deepagents` / `langgraph` upgrade, (b) the first real production run of the PCG, (c) any Vision iteration that changes coordination requirements, (d) any time something in unrelated work triggers "wait, this maps to PCG."

### 11.7 Phase 2 Correction Checklist

1. [x] Updated `AD.md §4 LangGraph Project Coordination Graph` — topology table (1 dispatcher + 7 mounted role subgraphs), dispatcher signature, enforce-Command.PARENT-exit rule, `finish_to_user` terminal tool note, Category 7 added, System Overview + Sequence diagrams, Runtime Topology, Observability trace, Factory Contract paragraph, OQ-H4 resolution, Project-Scoped Execution intro.
2. [x] Updated `docs/specs/pcg-data-contracts.md` — §1 Purpose, §2 Topology Recap, §4 Invariants (esp. #2 rewritten with Deep Agent SDK-layer structural isolation + terminal-exit requirement), §5 Command.PARENT contract (split handoff-tool shape from `finish_to_user`), §3 `messages` writer updated, §7.3 projects_registry writer updated, §8 dispatcher reference (pure routing), §10 Conformance Tests updated.
3. [x] Updated `docs/specs/handoff-tools.md` — frontmatter note, §1.1 uniform shape note for 23 handoff tools with pointer to §4.7, new §1.3 "Every Turn Terminates with Command.PARENT" rule including final-turn-guard middleware, new §4.7 Category 7 Terminal Emission with `finish_to_user`, §5 agent-scoped ownership PM row updated, §6 pipeline flow terminal line updated.
4. [x] Updated `docs/specs/repo-and-workspace-layout.md` §3 — factory code now shows dispatcher + `for role_name, role_graph in ROLE_GRAPHS.items(): builder.add_node(role_name, role_graph)`, §3.1 node responsibilities now lists all 8 nodes (dispatcher + 7 roles) with exit contract per role.
5. [x] `DECISIONS.md` — Q4 / Q10 / Q11 supersession notes updated in place so the frozen rationale now points at the corrected mounted-subgraph architecture instead of the discarded explicit-invocation pattern.
6. [x] Appended `CHANGELOG.md` correction entry.
7. [x] `last_synced: 2026-04-22` on all three specs already at today's date; provenance-line notes updated on pcg-data-contracts.md and handoff-tools.md and repo-and-workspace-layout.md to reference the correction.
