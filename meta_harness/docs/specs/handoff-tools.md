---
doc_type: spec
derived_from:
  - AD §4 Handoff Protocol
  - AD §4 Handoff Tool Use-Case Matrix
status: active
last_synced: 2026-04-27
owners: ["@Jason"]
---

# Handoff Tools Specification

> **Provenance:** Derived from `AD.md §4 Handoff Protocol` (tool catalog, role-scoped ownership, pipeline order, gate semantics) and `§4 Handoff Tool Use-Case Matrix` (23-tool matrix).
> **Status:** Active · **Last synced with AD:** 2026-04-27 (updated for `OQ-HO` resolution: 1 dispatcher + 7 mounted role subgraphs; `acceptance_stamps` channel; `finish_to_user` terminal-emission tool added; clarified sibling relationship with `pcg-data-contracts.md` and concrete definitions spec; **clarified acceptance gate truth semantics per Ticket 4: gate requires both stamp presence AND accepted is True**).
> **Consumers:** Developer (implementation), Evaluator (conformance checking).

## 1. Purpose

This spec is the interface contract for agent-to-agent handoff tools in Meta
Harness. It enumerates the 23 concrete tools that implement the decisions
locked in `AD.md §4`: the `reason` enum, verb semantics, PM-as-hub pipeline,
and middleware gate policy.

The parent AD defines *what* handoffs are and *why* they route the way they
do. This spec defines *which concrete tools exist, who owns them, what
artifacts they carry, and which middleware gate applies*.

**Relationship to PCG data contracts and concrete definitions.** This spec
owns the semantic tool catalog: tool names, caller/target roles, reason values,
artifact flow, middleware gates, role-scoped ownership, and pipeline order. It
intentionally does not own the full PCG state or concrete model-visible schemas.
Shared data contracts live in `docs/specs/pcg-data-contracts.md`: state
channels, reducers, `Command.PARENT` update shape, `HandoffRecord` fields, and
field ownership. Concrete per-tool definitions live in
`docs/specs/handoff-tool-definitions.md`: descriptions, visible parameters,
runtime-injected inputs, fixed fields, and return shapes. Code generation or
implementation must compose all three specs.

## 1.1 Uniform Tool Return Shape (handoff tools)

Every handoff tool in this spec returns exactly the shape below. The only
variation is in the `update` dict payload; the `graph` and `goto` are
identical for all 23 handoff tools.

```python
Command(
    graph=Command.PARENT,
    goto="dispatch_handoff",
    update={
        "handoff_log": [handoff_record],            # append via operator.add
        "current_agent": target_agent,               # overwrite
        "current_phase": new_project_phase_if_transition,  # OMIT if no lifecycle transition
        # Acceptance-stamp tools additionally include:
        # "acceptance_stamps": {"application": stamp_record}
        #   or
        # "acceptance_stamps": {"harness": stamp_record}
    },
)
```

The update dict **never** includes `messages` (reserved for the terminal
`finish_to_user` tool) and **never** includes a `pending_handoff` key
(removed in `OQ-HO` resolution). See `docs/specs/pcg-data-contracts.md §5`
for the full update contract.

The PM additionally owns one **terminal-emission tool** that uses a
different shape — see §1.3 and §4.7 (Category 7: Terminal Emission).

## 1.2 Store-Side Effects

Artifact-producing tools additionally write to the `artifact_manifest`
`Store` namespace (`("projects", project_id, "artifact_manifest")`) so that
any surface — TUI, web app, headless ingress, PM session threads — can
enumerate project artifacts without walking role filesystems. Recommended
implementation: a thin middleware hook on artifact-producing tools performs
the Store write, keeping the tool body focused on the handoff contract.

The Harness Engineer's trendline-producing tool additionally writes to the
`optimization_trendline` `Store` namespace. Developer filesystem
permissions exclude this namespace (Developer info isolation). See
`docs/specs/pcg-data-contracts.md §7`.

## 1.3 Every Turn Terminates with `Command.PARENT`

**Invariant.** A role subgraph's turn MUST end by emitting `Command(graph=Command.PARENT, ...)`. Specialists satisfy this naturally — their final tool call is a handoff tool. The PM satisfies it via either a handoff tool or the terminal `finish_to_user` tool (Category 7).

**Why.** LangGraph's mounted-subgraph state mapping merges a naturally-completing subgraph's final state into parent state via shared channel reducers. PCG has `messages` with `add_messages`; a role Deep Agent's `_OutputAgentState` also exposes `messages` (its full conversation history). Without this invariant, every role's natural completion would append the child's entire conversation to PCG `messages`, violating the user-facing-I/O-only invariant.

**Enforcement.** Every role receives a thin **final-turn-guard middleware** in its stack. The middleware's `after_model` hook inspects the agent's last `AIMessage`: if it contains no tool call to a handoff tool or `finish_to_user`, the middleware injects a `SystemMessage` nudge instructing the agent to conclude its turn via the appropriate tool, and forces another model iteration. This is a prompt-hygiene safety net; a correctly-prompted role should never trigger it. The middleware is distinct from `StagnationGuardMiddleware` (which handles overall cost/progress) and runs in the tail stack alongside `HumanInTheLoopMiddleware`.

## 2. Naming Convention

Tool names read as sentences: `<verb>_<artifact|phase>_to_<role>`.

- Single-artifact deliveries use the artifact name (e.g.
  `deliver_prd_to_harness_engineer`).
- Composite package deliveries use the phase name plus `package` (e.g.
  `deliver_design_package_to_architect`) to signal that the PM is handing off
  a consolidated bundle of accumulated artifacts.

## 3. Verb Semantics

Defined as AD decisions; restated here for reference. Verb choice encodes
blocking behavior:

- **`deliver`** — caller hands off ownership of a pipeline stage (blocking).
- **`return`** — specialist returns completed work to PM or calling specialist (blocking).
- **`submit`** — caller submits work for review or evaluation (blocking).
- **`consult`** — caller requests expert input without transferring ownership (non-blocking).
- **`announce`** — caller pushes intent or a heads-up without expecting a deliverable back (non-blocking).
- **`ask`** — caller asks a question (non-blocking).
- **`coordinate`** — QA agents align with each other (non-blocking).

## 4. Tool Matrix

Tools are organized into six categories by transition type.

### 4.1 Pipeline Delivery — PM delivers artifact to start a pipeline stage

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 1 | `deliver_prd_to_harness_engineer` | `deliver` | PM | HE | PRD + proposed eval criteria + business-logic datasets → refined eval criteria, rubrics, public/held-out datasets, calibrated judges | Stage 1: PRD finalized |
| 2 | `deliver_prd_to_researcher` | `deliver` | PM | Researcher | PRD + refined eval criteria + public datasets → research bundle | HE Stage 1 complete |
| 3 | `deliver_design_package_to_architect` | `deliver` | PM | Architect | PRD + eval suite + research bundle → design spec | Research complete |
| 4 | `deliver_planning_package_to_planner` | `deliver` | PM | Planner | Design spec + public eval criteria + public datasets → implementation plan | HE Stage 2 complete |
| 5 | `deliver_development_package_to_developer` | `deliver` | PM | Developer | Plan + spec + public eval + PRD → phase deliverables | Plan accepted |

### 4.2 Pipeline Return — Specialist returns completed work to PM

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 6 | `return_eval_suite_to_pm` | `return` | HE | PM | Refined eval criteria + rubrics + public datasets (HE retains held-out datasets + copies in its own filesystem) | None |
| 7 | `return_research_bundle_to_pm` | `return` | Researcher | PM | Research bundle with findings and refs | None |
| 8 | `return_design_package_to_pm` | `return` | Architect | PM | Design spec + tool schemas + system prompts | None |
| 9 | `return_plan_to_pm` | `return` | Planner | PM | Phased implementation plan with eval break points | None |
| 10 | `return_product_to_pm` | `return` | Developer | PM | Finished product + final artifacts → PM presents to user | Evaluator acceptance required; HE acceptance required if HE participated in project |

### 4.3 Acceptance — QA agents submit acceptance stamps (non-blocking)

The Developer's `return_product_to_pm` gate reads the first-class
`acceptance_stamps` state channel populated by these tools.

| # | Tool | `reason` | Caller | Target | `acceptance_stamps` write | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|---|
| 11 | `submit_harness_acceptance` | `submit` | HE | PM | `{"harness": stamp_record}` | Acceptance stamp: target harness quality verified | None (stamp only) |
| 12 | `submit_application_acceptance` | `submit` | Evaluator | PM | `{"application": stamp_record}` | Acceptance stamp: target application quality verified | None (stamp only) |

Each acceptance-stamp tool's `Command.PARENT` update dict includes the
`acceptance_stamps` key **in addition to** the standard `handoff_log` /
`current_agent` entries, so the audit trail and gate channel stay
synchronized.

**Acceptance gate logic for `return_product_to_pm`.** The middleware gate on
this tool reads `state["acceptance_stamps"]`:

- `state["acceptance_stamps"]["application"]` must be present AND
  `state["acceptance_stamps"]["application"]["accepted"] is True` (Evaluator
  stamp; always required). Presence alone is insufficient; rejected stamps
  (`accepted is False`) are written for auditability but never satisfy the gate.
- `state["acceptance_stamps"]["harness"]` must be present AND
  `state["acceptance_stamps"]["harness"]["accepted"] is True` if the HE
  participated in the project thread. HE participation is derived by
  scanning `state["handoff_log"]` for any record with
  `source_agent == "harness_engineer"` or
  `target_agent == "harness_engineer"`. If no HE participation is found,
  the HE acceptance check is skipped.
- Scanning `handoff_log` for acceptance records is an anti-pattern and
  must be rejected in review (conformance test: gate reads
  `acceptance_stamps`, never iterates `handoff_log` looking for
  `reason == "submit"` stamps).

This preserves the "no `has_target_harness` state key" decision while
decoupling gate logic from audit-log structure.

### 4.4 Stage Review — Specialist submits work to HE for eval coverage

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 13 | `submit_spec_to_harness_engineer` | `submit` | Architect | HE | Design spec → evalability review + dev-phase eval harness (Stage 2 intervention) | Spec accepted |
| 14 | `return_eval_coverage_to_architect` | `return` | HE | Architect | Eval coverage for new components + dev-phase eval criteria | None |

### 4.5 Phase Review — Developer submits phase deliverables for QA

The model-visible parameter remains named `phase` on these tools for Developer
usability, but the concrete definitions spec maps it to `plan_phase_id` in the
`HandoffRecord`. It is not the PCG lifecycle `current_phase`.

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 15 | `announce_phase_to_evaluator` | `announce` | Developer | Evaluator | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 16 | `announce_phase_to_harness_engineer` | `announce` | Developer | HE | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 17 | `submit_phase_to_evaluator` | `submit` | Developer | Evaluator | Phase deliverables → pass/fail findings, spec/plan compliance report | Deliverables match plan |
| 18 | `submit_phase_to_harness_engineer` | `submit` | Developer | HE | Phase deliverables → EBDR-1 feedback packet (eval science findings, no scoring logic leaked) | None |

### 4.6 Specialist Consultation — Non-ownership-transfer expert input

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 19 | `consult_harness_engineer_on_gates` | `consult` | Planner | HE | Plan draft → eval gate placement recommendations (Stage 3 intervention) | None |
| 20 | `consult_evaluator_on_gates` | `consult` | Planner | Evaluator | Plan draft → acceptance gate placement recommendations | None |
| 21 | `request_research_from_researcher` | `consult` | Architect, HE, PM | Researcher | Research question → targeted findings | None |
| 22 | `ask_pm` | `question` | Any specialist | PM | Stakeholder question → answer/clarification | None |
| 23 | `coordinate_qa` | `coordinate` | HE ↔ Evaluator | Evaluator ↔ HE | QA findings → aligned review strategy | None |

### 4.7 Terminal Emission — PM closes the project thread

This category contains exactly one tool. It is not a handoff between agents;
it is a lifecycle bookend that terminates the PCG graph with the PM's final
response to the user.

| # | Tool | Caller | Target | Emission Shape | Writes to `handoff_log`? |
|---|---|---|---|---|---|
| 24 | `finish_to_user` | PM | (user, via `messages` channel) | `Command(graph=Command.PARENT, goto=END, update={"messages": [AIMessage(final_response)]})` | **No** — terminal emission is a lifecycle bookend, not an inter-agent handoff. |

**When PM uses it.** After the PM has presented the finished product to the
user (via `ask_user` middleware) and received satisfaction confirmation — or
after any PM session-thread terminal conversation turn. `finish_to_user` is
not gated; the PM's system prompt decides when to invoke it.

**Why it's a separate tool, not a handoff.** `finish_to_user` does not
append to `handoff_log` because termination is not an event in the inter-
agent coordination audit trail. Including it in `handoff_log` would
pollute the audit with lifecycle bookends. It satisfies the §1.3
termination invariant and nothing else.

**Autonomous mode interaction.** When autonomous mode is enabled, the PM
still calls `finish_to_user` as the terminal action; autonomous mode only
suppresses the pre-terminal `ask_user` satisfaction check.

## 5. Agent-Scoped Tool Ownership

Each agent only receives the tools relevant to its role. An agent cannot call
a tool it does not own.

| Agent | Pipeline Delivery | Pipeline Return | Acceptance | Stage Review | Phase Review | Consultation |
|---|---|---|---|---|---|---|
| PM | `deliver_prd_to_harness_engineer`, `deliver_prd_to_researcher`, `deliver_design_package_to_architect`, `deliver_planning_package_to_planner`, `deliver_development_package_to_developer` | — | `submit_harness_acceptance` (receives), `submit_application_acceptance` (receives) | — | — | `request_research_from_researcher`; **Terminal:** `finish_to_user` (Category 7) |
| Harness Engineer | — | `return_eval_suite_to_pm`, `return_eval_coverage_to_architect` | `submit_harness_acceptance` | `submit_spec_to_harness_engineer` (receives) | `announce_phase_to_harness_engineer` (receives), `submit_phase_to_harness_engineer` (receives) | `consult_harness_engineer_on_gates` (receives), `request_research_from_researcher`, `coordinate_qa` |
| Researcher | — | `return_research_bundle_to_pm` | — | — | — | `request_research_from_researcher` (receives) |
| Architect | — | `return_design_package_to_pm` | — | `submit_spec_to_harness_engineer` | — | `request_research_from_researcher` |
| Planner | — | `return_plan_to_pm` | — | — | — | `consult_harness_engineer_on_gates`, `consult_evaluator_on_gates` |
| Developer | — | `return_product_to_pm` | — | — | `announce_phase_to_evaluator`, `announce_phase_to_harness_engineer`, `submit_phase_to_evaluator`, `submit_phase_to_harness_engineer` | `ask_pm` |
| Evaluator | — | — | `submit_application_acceptance` | — | `announce_phase_to_evaluator` (receives), `submit_phase_to_evaluator` (receives) | `consult_evaluator_on_gates` (receives), `coordinate_qa` |

## 6. Pipeline Flow Diagram

The pipeline progression flows through the PM as hub. Specialists return
completed work to the PM, who then delivers to the next specialist. Direct
specialist-to-specialist interactions exist for stage reviews and
consultations.

```txt
Stakeholder → PM
              │
              ├─ deliver_prd_to_harness_engineer ──→ HE (Stage 1)
              │     ← return_eval_suite_to_pm
              │
              ├─ deliver_prd_to_researcher ──→ Researcher
              │     ← return_research_bundle_to_pm
              │
              ├─ deliver_design_package_to_architect ──→ Architect
              │     │
              │     ├─ submit_spec_to_harness_engineer ──→ HE (Stage 2)
              │     │     ← return_eval_coverage_to_architect
              │     │
              │     ← return_design_package_to_pm
              │
              ├─ deliver_planning_package_to_planner ──→ Planner
              │     │
              │     ├─ consult_harness_engineer_on_gates (non-blocking)
              │     ├─ consult_evaluator_on_gates (non-blocking)
              │     │
              │     ← return_plan_to_pm
              │
              ├─ deliver_development_package_to_developer ──→ Developer
                    │
                    ├─ announce_phase_to_evaluator (non-blocking)
                    ├─ announce_phase_to_harness_engineer (non-blocking)
                    │
                    │  ... developer executes phase ...
                    │
                    ├─ submit_phase_to_evaluator ──→ Evaluator
                    ├─ submit_phase_to_harness_engineer ──→ HE
                    ├─ ask_pm (non-blocking)
                    │
                    ← phase deliverables
                    │
                    │  ... final phase complete ...
                    │
                    ├─ submit_application_acceptance ←── Evaluator (non-blocking stamp)
                    ├─ submit_harness_acceptance ←── HE (non-blocking stamp, conditional)
                    │
                    ├─ return_product_to_pm (gated by acceptance stamps)
                    │
              ← PM presents finished product to user
              PM uses ask_user → user satisfied → PM calls finish_to_user
              → Command(graph=PARENT, goto=END, update={messages: [AIMessage(final)]}) → END

Phase communication arc:
  1. Developer announces phase intent to each QA agent (non-blocking)
     "I'm starting phase N end-to-end, will meet these eval criteria"
     QA agents respond: "Agreed, awaiting your submission"
  2. Developer executes the phase
  3. Developer submits phase deliverables to each QA agent (blocking)
     Cannot proceed to next phase without feedback

Core evaluation loops (blocking — developer cannot proceed without feedback):
  Developer ──submit_phase_to_evaluator──→ Evaluator
       ← pass/fail findings, spec/plan compliance report
  Developer ──submit_phase_to_harness_engineer──→ HE
       ← EBDR-1 feedback packet (directional signal, no scoring logic leaked)

  Both loops enforce information isolation:
  - Evaluator: validates code against spec/plan, hard fails/passes phases
  - HE: runs eval science, produces EBDR-1 feedback that gives the optimizer
    directional signal without exposing rubrics, judge configs, or held-out data
  - Developer is completely blind to evaluation artifacts — only sees feedback
    packets and can inspect its own traces in LangSmith

Specialist loops (non-blocking):
  Architect ↔ Researcher  (request_research_from_researcher)
  HE ↔ Evaluator          (coordinate_qa)
  Any specialist → PM      (ask_pm)
```
