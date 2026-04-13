# Architecture Decision Record

> [!TIP]
> Keep this doc concise, factual, and testable. If a claim cannot be verified, add a validation step.

---

## 0) Header

| Field | Value |
|---|---|
| ADR ID | `ADR-001` |
| Title | `Meta Harness Architecture` |
| Status | `Pending` |
| Date | `2026-04-12` |
| Author(s) | `@Jason` |
| Reviewers | `@Jason` |
| Related PRs | `#NA`, `#NA` |
| Related Docs | `[AGENTS.md](../.agents/pm/AGENTS.md)`, `[SME Transcript](./sme_input/PCG-state-schema.md)`, `[PCG Analysis](./reports/pcg-state-schema-analysis.md)` |

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

`Status: Pending` · `Risk: Medium` · `Impact: High`

---

## 2) Context

### Problem Statement

Building, observing, and shipping LLM applications requires a multi-agent system
where specialist agents (evaluation science, research, architecture, planning,
development, quality assurance) collaborate under a project manager that owns
stakeholder communication. Existing approaches either flatten all specialist
cognition into a single agent's context window, force stateless ephemeral
sub-agent calls that cannot resume project-specific trajectories, or require a
heavy orchestration layer that duplicates agent reasoning. We need a topology
that preserves per-agent durable state, supports direct specialist-to-specialist
loops without PM mediation, keeps cognition inside Deep Agent harnesses, and
makes handoffs observable and auditable.

### Constraints

- All core agents must be stateful Deep Agents with stable checkpoint namespaces — no ephemeral `task` subagents for project roles.
- The coordination layer must be thin and deterministic — no LLM calls in PCG nodes, no routing intelligence in the graph.
- Agent-to-agent communication must go through explicit handoff tools that return `Command.PARENT` — no direct peer invocation.
- Phase gate enforcement must be middleware hooks on handoff tools, not PCG conditional edges.
- The system must support both local-first (user disk) and sandbox-backed (VM) execution from day one.
- The system must leverage the Deep Agents SDK as the primary agent harness — do not reimplement SDK capabilities.

### Non-Goals

- [ ] Deployment at scale / multi-tenant SaaS
- [ ] Threat modeling and security hardening (v1)
- [ ] Full web application deployment (v1; local CLI TUI first)
- [ ] Remotely deployed role assistants communicating via LangGraph SDK APIs (v2+)
- [ ] Custom handoff middleware beyond phase gate hooks (v2+)

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
| `process_handoff` | On first invocation (no pending handoff): accept stakeholder input, set `current_agent` to PM, create a synthetic handoff record from the user's message. On subsequent invocations: record the handoff, ensure the target role's checkpoint namespace and workspace paths are initialized, and prepare the invocation payload. |
| `run_agent` | Construct a single `HumanMessage` from `pending_handoff.brief` and invoke the target mounted Deep Agent child graph under its stable role namespace. Clear `pending_handoff` on completion. |

#### PCG State Schema

The `ProjectCoordinationState` carries only deterministic coordination data — no agent cognition, no artifact content, no specialist messages.

| Field | Type | Purpose | Set by |
|---|---|---|---|
| `messages` | `Annotated[list[AnyMessage], add_messages]` | **User-facing I/O channel.** Accumulates stakeholder input and PM's final product response only — lifecycle bookends. Never written to during pipeline execution. Also the only key shared with `_InputAgentState`, so it is the conduit by which `run_agent` passes input to child graphs. | `process_handoff` (stakeholder input), PM normal exit (final response) |
| `project_id` | `str` | Root thread identifier; doubles as project namespace for all child checkpoint namespaces | `process_handoff` (from initial invocation) |
| `current_phase` | `Literal["scoping", "research", "architecture", "planning", "development", "acceptance"]` | Current project phase; middleware reads this for gate dispatch | `process_handoff` (advanced on phase-transition handoffs) |
| `current_agent` | `Literal["project_manager", "harness_engineer", "researcher", "architect", "planner", "developer", "evaluator"]` | Which role graph is currently active; `run_agent` reads this to select the correct mounted child | `process_handoff` |
| `handoff_log` | `Annotated[list[HandoffRecord], add_messages]` | Append-only coordination audit trail — who handed what to whom, when, why, with which artifacts. Also serves as acceptance record for gated tools (e.g. `return_product_to_pm`). Capped at N records; cap mitigation delegated to implementation spec. | `process_handoff` |
| `pending_handoff` | `HandoffRecord \| None` | Active handoff cursor — the handoff record currently being processed by `run_agent`. Set by `process_handoff`, consumed by `run_agent`, cleared on completion. | `process_handoff` (set), `run_agent` (clear) |

**Key invariants:**

1. **`messages` is the user-facing I/O channel.** It accumulates only stakeholder `HumanMessage` objects (in) and the PM's final `AIMessage` product response (out) — lifecycle bookends. Handoff tools do NOT write to it. Child agent intermediate output does NOT flow back into it. The `add_messages` reducer is required to prevent overwrite when multiple user messages arrive across invocations.
2. **`messages` is the only key visible to child agents.** LangGraph maps parent state to child input by shared key name. The Deep Agent input schema (`_InputAgentState`) defines only `messages`. The implementation MUST set `input_schema=_InputAgentState` on each `add_node` call for mounted child graphs to prevent other PCG keys from leaking into child input.
3. **`run_agent` constructs the child's input, not the PCG.** The `run_agent` node constructs a single `HumanMessage` containing the handoff brief (from `pending_handoff`) and passes it as the child's `messages` input. The child never sees the raw PCG `messages` list.
4. **`handoff_log` uses `add_messages` for append-only semantics.** `HandoffRecord` objects implement the message protocol (have an `id` field) so `add_messages` provides append-without-overwrite. This is a reuse of the reducer for its semantics, not because handoff records are messages. The cap threshold N is a runtime constant; cap mitigation mechanism is delegated to the implementation spec.
5. **`pending_handoff` is an execution cursor, not a data store.** It points to the handoff currently being processed. It is set by `process_handoff`, consumed by `run_agent`, and cleared on completion. It is required by the two-node topology (data must flow through state between nodes).
6. **Child agents own their own conversation history.** Each mounted Deep Agent accumulates messages in its own checkpoint namespace. The PCG's `messages` key is not a conversation history — it's an I/O channel. Child agent message compaction is handled by `SummarizationMiddleware` within each agent, not by the PCG.
7. **Graph lifecycle is PM-controlled.** The PM decides when to end (finish normally → END) or stay alive (use `ask_user` → interrupt → pause). The PCG is transparent to interrupts — `ask_user` pauses the PM's child graph, which pauses the PCG node, which pauses the graph. Resume flows through automatically.

Exact Pydantic/TypedDict wire format and `HandoffRecord` type definition delegated to implementation spec.

The topology is linear with two nodes:

```txt
START → process_handoff → run_agent(PM)
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

#### `Command.PARENT` Update Contract

The handoff tool's `Command.PARENT` update dict writes to specific parent state
channels using their reducers. The AD specifies which keys are written — this is
an architectural decision (what gets communicated), not an implementation detail.

```python
Command(
    graph=Command.PARENT,
    goto="process_handoff",
    update={
        "handoff_log": [HandoffRecord(
            project_id=...,
            source_agent=...,
            target_agent=...,
            reason=...,
            brief=...,
            artifact_paths=...,
        )],
        "current_agent": <target_agent>,           # overwritten (no reducer)
        "current_phase": <new_phase_if_transition>, # overwritten; only on phase transitions
        "pending_handoff": HandoffRecord(...),      # same record as handoff_log entry
    }
)
```

**Key observation:** The update dict does NOT include `messages`. The handoff brief
and artifact paths are captured in `handoff_log`, not in `messages`. This is the
lifecycle-bookend invariant: `messages` only accumulates stakeholder input and the
PM's final product response.

**PCG-filled fields** (`handoff_id`, `langsmith_run_id`, `status`, `created_at`) are
added by `process_handoff`, not by the calling agent. The calling agent populates:
`project_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`.

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

#### Phase Gates

Phase enum values: `scoping`, `research`, `architecture`, `planning`, `development`, `acceptance`.

Two transitions require **explicit user approval**; all others auto-advance:

| Transition | What user reviews | Trigger |
|---|---|---|
| `scoping` → `research` | PRD + eval suite + business-logic datasets, rendered as stakeholder-friendly document package | PM receives completed eval suite from HE, packages it, presents to user |
| `architecture` → `planning` | Full design spec + tool schemas + system prompts, rendered as stakeholder-friendly document package | PM receives completed design from Architect, packages it, presents to user |

**Approval mechanism:** The PM owns a dedicated tool that presents the document package (docx/pdf/pptx) to the user for review. The user can accept, request revisions, or provide feedback. The PM resumes on user response. This is prompt-driven — the PM decides when to invoke the tool based on its system prompt — not a PCG-level interrupt. Exact tool schema and document rendering format are delegated to the implementation spec.

**Autonomous mode:** A runtime toggle that, when enabled, auto-advances all gates including the two approval gates. In autonomous mode the PM still packages the documents but does not pause for user review.

**All other transitions** (research → architecture, planning → development, development → acceptance, and any specialist-to-specialist handoffs) auto-advance via handoff tools. Middleware gates on handoff tools enforce prerequisite checks (e.g., PRD finalized before `(PM, HE, deliver)`) but do not require user approval.

#### PCG State Growth and Parent-to-Child Context Propagation

**Child agents do not see PCG state.** LangGraph maps parent state to child graph input by shared key names only. The Deep Agent input schema (`_InputAgentState`) defines a single key: `messages`. The implementation MUST set `input_schema=_InputAgentState` on each `add_node` call for mounted child graphs — without this, LangGraph defaults to passing the full parent state schema, which would leak PCG-private keys into child agents. The `run_agent` node controls exactly what enters the child's `messages` input (a single `HumanMessage` constructed from `pending_handoff.brief`).

**`messages` growth is bounded by design.** The `messages` key accumulates only lifecycle bookends — stakeholder input and the PM's final product response. It never grows during pipeline execution. Over a project thread's lifetime, `messages` contains at most 2 entries per lifecycle cycle (one `HumanMessage` in, one `AIMessage` out), plus any follow-up re-invocations.

**Unbounded handoff log growth is a persistence concern, not a context-flooding concern.** The handoff log accumulates in the PCG's own checkpoint state. Child agents never read it. However, an unbounded log bloats checkpoint storage over time. The AD mandates a cap strategy; the exact mechanism is delegated to the implementation spec:

- **v1:** Cap the handoff log to the last N records per project thread. The cap threshold N is a runtime constant. The mitigation mechanism for records that exceed the cap is delegated to the implementation spec (options: summarize into a string field, migrate to LangGraph Store, or discard with a count marker).
- **v2 option:** Move the full handoff history to the LangGraph `Store` (key-value) instead of the PCG state, so the PCG state never grows. The `run_agent` node and middleware can query the store on demand.

**Child agent message compaction** is handled by the Deep Agents `SummarizationMiddleware`, which is already in every agent's middleware stack. No additional compaction mechanism is needed at the PCG level for child agent context.

#### Gate-Ownership Boundary: Harness Engineer vs Evaluator

The two QA-gate roles own orthogonal dimensions of target-application quality:

| Gate Owner | Dimension | Evaluates | Does not evaluate |
|---|---|---|---|
| **Harness Engineer** | Target *harness* (LLM agent behavior) | Eval rubric validity, dataset coverage, judge calibration, trajectory quality, scenario testing (binary + Likert) | Code style, SDK conventions, UI functionality |
| **Evaluator** | Target *application* (code/software behavior) | Spec-code alignment, naming/SDK conventions, UI/UX functionality, feature completeness, integration correctness | Eval science, rubric design, judge calibration |

**Conditional scope:** The Harness Engineer only gates when the target application includes an LLM/harness component. If no target harness exists, the Evaluator covers all dimensions.

**Routing enforcement:** The Developer system prompt encodes which tool to call for which gate dimension (`submit_phase_to_harness_engineer` for target-harness concerns, `submit_phase_to_evaluator` for target-application concerns). The AD defines the boundary; the prompt owns the routing.

#### Handoff Tool Use-Case Matrix

Tools are organized into six categories by transition type. The naming
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
| 10 | `return_product_to_pm` | `return` | Developer | PM | Finished product + final artifacts → PM presents to user | Evaluator acceptance required; HE acceptance required if HE participated in project |

**Acceptance** — QA agents submit acceptance stamps (non-blocking); Developer's `return_product_to_pm` gate reads these:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 11 | `submit_harness_acceptance` | `submit` | HE | PM | Acceptance stamp: target harness quality verified | None (stamp only) |
| 12 | `submit_application_acceptance` | `submit` | Evaluator | PM | Acceptance stamp: target application quality verified | None (stamp only) |

**Acceptance gate logic for `return_product_to_pm`:** The middleware gate on this tool checks `handoff_log` for acceptance stamps before allowing the handoff through. Evaluator acceptance is always required. Harness Engineer acceptance is required only if the HE was ever invoked in the project thread — the gate derives HE relevance by scanning `handoff_log` for any record with `source_agent == "harness_engineer"` or `target_agent == "harness_engineer"`. If no HE participation is found, the HE acceptance check is skipped. This avoids adding a `has_target_harness` state key.

**Stage Review** — Specialist submits work to HE for eval coverage:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 13 | `submit_spec_to_harness_engineer` | `submit` | Architect | HE | Design spec → evalability review + dev-phase eval harness (Stage 2 intervention) | Spec accepted |
| 14 | `return_eval_coverage_to_architect` | `return` | HE | Architect | Eval coverage for new components + dev-phase eval criteria | None |

**Phase Review** — Developer submits phase deliverables for QA:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 15 | `announce_phase_to_evaluator` | `announce` | Developer | Evaluator | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 16 | `announce_phase_to_harness_engineer` | `announce` | Developer | HE | Phase intent + eval criteria acknowledgment → "agreed, awaiting submission" | None |
| 17 | `submit_phase_to_evaluator` | `submit` | Developer | Evaluator | Phase deliverables → pass/fail findings, spec/plan compliance report | Deliverables match plan |
| 18 | `submit_phase_to_harness_engineer` | `submit` | Developer | HE | Phase deliverables → EBDR-1 feedback packet (eval science findings, no scoring logic leaked) | None |

**Specialist Consultation** — Non-ownership-transfer expert input:

| # | Tool | `reason` | Caller | Target | Artifact Flow | Middleware Gate |
|---|---|---|---|---|---|---|
| 19 | `consult_harness_engineer_on_gates` | `consult` | Planner | HE | Plan draft → eval gate placement recommendations (Stage 3 intervention) | None |
| 20 | `consult_evaluator_on_gates` | `consult` | Planner | Evaluator | Plan draft → acceptance gate placement recommendations | None |
| 21 | `request_research_from_researcher` | `consult` | Architect, HE, PM | Researcher | Research question → targeted findings | None |
| 22 | `ask_pm` | `question` | Any specialist | PM | Stakeholder question → answer/clarification | None |
| 23 | `coordinate_qa` | `coordinate` | HE ↔ Evaluator | Evaluator ↔ HE | QA findings → aligned review strategy | None |

#### Agent-Scoped Tool Ownership

Each agent only receives the tools relevant to its role. An agent cannot call a
tool it does not own.

| Agent | Pipeline Delivery | Pipeline Return | Acceptance | Stage Review | Phase Review | Consultation |
|---|---|---|---|---|---|---|
| PM | `deliver_prd_to_harness_engineer`, `deliver_prd_to_researcher`, `deliver_design_package_to_architect`, `deliver_planning_package_to_planner`, `deliver_development_package_to_developer` | — | `submit_harness_acceptance` (receives), `submit_application_acceptance` (receives) | — | — | `request_research_from_researcher` |
| Harness Engineer | — | `return_eval_suite_to_pm`, `return_eval_coverage_to_architect` | `submit_harness_acceptance` | `submit_spec_to_harness_engineer` (receives) | `announce_phase_to_harness_engineer` (receives), `submit_phase_to_harness_engineer` (receives) | `consult_harness_engineer_on_gates` (receives), `request_research_from_researcher`, `coordinate_qa` |
| Researcher | — | `return_research_bundle_to_pm` | — | — | — | `request_research_from_researcher` (receives) |
| Architect | — | `return_design_package_to_pm` | — | `submit_spec_to_harness_engineer` | — | `request_research_from_researcher` |
| Planner | — | `return_plan_to_pm` | — | — | — | `consult_harness_engineer_on_gates`, `consult_evaluator_on_gates` |
| Developer | — | `return_product_to_pm` | — | — | `announce_phase_to_evaluator`, `announce_phase_to_harness_engineer`, `submit_phase_to_evaluator`, `submit_phase_to_harness_engineer` | `ask_pm` |
| Evaluator | — | — | `submit_application_acceptance` | — | `announce_phase_to_evaluator` (receives), `submit_phase_to_evaluator` (receives) | `consult_evaluator_on_gates` (receives), `coordinate_qa` |

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
                    │
                    │  ... final phase complete ...
                    │
                    ├─ submit_application_acceptance ←── Evaluator (non-blocking stamp)
                    ├─ submit_harness_acceptance ←── HE (non-blocking stamp, conditional)
                    │
                    ├─ return_product_to_pm (gated by acceptance stamps)
                    │
              ← PM presents finished product to user
              PM uses ask_user → user satisfied → PM finishes → END

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
    builder.add_node("process_handoff", process_handoff)
    builder.add_node("run_agent", run_agent)
    builder.add_edge(START, "process_handoff")
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

- `process_handoff`: On first invocation (no pending handoff): accept stakeholder
  input, set `current_agent` to PM, create a synthetic handoff record. On
  subsequent invocations: record the handoff, ensure the target role's checkpoint
  namespace and workspace paths are initialized, and prepare the invocation payload.
- `run_agent`: Construct a single `HumanMessage` from `pending_handoff.brief` and
  invoke the target mounted Deep Agent child graph using the parent project thread
  and target role namespace. Clear `pending_handoff` on completion.

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
    U["User / UI"] --> PCG["LangGraph Project Coordination Graph\n2 nodes: process_handoff, run_agent\nthread: project_id"]
    PCG -->|"process_handoff → run_agent"| PM["PM Deep Agent\nnamespace: project_manager"]

    PCG -->|"process_handoff → run_agent"| HE["Harness Engineer\nnamespace: harness_engineer"]
    PCG -->|"process_handoff → run_agent"| R["Researcher\nnamespace: researcher"]
    PCG -->|"process_handoff → run_agent"| A["Architect\nnamespace: architect"]
    PCG -->|"process_handoff → run_agent"| PL["Planner\nnamespace: planner"]
    PCG -->|"process_handoff → run_agent"| D["Developer\nnamespace: developer"]
    PCG -->|"process_handoff → run_agent"| E["Evaluator\nnamespace: evaluator"]

    PM -->|"deliver_prd_to_* / return_*_to_pm"| PCG
    A -->|"submit_spec_to_harness_engineer"| PCG
    HE -->|"ask_pm / return_eval_*"| PCG
    D -->|"submit_phase_to_* / return_product_to_pm"| PCG
    E -->|"submit_application_acceptance"| PCG
    HE -->|"submit_harness_acceptance"| PCG

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
    PCG->>PM: process_handoff → run_agent(PM)
    PM->>PCG: deliver_prd_to_harness_engineer(Command.PARENT)
    PCG->>FS: Append handoff record and artifact paths
    PCG->>HE: process_handoff → run_agent(HE)
    HE-->>PCG: return_eval_suite_to_pm(Command.PARENT)

    alt Stakeholder clarification needed
        HE->>PCG: ask_pm(Command.PARENT)
        PCG->>PM: process_handoff → run_agent(PM)
        PM->>User: ask_user middleware (scoped clarification)
        User-->>PM: Answer
        PM-->>PCG: deliver_prd_to_harness_engineer(Command.PARENT)
        PCG->>HE: process_handoff → run_agent(HE, resume)
    end

    PM->>PCG: deliver_prd_to_researcher(Command.PARENT)
    PCG->>R: process_handoff → run_agent(Researcher)
    R-->>PCG: return_research_bundle_to_pm(Command.PARENT)

    PM->>PCG: deliver_design_package_to_architect(Command.PARENT)
    PCG->>A: process_handoff → run_agent(Architect)
    A->>PCG: submit_spec_to_harness_engineer(Command.PARENT)
    PCG->>HE: process_handoff → run_agent(HE, Stage 2)
    HE-->>PCG: return_eval_coverage_to_architect(Command.PARENT)
    PCG->>A: process_handoff → run_agent(Architect, resume)
    A-->>PCG: return_design_package_to_pm(Command.PARENT)

    PM->>PCG: deliver_planning_package_to_planner(Command.PARENT)
    PCG->>PL: process_handoff → run_agent(Planner)
    PL-->>PCG: return_plan_to_pm(Command.PARENT)

    PM->>PCG: deliver_development_package_to_developer(Command.PARENT)
    PCG->>D: process_handoff → run_agent(Developer)

    D->>PCG: submit_phase_to_evaluator(Command.PARENT)
    PCG->>E: process_handoff → run_agent(Evaluator)
    E-->>PCG: pass/fail findings (Command.PARENT)
    PCG->>D: process_handoff → run_agent(Developer, resume)

    Note over D,E: ... repeat for each development phase ...

    E->>PCG: submit_application_acceptance(Command.PARENT)
    HE->>PCG: submit_harness_acceptance(Command.PARENT)
    D->>PCG: return_product_to_pm(Command.PARENT, gated by acceptance stamps)
    PCG->>PM: process_handoff → run_agent(PM)

    PM->>User: Present finished product
    PM->>User: ask_user (satisfaction check)
    User-->>PM: Satisfied
    PM-->>PCG: PM finishes normally → END

    PCG->>LS: Emit correlation metadata
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

## 5) Implementation Plan

The implementation plan (Upon Approval will be transfered to) is decomposed into three spec documents under `docs/spec/`:

1. **Requirements Document** — EARS-format functional and non-functional requirements derived from this AD.
2. **Design Document** — Technical design derived from the requirements: TypedDict/Pydantic wire formats, middleware dispatch tables, system prompt behavioral contracts, tool schemas, and integration patterns.
3. **Task Document** — Phased task list derived from the design document: ordered implementation work items with acceptance criteria.

These three documents, together with this AD, form the four sources of truth for v1 development.

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

v1 is a local-first CLI TUI application running on the user's machine. Security and compliance considerations for v1:

- Data classification: `internal` by default — project artifacts, eval datasets, and agent state live on the user's local filesystem or in a locally-managed sandbox.
- PII handling: Agent prompts and tools must not log or transmit stakeholder PII to external services beyond the LLM API call. The AD does not mandate PII detection in v1; this is a prompt/tool design concern for the spec.
- Access model: Single-user local execution. No multi-tenant access control in v1.
- Retention policy: User-managed. The local SqliteSaver checkpoint database and filesystem artifacts persist until the user deletes them. No automatic retention policy in v1.

Web application deployment, multi-tenant access control, and compliance hardening are v2+ concerns.

---
 
## 9) Open Questions

> **Closed decisions** are archived in [DECISIONS.md](./DECISIONS.md). **Changelog** is archived in [CHANGELOG.md](./CHANGELOG.md).

**Agent primitive decisions (closed 2026-04-13):**

- [x] **Q8: Extended middleware per agent.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md).
- [x] **Q9: Middleware dispatch table.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md).
- [x] **Q10: Tool schema contracts.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md).
- [x] **Q11: Model selection per agent.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md).
- [x] **Q13: Anthropic provider-specific middleware integration.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md). Adopt `ClaudeBashToolMiddleware` and `FilesystemClaudeMemoryMiddleware` via Anthropic provider profile; reject text editor and file search middleware (overlap with `FilesystemMiddleware`); two-layer memory architecture (AGENTS.md = long-term, `/memories/` = short-term); server-side tools deferred to v2.
- [x] **Q12: System prompt behavioral contracts.** Closed 2026-04-13 → archived in [DECISIONS.md](./DECISIONS.md). External `.md` files next to each agent factory (not hardcoded). AD locks behavioral invariants (must-recognize, must-not-do, self-awareness triggers); prompt text is spec territory. Per-role `MEMORY_SYSTEM_PROMPT` tuning. Autonomous mode auto-approves user-approval gates.

---

## 10) Changelog

> Archived in [CHANGELOG.md](./CHANGELOG.md). New entries must be appended there, not here.

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
