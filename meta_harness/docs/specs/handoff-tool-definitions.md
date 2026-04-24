---
doc_type: spec
derived_from:
  - AD §4 Handoff Protocol
  - AD §4 Handoff Tool Use-Case Matrix
  - AD §4 Command.PARENT Update Contract
  - AD §4 Data Contracts
status: active
last_synced: 2026-04-24
owners: ["@Jason"]
---

# Handoff Tool Definitions Specification

> **Provenance:** Derived from `AD.md §4 Handoff Protocol` (semantic catalog), `§4 Handoff Tool Use-Case Matrix` (23-tool matrix), `§4 Command.PARENT Update Contract` (state update shape), and `§4 Data Contracts` (HandoffRecord wire format).
> **Status:** Active · **Last synced with AD:** 2026-04-24 (created for `T-H1` / `OQ-H6`; updated for `OQ-HO` resolution: `acceptance_stamps` channel, `finish_to_user` terminal-emission tool added, `project_phase` / `plan_phase_id` split clarified; **removed status field from hidden runtime fields per Ticket 4**; **restored dispatcher re-entry `goto` for all normal handoff parent commands per Ticket 5 feedback**; **registered PM `request_approval` model-visible tool per Ticket 5 feedback**).
> **Consumers:** Developer (implementation), code generation tools, Evaluator (conformance checking).

## 1. Purpose

This spec locks the concrete model-visible API for the 23 Meta Harness handoff
tools, PM's terminal `finish_to_user` tool, and PM's structured
`request_approval` tool. It composes the sibling specs:

- `docs/specs/handoff-tools.md` owns the semantic catalog: tool names,
  owners, targets, reasons, gates, artifact flow, and pipeline order.
- `docs/specs/pcg-data-contracts.md` owns PCG state, reducers,
  `HandoffRecord`, and `Command.PARENT` update shape.
- This spec owns concrete tool definitions: descriptions, visible parameters,
  hidden runtime inputs, fixed record fields, record assembly, return shape,
  and role-scoped model-visible tool membership.

Implementation must not infer tool semantics from Python function names,
docstrings, or generated schemas alone. LangChain derives callable schemas from
function signatures or `args_schema`; those signatures must follow this spec.

## 2. SDK Alignment

The implementation uses normal LangChain/LangGraph tool behavior:

- Handoff tools are regular `BaseTool` / `@tool` definitions registered on the
  owning Deep Agent.
- Every handoff tool accepts a hidden `runtime: ToolRuntime` argument. The
  model cannot supply this value; LangGraph injects it during tool execution.
- The 23 handoff tool bodies return
  `Command(graph=Command.PARENT, goto="dispatch_handoff", update=...)`.
  Parent commands do not need a matching `ToolMessage` in the current graph's
  message history.
- PM's `request_approval` tool is model-visible but is not an agent-to-agent
  handoff. It returns `Command(graph=Command.PARENT,
  goto=Send("project_manager", {"messages": [...], "pcg_gate_context": ...}),
  update={"acceptance_stamps": {...}})`.
- Phase gate middleware uses `AgentMiddleware.wrap_tool_call` /
  `awrap_tool_call` around the handoff tools. Gate failure returns a revision
  `ToolMessage` to the calling agent and emits no parent command. Gate pass
  calls the tool handler and allows the `Command.PARENT` to bubble.
- `Command.PARENT` is valid only inside a mounted subgraph. Role Deep Agents
  stay mounted under the PCG; they are never invoked from the dispatcher with
  `.invoke()` / `.ainvoke()`.

Local SDK checks supporting this shape:

- `ToolNode` constructs a `ToolRuntime` for every call and passes the original
  model tool call without runtime injection in the model arguments
  (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:799-812`).
- Injected tool fields are stripped from model-provided args and replaced with
  trusted runtime values before execution
  (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:1388-1397`).
- `ToolNode` validates matching `ToolMessage`s only for current-graph commands;
  parent commands are allowed to bubble without a local message update
  (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:1450-1467`).
- A `Command.PARENT` at top level raises "There is no parent graph", so the
  handoff protocol depends on mounted role subgraphs rather than dispatcher
  `.ainvoke()` calls
  (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:58-59`).

## 3. Visible Schema Families

Model-visible tools use one of five visible schema families.

| Family | Model-visible parameters | Used by |
|---|---|---|
| `CommonHandoffInput` | `brief: str`, `artifact_paths: list[str]` | 17 normal handoff tools |
| `AcceptanceHandoffInput` | `brief: str`, `artifact_paths: list[str]`, `accepted: bool` | 2 acceptance-stamp tools |
| `PhaseReviewHandoffInput` | `brief: str`, `artifact_paths: list[str]`, `phase: str` | 4 Developer phase-review tools |
| `TerminalEmissionInput` | `final_response: str` | PM's terminal `finish_to_user` tool |
| `ApprovalInput` | `package_brief: str`, `artifact_paths: list[str]`, `approval_type: Literal["scoping_to_research", "architecture_to_planning"]` | PM's `request_approval` tool |

Field semantics:

- `brief` is the receiving agent's concise work summary, question, or review
  packet. It is not a transcript dump.
- `artifact_paths` are role-filesystem paths or package paths already created
  by the caller. Empty is valid for non-artifact handoffs; implementations may
  use a safe empty-list default such as Pydantic `default_factory=list`.
- `accepted` is an independent QA stamp. `true` satisfies the relevant final
  acceptance gate; `false` records rejection and does not satisfy the gate.
- `phase` is model-visible for Developer ergonomics, but it is not the PCG
  lifecycle phase. The tool helper stores it as `plan_phase_id` in
  `HandoffRecord`.
- `final_response` is the PM's final user-facing message for the PCG
  `messages` channel.
- `approval_type` is the gate-specific `StampKey` for PM approval checkpoints.
  It cannot be reused across gates.

## 4. Hidden Runtime Contract

The model cannot provide these values:

- `runtime`
- `project_id`
- `project_thread_id`
- `source_agent`
- `target_agent`
- `reason`
- `project_phase`
- `plan_phase_id`
- `handoff_id`
- `langsmith_run_id`
- `created_at`
- `acceptance_stamps`
- `pcg_gate_context`
- `store`
- PCG state

Runtime and state-derived values are system-owned. The implementation must
strip or ignore any caller-supplied value for hidden fields.

## 5. Handoff Record Assembly

Every handoff tool calls a system-owned handoff-record helper before returning
its `Command.PARENT`. The helper assembles a complete `HandoffRecord` from:

- visible model input: `brief`, `artifact_paths`, optional `accepted`, optional
  model-visible `phase`
- fixed tool definition metadata: allowed owner role(s), target role, reason,
  and lifecycle `project_phase` if the tool transitions the PCG lifecycle
- runtime context: `project_id`, `project_thread_id`, current run metadata,
  timestamp, and tool-call context

`dispatch_handoff` does not fill record fields after the reducer appends the
record. It reads `handoff_log[-1]`, upserts the current project registry entry,
and returns `Command(goto=Send(<target_agent>, child_input))`, where
`child_input` always includes `{"messages": [handoff_message]}` and includes
`pcg_gate_context` for gated target roles.

Lifecycle phase split:

- `project_phase` is the PCG lifecycle enum that may update
  `current_phase`: `scoping`, `research`, `architecture`, `planning`,
  `development`, or `acceptance`.
- `plan_phase_id` is a Developer-plan phase identifier. It is populated only by
  tools in the `PhaseReviewHandoffInput` family. The model-visible parameter
  remains named `phase` for tool usability, but no implementation may write
  that value to `current_phase`.

## 6. Return Shapes

All 23 handoff tools return this base shape. `current_phase` is conditional:
include it only when the assembled `handoff_record.project_phase` is not
`None`. That means only lifecycle-transitioning rows update `current_phase`;
phase-review tools store their visible `phase` argument as `plan_phase_id`
inside `handoff_record` and never update `current_phase`.

```python
Command(
    graph=Command.PARENT,
    goto="dispatch_handoff",
    update={
        "handoff_log": [handoff_record],
        "current_agent": target_agent,
        # Include only when handoff_record.project_phase is not None:
        "current_phase": handoff_record.project_phase,
        # Acceptance tools additionally include:
        # "acceptance_stamps": {"application": handoff_record}
        #   or
        # "acceptance_stamps": {"harness": handoff_record}
    },
)
```

The update dict never includes `messages` and never includes
`pending_handoff`.

PM's terminal emission tool returns:

```python
Command(
    graph=Command.PARENT,
    goto=END,
    update={"messages": [AIMessage(final_response)]},
)
```

`finish_to_user` never writes `handoff_log` and never writes
`acceptance_stamps`.

PM's approval tool returns:

```python
Command(
    graph=Command.PARENT,
    goto=Send(
        "project_manager",
        {
            "messages": [approval_result_message],
            "pcg_gate_context": refreshed_gate_context,
        },
    ),
    update={"acceptance_stamps": {approval_type: approval_record}},
)
```

`request_approval` never writes `handoff_log` and never routes through
`dispatch_handoff`; it is PM self-reentry after a stamp update.

## 7. Concrete Tool Definitions

Descriptions below are model-visible. They should be used as the source text
for the tool descriptions unless implementation discovers a provider-specific
schema limitation that requires a purely mechanical rephrase.

| # | Tool | Owner(s) | Description | Schema | Fixed fields | Gate | Side effects |
|---|---|---|---|---|---|---|---|
| 1 | `deliver_prd_to_harness_engineer` | `project_manager` | Deliver the finalized PRD and proposed evaluation criteria to the Harness Engineer to design the evaluation suite. Use when scoping is ready for evaluation-design work. | Common | `source_agent=project_manager`; `target_agent=harness_engineer`; `reason=deliver`; `project_phase=scoping` | PRD finalized; PRD artifact present | Logical artifact-manifest writes for referenced artifacts; substrate provisional under OQ-H5 |
| 2 | `deliver_prd_to_researcher` | `project_manager` | Deliver the PRD, public evaluation criteria, and public datasets to the Researcher for targeted research. Use after Stage 1 evaluation design is complete and the scoping package is approved. | Common | `source_agent=project_manager`; `target_agent=researcher`; `reason=deliver`; `project_phase=research` | HE Stage 1 complete; stakeholder scoping approval required | Logical artifact-manifest writes for referenced artifacts; substrate provisional under OQ-H5 |
| 3 | `deliver_design_package_to_architect` | `project_manager` | Deliver the research-ready design package to the Architect. Use when research is complete and the Architect should produce the design specification. | Common | `source_agent=project_manager`; `target_agent=architect`; `reason=deliver`; `project_phase=architecture` | Research complete | Logical artifact-manifest writes for referenced artifacts; substrate provisional under OQ-H5 |
| 4 | `deliver_planning_package_to_planner` | `project_manager` | Deliver the approved design package to the Planner. Use when the design spec and evaluation coverage are ready to become an implementation plan. | Common | `source_agent=project_manager`; `target_agent=planner`; `reason=deliver`; `project_phase=planning` | HE Stage 2 complete; stakeholder architecture approval required | Logical artifact-manifest writes for PM-assembled package; substrate provisional under OQ-H5 |
| 5 | `deliver_development_package_to_developer` | `project_manager` | Deliver the accepted implementation package to the Developer. Use when planning is complete and development should begin. | Common | `source_agent=project_manager`; `target_agent=developer`; `reason=deliver`; `project_phase=development` | Plan accepted | Logical artifact-manifest writes for PM-assembled package; substrate provisional under OQ-H5 |
| 6 | `return_eval_suite_to_pm` | `harness_engineer` | Return the evaluation suite summary to the Project Manager. Include public criteria, rubrics, public datasets, and what remains private to HE. | Common | `source_agent=harness_engineer`; `target_agent=project_manager`; `reason=return`; `project_phase=None` | None | Logical artifact-manifest writes for public eval artifacts; held-out/private artifacts remain HE-scoped |
| 7 | `return_research_bundle_to_pm` | `researcher` | Return the completed research bundle to the Project Manager with findings, references, and artifact paths. | Common | `source_agent=researcher`; `target_agent=project_manager`; `reason=return`; `project_phase=None` | None | Logical artifact-manifest writes for research artifacts |
| 8 | `return_design_package_to_pm` | `architect` | Return the completed design package to the Project Manager with design spec, tool schemas, prompt contracts, and open risks. | Common | `source_agent=architect`; `target_agent=project_manager`; `reason=return`; `project_phase=None` | None | Logical artifact-manifest writes for design artifacts |
| 9 | `return_plan_to_pm` | `planner` | Return the implementation plan to the Project Manager with phase sequence, evaluation breakpoints, and acceptance criteria. | Common | `source_agent=planner`; `target_agent=project_manager`; `reason=return`; `project_phase=None` | None | Logical artifact-manifest writes for plan artifacts |
| 10 | `return_product_to_pm` | `developer` | Return the finished product to the Project Manager for final user presentation. Use only after required acceptance stamps exist. | Common | `source_agent=developer`; `target_agent=project_manager`; `reason=return`; `project_phase=acceptance` | Application acceptance required; harness acceptance required if HE participated | Logical artifact-manifest writes for final product artifacts |
| 11 | `submit_harness_acceptance` | `harness_engineer` | Submit the Harness Engineer acceptance stamp for target-harness quality. Set accepted true only when harness/eval-science quality is verified. | Acceptance | `source_agent=harness_engineer`; `target_agent=project_manager`; `reason=submit`; `project_phase=None`; stamp key `harness` | None; stamp only | Writes `acceptance_stamps["harness"]`; logical artifact-manifest writes for evidence artifacts |
| 12 | `submit_application_acceptance` | `evaluator` | Submit the Evaluator acceptance stamp for target-application quality. Set accepted true only when implementation quality is verified. | Acceptance | `source_agent=evaluator`; `target_agent=project_manager`; `reason=submit`; `project_phase=None`; stamp key `application` | None; stamp only | Writes `acceptance_stamps["application"]`; logical artifact-manifest writes for evidence artifacts |
| 13 | `submit_spec_to_harness_engineer` | `architect` | Submit the design spec to the Harness Engineer for evalability and development-phase evaluation coverage review. | Common | `source_agent=architect`; `target_agent=harness_engineer`; `reason=submit`; `project_phase=None` | Spec accepted enough for HE review; spec artifact present | Logical artifact-manifest writes for submitted spec artifacts |
| 14 | `return_eval_coverage_to_architect` | `harness_engineer` | Return eval coverage feedback to the Architect after Stage 2 review, including new criteria and required design changes. | Common | `source_agent=harness_engineer`; `target_agent=architect`; `reason=return`; `project_phase=None` | None | Logical artifact-manifest writes for coverage artifacts |
| 15 | `announce_phase_to_evaluator` | `developer` | Announce the Developer plan phase to the Evaluator before implementation submission. Use to align on expected application-quality checks. | PhaseReview | `source_agent=developer`; `target_agent=evaluator`; `reason=announce`; `project_phase=None`; visible `phase` becomes `plan_phase_id` | None | No required Store side effect; logical artifact writes only if paths are supplied |
| 16 | `announce_phase_to_harness_engineer` | `developer` | Announce the Developer plan phase to the Harness Engineer before target-harness or eval-science review. | PhaseReview | `source_agent=developer`; `target_agent=harness_engineer`; `reason=announce`; `project_phase=None`; visible `phase` becomes `plan_phase_id` | None | No required Store side effect; logical artifact writes only if paths are supplied |
| 17 | `submit_phase_to_evaluator` | `developer` | Submit completed plan-phase deliverables to the Evaluator for pass/fail review against the accepted plan and design. | PhaseReview | `source_agent=developer`; `target_agent=evaluator`; `reason=submit`; `project_phase=None`; visible `phase` becomes `plan_phase_id` | Matching Evaluator announcement for `plan_phase_id`; deliverables reference plan | Logical artifact-manifest writes for deliverables and test evidence |
| 18 | `submit_phase_to_harness_engineer` | `developer` | Submit completed plan-phase deliverables to the Harness Engineer for target-harness and evaluation-science feedback. | PhaseReview | `source_agent=developer`; `target_agent=harness_engineer`; `reason=submit`; `project_phase=None`; visible `phase` becomes `plan_phase_id` | None | Logical artifact-manifest writes for deliverables; HE review workflow may emit sanitized trendline data, substrate provisional under OQ-H5 |
| 19 | `consult_harness_engineer_on_gates` | `planner` | Ask the Harness Engineer for evaluation gate placement recommendations while planning. Use for expert input without transferring ownership. | Common | `source_agent=planner`; `target_agent=harness_engineer`; `reason=consult`; `project_phase=None` | None | No required Store side effect |
| 20 | `consult_evaluator_on_gates` | `planner` | Ask the Evaluator for acceptance gate placement recommendations while planning. Use for application-quality review input without transferring ownership. | Common | `source_agent=planner`; `target_agent=evaluator`; `reason=consult`; `project_phase=None` | None | No required Store side effect |
| 21 | `request_research_from_researcher` | `project_manager`, `harness_engineer`, `architect` | Request targeted research from the Researcher. Use for a bounded question and include enough context in brief for a fresh research pass. | Common | `source_agent=<owning runtime role>`; `target_agent=researcher`; `reason=consult`; `project_phase=None` | None | Logical artifact-manifest writes for supplied context artifacts |
| 22 | `ask_pm` | any specialist except `project_manager` | Ask the Project Manager for stakeholder clarification, scope authority, or business-priority guidance. Use only when the question needs PM authority. | Common | `source_agent=<owning runtime role>`; `target_agent=project_manager`; `reason=question`; `project_phase=None` | None | No required Store side effect |
| 23 | `coordinate_qa` | `harness_engineer`, `evaluator` | Coordinate QA strategy between Harness Engineer and Evaluator. Use to align findings without changing ownership of work. | Common | `source_agent=<harness_engineer or evaluator>`; `target_agent=<the other QA role>`; `reason=coordinate`; `project_phase=None` | None | No required Store side effect |
| 24 | `finish_to_user` | `project_manager` | Send the final user-facing response and terminate the PCG turn. Use only when PM is ready to close the current user-facing lifecycle. | Terminal | no `HandoffRecord`; no source/target/reason | None | Writes only PCG `messages`; terminal lifecycle event, not a handoff |
| 25 | `request_approval` | `project_manager` | Present a scoped document package for stakeholder approval of the scoping-to-research or architecture-to-planning gate. Use after PM has assembled the package and before retrying the gated handoff. | Approval | `source_agent=project_manager`; `target_agent=project_manager`; `reason=submit`; `project_phase=None`; stamp key is visible `approval_type` | None; approval checkpoint only | Writes `acceptance_stamps[approval_type]`; re-enters PM with approval-result message and refreshed `pcg_gate_context`; does not append `handoff_log` |

### 7.1 Exact Return Shapes

Every model-visible tool above returns one of these concrete parent commands.
Rows 1-23 use a `HandoffRecord` helper; row 24 emits no record; row 25 creates
an approval stamp record only for `acceptance_stamps`.

| Row | Parent command |
|---|---|
| 1 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "harness_engineer", "current_phase": "scoping"})` |
| 2 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "researcher", "current_phase": "research"})` |
| 3 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "architect", "current_phase": "architecture"})` |
| 4 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "planner", "current_phase": "planning"})` |
| 5 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "developer", "current_phase": "development"})` |
| 6 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager"})` |
| 7 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager"})` |
| 8 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager"})` |
| 9 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager"})` |
| 10 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager", "current_phase": "acceptance"})` |
| 11 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager", "acceptance_stamps": {"harness": record}})` |
| 12 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager", "acceptance_stamps": {"application": record}})` |
| 13 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "harness_engineer"})` |
| 14 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "architect"})` |
| 15 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "evaluator"})` |
| 16 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "harness_engineer"})` |
| 17 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "evaluator"})` |
| 18 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "harness_engineer"})` |
| 19 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "harness_engineer"})` |
| 20 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "evaluator"})` |
| 21 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "researcher"})` |
| 22 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": "project_manager"})` |
| 23 | `Command(graph=Command.PARENT, goto="dispatch_handoff", update={"handoff_log": [record], "current_agent": record.target_agent})` |
| 24 | `Command(graph=Command.PARENT, goto=END, update={"messages": [AIMessage(final_response)]})` |
| 25 | `Command(graph=Command.PARENT, goto=Send("project_manager", {"messages": [approval_result_message], "pcg_gate_context": refreshed_gate_context}), update={"acceptance_stamps": {approval_type: record}})` |

### 7.2 Role Toolsets

Role factories register exactly these tool names:

| Role | Rows from §7 |
|---|---|
| `project_manager` | 1, 2, 3, 4, 5, 21, 24, 25 |
| `harness_engineer` | 6, 11, 14, 21, 22, 23 |
| `researcher` | 7, 22 |
| `architect` | 8, 13, 21, 22 |
| `planner` | 9, 19, 20, 22 |
| `developer` | 10, 15, 16, 17, 18, 22 |
| `evaluator` | 12, 22, 23 |

## 8. Gate Middleware Contract

> Implementation detail (full gate and approval contract): see [`docs/specs/approval-and-gate-contracts.md`](./approval-and-gate-contracts.md).

Gate middleware is installed only on roles that own gated tools. It inspects
the fixed fields and model-visible arguments before the tool body emits a
parent command. PCG-derived reads come from the dispatcher-projected
`pcg_gate_context` child input, not direct parent `ProjectCoordinationState`.

Required behavior:

- Gate pass: call the handler and return its `Command.PARENT`.
- Gate failure: return a `ToolMessage` addressed to the current tool call with
  concise revision instructions. Do not return a `Command`.
- Gate errors that are implementation defects may raise; recoverable product
  gate failures should be returned to the model as tool feedback.
- Row 10 reads `acceptance_stamps`. It must not scan `handoff_log` for
  acceptance records. HE participation may still be derived from `handoff_log`.
- `accepted=false` writes the stamp record but never satisfies final gates.
- `phase` in phase-review tools is compared as `plan_phase_id`, not as
  `current_phase`.
- PM's `request_approval` is not gated, but it must refresh
  `pcg_gate_context` in its self-reentry `Send` payload after writing the
  approval stamp.

For exact gate function inputs, pass conditions, failure feedback, autonomous
mode behavior, user approval tool contract, terminal emission, and final-turn
guard specifications, see the approval-and-gate-contracts.md spec.

## 9. Implementation Conformance

Minimum checks for the later implementation:

1. Generated tool schemas expose only the parameters for the expected schema
   family.
2. `runtime`, state, Store, project identity, role names, reasons,
   timestamps, and run IDs are not model-visible.
3. LLM-supplied injected fields are stripped or ignored.
4. Every handoff tool returns
   `Command(graph=Command.PARENT, goto="dispatch_handoff", update=...)`.
5. `finish_to_user` returns `Command(graph=Command.PARENT, goto=END,
   update={"messages": [...]})` and does not append to `handoff_log`.
6. No handoff update writes `messages` or `pending_handoff`.
7. `current_phase` is updated only from `HandoffRecord.project_phase`.
8. The model-visible phase-review argument `phase` is stored as
   `plan_phase_id`.
9. Gate failure returns a `ToolMessage` and produces no parent-state update.
10. Role factories register only the tools listed for their role in §7.2,
    including PM's `request_approval`.
