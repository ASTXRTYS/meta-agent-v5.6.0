---
doc_type: spec
derived_from:
  - AD §4 Phase Gate Middleware
  - AD §4 Handoff Protocol
  - AD §4 Handoff Tool Use-Case Matrix
  - AD §4 Command.PARENT Update Contract
status: draft
last_synced: 2026-04-24
owners: ["@Jason"]
---

# Approval and Gate Contracts Specification

> **Provenance:** Derived from `AD.md §4 Phase Gate Middleware` (middleware hooks on handoff tools), `§4 Handoff Protocol` (two user-approval transitions), `§4 Handoff Tool Use-Case Matrix` (gated tool table), and `§4 Command.PARENT Update Contract` (state update shapes).
> **Status:** Draft · **Last synced with AD:** 2026-04-24 (revised per EBDR-1 feedback: fixed final-turn guard jump_to routing; added StampKey type coherence; unified approval/rejection return pattern via Command.PARENT with feedback field; removed invalid ApprovalPersistenceMiddleware; restored dispatcher `goto` for handoff tools; added explicit `pcg_gate_context` bridge for role middleware; synchronized gate matrix and `request_approval` tool registration across specs; clarified PM-session composition per Ticket 7).
> **Consumers:** Developer (gate middleware implementation), Evaluator (conformance checking).

## 1. Purpose

This spec defines the full runtime contract for gate middleware, user approval tools, autonomous mode behavior, and terminal emission in Meta Harness. It specifies:

- Gate middleware API surface and installation points
- Exact gate function inputs, pass conditions, failure feedback, and state/Project Records Layer reads for every gated tool
- ToolMessage content requirements for recoverable gate failures
- Which failures raise exceptions and which return model feedback
- User approval package tool contract and artifact/package schemas
- Autonomous-mode behavior for every gate and approval checkpoint
- `finish_to_user` terminal tool schema, writer behavior, and graph termination
- Final-turn-guard middleware behavior and exact re-prompt update
- Interaction between `ask_user`, approval tools, and `finish_to_user`

The sibling spec `docs/specs/handoff-tool-definitions.md` owns model-visible tool definitions and parent-command return shapes. This spec owns the middleware and runtime enforcement contract.

## 2. SDK Alignment

Gate middleware uses LangChain's `AgentMiddleware.awrap_tool_call` hook:

```python
async def awrap_tool_call(
    self,
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
) -> ToolMessage | Command[Any]:
```

SDK behavior verified against source:

- `AgentMiddleware.awrap_tool_call` signature: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:731-798`
- Handler can be called multiple times for retry logic or skipped entirely for short-circuit
- Returning `ToolMessage` to the model provides revision feedback; returning `Command` allows parent command to bubble
- `ToolNode` validates parent commands and allows `Command(graph=PARENT)` to bubble without matching `ToolMessage`: `.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:1450-1467`
- `HumanInTheLoopMiddleware` uses `after_model` hook with `langgraph.types.interrupt()`: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/human_in_the_loop.py:288-300`
- Mounted subgraph input is selected from the child graph's declared input
  schema, not the parent state: `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1308-1314`
- `ToolNode` passes child `tool_runtime.state` into `ToolCallRequest`; mounted
  role middleware therefore sees child role state, not raw
  `ProjectCoordinationState`: `.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:1019-1025`
- LangChain merges middleware state schemas into the agent input schema unless
  fields are annotated `OmitFromInput`; this spec uses an input-accepted,
  output-omitted `pcg_gate_context` field for gated roles:
  `.venv/lib/python3.11/site-packages/langchain/agents/factory.py:402-444`
- Deep Agents CLI implements `ask_user` as its own `AskUserMiddleware` that
  exposes an `ask_user` tool and calls `interrupt()` inside that tool, not as
  LangChain `HumanInTheLoopMiddleware`:
  `.reference/libs/cli/deepagents_cli/ask_user.py:205-255`
- `create_deep_agent()` appends caller-provided middleware before provider
  middleware, memory, optional `HumanInTheLoopMiddleware`, and permission
  middleware, so Ticket 5 middleware ordering is specified within the
  role-supplied custom middleware list:
  `.reference/libs/deepagents/deepagents/graph.py:570-586`

Gate middleware does NOT use `HumanInTheLoopMiddleware` for phase gates. Phase gates are pre-execution checks via `awrap_tool_call`, not post-model interrupts.

## 2.5 Type Definitions (Cross-Spec Coherence)

The following types are defined in `docs/specs/pcg-data-contracts.md` and used consistently across specs:

```python
from typing import Literal
from typing_extensions import TypedDict

# Canonical stamp keys for acceptance_stamps channel
StampKey = Literal["application", "harness", "scoping_to_research", "architecture_to_planning"]

class PCGGateContext(TypedDict, total=False):
    project_id: str
    project_thread_id: str
    current_phase: ProjectPhase
    current_agent: AgentName
    handoff_log: list[HandoffRecord]
    acceptance_stamps: dict[StampKey, HandoffRecord]
```

**Stamp key semantics:**
- `"application"`: Evaluator acceptance stamp (set by `submit_application_acceptance`)
- `"harness"`: Harness Engineer acceptance stamp (set by `submit_harness_acceptance`)
- `"scoping_to_research"`: PM approval for scoping→research transition (set by `request_approval`)
- `"architecture_to_planning"`: PM approval for architecture→planning transition (set by `request_approval`)

Gate functions MUST use `StampKey` for `acceptance_stamps` lookups, not raw strings.

## 3. Gate Middleware Installation

Gate middleware is installed in the agent's middleware stack during factory assembly. Installation points:

| Agent | Gate middleware class | Installed in stack position |
|---|---|---|
| PM | `PMPhaseGateMiddleware` | After role-specific `AskUserMiddleware`, before `FinalTurnGuardMiddleware` |
| Architect | `ArchitectPhaseGateMiddleware` | After role-specific `AskUserMiddleware`, before `FinalTurnGuardMiddleware` |
| Developer | `DeveloperPhaseGateMiddleware` | After universal middleware (no HITL middleware on Developer) |

Universal middleware (CollapseMiddleware, ContextEditingMiddleware, SummarizationToolMiddleware, ModelCallLimitMiddleware, StagnationGuardMiddleware) runs before gate middleware on all agents.

Gate middleware uses `awrap_tool_call` only. It does not implement `wrap_model_call`, `before_model`, `after_model`, or other hooks.

Each gate middleware class declares a state schema that accepts the dispatcher
projection used by gated roles:

```python
from typing import Annotated
from typing_extensions import NotRequired

class PhaseGateState(AgentState):
    pcg_gate_context: NotRequired[Annotated[PCGGateContext, OmitFromOutput]]
```

`pcg_gate_context` is not model-visible and is not returned to the PCG on
natural role completion. It exists only so `awrap_tool_call` can evaluate
PCG-derived prerequisites inside the mounted role subgraph.

## 4. Gate Function Contract

Every gate function has this signature:

```python
async def check_gate(
    tool_name: str,
    tool_args: dict[str, Any],
    gate_context: PCGGateContext,
    runtime: ToolRuntime,
) -> tuple[bool, str | None]:
    """
    Check if a handoff tool call satisfies its gate condition.

    Args:
        tool_name: The handoff tool being called (e.g., "deliver_prd_to_harness_engineer")
        tool_args: Model-visible arguments (brief, artifact_paths, accepted, phase)
        gate_context: Dispatcher-created projection of PCG state
            (handoff_log, acceptance_stamps, current_phase, etc.)
        runtime: LangGraph runtime context (config, store, tool_call_id)

    Returns:
        (pass, feedback):
        - pass: True if gate satisfied, False if gate failed
        - feedback: None if pass, otherwise revision instruction string for the model
    """
```

Gate functions MUST NOT read `ProjectCoordinationState` directly. They run
inside mounted role Deep Agents, and `ToolCallRequest.state` is the child role
state. Gate middleware extracts `request.state["pcg_gate_context"]` and passes
that projection into gate functions. Missing `pcg_gate_context` on a gated tool
call is an implementation defect and must raise.

Gate functions never raise exceptions for recoverable failures. They return `(False, feedback)` to allow the model to revise. Only implementation defects (corrupted state, missing required fields) raise exceptions.

## 5. Gated Tool Specifications

### 5.1 PM Gates

#### 5.1.1 `deliver_prd_to_harness_engineer` (Row 1)

**Gate type:** Prerequisite-only

**Gate function:** `check_prd_finalized_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- `tool_args.artifact_paths` is non-empty
- At least one path in `artifact_paths` has a `.md` or `.txt` extension (PRD artifact)

**State/Project Records Layer reads:**
- None (only tool_args validation)

**Failure feedback:**
```
Cannot deliver to Harness Engineer: PRD artifact not found in artifact_paths.
Create the PRD document in your filesystem and include its path in artifact_paths.
Expected: artifact_paths non-empty with at least one .md or .txt file.
```

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint, only prerequisite check).

---

#### 5.1.2 `deliver_prd_to_researcher` (Row 2)

**Gate type:** Prerequisite + User Approval

**Gate function:** `check_scoping_to_research_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.acceptance_stamps`: dict[str, HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- Prerequisite: `(source_agent="harness_engineer", target_agent="project_manager", reason="return")` exists in `gate_context.handoff_log`
- User approval: `gate_context.acceptance_stamps["scoping_to_research"]` exists AND `gate_context.acceptance_stamps["scoping_to_research"]["accepted"] is True`

**State/Project Records Layer reads:**
- `gate_context.handoff_log`: scan for HE return record
- `gate_context.acceptance_stamps["scoping_to_research"]`: read gate-specific PM approval stamp

**Failure feedback (prerequisite):**
```
Cannot deliver to Researcher: Harness Engineer Stage 1 not complete.
HE must return eval suite to PM first via return_eval_suite_to_pm.
Current handoff_log does not contain (source="harness_engineer", target="project_manager", reason="return").
```

**Failure feedback (approval):**
```
Cannot deliver to Researcher: PRD package requires stakeholder approval.
Use the request_approval tool to present the PRD and HE eval suite for review.
Once approved, the system will create an approval stamp and you may retry this handoff.
```

**Failure feedback (approval rejected):**
```
Cannot deliver to Researcher: PRD package approval was rejected.
The scoping_to_research approval stamp exists but has accepted=False.
Review the approval feedback, revise the package, and request approval again.
```

**Autonomous mode behavior:** Auto-approve by creating `scoping_to_research` stamp with `accepted=True` immediately. PM calls `request_approval` tool which in autonomous mode bypasses human interrupt, writes the stamp, and re-enters PM with an approval-result message.

---

#### 5.1.3 `deliver_design_package_to_architect` (Row 3)

**Gate type:** Prerequisite-only

**Gate function:** `check_research_complete_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- `(source_agent="researcher", target_agent="project_manager", reason="return")` exists in `gate_context.handoff_log`

**State/Project Records Layer reads:**
- `gate_context.handoff_log`: scan for Researcher return record

**Failure feedback:**
```
Cannot deliver to Architect: Research not complete.
Researcher must return research bundle to PM first via return_research_bundle_to_pm.
Current handoff_log does not contain (source="researcher", target="project_manager", reason="return").
```

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint).

---

#### 5.1.4 `deliver_planning_package_to_planner` (Row 4)

**Gate type:** Prerequisite + User Approval

**Gate function:** `check_architecture_to_planning_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.acceptance_stamps`: dict[str, HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- Prerequisite A: `(source_agent="harness_engineer", target_agent="architect", reason="return")` exists in `gate_context.handoff_log` (HE Stage 2 evaluation coverage returned)
- Prerequisite B: `(source_agent="architect", target_agent="project_manager", reason="return")` exists in `gate_context.handoff_log` (Architect returned final design package)
- User approval: `gate_context.acceptance_stamps["architecture_to_planning"]` exists AND `gate_context.acceptance_stamps["architecture_to_planning"]["accepted"] is True`

**State/Project Records Layer reads:**
- `gate_context.handoff_log`: scan for HE Stage 2 return record and Architect return record
- `gate_context.acceptance_stamps["architecture_to_planning"]`: read gate-specific PM approval stamp

**Failure feedback (HE Stage 2 missing):**
```
Cannot deliver to Planner: Harness Engineer Stage 2 not complete.
HE must return eval coverage to Architect first via return_eval_coverage_to_architect.
Current handoff_log does not contain (source="harness_engineer", target="architect", reason="return").
```

**Failure feedback (Architect return missing):**
```
Cannot deliver to Planner: Design spec not complete.
Architect must return design package to PM first via return_design_package_to_pm.
Current handoff_log does not contain (source="architect", target="project_manager", reason="return").
```

**Failure feedback (approval):**
```
Cannot deliver to Planner: Design package requires stakeholder approval.
Use the request_approval tool to present the design spec, tool schemas, and system prompts for review.
Once approved, the system will create an approval stamp and you may retry this handoff.
```

**Failure feedback (approval rejected):**
```
Cannot deliver to Planner: Design package approval was rejected.
The architecture_to_planning approval stamp exists but has accepted=False.
Review the approval feedback, revise the package, and request approval again.
```

**Autonomous mode behavior:** Auto-approve by creating `architecture_to_planning` stamp with `accepted=True` immediately. PM calls `request_approval` tool which in autonomous mode bypasses human interrupt, writes the stamp, and re-enters PM with an approval-result message.

---

#### 5.1.5 `deliver_development_package_to_developer` (Row 5)

**Gate type:** Prerequisite-only

**Gate function:** `check_plan_accepted_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- `(source_agent="planner", target_agent="project_manager", reason="return")` exists in `gate_context.handoff_log`

**State/Project Records Layer reads:**
- `gate_context.handoff_log`: scan for Planner return record

**Failure feedback:**
```
Cannot deliver to Developer: Implementation plan not complete.
Planner must return implementation plan to PM first via return_plan_to_pm.
Current handoff_log does not contain (source="planner", target="project_manager", reason="return").
```

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint).

---

### 5.2 Architect Gates

#### 5.2.1 `submit_spec_to_harness_engineer` (Row 13)

**Gate type:** Prerequisite-only

**Gate function:** `check_spec_accepted_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- `tool_args.artifact_paths` is non-empty
- At least one path has a `.md` or `.txt` extension (design spec artifact)

**State/Project Records Layer reads:**
- None (only tool_args validation)

**Failure feedback:**
```
Cannot submit to Harness Engineer: Design spec artifact not found in artifact_paths.
Create the design spec document and include its path in artifact_paths.
Expected: artifact_paths non-empty with at least one .md or .txt file.
```

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint).

---

### 5.3 Developer Gates

#### 5.3.1 `return_product_to_pm` (Row 10)

**Gate type:** Acceptance-stamp verification

**Gate function:** `check_acceptance_stamps_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.acceptance_stamps`: dict[str, HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- `gate_context.acceptance_stamps["application"]` exists AND `gate_context.acceptance_stamps["application"]["accepted"] is True` (Evaluator stamp, always required)
- HE participation check: scan `gate_context.handoff_log` for any record with `source_agent="harness_engineer"` or `target_agent="harness_engineer"`
  - If HE participated: `gate_context.acceptance_stamps["harness"]` must exist AND `gate_context.acceptance_stamps["harness"]["accepted"] is True`
  - If HE did not participate: skip HE stamp check

**State/Project Records Layer reads:**
- `gate_context.acceptance_stamps["application"]`: read Evaluator stamp
- `gate_context.acceptance_stamps["harness"]`: read HE stamp (conditional)
- `gate_context.handoff_log`: scan for HE participation (conditional, used only for determining if HE stamp is required)

**Failure feedback (missing application stamp):**
```
Cannot return product to PM: Evaluator acceptance stamp not found.
Evaluator must submit application acceptance stamp via submit_application_acceptance.
The stamp must have accepted=True to satisfy the gate.
```

**Failure feedback (application rejected):**
```
Cannot return product to PM: Evaluator rejected the application.
The application acceptance stamp exists but has accepted=False.
Review Evaluator feedback, fix issues, and request re-evaluation.
```

**Failure feedback (missing harness stamp when required):**
```
Cannot return product to PM: Harness Engineer acceptance stamp not found.
HE participated in this project (found in handoff_log).
HE must submit harness acceptance stamp via submit_harness_acceptance.
The stamp must have accepted=True to satisfy the gate.
```

**Failure feedback (harness rejected):**
```
Cannot return product to PM: Harness Engineer rejected the target harness.
The harness acceptance stamp exists but has accepted=False.
Review HE feedback, fix eval science issues, and request re-evaluation.
```

**Autonomous mode behavior:** Same as interactive mode (acceptance gates are never auto-approved; QA stamps are structural requirements).

---

#### 5.3.2 `submit_phase_to_evaluator` (Row 17)

**Gate type:** Prerequisite-only (announcement matching)

**Gate function:** `check_phase_announcement_gate`

**Inputs:**
- `tool_args.brief`: str
- `tool_args.artifact_paths`: list[str]
- `tool_args.phase`: str (model-visible, stored as `plan_phase_id` in HandoffRecord)
- `gate_context.handoff_log`: list[HandoffRecord]
- `gate_context.current_phase`: str | None

**Pass condition:**
- A matching announcement exists: `(source_agent="developer", target_agent="evaluator", reason="announce", plan_phase_id=<tool_args.phase>)` in `gate_context.handoff_log`
- `tool_args.artifact_paths` is non-empty (phase deliverables must exist)

**State/Project Records Layer reads:**
- `gate_context.handoff_log`: scan for matching announcement record with matching `plan_phase_id`

**Failure feedback (no announcement):**
```
Cannot submit phase to Evaluator: No matching announcement for phase '{phase}'.
You must first announce phase intent via announce_phase_to_evaluator.
The announcement must have the same phase identifier.
```

**Failure feedback (no deliverables):**
```
Cannot submit phase to Evaluator: No phase deliverables in artifact_paths.
Include the phase implementation files, tests, and evidence in artifact_paths.
```

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint).

---

#### 5.3.3 `submit_phase_to_harness_engineer` (Row 18)

**Gate type:** None

Row 18 is intentionally ungated. The Harness Engineer review path may be used
for target-harness and evaluation-science feedback even when there was no prior
announcement. The Developer system prompt owns routing discipline; middleware
must not block this tool on announcement matching.

**Autonomous mode behavior:** Same as interactive mode (no approval checkpoint).

---

## 6. User Approval Tool Contract

Meta Harness uses a custom approval tool pattern, not `HumanInTheLoopMiddleware`. The PM owns an approval tool that creates self-referential stamp records in `acceptance_stamps` and re-enters the mounted PM role with an explicit approval-result message.

### 6.1 Approval Tool Schema

**Tool name:** `request_approval` (PM-only)

Canonical model-visible registration lives in
`docs/specs/handoff-tool-definitions.md` row 25 and PM's role toolset. Although
this is not an agent-to-agent handoff, it is a model-visible PM tool and must be
registered by the same role factory that registers PM handoff tools.

**Model-visible parameters:**
```python
class ApprovalInput(TypedDict):
    package_brief: str  # Summary of what requires approval
    artifact_paths: list[str]  # Paths to artifacts for review
    approval_type: Literal["scoping_to_research", "architecture_to_planning"]
```

**Fixed fields (hidden from model):**
- `source_agent = "project_manager"`
- `target_agent = "project_manager"`
- `reason = "submit"`
- `project_phase = None` (approval is a checkpoint, not a lifecycle transition)
- `accepted`: bool (determined by human or autonomous mode)

**Return shape (unified for both approval and rejection):**
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
    update={
        "acceptance_stamps": {approval_type: handoff_record},  # Gate-specific key
    },
)

# The handoff_record includes:
# - accepted: bool (True for approval, False for rejection)
# - feedback: str | None (rejection reason if rejected, None if approved)
```

**PM re-entry behavior:**
- `approval_result_message` is a `HumanMessage` sent via `Send` directly to the mounted `project_manager` role.
- If `accepted=True`, the message tells PM the approval stamp was recorded and the gated handoff may be retried.
- If `accepted=False`, the message includes `record["feedback"]` and instructs PM to revise the package before requesting approval again.

The tool does NOT append to `handoff_log` and does NOT route through
`dispatch_handoff`, because approval is PM self-re-entry rather than an
agent-to-agent handoff. Approval records live only in `acceptance_stamps` with
gate-specific keys to prevent stale approval reuse. Gate middleware later reads
the stamp from `pcg_gate_context` when PM retries the gated handoff.

Because this self-reentry bypasses `dispatch_handoff`, the tool body must build
`refreshed_gate_context` by merging `{approval_type: handoff_record}` into the
current `runtime.state["pcg_gate_context"]["acceptance_stamps"]` projection.
This keeps the immediate PM re-entry runtime-aligned with the parent PCG update.

### 6.2 Approval Package Schemas

#### 6.2.1 Scoping-to-Research Package

**Approval type:** `scoping_to_research`

**Required artifacts in `artifact_paths`:**
- PRD document (`.md` or `.txt`)
- HE eval suite summary (`.md` or `.txt`)
- Public evaluation criteria (`.md` or `.txt`)
- Public datasets manifest or reference (`.md`, `.txt`, or `.csv`)

**Package brief template:**
```
PRD and evaluation design ready for research phase.

PRD: <brief summary of product vision and requirements>
HE eval suite: <summary of rubrics, public datasets, and calibration status>
Public criteria: <summary of evaluation metrics and success criteria>

This package transitions from scoping to research. Researcher will use this to identify SDKs, APIs, and abstractions that satisfy the PRD requirements with the specified evaluation framework.
```

#### 6.2.2 Architecture-to-Planning Package

**Approval type:** `architecture_to_planning`

**Required artifacts in `artifact_paths`:**
- Design spec (`.md` or `.txt`)
- Tool schemas (`.json`, `.yaml`, or `.py` with schema definitions)
- System prompts (`.md` files for each agent/component)
- Research bundle (from Researcher, `.md` or `.txt`)
- Eval coverage report (from HE Stage 2, `.md` or `.txt`)

**Package brief template:**
```
Design specification ready for implementation planning.

Design spec: <brief summary of architecture, components, and data flow>
Tool schemas: <summary of tool contracts and integration points>
System prompts: <summary of agent behavioral contracts>
Research bundle: <summary of SDK/API findings and references>
Eval coverage: <summary of development-phase eval harness readiness>

This package transitions from architecture to planning. Planner will use this to create a phased implementation plan with evaluation breakpoints.
```

### 6.3 Approval Tool Runtime Behavior

#### 6.3.1 Interactive Mode

When `autonomous_mode` is `False` or absent from runtime config:

1. PM calls `request_approval(package_brief, artifact_paths, approval_type)`
2. Tool body triggers a human interrupt via `langgraph.types.interrupt()` with approval payload
3. Human reviews package in UI (web app, TUI, or headless adapter)
4. Human selects decision: `approve` or `reject`
5. Tool creates `HandoffRecord` with `accepted=True/False` and `feedback`
   (rejection reason if rejected), emits `Command.PARENT` to update
   `acceptance_stamps[{approval_type}]`, and schedules
   `Send("project_manager", {"messages": [approval_result_message], "pcg_gate_context": refreshed_gate_context})`
6. PM re-enters with the approval-result message:
   - If `accepted=True`: Proceeds to call the gated handoff tool
   - If `accepted=False`: Uses the included rejection feedback to revise the package

**Interrupt payload shape:**
```python
{
    "type": "approval_request",
    "approval_type": "scoping_to_research" | "architecture_to_planning",
    "package_brief": str,
    "artifact_paths": list[str],
    "project_id": str,
    "project_thread_id": str,
}
```

**Human decision response shape:**
```python
{
    "decision": "approve" | "reject",
    "feedback": str | None,  # Required if reject, optional if approve
}
```

#### 6.3.2 Autonomous Mode

When `autonomous_mode=True` in runtime config (bridged by
`pcg-server-contract.md §6.1`):

1. PM calls `request_approval(package_brief, artifact_paths, approval_type)`
2. Tool body bypasses human interrupt entirely
3. Tool auto-creates `HandoffRecord` with `accepted=True` for the gate-specific key
4. Tool emits `Command.PARENT` to update `acceptance_stamps[{approval_type}]`
   and schedules `Send("project_manager", {"messages": [approval_result_message], "pcg_gate_context": refreshed_gate_context})`
5. No human feedback loop; PM re-enters with the approval-result message and
   proceeds to the next handoff

**Autonomous mode detection:**
```python
autonomous_mode = bool(runtime.config.get("configurable", {}).get("autonomous_mode", False))
```

### 6.4 Approval Tool Integration with Gate Middleware

The two user-approval gates (`deliver_prd_to_researcher` and `deliver_planning_package_to_planner`) check for gate-specific approval stamps. They do NOT call the approval tool themselves.

Workflow:
1. PM calls `request_approval(approval_type="scoping_to_research")` → creates stamp in `acceptance_stamps["scoping_to_research"]` and re-enters PM with an approval-result message plus refreshed `pcg_gate_context`
2. PM calls gated handoff tool (e.g., `deliver_prd_to_researcher`)
3. Gate middleware checks `pcg_gate_context.acceptance_stamps["scoping_to_research"]["accepted"]`
4. If `True`: gate passes, tool executes, returns `Command.PARENT`
5. If `False` or missing: gate fails, returns revision `ToolMessage`

This separation allows the PM to present the package for review, receive approval, and then proceed to handoff in separate turns. Gate-specific keys prevent stale approval reuse (a stamp from one gate cannot satisfy a different gate).

## 7. Terminal Emission Contract

### 7.1 `finish_to_user` Tool Schema

**Tool name:** `finish_to_user` (PM-only, Category 7)

**Model-visible parameters:**
```python
class TerminalEmissionInput(TypedDict):
    final_response: str  # PM's final user-facing message
```

**Fixed fields (hidden from model):**
- No `HandoffRecord` is created
- No `source_agent`, `target_agent`, `reason`, `project_phase`, `plan_phase_id`

**Return shape:**
```python
Command(
    graph=Command.PARENT,
    goto=END,
    update={"messages": [AIMessage(content=final_response)]},
)
```

**Side effects:**
- Writes only to PCG `messages` channel
- Does NOT append to `handoff_log`
- Does NOT write to `acceptance_stamps`
- Terminates the PCG graph (goto=END)

### 7.2 Terminal Emission Writer Behavior

The tool body is minimal:

```python
@tool
def finish_to_user(final_response: str) -> Command:
    """Send the final user-facing response and terminate the PCG turn."""
    return Command(
        graph=Command.PARENT,
        goto=END,
        update={"messages": [AIMessage(content=final_response)]},
    )
```

No state reads, no Project Records Layer writes, no Store operations. The tool is a pure graph termination primitive.

### 7.3 Graph Termination Semantics

When `finish_to_user` returns `Command(graph=PARENT, goto=END)`:

1. LangGraph Pregel receives the command at the PCG level
2. `goto=END` terminates the current graph execution
3. `update={"messages": [...]}` writes the final `AIMessage` to PCG state
4. The run completes and returns to the Agent Server / client surface
5. No further agent turns execute in this project thread invocation

The PCG does not have a `END` node. The termination is handled by LangGraph's built-in `END` sentinel.

### 7.4 When PM Uses `finish_to_user`

**PM session threads:**
- After any conversation turn where PM has provided a complete response
- No pre-condition check; PM's system prompt decides when to invoke

**Project threads:**
- After presenting the finished product to the user (via `ask_user` middleware) and receiving satisfaction confirmation
- After any PM session-thread terminal conversation turn (e.g., project closure, status summary)

**Pre-terminal interaction:**
- PM typically uses `AskUserMiddleware` to present the product and ask "Are you satisfied with this result?"
- If user confirms satisfaction, PM calls `finish_to_user`
- If user requests changes, PM continues work (does not call `finish_to_user`)

### 7.5 Autonomous Mode Interaction

When `autonomous_mode=True`:

- PM skips the pre-terminal `ask_user` satisfaction check
- PM calls `finish_to_user` directly after completing the product
- No human interrupt occurs before termination
- The final response in `finish_to_user` should include a summary of what was delivered

## 8. Final-Turn Guard Middleware

### 8.1 Purpose

The final-turn guard enforces the §1.3 invariant from `handoff-tools.md`: every role turn MUST terminate by emitting `Command(graph=Command.PARENT, ...)`. This prevents LangGraph's default subgraph state-mapping from merging a naturally-completing role's conversation history into PCG `messages`.

### 8.2 Middleware Installation

**Installed on:** All 7 role Deep Agents (PM, HE, Researcher, Architect, Planner, Developer, Evaluator)

**Stack position:** Last entry in the role-supplied custom middleware list,
after `AskUserMiddleware` and phase-gate middleware when either is present.
Do not rely on Deep Agents' `interrupt_on` shortcut for this ordering:
`create_deep_agent()` appends its optional `HumanInTheLoopMiddleware` after
caller-provided middleware, so a role that needs a custom final-turn guard must
install the guard explicitly in the `middleware=[...]` argument.

**Middleware class:** `FinalTurnGuardMiddleware`

**State schema:**

```python
class FinalTurnGuardState(AgentState):
    _final_turn_guard_nudges: NotRequired[Annotated[int, PrivateStateAttr]]
```

The counter is graph state, not middleware instance state. `PrivateStateAttr`
keeps it out of child input and output schemas while preserving it across the
agent loop inside a single invocation/checkpoint.

### 8.3 Middleware Hook

Uses `after_model` hook with `jump_to` support:

```python
@hook_config(can_jump_to=["model"])
async def aafter_model(
    self,
    state: AgentState[Any],
    runtime: Runtime[ContextT],
) -> dict[str, Any] | None:
```

SDK behavior verified against source:
- `jump_to` state field: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:354`
- `hook_config` decorator: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:856-906`
- Conditional edge resolution: `.venv/lib/python3.11/site-packages/langchain/agents/factory.py:1659-1671`

### 8.4 Trigger Conditions

The guard triggers when:

1. The last message in `state["messages"]` is an `AIMessage`
2. The `AIMessage` has NO tool calls (`tool_calls` is empty or None)

If the last `AIMessage` contains any tool call, the guard does not trigger and
returns `{"_final_turn_guard_nudges": 0}` when the counter is non-zero. This
resets the counter at the successful end of a guarded turn.

### 8.5 Re-Prompt Update

When triggered, the guard injects a `SystemMessage` and sets `jump_to: "model"` to force another iteration:

```python
nudge_message = SystemMessage(
    content=(
        "You must conclude your turn by calling a handoff tool or the terminal finish_to_user tool. "
        "Do not end your turn with a plain response. "
        "Use the appropriate handoff tool to transfer work or finish_to_user to terminate."
    )
)
return {
    "messages": [nudge_message],
    "_final_turn_guard_nudges": next_nudge_count,
    "jump_to": "model",  # Force another model iteration
}
```

The message is appended via the `add_messages` reducer, so it becomes the last message in the conversation history. The `jump_to: "model"` directive routes the graph back to the model node, bypassing the tools node and triggering another model call with the nudge message in context.

### 8.6 Loop Behavior and Stop Condition

After injecting the nudge:

1. The agent loop continues to the next model iteration
2. The model sees the nudge and should call a tool
3. If the model still does not call a tool (e.g., ignores the nudge), the guard triggers again
4. To prevent infinite loops, the guard tracks how many times it has nudged in the current turn via `state["_final_turn_guard_nudges"]`

**Counter semantics:**

- Missing `_final_turn_guard_nudges` means `0`.
- On each trigger, compute `next_nudge_count = current_count + 1`.
- If `next_nudge_count <= 3`, inject the nudge and write the updated counter.
- If the next model response contains a tool call, reset the counter to `0`.
- If a new invocation starts from a clean role checkpoint, the missing key starts
  at `0`; if a checkpoint resumes mid-loop, the private state value continues so
  the guard cannot loop forever after resume.

**Stop condition:** If `next_nudge_count > 3`, the guard raises an exception:

```python
raise RuntimeError(
    "Agent failed to terminate turn with tool call after 3 nudges. "
    "This indicates a prompt or system configuration issue."
)
```

The exception surfaces to the caller (PCG for role subgraphs, Agent Server for standalone PM session threads). Middleware instance attributes MUST NOT be used for this counter because one middleware instance can serve multiple runs or threads.

### 8.7 Interaction with `finish_to_user`

The PM's `finish_to_user` tool is a handoff tool for the purposes of the final-turn guard. When PM calls `finish_to_user`:

1. The `AIMessage` contains a tool call to `finish_to_user`
2. The guard does NOT trigger (condition: `AIMessage.tool_calls` is non-empty)
3. Tool executes, returns `Command(graph=PARENT, goto=END)`
4. Graph terminates normally

The guard only triggers on natural completions (plain text responses without tool calls).

### 8.8 Conformance Test Requirements

Tests must verify:

1. A role that ends with a plain `AIMessage` (no tool call) receives the nudge and is forced to iterate again
2. A role that ends with a tool call (handoff or `finish_to_user`) does NOT receive the nudge
3. After 3 nudge attempts without a tool call, the guard raises an exception
4. The nudge message content matches the spec exactly
5. The guard is installed on all 7 role agents
6. The guard is the last role-supplied custom middleware, after `AskUserMiddleware` and phase-gate middleware when present

## 9. Gate Middleware Implementation Contract

### 9.1 Middleware Class Structure

```python
class PMPhaseGateMiddleware(AgentMiddleware):
    """Phase gate middleware for PM handoff tools."""

    state_schema = PhaseGateState

    def __init__(self) -> None:
        super().__init__()
        self._gate_functions = {
            "deliver_prd_to_harness_engineer": check_prd_finalized_gate,
            "deliver_prd_to_researcher": check_scoping_to_research_gate,
            "deliver_design_package_to_architect": check_research_complete_gate,
            "deliver_planning_package_to_planner": check_architecture_to_planning_gate,
            "deliver_development_package_to_developer": check_plan_accepted_gate,
        }

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]

        if tool_name not in self._gate_functions:
            # Not a gated tool, pass through
            return await handler(request)

        gate_context = request.state.get("pcg_gate_context")
        if gate_context is None:
            raise RuntimeError(
                f"Missing pcg_gate_context for gated tool {tool_name}. "
                "Check dispatch_handoff Send payload and gate middleware state_schema."
            )

        gate_func = self._gate_functions[tool_name]
        pass, feedback = await gate_func(
            tool_name=tool_name,
            tool_args=tool_args,
            gate_context=gate_context,
            runtime=request.runtime,
        )

        if pass:
            # Gate satisfied, execute tool
            return await handler(request)
        else:
            # Gate failed, return revision feedback without executing tool
            return ToolMessage(
                content=feedback,
                name=tool_name,
                tool_call_id=request.tool_call["id"],
                status="error",
            )
```

### 9.2 Architect and Developer Middleware

Similar structure with their respective gated tool sets:

**ArchitectPhaseGateMiddleware:**
- Gated tool: `submit_spec_to_harness_engineer`
- Gate function: `check_spec_accepted_gate`

**DeveloperPhaseGateMiddleware:**
- Gated tools: `return_product_to_pm`, `submit_phase_to_evaluator`
- Gate functions: `check_acceptance_stamps_gate`, `check_phase_announcement_gate`

Both classes MUST set `state_schema = PhaseGateState` in the class body, or
inherit from a shared phase-gate base class that sets it. A gate middleware
class that inherits the default `AgentMiddleware.state_schema` is invalid
because `pcg_gate_context` would not be part of the role agent input schema.

`submit_phase_to_harness_engineer` is deliberately not installed in the
Developer gate map; row 18 has no middleware gate in the canonical handoff
matrix.

### 9.3 Approval Tool Rejection Handling (No Middleware Required)

The `request_approval` tool handles both approval and rejection through a unified return pattern. Since a tool can only return one value, the tool always returns `Command.PARENT` with the stamp update and a direct PM re-entry `Send`.

**Key insight:** There is no middleware for rejection persistence. The tool body itself always emits `Command.PARENT` with the stamp and a model-visible approval-result message. The distinction between approval and rejection is captured in the stamp's `accepted` and `feedback` fields, not in the return type.

**Return behavior:**

```python
# Both approval and rejection return Command.PARENT with stamp and PM re-entry
Command(
    graph=Command.PARENT,
    goto=Send(
        "project_manager",
        {
            "messages": [approval_result_message],
            "pcg_gate_context": refreshed_gate_context,
        },
    ),
    update={
        "acceptance_stamps": {approval_type: record},
    },
)

# The record always includes:
# - accepted: bool (True for approval, False for rejection)
# - feedback: str | None (rejection reason if rejected, None if approved)
```

**PM re-entry behavior:**

On re-entry after `request_approval`, the PM receives
`approval_result_message` and refreshed `pcg_gate_context` as the next child
input:

1. **If `accepted=True`:** The message tells PM the approval stamp was recorded and the gated handoff may be retried.
2. **If `accepted=False`:** The message includes `record["feedback"]` and instructs PM to revise before requesting approval again.

This design satisfies the runtime constraint (single return value), preserves
the audit trail (rejected stamps are persisted), and provides model feedback
through the explicit PM re-entry message. Gate middleware remains responsible
for reading `pcg_gate_context.acceptance_stamps[approval_type]` when PM retries
the gated handoff.

### 9.4 Error Handling

Gate functions should raise exceptions only for implementation defects:

**Defect examples (raise exception):**
- `pcg_gate_context` is missing from a gated role input
- `gate_context` is missing required keys (corrupted projection)
- `handoff_log` is not a list
- `acceptance_stamps` is not a dict
- Tool args have wrong types (schema validation failure before gate check)

**Recoverable failures (return feedback):**
- Prerequisite not met (missing prior handoff)
- Approval stamp missing or rejected
- Artifact paths empty or wrong file type
- Phase announcement not found

### 9.4 State/Project Records Layer Read Isolation

Gate functions read from:

- `pcg_gate_context`: projected `handoff_log`, `acceptance_stamps`, `current_phase`, and project identity
- Runtime context: `runtime.config` (for autonomous mode detection in approval tool)
- Tool arguments: `tool_args` (model-visible inputs)

Gate functions do NOT write to state or Project Records Layer. Writes happen only in:
- Tool body (creates `HandoffRecord`, writes to Store)
- Approval tool (creates stamp in `acceptance_stamps`)
- Middleware side-effect hooks (not used for gates)

## 10. Autonomous Mode Detection and Behavior

### 10.1 Detection

Autonomous mode is read from runtime config:

```python
configurable = runtime.config.get("configurable", {})
autonomous_mode = configurable.get("autonomous_mode", False)
```

Configured at thread creation time via Agent Server thread metadata or project context.
`pcg-server-contract.md §6.1` owns the exact bridge from
`ProjectCoordinationInput.autonomous_mode_config.enabled` and optional thread
metadata into this runnable config key. Gate and approval code MUST NOT read the
input payload or thread metadata directly.

### 10.2 Autonomous Mode Behavior Matrix

| Gate/Approval checkpoint | Interactive mode | Autonomous mode |
|---|---|---|
| `deliver_prd_to_harness_engineer` (prerequisite) | Check artifact_paths | Same |
| `deliver_prd_to_researcher` (prerequisite + approval) | Check HE return + approval stamp | Check HE return + auto-approve (create stamp immediately) |
| `deliver_design_package_to_architect` (prerequisite) | Check Researcher return | Same |
| `deliver_planning_package_to_planner` (prerequisite + approval) | Check HE Stage 2 return + Architect return + approval stamp | Check HE Stage 2 return + Architect return + auto-approve (create stamp immediately) |
| `deliver_development_package_to_developer` (prerequisite) | Check Planner return | Same |
| `submit_spec_to_harness_engineer` (prerequisite) | Check artifact_paths | Same |
| `return_product_to_pm` (acceptance) | Check application + harness stamps | Same (acceptance gates never auto-approve) |
| `submit_phase_to_evaluator` (prerequisite) | Check announcement + artifact_paths | Same |
| `submit_phase_to_harness_engineer` (ungated) | No middleware gate | Same |
| `request_approval` tool | Human interrupt, persist stamp, re-enter PM with result message + refreshed `pcg_gate_context` | Bypass interrupt, create stamp with accepted=True, re-enter PM with result message + refreshed `pcg_gate_context` |
| `finish_to_user` tool | After `ask_user` satisfaction check | Directly after product complete (skip `ask_user`) |
| Final-turn guard | Enforce tool call termination | Same |

### 10.3 Approval Tool Autonomous Mode Implementation

```python
from langchain_core.messages import HumanMessage
from langgraph.types import Command, Send

@tool
async def request_approval(
    package_brief: str,
    artifact_paths: list[str],
    approval_type: Literal["scoping_to_research", "architecture_to_planning"],
    runtime: ToolRuntime,
) -> Command:
    autonomous_mode = bool(runtime.config.get("configurable", {}).get("autonomous_mode", False))

    if autonomous_mode:
        # Auto-approve without human interrupt
        accepted = True
        feedback = None
    else:
        # Trigger human interrupt
        interrupt_payload = {
            "type": "approval_request",
            "approval_type": approval_type,
            "package_brief": package_brief,
            "artifact_paths": artifact_paths,
            "project_id": runtime.config.get("configurable", {}).get("project_id"),
            "project_thread_id": runtime.config.get("configurable", {}).get("project_thread_id"),
        }
        decision = interrupt(interrupt_payload)  # Blocks until human responds

        accepted = decision["decision"] == "approve"
        feedback = decision.get("feedback")

    # Create approval stamp record (includes feedback for rejection)
    record = create_approval_handoff_record(
        source_agent="project_manager",
        target_agent="project_manager",
        reason="submit",
        accepted=accepted,
        feedback=feedback if not accepted else None,  # Rejection reason preserved
        brief=f"Approval request: {approval_type}",
        artifact_paths=artifact_paths,
        runtime=runtime,
    )

    if accepted:
        approval_result_message = HumanMessage(
            content=(
                f"Approval recorded for {approval_type}. "
                "You may now retry the gated handoff."
            )
        )
    else:
        approval_result_message = HumanMessage(
            content=(
                f"Approval rejected for {approval_type}.\n\n"
                f"Feedback: {feedback}\n\n"
                "Revise the package before requesting approval again."
            )
        )

    current_gate_context = runtime.state["pcg_gate_context"]
    refreshed_gate_context = {
        **current_gate_context,
        "acceptance_stamps": {
            **current_gate_context.get("acceptance_stamps", {}),
            approval_type: record,
        },
    }

    # Always return Command.PARENT with stamp update and PM re-entry.
    return Command(
        graph=Command.PARENT,
        goto=Send(
            "project_manager",
            {
                "messages": [approval_result_message],
                "pcg_gate_context": refreshed_gate_context,
            },
        ),
        update={
            "acceptance_stamps": {approval_type: record},  # Gate-specific key
        },
    )
```

## 11. Conformance Tests

### 11.1 Gate Pass Tests

For each gated tool, verify:

1. When all pass conditions are satisfied, gate middleware calls the handler
2. Tool executes and returns `Command.PARENT`
3. Parent command updates PCG state correctly
4. No `ToolMessage` with error status is returned

**Test matrix:**

| Tool | Test scenario |
|---|---|
| `deliver_prd_to_harness_engineer` | artifact_paths non-empty with .md file → pass |
| `deliver_prd_to_researcher` | HE return exists + approval stamp accepted=True → pass |
| `deliver_design_package_to_architect` | Researcher return exists → pass |
| `deliver_planning_package_to_planner` | HE Stage 2 return exists + Architect return exists + approval stamp accepted=True → pass |
| `deliver_development_package_to_developer` | Planner return exists → pass |
| `submit_spec_to_harness_engineer` | artifact_paths non-empty with .md file → pass |
| `return_product_to_pm` | application stamp accepted=True + HE stamp accepted=True (when HE participated) → pass |
| `submit_phase_to_evaluator` | Matching announcement exists + artifact_paths non-empty → pass |

### 11.2 Gate Failure Tests

For each gated tool, verify:

1. When a pass condition fails, gate middleware returns `ToolMessage` with error status
2. Tool handler is NOT called
3. No parent command is emitted
4. Feedback message matches spec exactly
5. Model receives revision instruction and can retry

**Test matrix:**

| Tool | Failure scenario | Expected feedback substring |
|---|---|---|
| `deliver_prd_to_harness_engineer` | artifact_paths empty | "PRD artifact not found" |
| `deliver_prd_to_researcher` | HE return missing | "Harness Engineer Stage 1 not complete" |
| `deliver_prd_to_researcher` | Approval stamp missing | "requires stakeholder approval" |
| `deliver_prd_to_researcher` | Approval stamp rejected | "accepted=False" |
| `deliver_design_package_to_architect` | Researcher return missing | "Research not complete" |
| `deliver_planning_package_to_planner` | HE Stage 2 return missing | "Harness Engineer Stage 2 not complete" |
| `deliver_planning_package_to_planner` | Architect return missing | "Design spec not complete" |
| `deliver_planning_package_to_planner` | Approval stamp missing | "requires stakeholder approval" |
| `deliver_planning_package_to_planner` | Approval stamp rejected | "accepted=False" |
| `deliver_development_package_to_developer` | Planner return missing | "Implementation plan not complete" |
| `submit_spec_to_harness_engineer` | artifact_paths empty | "Design spec artifact not found" |
| `return_product_to_pm` | Application stamp missing | "Evaluator acceptance stamp not found" |
| `return_product_to_pm` | Application stamp rejected | "rejected the application" |
| `return_product_to_pm` | HE stamp missing (HE participated) | "Harness Engineer acceptance stamp not found" |
| `return_product_to_pm` | HE stamp rejected | "rejected the target harness" |
| `submit_phase_to_evaluator` | No matching announcement | "No matching announcement" |
| `submit_phase_to_evaluator` | artifact_paths empty | "No phase deliverables" |

### 11.3 Autonomous Mode Tests

Verify:

1. In autonomous mode, `request_approval` bypasses human interrupt and creates stamp with `accepted=True`
2. In autonomous mode, `request_approval` re-enters PM with an approval-result message and refreshed `pcg_gate_context` via `Send`
3. In autonomous mode, approval gates pass without human approval (stamp exists immediately)
4. In autonomous mode, `finish_to_user` is called without pre-terminal `ask_user`
5. In interactive mode, `request_approval` triggers interrupt and waits for decision
6. In interactive mode, rejected approval persists a stamp and re-enters PM with rejection feedback plus refreshed `pcg_gate_context`
7. In interactive mode, approval gates fail without approval stamp
8. Autonomous mode flag is read from `runtime.config["configurable"]["autonomous_mode"]`
9. Gated role middleware raises if `pcg_gate_context` is missing from child state

### 11.4 Terminal Emission Tests

Verify:

1. `finish_to_user` returns `Command(graph=PARENT, goto=END, update={"messages": [...]})`
2. `finish_to_user` does NOT append to `handoff_log`
3. `finish_to_user` does NOT write to `acceptance_stamps`
4. PCG terminates after `finish_to_user` (no further nodes execute)
5. Final `AIMessage` in PCG `messages` matches the `final_response` parameter

### 11.5 Final-Turn Guard Tests

Verify:

1. Role ending with plain `AIMessage` (no tool call) receives nudge `SystemMessage`
2. Role ending with tool call (handoff or `finish_to_user`) does NOT receive nudge
3. After nudge, model is forced to iterate again
4. After 3 nudge attempts without tool call, guard raises `RuntimeError`
5. Nudge message content matches spec exactly
6. Guard is installed on all 7 role agents
7. Guard is in tail stack position

### 11.6 Approval Package Tests

Verify:

1. Scoping-to-research package requires PRD, HE eval suite, public criteria, public datasets
2. Architecture-to-planning package requires design spec, tool schemas, system prompts, research bundle, eval coverage
3. Approval tool creates stamp in `acceptance_stamps[{approval_type}]` where approval_type is "scoping_to_research" or "architecture_to_planning" (not `handoff_log`)
4. Approval stamp has `source_agent="project_manager"`, `target_agent="project_manager"`, `reason="submit"`
5. Rejected approval creates stamp with `accepted=False` and returns `Command.PARENT` with `goto=Send("project_manager", ...)` containing rejection feedback and refreshed `pcg_gate_context`
6. Approved approval creates stamp with `accepted=True` and returns `Command.PARENT` with `goto=Send("project_manager", ...)` containing approval confirmation and refreshed `pcg_gate_context`

## 12. Interaction Between `ask_user`, Approval Tools, and `finish_to_user`

### 12.1 Normal Interactive Flow

```txt
PM completes work (e.g., PRD, design spec, or finished product)
  → PM calls ask_user (via AskUserMiddleware)
  → Human reviews and provides feedback
  → If feedback requires changes: PM revises work, loops back
  → If feedback is approval: PM calls request_approval (for scoping→research or architecture→planning)
  → Human approves via interrupt
  → Approval stamp created and refreshed pcg_gate_context sent back to PM
  → PM calls gated handoff tool
  → Gate passes (stamp exists)
  → Handoff executes
```

### 12.2 Terminal Flow (Project Completion)

```txt
Developer returns product to PM
  → Evaluator and HE acceptance stamps verified
  → PM presents product via ask_user
  → Human: "Are you satisfied with this result?"
  → If human requests changes: PM routes to Developer (loop)
  → If human confirms satisfaction: PM calls finish_to_user
  → PCG terminates
```

### 12.3 Autonomous Mode Flow

```txt
PM completes work
  → PM calls request_approval
  → Autonomous mode: bypass interrupt, auto-approve stamp created and refreshed pcg_gate_context sent back to PM
  → PM calls gated handoff tool
  → Gate passes (stamp exists)
  → Handoff executes
  ...
Developer returns product to PM
  → PM skips ask_user
  → PM calls finish_to_user directly
  → PCG terminates
```

### 12.4 PM-session Flow

```txt
User sends PM-session turn
  → PCG session mode routes input to mounted PM
  → PM may call ask_user for clarification
  → PM may call session tools such as spawn_project or project-status reads
  → PM calls finish_to_user
  → PCG terminates the current session run
```

`request_approval` and phase-gate middleware are project-mode only. They are not
model-visible on `pm_session` threads because session mode has no project
handoff topology, no `pcg_gate_context`, and no `acceptance_stamps` parent state.
`ask_user` and `finish_to_user` remain available to the PM in both modes. See
`pcg-server-contract.md §7.5` for the session input/state contract.

### 12.5 Separation of Concerns

- `ask_user` (AskUserMiddleware): General human feedback loop, not tied to specific gates
- `request_approval`: Structured approval checkpoint for specific lifecycle transitions, creates audit trail in `acceptance_stamps`
- `finish_to_user`: Terminal emission primitive, graph termination
- Gate middleware: Pre-execution checks on handoff tools, enforces prerequisites and approval stamp existence

These four mechanisms compose to provide the full approval and termination contract without overlapping responsibilities.
