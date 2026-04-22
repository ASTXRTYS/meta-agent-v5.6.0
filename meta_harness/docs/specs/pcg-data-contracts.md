---
doc_type: spec
derived_from:
  - AD §4 LangGraph Project Coordination Graph
  - AD §4 Handoff Protocol
  - AD §4 Data Contracts
status: active
last_synced: 2026-04-22
owners: ["@Jason"]
---

# PCG Data Contracts Specification

> **Provenance:** Derived from `AD.md §4 LangGraph Project Coordination Graph` (state schema and invariants), `§4 Handoff Protocol` (Command.PARENT Update Contract), and `§4 Data Contracts` (HandoffRecord wire format).  
> **Status:** Active · **Last synced with AD:** 2026-04-22  
> **Consumers:** Developer (implementation), Evaluator (conformance checking).

## 1. Purpose

The parent AD decides that the Project Coordination Graph (PCG) is a thin
two-node graph carrying only deterministic coordination data — no agent
cognition, no artifact content, no specialist messages. This spec defines
the exact state schema, the `Command.PARENT` update contract, and the
`HandoffRecord` wire format that implement those decisions.

## 2. PCG State Schema

The `ProjectCoordinationState` carries only deterministic coordination data.

| Field | Type | Purpose | Set by |
|---|---|---|---|
| `messages` | `Annotated[list[AnyMessage], add_messages]` | **User-facing I/O channel.** Accumulates stakeholder input and PM's final product response only — lifecycle bookends. Never written to during pipeline execution. Also the only key shared with `_InputAgentState`, so it is the conduit by which `run_agent` passes input to child graphs. | `process_handoff` (stakeholder input), PM normal exit (final response) |
| `project_id` | `str` | Durable Meta Harness project identity | `process_handoff` (from initial invocation) |
| `project_thread_id` | `str` | Canonical LangGraph project execution thread identity for this PCG run | `process_handoff` (from routing context) |
| `current_phase` | `Literal["scoping", "research", "architecture", "planning", "development", "acceptance"]` | Current project phase; middleware reads this for gate dispatch | `process_handoff` (advanced on phase-transition handoffs) |
| `current_agent` | `Literal["project_manager", "harness_engineer", "researcher", "architect", "planner", "developer", "evaluator"]` | Which role graph is currently active; `run_agent` reads this to select the correct mounted child | `process_handoff` |
| `handoff_log` | `Annotated[list[HandoffRecord], add_messages]` | Append-only coordination audit trail — who handed what to whom, when, why, with which artifacts. Also serves as acceptance record for gated tools (e.g. `return_product_to_pm`). Capped at N records; cap mitigation delegated to implementation. | `process_handoff` |
| `pending_handoff` | `HandoffRecord \| None` | Active handoff cursor — the handoff record currently being processed by `run_agent`. Set by `process_handoff`, consumed by `run_agent`, cleared on completion. | `process_handoff` (set), `run_agent` (clear) |

## 3. Key Invariants

1. **`messages` is the user-facing I/O channel.** It accumulates only
   stakeholder `HumanMessage` objects (in) and the PM's final `AIMessage`
   product response (out) — lifecycle bookends. Handoff tools do NOT write
   to it. Child agent intermediate output does NOT flow back into it. The
   `add_messages` reducer is required to prevent overwrite when multiple
   user messages arrive across invocations.
2. **`messages` is the only key visible to child agents.** LangGraph maps
   parent state to child input by shared key name. The Deep Agent input
   schema (`_InputAgentState`) defines only `messages`. The implementation
   MUST set `input_schema=_InputAgentState` on each `add_node` call for
   mounted child graphs to prevent other PCG keys from leaking into child
   input.
3. **`run_agent` constructs the child's input, not the PCG.** The
   `run_agent` node constructs a single `HumanMessage` containing the
   handoff brief (from `pending_handoff`) and passes it as the child's
   `messages` input. The child never sees the raw PCG `messages` list.
4. **`handoff_log` uses `add_messages` for append-only semantics.**
   `HandoffRecord` objects implement the message protocol (have an `id`
   field) so `add_messages` provides append-without-overwrite. This is a
   reuse of the reducer for its semantics, not because handoff records are
   messages. The cap threshold N is a runtime constant; cap mitigation
   mechanism is delegated to implementation.
5. **`pending_handoff` is an execution cursor, not a data store.** It
   points to the handoff currently being processed. It is set by
   `process_handoff`, consumed by `run_agent`, and cleared on completion.
   It is required by the two-node topology (data must flow through state
   between nodes).
6. **Child agents own their own conversation history.** Each mounted Deep
   Agent accumulates messages in its own checkpoint namespace. The PCG's
   `messages` key is not a conversation history — it's an I/O channel.
   Child agent message compaction is handled by `SummarizationMiddleware`
   within each agent, not by the PCG.
7. **Graph lifecycle is PM-controlled.** The PM decides when to end
   (finish normally → END) or stay alive (use `ask_user` → interrupt →
   pause). The PCG is transparent to interrupts — `ask_user` pauses the
   PM's child graph, which pauses the PCG node, which pauses the graph.
   Resume flows through automatically.

## 4. `Command.PARENT` Update Contract

The handoff tool's `Command.PARENT` update dict writes to specific parent
state channels using their reducers. The AD specifies which keys are
written; the field-level update shape is defined below.

```python
Command(
    graph=Command.PARENT,
    goto="process_handoff",
    update={
        "handoff_log": [HandoffRecord(
            project_id=...,
            project_thread_id=...,
            source_agent=...,
            target_agent=...,
            reason=...,
            brief=...,
            artifact_paths=...,
        )],
        "current_agent": <target_agent>,            # overwritten (no reducer)
        "current_phase": <new_phase_if_transition>, # overwritten; only on phase transitions
        "pending_handoff": HandoffRecord(...),      # same record as handoff_log entry
    }
)
```

**Key observation.** The update dict does NOT include `messages`. The
handoff brief and artifact paths are captured in `handoff_log`, not in
`messages`. This is the lifecycle-bookend invariant: `messages` only
accumulates stakeholder input and the PM's final product response.

**PCG-filled fields.** `handoff_id`, `langsmith_run_id`, `status`, and
`created_at` are added by `process_handoff`, not by the calling agent.
The calling agent populates: `project_id`, `project_thread_id`,
`source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`.

**Exception: PM-assembled handoff packages.** For downstream pipeline
delivery tools where the receiving agent needs the full accumulated
artifact set, the PM assembles a consolidated project handoff package — a
directory that gets copied into the receiving agent's filesystem. The
receiving agent then owns and organizes that copy. This applies to:

- `deliver_spec_to_planner` — Planner receives an organized package of
  design spec, public eval criteria, and public datasets.
- `deliver_plan_to_developer` — Developer receives the full project
  package: plan, spec, public eval, PRD, and research highlights. The
  Developer organizes this into a structured filesystem layout optimized
  for implementation and human readability.

Early-stage deliveries (`deliver_prd_to_harness_engineer`,
`deliver_prd_to_researcher`, `deliver_prd_to_architect`) remain as
references because those specialists only need a few specific artifacts
from the PM's already-organized namespace. The PM's role as organizer
aligns with its identity as the business-oriented project manager who
ensures artifacts are properly stored and structured before they flow
downstream.

## 5. `HandoffRecord` Wire Format

The exact Pydantic or `TypedDict` wire format is left to implementation.
The field set and enum values below are locked as AD decisions.

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
  "created_at": "RFC3339 timestamp"
}
```

### Field notes

- `project_id` — durable Meta Harness project identity.
- `project_thread_id` — canonical LangGraph thread for project execution.
  In local/dev it may equal `project_id` by convention.
- `target_agent` maps 1:1 to the checkpoint namespace in v1; no separate
  `target_role_namespace` field needed.
- `reason` encodes the *type of transition* (not the pipeline phase).
  Middleware dispatches on the `(source_agent, target_agent, reason)`
  triple to determine which gate logic to apply. The `question` reason
  covers specialist-to-PM stakeholder questions — no separate `question`
  field needed.
- `brief` is the concise summary the receiving agent reads.
- `artifact_paths` are filesystem paths to artifacts the calling agent
  produced, so the receiver knows what to load.
- `langsmith_run_id` is the LangSmith run ID for the mounted role graph
  invocation, for trace correlation.
- `status` tracks the handoff lifecycle (queued → running →
  completed/failed), not the agent's task status.
- `created_at` is an RFC3339 timestamp set by the PCG when the handoff is
  recorded.

## 6. Growth and Persistence Notes

- The `messages` key is bounded by design — only lifecycle bookends, at
  most 2 entries per lifecycle cycle.
- The `handoff_log` cap strategy for v1: cap to last N records per project
  thread. Mitigation options when records exceed the cap (summarize into a
  string field, migrate to LangGraph Store, or discard with a count
  marker) are delegated to implementation.
- v2 option: move full handoff history to the LangGraph `Store` (key-value)
  instead of the PCG state, so the PCG state never grows. The `run_agent`
  node and middleware can query the store on demand.
- Child agent message compaction is handled by the Deep Agents
  `SummarizationMiddleware` within each agent, not by the PCG.
