---
doc_type: spec
derived_from:
  - AD §4 Full Repo Structure Naming Decision
  - AD §4 LangGraph Project Coordination Graph Factory Contract
  - AD §4 Project Workspace and Memory Structure Proposal
status: active
last_synced: 2026-04-22
owners: ["@Jason"]
---

# Repository and Workspace Layout Specification

> **Provenance:** Derived from `AD.md §4 Full Repo Structure Naming Decision`, `§4 LangGraph Project Coordination Graph Factory Contract`, and `§4 Project Workspace and Memory Structure Proposal`.  
> **Status:** Active · **Last synced with AD:** 2026-04-22 (updated for `OQ-HO` resolution: 1 dispatcher + 7 mounted role subgraph nodes; `ROLE_GRAPHS` registry consumed at graph-construction time).  
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
same day), the PCG has **1 coordination node (`dispatch_handoff`) + 7
mounted role Deep Agent subgraph nodes**. The dispatcher routes via
`Command(goto=<target_agent>)`; role subgraph handoff tools emit
`Command(graph=PARENT, goto="dispatch_handoff", update={...})` which
bubbles back through Pregel's namespace hierarchy. Role graphs are mounted
(not `.ainvoke()`'d) because `Command.PARENT` only bubbles from inside a
parent Pregel's namespace (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/_io.py:56-59`);
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
    """
    return {
        "project_manager": create_project_manager_agent(),
        "harness_engineer": create_harness_engineer_agent(),
        "researcher": create_researcher_agent(),
        "architect": create_architect_agent(),
        "planner": create_planner_agent(),
        "developer": create_developer_agent(),
        "evaluator": create_evaluator_agent(),
    }


ROLE_GRAPHS = _build_role_graphs()


def make_graph(...) -> CompiledStateGraph:
    builder = StateGraph(
        ProjectCoordinationState,
        context_schema=ProjectCoordinationContext,
        input_schema=ProjectCoordinationInput,
        output_schema=ProjectCoordinationOutput,
    )

    # Coordination node — returns Command(goto=<role>) to route.
    builder.add_node("dispatch_handoff", dispatch_handoff)

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
  stakeholder input on `messages`, upsert `projects_registry`, return
  `Command(goto="project_manager", update={handoff_log, current_agent, current_phase})`.
  On re-entry triggered by a child-emitted
  `Command(graph=PARENT, goto="dispatch_handoff", update={...})`: read
  `handoff_log[-1]`, upsert `projects_registry`, return
  `Command(goto=<target_agent>)`. Never invokes role graphs directly —
  LangGraph handles routing through the Pregel loop.
- `project_manager` / `harness_engineer` / `researcher` / `architect` /
  `planner` / `developer` / `evaluator` — Mounted Deep Agent subgraphs.
  Entered via `Command(goto=<role_name>)`. Exit via a handoff tool
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
