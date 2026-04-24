---
doc_type: spec
derived_from:
  - AD §4 LangGraph Project Coordination Graph
  - AD §4 Handoff Protocol
  - AD §4 Data Contracts
  - AD §4 PM Session And Project Entry Model
status: active
last_synced: 2026-04-24
owners: ["@Jason"]
---
# PCG Data Contracts Specification

> **Provenance:** Derived from `AD.md §4 LangGraph Project Coordination Graph` (state schema, topology, and invariants), `§4 Handoff Protocol → Command.PARENT Update Contract`, `§4 Data Contracts`, and `§4 PM Session And Project Entry Model`.
> **Status:** Active · **Last synced with AD:** 2026-04-24 (rewritten for `OQ-HO` resolution; supersedes Q4 / Q10 / Q11 in `DECISIONS.md`; corrected to mount-as-subgraph pattern after review surfaced `.ainvoke()` / `Command.PARENT` incompatibility; clarified sibling relationship with `handoff-tools.md`; updated for `handoff-tool-definitions.md` field ownership and `project_phase` / `plan_phase_id` split; corrected routing primitive from string `goto` to `Send` for explicit child input injection per Ticket 1; added persistence contract and namespace semantics for mounted role subgraphs per Ticket 3; **repaired wire/data contract inconsistencies per Ticket 4: canonical snake_case role enums, removed unused status field, explicit langsmith_run_id fallback, no handoff_log cap, explicit type aliases, clarified acceptance truth semantics**; **restored dispatcher re-entry `goto` on normal handoff parent commands and added approval-result stamp feedback semantics per Ticket 5 feedback**; **moved product data-plane schemas to `project-data-plane.md` for Ticket 6 / `OQ-H5` closure**).
> **Consumers:** Developer (implementation), Evaluator (conformance checking).

## 1. Purpose

The parent AD decides that the Project Coordination Graph (PCG) is a thin
graph with 1 coordination node (`dispatch_handoff`) plus 7 mounted role
Deep Agent subgraph nodes. The coordination node records handoffs and routes via
`Command(goto=Send(<target_agent>, child_input))`, where `child_input` always
contains the rendered handoff message and contains `pcg_gate_context` for
gated roles.
Role Deep Agents are mounted as
subgraph nodes so `Command.PARENT` emitted by their handoff tools bubbles
natively through the Pregel namespace hierarchy. No agent cognition, no
artifact content, no specialist messages live in PCG state. This spec
defines the exact state schema (channels, reducers, ownership), the
`Command.PARENT` update contract, the `HandoffRecord` wire format, and the
PCG-owned cross-reference to the Project Data Plane. Product data-plane
schemas, read/write APIs, authorization, tenant boundaries, retention, and
trace metadata live in `docs/specs/project-data-plane.md`.

## 2. Type Aliases

The following type aliases are used throughout this spec and the handoff tool definitions:

```python
from typing import Literal
from typing_extensions import TypedDict

AgentName = Literal[
    "project_manager",
    "harness_engineer",
    "researcher",
    "architect",
    "planner",
    "developer",
    "evaluator",
]

HandoffSourceAgent = AgentName | Literal["system"]

Reason = Literal[
    "deliver",
    "return",
    "submit",
    "consult",
    "announce",
    "question",
    "coordinate",
]

ProjectPhase = Literal[
    "scoping",
    "research",
    "architecture",
    "planning",
    "development",
    "acceptance",
]

StampKey = Literal["application", "harness", "scoping_to_research", "architecture_to_planning"]

class PCGGateContext(TypedDict, total=False):
    org_id: str
    project_id: str
    project_thread_id: str
    current_phase: ProjectPhase
    current_agent: AgentName
    handoff_log: list[HandoffRecord]
    acceptance_stamps: dict[StampKey, HandoffRecord]
```

**Rationale:** These aliases provide canonical type definitions for enum values used across the PCG state schema and handoff tools. All role names use snake_case (Python convention) for consistency with code generation and SDK integration.

**Relationship to handoff tool specs.** This spec owns the shared PCG-side
wire/data contract that every handoff tool must emit: state channels, reducers,
`Command.PARENT` update shape, `HandoffRecord` fields, and model-vs-system
field ownership. `docs/specs/handoff-tools.md` owns the semantic tool catalog: which
tools exist, which role owns each tool, target role, reason, artifact flow,
middleware gate, and pipeline order. `docs/specs/handoff-tool-definitions.md`
owns the concrete model-visible tool definitions and composes both sources;
code generation or implementation must not invent fields or tool schemas outside
that combined contract.

**Relationship to runtime contract spec.** This spec owns the internal PCG state schema (channels, reducers, `HandoffRecord`, `Command.PARENT` update contract). `docs/specs/pcg-runtime-contract.md` owns the Agent Server boundary contract: `ProjectCoordinationInput`, `ProjectCoordinationContext`, `ProjectCoordinationOutput` schemas, thread metadata, bootstrap behavior, and the mapping from external caller to PCG state initialization. The two specs are siblings: runtime bootstrap readers consult `pcg-runtime-contract.md`; PCG state channel readers consult this spec.

**Relationship to project data plane spec.** This spec does not define product
database schemas or cross-surface read APIs. `docs/specs/project-data-plane.md`
owns `project_registry`, `artifact_manifest`, `optimization_trendline`,
`project_data_events`, `project_snapshots`, the owning operations, and
Developer-private / HE-private read boundaries. PCG handoff records contain
artifact references; Project Data Plane operations decide how those references
are registered, surfaced, archived, and audited.

## 3. Topology Recap (informative)

```txt
START → dispatch_handoff
          │  emits Command(goto=Send(target_agent, child_input))
          │  into the mounted role node. The Send.arg becomes the child's
          │  input and may include pcg_gate_context for gated roles.
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
`Send(target_agent, child_input)` creates a PUSH task that passes `packet.arg`
directly as the child's input
(`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`,
`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`),
ensuring the handoff brief reaches the receiving agent without polluting
PCG `messages`. See `AD.md §4 LangGraph Project Coordination Graph` for the
authoritative description.

## 4. `ProjectCoordinationState` Schema

The `ProjectCoordinationState` is a `TypedDict` with the following channels.
Implementation may substitute a `dataclass` or Pydantic model provided the
channel semantics (key names, types, reducer signatures) are preserved.


| Channel | Type | Reducer | Purpose | Writers | Readers |
|---------|------|---------|---------|---------|---------|
| `messages` | `list[AnyMessage]` | `add_messages` | User-facing I/O conduit. Written only via PM's `finish_to_user` tool. | PM's `finish_to_user` tool only | External surfaces only (TUI, web app, headless ingress). Specialist agents never read it. |
| `org_id` | `str` | overwrite (no reducer) | Tenant identity required for Project Data Plane reads/writes. | `dispatch_handoff` (initial from runtime input/thread metadata) | `dispatch_handoff`, data-plane writers |
| `project_id` | `str` | overwrite (no reducer) | Durable Meta Harness project identity. | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, data-plane writers |
| `project_thread_id` | `str` | overwrite | Canonical LangGraph project execution thread identity. May equal `project_id` in local/dev. | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, data-plane writers |
| `current_phase` | `ProjectPhase` | overwrite | Denormalization of last lifecycle-phase-transitioning handoff. Fast path for middleware gate dispatch. Not independent source-of-truth. | Handoff tools via `Command.PARENT` update when `HandoffRecord.project_phase` is present | `dispatch_handoff`; projected into `pcg_gate_context` for phase-gate middleware |
| `current_agent` | `AgentName` | overwrite | Which role `dispatch_handoff` is about to invoke. Matches `handoff_log[-1].target_agent`. | Handoff tools via `Command.PARENT` update | `dispatch_handoff`, middleware |
| `handoff_log` | `list[HandoffRecord]` | `operator.add` (list concatenation) | Append-only audit trail of all handoffs. No cap in v1. | Handoff tools via `Command.PARENT` update | `dispatch_handoff` (reads `[-1]`); projected into `pcg_gate_context` for prerequisite gates and HE-participation helper |
| `acceptance_stamps` | `dict[StampKey, HandoffRecord]` | merge-dict (see §4.1) | First-class stamp channel for product acceptance and user approval gates. Gate logic reads this through `pcg_gate_context`; never scans `handoff_log`. | `submit_application_acceptance`, `submit_harness_acceptance`, `request_approval` tools via `Command.PARENT` update | `dispatch_handoff`; projected into `pcg_gate_context` for user-approval gate middleware and `return_product_to_pm` gate middleware |

**Channel details:**

- **`messages`**: User-facing I/O conduit (LangGraph convention). Written only via PM's `finish_to_user` tool (`Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`). Multiple lifecycle cycles may occur across the project thread lifetime (headless-ready-infra policy).
- **`org_id`**: Tenant identity copied from runtime bootstrap input or thread
  metadata on first invocation. It is required for every Project Data Plane
  operation and never inferred from `project_id`.
- **`current_phase`**: Denormalization of the last lifecycle-phase-transitioning handoff. Fast path for middleware gate dispatch. **Not** an independent source of truth — `handoff_log` with `HandoffRecord.project_phase` remains authoritative. Developer implementation-plan phases are stored separately as `plan_phase_id` and never drive `current_phase`.
- **`handoff_log`**: Append-only audit trail of all handoffs in the project thread. No cap in v1 — projects have finite handoff counts. HE participation detection (scanning for `source_agent` or `target_agent == "harness_engineer"`) must work correctly regardless of log size.
- **`acceptance_stamps`**: First-class stamp channel. Gate logic for
  `deliver_prd_to_researcher`, `deliver_planning_package_to_planner`, and
  `return_product_to_pm` reads this through the `pcg_gate_context` projection;
  it never scans `handoff_log` for stamps.


Private per-middleware state (e.g. `StagnationGuardState`'s `_model_call_count`) is carried by the middleware, not in `ProjectCoordinationState`. The middleware's `AgentMiddleware.state_schema` augments the child agent's state, not the PCG's.

### 4.1 `acceptance_stamps` merge reducer

Semantics: a new value replaces the existing value at the same key; missing keys are preserved. Equivalent implementation:

```python
def _merge_stamps(
    left: dict[StampKey, HandoffRecord] | None,
    right: dict[StampKey, HandoffRecord] | None,
) -> dict[StampKey, HandoffRecord]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged
```

## 5. Key Invariants

1. **`messages` is the user-facing I/O conduit.** PCG `messages` is written only by the PM's terminal `finish_to_user` tool (via `Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`). Other handoff tools never include `messages` in their update dict. Specialist agents never read it. The `add_messages` reducer is retained because `messages` carries real `BaseMessage` objects — unlike the previous (structurally broken) application of `add_messages` to `handoff_log`.
2. **Child isolation is structural at the Deep Agent SDK layer.** The base `create_deep_agent()` input schema accepts `messages` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`) and the output schema exposes `messages` plus optional `structured_response` (`types.py:364-368`). Gated roles deliberately extend their agent state schema with `pcg_gate_context`, annotated as accepted input and omitted output, so role middleware can evaluate PCG-derived gates after LangGraph filters mounted subgraph input. LangChain merges middleware state schemas into the child input schema unless annotated `OmitFromInput` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain/agents/factory.py:402-444`); `OmitFromOutput` keeps the projection from leaking on natural completion (`types.py:340-347`). `todos`, `files`, `jump_to`, and middleware-private state remain private. When mounted via `add_node(role, role_graph)`, LangGraph reads the subgraph's declared `input_schema` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1306-1314`). **Every role turn must terminate by emitting `Command(graph=PARENT, ...)`**; this prevents the child's in-progress `messages` state from merging into PCG `messages` via subgraph-natural-completion semantics. A thin final-turn-guard middleware re-prompts any role whose last `AIMessage` lacks a handoff-tool or `finish_to_user` call. The dispatcher does **not** invoke role graphs via `.ainvoke()` — that would break `Command.PARENT` bubbling (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:56-59` raises `InvalidUpdateError` on PARENT commands at top-level).
3. **`handoff_log` uses a typed append reducer.** `Annotated[list[HandoffRecord], operator.add]`. `add_messages` is not valid here because it coerces inputs through `convert_to_messages` which raises `NotImplementedError` on non-`MessageLikeRepresentation` values (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langchain_core/messages/utils.py:727-730`).
4. **`current_phase` is a denormalization.** It is updated by handoff tools only when the appended record includes `project_phase`, and it is kept consistent with the most recent `HandoffRecord.project_phase`. Middleware may prefer `current_phase` for fast dispatch. Developer plan-phase identifiers are stored as `plan_phase_id` and must never update `current_phase`.
5. **`acceptance_stamps` is the gate source of truth.** User approval gates
   and the product acceptance gate on `return_product_to_pm` read
   `request.state["pcg_gate_context"]["acceptance_stamps"]`, which is a
   dispatcher-created projection of PCG state. Scanning `handoff_log` for stamp
   records is an anti-pattern and must be rejected in review.
6. **Each role Deep Agent owns its own conversation history.** Role state lives in the role's checkpoint namespace. LangGraph's mounted-subgraph persistence uses the parent `thread_id` with a stable child `checkpoint_ns` derived from the node name (`project_manager`, `harness_engineer`, etc.). The PCG's `handoff_log` is not conversation history.

### 5.1 Gate Context Projection Bridge

Gate middleware runs inside mounted role Deep Agents, so it cannot read parent
`ProjectCoordinationState` directly. `dispatch_handoff` MUST build a minimal
`PCGGateContext` from PCG state before routing to any gated role:

```python
def _build_pcg_gate_context(state: ProjectCoordinationState) -> PCGGateContext:
    return {
        "org_id": state["org_id"],
        "project_id": state["project_id"],
        "project_thread_id": state["project_thread_id"],
        "current_phase": state.get("current_phase"),
        "current_agent": state.get("current_agent"),
        "handoff_log": state.get("handoff_log", []),
        "acceptance_stamps": state.get("acceptance_stamps", {}),
    }
```

For gated target roles (`project_manager`, `architect`, `developer`),
`dispatch_handoff` sends:

```python
Send(
    target,
    {
        "messages": [handoff_message],
        "pcg_gate_context": _build_pcg_gate_context(state_after_update),
    },
)
```

`pcg_gate_context` is child-agent state, not a PCG state channel. The gate
middleware declares a state schema that accepts it as input and omits it from
output:

```python
class PhaseGateState(AgentState):
    pcg_gate_context: NotRequired[Annotated[PCGGateContext, OmitFromOutput]]
```

Gate functions read `request.state["pcg_gate_context"]`. Missing
`pcg_gate_context` on a gated tool call is an implementation defect and must
raise, because returning a recoverable `ToolMessage` would hide a broken runtime
assembly.

The PM's `request_approval` tool is a special self-reentry path that bypasses
`dispatch_handoff`; therefore its `Send("project_manager", ...)` payload MUST
include a refreshed `pcg_gate_context` created by merging the new approval stamp
into the current projection. Without that refreshed projection, the next PM
tool call would see stale approval state even though the parent PCG update was
applied.

**Persistence contract.** The PCG is compiled with a concrete `BaseCheckpointSaver` instance (e.g., `PostgresSaver` in production, `SqliteSaver` in local/dev). Each role Deep Agent is compiled with `checkpointer=None` to inherit the parent's checkpointer. LangGraph's Checkpointer type semantics (types.py:96-102) define `None` as "inherits checkpointer from the parent graph." StateGraph.compile() (state.py:1038-1084) documents that `checkpointer=None` "may inherit the parent graph's checkpointer when used as a subgraph." During task execution, the checkpointer is propagated via `CONFIG_KEY_CHECKPOINTER` config (pregel/_algo.py:715-718): `CONFIG_KEY_CHECKPOINTER: (checkpointer or configurable.get(CONFIG_KEY_CHECKPOINTER))`.

**Namespace semantics.** The stable checkpoint namespace for a role is the node name (e.g., `project_manager`). LangGraph constructs task-specific namespaces as `checkpoint_ns = f"{parent_ns}{NS_SEP}{name}"` and `task_checkpoint_ns = f"{checkpoint_ns}{NS_END}{task_id}"` (pregel/_algo.py:592-602). The stable namespace used for checkpoint storage is the recast namespace, which removes task IDs via `recast_checkpoint_ns(ns)` (_config.py:34-45): `NS_SEP.join(part.split(NS_END)[0] for part in ns.split(NS_SEP) if not part.isdigit())`. When a role is re-invoked via a handoff, LangGraph resolves checkpoint storage using the recast namespace (role name without task ID) under the same `project_thread_id`, ensuring the role resumes its prior conversation history. The PCG's `handoff_log` is not conversation history; it is an audit trail of handoff events only.
7. **Durable cross-thread product data lives in the Project Data Plane.** `project_registry`, `artifact_manifest`, and `optimization_trendline` are not PCG state channels. PCG helpers call the data-plane operations defined in `docs/specs/project-data-plane.md`; LangGraph Store may cache derived slices but is not the source of truth.
8. **Graph lifecycle is PM-controlled.** `ask_user` interrupts fire inside the PM's Deep Agent subgraph. LangGraph's native interrupt machinery pauses the subgraph and the parent graph transparently; resume flows through automatically — no PCG-level interrupt code is required.

## 6. `Command.PARENT` Update Contract

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
- Stamp-writing tools are the only tools that write to `acceptance_stamps`:
  `submit_application_acceptance`, `submit_harness_acceptance`, and PM's
  `request_approval`.
- Artifact-manifest updates are Project Data Plane writes (`register_artifact`), not state updates.

### 6.1 Tool-helper-vs-PCG field ownership

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
- `langsmith_run_id` (from `langsmith.get_current_run_tree().id` if tracing is enabled; `None` otherwise)
- `created_at` (RFC3339 UTC timestamp at record creation time)
- `project_phase` (only when the handoff transitions the PCG lifecycle phase)
- `plan_phase_id` (only for Developer plan-phase review tools)
- `accepted` (only on `submit_*_acceptance` tool calls)

The PCG (`dispatch_handoff`) reads the appended record, calls Project Data
Plane `update_project_progress`, and routes to `target_agent`. It does not
populate fields inside a record after that record has already been appended by
the `operator.add` reducer. Records are immutable append-only audit entries.

### 6.2 Exception — PM-assembled handoff packages

For downstream pipeline delivery tools where the receiving agent needs the full accumulated artifact set, the PM assembles a consolidated project handoff package — a directory copied into the receiving agent's filesystem. The receiving agent owns and organizes that copy.

This applies to:

- `deliver_planning_package_to_planner` — Planner receives an organized package of design spec, public eval criteria, and public datasets.
- `deliver_development_package_to_developer` — Developer receives the full project package: plan, spec, public eval, PRD, research highlights. The Developer organizes this into a structured filesystem layout optimized for implementation and human readability.

Early-stage deliveries (`deliver_prd_to_harness_engineer`, `deliver_prd_to_researcher`, `deliver_design_package_to_architect`) remain as references because those specialists only need a few specific artifacts from the PM's already-organized namespace. The PM's role as organizer aligns with its identity as the business-oriented project manager who ensures artifacts are properly stored and structured before they flow downstream.

## 7. `HandoffRecord` Wire Format

Implementation serializes this record as either a Pydantic model or a
`TypedDict`-compatible dict, preserving the field set and enum values locked
below as AD decisions.

```json
{
  "project_id": "string",
  "project_thread_id": "string",
  "handoff_id": "string",
  "source_agent": "system|project_manager|harness_engineer|researcher|architect|planner|developer|evaluator",
  "target_agent": "project_manager|harness_engineer|researcher|architect|planner|developer|evaluator",
  "reason": "deliver|return|submit|consult|announce|question|coordinate",
  "brief": "string",
  "artifact_paths": ["string"],
  "langsmith_run_id": "string|null",
  "created_at": "RFC3339 UTC timestamp (Z suffix)",
  "project_phase": "scoping|research|architecture|planning|development|acceptance|null",
  "plan_phase_id": "string|null",
  "accepted": "boolean|null",
  "feedback": "string|null"
}
```

### Field notes

- **Core fields (always present):** `project_id`, `project_thread_id`, `handoff_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`, `langsmith_run_id`, `created_at`.
- **Optional fields (context-dependent):** `project_phase` (PCG lifecycle-phase-transitioning records only), `plan_phase_id` (Developer plan-phase review records only), `accepted` (acceptance-stamp records only).
- **`source_agent`** is a role name except for the synthesized first handoff,
  where it is `"system"`.
- **`target_agent` maps 1:1 to checkpoint namespace** in v1. This is a deliberate simplification for v1; the AD leaves open the possibility of multiple instances of a role in v2.
- **`reason` encodes transition type**, not pipeline phase. Middleware dispatches on `(source_agent, target_agent, reason)` triple. See `docs/specs/handoff-tools.md` for the mapping.
- **`langsmith_run_id`** is the LangSmith run ID for the handoff tool execution. Set at record creation time from `langsmith.get_current_run_tree().id` if tracing is enabled; `None` otherwise. SDK: `.venv/lib/python3.11/site-packages/langsmith/run_helpers.py:74-76`.
- **`created_at`** is an RFC3339 timestamp with UTC timezone (use "Z" suffix). Set at record creation time and never updated. Monotonic: each new record has a timestamp >= the previous record's timestamp.
- **`artifact_paths`** is a list of relative paths from the project root. The PCG does not validate that these paths exist; that is the handoff tool's responsibility.
- **`project_phase`** (optional) — populated only when the handoff transitions the PCG lifecycle phase. Supports the `current_phase` denormalization.
- **`plan_phase_id`** (optional) — populated only by Developer phase-review tools. The model-visible tool argument is named `phase`, but the record field is `plan_phase_id` to keep Developer implementation-plan phases distinct from the PCG lifecycle enum.
- **`accepted`** (optional) — populated only by stamp records: the two
  `submit_*_acceptance` tools and PM's `request_approval` tool. Carries the
  acceptance or approval boolean.
- **`feedback`** (optional) — populated by `request_approval` when the approval
  is rejected. Carries the human-provided rejection feedback for the PM's
  approval-result re-entry message. `None` for approvals and non-approval
  handoffs.

## 8. Project Data Plane Cross-Reference

`pcg-data-contracts.md` does not define product data-plane schemas. Handoff
`artifact_paths` are references carried in the audit record; they are not the
artifact manifest. Artifact-producing helpers call Project Data Plane
`register_artifact`; `dispatch_handoff` calls `update_project_progress`; Harness
Engineer trendline helpers call `record_trendline_point`.

The Project Data Plane owns durable cross-surface records, tenant boundaries,
read/write APIs, access events, retention, deletion, schema versioning, and
Developer-private / HE-private exclusions. See
[`project-data-plane.md`](./project-data-plane.md).

## 9. `dispatch_handoff` Node Contract (reference implementation sketch)

Not normative code, but the semantic contract every conforming implementation must preserve. The dispatcher is a pure routing function — it returns `Command(goto=Send(...))` and never calls `.ainvoke()` on a role graph. LangGraph routes into the mounted role subgraph node through the Pregel loop once the Command is emitted.

### 9.1 Routing Primitive

The dispatcher MUST use `Send(target_agent, child_input)` as the `goto` value,
not a string. `child_input` always includes `messages` and includes
`pcg_gate_context` for gated roles. SDK behavior:
- `Send` yields to `TASKS` channel (`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`)
- `packet.arg` is passed directly as the subgraph's input (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`)
- Base Deep Agent input receives `messages`; gated roles receive `messages`
  plus `pcg_gate_context` through gate middleware state schema

String `goto` (e.g., `Command(goto="project_manager")`) is **forbidden** — it triggers PULL task semantics that read from parent channels, which would incorrectly pass PCG's user-facing `messages` to the child.

### 9.2 Receiving-Agent Input Payload Shape

The `Send.arg` MUST be a dict with one required key and one optional gated-role
key:

```python
{
    "messages": [
        {
            "role": "user",
            "content": "[[Handoff from {source_agent}]]\n\n{brief}\n\n[[Artifacts]]\n{artifact_list}",
            "name": None,  # Optional: could include handoff_id as metadata
        }
    ],
    # Present only when target role has phase-gate middleware.
    "pcg_gate_context": PCGGateContext,
}
```

**Field specifications:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `list[HumanMessage]` | Yes | Exactly one rendered handoff packet for the receiving role |
| `pcg_gate_context` | `PCGGateContext` | Only for gated roles | Dispatcher-created projection used by phase-gate middleware; not rendered into `messages` and omitted from child output |
| `role` | `Literal["user"]` | Yes | Fixed as `"user"` — the handoff arrives as a user message from the perspective of the receiving agent |
| `content` | `str` | Yes | Formatted handoff packet (see §9.3) |

### 9.3 Handoff Message Content Format

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

### 9.4 Pre-Routing Validation Rules

Before constructing the `Send`, the dispatcher MUST validate:

1. **`target_agent` presence**: `HandoffRecord.target_agent` must be non-empty and in `ROLE_GRAPHS.keys()`. **Failure**: raise `ValueError(f"Invalid target_agent: {target_agent}")` — do not route.

2. **`brief` presence**: `HandoffRecord.brief` must be non-empty string after stripping whitespace. **Failure**: raise `ValueError("HandoffRecord.brief is empty")` — do not route.

3. **`artifact_paths` validity**: Each path must be a string starting with `/` (absolute) or a valid relative path. **Failure**: raise `ValueError(f"Invalid artifact path: {path}")` — do not route.

4. **Sanity check**: `source_agent != target_agent` (no self-handoff). **Failure**: raise `ValueError("Self-handoff not permitted")` — do not route.

All validation failures are **hard stops** — the dispatcher does not emit a `Command`, allowing Pregel to surface the exception to the caller.

### 9.5 Initial Stakeholder Input to First PM Turn

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

### 9.6 Reference Implementation

```python
from typing import Any
from langgraph.types import Command, Send
from langchain_core.messages import HumanMessage

GATED_ROLE_NAMES = {"project_manager", "architect", "developer"}

def _child_input_for(target: AgentName, handoff_message: HumanMessage, state: ProjectCoordinationState) -> dict[str, Any]:
    child_input: dict[str, Any] = {"messages": [handoff_message]}
    if target in GATED_ROLE_NAMES:
        child_input["pcg_gate_context"] = _build_pcg_gate_context(state)
    return child_input

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

    # --- 4. Update project registry ----------------------------------------------
    await update_project_progress(
        org_id=state["org_id"],
        project_id=state["project_id"],
        project_thread_id=state["project_thread_id"],
        current_phase=record.get("project_phase", state.get("current_phase")),
        current_agent=target,
        last_handoff_id=record["handoff_id"],
        last_handoff_at=record["created_at"],
        trace_context={
            "thread_id": runtime.execution_info.thread_id,
            "project_thread_id": state["project_thread_id"],
            "run_id": runtime.execution_info.run_id,
            "langsmith_run_id": record.get("langsmith_run_id"),
            "handoff_id": record["handoff_id"],
            "source_agent": record["source_agent"],
        },
    )

    # --- 5. Route via Send (not string goto) -------------------------------------
    if not state["handoff_log"]:
        # First invocation: include initial state updates
        state_after_update = {
            **state,
            "handoff_log": [record],
            "current_agent": target,
            "current_phase": record.get("project_phase", "scoping"),
        }
        return Command(
            goto=Send(target, _child_input_for(target, handoff_message, state_after_update)),
            update={
                "handoff_log": [record],
                "org_id": state["org_id"],
                "current_agent": target,
                "current_phase": record.get("project_phase", "scoping"),
            },
        )
    else:
        # Re-entry: route to target with handoff message
        return Command(goto=Send(target, _child_input_for(target, handoff_message, state)))
```

**How routing actually works.** When `dispatch_handoff` emits `Command(goto=Send("project_manager", {"messages": [handoff_message], "pcg_gate_context": gate_context}))`, LangGraph's Pregel loop:
1. Maps the `Send` to the `TASKS` channel (`.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:66-67`)
2. Creates a PUSH task where `packet.arg` is passed directly as the subgraph's input (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`)
3. The mounted Deep Agent subgraph receives the input filtered through its declared input schema. Base roles accept `messages`; gated roles accept `messages` plus `pcg_gate_context` through their gate-middleware state schema.
4. The subgraph runs until one of its internal nodes emits a Command. If a handoff tool emits `Command(graph=PARENT, goto="dispatch_handoff", update={...})`, the inner Pregel raises `ParentCommand`; the outer Pregel catches it, applies the update to PCG state via reducers, and re-enters `dispatch_handoff`. If `finish_to_user` emits `Command(graph=PARENT, goto=END, update={...})`, the outer Pregel applies the `messages` update and terminates the graph. Natural completion of a role subgraph is not expected and should be prevented by the final-turn-guard middleware.

## 10. Growth, Cap, and Migration Notes

- `messages` is bounded by natural PM completion frequency. Headless ingress may produce multiple lifecycle cycles; the channel is not artificially capped at 2 entries.
- `handoff_log` has no cap in v1. Projects have finite handoff counts. HE participation detection (scanning for `source_agent` or `target_agent == "harness_engineer"`) must work correctly regardless of log size. If cap becomes necessary in v2, move handoff history into the Project Data Plane and update gate logic to read from a data-plane operation, not checkpoint state.
- `acceptance_stamps` has a natural bound of 4 entries (`application`,
  `harness`, `scoping_to_research`, `architecture_to_planning`). No cap needed.
- Project Data Plane records grow outside state-checkpoint pressure; retention, archival, deletion, and migration rules are defined in `project-data-plane.md`.

## 11. Conformance Tests (minimum set)

Implementation must pass at least these assertions:

1. A `HandoffRecord` appended to `handoff_log` via a `Command.PARENT` update round-trips through checkpoint save/load without type coercion loss (detects accidental reintroduction of `add_messages` on this channel).
2. `dispatch_handoff` returns a `Command` with `goto=Send(<role_name>, child_input)` for one of the 7 role names, where `child_input["messages"]` contains the rendered handoff packet and gated-role inputs also include `pcg_gate_context`. It never calls `.ainvoke()` or `.invoke()` on a role graph (static analysis: search for `ROLE_GRAPHS[...].ainvoke` or `.invoke` inside dispatcher source — must have zero matches).
3. Every role's handoff-tool set and the PM's `finish_to_user` tool together cover the role's possible terminal actions. A final-turn-guard middleware re-prompts any role whose last `AIMessage` lacks a tool call to a handoff tool or `finish_to_user`.
4. User approval gates and the acceptance gate on `return_product_to_pm` read `request.state["pcg_gate_context"]["acceptance_stamps"]` and not `handoff_log` for stamp truth (static analysis or unit test).
5. `current_phase == <most recent non-null HandoffRecord.project_phase> or <previously-set lifecycle phase>` after every handoff (denormalization consistency). `plan_phase_id` must never drive `current_phase`.
6. `dispatch_handoff` calls Project Data Plane `update_project_progress` on every handoff (fuzz: random-length handoff chains, verify `project_registry` matches the last record).
7. Developer-role runtime cannot call trendline, HE-private artifact, Evaluator-private artifact, or live-snapshot reads (toolset and data-access policy tests in `project-data-plane.md`).

## 12. Conformance Matrix

| Channel/Field | Owner | Writer | Reader | Reducer | Validation Rule | Test Expectation |
|---------------|-------|--------|--------|---------|----------------|-----------------|
| `messages` | PCG | PM's `finish_to_user` only | External surfaces (TUI, web app, headless) | `add_messages` | Must be `list[AnyMessage]`; never written by handoff tools | Only `finish_to_user` writes; specialist agents never read |
| `org_id` | PCG | `dispatch_handoff` (initial) | `dispatch_handoff`, data-plane writers | overwrite | Must be non-empty string | Immutable after initialization |
| `project_id` | PCG | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, data-plane writers | overwrite | Must be non-empty string | Immutable after initialization |
| `project_thread_id` | PCG | `dispatch_handoff` (initial) | `dispatch_handoff`, middleware, data-plane writers | overwrite | Must be non-empty string | Immutable after initialization |
| `current_phase` | PCG | Handoff tools (when `project_phase` present) | `dispatch_handoff` projection into gate middleware | overwrite | Must be one of `ProjectPhase` enum values | Matches most recent `HandoffRecord.project_phase` |
| `current_agent` | PCG | Handoff tools | `dispatch_handoff`, middleware | overwrite | Must be one of `AgentName` enum values | Matches `handoff_log[-1].target_agent` |
| `handoff_log` | PCG | Handoff tools | `dispatch_handoff`, HE-participation helper | `operator.add` (list concatenation) | Each record must be valid `HandoffRecord` | Append-only; no cap in v1; HE detection works at any size |
| `acceptance_stamps` | PCG | `submit_*_acceptance`, `request_approval` tools | `dispatch_handoff` projection into user-approval gates and `return_product_to_pm` gate | merge-dict | Keys must be `StampKey`; values must be `HandoffRecord` with `accepted` field | Gates read this via `pcg_gate_context`, never `handoff_log` |
| `HandoffRecord.project_id` | PCG | Tool helper | All readers | N/A | Must match PCG `project_id` | Invariant: all records in same log have same `project_id` |
| `HandoffRecord.source_agent` | PCG | Tool helper or initial bootstrap synthesis | All readers | N/A | Must be one of `HandoffSourceAgent` enum values | Must be valid role name (snake_case) or `"system"` for initial bootstrap only |
| `HandoffRecord.target_agent` | PCG | Tool helper | All readers | N/A | Must be one of `AgentName` enum values | Must be valid role name (snake_case) |
| `HandoffRecord.reason` | PCG | Tool helper | All readers | N/A | Must be one of `Reason` enum values | Must be valid reason value |
| `HandoffRecord.langsmith_run_id` | PCG | Tool helper | All readers | N/A | Must be string or `None` | From `langsmith.get_current_run_tree().id` if tracing enabled |
| `HandoffRecord.created_at` | PCG | Tool helper | All readers | N/A | Must be RFC3339 UTC with "Z" suffix | Monotonic: each new record >= previous |
| `HandoffRecord.accepted` | PCG | `submit_*_acceptance`, `request_approval` tools | Gate logic through `pcg_gate_context` | N/A | Must be boolean on stamp records | Gates require both presence AND `accepted is True` |
8. **Receiving-agent input contains rendered HandoffRecord packet, not raw PCG messages.** Given a mounted role subgraph with a spy node that captures its input, when `dispatch_handoff` routes to that role, the spy receives exactly one `HumanMessage` with:
   - `content` containing the formatted handoff packet per §9.3
   - `role == "user"`
   - The `brief` text from `HandoffRecord` appears verbatim in the content
   - The `artifact_paths` are rendered as a bullet list
   The raw PCG `messages` channel MUST NOT appear in the child's input. Gated
   roles additionally receive `pcg_gate_context`; non-gated roles do not. The
   projection is not rendered into messages and is omitted from role output.
9. **Role graphs are compiled with checkpointer=None.** Static analysis: verify that each `create_<role>_agent()` call in `_build_role_graphs()` passes `checkpointer=None` explicitly. This enables runtime inheritance from the parent PCG's checkpointer per the persistence contract. However, static analysis alone cannot verify actual inheritance — the runtime mechanism is CONFIG_KEY_CHECKPOINTER config propagation during task execution (SDK verification: types.py:96-102 defines None=inherit; _algo.py:715-718 shows CONFIG_KEY_CHECKPOINTER propagation; main.py:1265-1266 shows checkpointer resolution from config). **Runtime verification is provided by tests #10 and #11**, which verify checkpoint namespace persistence under the parent's checkpointer, proving that role subgraphs actually inherit the parent's checkpointer at runtime.
10. **Repeated role invocation preserves role-local conversation history.** Given a project thread with a PCG compiled with a concrete checkpointer, execute a handoff chain: PM -> Harness Engineer -> PM -> Harness Engineer. After the second Harness Engineer invocation, query the Harness Engineer's checkpoint namespace (via `graph.get_state(config={"configurable": {"thread_id": project_thread_id, "checkpoint_ns": "harness_engineer"}})`). The role's `messages` state must contain messages from both Harness Engineer turns, proving checkpoint resumption from the stable namespace under the same `project_thread_id`. The PCG's `handoff_log` must contain exactly 4 records (PM->HE, HE->PM, PM->HE, HE->PM), proving that role conversation history is not stored in PCG state.
11. **Different roles do not share conversation history.** Execute a handoff chain: PM -> Harness Engineer -> Researcher -> Harness Engineer. Query the Researcher's checkpoint namespace (`checkpoint_ns="researcher"`). Its `messages` must contain only the Researcher's turn messages, not the Harness Engineer's messages. Query the Harness Engineer's checkpoint namespace (`checkpoint_ns="harness_engineer"`). Its `messages` must contain messages from both Harness Engineer turns, proving namespace isolation.
12. **PCG state does not absorb role-local messages except via explicit parent commands.** After a multi-turn handoff chain, query the PCG's checkpoint namespace (empty string, the root). The PCG's `messages` channel must contain only messages written by the PM's `finish_to_user` tool (if any), not any role-local conversation history. The PCG's `handoff_log` must contain the full audit trail, but this is structured data, not conversation history.
