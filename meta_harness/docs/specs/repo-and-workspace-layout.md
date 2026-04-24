---
doc_type: spec
derived_from:
  - AD §4 Full Repo Structure Naming Decision
  - AD §4 LangGraph Project Coordination Graph Factory Contract
  - AD §4 Project Workspace and Memory Structure Proposal
status: active
last_synced: 2026-04-26
owners: ["@Jason"]
---

# Repository and Workspace Layout Specification

> **Provenance:** Derived from `AD.md §4 Full Repo Structure Naming Decision`, `§4 LangGraph Project Coordination Graph Factory Contract`, and `§4 Project Workspace and Memory Structure Proposal`.  
> **Status:** Active · **Last synced with AD:** 2026-04-25 (updated for `OQ-HO` resolution: 1 dispatcher + 7 mounted role subgraph nodes; `ROLE_GRAPHS` registry consumed at graph-construction time; **corrected routing primitive from string `goto` to `Send` for explicit child input injection per Ticket 1**; **added persistence contract for mounted role subgraphs per Ticket 3**).  
> **Consumers:** Developer (scaffolding, file creation), Evaluator (structural conformance).

## 1. Purpose

The parent AD locks the naming decisions for the Meta Harness repository
and the on-disk project workspace layout: `agents/` for peer specialists
(not `subagents/`), root `graph.py` as the PCG entrypoint, role-scoped
memory filesystems, and direct SDK abstraction imports at the consuming
boundary rather than app-owned wrapper modules. This spec renders those
decisions into the concrete trees and factory shape a developer can
scaffold against.

## 2. Repository Structure

```txt
meta-harness/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── AD.md
├── langgraph.json
├── graph.py                          # LangGraph Project Coordination Graph entrypoint/factory
├── docs/
│   ├── specs/
│   └── archive/
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

### 2.1 Naming choices embedded in this tree

- Use root `graph.py` for the deterministic LangGraph Project Coordination
  Graph. This mirrors the LangGraph and Deep Agents CLI graph-entrypoint
  convention while preventing a premature `project_coordination_graph/`
  package from spreading the routing logic across files before the first
  implementation proves its shape.
- Put the PCG `StateGraph` state schema, node functions, conditional
  routing, handoff record helpers, phase-gate transitions, project thread
  and role checkpoint namespace helpers, and compile call in root
  `graph.py` initially. Split only after the file has a concrete pressure
  point, such as shared typed contracts needed outside graph tests,
  sandbox integration wiring, or a production persistence adapter. (*If the need for this surfaces, you must run this past Jason.*)
- Use `integrations/` for sandbox provider wiring. Mirror the Deep Agents
  CLI convention: keep the provider interface in `sandbox_provider.py`,
  create or connect to sandbox backends through `sandbox_factory.py`, and
  pass the resulting SDK backend into the owning agent/PCG construction
  path.
- Construct backend, checkpointer, store, model, and middleware
  configuration at the SDK boundary that consumes it: the role Deep Agent
  factory, the root PCG factory, or the CLI-aligned sandbox integration
  package. Import SDK abstractions directly instead of wrapping them
  behind app-owned convention files.
- Keep `tools/` for now, but do not name nested tool modules until
  concrete tool contracts exist.

## 3. PCG Factory Contract

The PCG is a LangGraph application boundary. It is not a Deep Agent and it
is not an agent registry. After the `OQ-HO` rewrite (2026-04-22, corrected
same day), the PCG has exactly 2 nodes: `dispatch_handoff` plus 7 mounted role
Deep Agent subgraph nodes. The dispatcher routes via
`Command(goto=Send(target_agent, {"messages": [handoff_message]}))`; role
subgraph handoff tools emit `Command(graph=PARENT, goto="dispatch_handoff",
update={...})` which bubbles back through Pregel's namespace hierarchy.
`Send` is required (not string `goto`) because the Deep Agent's `_InputAgentState`
only accepts `messages` (`.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`),
and `Send.arg` is passed directly as child input (`.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:1002`).
Role graphs are mounted (not `.ainvoke()`'d) because `Command.PARENT` only bubbles
from inside a parent Pregel's namespace
(`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:56-59`);
an `.ainvoke()`'d child runs in a top-level Pregel context and its
`Command.PARENT` emissions raise `InvalidUpdateError`.

Child isolation is structural at the Deep Agent SDK layer: `create_deep_agent()`
declares `input_schema=_InputAgentState` (messages only) and
`output_schema=_OutputAgentState` (messages + optional `structured_response`,
all other keys dropped via `PrivateStateAttr` / `OmitFromOutput`). LangGraph
reads the subgraph's declared `input_schema` automatically on mount
(`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1306-1314`),
so no `input_schema=` parameter is needed on `add_node`.

A tasteful first implementation keeps this in root `graph.py`:

```python
from langgraph.graph import StateGraph, START
from langgraph.pregel import Pregel

from meta_harness.agents.project_manager.agent import create_project_manager_agent
from meta_harness.agents.harness_engineer.agent import create_harness_engineer_agent
from meta_harness.agents.researcher.agent import create_researcher_agent
from meta_harness.agents.architect.agent import create_architect_agent
from meta_harness.agents.planner.agent import create_planner_agent
from meta_harness.agents.developer.agent import create_developer_agent
from meta_harness.agents.evaluator.agent import create_evaluator_agent


def _build_role_graphs() -> dict[str, Pregel]:
    """In-process registry of compiled role Deep Agent graphs.

    Used at graph-construction time to mount each role as a subgraph node.
    The dispatcher routes into these nodes via Command(goto=<role_name>);
    it never invokes them directly.

    Persistence contract: each role is compiled with checkpointer=None to
    inherit the parent PCG's checkpointer at runtime. LangGraph's mounted-subgraph
    persistence uses the parent thread_id with a stable child checkpoint_ns
    derived from the node name. The stable namespace is the recast checkpoint
    namespace (role name without task ID), which LangGraph uses when resolving
    checkpoint storage for subgraphs with inherited checkpointers. This ensures
    repeated handoffs to the same role resume from the stable namespace under
    the same project_thread_id.

    Inheritance mechanism: checkpointer=None does NOT bind the parent's checkpointer
    instance at graph-construction time. Instead, LangGraph propagates the parent's
    checkpointer to child subgraphs at runtime via CONFIG_KEY_CHECKPOINTER config
    propagation. The parent Pregel passes its checkpointer in the task config
    (_algo.py:715-718), and the child retrieves it from config with fallback to
    self.checkpointer (main.py:1265-1266). When querying a subgraph's state,
    the parent explicitly patches the config to pass its checkpointer
    (main.py:1279-1281). The child's compiled checkpointer=None enables this
    runtime inheritance by signaling "use the checkpointer from config."
    (SDK verification: types.py:96-102 defines Checkpointer type with None=inherit;
    state.py:1060 documents runtime inheritance; _algo.py:592-602 constructs task
    namespaces; _config.py:34-45 defines recast_checkpoint_ns; _algo.py:715-718
    shows CONFIG_KEY_CHECKPOINTER propagation during task execution;
    main.py:1265-1266 shows checkpointer resolution from config;
    main.py:1279-1281 shows parent patching config for subgraph state queries.)
    """
    return {
        "project_manager": create_project_manager_agent(checkpointer=None),
        "harness_engineer": create_harness_engineer_agent(checkpointer=None),
        "researcher": create_researcher_agent(checkpointer=None),
        "architect": create_architect_agent(checkpointer=None),
        "planner": create_planner_agent(checkpointer=None),
        "developer": create_developer_agent(checkpointer=None),
        "evaluator": create_evaluator_agent(checkpointer=None),
    }


ROLE_GRAPHS = _build_role_graphs()


def make_graph(...) -> CompiledStateGraph:
    builder = StateGraph(
        ProjectCoordinationState,  # from pcg-data-contracts.md
        context_schema=ProjectCoordinationContext,  # from pcg-runtime-contract.md
        input_schema=ProjectCoordinationInput,  # from pcg-runtime-contract.md
        output_schema=ProjectCoordinationOutput,  # from pcg-runtime-contract.md
    )

    # Coordination node — returns Command(goto=<role>) to route.
    # Uses node-level input schema to access bootstrap fields.
    # See pcg-runtime-contract.md §8 for input-to-state mapping details.
    builder.add_node("dispatch_handoff", dispatch_handoff, input_schema=DispatchHandoffInput)

    # Role Deep Agents mounted as subgraph nodes. No input_schema= needed —
    # each compiled Deep Agent declares _InputAgentState internally, and
    # LangGraph honors that on mount. Command.PARENT bubbles natively from
    # inside these subgraphs.
    for role_name, role_graph in ROLE_GRAPHS.items():
        builder.add_node(role_name, role_graph)

    builder.add_edge(START, "dispatch_handoff")
    # Zero static edges between dispatcher and roles — all routing is via
    # Command(goto=...) emissions.

    return builder.compile(
        checkpointer=checkpointer,
        store=store,
        name="meta-harness-project-coordination-graph",
    )


graph = make_graph
```

`make_graph()` is the preferred factory shape because the Deep Agents
deploy template uses an async `make_graph(config, runtime)` factory when
graph construction needs runtime config, while the CLI server also
supports a module-level `graph` export. The root `langgraph.json` can
point to either `./graph.py:graph` or `./graph.py:make_graph`; prefer
`./graph.py:make_graph` if the PCG needs invocation-time config/runtime,
otherwise `./graph.py:graph` is simpler. The role factories use
`create_<role>_agent()` returning Deep Agent graphs via
`create_deep_agent()`.

### 3.1 Node responsibilities (deterministic plumbing only)

- `dispatch_handoff` — The sole coordination node. On first invocation
  (empty `handoff_log`): synthesize an initial handoff record from
  stakeholder input, validate, upsert `projects_registry`, return
  `Command(goto=Send("project_manager", {"messages": [handoff_message]}), update={handoff_log, current_agent, current_phase})`.
  On re-entry triggered by a child-emitted
  `Command(graph=PARENT, goto="dispatch_handoff", update={...})`: read
  `handoff_log[-1]`, validate, construct `handoff_message` per
  `pcg-data-contracts.md §8.3`, upsert `projects_registry`, return
  `Command(goto=Send(target_agent, {"messages": [handoff_message]}))`.
  Never invokes role graphs directly — LangGraph handles routing through
  the Pregel loop.
- `project_manager` / `harness_engineer` / `researcher` / `architect` /
  `planner` / `developer` / `evaluator` — Mounted Deep Agent subgraphs.
  Entered via `Command(goto=Send(role_name, {"messages": [handoff_message]}))`.
  The `Send.arg` is passed directly as the child's `messages` input per
  `_InputAgentState` schema. Exit via a handoff tool
  (`Command(graph=PARENT, goto="dispatch_handoff", update={...})`) or, for
  the PM only, the terminal `finish_to_user` tool
  (`Command(graph=PARENT, goto=END, update={"messages": [AIMessage(...)]})`).
  Every role's middleware stack includes a final-turn-guard that re-prompts
  if the agent's last `AIMessage` lacks a tool call to a handoff tool or
  `finish_to_user` — natural completion of a role subgraph is not
  permitted because it would merge the child's conversation history into
  PCG `messages`.

Phase gate enforcement, HITL question surfacing, and routing intelligence
are **not** PCG responsibilities. Phase gates are middleware hooks on
handoff tools. HITL questions are handled by the `ask_user` middleware
provided by the Deep Agents SDK (found in the `deepagents_cli` module).
Routing decisions are made by the calling agent via tool selection.

See `docs/specs/pcg-data-contracts.md §8` for the `dispatch_handoff`
reference implementation sketch and the full mount-and-route protocol
explanation.

## 4. Project Workspace and Memory Structure

The memory filesystem keeps a role-scoped structure. This tree preserves a
shared team memory file at the root plus per-role `AGENTS.md`, `memory/`,
`skills/`, and project artifact directories. Backend routing maps this
layout onto disk or sandbox storage through SDK backends; the tree
describes workspace semantics, not a new app-owned backend layer. The
`dev/` path is a workspace bucket, not a Python module naming decision.

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
