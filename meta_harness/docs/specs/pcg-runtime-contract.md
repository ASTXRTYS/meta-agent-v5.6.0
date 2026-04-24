---
doc_type: spec
derived_from:
  - AD §4 PM Session And Project Entry Model
  - AD §4 Identity Linkage and Cardinality
  - AD §4 LangGraph Project Coordination Graph Factory Contract
status: active
last_synced: 2026-04-24
owners: ["@Jason"]
---
# PCG Runtime Contract Specification

> **Provenance:** Derived from `AD.md §4 PM Session And Project Entry Model`, `§4 Identity Linkage and Cardinality`, and `§4 LangGraph Project Coordination Graph Factory Contract`.
> **Status:** Active · **Last synced with AD:** 2026-04-24 (org identity bridge synced for Ticket 6 / Project Data Plane)
> **Consumers:** Developer (graph factory implementation), Agent Server callers (web app, headless ingress adapters, PM session tools), Evaluator (conformance checking).

## 1. Purpose

The parent AD names `ProjectCoordinationInput`, `ProjectCoordinationContext`, and `ProjectCoordinationOutput` as the LangGraph StateGraph schemas for the Project Coordination Graph (PCG), and the repo layout spec uses them in the graph factory signature. This spec defines their exact fields, required/optional status, runtime sources, and the bootstrap contract for project thread creation from both UI-onboarding and chat-driven paths. It resolves the conflict between PCG `messages` as PM-terminal user output and initial stakeholder input as the first handoff source.

**Relationship to `pcg-data-contracts.md`.** This spec owns the Agent Server boundary contract: input/context/output schemas, thread metadata, bootstrap behavior, and the mapping from external caller to PCG state initialization. `docs/specs/pcg-data-contracts.md` owns the internal PCG state schema (channels, reducers, `HandoffRecord`, `Command.PARENT` update contract). The two specs are siblings: runtime bootstrap readers consult this spec; PCG state channel readers consult `pcg-data-contracts.md`.

## 2. Thread Identity Model (recap from AD)

| Identity | Meaning | Source |
|---|---|---|
| `thread_id` | LangGraph checkpoint/conversation identity | LangGraph Agent Server (generated or caller-provided) |
| `project_id` | Durable Meta Harness project identity | Caller-provided (or system-generated for UI-onboarding) |
| `project_thread_id` | Canonical LangGraph thread for one executable project | LangGraph Agent Server (caller-provided or generated) |
| `pm_session_thread_id` | LangGraph thread for non-project/cross-project PM conversation | LangGraph Agent Server (caller-provided or generated) |

**Key invariants from AD:**
- `project_thread_id` may equal `project_id` in local/dev by convention, but that is not the definition of `project_id`.
- `pm_session` is not a second PM identity and not a `ProjectCoordinationState` key. It is a LangGraph thread with metadata `thread_kind = "pm_session"`.
- The link from a project back to its originating `pm_session` (if any) lives in the Project Data Plane `project_registry` record as a nullable `pm_session_thread_id` field. `null` denotes UI-onboarding path (no originating session).
- A single `pm_session` thread may spawn multiple `project` threads over its lifetime (one-to-many, append never overwrite).
- PM session threads and project threads are fully independent LangGraph threads; they do not share a Pregel namespace hierarchy.

## 3. `ProjectCoordinationInput` Schema

The input schema defines what external callers (web app, headless ingress adapters, PM session tools) provide when invoking the PCG. This is the `input_schema` parameter to the LangGraph `StateGraph` constructor.

```python
class AutonomousModeConfig(TypedDict, total=False):
    enabled: bool

class ProjectCoordinationInput(TypedDict, total=False):
    org_id: str
    project_id: str
    project_thread_id: str | None
    pm_session_thread_id: str | None
    initial_stakeholder_input: str
    initial_artifact_paths: list[str] | None
    autonomous_mode_config: AutonomousModeConfig | None
```

### Field table

| Field | Type | Required | Source | Purpose |
|-------|------|----------|--------|---------|
| `org_id` | `str` | Yes | Authenticated surface/backend, PM tool, or headless ingress adapter | Tenant identity used by Project Data Plane rows and authorization. Must match thread metadata `org_id`. |
| `project_id` | `str` | Yes | Caller (web app, headless ingress, PM tool) or system-generated (UI-onboarding) | Durable Meta Harness project identity. Used as the primary key in Project Data Plane records (`project_registry`, `artifact_manifest`, `optimization_trendline`). |
| `project_thread_id` | `str \| None` | No | Caller (web app, headless ingress, PM tool) or LangGraph Agent Server (if omitted, SDK generates UUID) | Canonical LangGraph thread for project execution. If omitted, the Agent Server generates a UUID. Must equal the `thread_id` of the LangGraph thread on which the PCG runs. |
| `pm_session_thread_id` | `str \| None` | No | Caller (web app onboarding flow) or PM tool (chat-driven path) | Link back to originating `pm_session` thread. `null` denotes UI-onboarding path (no originating session). Stored in `project_registry.pm_session_thread_id`. |
| `initial_stakeholder_input` | `str` | Yes | Caller (web app onboarding form, headless ingress payload, PM tool synthesis) | The initial stakeholder request that becomes the first PM turn. Synthesized by `dispatch_handoff` into the initial `HandoffRecord` with `source_agent="system"`, `target_agent="project_manager"`, `reason="coordinate"`. |
| `initial_artifact_paths` | `list[str] \| None` | No | Caller (web app onboarding file upload, headless ingress attachment list) | Optional filesystem paths to pre-existing artifacts (e.g. uploaded PRD, reference spec). Included in the initial `HandoffRecord.artifact_paths`. |
| `autonomous_mode_config` | `AutonomousModeConfig \| None` | No | Caller (headless ingress adapter, future web app autonomous toggle) | Runtime toggle for autonomous execution. `enabled=true` means approval gates auto-approve as specified in `approval-and-gate-contracts.md`; timeout policies and checkpoint cadence remain future decisions. |

### Field sourcing rules

- **UI-onboarding path:** The web app backend calls `client.threads.create(metadata={"thread_kind": "project", "org_id": org_id}, thread_id=<caller-provided-or-generated>)` then `client.runs.create(thread_id=..., input={...ProjectCoordinationInput...})`. The web app provides `org_id`, `project_id`, `pm_session_thread_id=null`, `initial_stakeholder_input`, and optionally `initial_artifact_paths`. The Agent Server generates `project_thread_id` if omitted.
- **Chat-driven path:** The PM's `spawn_project` tool calls the Agent Server thread-create API from inside its execution context. The PM provides `org_id` from the current PM session thread metadata, `project_id` (or requests system generation), `pm_session_thread_id` (the current PM session's thread_id), `initial_stakeholder_input` (synthesized from conversation context), and optionally `initial_artifact_paths`. The Agent Server generates `project_thread_id` if omitted.
- **Headless ingress path:** The ingress adapter (Slack, email, Discord, GitHub, Linear) calls the Agent Server APIs directly. The adapter resolves `org_id`, provides `project_id` (if resuming) or requests system generation, sets `pm_session_thread_id=null` (headless has no PM session), provides `initial_stakeholder_input` (parsed from ingress event), and optionally provides `initial_artifact_paths` (attachments).

### Idempotency behavior

Repeated project-spawn attempts with the same `project_id`:
- **If `project_thread_id` is provided:** The caller asserts a specific thread identity. If a thread with that `thread_id` already exists, the behavior depends on the LangGraph SDK `if_exists` parameter passed to `threads.create()`. Meta Harness callers SHOULD use `if_exists="do_nothing"` and validate that the existing thread's `thread_kind="project"` metadata matches expectations before proceeding.
- **If `project_thread_id` is omitted:** The Agent Server generates a new UUID on each call. Multiple calls with the same `project_id` but omitted `project_thread_id` create multiple distinct threads — this is a caller error. The Project Data Plane enforces `(org_id, project_id)` uniqueness and rejects conflicting `project_thread_id` values.

## 4. `ProjectCoordinationContext` Schema

The context schema defines runtime context injected by LangGraph via the `Runtime[ContextT]` object. This is the `context_schema` parameter to the LangGraph `StateGraph` constructor. Context is read-only from the graph's perspective and does not participate in state checkpointing.

```python
class ProjectCoordinationContext(TypedDict, total=False):
    execution_info: ExecutionInfo
    server_info: ServerInfo | None
```

### Field table

| Field | Type | Required | Source | Purpose |
|-------|------|----------|--------|---------|
| `execution_info` | `ExecutionInfo` | Yes | LangGraph Runtime (injected) | Read-only execution metadata: `checkpoint_id`, `checkpoint_ns`, `task_id`, `thread_id`, `run_id`, `node_attempt`, `node_first_attempt_time`. See `.venv/lib/python3.11/site-packages/langgraph/runtime.py:24-55`. |
| `server_info` | `ServerInfo \| None` | No | LangGraph Server (injected when running on LangGraph Platform) | Server metadata: `assistant_id`, `graph_id`, `user`. `None` when running open-source LangGraph without LangSmith deployments. See `.venv/lib/python3.11/site-packages/langgraph/runtime.py:58-74`. |

### Usage pattern

The `dispatch_handoff` coordination node receives the `Runtime[ProjectCoordinationContext]` as a parameter:

```python
async def dispatch_handoff(
    state: ProjectCoordinationState,
    runtime: Runtime[ProjectCoordinationContext],
) -> Command:
    thread_id = runtime.execution_info.thread_id
    run_id = runtime.execution_info.run_id
    # ... use runtime.context for server_info if needed
```

Context is NOT part of checkpoint state. It is injected fresh on each graph invocation by the LangGraph runtime.

## 5. `ProjectCoordinationOutput` Schema

The output schema defines what the PCG returns to external callers. This is the `output_schema` parameter to the LangGraph `StateGraph` constructor. Output is derived from the final PCG state after graph completion.

```python
class ProjectCoordinationOutput(TypedDict, total=False):
    messages: list[AnyMessage]
    org_id: str
    project_id: str
    project_thread_id: str
    current_phase: str
    current_agent: str | None
    status: Literal["active", "paused", "completed", "failed"]
```

### Field table

| Field | Type | Required | Source | Purpose |
|-------|------|----------|--------|---------|
| `messages` | `list[AnyMessage]` | Yes | PCG state `messages` channel (PM's `finish_to_user` tool) | User-facing output. Written only by the PM's terminal `finish_to_user` tool via `Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`. |
| `org_id` | `str` | Yes | PCG state `org_id` channel | Tenant identity echoed back to caller for confirmation and data-plane correlation. |
| `project_id` | `str` | Yes | PCG state `project_id` channel | Durable project identity, echoed back to caller for confirmation. |
| `project_thread_id` | `str` | Yes | PCG state `project_thread_id` channel | Canonical execution thread identity, echoed back to caller. |
| `current_phase` | `str` | Yes | PCG state `current_phase` channel | Lifecycle phase at graph completion. |
| `current_agent` | `str \| None` | No | PCG state `current_agent` channel | Which agent was active when the graph completed. `None` if graph terminated without an active agent (e.g. terminal emission). |
| `status` | `Literal["active", "paused", "completed", "failed"]` | Yes | Derived from Project Data Plane `project_registry` or termination condition | Project status at graph completion. Set to `"completed"` on PM's `finish_to_user` terminal emission. Set to `"failed"` on unhandled exception. Set to `"paused"` on interrupt (HITL). Default `"active"` otherwise. |

### Output on resume

When resuming a project thread (subsequent run on the same `project_thread_id`):
- `messages` contains only the NEW messages written since the last checkpoint (the `add_messages` reducer appends).
- Other fields reflect the current PCG state at resumption time.
- The caller should distinguish "initial bootstrap output" (first run, `handoff_log` empty) from "resumption output" (subsequent run, `handoff_log` non-empty) by checking the run history or the Project Data Plane `project_registry.last_handoff_at` timestamp.

## 6. Thread Metadata Contract

Every LangGraph thread created for Meta Harness MUST include the following metadata keys in the `metadata` dict passed to `threads.create()` or `runs.create()`:

| Key | Value | Required | Thread kind |
|-----|-------|----------|-------------|
| `thread_kind` | `"pm_session"` or `"project"` | Yes | Both |
| `org_id` | `str` | Yes | Both |
| `project_id` | `str` (the durable project identity) | Yes for `project` threads | `project` only |
| `pm_session_thread_id` | `str \| None` | No (null for UI-onboarding) | `project` only |
| `autonomous_mode` | `bool` | No (defaults false) | `project` only |

**Enforcement:** The Agent Server does not enforce these metadata keys natively. Meta Harness callers (web app backend, PM session tools, headless ingress adapters) MUST include them. Conformance tests SHOULD verify that thread creation calls include the required metadata.

### 6.1 Autonomous Mode Runtime Config Bridge

LangGraph SDK run APIs accept a `config` argument (`runs.create(...,
config=...)` / `runs.stream(..., config=...)`). Meta Harness callers MUST bridge
the input/thread toggle into runnable config on every project run:

```python
autonomous_mode = bool(
    input.get("autonomous_mode_config", {}).get("enabled")
    if input.get("autonomous_mode_config") is not None
    else thread_metadata.get("autonomous_mode", False)
)

client.runs.create(
    thread_id=project_thread_id,
    assistant_id="meta-harness-project-coordination-graph",
    input=input,
    config={"configurable": {"autonomous_mode": autonomous_mode}},
)
```

The approval and terminal-emission spec reads only
`runtime.config["configurable"]["autonomous_mode"]`. It does not read
`ProjectCoordinationInput` or thread metadata directly. Missing
`configurable.autonomous_mode` is treated as `False`.

## 7. Bootstrap Behavior

### 7.1 First invocation contract

On first PCG invocation (empty `handoff_log`), the `dispatch_handoff` coordination node:

1. Extracts `initial_stakeholder_input` and `initial_artifact_paths` from `ProjectCoordinationInput` (NOT from PCG `messages` channel, which is reserved for PM-terminal output).
2. Synthesizes a `HandoffRecord` with:
   - `source_agent`: `"system"` (special value for initial bootstrap)
   - `target_agent`: `"project_manager"`
   - `reason`: `"coordinate"`
   - `brief`: The `initial_stakeholder_input` text
   - `artifact_paths`: `initial_artifact_paths` or empty list
   - `project_id`, `project_thread_id`: from PCG state (populated from input on first invocation)
   - `handoff_id`: generated (e.g. `uuid4()`)
   - `langsmith_run_id`: from `runtime.execution_info.run_id`
   - `created_at`: RFC3339 timestamp
3. Copies `org_id` from input/thread metadata into PCG state and appends the synthesized record to `handoff_log` via the initial state update.
4. Sets `current_agent = "project_manager"` and `current_phase = "scoping"` via the initial state update.
5. Constructs the handoff message per `pcg-data-contracts.md §9.3` and emits `Command(goto=Send("project_manager", child_input))`, where `child_input` contains the handoff message and PM's `pcg_gate_context`.

This ensures the initial PM turn receives the stakeholder request as a formatted handoff message, identical to subsequent inter-agent handoffs. The PCG `messages` channel remains empty until the PM's terminal `finish_to_user` tool writes to it.

### 7.2 UI-onboarding path

1. User completes onboarding flow in web app.
2. Web app backend collects `project_id` (or requests system generation), `initial_stakeholder_input`, and optional `initial_artifact_paths`.
3. Web app backend calls `client.threads.create(metadata={"thread_kind": "project", "org_id": org_id, "project_id": project_id, "pm_session_thread_id": None}, thread_id=<caller-provided-or-generated>)`.
4. Web app backend calls `client.runs.create(thread_id=project_thread_id, input={ProjectCoordinationInput...}, assistant_id="meta-harness-project-coordination-graph")`.
5. Agent Server invokes the PCG with the provided input.
6. `dispatch_handoff` executes the first-invocation contract (§7.1).
7. User lands in the project thread immediately; the web app UI switches to project view.

### 7.3 Chat-driven path

1. User chats with PM on a `pm_session` thread.
2. PM perceives readiness and calls session-scoped `spawn_project` tool with synthesized `initial_stakeholder_input`.
3. `spawn_project` tool body calls `client.threads.create(metadata={"thread_kind": "project", "org_id": org_id, "project_id": project_id, "pm_session_thread_id": runtime.execution_info.thread_id}, thread_id=<caller-provided-or-generated>)` from inside its execution context.
4. Tool returns `{project_id, project_thread_id, status}` to the PM and (via tool output) to the surface.
5. Surface backend calls `client.runs.create(thread_id=project_thread_id, input={ProjectCoordinationInput...}, assistant_id="meta-harness-project-coordination-graph")`.
6. Agent Server invokes the PCG with the provided input.
7. `dispatch_handoff` executes the first-invocation contract (§7.1).
8. Surface navigates the user's active thread pointer to the new `project_thread_id`.

### 7.4 Headless ingress path

1. Ingress event arrives (Slack message, email, GitHub issue, Linear ticket, etc.).
2. Ingress adapter parses the event into `initial_stakeholder_input` and optional `initial_artifact_paths`.
3. Ingress adapter determines if this is a new project (no existing `project_id` binding) or a resumption (existing `project_id` in adapter state).
4. For new project: adapter calls `client.threads.create(metadata={"thread_kind": "project", "org_id": org_id, "project_id": <generated-or-provided>, "pm_session_thread_id": None})` then `client.runs.create(thread_id=project_thread_id, input={ProjectCoordinationInput...})`.
5. For resumption: adapter calls `client.runs.create(thread_id=existing_project_thread_id, input={ProjectCoordinationInput...})` with `initial_stakeholder_input` set to the new user message.
6. Agent Server invokes the PCG.
7. For new project: `dispatch_handoff` executes the first-invocation contract (§7.1).
8. For resumption: `dispatch_handoff` reads `handoff_log[-1]` and routes to `target_agent` normally.

## 8. Input-to-State Mapping for Bootstrap Fields

The `dispatch_handoff` coordination node requires access to bootstrap fields (`initial_stakeholder_input`, `initial_artifact_paths`) that are not part of the PCG state schema. LangGraph's input-to-state mapping requires careful handling to ensure these fields are accessible to the node.

### The mapping mechanism

LangGraph's `StateGraph` registers schemas via `_add_schema` per `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:250-271`:
```python
self._add_schema(self.state_schema)
self._add_schema(self.input_schema, allow_managed=False)
self._add_schema(self.output_schema, allow_managed=False)
```

Each schema maps to a dict of channels: `self.schemas[schema] = {**channels, **managed}`.

The START node writes input fields to state channels based on the graph-level `input_schema` per line 1240-1242:
```python
output_keys = [
    k
    for k, v in self.builder.schemas[self.builder.input_schema].items()
    if not is_managed_value(v)
]
```

For non-START nodes, the node reads from channels based on its declared `input_schema` per lines 1308-1309:
```python
input_schema = node.input_schema if node else self.builder.state_schema
input_channels = list(self.builder.schemas[input_schema])
```

### The failure mode

If `ProjectCoordinationInput` has fields not in `ProjectCoordinationState`, and `dispatch_handoff` only accepts `ProjectCoordinationState`, the bootstrap fields are written to state channels by START but not read by the node because the node's `input_channels` don't include those fields.

### The correct pattern

The graph-level `input_schema` MUST be a superset of the node's input schema for the node to access all input fields. There are two valid approaches:

**Approach A: Node-level input schema (preferred)**
- Declare a node-level `DispatchHandoffInput` that extends `ProjectCoordinationState` with bootstrap fields
- Pass `input_schema=DispatchHandoffInput` to `builder.add_node("dispatch_handoff", ...)`
- The node function signature accepts `DispatchHandoffInput`
- LangGraph registers `DispatchHandoffInput` in `self.schemas` and the node reads from those channels

**Approach B: Bootstrap fields in state schema (rejected)**
- Add `initial_stakeholder_input` and `initial_artifact_paths` to `ProjectCoordinationState`
- These become persistent state channels
- Violates the invariant that PCG state is only for coordination data

This spec uses **Approach A** to keep bootstrap fields transient (only on first invocation) and avoid polluting the persistent state schema.

### DispatchHandoffInput schema

```python
class DispatchHandoffInput(TypedDict, total=False):
    # Inherits all ProjectCoordinationState channels
    messages: list[AnyMessage]
    org_id: str
    project_id: str
    project_thread_id: str
    current_phase: Literal["scoping","research","architecture","planning","development","acceptance"]
    current_agent: Literal["project_manager","harness_engineer","researcher","architect","planner","developer","evaluator"]
    handoff_log: list[HandoffRecord]
    acceptance_stamps: dict[Literal["application","harness","scoping_to_research","architecture_to_planning"], HandoffRecord]
    # Bootstrap fields (only on first invocation)
    initial_stakeholder_input: str
    initial_artifact_paths: list[str] | None
```

### Factory contract

```python
builder.add_node(
    "dispatch_handoff",
    dispatch_handoff,
    input_schema=DispatchHandoffInput,  # node-level input schema
)
```

Node function signature:
```python
async def dispatch_handoff(
    state: DispatchHandoffInput,  # node-level input, not ProjectCoordinationState
    runtime: Runtime[ProjectCoordinationContext],
) -> Command:
```

On first invocation, bootstrap fields are populated from graph-level `ProjectCoordinationInput`. On subsequent invocations, these fields are `None` or empty, and the node reads from `handoff_log[-1]`.

## 9. `messages` Channel Invariant Resolution

**Conflict resolved:** PCG `messages` is described as PM-terminal user output, while initial project bootstrap uses stakeholder input to create the first handoff.

**Resolution:** The `messages` channel is strictly the user-facing I/O conduit written ONLY by the PM's `finish_to_user` tool. Initial stakeholder input does NOT flow through `messages` at all. It flows through `ProjectCoordinationInput.initial_stakeholder_input`, which `dispatch_handoff` synthesizes into the initial `HandoffRecord` on first invocation. The handoff brief is then passed to the PM via the `Send` payload as the child's `messages` input (per `pcg-data-contracts.md §9.2`). This preserves the invariant that PCG `messages` contains only PM-terminal output, while still giving the PM the stakeholder input as its first turn.

**On resume:** Subsequent runs on the same `project_thread_id` receive user input via the `input` parameter to `runs.create()`. The caller provides a new `ProjectCoordinationInput` with a fresh `initial_stakeholder_input`. `dispatch_handoff` treats this as a new handoff from "system" to the current agent, synthesizes a `HandoffRecord`, and routes accordingly. The PCG `messages` channel remains empty until the PM's next `finish_to_user` emission.

## 10. Autonomous Mode Configuration

**Status:** Specified for approval and terminal-emission behavior. The
`autonomous_mode_config.enabled` input field and optional
`thread_metadata["autonomous_mode"]` field are bridged into
`config={"configurable": {"autonomous_mode": bool}}` on every run. Approval-gate
behavior is specified in `approval-and-gate-contracts.md`; timeout policies and
checkpoint cadence remain future decisions.

## 10. Graph Factory Signature (updated for `repo-and-workspace-layout.md`)

The PCG factory in `graph.py` uses the schemas defined in this spec:

```python
from langgraph.graph import StateGraph, START
from langgraph.pregel import Pregel
from typing_extensions import TypedDict

class AutonomousModeConfig(TypedDict, total=False):
    enabled: bool

class ProjectCoordinationInput(TypedDict, total=False):
    org_id: str
    project_id: str
    project_thread_id: str | None
    pm_session_thread_id: str | None
    initial_stakeholder_input: str
    initial_artifact_paths: list[str] | None
    autonomous_mode_config: AutonomousModeConfig | None

class ProjectCoordinationContext(TypedDict, total=False):
    execution_info: ExecutionInfo
    server_info: ServerInfo | None

class ProjectCoordinationOutput(TypedDict, total=False):
    messages: list[AnyMessage]
    org_id: str
    project_id: str
    project_thread_id: str
    current_phase: str
    current_agent: str | None
    status: Literal["active", "paused", "completed", "failed"]

def make_graph(...) -> CompiledStateGraph:
    builder = StateGraph(
        ProjectCoordinationState,  # from pcg-data-contracts.md
        context_schema=ProjectCoordinationContext,
        input_schema=ProjectCoordinationInput,
        output_schema=ProjectCoordinationOutput,
    )
    # ... add nodes, compile
```

See `docs/specs/repo-and-workspace-layout.md §3` for the full factory contract.

## 11. Conformance Tests (minimum set)

Implementation must pass at least these assertions:

1. **Thread metadata completeness.** Given a thread created by the web app backend or PM session tool, the thread's metadata dict contains keys `thread_kind`, `org_id`, `project_id` (for `project` threads), and optionally `pm_session_thread_id`. Missing required keys is a rejection condition.
2. **First-invocation input isolation.** Given a first PCG invocation with `ProjectCoordinationInput.initial_stakeholder_input="build a chatbot"`, the PCG state `messages` channel is empty after `dispatch_handoff` completes. The stakeholder input appears only in the synthesized `HandoffRecord.brief` and in the PM's child input via `Send`.
3. **Bootstrap handoff record shape.** Given a first PCG invocation, the synthesized `HandoffRecord` has `source_agent="system"`, `target_agent="project_manager"`, `reason="coordinate"`, and non-empty `brief` matching the input.
4. **UI-onboarding null pm_session_thread_id.** Given a project created via the UI-onboarding path, the Project Data Plane `project_registry` entry for that project has `pm_session_thread_id=null`.
5. **Chat-driven pm_session_thread_id linkage.** Given a project created via the chat-driven path, the Project Data Plane `project_registry` entry for that project has `pm_session_thread_id` equal to the originating PM session's thread_id.
6. **Output schema derivation.** Given a completed PCG run, the output dict contains all keys from `ProjectCoordinationOutput` with non-null values where required. Missing required keys is a rejection condition.
7. **Context injection.** Given a PCG node function with `runtime: Runtime[ProjectCoordinationContext]` parameter, `runtime.execution_info.thread_id` equals the LangGraph thread ID and `runtime.execution_info.run_id` equals the LangGraph run ID.
8. **Idempotency with explicit project_thread_id.** Given two `threads.create` calls with the same `project_thread_id` and `if_exists="do_nothing"`, the second call returns the existing thread without error and the thread's metadata is unchanged.
9. **Autonomous config bridge.** Given `ProjectCoordinationInput.autonomous_mode_config={"enabled": True}`, the run submission includes `config={"configurable": {"autonomous_mode": True}}`, and PM's `request_approval` tool observes `runtime.config["configurable"]["autonomous_mode"] is True`.
10. **Org identity bridge.** Given a project run with `ProjectCoordinationInput.org_id`, `dispatch_handoff` writes the same value into PCG state and Project Data Plane operations receive that `org_id`.
