# Architecture Decision Record

> [!TIP]
> Keep this doc concise, factual, and testable. If a claim cannot be verified, add a validation step.

---

## 0) Header

| Field | Value |
|---|---|
| ADR ID | `ADR-001` |
| Title | `Meta Harness Architecture` |
| Status | `Proposed` |
| Date | `2025-10-15` |
| Author(s) | `@Jason` |
| Reviewers | `@Jason` |
| Related PRs | `#NA`, `#NA` |
| Related Docs | `[Requirements Scratch](./tmp.md)`, `[SME Transcript](./SME.md)` |

**One-liner:** `Meta Harness Architecture`

---

## 1) Decision Snapshot

```txt
We will model the PM, Harness Engineer, Researcher, Architect, Planner,
Developer, and Evaluator as peer, stateful Deep Agent graphs mounted under a thin
LangGraph Project Coordination Graph. The Project Coordination Graph owns the
project thread, parent-mediated handoff routing, run status, and phase gates. The
Deep Agent graphs own role-specific cognition, tools, memory, skills,
summarization, artifact work, and private role state through child graph
checkpoint namespaces.
```

### Decision Badge

`Status: Proposed` · `Risk: Medium` · `Impact: High`

---

## 2) Context

### Problem Statement

<What problem are we solving, for whom, and why now?>

### Constraints

- `<constraint 1>`
- `<constraint 2>`
- `<constraint 3>`

### Non-Goals

- [ ] `<Deployment at scale>`
- [ ] `<Threat modeling and security hardening>`
- [ ] `<Full web application deployment>` **[This-wll-flip-very-soon]**

---

## 3) Options Considered

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | PM owns core roles as declarative `SubAgent` dict specs | Lowest initial wiring; uses SDK-provided `task` tool | `task` subagent calls are explicitly ephemeral and stateless; specialists cannot reliably resume project-specific trajectory | `Rejected` |
| B | PM owns core roles as `CompiledSubAgent` runnables | Can wrap full `create_deep_agent()` graphs | Stock `task` invocation passes only synthesized state, not a stable `thread_id` config; persistence would require a wrapper outside the first-class path | `Rejected as primary topology` |
| C | PM uses stock `AsyncSubAgent` for each specialist | Supports remote/background execution, status checks, and follow-up updates on the same task thread | `start_async_task` creates a new remote thread each time; not enough by itself for mounted project-role identity | `Use only for ad hoc background tasks` |
| D | Peer `create_deep_agent()` graphs mounted under a thin LangGraph Project Coordination Graph | Preserves per-agent state, permits direct specialist loops, keeps cognition inside Deep Agents, and makes handoffs observable | Requires a small deterministic coordination layer and project thread / role namespace registry | `Selected` |

<details>
<summary><strong>Decision rationale notes</strong> (expand)</summary>

### Why selected option wins

1. It matches the SDK boundary: `create_deep_agent()` already assembles the agent harness and accepts `checkpointer`, `store`, `backend`, `memory`, `skills`, `subagents`, and `name`.
2. It gives every core role stable project-scoped state and its own checkpoint history, rather than forcing PM to carry or restate specialist context.
3. It keeps LangGraph focused on deterministic coordination, not role cognition.

### Why alternatives lose

- Option A: Declarative `SubAgent` specs are for isolated tasks, not durable project roles.
- Option B: `CompiledSubAgent` is a useful escape hatch, but the stock `task` tool does not provide the stable runtime config required for project-scoped checkpoint resume.
- Option C: Stock `AsyncSubAgent` is useful for background execution, but it is
  not the core project-role topology because it launches generated remote task
  threads rather than mounted role graphs under the Project Coordination Graph.

</details>

---

## 4) Architecture

### Runtime Topology Decision

The core topology is:

```txt
Human/UI
  -> LangGraph Project Coordination Graph
      -> PM Deep Agent child graph
      -> Harness Engineer Deep Agent child graph
      -> Researcher Deep Agent child graph
      -> Architect Deep Agent child graph
      -> Planner Deep Agent child graph
      -> Developer Deep Agent child graph
      -> Evaluator Deep Agent child graph
```

The Project Coordination Graph is the LangGraph application entrypoint. The PM is
still the default user-facing agent and scope owner, but it is not the container
for all specialist cognition. The PM and specialists are peer Deep Agent child
graphs. Each role must be assembled by its own `create_deep_agent()` factory with
`name=` set for trace metadata, its own tool ownership, its own prompt, its own
memory sources, and its own child graph state.

For local mounted-graph execution, use one stable root thread per project:

```txt
thread_id = "{project_id}"
```

Role isolation is provided by child graph state schemas and stable checkpoint
namespaces under that project thread:

```txt
checkpoint_ns = ""                         # Project Coordination Graph state
checkpoint_ns = "project_manager"          # PM role state
checkpoint_ns = "harness_engineer"         # Harness Engineer role state
checkpoint_ns = "researcher"               # Researcher role state
checkpoint_ns = "architect"                # Architect role state
checkpoint_ns = "planner"                  # Planner role state
checkpoint_ns = "developer"                # Developer role state
checkpoint_ns = "evaluator"                # Evaluator role state
```

The exact namespace strings can change during implementation, but the invariant
cannot: re-invoking the Harness Engineer for the same project must resume the
Harness Engineer's role state, not the PM state and not a fresh ephemeral
subagent task.

### LangGraph Project Coordination Graph

The Project Coordination Graph is the thin LangGraph orchestration layer around
the Deep Agent harnesses. It should not replace the harness.

Committed naming decision: use `Project Coordination Graph` for this layer and
`ProjectCoordination*` for its concrete schemas, such as
`ProjectCoordinationState`, `ProjectCoordinationContext`,
`ProjectCoordinationInput`, and `ProjectCoordinationOutput`. Do not use bare
`ProjectState` or `ProjectContext` for this graph; those names imply ownership of
the full project domain state and would blur the boundary between deterministic
routing state, project artifacts, project memory, and agent cognition.

Its responsibilities are:

- Accept the handoff command from a Deep Agent tool via `Command.PARENT`.
- Record the handoff in Project Coordination Graph state.
- Invoke the target mounted Deep Agent child graph under its stable role namespace.
- Preserve enough Project Coordination Graph state to reconstruct which agent handed work
  to whom, why, and with which artifact references.

Phase gate enforcement and HITL question surfacing are **not** PCG responsibilities.
They are handled by middleware hooks on the handoff tools (see Handoff Protocol below).

Its non-responsibilities are equally important:

- Do not implement research, architecture, planning, coding, or evaluation logic in LangGraph nodes.
- Do not put all specialist messages into one shared graph state.
- Do not use the PM as a pass-through for every specialist-to-specialist loop.
- Do not reimplement Deep Agents middleware for planning, memory, skills, filesystem access, summarization, or tool calling.
- Do not implement phase gate logic in PCG nodes or conditional edges — phase gates are middleware hooks on handoff tools.
- Do not implement routing intelligence — the calling agent chooses its target via the handoff tool; the PCG is plumbing, not a router.

| Node | Purpose |
|---|---|
| `receive_user_input` | Accept new stakeholder input and write it into state for the PM. |
| `process_handoff` | Record the handoff, ensure the target role's checkpoint namespace and workspace paths are initialized, and prepare the invocation payload. |
| `run_agent` | Invoke the target mounted Deep Agent child graph under its stable role namespace. |

The topology is linear:

```txt
START → receive_user_input → run_agent(PM)
                                    │
                              PM calls handoff tool
                              middleware hook fires (phase gate)
                                    │
                              gate passes → Command.PARENT emitted
                              gate fails → tool returns revision prompt to agent
                                    │
                              process_handoff → run_agent(target)
                                    │
                              target calls handoff or returns
                                    │
                              process_handoff → run_agent(next target)  (loop)
```

There are no conditional edges. The only branching happens *before* the
`Command.PARENT` reaches the PCG: the middleware hook on the handoff tool
decides whether to allow the handoff through or return a revision prompt to
the calling agent. If the command reaches the PCG, it always flows through
`process_handoff` → `run_agent`.

### Handoff Protocol

All agent-to-agent communication goes through explicit handoff tools. A handoff
tool returns `Command(graph=Command.PARENT, goto="process_handoff",
update=<handoff_payload>)` rather than directly invoking arbitrary peers. The
PCG records the handoff and invokes the target mounted role graph.

A handoff should carry:

- `project_id`
- `source_agent`
- `target_agent`
- `reason` (enum: `deliver | return | submit | consult | announce | coordinate | question`)
- `brief` (prose summary for the receiving agent)
- `artifact_paths`

The `reason` enum encodes the *type of transition*, not the pipeline phase.
Middleware dispatches on the `(source_agent, target_agent, reason)` triple to
determine which gate logic to apply. For example, `(PM, HE, deliver)` triggers
the Stage 1 PRD-finalized gate, while `(Architect, HE, submit)` triggers the
Stage 2 spec-acceptance gate.

The receiving agent gets a concise brief plus artifact paths, not a dump of the
caller's full conversation. The receiving agent resumes its own role state and
decides what context to load.

Artifact paths are references by default — the receiving agent reads artifacts
from the caller's namespace via the provided paths. Each agent owns its own
filesystem namespace and tags its artifacts with the `project_id`.

**Exception: PM-assembled handoff packages.** For downstream pipeline delivery
tools where the receiving agent needs the full accumulated artifact set, the PM
assembles a consolidated project handoff package — a directory that gets copied
into the receiving agent's filesystem. The receiving agent then owns and organizes
that copy. This applies to:

- `deliver_spec_to_planner` — Planner receives an organized package of design spec,
  public eval criteria, and public datasets.
- `deliver_plan_to_developer` — Developer receives the full project package: plan,
  spec, public eval, PRD, and research highlights. The Developer organizes this
  into a structured filesystem layout optimized for implementation and human
  readability.

Early-stage deliveries (`deliver_prd_to_harness_engineer`,
`deliver_prd_to_researcher`, `deliver_prd_to_architect`) remain as references
because those specialists only need a few specific artifacts from the PM's
already-organized namespace. The PM's role as organizer aligns with its identity
as the business-oriented project manager who ensures artifacts are properly
stored and structured before they flow downstream.

### Phase Gate Middleware

Phase gate enforcement is a middleware hook on each handoff tool, not a PCG node
or conditional edge. When an agent calls a handoff tool, the middleware hook
fires before the `Command.PARENT` is emitted:

1. Inspect the handoff tool call (`source_agent`, `target_agent`, `reason`,
   `artifact_paths`).
2. Check phase prerequisites (e.g., PRD finalized before `(PM, HE, deliver)`;
   spec approved before `(Architect, HE, submit)`;
   deliverables match plan before `(Developer, Evaluator, submit)`).
3. Gate passes → allow the `Command.PARENT` through to the PCG.
4. Gate fails → return a revision/validation prompt to the calling agent instead
   of the command. The agent reflects, revises, and re-attempts.

This keeps the PCG topology linear (no conditional edges) and makes gate logic
extensible: new phase gates are middleware additions, not PCG topology changes.
Different agents can have different gate middleware — the `(PM, HE, deliver)`
gate checks different things than the `(Architect, HE, submit)` gate. The
`(source_agent, target_agent, reason)` triple tells the middleware which gate
logic to apply.

#### Handoff Tool Use-Case Matrix

Tools are organized into four categories by transition type. The naming
convention is `<verb>_<artifact|phase>_package_to_<role>`: the tool name reads
as a sentence that tells both the calling agent and any maintainer exactly what
is flowing where. Single-artifact deliveries use the artifact name
(e.g. `deliver_prd_to_harness_engineer`); composite package deliveries use the
phase name plus `package` (e.g. `deliver_design_package_to_architect`) to signal
that the PM is handing off a consolidated bundle of accumulated artifacts.

Verb semantics also encode blocking behavior:
- **`deliver`** = the caller is handing off ownership of a pipeline stage (blocking)
- **`return`** = the specialist is returning completed work to the PM or calling specialist (blocking)
- **`submit`** = the caller is submitting work for review or evaluation (blocking)
- **`consult`** = the caller is requesting expert input without transferring ownership (non-blocking)
- **`announce`** = the caller is pushing intent or a heads-up without expecting a deliverable back (non-blocking)
- **`ask`** = the caller is asking a question (non-blocking)
- **`coordinate`** = QA agents are aligning with each other (non-blocking)

**Pipeline Delivery** — PM delivers artifact to start a pipeline stage:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 1 | `deliver_prd_to_harness_engineer` | `deliver` | PM | HE | PRD + proposed eval criteria + business-logic datasets → refined eval criteria, rubrics, public/held-out datasets, calibrated judges | Stage 1: PRD finalized |
| 2 | `deliver_prd_to_researcher` | `deliver` | PM | Researcher | PRD + refined eval criteria + public datasets → research bundle | HE Stage 1 complete |
| 3 | `deliver_design_package_to_architect` | `deliver` | PM | Architect | PRD + eval suite + research bundle → design spec | Research complete |
| 4 | `deliver_planning_package_to_planner` | `deliver` | PM | Planner | Design spec + public eval criteria + public datasets → implementation plan | HE Stage 2 complete |
| 5 | `deliver_development_package_to_developer` | `deliver` | PM | Developer | Plan + spec + public eval + PRD → phase deliverables | Plan accepted |

**Pipeline Return** — Specialist returns completed work to PM:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 6 | `return_eval_suite_to_pm` | `return` | HE | PM | Refined eval criteria + rubrics + public datasets (HE retains held-out datasets + copies in its own filesystem) | None |
| 7 | `return_research_bundle_to_pm` | `return` | Researcher | PM | Research bundle with findings and refs | None |
| 8 | `return_design_package_to_pm` | `return` | Architect | PM | Design spec + tool schemas + system prompts | None |
| 9 | `return_plan_to_pm` | `return` | Planner | PM | Phased implementation plan with eval break points | None |

**Stage Review** — Specialist submits work to HE for eval coverage:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 10 | `submit_spec_to_harness_engineer` | `submit` | Architect | HE | Design spec → evalability review + dev-phase eval harness (Stage 2 intervention) | Spec accepted |
| 11 | `return_eval_coverage_to_architect` | `return` | HE | Architect | Eval coverage for new components + dev-phase eval criteria | None |

**Phase Review** — Developer submits phase deliverables for QA:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 12 | `announce_phase_to_evaluator` | `announce` | Developer | Evaluator | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 13 | `announce_phase_to_harness_engineer` | `announce` | Developer | HE | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 14 | `submit_phase_to_evaluator` | `submit` | Developer | Evaluator | Phase deliverables → pass/fail findings, spec/plan compliance report | Deliverables match plan |
| 15 | `submit_phase_to_harness_engineer` | `submit` | Developer | HE | Phase deliverables → EBDR-1 feedback packet (eval science findings, no scoring logic leaked) | None |

**Specialist Consultation** — Non-ownership-transfer expert input:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 16 | `consult_harness_engineer_on_gates` | `consult` | Planner | HE | Plan draft → eval gate placement recommendations (Stage 3 intervention) | None |
| 17 | `consult_evaluator_on_gates` | `consult` | Planner | Evaluator | Plan draft → acceptance gate placement recommendations | None |
| 18 | `request_research_from_researcher` | `consult` | Architect, HE, PM | Researcher | Research question → targeted findings | None |
| 19 | `ask_pm` | `question` | Any specialist | PM | Stakeholder question → answer/clarification | None |
| 20 | `coordinate_qa` | `coordinate` | HE ↔ Evaluator | Evaluator ↔ HE | QA findings → aligned review strategy | None |

#### Agent-Scoped Tool Ownership

Each agent only receives the tools relevant to its role. An agent cannot call a
tool it does not own.

| Agent | Pipeline Delivery | Pipeline Return | Stage Review | Phase Review | Consultation |
|---|---|---|---|---|---|
| PM | `deliver_prd_to_harness_engineer`, `deliver_prd_to_researcher`, `deliver_design_package_to_architect`, `deliver_planning_package_to_planner`, `deliver_development_package_to_developer` | — | — | — | `request_research_from_researcher` |
| Harness Engineer | — | `return_eval_suite_to_pm`, `return_eval_coverage_to_architect` | `submit_spec_to_harness_engineer` (receives) | `announce_phase_to_harness_engineer` (receives), `submit_phase_to_harness_engineer` (receives) | `consult_harness_engineer_on_gates` (receives), `request_research_from_researcher`, `coordinate_qa` |
| Researcher | — | `return_research_bundle_to_pm` | — | — | `request_research_from_researcher` (receives) |
| Architect | — | `return_design_package_to_pm` | `submit_spec_to_harness_engineer` | — | `request_research_from_researcher` |
| Planner | — | `return_plan_to_pm` | — | — | `consult_harness_engineer_on_gates`, `consult_evaluator_on_gates` |
| Developer | — | — | — | `announce_phase_to_evaluator`, `announce_phase_to_harness_engineer`, `submit_phase_to_evaluator`, `submit_phase_to_harness_engineer` | `ask_pm` |
| Evaluator | — | — | — | `announce_phase_to_evaluator` (receives), `submit_phase_to_evaluator` (receives) | `consult_evaluator_on_gates` (receives), `coordinate_qa` |

#### Pipeline Flow Diagram

The pipeline progression flows through the PM as hub. Specialists return
completed work to the PM, who then delivers to the next specialist. Direct
specialist-to-specialist interactions exist for stage reviews and consultations. 

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

### Mounted Graph Execution and Sandbox Semantics

Meta Harness v1 uses a single Project Coordination Graph with peer role Deep
Agents mounted as child subgraphs. This is the only v1 project-role topology.
The PM remains the user-facing agent inside that topology.

Sandbox support does not change the graph topology. A sandbox is a backend and
runtime environment for file and shell/tool execution, not a separate top-level
agent application. A sandbox-backed role agent is still a mounted child graph; it
just receives a sandbox-capable backend.

Separate remotely deployed role assistants are out of scope for v1. That topology
would communicate through LangGraph SDK thread/run APIs rather than native
`Command.PARENT`, and it should not be treated as the default Meta Harness
handoff model.

The local development harness should expose the Project Coordination Graph
through `langgraph.json` + `langgraph dev` so LangGraph Studio can inspect graph
behavior, project thread state, child checkpoint namespaces, and routing.

Stock `AsyncSubAgent` remains useful for ad hoc background tasks, but it should
not be the primary project-role topology. Its start path creates a new remote
thread and then stores that generated thread ID as the task ID. That is at odds
with the invariant that every core role is a mounted, stateful Deep Agent child
graph under the Project Coordination Graph.

### Observability, Tracing, and Studio

LangSmith tracing is a first-class requirement for this topology. The
Project Coordination Graph should not rely on ad hoc logs to reconstruct agent behavior
after the fact. Every Project Coordination Graph handoff and Deep Agent invocation should
be searchable by at least:

- `project_id`
- `agent_name`
- `thread_id`
- `handoff_id`
- `phase`
- `from_agent`
- `to_agent`

LangGraph Studio and LangSmith serve different jobs in the local workflow.
LangGraph Studio is the interactive local development surface for graph
behavior, thread inspection, and checkpoint debugging through `langgraph dev`.
LangSmith is the durable observability and evaluation plane for traces, run
trees, feedback, datasets, experiments, and shareable thread/run links.

Do not assume trace hierarchy alone is enough to reconstruct project behavior.
The Project Coordination Graph must persist handoff records and propagate
correlation metadata so sandbox-backed tool work, role graph runs, and phase-gate
decisions can be stitched together in LangSmith.

#### Local Development Tracing — Configuration and Architecture

**Environment setup (`.env` / `.env.example`):**

```
LANGSMITH_API_KEY=<key>
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=meta-harness
LANGCHAIN_CALLBACKS_BACKGROUND=false
```

- `LANGSMITH_TRACING=true` must be explicit. Neither `langgraph dev` nor the
  Deep Agents CLI auto-enables tracing — both check for `LANGSMITH_API_KEY` and
  `LANGSMITH_TRACING` before activating the tracing pipeline
  (`.reference/libs/cli/deepagents_cli/config.py:1622-1628`).
- `LANGSMITH_PROJECT=meta-harness` is the v1 project name. All local dev, CI,
  and production runs flow to the same LangSmith project; environment is
  distinguished by `metadata` on the run, not by project name.
- `LANGCHAIN_CALLBACKS_BACKGROUND=false` is required for eval and experiment
  runs to flush traces synchronously before process exit. Safe to leave on for
  interactive dev sessions.

**Trace hierarchy — no explicit wiring required:**

LangGraph Pregel automatically propagates a child callback manager (scoped to
`graph:step:<N>`) into every node's `RunnableConfig` via
`manager.get_child(f"graph:step:{step}")` (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:694-698`).
When a mounted Deep Agent child graph executes as a subgraph node inside the
Project Coordination Graph, it inherits the parent's LangSmith run context
through this mechanism. Each role agent invocation appears as a nested run
under the PCG root run automatically. No `parent_run_id` threading in
application code is needed or appropriate.

**Role identity in traces — free via `name=`:**

`create_deep_agent(name=<role>)` passes the name to `create_agent()` as the
graph run name and also embeds it as `lc_agent_name` in the `metadata` block
on every run from that agent
(`.reference/libs/deepagents/deepagents/graph.py:617-622`). Every role
(e.g. `"pm"`, `"developer"`, `"harness-engineer"`) will be identifiable by
name in LangSmith without additional instrumentation.

**Correlation metadata placement:**

The seven required searchable fields are split across two concerns:

- `project_id`, `agent_name`, `thread_id` — set once on the PCG's
  `.with_config({"metadata": {...}})` at graph initialization time, scoped to
  the project thread.
- `handoff_id`, `phase`, `from_agent`, `to_agent` — handoff-scoped fields;
  carried by the handoff record schema and not set as LangSmith run metadata
  directly. These are retrieved by querying handoff records, not by filtering
  LangSmith runs.

### Specialist Loops

Specialist-to-specialist loops should not require PM mediation unless the loop
needs stakeholder clarification or scope authority. Examples:

- PM -> Harness Engineer -> PM when the Harness Engineer needs stakeholder
  clarification before finalizing eval criteria, rubrics, or datasets.
- Architect -> Researcher -> Architect for SDK/API gaps.
- Architect -> Harness Engineer -> Architect for evalability questions in the design.
- Architect -> Planner only after Harness Engineer review of new eval-relevant
  tools, prompts, datasets, and target harness criteria.
- Developer -> Evaluator -> Developer at phase boundaries.
- Developer -> Harness Engineer -> Developer for eval harness failures or dataset issues.
- Developer -> Harness Engineer and Developer -> Evaluator during final
  acceptance, because both agents gate different dimensions of readiness.

The loop is not a direct shared-memory conversation. It is a sequence of mounted
role graph invocations under the project thread, linked by handoff records and
artifact references in the Project Coordination Graph.

The Developer needs explicit routing guidance because the Harness Engineer and
Evaluator can both block a development phase:

| Target | Owns | Developer should route when |
|---|---|---|
| Harness Engineer | Evaluation science: rubrics, datasets, LLM judges, calibration, experiment design, eval harness behavior, public/held-out dataset policy | A phase fails because the eval harness, metric, judge, dataset, calibration method, or target-harness measurement strategy needs expert review. |
| Evaluator | Acceptance against the accepted plan and design: code/spec alignment, naming and SDK compliance, UI/UX/TUI behavior, test execution, phase pass/fail findings | A phase needs implementation review, UX/TUI verification, design conformance checking, or a hard pass/fail against the approved task plan. |
| PM | Stakeholder scope and business acceptance | A specialist question changes requirements, success criteria, user-facing behavior, or business priority. |

This boundary belongs in the Developer prompt and tool descriptions. The AD
does not need the final schema, but the later implementation spec should encode
the distinction so Developer feedback loops do not collapse into one vague
`request_evaluation` path.

### Source Alignment Notes

- `create_deep_agent()` accepts `checkpointer`, `store`, `backend`, `memory`, `skills`, `subagents`, and `name`, and passes `checkpointer`, `store`, and `name` through to the compiled agent (`.reference/libs/deepagents/deepagents/graph.py:217-236`, `602-623`).
- Declarative `task` subagents are documented as ephemeral and stateless, and the `task` implementation invokes the subagent with synthesized state but no runtime config (`.reference/libs/deepagents/deepagents/middleware/subagents.py:152-162`, `355-376`).
- `CompiledSubAgent` runnables are used as-is, but the same `task` call path still does not provide a stable project `thread_id` config (`.reference/libs/deepagents/deepagents/middleware/subagents.py:488-493`).
- Stock `AsyncSubAgent` launches a remote thread with `client.threads.create()` and uses that generated ID as `task_id`; follow-up updates reuse that task thread (`.reference/libs/deepagents/deepagents/middleware/async_subagents.py:280-318`, `500-548`).
- LangGraph checkpoint memory is keyed by `thread_id`; reusing the same thread accumulates state across invocations (`.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1038-1074`).
- LangGraph `Command.PARENT` targets the closest parent graph, and parent-command bubbling is handled by LangGraph runtime internals (`.venv/lib/python3.11/site-packages/langgraph/types.py:652-702`, `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1540-1550`).
- `ToolNode` supports tool-returned `Command` values, and LangChain `create_agent()` wires tools through `ToolNode`, which keeps this path compatible with Deep Agents because `create_deep_agent()` delegates to `create_agent()` (`.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:857-899`, `.venv/lib/python3.11/site-packages/langchain/agents/factory.py:920-939`, `.reference/libs/deepagents/deepagents/graph.py:602-623`).
- Mounted subgraph persistence can use the parent project `thread_id` with stable child checkpoint namespaces when the child graph is compiled for subgraph checkpointing; root graphs cannot use `checkpointer=True` (`.venv/lib/python3.11/site-packages/langgraph/pregel/main.py:2416`, `2613-2615`, `.venv/lib/python3.11/site-packages/langgraph/_internal/_config.py:34-45`).
- The lower-level LangGraph SDK supports explicit thread creation and explicit run submission against a chosen thread; this matters for any future split-assistant deployment, but it is not the v1 mounted-graph default (`.venv/lib/python3.11/site-packages/langgraph_sdk/_async/threads.py:98-143`, `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py:435-462`, `552-585`).
- The Deep Agents CLI scaffolds `langgraph.json` for `langgraph dev` with a graph entry point and optional checkpointer path (`.reference/libs/cli/deepagents_cli/server.py:85-119`, `.reference/libs/cli/deepagents_cli/server_manager.py:92-115`).
- The Deep Agents CLI server graph is a module-level graph entrypoint: `server_graph.py` builds the graph from environment-backed server config and exports `graph = make_graph()` for the generated `langgraph.json` reference (`.reference/libs/cli/deepagents_cli/server_graph.py:1-10`, `93-196`).
- The Deep Agents CLI server path creates sandbox backends through `deepagents_cli.integrations.sandbox_factory.create_sandbox(...)`, keeps the sandbox context manager open for the server process lifetime, and passes the resulting backend into `create_cli_agent(...)` (`.reference/libs/cli/deepagents_cli/server_graph.py:117-170`, `.reference/libs/cli/deepagents_cli/integrations/sandbox_factory.py:1-134`).
- The Deep Agents CLI names its sandbox integration package `integrations/` and keeps the provider boundary in `sandbox_provider.py`; Meta Harness should follow that package convention instead of inventing a `runtime/sandbox.py` shape (`.reference/libs/cli/deepagents_cli/integrations/__init__.py`, `.reference/libs/cli/deepagents_cli/integrations/sandbox_provider.py:1-49`).
- `create_cli_agent(...)` chooses SDK backends directly: local mode uses `LocalShellBackend` or `FilesystemBackend`, sandbox mode uses the supplied sandbox backend, and any `CompositeBackend` use is an SDK import for routing generated/temporary file areas rather than an app-owned backend module (`.reference/libs/cli/deepagents_cli/agent.py:1104-1218`, `.reference/libs/deepagents/deepagents/backends/composite.py:119-158`).
- The Deep Agents deploy template also uses a graph factory entrypoint: generated `langgraph.json` points to `./deploy_graph.py:make_graph`, and the generated module exposes `graph = make_graph` for runtime factory loading (`.reference/libs/cli/deepagents_cli/deploy/bundler.py:192-201`, `.reference/libs/cli/deepagents_cli/deploy/templates.py:430-469`).
- The deploy template is where the CLI builds a generated backend factory with an SDK `CompositeBackend`, a sandbox default, and store-backed `/memories/` and `/skills/` routes; that pattern should be imported or adapted from the SDK/CLI after focused implementation validation, not mirrored as a first-pass `runtime/` package or app-owned `checkpointers.py`, `stores.py`, or `model_policy.py` modules (`.reference/libs/cli/deepagents_cli/deploy/templates.py:199-207`, `405-424`).
- LangGraph API treats callable graph exports as factories, compiles exported `StateGraph` builders automatically, and accepts already-compiled Pregel graphs (`.venv/lib/python3.11/site-packages/langgraph_api/graph.py:330-379`, `730-765`).
- LangGraph SDK assistants use graph IDs that are normally set in `langgraph.json` (`.venv/lib/python3.11/site-packages/langgraph_sdk/_async/assistants.py:320-350`).
- LangGraph local development docs show `langgraph.json` using `"dependencies": ["."]` and graph refs shaped like `"my_agent": "./my_agent/agent.py:graph"`, so a root `./graph.py:graph` or `./graph.py:make_graph` entrypoint is a valid project layout when the root is the app boundary ([LangGraph local development docs](https://docs.langchain.com/langsmith/local-dev-testing)).
- Deep Agents CLI resolves LangSmith thread URLs only when tracing is configured, and its `/trace` flow tells users to set `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` when unavailable (`.reference/libs/cli/deepagents_cli/config.py:1600-1745`, `.reference/libs/cli/deepagents_cli/app.py:2545-2579`).

## Full Repo Structure Naming Decision

The v1 repo is organized around peer Deep Agent factories, not around a PM-owned
`subagents/` bucket. The root `graph.py` is the approved LangGraph application
entrypoint and the self-contained deterministic Project Coordination Graph
factory. The selected topology makes `agents/` the approved module name for core
roles. SDK `SubAgent` dicts, if any are later needed for ephemeral isolated
tasks, are reserved for a narrowly named `task_agents/` module inside the owning
role, not at the top level.

```txt
meta-harness/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── AD.md
├── langgraph.json
├── graph.py                          # LangGraph Project Coordination Graph entrypoint/factory
├── docs/
│   ├── architecture/
│   └── specs/
├── src/
│   └── meta_harness/
│       ├── __init__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── catalog.py                  # one source of truth for role identity
│       │   ├── project_manager/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py                # create_deep_agent(name="project-manager", ...)
│       │   │   └── system_prompt.md
│       │   ├── harness_engineer/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── system_prompt.md
│       │   ├── researcher/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── system_prompt.md
│       │   ├── architect/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── system_prompt.md
│       │   ├── planner/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── system_prompt.md
│       │   ├── developer/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── system_prompt.md
│       │   └── evaluator/
│       │       ├── __init__.py
│       │       ├── agent.py
│       │       └── system_prompt.md
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── sandbox_factory.py          # follow deepagents_cli.integrations
│       │   └── sandbox_provider.py         # provider boundary if wrappers are needed
│       └── tools/
└── tests/
    ├── contract/
    ├── integration/
    └── eval/
```

Naming choices embedded in this tree:

- Use `agents/` for PM and peer specialists.
- Do not use top-level `subagents/` for core roles.
- Use `developer/` as the canonical module. Generator and optimizer are
  responsibilities inside the Developer prompt and tool descriptions, not module
  names.
- Use root `graph.py` for the deterministic LangGraph Project Coordination Graph. This
  mirrors the LangGraph and Deep Agents CLI graph-entrypoint convention while
  preventing a premature `project_coordination_graph/` package from spreading the routing
  logic across files before the first implementation proves its shape.
- Put the Project Coordination Graph `StateGraph` state schema, node functions, conditional
  routing, handoff record helpers, phase-gate transitions, project thread and
  role checkpoint namespace helpers, and compile call in root `graph.py` initially. Split only
  after the file has a concrete pressure point, such as shared typed contracts
  needed outside graph tests, sandbox integration wiring, or a production
  persistence adapter.
- Use `integrations/` for sandbox provider wiring. Mirror the Deep Agents CLI
  convention: keep the provider interface in `sandbox_provider.py`, create or
  connect to sandbox backends through `sandbox_factory.py`, and pass the resulting
  SDK backend into the owning agent/Project Coordination Graph construction path.
- Do not add a first-pass `runtime/` package, `runtime/backends/`, `runtime/sandbox.py`,
  `checkpointers.py`, `stores.py`, `model_policy.py`, or `middleware_profiles.py`.
  Those are not SDK/CLI conventions for this boundary. Add a module only after a
  concrete SDK-aligned need appears and its name is approved.
- Construct backend, checkpointer, store, model, and middleware configuration at
  the SDK boundary that consumes it: the role Deep Agent factory, the root
  Project Coordination Graph factory, or the CLI-aligned sandbox integration package.
  Import SDK abstractions directly instead of wrapping them behind app-owned
  convention files.
- Keep `tools/` for now, but do not name nested tool modules until concrete tool
  contracts exist.

### LangGraph Project Coordination Graph Factory Contract

The Project Coordination Graph is a LangGraph application boundary. It is not a
Deep Agent and it is not an agent registry. A tasteful first implementation
should keep this in root `graph.py`:

```python
def make_graph(...) -> CompiledStateGraph:
    builder = StateGraph(
        ProjectCoordinationState,
        context_schema=ProjectCoordinationContext,
        input_schema=ProjectCoordinationInput,
        output_schema=ProjectCoordinationOutput,
    )
    builder.add_node("receive_user_input", receive_user_input)
    builder.add_node("process_handoff", process_handoff)
    builder.add_node("run_agent", run_agent)
    builder.add_edge(START, "receive_user_input")
    builder.add_edge("receive_user_input", "run_agent")
    builder.add_edge("process_handoff", "run_agent")
    return builder.compile(
        checkpointer=checkpointer,
        store=store,
        name="meta-harness-project-coordination-graph",
    )


graph = make_graph
```

`make_graph()` is proposed because the Deep Agents deploy template uses an async
`make_graph(config, runtime)` factory shape when graph construction needs runtime
config, while the CLI server also supports a module-level `graph` export. The
root `langgraph.json` can point to either `./graph.py:graph` or
`./graph.py:make_graph`; prefer `./graph.py:make_graph` if the Project Coordination Graph
needs invocation-time config/runtime, otherwise `./graph.py:graph` is simpler.
The role factories should use `create_<role>_agent()` because those modules return
Deep Agent graphs via `create_deep_agent()`.

The Project Coordination Graph nodes should only do deterministic plumbing:

- `receive_user_input`: write user input into state.
- `process_handoff`: record the handoff, ensure the target role's checkpoint
  namespace and workspace paths are initialized, and prepare the invocation payload.
- `run_agent`: invoke the target mounted Deep Agent child graph using the parent
  project thread and target role namespace.

Phase gate enforcement, HITL question surfacing, and routing intelligence are
**not** PCG responsibilities. Phase gates are middleware hooks on handoff tools.
HITL questions are handled by the `ask_user` middleware provided by the Deep
Agents SDK. Routing decisions are made by the calling agent via tool selection.

The Project Coordination Graph must not implement research, architecture, planning,
development, eval-science, prompt composition, phase gate logic, or provider/model
request policy. Those remain in peer Deep Agent factories, SDK configuration calls,
tool/prompt contracts, and middleware hooks. Do not create a runtime policy package
before a concrete SDK-aligned need appears.

## Project Workspace and Memory Structure Proposal

The memory filesystem should keep the original role-scoped structure. This tree
preserves a shared team memory file at the root plus per-role `AGENTS.md`,
`memory/`, `skills/`, and project artifact directories. Backend routing can still
map this layout onto disk or sandbox storage through SDK backends; the tree below
describes the desired workspace semantics, not a new app-owned backend layer.
The `dev/` path is a workspace bucket, not a Python module naming decision.

```txt
~/Agents/
├── AGENTS.md                         # shared team memory; PM writes here
├── pm/
│   ├── AGENTS.md                     # PM core memory loaded via memory=
│   ├── memory/                       # PM on-demand memory files
│   ├── skills/                       # PM skills; SKILL.md subdirs
│   └── projects/                     # PM project tracking, tagged by project ID
├── architect/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/                     # Architect project specs
│       ├── specs-(Previous)          # Previous spec versions, tagged by project ID
│       └── target-spec/              # Current target specification
├── researcher/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── research-bundles/         # Compiled research artifacts, tagged by project ID
├── planner/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── plans/                    # Generated development plans
├── dev/                              # Developer / Generator / Optimizer
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── wip/                      # Work-in-progress implementations
└── harness-engineer/
    ├── AGENTS.md
    ├── memory/
    ├── skills/
    └── projects/
        ├── eval-harnesses/           # Evaluation harness definitions
        ├── datasets/
        │   ├── public/               # Public datasets for dev phases
        │   └── held-out/             # Held-out datasets for final eval
        ├── rubrics/                  # Scoring rubrics and criteria
        └── experiments/              # Experiment logs and results
```


### System Overview

```mermaid
flowchart LR
    U["User / UI"] --> PCG["LangGraph Project Coordination Graph\nthread: project"]
    PCG --> PM["PM Deep Agent\nnamespace: project_manager"]

    PCG --> HE["Harness Engineer\nnamespace: harness_engineer"]
    PCG --> R["Researcher\nnamespace: researcher"]
    PCG --> A["Architect\nnamespace: architect"]
    PCG --> PL["Planner\nnamespace: planner"]
    PCG --> D["Developer\nnamespace: developer"]
    PCG --> E["Evaluator\nnamespace: evaluator"]

    PM -->|"handoff tool returns Command.PARENT"| PCG
    A -->|"request_research"| PCG
    HE -->|"ask_pm / evalability question"| PCG
    D -->|"request_evaluation"| PCG
    E -->|"pass/fail + findings"| PCG

    PCG --> FS["Project Artifacts\nPRD, design, plans, evals, datasets"]
    PCG --> LG["LangGraph Dev Server\nlanggraph.json graph ID"]
    LG --> STUDIO["LangGraph Studio\nlocal dev inspection"]
    PCG --> OBS["LangSmith\ntraces, run/thread links, evals"]
```

### Sequence (optional)

```mermaid
sequenceDiagram
    participant User as User / UI
    participant PM as PM Deep Agent
    participant PCG as LangGraph Project Coordination Graph
    participant HE as Harness Engineer
    participant R as Researcher
    participant A as Architect
    participant PL as Planner
    participant D as Developer
    participant E as Evaluator
    participant FS as Project Workspace
    participant LS as LangSmith

    User->>PCG: Scope request and requirements
    PCG->>PM: Route user input to PM child graph
    PM->>PCG: Command.PARENT handoff_to_harness_engineer(project_id, brief, artifact_refs)
    PCG->>FS: Append handoff record and artifact refs
    PCG->>HE: Invoke mounted Harness Engineer role graph
    HE-->>PCG: Eval criteria, rubrics, dataset questions

    alt Stakeholder clarification needed
        PCG->>PM: surface_question(question, asking_agent)
        PM->>User: Ask scoped clarification
        User-->>PM: Answer
        PM-->>PCG: Answer with project context
        PCG->>HE: Resume same Harness Engineer role graph
    end

    PCG->>A: Invoke Architect with PRD and eval refs
    A->>PCG: request_research(targeted_gap, artifact_refs)
    PCG->>R: Invoke Researcher mounted role graph
    R-->>PCG: Research bundle refs
    PCG-->>A: Resume Architect role graph with research refs
    A-->>PCG: Design/spec artifact refs
    PCG->>PL: Invoke Planner mounted role graph
    PL-->>PCG: Phase plan refs
    PCG->>D: Invoke Developer mounted role graph
    D->>PCG: request_evaluation(phase, artifact_refs)

    par Implementation acceptance
        PCG->>E: Invoke Evaluator mounted role graph
        E-->>PCG: Pass/fail findings
    and Eval science review
        PCG->>HE: Invoke Harness Engineer for eval harness questions
        HE-->>PCG: Experiment and eval findings
    end

    PCG->>LS: Emit correlation metadata
    PCG-->>PM: Phase gate result and next action
    PM-->>User: Status, question, or delivery summary
```

### Data Contracts

The exact Pydantic or `TypedDict` wire format should be defined in the
implementation spec. The field set and enum values below are locked as an AD decision.

```json
{
  "project_id": "string",
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

Field notes:

- `project_id` doubles as the root `thread_id`; no separate `project_thread_id` field needed.
- `target_agent` maps 1:1 to the checkpoint namespace in v1; no separate `target_role_namespace` field needed.
- `reason` encodes the *type of transition* (not the pipeline phase). Middleware dispatches on the `(source_agent, target_agent, reason)` triple to determine which gate logic to apply. The `question` reason covers specialist-to-PM stakeholder questions — no separate `question` field needed.
- `brief` is the concise summary the receiving agent reads; was listed in the Handoff Protocol but previously missing from this schema.
- `artifact_paths` are filesystem paths to artifacts the calling agent produced, so the receiver knows what to load.
- `langsmith_run_id` is the LangSmith run ID for the mounted role graph invocation, for trace correlation.
- `status` tracks the handoff lifecycle (queued → running → completed/failed), not the agent's task status.
- `created_at` is an RFC3339 timestamp set by the PCG when the handoff is recorded.

---

## 5) Implementation Plan *Will have an implementation plan for each agent, and a full system implementation plan that will be documented in a separate file @ docs/spec/~~~*

### Milestones <TBD>

- [ ] M1: `<milestone name>`
- [ ] M2: `<milestone name>`
- [ ] M3: `<milestone name>`

### Rollout Strategy <TBD>

| Stage | Traffic / Scope | Guardrails | Rollback Trigger |
|---|---|---|---|
| Dev | `<scope>` | `<checks>` | `<trigger>` |
| Staging | `<scope>` | `<checks>` | `<trigger>` |
| Prod (canary) | `<scope>` | `<checks>` | `<trigger>` |

```diff
- Old behavior: <describe>
+ New behavior: <describe>
```

---

## 6) Observability & Evaluation

### Required Signals

- LangSmith traces for PM and every specialist Deep Agent invocation.
- Project Coordination Graph handoff records keyed by `project_id`, `handoff_id`, source agent, target agent, phase, artifact refs, run ID, and resulting gate decision.
- Stable project `thread_id`, role `checkpoint_ns`, and `agent_name` metadata on every mounted role invocation.
- LangGraph Studio local inspection path through `langgraph.json` and `langgraph dev`.
- LangSmith thread/run links exposed in the UI when tracing is configured.
- Evaluation feedback from Harness Engineer and Evaluator kept separate by owner and gate type.

### Success Criteria

| Metric | Baseline | Target | Window |
|---|---|---|---|
| Project-role state reuse | No stable baseline | Same `(project_id, agent_name)` resumes the same mounted role graph state | Every handoff |
| Handoff traceability | Manual reconstruction | Each handoff has a Project Coordination Graph record and a LangSmith run/thread reference when configured | Every handoff |
| Developer gate routing | Ambiguous `request_evaluation` target | Developer can distinguish Harness Engineer scientific eval issues from Evaluator implementation/spec acceptance issues | Every phase gate |
| Local dev inspection | Ad hoc terminal logs | A local `langgraph dev` workflow can inspect the Project Coordination Graph, project thread, and role namespaces in LangGraph Studio | Before v1 implementation hardening |

### Validation Plan

1. Prove Project Coordination Graph -> PM -> Harness Engineer -> PM with a stable project thread, visible role checkpoint namespaces, and LangSmith metadata.
2. Prove Architect -> Researcher -> Architect without PM mediation.
3. Prove Developer -> Evaluator -> Developer and Developer -> Harness Engineer -> Developer route to different gate owners.
4. Prove a sandbox-backed role agent preserves the same mounted graph topology while using a sandbox-capable backend for file and shell/tool execution.

---

## 7) Risks, Tradeoffs, and Mitigations

> [!WARNING]
> List realistic failure modes, not generic statements.

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Core specialists accidentally implemented as ephemeral `task` subagents | `M` | `H` | Treat `task` as an isolated-worker tool only. Add tests or trace checks that core roles run as mounted child graphs with stable role checkpoint namespaces. | `@Jason` |
| Stock `AsyncSubAgent` becomes the primary project-role topology | `M` | `H` | Keep `AsyncSubAgent` limited to ad hoc background tasks. Core roles must stay mounted under the Project Coordination Graph for v1. | `@Jason` |
| Sandbox support is mistaken for a separate agent topology | `M` | `H` | Treat sandbox as backend/runtime configuration for mounted role agents, not as a reason to split roles into separate top-level assistants. | `@Jason` |
| LangGraph Project Coordination Graph grows into a second agent brain | `M` | `M` | Keep LangGraph nodes deterministic and coarse. Deep Agents own cognition; LangGraph owns routing, state, and gates. | `@Jason` |
| Handoff loops become invisible or hard to debug | `M` | `H` | Persist structured handoff records with caller, target, reason, artifact refs, run ID, and resulting gate decision. | `@Jason` |
| LangSmith traces are insufficient to reconstruct graph behavior by themselves | `M` | `H` | Standardize correlation metadata and persist Project Coordination Graph handoff records; do not depend on implicit trace hierarchy alone. | `@Jason` |
| Developer confuses Harness Engineer feedback with Evaluator feedback | `M` | `M` | Encode the owner split in Developer prompt/tool descriptions and phase-gate records. | `@Jason` |
| Parallel updates interrupt active specialist work unexpectedly | `M` | `M` | Route updates through explicit handoff records and reserve cancellation or interruption for explicit redirects or stale work cancellation. | `@Jason` |

---

## 8) Security / Privacy / Compliance

- Data classification: `<public/internal/restricted>`
- PII handling: `<none / masked / encrypted>`
- Access model: `<RBAC details>`
- Retention policy: `<duration + deletion mechanism>`

---
 
## 9) Open Questions

- [x] Jason approval: adopt the section 4 repo-structure naming decision that uses root `graph.py` for the LangGraph Project Coordination Graph entrypoint, uses `agents/` for peer role modules, reserves `task_agents/` only for future role-owned ephemeral SDK `SubAgent` helpers, uses `developer/` as the canonical Developer module name, and follows the Deep Agents CLI `integrations/` sandbox convention. Approved by Jason on `2026-04-11`.
- [x] Decide the production checkpointer and store backend for local-first and sandbox-backed mounted graph execution. Decision: three runtime modes, two code paths. (1) **Local dev** (`langgraph dev`): `SqliteSaver` checkpointer and managed store are auto-injected by the dev server — factory passes neither. (2) **CLI TUI shipped to end users**: `SqliteSaver` (from `langgraph-checkpoint-sqlite`) at a user-local path (e.g. `~/.metaharness/state.db`) explicitly passed to the Project Coordination Graph factory; `InMemoryStore()` for store (no `StoreBackend` needed — `FilesystemBackend` owns disk persistence). (3) **Web app / LangGraph Platform**: managed Postgres-backed checkpointer and store are auto-injected by the platform — factory passes neither. `StoreBackend()` with no args resolves from the LangGraph execution context via `get_store()` in all platform-managed modes. `langgraph-checkpoint-sqlite` is a required production dependency. Approved by Jason on `2026-04-12`.
- [x] Decide whether the project-aware handoff wrapper is implemented as a LangGraph Project Coordination Graph node, a tool service, custom Deep Agents middleware, or a combination. Decision: v1 handoffs are explicit Deep Agent tools that return `Command(graph=Command.PARENT, goto=<coordination_node>, update=<handoff_payload>)`; Project Coordination Graph nodes record and route the handoff; custom handoff middleware is out of v1. Approved by Jason on `2026-04-12`.
- [x] Co-author and approve the first Project Coordination Graph node set. Decision: three nodes (`receive_user_input`, `process_handoff`, `run_agent`), no conditional edges, linear topology. Phase gates moved to middleware hooks on handoff tools. Routing intelligence owned by calling agents via tool selection. Removed `record_handoff` and `ensure_role_state` as separate nodes (merged into `process_handoff`). Removed `route_after_agent`, `gate_phase`, and `surface_question` (routing is agent-driven, gates are middleware, HITL is SDK `ask_user`). Approved by Jason on `2026-04-12`.
- [x] Co-author and approve the handoff tool use-case matrix. Decision: 19 tools across 5 categories (Pipeline Delivery, Pipeline Return, Stage Review, Phase Review, Specialist Consultation). Naming convention `<verb>_<artifact>_to_<role>` — verb encodes blocking semantics. PM is the pipeline hub: specialists return to PM, PM delivers to next specialist. Direct specialist-to-specialist interactions for stage reviews and consultations. `reason` enum changed from phase-based (`scope_handoff|eval_request|...`) to verb-based (`deliver|return|submit|consult|coordinate|question`) — middleware dispatches on `(source, target, reason)` triple. Agent-scoped tool ownership: each agent only receives relevant tools. Artifact paths are references, not copies. Approved by Jason on `2026-04-12`.
- [x] Define the minimal handoff record schema in the AD; delegate exact Pydantic/TypedDict wire format to the implementation spec. Decision: locked field set is `project_id`, `handoff_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`, `langsmith_run_id`, `status`, `created_at`. Removed `project_thread_id` (redundant with `project_id`), `target_role_namespace` (derivable from `target_agent` in v1), and `question` (folded into `reason`). Renamed `artifact_refs` → `artifact_paths` and `run_id` → `langsmith_run_id` for clarity. Added `brief` (was in Handoff Protocol but missing from schema). Approved by Jason on `2026-04-12`.
- [ ] Define the phase gate enum values in the AD (e.g., scoping, harness-engineering, research, architecture, planning, development, acceptance) and which gate transitions require explicit approval vs. automatic advancement.
- [x] Decide whether sandbox execution changes the v1 graph topology. Decision: sandbox support is backend/runtime configuration for mounted role agents and does not split roles into separate top-level assistants. Separate remotely deployed role assistants are out of scope for v1. Approved by Jason on `2026-04-12`.
- [ ] Decide whether the Harness Engineer vs Evaluator gate-owner boundary belongs in this AD, a Developer prompt spec, or a separate evaluation architecture spec.
- [ ] As a context engineering matter: is it wise to allow the PCG state to grow unboundedly with every handoff record? Furthermore, does the PCG's accumulated state flood each mounted child agent's context window at invocation, or does the child agent selectively pull only the context it needs? Clarify the LangGraph parent-to-child state propagation contract and determine whether a compaction/summarization strategy is needed for the PCG handoff log.

---

## 10) Changelog

| Date | Author | Change |
|---|---|---|
| `2026-04-12` | `@Cascade` | Refined artifact path semantics: references by default, but PM-assembled handoff packages for `deliver_planning_package_to_planner` and `deliver_development_package_to_developer`. The PM consolidates the full artifact set into an organized directory that gets copied into the receiving agent's filesystem. Early-stage deliveries remain as references. |
| `2026-04-12` | `@Cascade` | Overhauled handoff tool use-case matrix: 7 → 19 tools across 5 categories. Adopted `<verb>_<artifact>_to_<role>` naming convention (verb encodes blocking semantics). PM-as-hub pipeline topology: specialists return to PM, PM delivers to next specialist. Added Pipeline Return category for specialist→PM returns. Added Stage Review category for Architect↔HE Stage 2 loop. Added `coordinate_qa` for HE↔Evaluator alignment. Changed `reason` enum from phase-based to verb-based (`deliver|return|submit|consult|coordinate|question`) — middleware dispatches on `(source, target, reason)` triple. Added agent-scoped tool ownership table. Added artifact path reference semantics (paths, not copies). |
| `2026-04-12` | `@Cascade` | Locked handoff tool use-case matrix (v1): 7 tools with `reason` enum mapping, triggering scenarios, required payload, blocking behavior, middleware gates, and expected outputs. Only `request_research` and `ask_pm` are non-blocking. |
| `2026-04-12` | `@Cascade` | Session arc: set out to close the handoff record schema open question; reasoning through field purposes (what's redundant, what's ambiguous, who fills what) revealed that the PCG node set was also answerable. Key insight from Jason: if each node is a Deep Agent that decides its own peer target via tool call, then the PCG doesn't route — it plumbs. Phase gates are middleware hooks, not graph nodes or conditional edges. Closed two open questions for the price of one. |
| `2026-04-12` | `@Cascade` | Simplified PCG topology to 3 nodes (`receive_user_input`, `process_handoff`, `run_agent`) with no conditional edges. Moved phase gate enforcement to middleware hooks on handoff tools. Moved routing intelligence to calling agents (tool selection). Merged `record_handoff` + `ensure_role_state` into `process_handoff`. Removed `route_after_agent`, `gate_phase`, `surface_question` from node set. Added `reason` enum for middleware dispatch. Updated factory contract, responsibilities, and handoff protocol sections. |
| `2026-04-12` | `@Cascade` | Locked handoff record schema field set in the AD: `project_id`, `handoff_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`, `langsmith_run_id`, `status`, `created_at`. Removed `project_thread_id`, `target_role_namespace`, `question`. Renamed `artifact_refs` → `artifact_paths`, `run_id` → `langsmith_run_id`. Added `brief`. Opened question on PCG state growth and parent-to-child context propagation. |
| `2026-04-12` | `@Cascade` | Locked local development tracing configuration and architecture: `LANGSMITH_TRACING=true` must be explicit, `LANGSMITH_PROJECT=meta-harness` as v1 project name, `LANGCHAIN_CALLBACKS_BACKGROUND=false` required for eval runs. Documented that LangGraph Pregel propagates child callback context automatically — no `parent_run_id` wiring needed. Role identity free via `create_deep_agent(name=)`. Correlation metadata split: `project_id`/`agent_name`/`thread_id` on PCG `.with_config()`; handoff-scoped fields carried by handoff record schema. Removed ambiguous LangSmith UI exposure open question. |
| `2026-04-12` | `@Cascade` | Closed checkpointer and store backend decision: `SqliteSaver` for CLI TUI (explicit, user-local path), platform-managed for web app and `langgraph dev`. Added `langgraph-checkpoint-sqlite` as required dependency. |
| `2026-04-12` | `@Codex` | Marked the Project Coordination Graph node set and handoff tool use-case matrix as discussion-needed before AD acceptance. |
| `2026-04-12` | `@Codex` | Locked the mounted Project Coordination Graph handoff decision: PM remains UI-facing, role agents are child graphs, handoff tools return `Command.PARENT`, and sandbox support does not change topology. |
| `2026-04-11` | `@Codex` | Closed Jason approval on the repo-structure naming decision for `graph.py`, `agents/`, `developer/`, `task_agents/`, and `integrations/`. |
| `2026-04-11` | `@Codex` | Locked the committed `Project Coordination Graph` naming decision and `ProjectCoordination*` schema prefix. |
| `2026-04-11` | `@Codex` | Replaced the placeholder data-contract block with a proposed Project Coordination Graph handoff record shape. |
| `2026-04-11` | `@Codex` | Adopted `Project Coordination Graph` as the name for the thin LangGraph orchestration layer. |
| `2026-04-11` | `@Codex` | Restored Jason's original role-scoped memory filesystem proposal. |
| `2026-04-11` | `@Codex` | Changed ADR status to Proposed and replaced the generic sequence diagram with the Meta Harness handoff flow. |
| `2026-04-11` | `@Codex` | Replaced first-pass `runtime/` module proposal with the Deep Agents CLI `integrations/` sandbox convention. |
| `2026-04-11` | `@Codex` | Revised repo proposal to use root `graph.py` as the LangGraph Project Coordination Graph entrypoint and added graph factory evidence from Deep Agents CLI and LangGraph API source. |
| `2026-04-11` | `@Codex` | Proposed peer-agent repo structure and project workspace layout for Jason review. |
| `2026-04-11` | `@Codex` | Added LangSmith tracing, LangGraph Studio, and Developer gate-owner guidance. |
| `2026-04-11` | `@Codex` | Added stateful peer Deep Agents topology and LangGraph Project Coordination Graph guidance. |
| `YYYY-MM-DD` | `@name` | Initial draft |

---

## Appendix

### Links

- [Design Mock](./mock.png)
- [Issue Tracker](https://example.com)

### Image / Diagram

![Overview Diagram](overview.png)

### Footnotes

Key assumption goes here.[^1]

[^1]: `<supporting evidence or citation>`
