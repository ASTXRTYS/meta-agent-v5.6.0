# PCG Spec Closure Tickets

> **Purpose:** Execution tickets for closing all known underspecified or blocking
> PCG / handoff / project-data-plane spec gaps before implementation begins.
> This is a local planning document, not a shipped product spec. Each ticket
> must land its normative decisions in `AD.md` and the appropriate
> `docs/specs/*.md` files under the governance rules in `AGENTS.md`.
>
> **Operating rule:** Do not leave placeholders, TODOs, provisional mechanisms,
> implementation-determined behavior, or undecided alternatives in normative
> specs. If discovery invalidates a suspected direction below, replace it with
> the verified direction and cite the source that proves it.
>
> **Auggie status:** Do not use Auggie for this pass. Use local `.venv/`,
> `.reference/`, and official LangChain / LangGraph / Deep Agents / LangSmith
> docs when available.

## Storage Location and Governance

These tickets live in `meta_harness/local-docs/` because they are execution
planning for coding agents, not product-facing specs. Normative decisions must
land in `AD.md` first, then flow into the derived specs under `docs/specs/`.

This closure pass creates three new specs:

- `docs/specs/pcg-runtime-contract.md`
- `docs/specs/approval-and-gate-contracts.md`
- `docs/specs/project-data-plane.md`

It also repairs these existing specs:

- `docs/specs/pcg-data-contracts.md`
- `docs/specs/handoff-tools.md`
- `docs/specs/handoff-tool-definitions.md`
- `docs/specs/repo-and-workspace-layout.md`

Execution order:

1. Ticket 1 — PCG Routing and Receiving-Agent Input
2. Ticket 2 — Project Thread Bootstrap, Context, Input, and Output
3. Ticket 3 — Mounted Role Persistence and Namespace Contract
4. Ticket 4 — PCG Wire/Data Contract Repair
5. Ticket 5 — Gate, Approval, and Terminal-Emission Contract
6. Ticket 6 — Project Data Plane Contract

## Ticket 1 — PCG Routing and Receiving-Agent Input *[Resolved]*

### Problem

`docs/specs/pcg-data-contracts.md` says the receiving agent reads the handoff
`brief` and artifact paths, but the dispatcher sketch routes with a plain
`Command(goto=<target_agent>)`. Local SDK inspection indicates that plain string
`goto` schedules the target node from the parent state channels, while `Send`
is the SDK primitive for invoking a node with custom input. The current spec
therefore does not prove that mounted role Deep Agents receive the handoff brief
instead of the parent PCG `messages` channel.

### Scope

Resolve the exact routing mechanism from `dispatch_handoff` into mounted role
Deep Agent subgraphs.

This ticket owns:

- String `goto` vs `Send(target_agent, input)` decision.
- Exact receiving-agent input payload shape.
- Exact conversion from `HandoffRecord` to the child `messages` input.
- Whether the handoff brief is a `HumanMessage`, `SystemMessage`, or structured
  message content.
- How artifact paths and handoff metadata are represented in that input.
- How initial stakeholder input reaches the first PM role turn.
- Static and runtime conformance checks proving the child receives exactly the
  intended handoff packet.

### Required discovery

The assignee must independently verify the routing semantics before changing
specs. Treat the following as starting points, not conclusions:

- `langgraph.types.Command` and `Send` semantics:
  `.venv/lib/python3.11/site-packages/langgraph/types.py`
- Command-to-writes mapping:
  `.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py`
- StateGraph node input mapping:
  `.venv/lib/python3.11/site-packages/langgraph/graph/state.py`
- Pregel PULL and PUSH task preparation:
  `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py`
- Deep Agent input schema:
  `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py`
- Deep Agents graph assembly:
  `.reference/libs/deepagents/deepagents/graph.py`

### Deliverables

- Update `AD.md §4 LangGraph Project Coordination Graph` so the routing
  primitive is unambiguous.
- Update `docs/specs/pcg-data-contracts.md §2` and `§8` with the exact routing
  command and reference implementation.
- Update `docs/specs/repo-and-workspace-layout.md §3` factory sketch if the
  dispatcher return shape changes.
- Add a conformance requirement that exercises at least one handoff into a
  mounted role graph and asserts the child input contains the rendered
  `HandoffRecord` packet, not the raw PCG `messages` list.

### Acceptance criteria

- No normative text says the dispatcher "passes the brief" without showing the
  actual SDK mechanism.
- The selected mechanism is cited to local SDK source or official docs.
- The receiving-agent message format is fully specified with field names,
  message type, allowed metadata, and artifact path rendering rules.
- The spec states how malformed `artifact_paths`, empty `brief`, or missing
  `target_agent` are rejected before routing.
- No implementation author has to decide the child input shape from inference.

## Ticket 2 — Project Thread Bootstrap, Context, Input, and Output

### Problem

`AD.md` names `ProjectCoordinationInput`, `ProjectCoordinationContext`, and
`ProjectCoordinationOutput`, and the repo layout spec uses them in the graph
factory, but no spec defines their fields. The current documents also conflict
around `messages`: PCG `messages` is described as PM-terminal user output, while
initial project bootstrap uses stakeholder input to create the first handoff.

### Scope

Define the project-thread entry and exit contract from the Agent Server boundary
into the PCG and back to clients.

This ticket owns:

- `ProjectCoordinationInput` fields and required/optional status.
- `ProjectCoordinationContext` fields and runtime sources.
- `ProjectCoordinationOutput` fields and client-facing semantics.
- Thread metadata required for project execution.
- Bootstrap behavior for UI-created and PM-session-created project threads.
- Relationship between `project_id`, `project_thread_id`, `thread_id`, and
  `pm_session_thread_id`.
- Autonomous-mode input/config location.
- How initial stakeholder context becomes the initial `HandoffRecord`.
- What lands in PCG `messages` on input, output, and resume.
- Idempotency behavior for repeated project-spawn attempts.

### Required discovery

The assignee must verify Agent Server / LangGraph thread invocation mechanics
before finalizing payload shapes:

- `meta_harness/AD.md §4 PM Session And Project Entry Model`
- `meta_harness/AD.md §4 Identity Linkage and Cardinality`
- `meta_harness/local-docs/SDK_REFERENCE.md`
- LangGraph SDK thread and run APIs:
  `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/threads.py`
  and `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py`
- LangGraph runtime object:
  `.venv/lib/python3.11/site-packages/langgraph/runtime.py`
- LangGraph API callable graph exports:
  `.venv/lib/python3.11/site-packages/langgraph_api/graph.py`

### Deliverables

- Create `docs/specs/pcg-runtime-contract.md`.
- Keep `docs/specs/pcg-data-contracts.md` focused on state channels, reducers,
  `HandoffRecord`, and parent update shapes; point runtime bootstrap readers to
  `pcg-runtime-contract.md`.
- Update `AD.md §9 Derived Specs`.
- Add parent AD pointers for every new spec.
- Define concrete `TypedDict` or Pydantic-style field tables for input, context,
  and output.
- Update any examples in `repo-and-workspace-layout.md` to use the resolved
  factory signature and schema names.

### Acceptance criteria

- The first PCG invocation can be implemented from the docs without inventing
  bootstrap fields.
- The PM-session spawn path and UI-onboarding path converge on the same payload
  shape.
- The docs state exactly where `pm_session_thread_id` is stored and how null is
  represented.
- The docs state exactly how autonomous mode is supplied and read.
- The docs state exactly which values come from client input, thread metadata,
  runtime context, Store/data plane, or system generation.
- There is no conflict between initial stakeholder input and the `messages`
  channel invariant.

## Ticket 3 — Mounted Role Persistence and Namespace Contract

### Problem

The specs assert that each role Deep Agent owns persistent conversation history
in its checkpoint namespace. The docs do not fully specify the role graph
checkpointer mode, parent checkpointer inheritance behavior, namespace shape, or
how repeated invocations of the same role are proven to resume the intended role
state.

### Scope

Define the persistence contract for the seven mounted role Deep Agent subgraphs.

This ticket owns:

- Role graph `checkpointer` argument value.
- Parent PCG checkpointer requirements.
- Whether role subgraphs inherit, opt in with `True`, or receive explicit saver
  instances.
- Checkpoint namespace format for PCG and each role.
- Whether namespace includes task IDs, and which recast namespace is treated as
  stable role identity.
- How repeated handoffs to the same role resume prior role state.
- How `thread_id`, `project_thread_id`, checkpoint namespace, role name, and
  LangSmith metadata correlate.
- How to inspect role state in local development and LangGraph Studio.
- Test requirements for state retention and namespace isolation.

### Required discovery

The assignee must verify the exact semantics against the installed SDK:

- LangGraph `Checkpointer` type:
  `.venv/lib/python3.11/site-packages/langgraph/types.py`
- StateGraph `compile(checkpointer=...)` behavior:
  `.venv/lib/python3.11/site-packages/langgraph/graph/state.py`
- Pregel subgraph checkpoint setup:
  `.venv/lib/python3.11/site-packages/langgraph/pregel/main.py`
- Namespace recasting:
  `.venv/lib/python3.11/site-packages/langgraph/_internal/_config.py`
- Pregel task namespace construction:
  `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py`
- Deep Agents `create_deep_agent(checkpointer=...)` passthrough:
  `.reference/libs/deepagents/deepagents/graph.py`

### Deliverables

- Update `AD.md §4 LangGraph Project Coordination Graph` with the final
  persistence contract.
- Update `docs/specs/repo-and-workspace-layout.md §3` role factory sketch to
  show the exact checkpointer mode.
- Update `docs/specs/pcg-data-contracts.md` invariant #6 with precise namespace
  semantics.
- Add conformance tests for:
  - repeated role invocation preserving role-local messages;
  - different roles not sharing conversation history;
  - PCG state not absorbing role-local messages except through explicit parent
    command updates;
  - trace/checkpoint metadata containing enough information to correlate a role
    turn to `project_thread_id`, role name, and handoff id.

### Acceptance criteria

- The role persistence mechanism is SDK-cited and deterministic.
- A developer knows exactly what `create_deep_agent(..., checkpointer=...)`
  receives for every role.
- A developer knows exactly what the PCG graph `compile(checkpointer=...)`
  receives in local/dev and production entrypoints.
- The stable role namespace is named in the docs and tested.
- The docs do not rely on a vague phrase like "stable checkpoint namespace"
  without defining the namespace source.

## Ticket 4 — PCG Wire/Data Contract Repair

### Problem

Several PCG data-contract details are internally inconsistent or not precise
enough for implementation: role enum spelling, acceptance truth semantics,
`HandoffRecord.status`, `langsmith_run_id`, `handoff_log` cap vs HE
participation, and exact reducer behavior.

### Scope

Repair `pcg-data-contracts.md` so every field, enum, reducer, writer, reader,
and invariant is implementation-ready.

This ticket owns:

- Canonical role enum spelling.
- `AgentName`, `Reason`, `ProjectPhase`, `StampKey`, and status type aliases.
- `HandoffRecord` required vs nullable vs omitted fields.
- Whether `status` exists in the append-only record or moves to explicit status
  transition records.
- Acceptance stamp satisfaction rule: stamp key presence vs `accepted is True`.
- Rejection semantics for `accepted is False`.
- HE participation tracking that remains correct when handoff history grows.
- Handoff-log cap policy and its interaction with gates, audit, registry, and
  conformance tests.
- `langsmith_run_id` source and fallback.
- Timestamp format, timezone, and monotonic/idempotency constraints.
- Reducer definitions for `handoff_log` and `acceptance_stamps`.

### Required discovery

The assignee must independently check each suspected issue against the current
spec set and SDK:

- `docs/specs/pcg-data-contracts.md`
- `docs/specs/handoff-tools.md`
- `docs/specs/handoff-tool-definitions.md`
- `AD.md §4 Data Contracts`
- LangSmith run context:
  `.venv/lib/python3.11/site-packages/langsmith/run_helpers.py`
  and `.venv/lib/python3.11/site-packages/langsmith/__init__.py`
- LangGraph runtime execution info:
  `.venv/lib/python3.11/site-packages/langgraph/runtime.py`
- Message reducer behavior:
  `.venv/lib/python3.11/site-packages/langgraph/graph/message.py`
  and `.venv/lib/python3.11/site-packages/langchain_core/messages/utils.py`

### Deliverables

- Update `docs/specs/pcg-data-contracts.md` field tables and invariants.
- Update `docs/specs/handoff-tool-definitions.md` if any tool fixed fields or
  return shapes change.
- Update `docs/specs/handoff-tools.md` if gate language changes.
- Update `AD.md` where the current decision language is too loose or conflicts
  with the repaired spec.
- Add a compact conformance matrix: channel/field, owner, writer, reader,
  reducer, validation rule, and test expectation.

### Acceptance criteria

- Role names use one canonical spelling across all specs and examples.
- Acceptance gates require `accepted is True`; rejected stamps remain auditable
  and cannot satisfy gates.
- HE participation remains correct regardless of handoff-log size.
- Every field in `HandoffRecord` has a source, validation rule, nullability
  rule, and update rule.
- `langsmith_run_id` has an SDK-cited source and explicit fallback behavior.
- No line in the PCG data contract asks implementation to choose a cap,
  migration path, enum value, status transition, or correlation source.

## Ticket 5 — Gate, Approval, and Terminal-Emission Contract

### Problem

The specs identify gates, approval moments, autonomous mode, `finish_to_user`,
and final-turn guarding, but do not fully specify the tool/middleware contract
for gate failures, approval package presentation, autonomous bypass, or terminal
emission. This leaves prompt authors and middleware implementers to decide
runtime behavior.

### Scope

Define the full gate and approval contract for PM, specialists, and QA roles.

This ticket owns:

- Gate middleware API surface and installation points.
- Gate lookup keys and required state/data-plane reads.
- Gate pass/failure return shapes.
- ToolMessage content requirements for recoverable gate failures.
- Which failures raise exceptions and which return model feedback.
- User approval package tool contract.
- Approval artifact/package shape for scoping-to-research and
  architecture-to-planning transitions.
- Autonomous-mode behavior for every gate and approval checkpoint.
- `finish_to_user` terminal tool schema, writer behavior, and graph termination.
- Final-turn-guard middleware behavior and exact re-prompt update.
- Interaction between `ask_user`, approval tools, and `finish_to_user`.

### Required discovery

The assignee must verify middleware and tool behavior against source:

- LangChain `AgentMiddleware` hooks:
  `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py`
- LangChain agent graph edge behavior for `jump_to`:
  `.venv/lib/python3.11/site-packages/langchain/agents/factory.py`
- LangGraph `ToolNode` command handling:
  `.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py`
- Deep Agents HITL / permissions / middleware references:
  `.reference/libs/deepagents/deepagents/middleware/`
- Existing handoff specs:
  `docs/specs/handoff-tools.md`
  and `docs/specs/handoff-tool-definitions.md`

### Deliverables

- Create `docs/specs/approval-and-gate-contracts.md`.
- Keep `docs/specs/handoff-tool-definitions.md` focused on model-visible tool
  definitions and parent-command return shapes; point gate and approval readers
  to `approval-and-gate-contracts.md`.
- Update AD pointers and `AD.md §9 Derived Specs`.
- Update `AD.md §4 Phase Gate Middleware` and `§4 Handoff Tool Use-Case Matrix`
  so the normative decision language matches the spec.
- Specify every gated tool's gate function inputs, pass condition, failure
  feedback, and state/data-plane reads.
- Specify user approval package schemas and terminal emission schemas.
- Add conformance checks for gate pass, gate failure, autonomous mode,
  user approval, `finish_to_user`, and final-turn guard.

### Acceptance criteria

- Every gated tool has an exact gate contract.
- Gate failure behavior is implementable without inventing ToolMessage wording
  or control flow.
- Autonomous mode has exact behavior for every user approval and final
  satisfaction checkpoint.
- `finish_to_user` cannot accidentally append `handoff_log` or write fields
  outside `messages`.
- Final-turn guard has exact trigger conditions, injected message content, loop
  behavior, and stop condition.
- No prompt author is responsible for silently enforcing a runtime invariant
  that belongs in middleware or a tool contract.

## Ticket 6 — Project Data Plane Contract

### Problem

`pcg-data-contracts.md §7` defines Store namespaces for artifact manifest,
optimization trendline, and project registry, but `AD.md OQ-H5` correctly
identifies unresolved substrate, source-of-truth, write-path, read-path,
multi-tenant, permission, sanitization, retention, and schema-governance
questions. These are product data-plane decisions, not PCG state-channel
details.

### Scope

Replace provisional Store namespace language with a fully specified project
data-plane contract that all surfaces and agents can implement against.

This ticket owns:

- Whether LangGraph Store, product database, or a coordinated combination is
  authoritative for each data type.
- Artifact manifest schema, source of truth, write transaction, recovery, and
  dangling-path handling.
- Project registry schema, source of truth, query shape, idempotency, and
  multi-writer behavior.
- PM-session observability read API.
- Web/TUI/headless ingress read API.
- Tenant/org namespace strategy.
- Permission model for agent reads and writes.
- Developer exclusion from private HE/evaluation data.
- Sanitization enforcement for any visible optimization/evaluation summary.
- Retention, archival, deletion, and schema migration rules.
- How LangSmith traces correlate data-plane reads and writes to user turns,
  project threads, handoffs, and role invocations.

### Required discovery

The assignee must study both the local spec intent and upstream primitives:

- `AD.md OQ-H5`
- `AD.md OQ-PM1`, `OQ-PM2`, and `OQ-PM3`
- `docs/specs/pcg-data-contracts.md §7`
- LangGraph Store base API:
  `.venv/lib/python3.11/site-packages/langgraph/store/base/__init__.py`
- LangGraph memory store behavior:
  `.venv/lib/python3.11/site-packages/langgraph/store/memory/__init__.py`
- Deep Agents StoreBackend namespace patterns:
  `.reference/libs/deepagents/deepagents/backends/store.py`
- Open SWE product data-plane precedent:
  `.reference/apps/open-swe/`
- LangSmith client and dataset/artifact APIs if any data-plane records need
  trace or dataset correlation.

### Deliverables

- Create `docs/specs/project-data-plane.md`.
- Replace `pcg-data-contracts.md §7` with a short pointer to
  `project-data-plane.md` plus only the PCG-owned cross-reference.
- Update `AD.md OQ-H5` from open question to resolved decision text.
- Update `AD.md §9 Derived Specs` and all parent AD pointers.
- Define all data-plane schemas with version fields, indexes, ownership,
  read/write APIs, auth/tenant constraints, and trace metadata.
- Define conformance tests for data-plane write/read permissions, PM-session
  reads, registry updates, artifact manifest writes, deletion/archival, and
  private-data exclusion.

### Acceptance criteria

- `pcg-data-contracts.md` no longer owns product data-plane mechanism.
- Every data-plane read/write has an owning API, source of truth, permission
  check, tenant boundary, and trace correlation rule.
- Developer-private and HE-private boundaries are structurally enforced by tool
  availability, data access layer, backend permissions, or store/database policy
  explicitly named in the spec.
- Artifact references cannot silently dangle; the spec states validation,
  recovery, and deletion behavior.
- PM-session, web/TUI, and headless ingress use one coherent data-plane
  contract rather than separate ad hoc mechanisms.
- Retention and schema migration behavior is fully specified.

## Global Completion Criteria

The closure pass is complete only when all six tickets have landed and the
following checks pass:

- Every doc under `docs/specs/` has current provenance, AD pointer, and
  `AD.md §9` registration.
- Every concept mentioned in `pcg-data-contracts.md` has a single owning spec.
- `pcg-data-contracts.md` contains no provisional Store/data-plane mechanism.
- No normative spec uses unresolved phrases such as "implementation-determined",
  "recommended", "or equivalent", "may choose", or "left to implementation" for
  runtime behavior.
- Every SDK-sensitive claim cites local SDK source or official docs.
- Every runtime invariant has a conformance test or explicit test plan.
- The specs collectively define enough behavior for implementation to begin
  without inventing routing, persistence, bootstrap, gate, approval, data-plane,
  identity, or permission semantics.
