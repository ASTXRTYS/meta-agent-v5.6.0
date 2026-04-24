---
doc_type: spec
derived_from:
  - AD §4 LangGraph Project Coordination Graph
  - AD §4 Handoff Protocol
  - AD §4 Data Contracts
status: active
last_synced: 2026-04-24
owners: ["@Jason"]
---
# PCG Data Contracts Specification

> **Provenance:** Derived from `AD.md §4 LangGraph Project Coordination Graph` (state schema, topology, and invariants), `§4 Handoff Protocol → Command.PARENT Update Contract`, and `§4 Data Contracts`.  
> **Status:** Active · **Last synced with AD:** 2026-04-24 (rewritten for `OQ-HO` resolution; supersedes Q4 / Q10 / Q11 in `DECISIONS.md`; corrected to mount-as-subgraph pattern after review surfaced `.ainvoke()` / `Command.PARENT` incompatibility; clarified sibling relationship with `handoff-tools.md`; updated for `handoff-tool-definitions.md` field ownership and `project_phase` / `plan_phase_id` split; **corrected routing primitive from string `goto` to `Send` for explicit child input injection per Ticket 1**).
> **Consumers:** Developer (implementation), Evaluator (conformance checking).

## 1. Purpose

The parent AD decides that the Project Coordination Graph (PCG) is a thin
graph with 1 coordination node (`dispatch_handoff`) plus 7 mounted role
Deep Agent subgraph nodes. The coordination node records handoffs and
routes via `Command(goto=<target_agent>)`. Role Deep Agents are mounted as
subgraph nodes so `Command.PARENT` emitted by their handoff tools bubbles
natively through the Pregel namespace hierarchy. No agent cognition, no
artifact content, no specialist messages live in PCG state. This spec
defines the exact state schema (channels, reducers, ownership), the
`Command.PARENT` update contract, the `HandoffRecord` wire format, and the
durable `Store` namespaces that together implement the AD decisions.

**Relationship to handoff tool specs.** This spec owns the shared PCG-side
wire/data contract that every handoff tool must emit: state channels, reducers,
`Command.PARENT` update shape, `HandoffRecord` fields, and model-vs-system
field ownership. `docs/specs/handoff-tools.md` owns the semantic tool catalog: which
tools exist, which role owns each tool, target role, reason, artifact flow,
middleware gate, and pipeline order. `docs/specs/handoff-tool-definitions.md`
owns the concrete model-visible tool definitions and composes both sources;
code generation or implementation must not invent fields or tool schemas outside
that combined contract.

## 2. Topology Recap (informative)

```txt
START → dispatch_handoff
          │  emits Command(goto=Send(target_agent, {"messages": [handoff_message]}))
          │  into the mounted role node. The Send.arg becomes the child's
          │  messages input per _InputAgentState schema.
          ▼
     (mounted role subgraph: project_manager | harness_engineer | ...)
          │  role turn terminates by emitting Command(graph=PARENT, ...)
          │  which bubbles through Pregel namespaces back to the PCG,
          │  dispatch_handoff re-enters and routes to the next role.
          │
          │  PM terminal case: finish_to_user emits
          │  Command(graph=PARENT, goto=END, update={messages: [...]})
          ▼
         END
```

1 coordination node + 7 mounted role subgraph nodes. Zero conditional
edges. Zero static edges between dispatcher and roles — routing is
entirely driven by `Command(goto=Send(...))` emissions.

**Why `Send` not string `goto`:** A string `goto` (e.g., `Command(goto="project_manager")`)
triggers a PULL task that reads input from parent state channels
(`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:68-69`).
The Deep Agent's `_InputAgentState` only accepts `messages`
(`.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`),
but PCG `messages` is reserved for user-facing I/O (Invariant #1). Using
`Send(target_agent, {"messages": [handoff_message]})` creates a PUSH task
that passes `packet.arg` directly as the child's input
(`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`,
`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`),
ensuring the handoff brief reaches the receiving agent without polluting
PCG `messages`. See `AD.md §4 LangGraph Project Coordination Graph` for the
authoritative description.

## 3. `ProjectCoordinationState` Schema

The `ProjectCoordinationState` is a `TypedDict` with the following channels.
Implementation may substitute a `dataclass` or Pydantic model provided the
channel semantics (key names, types, reducer signatures) are preserved.


| Channel | Type | Reducer | Purpose | Writers | Readers |
|---------|------|---------|---------|---------|---------|
| `messages` | `list[AnyMessage]` | `add_messages` | User-facing I/O conduit. Written only via PM's `finish_to_user` tool. | PM's `finish_to_user` tool only | External surfaces only (TUI, web app, headless ingress). Specialist agents never read it. |
| `project_id` | `str` | overwrite (no reducer) | Durable Meta Harness project identity. | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, Store writers |
| `project_thread_id` | `str` | overwrite | Canonical LangGraph project execution thread identity. May equal `project_id` in local/dev. | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, Store writers |
| `current_phase` | `Literal["scoping","research","architecture","planning","development","acceptance"]` | overwrite | Denormalization of last lifecycle-phase-transitioning handoff. Fast path for middleware gate dispatch. Not independent source-of-truth. | Handoff tools via `Command.PARENT` update when `HandoffRecord.project_phase` is present | Phase-gate middleware |
| `current_agent` | `Literal["project_manager","harness_engineer","researcher","architect","planner","developer","evaluator"]` | overwrite | Which role `dispatch_handoff` is about to invoke. Matches `handoff_log[-1].target_agent`. | Handoff tools via `Command.PARENT` update | `dispatch_handoff`, middleware |
| `handoff_log` | `list[HandoffRecord]` | `operator.add` | Append-only audit trail of all handoffs. v1 has implementation-determined cap. | Handoff tools via `Command.PARENT` update | `dispatch_handoff` (reads `[-1]`), HE-participation helper for acceptance gate |
| `acceptance_stamps` | `dict[Literal["application","harness"], HandoffRecord]` | merge-dict (see §3.1) | First-class acceptance-stamp channel. Gate logic reads this; never scans `handoff_log`. | `submit_application_acceptance`, `submit_harness_acceptance` tools via `Command.PARENT` update | `return_product_to_pm` gate middleware |

**Channel details:**

- **`messages`**: User-facing I/O conduit (LangGraph convention). Written only via PM's `finish_to_user` tool (`Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`). Multiple lifecycle cycles may occur across the project thread lifetime (headless-ready-infra policy).
- **`current_phase`**: Denormalization of the last lifecycle-phase-transitioning handoff. Fast path for middleware gate dispatch. **Not** an independent source of truth — `handoff_log` with `HandoffRecord.project_phase` remains authoritative. Developer implementation-plan phases are stored separately as `plan_phase_id` and never drive `current_phase`.
- **`handoff_log`**: Append-only audit trail of all handoffs in the project thread. v1 has an implementation-determined cap; trimming / migration to `Store` is a pure persistence concern.
- **`acceptance_stamps`**: First-class acceptance-stamp channel. Gate logic for `return_product_to_pm` reads this; never scans `handoff_log`.


Private per-middleware state (e.g. `StagnationGuardState`'s `_model_call_count`) is carried by the middleware, not in `ProjectCoordinationState`. The middleware's `AgentMiddleware.state_schema` augments the child agent's state, not the PCG's.

### 3.1 `acceptance_stamps` merge reducer

Semantics: a new value replaces the existing value at the same key; missing keys are preserved. Equivalent implementation:

```python
def _merge_stamps(
    left: dict[Literal["application", "harness"], HandoffRecord] | None,
    right: dict[Literal["application", "harness"], HandoffRecord] | None,
) -> dict[Literal["application", "harness"], HandoffRecord]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged
```

## 4. Key Invariants

1. **`messages` is the user-facing I/O conduit.** PCG `messages` is written only by the PM's terminal `finish_to_user` tool (via `Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`). Other handoff tools never include `messages` in their update dict. Specialist agents never read it. The `add_messages` reducer is retained because `messages` carries real `BaseMessage` objects — unlike the previous (structurally broken) application of `add_messages` to `handoff_log`.
2. **Child isolation is structural at the Deep Agent SDK layer.** Every role is a `create_deep_agent()` compiled graph with its own declared `input_schema=_InputAgentState` (messages only; `@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`) and `output_schema=_OutputAgentState` (messages + optional `structured_response`; `types.py:364-368`). `todos`, `files`, `jump_to`, and all middleware-private state carry `PrivateStateAttr` / `OmitFromOutput` annotations (`types.py:346-347`) and are dropped structurally at the child's compile time. When mounted via `add_node(role, role_graph)`, LangGraph reads the subgraph's declared `input_schema` and only passes the shared `messages` channel (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1306-1314`). **Every role turn must terminate by emitting `Command(graph=PARENT, ...)`**; this prevents the child's in-progress `messages` state from merging into PCG `messages` via subgraph-natural-completion semantics. A thin final-turn-guard middleware re-prompts any role whose last `AIMessage` lacks a handoff-tool or `finish_to_user` call. The dispatcher does **not** invoke role graphs via `.ainvoke()` — that would break `Command.PARENT` bubbling (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:56-59` raises `InvalidUpdateError` on PARENT commands at top-level).
3. **`handoff_log` uses a typed append reducer.** `Annotated[list[HandoffRecord], operator.add]`. `add_messages` is not valid here because it coerces inputs through `convert_to_messages` which raises `NotImplementedError` on non-`MessageLikeRepresentation` values (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain_core/messages/utils.py:727-730`).
4. **`current_phase` is a denormalization.** It is updated by handoff tools only when the appended record includes `project_phase`, and it is kept consistent with the most recent `HandoffRecord.project_phase`. Middleware may prefer `current_phase` for fast dispatch. Developer plan-phase identifiers are stored as `plan_phase_id` and must never update `current_phase`.
5. **`acceptance_stamps` is the gate source of truth.** The acceptance gate on `return_product_to_pm` reads `state["acceptance_stamps"]`. Scanning `handoff_log` for acceptance records is an anti-pattern and must be rejected in review.
6. **Each role Deep Agent owns its own conversation history.** Role state lives in the role's checkpoint namespace. LangGraph's mounted-subgraph persistence uses the parent `thread_id` with a stable child `checkpoint_ns` derived from the node name (`project_manager`, `harness_engineer`, etc.). The PCG's `handoff_log` is not conversation history.
7. **Durable cross-thread data lives in `Store`.** `artifact_manifest`, `optimization_trendline`, and `projects_registry` are `Store` namespaces, not PCG state channels. See §7.
8. **Graph lifecycle is PM-controlled.** `ask_user` interrupts fire inside the PM's Deep Agent subgraph. LangGraph's native interrupt machinery pauses the subgraph and the parent graph transparently; resume flows through automatically — no PCG-level interrupt code is required.

## 5. `Command.PARENT` Update Contract

All handoff tools return:

```python
# Handoff tools (23 total) return:
Command(
    graph=Command.PARENT,
    goto="dispatch_handoff",
    update={
        "handoff_log": [handoff_record],              # appended via operator.add
        "current_agent": target_agent,                 # overwritten
        "current_phase": new_project_phase_if_transition,  # overwritten; OMIT if no lifecycle transition
        # Acceptance-stamp tools additionally include:
        # "acceptance_stamps": {"application": stamp_record}
        #   or
        # "acceptance_stamps": {"harness": stamp_record}
    },
)

# The terminal PM tool finish_to_user returns:
Command(
    graph=Command.PARENT,
    goto=END,
    update={
        "messages": [AIMessage(final_response_text)],
    },
)
```

**Key observations:**

- Handoff-tool update dicts **never** include `messages` (reserved for `finish_to_user`). Handoff briefs and artifact paths travel inside the `HandoffRecord` appended to `handoff_log`.
- `finish_to_user` is the **only** tool that writes to `messages`. It does NOT append to `handoff_log` — terminal emission is a lifecycle bookend, not an inter-agent handoff.
- The update dict **never** includes `pending_handoff`. That field no longer exists; the dispatcher reads `handoff_log[-1]`.
- `current_phase` is set only on lifecycle-phase-transitioning records. Non-transitioning handoffs omit the key.
- Acceptance tools are the only tools that write to `acceptance_stamps`.
- Artifact-manifest updates are `Store` writes (see §7), not state updates.

### 5.1 Tool-helper-vs-PCG field ownership

The model-visible tool call supplies only:

- `brief`
- `artifact_paths`
- `accepted` (acceptance tools only)
- `phase` (Developer phase-review tools only; stored as `plan_phase_id`)

Before returning `Command.PARENT`, the tool body calls a system-owned helper
that assembles the full `HandoffRecord`. The helper populates:

- `project_id`
- `project_thread_id`
- `source_agent`
- `target_agent`
- `reason`
- `handoff_id` (generated; e.g. `uuid4()`)
- `langsmith_run_id` (current run id via `langsmith.client.get_current_run_tree()` or equivalent; implementation-specific)
- `status` (initialized to `"queued"` at record creation)
- `created_at` (RFC3339 timestamp at record creation time)
- `project_phase` (only when the handoff transitions the PCG lifecycle phase)
- `plan_phase_id` (only for Developer plan-phase review tools)
- `accepted` (only on `submit_*_acceptance` tool calls)

The PCG (`dispatch_handoff`) reads the appended record, upserts
`projects_registry`, and routes to `target_agent`. It does not populate fields
inside a record after that record has already been appended by the
`operator.add` reducer. Any future lifecycle status transition beyond
`"queued"` must use an explicit state/update contract; it must not rely on
in-place mutation of an appended record.

### 5.2 Exception — PM-assembled handoff packages

For downstream pipeline delivery tools where the receiving agent needs the full accumulated artifact set, the PM assembles a consolidated project handoff package — a directory copied into the receiving agent's filesystem. The receiving agent owns and organizes that copy.

This applies to:

- `deliver_planning_package_to_planner` — Planner receives an organized package of design spec, public eval criteria, and public datasets.
- `deliver_development_package_to_developer` — Developer receives the full project package: plan, spec, public eval, PRD, research highlights. The Developer organizes this into a structured filesystem layout optimized for implementation and human readability.

Early-stage deliveries (`deliver_prd_to_harness_engineer`, `deliver_prd_to_researcher`, `deliver_design_package_to_architect`) remain as references because those specialists only need a few specific artifacts from the PM's already-organized namespace. The PM's role as organizer aligns with its identity as the business-oriented project manager who ensures artifacts are properly stored and structured before they flow downstream.

## 6. `HandoffRecord` Wire Format

The exact Pydantic / `TypedDict` serialization is left to implementation. The field set and enum values below are locked as AD decisions.

```json
{
  "project_id": "string",
  "project_thread_id": "string",
  "handoff_id": "string",
  "source_agent": "project-manager|harness-engineer|researcher|architect|planner|developer|evaluator",
  "target_agent": "project-manager|harness-engineer|researcher|architect|planner|developer|evaluator",
  "reason": "deliver|return|submit|consult|announce|coordinate|question",
  "brief": "string",
  "artifact_paths": ["string"],
  "langsmith_run_id": "string|null",
  "status": "queued|running|completed|failed",
  "created_at": "RFC3339 timestamp",
  "project_phase": "scoping|research|architecture|planning|development|acceptance|null",
  "plan_phase_id": "string|null",
  "accepted": "true|false|null"
}
```

### Field notes

- `project_id` — durable Meta Harness project identity.
- `project_thread_id` — canonical LangGraph thread for project execution. In local/dev may equal `project_id` by convention.
- `target_agent` maps 1:1 to the checkpoint namespace in v1.
- `reason` encodes the *type of transition* (not the pipeline phase). Middleware dispatches on `(source_agent, target_agent, reason)` for gate logic.
- `brief` is the concise summary the receiving agent reads — the only thing `dispatch_handoff` passes into the child's `messages` input.
- `artifact_paths` are filesystem paths to artifacts the calling agent produced; the receiver reads them from the caller's namespace.
- `langsmith_run_id` is the LangSmith run id for the dispatching PCG invocation, for trace correlation.
- `status` tracks the handoff lifecycle (`queued` → `running` → `completed`/`failed`), not the agent's task status.
- `created_at` is an RFC3339 timestamp set by the system-owned record helper before the parent update is returned.
- **`project_phase`** (optional) — populated only when the handoff transitions the PCG lifecycle phase. Supports the `current_phase` denormalization.
- **`plan_phase_id`** (optional) — populated only by Developer phase-review tools. The model-visible tool argument is named `phase`, but the record field is `plan_phase_id` to keep Developer implementation-plan phases distinct from the PCG lifecycle enum.
- **`accepted`** (optional) — populated only by the two `submit_*_acceptance` tools. Carries the acceptance boolean.

## 7. Durable Cross-Thread Data (`Store` Namespaces)

> **Status flag (2026-04-22):** This entire section is flagged for reconsideration under `AD.md §Open Questions → OQ-H5` (Durable cross-thread data substrate, source-of-truth model, and uniform read/write contract). The three namespaces below are the current best-effort design that closed the **functional** requirements of `OQ-H1` (PM session visibility) and `OQ-H3` (Developer-blind optimization trendline), but the **mechanism** — LangGraph `Store` as substrate, conventional write-path enforcement, filesystem-permission-based Developer exclusion, unspecified read-path interface, single-tenant namespace shape, and free-form sanitization — has unresolved upstream questions about substrate choice, source-of-truth model, multi-tenant composition, and schema governance. Consumers of this spec should treat §7 as **provisional**. Any implementation depending on it must either wait for `OQ-H5` resolution or accept the risk of rework. See `AD.md §Open Questions → OQ-H5` for the articulated decision space and pickup hints.

The LangGraph `Store` is the durable cross-thread surface for project data that must be readable from any ingress source or from `pm_session` threads. Store access goes through `langgraph.store.base.BaseStore`; in local dev this is typically `InMemoryStore` paired with `SqliteSaver`, in LangGraph Platform it is auto-resolved from the runtime.

### 7.1 `artifact_manifest`

- **Namespace:** `("projects", project_id, "artifact_manifest")`
- **Key shape:** `artifact_id` (`str`, e.g. uuid or slug).
- **Value shape (TypedDict):**
  ```python
  class ArtifactManifestEntry(TypedDict):
      artifact_id: str
      project_id: str
      type: Literal["prd", "eval_suite", "research_bundle", "design_spec", "plan", "phase_deliverable", "final_product", "dataset", "rubric", "trendline_snapshot", ...]
      owner_agent: AgentName
      path: str               # filesystem path (role-scoped namespace)
      public: bool            # exposed to non-owning surfaces
      created_at: str          # RFC3339
      handoff_id: str | None   # handoff record that introduced this artifact (if any)
      metadata: dict[str, Any] # optional; type-specific fields (e.g. dataset row count, plan phase count)
  ```
- **Writers:** any agent producing an artifact. Recommended: a thin middleware hook on artifact-producing tools writes the manifest entry automatically, so the tool contract stays unchanged.
- **Readers:** TUI, web app, headless ingress adapters, PM session threads, `dispatch_handoff` (to populate `projects_registry.artifact_count`).

### 7.2 `optimization_trendline`

- **Namespace:** `("projects", project_id, "optimization_trendline")`
- **Key shape:** `iteration_id` (`str`, monotonic).
- **Value shape (TypedDict):**
  ```python
  class TrendlinePoint(TypedDict):
      iteration_id: str
      project_id: str
      plan_phase_id: str         # development plan phase identifier
      metric: str                 # e.g. "harness_pass_rate", "accuracy", "latency_p95"
      value: float
      direction: Literal["higher_is_better", "lower_is_better"]
      timestamp: str               # RFC3339
      notes: str                   # optional human-readable context; MUST NOT contain rubric text, judge prompts, or held-out examples
  ```
- **Writer:** Harness Engineer exclusively. HE's filesystem permissions grant write access to this namespace.
- **Readers:** TUI, web app, headless ingress adapters, PM session threads. **NOT the Developer** — Developer's filesystem permissions explicitly exclude this namespace, preserving the information isolation locked in `AD.md §4 Gate-Ownership Boundary`.
- **Sanitization invariant:** HE populates `notes` with only directional signals (e.g. "rubric #3 pass rate improved after prompt edit X"). Rubric text, judge configs, and held-out dataset content never appear in trendline entries.

### 7.3 `projects_registry`

- **Namespace:** `("projects_registry",)` — global, not per-project.
- **Key shape:** `project_id` (`str`).
- **Value shape (TypedDict):**
  ```python
  class ProjectRegistryEntry(TypedDict):
      project_id: str
      project_thread_id: str
      pm_session_thread_id: str | None  # originating pm_session thread; null for UI-onboarding path
      current_phase: str
      current_agent: str
      last_handoff_id: str
      last_handoff_at: str        # RFC3339
      artifact_count: int
      status: Literal["active", "paused", "completed", "archived"]
  ```
- **Writer:** `dispatch_handoff` on each handoff (derives registry
  `current_phase`, `current_agent`, `last_handoff_id`, `last_handoff_at`, and
  `artifact_count` from the already-appended `HandoffRecord` and current PCG
  state). It never mutates `HandoffRecord` fields after append. On PM's
  `finish_to_user` (terminal emission), a separate hook on that tool sets
  `status="completed"` in the same `Command.PARENT.update` path or via a
  companion middleware after-hook.
- **Readers:** PM session threads (listing active projects), web app project list view, any headless ingress adapter asking "what is project X doing right now."

## 8. `dispatch_handoff` Node Contract (reference implementation sketch)

Not normative code, but the semantic contract every conforming implementation must preserve. The dispatcher is a pure routing function — it returns `Command(goto=Send(...))` and never calls `.ainvoke()` on a role graph. LangGraph routes into the mounted role subgraph node through the Pregel loop once the Command is emitted.

### 8.1 Routing Primitive

The dispatcher MUST use `Send(target_agent, {"messages": [handoff_message]})` as the `goto` value, not a string. SDK behavior:
- `Send` yields to `TASKS` channel (`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`)
- `packet.arg` is passed directly as the subgraph's input (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`)
- The child's `_InputAgentState` receives only the `messages` key (`.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`)

String `goto` (e.g., `Command(goto="project_manager")`) is **forbidden** — it triggers PULL task semantics that read from parent channels, which would incorrectly pass PCG's user-facing `messages` to the child.

### 8.2 Receiving-Agent Input Payload Shape

The `Send.arg` MUST be a dict with exactly one key:

```python
{
    "messages": [
        {
            "role": "user",
            "content": "[[Handoff from {source_agent}]]\n\n{brief}\n\n[[Artifacts]]\n{artifact_list}",
            "name": None,  # Optional: could include handoff_id as metadata
        }
    ]
}
```

**Field specifications:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | `Literal["user"]` | Yes | Fixed as `"user"` — the handoff arrives as a user message from the perspective of the receiving agent |
| `content` | `str` | Yes | Formatted handoff packet (see §8.3) |

### 8.3 Handoff Message Content Format

The `content` string MUST follow this exact structure:

```
[[Handoff from {source_agent} to {target_agent}]]
Reason: {reason}

{Brief text from HandoffRecord.brief}

[[Artifacts]]
- {artifact_path_1}
- {artifact_path_2}
...
```

**Formatting rules:**
1. `source_agent`, `target_agent`, `reason` come from `HandoffRecord`
2. `brief` is inserted verbatim from `HandoffRecord.brief`
3. `artifact_paths` from `HandoffRecord.artifact_paths` are rendered as a bullet list
4. Empty `artifact_paths` list renders `[[Artifacts]]\nNone` (not omitted)
5. Lines are separated by `\n` (Unix-style)

### 8.4 Pre-Routing Validation Rules

Before constructing the `Send`, the dispatcher MUST validate:

1. **`target_agent` presence**: `HandoffRecord.target_agent` must be non-empty and in `ROLE_GRAPHS.keys()`. **Failure**: raise `ValueError(f"Invalid target_agent: {target_agent}")` — do not route.

2. **`brief` presence**: `HandoffRecord.brief` must be non-empty string after stripping whitespace. **Failure**: raise `ValueError("HandoffRecord.brief is empty")` — do not route.

3. **`artifact_paths` validity**: Each path must be a string starting with `/` (absolute) or a valid relative path. **Failure**: raise `ValueError(f"Invalid artifact path: {path}")` — do not route.

4. **Sanity check**: `source_agent != target_agent` (no self-handoff). **Failure**: raise `ValueError("Self-handoff not permitted")` — do not route.

All validation failures are **hard stops** — the dispatcher does not emit a `Command`, allowing Pregel to surface the exception to the caller.

### 8.5 Initial Stakeholder Input to First PM Turn

On first invocation (`not state["handoff_log"]`):

1. Extract initial stakeholder input from `ProjectCoordinationInput` (not from PCG `messages` channel directly)
2. Synthesize a `HandoffRecord` with:
   - `source_agent`: `"system"` (special value for initial bootstrap)
   - `target_agent`: `"project_manager"`
   - `reason`: `"coordinate"`
   - `brief`: The stakeholder input text
   - `artifact_paths`: Empty list (or paths from input if provided)
3. Proceed through validation and `Send` construction as normal

This ensures the initial PM turn receives the stakeholder request as a formatted handoff message, identical to subsequent inter-agent handoffs.

### 8.6 Reference Implementation

```python
from langgraph.types import Command, Send
from langchain_core.messages import HumanMessage

async def dispatch_handoff(
    state: ProjectCoordinationState,
    runtime: Runtime[ProjectCoordinationContext],
) -> Command:
    """Coordination node. Emits Command(goto=Send(...)) to route; never invokes directly."""

    from meta_harness.agents.catalog import ROLE_GRAPHS  # 7 valid role names

    # --- 1. First invocation: synthesize initial handoff from stakeholder input --
    if not state["handoff_log"]:
        record = _synthesize_initial_handoff(state, runtime)
    else:
        record = state["handoff_log"][-1]

    # --- 2. Pre-routing validation (hard stops on failure) -----------------------
    target = record["target_agent"]
    if target not in ROLE_GRAPHS:
        raise ValueError(f"Invalid target_agent: {target}")
    if not record.get("brief", "").strip():
        raise ValueError("HandoffRecord.brief is empty")
    for path in record.get("artifact_paths", []):
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"Invalid artifact path: {path}")
    if record["source_agent"] == target:
        raise ValueError("Self-handoff not permitted")

    # --- 3. Construct handoff message ------------------------------------------
    artifact_list = "\n".join(f"- {p}" for p in record.get("artifact_paths", [])) or "None"
    content = (
        f"[[Handoff from {record['source_agent']} to {record['target_agent']}]]\n"
        f"Reason: {record['reason']}\n\n"
        f"{record['brief']}\n\n"
        f"[[Artifacts]]\n"
        f"{artifact_list}"
    )
    handoff_message = HumanMessage(content=content)

    # --- 4. Update projects registry ---------------------------------------------
    await _upsert_projects_registry(state, record, runtime.store)

    # --- 5. Route via Send (not string goto) -------------------------------------
    if not state["handoff_log"]:
        # First invocation: include initial state updates
        return Command(
            goto=Send(target, {"messages": [handoff_message]}),
            update={
                "handoff_log": [record],
                "current_agent": target,
                "current_phase": record.get("project_phase", "scoping"),
            },
        )
    else:
        # Re-entry: route to target with handoff message
        return Command(goto=Send(target, {"messages": [handoff_message]}))
```

**How routing actually works.** When `dispatch_handoff` emits `Command(goto=Send("project_manager", {"messages": [handoff_message]}))`, LangGraph's Pregel loop:
1. Maps the `Send` to the `TASKS` channel (`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`)
2. Creates a PUSH task where `packet.arg` (the `{"messages": [...]}` dict) is passed directly as the subgraph's input (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`)
3. The mounted Deep Agent subgraph receives the input filtered through its `_InputAgentState` schema — only `messages` is accepted
4. The subgraph runs until one of its internal nodes emits a Command. If a handoff tool emits `Command(graph=PARENT, goto="dispatch_handoff", update={...})`, the inner Pregel raises `ParentCommand`; the outer Pregel catches it, applies the update to PCG state via reducers, and re-enters `dispatch_handoff`. If `finish_to_user` emits `Command(graph=PARENT, goto=END, update={...})`, the outer Pregel applies the `messages` update and terminates the graph. Natural completion of a role subgraph is not expected and should be prevented by the final-turn-guard middleware.

## 9. Growth, Cap, and Migration Notes

- `messages` is bounded by natural PM completion frequency. Headless ingress may produce multiple lifecycle cycles; the channel is not artificially capped at 2 entries.
- `handoff_log` has an implementation-determined v1 cap. Gate dispatch does not depend on log length, so trimming is a pure persistence concern. v2 option: move the durable audit trail to `Store` namespace `("projects", project_id, "handoff_history")` on rollover; the dispatcher can then keep only the last N entries in checkpoint state.
- `acceptance_stamps` has a natural bound of 2 entries (one `application`, one `harness`). No cap needed.
- **Store namespaces** grow without state-checkpoint pressure; their retention policy is a deployment concern (local SQLite / Platform managed store / self-hosted Postgres).

## 10. Conformance Tests (minimum set)

Implementation must pass at least these assertions:

1. A `HandoffRecord` appended to `handoff_log` via a `Command.PARENT` update round-trips through checkpoint save/load without type coercion loss (detects accidental reintroduction of `add_messages` on this channel).
2. `dispatch_handoff` returns a `Command` with `goto` set to one of the 7 role names (for routing) or `END` (on terminal conditions that the dispatcher itself recognizes). It never calls `.ainvoke()` or `.invoke()` on a role graph (static analysis: search for `ROLE_GRAPHS[...].ainvoke` or `.invoke` inside dispatcher source — must have zero matches).
3. Every role's handoff-tool set and the PM's `finish_to_user` tool together cover the role's possible terminal actions. A final-turn-guard middleware re-prompts any role whose last `AIMessage` lacks a tool call to a handoff tool or `finish_to_user`.
4. The acceptance gate on `return_product_to_pm` reads `state["acceptance_stamps"]` and not `state["handoff_log"]` (static analysis or unit test).
5. `current_phase == <most recent non-null HandoffRecord.project_phase> or <previously-set lifecycle phase>` after every handoff (denormalization consistency). `plan_phase_id` must never drive `current_phase`.
6. `Store` writes to `projects_registry` occur on every handoff (fuzz: random-length handoff chains, verify registry matches last record).
7. Developer's filesystem permissions do not include read access to `projects/{project_id}/optimization_trendline` (permission-layer unit test).
8. **Receiving-agent input contains rendered HandoffRecord packet, not raw PCG messages.** Given a mounted role subgraph with a spy node that captures its input, when `dispatch_handoff` routes to that role, the spy receives exactly one `HumanMessage` with:
   - `content` containing the formatted handoff packet per §8.3
   - `role == "user"`
   - The `brief` text from `HandoffRecord` appears verbatim in the content
   - The `artifact_paths` are rendered as a bullet list
   The raw PCG `messages` channel MUST NOT appear in the child's input (structural assertion via `_InputAgentState` schema filtering).
