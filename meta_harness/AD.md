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
Developer, and Evaluator as peer, stateful Deep Agent graphs, coordinated by a
thin LangGraph Project Coordination Graph. The Project Coordination Graph owns
project-scoped thread identity, handoff routing, run status, and phase gates. The
Deep Agent graphs own role-specific cognition, tools, memory, skills,
summarization, and artifact work.
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
| C | PM uses stock `AsyncSubAgent` for each specialist | Supports remote/background execution, status checks, and follow-up updates on the same task thread | `start_async_task` creates a new remote thread each time; not enough by itself for project-scoped specialist identity | `Use only behind a project-aware wrapper` |
| D | Peer `create_deep_agent()` graphs coordinated by a thin LangGraph Project Coordination Graph | Preserves per-agent state, permits direct specialist loops, keeps cognition inside Deep Agents, and makes handoffs observable | Requires a small deterministic coordination layer and thread/run registry | `Selected` |

<details>
<summary><strong>Decision rationale notes</strong> (expand)</summary>

### Why selected option wins

1. It matches the SDK boundary: `create_deep_agent()` already assembles the agent harness and accepts `checkpointer`, `store`, `backend`, `memory`, `skills`, `subagents`, and `name`.
2. It gives every core role a stable project-scoped thread and its own checkpoint history, rather than forcing PM to carry or restate specialist context.
3. It keeps LangGraph focused on deterministic coordination, not role cognition.

### Why alternatives lose

- Option A: Declarative `SubAgent` specs are for isolated tasks, not durable project roles.
- Option B: `CompiledSubAgent` is a useful escape hatch, but the stock `task` tool does not provide the stable runtime config required for project-scoped checkpoint resume.
- Option C: Stock `AsyncSubAgent` is useful for background execution, but the project must wrap or replace its launch path when project-scoped specialist thread IDs are required.

</details>

---

## 4) Architecture

### Runtime Topology Decision

The core topology is:

```txt
Human/UI
  -> PM Deep Agent thread
      -> LangGraph Project Coordination Graph
          -> Harness Engineer Deep Agent thread
          -> Researcher Deep Agent thread
          -> Architect Deep Agent thread
          -> Planner Deep Agent thread
          -> Developer Deep Agent thread
          -> Evaluator Deep Agent thread
```

The PM is the default front door and scope owner, not the container for all
specialist cognition. The specialists are peer Deep Agent graphs. Each role must
be assembled by its own `create_deep_agent()` factory with `name=` set for trace
metadata, its own tool ownership, its own prompt, its own memory sources, and a
checkpointer-backed project thread.

For project-scoped identity, use one stable thread per `(project_id,
agent_name)` pair:

```txt
thread_id = "{project_id}:{agent_name}"
```

The exact string format can change during implementation, but the invariant
cannot: re-invoking the Harness Engineer for the same project must resume the
Harness Engineer's project thread, not the PM thread and not a fresh subagent
thread.

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

- Resolve the target agent for a handoff.
- Compute the project-scoped target `thread_id`.
- Ensure the target thread exists, locally or remotely.
- Invoke the target Deep Agent graph with the stable `thread_id`.
- Track run IDs, handoff status, phase gates, and unresolved questions.
- Route phase transitions when a handoff completes or fails.
- Surface human-in-the-loop questions when an agent cannot proceed without stakeholder input.
- Preserve enough Project Coordination Graph state to reconstruct which agent handed work
  to whom, why, and with which artifact references.

Its non-responsibilities are equally important:

- Do not implement research, architecture, planning, coding, or evaluation logic in LangGraph nodes.
- Do not put all specialist messages into one shared graph state.
- Do not use the PM as a pass-through for every specialist-to-specialist loop.
- Do not reimplement Deep Agents middleware for planning, memory, skills, filesystem access, summarization, or tool calling.

The Project Coordination Graph should be a small `StateGraph` with coarse nodes,
not a large multi-agent monolith. A reasonable conceptual node set is:

| Node | Purpose |
|---|---|
| `receive_user_input` | Accept new stakeholder input and route it to PM when project scope is still being shaped. |
| `run_agent` | Invoke a named Deep Agent with a handoff brief and stable project-scoped thread config. |
| `ensure_thread` | Idempotently create or look up the target local/remote thread before invocation. |
| `record_handoff` | Append a structured handoff record with caller, target, reason, artifact refs, and run ID. |
| `route_after_agent` | Decide whether the next step is another agent, a phase gate, a human question, or done. |
| `gate_phase` | Enforce required review/eval gates before moving from scoping to harness engineering, architecture, planning, development, and final acceptance. |
| `surface_question` | Turn a specialist question into PM or user-facing HITL, then route the answer back to the asking agent's thread. |

This node list is an architecture guide, not a final schema. The final spec
should keep the same separation: deterministic routing in LangGraph, open-ended
work inside Deep Agents.

### Handoff Protocol

All agent-to-agent communication should go through explicit handoff tools or
Project Coordination Graph commands. A handoff should carry:

- `project_id`
- `from_agent`
- `to_agent`
- `reason`
- `brief`
- `artifact_refs`
- `expected_output`
- `blocking`
- `phase`

The receiving agent should get a concise brief plus artifact references, not a
dump of the caller's full conversation. The receiving agent resumes its own
project thread and decides what context to load.

Recommended handoff tools:

| Tool | Caller | Target | Use |
|---|---|---|---|
| `handoff_to_harness_engineer` | PM, Architect, Developer | Harness Engineer | Eval criteria, rubric design, calibration, public/held-out datasets, and milestone evals. |
| `request_research` | Architect, Harness Engineer, PM | Researcher | Targeted SDK/API/model capability research. |
| `handoff_to_architect` | PM, Researcher, Harness Engineer | Architect | Design synthesis from PRD, research, and eval constraints. |
| `handoff_to_planner` | Architect, Harness Engineer | Planner | Convert accepted design and public eval criteria into an implementation plan. |
| `handoff_to_developer` | Planner | Developer | Execute an approved phase plan. |
| `request_evaluation` | Developer, PM | Evaluator and/or Harness Engineer | Validate code/spec alignment and run technical evals. |
| `ask_pm` | Any specialist | PM | Ask stakeholder-facing questions without giving the specialist permanent ownership of PM scope. |

Implementation can expose these as Deep Agent tools, but the tools should call a
shared Project Coordination Graph entrypoint rather than directly invoking arbitrary peers. That
keeps thread ID calculation, run tracking, and phase gating centralized.

### Local and Remote Invocation Modes

Support two invocation modes behind the same handoff interface:

1. Local-first mode: the Project Coordination Graph invokes an in-process compiled Deep Agent
   graph with `agent.ainvoke(input, config={"configurable": {"thread_id":
   thread_id}})`. This is the simplest path for local development and testing.
   The local development harness should also expose the graph through a
   `langgraph.json` + `langgraph dev` workflow so LangGraph Studio can inspect
   local graph behavior, thread state, checkpoints, and routing before the
   remote/sandbox layer is introduced.
2. Remote/sandbox mode: the Project Coordination Graph uses the LangGraph SDK. It should call
   `threads.create(thread_id=thread_id, if_exists="do_nothing", metadata=...)`
   and then `runs.create(thread_id=thread_id, assistant_id=graph_id, input=...,
   multitask_strategy=...)`.

Use `multitask_strategy="enqueue"` when a new handoff should wait behind an
active target run. Use `multitask_strategy="interrupt"` only when the new
message should replace or redirect the active run.

Stock `AsyncSubAgent` remains useful for ad hoc background tasks, but it should
not be the primary project-role topology. Its start path creates a new remote
thread and then stores that generated thread ID as the task ID. That is at odds
with the invariant that every specialist role must resume the same
project-scoped thread.

Remote/sandbox mode is a design spike, not a solved implementation detail. It
crosses at least three abstraction boundaries: Deep Agents sandbox/backends,
LangGraph server/SDK threads and runs, and LangSmith trace/run identity. The
selected architecture requires a project-aware wrapper, but the exact mechanism
should be decided after a narrow prototype proves stable thread reuse, run
queuing, artifact access, interrupt behavior, and trace correlation across one
specialist loop.

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

Do not assume trace hierarchy will automatically remain intact across the
local/remote/sandbox boundary. The Project Coordination Graph must persist handoff records
and propagate correlation metadata so traces can still be stitched together
when a specialist run occurs in a separate process, server, or sandbox.

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

The loop is not a direct shared-memory conversation. It is a sequence of
project-scoped agent thread invocations, linked by handoff records and artifact
references in the Project Coordination Graph.

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
- The lower-level LangGraph SDK supports explicit thread creation and explicit run submission against a chosen thread (`.venv/lib/python3.11/site-packages/langgraph_sdk/_async/threads.py:98-143`, `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py:435-462`, `552-585`).
- The Deep Agents CLI scaffolds `langgraph.json` for `langgraph dev` with a graph entry point and optional checkpointer path (`.reference/libs/cli/deepagents_cli/server.py:85-119`, `.reference/libs/cli/deepagents_cli/server_manager.py:92-115`).
- The Deep Agents CLI server graph is a module-level graph entrypoint: `server_graph.py` builds the graph from environment-backed server config and exports `graph = make_graph()` for the generated `langgraph.json` reference (`.reference/libs/cli/deepagents_cli/server_graph.py:1-10`, `93-196`).
- The Deep Agents CLI server path creates sandbox backends through `deepagents_cli.integrations.sandbox_factory.create_sandbox(...)`, keeps the sandbox context manager open for the server process lifetime, and passes the resulting backend into `create_cli_agent(...)` (`.reference/libs/cli/deepagents_cli/server_graph.py:117-170`, `.reference/libs/cli/deepagents_cli/integrations/sandbox_factory.py:1-134`).
- The Deep Agents CLI names its sandbox integration package `integrations/` and keeps the provider boundary in `sandbox_provider.py`; Meta Harness should follow that package convention instead of inventing a `runtime/sandbox.py` shape (`.reference/libs/cli/deepagents_cli/integrations/__init__.py`, `.reference/libs/cli/deepagents_cli/integrations/sandbox_provider.py:1-49`).
- `create_cli_agent(...)` chooses SDK backends directly: local mode uses `LocalShellBackend` or `FilesystemBackend`, sandbox mode uses the supplied sandbox backend, and any `CompositeBackend` use is an SDK import for routing generated/temporary file areas rather than an app-owned backend module (`.reference/libs/cli/deepagents_cli/agent.py:1104-1218`, `.reference/libs/deepagents/deepagents/backends/composite.py:119-158`).
- The Deep Agents deploy template also uses a graph factory entrypoint: generated `langgraph.json` points to `./deploy_graph.py:make_graph`, and the generated module exposes `graph = make_graph` for runtime factory loading (`.reference/libs/cli/deepagents_cli/deploy/bundler.py:192-201`, `.reference/libs/cli/deepagents_cli/deploy/templates.py:430-469`).
- The deploy template is where the CLI builds a generated backend factory with an SDK `CompositeBackend`, a sandbox default, and store-backed `/memories/` and `/skills/` routes; that pattern should be imported or adapted from the SDK/CLI after a spike, not mirrored as a first-pass `runtime/` package or app-owned `checkpointers.py`, `stores.py`, or `model_policy.py` modules (`.reference/libs/cli/deepagents_cli/deploy/templates.py:199-207`, `405-424`).
- LangGraph API treats callable graph exports as factories, compiles exported `StateGraph` builders automatically, and accepts already-compiled Pregel graphs (`.venv/lib/python3.11/site-packages/langgraph_api/graph.py:330-379`, `730-765`).
- LangGraph SDK assistants use graph IDs that are normally set in `langgraph.json` (`.venv/lib/python3.11/site-packages/langgraph_sdk/_async/assistants.py:320-350`).
- LangGraph local development docs show `langgraph.json` using `"dependencies": ["."]` and graph refs shaped like `"my_agent": "./my_agent/agent.py:graph"`, so a root `./graph.py:graph` or `./graph.py:make_graph` entrypoint is a valid project layout when the root is the app boundary ([LangGraph local development docs](https://docs.langchain.com/langsmith/local-dev-testing)).
- Deep Agents CLI resolves LangSmith thread URLs only when tracing is configured, and its `/trace` flow tells users to set `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` when unavailable (`.reference/libs/cli/deepagents_cli/config.py:1600-1745`, `.reference/libs/cli/deepagents_cli/app.py:2545-2579`).

## Full Repo Structure *Proposal only*

The v1 repo should be organized around peer Deep Agent factories, not around a
PM-owned `subagents/` bucket. The root `graph.py` should be the LangGraph
application entrypoint and the self-contained deterministic Project Coordination Graph
factory. The selected topology makes `agents/` the right module name for core
roles. SDK `SubAgent` dicts, if any are later needed for ephemeral isolated
tasks, should live under a narrowly named `task_agents/` module inside the owning
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
  routing, handoff record helpers, phase-gate transitions, project-role
  `thread_id` helpers, and compile call in root `graph.py` initially. Split only
  after the file has a concrete pressure point, such as shared typed contracts
  needed outside graph tests, a remote SDK client adapter, or a production
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
    builder.add_node("record_handoff", record_handoff)
    builder.add_node("ensure_thread", ensure_thread)
    builder.add_node("run_agent", run_agent)
    builder.add_node("gate_phase", gate_phase)
    builder.add_edge(START, "record_handoff")
    builder.add_edge("record_handoff", "ensure_thread")
    builder.add_edge("ensure_thread", "run_agent")
    builder.add_conditional_edges("run_agent", route_after_agent)
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

The Project Coordination Graph nodes should only do deterministic coordination:

- `record_handoff`: persist or append a handoff record.
- `ensure_thread`: compute and ensure the target project-role `thread_id`.
- `run_agent`: invoke a peer Deep Agent locally or submit a remote run using the
  stable target thread.
- `gate_phase`: enforce deterministic pass/fail transition policy from recorded
  Evaluator or Harness Engineer results.
- `surface_question`: route a specialist's stakeholder question to PM or UI.

The Project Coordination Graph must not implement research, architecture, planning,
development, eval-science, prompt composition, or provider/model request policy.
Those remain in peer Deep Agent factories, SDK configuration calls, and
tool/prompt contracts. Do not create a runtime policy package before a concrete
SDK-aligned need appears.

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
    U["User / UI"] --> PM["PM Deep Agent\nthread: project:pm"]
    PM --> PCG["LangGraph Project Coordination Graph\nthreads, handoffs, phase gates"]

    PCG --> HE["Harness Engineer\nthread: project:harness-engineer"]
    PCG --> R["Researcher\nthread: project:researcher"]
    PCG --> A["Architect\nthread: project:architect"]
    PCG --> PL["Planner\nthread: project:planner"]
    PCG --> D["Developer\nthread: project:developer"]
    PCG --> E["Evaluator\nthread: project:evaluator"]

    A -->|"request_research"| PCG
    HE -->|"ask_pm / evalability question"| PCG
    D -->|"request_evaluation"| PCG
    E -->|"pass/fail + findings"| PCG

    PCG --> FS["Project Artifacts\nPRD, design, plans, evals, datasets"]
    PCG --> LG["LangGraph Server\nlanggraph.json graph IDs"]
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

    User->>PM: Scope request and requirements
    PM->>PCG: handoff_to_harness_engineer(project_id, brief, artifact_refs)
    PCG->>FS: Append handoff record and artifact refs
    PCG->>HE: Invoke stable project-role thread
    HE-->>PCG: Eval criteria, rubrics, dataset questions

    alt Stakeholder clarification needed
        PCG->>PM: surface_question(question, asking_agent)
        PM->>User: Ask scoped clarification
        User-->>PM: Answer
        PM-->>PCG: Answer with project context
        PCG->>HE: Resume same Harness Engineer thread
    end

    PCG->>A: Invoke Architect with PRD and eval refs
    A->>PCG: request_research(targeted_gap, artifact_refs)
    PCG->>R: Invoke Researcher stable project-role thread
    R-->>PCG: Research bundle refs
    PCG-->>A: Resume Architect thread with research refs
    A-->>PCG: Design/spec artifact refs
    PCG->>PL: Invoke Planner stable project-role thread
    PL-->>PCG: Phase plan refs
    PCG->>D: Invoke Developer stable project-role thread
    D->>PCG: request_evaluation(phase, artifact_refs)

    par Implementation acceptance
        PCG->>E: Invoke Evaluator stable project-role thread
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

The exact Pydantic or `TypedDict` contracts should be defined in the
implementation spec. For this AD, the minimum proposed Project Coordination Graph handoff
record is:

```json
{
  "project_id": "string",
  "handoff_id": "string",
  "source_agent": "project-manager|harness-engineer|researcher|architect|planner|developer|evaluator",
  "target_agent": "project-manager|harness-engineer|researcher|architect|planner|developer|evaluator",
  "target_thread_id": "{project_id}:{target_agent}",
  "reason": "string",
  "artifact_refs": ["string"],
  "run_id": "string|null",
  "status": "queued|running|blocked|failed|completed",
  "question": "string|null",
  "created_at": "RFC3339 timestamp"
}
```

This is a proposed minimum, not a final wire format.

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
- Stable `thread_id` metadata on every project-role run.
- LangGraph Studio local inspection path through `langgraph.json` and `langgraph dev`.
- LangSmith thread/run links exposed in the UI when tracing is configured.
- Evaluation feedback from Harness Engineer and Evaluator kept separate by owner and gate type.

### Success Criteria

| Metric | Baseline | Target | Window |
|---|---|---|---|
| Project-role thread reuse | No stable baseline | Same `(project_id, agent_name)` resumes the same LangGraph thread | Every handoff |
| Handoff traceability | Manual reconstruction | Each handoff has a Project Coordination Graph record and a LangSmith run/thread reference when configured | Every handoff |
| Developer gate routing | Ambiguous `request_evaluation` target | Developer can distinguish Harness Engineer scientific eval issues from Evaluator implementation/spec acceptance issues | Every phase gate |
| Local dev inspection | Ad hoc terminal logs | A local `langgraph dev` workflow can inspect the Project Coordination Graph in LangGraph Studio | Before remote/sandbox spike |

### Validation Plan

1. Prove local-first PM -> Harness Engineer -> PM with stable threads, visible checkpoints, and LangSmith metadata.
2. Prove Architect -> Researcher -> Architect without PM mediation.
3. Prove Developer -> Evaluator -> Developer and Developer -> Harness Engineer -> Developer route to different gate owners.
4. Only after local-first validation, run a narrow remote/sandbox spike that exercises one specialist loop with explicit thread IDs, queued runs, artifact access, and trace correlation.

---

## 7) Risks, Tradeoffs, and Mitigations

> [!WARNING]
> List realistic failure modes, not generic statements.

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Core specialists accidentally implemented as ephemeral `task` subagents | `M` | `H` | Treat `task` as an isolated-worker tool only. Add tests or trace checks that core roles receive stable project-scoped `thread_id`s. | `@Jason` |
| Stock `AsyncSubAgent` creates fresh remote threads for project-role work | `M` | `H` | Use a project-aware handoff wrapper that calls LangGraph SDK thread creation with explicit `thread_id` and `if_exists="do_nothing"`. | `@Jason` |
| Remote/sandbox handoff layer is underestimated | `H` | `H` | Treat as a separate spike. Prove one loop before committing to module names, tool contracts, or production async behavior. | `@Jason` |
| LangGraph Project Coordination Graph grows into a second agent brain | `M` | `M` | Keep LangGraph nodes deterministic and coarse. Deep Agents own cognition; LangGraph owns routing, state, and gates. | `@Jason` |
| Handoff loops become invisible or hard to debug | `M` | `H` | Persist structured handoff records with caller, target, reason, artifact refs, run ID, and resulting gate decision. | `@Jason` |
| LangSmith traces fragment across local, server, and sandbox execution | `M` | `H` | Standardize correlation metadata and expose LangSmith links from the UI. Do not depend on implicit parent/child trace structure across process boundaries. | `@Jason` |
| Developer confuses Harness Engineer feedback with Evaluator feedback | `M` | `M` | Encode the owner split in Developer prompt/tool descriptions and phase-gate records. | `@Jason` |
| Parallel updates interrupt active specialist work unexpectedly | `M` | `M` | Default to queued follow-up runs; reserve interrupt strategy for explicit redirects or stale work cancellation. | `@Jason` |

---

## 8) Security / Privacy / Compliance

- Data classification: `<public/internal/restricted>`
- PII handling: `<none / masked / encrypted>`
- Access model: `<RBAC details>`
- Retention policy: `<duration + deletion mechanism>`

---

## 9) Open Questions

- [ ] Jason approval: adopt the section 4 repo-structure proposal that uses root `graph.py` for the LangGraph Project Coordination Graph entrypoint, uses `agents/` for peer role modules, reserves `task_agents/` for ephemeral SDK `SubAgent` helpers, uses `developer/` as the canonical Developer module name, and follows the Deep Agents CLI `integrations/` sandbox convention.
- [ ] Decide the production checkpointer and store backend for local-first and remote/sandbox modes.
- [ ] Decide whether the project-aware handoff wrapper is implemented as a LangGraph Project Coordination Graph node, a tool service, custom Deep Agents middleware, or a combination.
- [ ] Define the minimal handoff record schema and phase gate enum in the implementation spec.
- [ ] Decide how LangSmith thread/run links will be exposed in the UI for each project-role thread.
- [ ] Define the `langgraph.json` graph ID convention for PM, Project Coordination Graph, and specialist agents in local development.
- [ ] Spike the remote/sandbox handoff path across Deep Agents backends, LangGraph SDK thread/run APIs, and LangSmith trace correlation.
- [ ] Decide whether the Harness Engineer vs Evaluator gate-owner boundary belongs in this AD, a Developer prompt spec, or a separate evaluation architecture spec.

---

## 10) Changelog

| Date | Author | Change |
|---|---|---|
| `2026-04-11` | `@Codex` | Locked the committed `Project Coordination Graph` naming decision and `ProjectCoordination*` schema prefix. |
| `2026-04-11` | `@Codex` | Replaced the placeholder data-contract block with a proposed Project Coordination Graph handoff record shape. |
| `2026-04-11` | `@Codex` | Adopted `Project Coordination Graph` as the name for the thin LangGraph orchestration layer. |
| `2026-04-11` | `@Codex` | Restored Jason's original role-scoped memory filesystem proposal. |
| `2026-04-11` | `@Codex` | Changed ADR status to Proposed and replaced the generic sequence diagram with the Meta Harness handoff flow. |
| `2026-04-11` | `@Codex` | Replaced first-pass `runtime/` module proposal with the Deep Agents CLI `integrations/` sandbox convention. |
| `2026-04-11` | `@Codex` | Revised repo proposal to use root `graph.py` as the LangGraph Project Coordination Graph entrypoint and added graph factory evidence from Deep Agents CLI and LangGraph API source. |
| `2026-04-11` | `@Codex` | Proposed peer-agent repo structure and project workspace layout; left final module naming pending Jason approval. |
| `2026-04-11` | `@Codex` | Added LangSmith tracing, LangGraph Studio, remote/sandbox spike, and Developer gate-owner guidance. |
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
