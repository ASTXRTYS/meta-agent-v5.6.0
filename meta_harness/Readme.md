

# Meta Harness v2

### Peer-to-Peer Multi-Agent Pipeline for Building AI Applications

`ADR-001` · `Status: Proposed` · `Risk: Medium` · `Impact: High`

[Deep Agents SDK](https://pypi.org/project/deepagents/)
[LangGraph](https://github.com/langchain-ai/langgraph)
[LangSmith](https://smith.langchain.com)
[Python](https://python.org)



---

## Architecture Diagram

> **[Open in Excalidraw](https://excalidraw.com/#json=4bcuKO8RtUas_BAnIw_eJ,3JUUbBs5wIIZzx-DsiC0lw)** — interactive pan/zoom with full detail

Project Coordination Graph

**📐 Diagram legend**


| Visual                     | Meaning                                                                          |
| -------------------------- | -------------------------------------------------------------------------------- |
| **Blue solid arrow** `→`   | Pipeline Delivery — PM delivers artifact package to start a stage (blocking)     |
| **Amber solid arrow** `→`  | Pipeline Return — Specialist returns completed work to PM (blocking)             |
| **Purple solid arrow** `→` | Stage Review / Submit — Work submitted for review or evaluation (blocking)       |
| **Green dashed arrow** `⇢` | Consultation — Expert input without ownership transfer (non-blocking)            |
| **Pink dashed arrow** `⇢`  | Announce — Intent/heads-up pushed without expecting a deliverable (non-blocking) |
| **Red solid arrow** `→`    | EBDR-1 / Eval Feedback Loop — Scientific evaluation feedback                     |
| **Amber square** `■`       | Middleware Phase Gate — Enforced before handoff passes to PCG                    |




---

## What Is This?

Meta Harness takes a product idea from initial concept through to a **fully built, tested, and evaluated AI application**. It orchestrates a pipeline of seven specialized Deep Agents — from requirements gathering through research, architecture, planning, implementation, and evaluation — with a built-in **optimizer-evaluator feedback loop** that enforces scientific rigor throughout development.

### What Changed from v1 → v2


| Dimension            | v1                                                                  | v2                                                                   |
| -------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Topology**         | PM owns all specialists as subagents                                | Peer Deep Agent child graphs under a thin LangGraph PCG              |
| **Routing**          | PM mediates every handoff                                           | Agents route themselves via handoff tool selection; PCG plumbs       |
| **State**            | Shared PM context window                                            | Per-role checkpoint namespaces under one project thread              |
| **Phase Gates**      | Implicit in PM logic                                                | Explicit middleware hooks on handoff tools                           |
| **Specialist Loops** | PM as pass-through                                                  | Direct peer-to-peer (Architect↔Researcher, Developer↔HE, etc.)       |
| **Agent Count**      | 7 (PM, HE, Researcher, Architect, Planner, Developer, Verification) | 7 (PM, HE, Researcher, Architect, Planner, Developer, **Evaluator**) |
| **Handoff Protocol** | Implicit context passing                                            | 20 explicit handoff tools with `reason` enum and middleware gates    |


> **Core insight:** If agents are LLMs making conscious decisions about peer communication, routing should live *in the agents*, not in a coordination layer. The coordination layer is plumbing, not a brain.

---

## Guiding Principles


|     |
| --- |
|     |


### 🎯 PM Scopes Criteria, HE Owns the Science

The **PM** is a business-oriented project manager. It translates stakeholder vision into clear requirements and evaluation criteria — defining **WHAT** success looks like.

The **Harness Engineer** is the scientific authority on evaluation. It owns **HOW** to evaluate: scoring rubrics, LLM judge assembly, calibration methodology, and harness topology.



### 🔒 Information Isolation Is Non-Negotiable

The optimizer-evaluator feedback loop only works if **information asymmetry is maintained**. The Developer must remain blind to evaluation artifacts to prevent reward hacking and overfitting.

The Developer sees EBDR-1 feedback packets and its own LangSmith traces. It never sees rubrics, judge configs, or held-out datasets.



---

## Agent Roster

> Each agent is a full `create_deep_agent()` graph with its own prompt, tools, memory, skills, and checkpoint namespace.

### Project Manager (PM) — *Pipeline Hub*


|                 |                                                                          |
| --------------- | ------------------------------------------------------------------------ |
| **Identity**    | Business-oriented orchestrator and requirements owner                    |
| **Owns**        | PRD, eval criteria scoping, artifact organization, stakeholder alignment |
| **Delivers to** | HE, Researcher, Architect, Planner, Developer                            |
| **Namespace**   | `checkpoint_ns = "project_manager"`                                      |


The PM is the **hub** of the pipeline. Specialists return completed work to the PM, and the PM delivers consolidated packages to the next specialist. The PM never performs research, architecture, planning, coding, or evaluation — it coordinates.

---

### Harness Engineer (HE) — *Eval Science Authority*


|                         |                                                                      |
| ----------------------- | -------------------------------------------------------------------- |
| **Identity**            | Scientific iterator, LLM judge authority, phase-gate enforcer        |
| **Owns**                | Rubrics, LLM judges, calibration, held-out datasets, EBDR-1 feedback |
| **Intervention Points** | Stage 1 (PRD), Stage 2 (Spec), Stage 3 (Plan), Dev Loop (EBDR-1)     |
| **Namespace**           | `checkpoint_ns = "harness_engineer"`                                 |


**HE Intervention Stages**

**Stage 1 — PRD Finalization**

- Refine PM's proposed evaluation criteria into a complete evaluation harness
- Determine eval types: binary, binary score, Likert, categories
- Define judge strategy: count, scope, model selection, prompt writing, scoring schema
- Create full synthetic dataset (building on PM's initial examples)
- Calibrate each judge against synthetic data
- **Gate:** PRD cannot be finalized until eval harness is complete and all judges are calibrated

**Stage 2 — Spec Evaluation Coverage**

- Create eval coverage for new components introduced by the Architect
- System prompts, tools, programmatic behaviors, middleware
- Ensure the Developer can effectively hill-climb against new components
- **Gate:** Spec cannot flow to Planner until eval coverage exists for all architect-introduced components

**Stage 3 — Gate Placement**

- Dictate where evaluation gates belong in the development plan
- Create parallel eval plan: which evals run after which dev phases
- Set phase-gate criteria that must be met before progressing



---

### Researcher — *Deep Ecosystem Research*


|                |                                                             |
| -------------- | ----------------------------------------------------------- |
| **Identity**   | Multi-pass web researcher and evidence synthesizer          |
| **Owns**       | SDK/API discovery, decision-space mapping, evidence bundles |
| **Returns to** | PM (research bundle)                                        |
| **Namespace**  | `checkpoint_ns = "researcher"`                              |


May loop with the Architect via `request_research_from_researcher` when further discovery is needed to inform technical decisions.

---

### Architect — *System Design + Spec*


|                |                                                                  |
| -------------- | ---------------------------------------------------------------- |
| **Identity**   | System architect and technical specification author              |
| **Owns**       | Design spec, tool schemas, system prompts, component definitions |
| **Loops with** | Researcher (discovery), HE (Stage 2 eval coverage)               |
| **Namespace**  | `checkpoint_ns = "architect"`                                    |


Introduces new components that didn't exist at PRD time — triggering HE Stage 2 intervention for evaluation coverage.

---

### Planner — *Implementation Strategy*


|               |                                                      |
| ------------- | ---------------------------------------------------- |
| **Identity**  | Implementation strategist                            |
| **Owns**      | Phased implementation plan with eval break points    |
| **Consults**  | HE (gate placement), Evaluator (acceptance criteria) |
| **Namespace** | `checkpoint_ns = "planner"`                          |


The plan marks *when* to evaluate, never *what* or *how*. Eval criteria are invisible to the Planner beyond the public subset.

---

### Developer — *The Optimizer*


|                |                                              |
| -------------- | -------------------------------------------- |
| **Identity**   | Hill-climbing implementation engineer        |
| **Owns**       | Phase deliverables: code, prompts, tools, UI |
| **Submits to** | Evaluator (pass/fail), HE (EBDR-1 feedback)  |
| **Namespace**  | `checkpoint_ns = "developer"`                |


Works phase-by-phase against the plan. **Completely blind to evaluation artifacts** — only sees EBDR-1 feedback packets and can inspect its own traces in LangSmith.

---

### Evaluator — *Acceptance + Compliance*


|                      |                                                                     |
| -------------------- | ------------------------------------------------------------------- |
| **Identity**         | Acceptance gatekeeper and spec compliance checker                   |
| **Owns**             | Pass/fail findings, spec/plan compliance reports, phase advancement |
| **Coordinates with** | HE (via `coordinate_qa`)                                            |
| **Namespace**        | `checkpoint_ns = "evaluator"`                                       |


Validates code against spec and plan. Issues hard pass/fail decisions on phase deliverables. Does not own eval science — that's HE's domain.

---

## Information Isolation Matrix

> This is architecturally critical. The optimizer-evaluator loop only works if information asymmetry is maintained.


| Artifact                     | PM  | HE  | Researcher | Architect | Planner | Developer | Evaluator |
| ---------------------------- | --- | --- | ---------- | --------- | ------- | --------- | --------- |
| PRD + requirements           | ✅   | ✅   | ✅          | ✅         | ✅       | ✅         | ✅         |
| Evaluation criteria (public) | ✅   | ✅   | ✅          | ✅         | ✅       | ✅         | ✅         |
| Scoring rubrics              | ❌   | ✅   | ❌          | ❌         | ❌       | ❌         | ❌         |
| LLM judge configs            | ❌   | ✅   | ❌          | ❌         | ❌       | ❌         | ❌         |
| Held-out eval datasets       | ❌   | ✅   | ❌          | ❌         | ❌       | ❌         | ❌         |
| Development plan             | ✅   | ✅   | ❌          | ✅         | ✅       | ✅         | ✅         |
| EBDR-1 feedback packets      | ❌   | ✅   | ❌          | ❌         | ❌       | ✅         | ❌         |
| Raw traces (LangSmith)       | ❌   | ❌   | ❌          | ❌         | ❌       | ✅         | ❌         |


---

## Handoff Protocol

All agent-to-agent communication goes through explicit handoff tools. A handoff tool returns `Command(graph=Command.PARENT, goto="process_handoff", update=<payload>)` — the PCG records the handoff and invokes the target agent.

### Naming Convention

```
<verb>_<artifact|phase>_package_to_<role>
```

The tool name reads as a sentence: `deliver_prd_to_harness_engineer`, `submit_phase_to_evaluator`, `consult_harness_engineer_on_gates`.

### Verb Semantics


| Verb         | Blocking? | Meaning                                               |
| ------------ | --------- | ----------------------------------------------------- |
| `deliver`    | ✅         | Caller hands off ownership of a pipeline stage        |
| `return`     | ✅         | Specialist returns completed work                     |
| `submit`     | ✅         | Caller submits work for review or evaluation          |
| `consult`    | ❌         | Request expert input without transferring ownership   |
| `announce`   | ❌         | Push intent or heads-up; no deliverable expected back |
| `ask`        | ❌         | Ask a question                                        |
| `coordinate` | ❌         | QA agents align with each other                       |


### Handoff Record Schema

Every handoff is recorded in PCG state:

```python
# Calling agent populates:
project_id: str          # doubles as root thread_id
source_agent: AgentEnum  # project-manager | harness-engineer | researcher | ...
target_agent: AgentEnum  # same enum
reason: ReasonEnum       # deliver | return | submit | consult | announce | coordinate | question
brief: str               # prose summary for the receiving agent
artifact_paths: list     # filesystem paths to artifacts (references, not copies)

# PCG fills in:
handoff_id: str          # unique identifier
langsmith_run_id: str    # trace correlation
status: StatusEnum       # queued | running | completed | failed
created_at: str          # RFC3339 timestamp
```

Middleware dispatches on the `(source_agent, target_agent, reason)` triple to determine which gate logic to apply.

---

## The 20 Handoff Tools

**Pipeline Delivery** — PM delivers artifact to start a stage (5 tools)


| #   | Tool                                       | Target     | Artifact Flow                                  | Gate                |
| --- | ------------------------------------------ | ---------- | ---------------------------------------------- | ------------------- |
| 1   | `deliver_prd_to_harness_engineer`          | HE         | PRD + eval criteria + datasets → eval harness  | PRD finalized       |
| 2   | `deliver_prd_to_researcher`                | Researcher | PRD + eval criteria → research bundle          | HE Stage 1 complete |
| 3   | `deliver_design_package_to_architect`      | Architect  | PRD + eval suite + research → design spec      | Research complete   |
| 4   | `deliver_planning_package_to_planner`      | Planner    | Design spec + public eval → impl plan          | HE Stage 2 complete |
| 5   | `deliver_development_package_to_developer` | Developer  | Plan + spec + public eval + PRD → deliverables | Plan accepted       |




**Pipeline Return** — Specialist returns completed work to PM (4 tools)


| #   | Tool                           | Caller     | Artifact Flow                                     |
| --- | ------------------------------ | ---------- | ------------------------------------------------- |
| 6   | `return_eval_suite_to_pm`      | HE         | Refined eval criteria + rubrics + public datasets |
| 7   | `return_research_bundle_to_pm` | Researcher | Research bundle with findings and refs            |
| 8   | `return_design_package_to_pm`  | Architect  | Design spec + tool schemas + prompts              |
| 9   | `return_plan_to_pm`            | Planner    | Phased plan with eval break points                |




**Stage Review** — Specialist submits work to HE for eval coverage (2 tools)


| #   | Tool                                | Caller → Target | Artifact Flow                       |
| --- | ----------------------------------- | --------------- | ----------------------------------- |
| 10  | `submit_spec_to_harness_engineer`   | Architect → HE  | Design spec → Stage 2 eval coverage |
| 11  | `return_eval_coverage_to_architect` | HE → Architect  | Eval coverage for new components    |




**Phase Review** — Developer submits deliverables for QA (4 tools)


| #   | Tool                                 | Target    | Artifact Flow                                |
| --- | ------------------------------------ | --------- | -------------------------------------------- |
| 12  | `announce_phase_to_evaluator`        | Evaluator | Phase intent → "agreed, awaiting submission" |
| 13  | `announce_phase_to_harness_engineer` | HE        | Phase intent → "agreed, awaiting submission" |
| 14  | `submit_phase_to_evaluator`          | Evaluator | Deliverables → pass/fail findings            |
| 15  | `submit_phase_to_harness_engineer`   | HE        | Deliverables → EBDR-1 feedback packet        |




**Specialist Consultation** — Non-blocking expert input (5 tools)


| #   | Tool                                | Caller(s)         | Target         |
| --- | ----------------------------------- | ----------------- | -------------- |
| 16  | `consult_harness_engineer_on_gates` | Planner           | HE             |
| 17  | `consult_evaluator_on_gates`        | Planner           | Evaluator      |
| 18  | `request_research_from_researcher`  | Architect, HE, PM | Researcher     |
| 19  | `ask_pm`                            | Any specialist    | PM             |
| 20  | `coordinate_qa`                     | HE ↔ Evaluator    | HE ↔ Evaluator |




---

## The Development Loop

The core of the system: the **optimizer-evaluator feedback cycle** that repeats for each phase in the plan.

```
┌─────────────────────────────────────────────────────────┐
│                Development Phase Loop                    │
│                                                         │
│   ┌──────────┐   submit    ┌───────────┐               │
│   │Developer │ ──────────→ │ Evaluator │               │
│   │(Optimizer)│ ←────────── │ Pass/Fail │               │
│   │          │   findings   └───────────┘               │
│   │          │                                          │
│   │          │   submit    ┌───────────┐               │
│   │          │ ──────────→ │ Harness   │               │
│   │          │ ←────────── │ Engineer  │               │
│   │          │   EBDR-1    │           │               │
│   └──────────┘             └───────────┘               │
│        │                                                │
│        └── iterate until phase gate passes ──→ next    │
│                                                         │
│   ⚠️  Developer is BLIND to eval artifacts              │
└─────────────────────────────────────────────────────────┘
```

### Phase Communication Arc

1. **Announce** — Developer announces phase intent to Evaluator and HE (non-blocking)
  > *"I'm starting phase N, will meet these eval criteria"*
  > QA agents respond: *"Agreed, awaiting your submission"*
2. **Execute** — Developer implements the phase
3. **Submit** — Developer submits phase deliverables to both QA agents (blocking)
4. **Feedback** — Developer receives findings from Evaluator + EBDR-1 from HE
5. **Iterate** — Loop continues until both gates pass
6. **Advance** — Move to next phase

### Developer Routing Guide


| Route to             | When                                                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Harness Engineer** | Phase fails because eval harness, metric, judge, dataset, calibration, or measurement strategy needs expert review |
| **Evaluator**        | Phase needs implementation review, UX verification, design conformance, or hard pass/fail against the plan         |
| **PM**               | Question changes requirements, success criteria, user-facing behavior, or business priority                        |


---

## Project Coordination Graph (PCG)

The PCG is the **thin LangGraph orchestration layer** — plumbing, not a brain.

### 3-Node Linear Topology

```
START → receive_user_input → run_agent(PM)
                                  │
                            Agent calls handoff tool
                            Middleware gate fires
                                  │
                            Gate passes → Command.PARENT
                            Gate fails  → revision prompt to agent
                                  │
                            process_handoff → run_agent(target)
                                  │
                            target calls handoff or returns
                                  │
                            process_handoff → run_agent(next)  ← loop
```


| Node                 | Purpose                                                     |
| -------------------- | ----------------------------------------------------------- |
| `receive_user_input` | Accept stakeholder input, write to state for PM             |
| `process_handoff`    | Record handoff, ensure target namespace, prepare payload    |
| `run_agent`          | Invoke target mounted Deep Agent under its stable namespace |


**No conditional edges.** The only branching happens *before* `Command.PARENT` reaches the PCG: the middleware hook on the handoff tool decides whether to allow the handoff or return a revision prompt. If the command reaches the PCG, it always flows through `process_handoff` → `run_agent`.

### Phase Gate Middleware

Phase gates are **middleware hooks on handoff tools**, not PCG nodes or conditional edges:

1. Inspect `(source_agent, target_agent, reason, artifact_paths)`
2. Check prerequisites (PRD finalized? Spec approved? Deliverables match plan?)
3. **Pass** → allow `Command.PARENT` through to PCG
4. **Fail** → return revision prompt to calling agent; agent reflects, revises, re-attempts

New phase gates = middleware additions, not PCG topology changes.

---

## Observability

### LangSmith Tracing

Every PCG handoff and Deep Agent invocation is searchable by:


| Field        | Scope                                             |
| ------------ | ------------------------------------------------- |
| `project_id` | Set once at PCG init                              |
| `agent_name` | Auto-propagated via `create_deep_agent(name=...)` |
| `thread_id`  | Set once at PCG init                              |
| `handoff_id` | Handoff-scoped, in handoff records                |
| `phase`      | Handoff-scoped, in handoff records                |
| `from_agent` | Handoff-scoped, in handoff records                |
| `to_agent`   | Handoff-scoped, in handoff records                |


### LangGraph Studio

Local development inspection via `langgraph dev` — graph behavior, thread state, checkpoint namespaces, routing visibility.

### Environment Setup

```bash
# .env
LANGSMITH_API_KEY=<key>
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=meta-harness
LANGCHAIN_CALLBACKS_BACKGROUND=false
```

---

## Project Structure

```
meta-harness/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── AD.md
├── langgraph.json
├── graph.py                          # PCG entrypoint: make_graph() → CompiledStateGraph
├── docs/
│   ├── architecture/
│   └── specs/
├── src/
│   └── meta_harness/
│       ├── __init__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── catalog.py            # single source of truth for role identity
│       │   ├── project_manager/
│       │   │   ├── agent.py          # create_deep_agent(name="project-manager", ...)
│       │   │   └── system_prompt.md
│       │   ├── harness_engineer/
│       │   ├── researcher/
│       │   ├── architect/
│       │   ├── planner/
│       │   ├── developer/
│       │   └── evaluator/
│       ├── integrations/
│       │   ├── sandbox_factory.py    # follows deepagents_cli.integrations convention
│       │   └── sandbox_provider.py
│       └── tools/
└── tests/
    ├── contract/                     # fast invariant tests — no I/O
    ├── integration/                  # app composition tests
    └── eval/                         # live behavioral tests
```

---

## Quick Reference

### Tech Stack


| Layer               | Technology                                                                          |
| ------------------- | ----------------------------------------------------------------------------------- |
| **Agent Framework** | [Deep Agents SDK](https://pypi.org/project/deepagents/) ≥ 0.4.3                     |
| **Orchestration**   | [LangGraph](https://github.com/langchain-ai/langgraph) ≥ 1.0                        |
| **Observability**   | [LangSmith](https://smith.langchain.com)                                            |
| **Local Dev**       | [LangGraph Studio](https://docs.langchain.com/langgraph-studio) via `langgraph dev` |
| **Models**          | Anthropic Claude (via `langchain-anthropic`), OpenAI (via `langchain-openai`)       |
| **Persistence**     | SQLite checkpointer (`langgraph-checkpoint-sqlite`)                                 |
| **Runtime**         | Python ≥ 3.11                                                                       |


### Key Concepts Glossary


| Term                      | Definition                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------- |
| **PCG**                   | Project Coordination Graph — the thin LangGraph orchestration layer                 |
| **EBDR-1**                | Evaluator Behavioral Diagnostic Report — directional feedback without scoring logic |
| **Handoff**               | Explicit tool call returning `Command.PARENT` with structured payload               |
| **Phase Gate**            | Middleware hook that enforces prerequisites before a handoff passes                 |
| **Checkpoint Namespace**  | Per-role state isolation under one project thread                                   |
| **Information Isolation** | Architectural constraint: Developer cannot see eval artifacts                       |
| **Pipeline Hub**          | PM role — specialists return to PM, PM delivers to next specialist                  |


---

## Historical Context

This project evolved from the **Long Horizon Meta Harness v1**, which used the PM as the container for all specialist cognition. The v1 architecture is documented in the [original Readme](../Readme.md) and its [diagram](../Harness-Diagram.png).

Key evolution drivers:

- **State isolation** — specialists needed their own checkpoint history, not shared PM context
- **Peer communication** — direct Architect↔Researcher loops without PM pass-through
- **Observable handoffs** — explicit tool calls with structured records, not implicit context passing
- **Middleware extensibility** — new gates as middleware hooks, not topology changes
- **Evaluation separation** — Evaluator role split from HE to separate acceptance testing from eval science

---



*Built with [Deep Agents SDK](https://pypi.org/project/deepagents/) · Orchestrated by [LangGraph](https://github.com/langchain-ai/langgraph) · Traced by [LangSmith*](https://smith.langchain.com)

