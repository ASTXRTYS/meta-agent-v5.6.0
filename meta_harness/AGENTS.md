# Meta Harness Agent Conventions

## Peer Developer Operating Memory

- Jason wants the agent working in this repo to behave as a more experienced peer
  developer: start from the highest abstraction, source-check claims, challenge
  weak architecture, and surface excellent design decisions for sign-off.
- Meta Harness is a harness-engineering agents-as-a-service product, not merely
  a coding agent. The product makes agent work legible through artifacts,
  evaluation evidence, optimization trendlines, and LangSmith links while keeping
  LangSmith as the forensic layer.
- Treat `AGENTS.md` as the normative implementation contract, `AD.md` as the
  active architecture baseline, `DECISIONS.md` as frozen rationale, and
  `local-docs/` as the local coding-agent reference library. If they conflict, prefer this file and repair
  the other document.
- Assume docs may contain stale or over-delegated assertions from prior agents.
  When a correction is transient or task-specific, surface it to Jason and either
  address it immediately or promote it to a high-priority item here; do not turn
  transient findings into generic best-practice memory.
- Use Auggie MCP as the first-pass semantic retrieval layer for LangChain
  ecosystem research. Treat it as fast discovery*Extremely valuable for gathering source information, best practices, abstractions, and patterns; ASTxRTYS/docs is the real docs for the full stack of LangChain*, always assert against final authority: verify
  exact SDK behavior against local `.reference/` or `.venv/` source before
  writing specs or code.


- Use Auggie MCP as a semantic discovery amplifier for agent engineering. When working on LangChain, LangGraph, Deep Agents, LangSmith, evals, sandboxes, coding agents, or production agent architecture, query Jason’s indexed reference repos early to find how the ecosystem itself solves similar problems.

- Treat Auggie as fast pattern discovery, not final authority. The right workflow is: retrieve relevant docs/examples by concept, compare across layers, then verify exact SDK behavior against official docs, local source, or installed package source before designing specs or writing code.

Develop taste by triangulating:
- Docs for intended public abstractions and conceptual framing
- SDK source for actual behavior, imports, contracts, and edge cases
- Production reference apps for how good teams compose those primitives under real constraints

For evaluation design, bias toward studying `openevals` and `langsmith-sdk` before inventing evaluator contracts, feedback schemas, dataset flows, or experiment loops. For coding-agent, sandbox, local-first, or TUI design, study Deep Agents CLI and Open SWE before inventing local patterns.

The goal is not to copy references mechanically. The goal is to absorb the ecosystem’s best abstractions, notice where they generalize, and let that compound into better judgment over time.


## Auggie Reference Retrieval Workflow

Use Auggie MCP with conceptual queries when working on LangChain, LangGraph,
Deep Agents, LangSmith, evaluation, sandbox, TUI, or production-agent
architecture. Prefer semantic retrieval across multiple reference repos before
inventing a new abstraction.

Reference repos and primary signal:

- `ASTXRTYS/docs`: official LangChain, LangGraph, Deep Agents, and LangSmith
  docs. Use for conceptual guides, deployment/auth docs, production guidance,
  and public API intent.
- `ASTXRTYS/deepagents`, `libs/deepagents`: Deep Agents SDK implementation.
  Use for `create_deep_agent()`, middleware stack order, filesystem backends,
  skills, memory, subagents, permissions, profiles, and deploy templates.
- `ASTXRTYS/deepagents`, `libs/cli/deepagents_cli`: LangChain's open-source
  Deep Agents CLI coding agent. This is a high-signal production reference for
  coding-agent assembly, `create_cli_agent()`, `langgraph dev` server wiring,
  sandbox backend routing, MCP/tool loading, Textual TUI widgets, approval/ask
  user UX, status rendering, and local-first agent ergonomics.
- `ASTXRTYS/langgraph`: LangGraph runtime internals. Use for `StateGraph`,
  subgraphs, checkpoint namespaces, `Command.PARENT`, persistence, streaming,
  interrupts, and Agent Server behavior.
- `ASTXRTYS/langchain`: LangChain agent foundation. Use for `create_agent()`,
  `AgentMiddleware`, built-in middleware, tool handling, model abstraction,
  structured output, and provider-neutral agent contracts.
- `ASTXRTYS/open-swe`: production coding-agent application patterns. Use for
  sandbox lifecycle, thread metadata, GitHub credential flow, PR publication,
  Slack/Linear/GitHub ingress, middleware safety nets, and source-context
  assembly.
- `ASTXRTYS/langsmith-sdk`: LangSmith client and evaluation infrastructure. Use
  for datasets, examples, experiment runners, `evaluate()` / `aevaluate()`,
  tracing helpers, feedback creation/update, presigned feedback tokens, and
  programmatic LangSmith workflows.
- `ASTXRTYS/openevals`: evaluator building blocks. Use for LLM-as-judge,
  structured-output/JSON match evaluators, trajectory LLM judges, strict /
  unordered / subset / superset trajectory matching, sync/async evaluator
  constructors, and `EvaluatorResult` shape.
- `ASTXRTYS/meta-agent-v5.6.0`: local Meta Harness architecture, decisions,
  constraints, historical context, and project-specific docs.

Workflow:

1. Start from `meta_harness/AGENTS.md` when inside Meta Harness.
2. Query Auggie by concept, not just by symbol name.
3. For architecture questions, triangulate: docs for intent, SDK repos for
   implementation, production apps for usage patterns.
4. For evaluation or experiment design, inspect both `openevals` and
   `langsmith-sdk` before inventing evaluator contracts or feedback schemas.
5. For coding-agent, sandbox, local-first, or TUI design, inspect
   `deepagents/libs/cli/deepagents_cli` and `open-swe` before inventing local
   patterns.
6. Verify exact imports, call signatures, middleware behavior, and runtime
   semantics in local `.reference/` or `.venv/` source before changing specs or
   code.
7. Persist reusable patterns and anti-patterns as memory or skills. Surface
   transient repo/doc corrections to Jason instead of storing them as generic
   memory.

## Highest-Level Decisions

- Meta Harness will adopt the Deep Agents harness from langchain as its primary
  agent runtime/framework.
- Deep Agents is an excellent default harness layer for open-ended, multi-step
  agent work which can be perfectly tuned for a task by carefully crafted system
  prompts, task-specific tools, skills, and an opinionated file system for
  memory.
- From day one, we need to ship our LLM application to allow our agents to have their own virtual machine and their own virtual file system. With that being said, we need to also ship the capability to use our LLM application as a local-first system where the file system for memory and artifact persistence can be stored on the user's disk if the user so desires. There must be dual modality, local-first, and also the ability for the agent to spin up its own virtual machine and entirely run inside of a sandbox.
- For the deep agents abstraction, Langchain ships the majority of all needed logic to develop an agent harness or an LLM application. We must always leverage what the deep agents SDK provides and embrace middleware as an extension of the deep agent's harness abilities.
- A rewrite is allowed to be incremental. New v1 code should be clean enough
  that old v0.5 code can be ported over one behavior at a time.
- We will ship with our main agent, which is going to be the direct interface that most users will interact with. Other agents will be part of this LLM application, and it is to be decided whether they should be sub-agents or have the same or be their own standalone agent. The researcher, who is in charge of researching, should itself be fully stateful and capable of managing its own set of sub-agents, so the researcher must be its own deep agent as well. We will ship with an architect who, as I mentioned for the researcher, must be stateful, have its own memory, and be its own create deep agent that has access to all the benefits of the deep agent harness. The same applies for all of the agents that I will mention here:
- The planner, our planner agent
- our developer agent who serves as our coding agent, essentially our generator
- our harness engineer agent
- and our evaluator agent  All of these agents together serve as an LLM application for developing, observing, and shipping other LLM applications. The decision that I am wrestling with is: should we have the project manager as its own agent and all these other agents serve as sub-agents, or should each agent serve as its own deep agent separately without needing to be a sub-agent? In my articulation, I realize I must clarify that, when I say, "should these agents be sub-agents of the PM in a world where they do end up being the sub-agents of the PM," they must also be deep agents, even if they are sub-agents. The only thing that I am attempting to articulate is: should they be compiled as sub-agents, or should they be their own deep agent? This is the decision matrix that I am wrestling with.
  
    ## HIGH-LEVEL REQUIREMENTS (NOT YET RESOLVED)
### **"PM Scopes Criteria, Harness Engineer Owns the Science"**

---

### **Core Agent Roles**

#### **Project Manager (PM)**
- **Responsibility**: Business-oriented project manager with exceptional organizational skills
- **Function**: Translates stakeholder vision into clear requirements and evaluation criteria — defining **WHAT** success looks like
- **Key Capability**: Context building and project scope dissemination

#### **Harness Engineer**
- **Responsibility**: PM's brightest technical coworker — the scientific authority on evaluation
- **Function**: Owns **HOW** to evaluate: scoring rubrics, LLM judge assembly, calibration methodology,runs experiments, designs eval harnesses, serves as full agent harness engineer and harness topology

---

### **Critical Design Constraint: PM Self-Awareness**
When the PM finishes shaping evaluation criteria and business-logic datasets with stakeholders, it must recognize:

> *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."*

This self-awareness — knowing where its expertise ends and the Harness Engineer's begins — is a core design constraint.

---

### **Communication Architecture**

#### **PM Context Broadcasting Mechanism**
The PM should be able to send a "burst of information" to all relevant agents (researcher, architect, harness engineer) when project scope is clear.

**Implementation Option**: Shared `@AGENTS.md` file per project that serves as:
- A communication board accessible to all agents
- PM's mechanism for publishing high-signal project information
- Context engineering foundation in the agent memory filesystem

---

### **Workflow Handoffs & Loops**

#### **Phase 1: PM → Harness Engineer Handoff**
1. **PM recognizes completion** of stakeholder discussions and PRD finalization
2. **PM communicates** to Harness Engineer:
   - Final PRD
   - Evaluation criteria
   - Rough draft datasets from stakeholder
3. **Harness Engineer responsibilities**:
   - Finalize datasets and evaluation criteria
   - Create scoring rubrics
   - Generate held-out datasets for LLM judge calibration and final phase experiments against target harness and target application
   - Create evaluation criteria and datasets for researcher consumption

#### **Feedback Loop Capability**
- Harness Engineer may have questions for PM → PM asks high-signal questions to stakeholder
- Harness Engineer can use `ask_user` middleware tool for targeted stakeholder questions
- Loop must be optional but available
- Deep Agent's CLI shows an example of this `ask_user` middleware and tool.

#### **Phase 2: Researcher ↔ Architect Collaboration**
- **Architect's role**: NOT to research, but to design based on research bundle and PRD
- **Researcher's role**: Identify SDKs, APIs, abstractions to satisfy PRD requirements (langchain abstraction biased due to the robustness and elegance of the full Langchain ecosystem (i.e., Langchain, Langgraph, and Deep Agents).

**Research Focus Areas**:
- LangChain ecosystem (LangGraph, Deep Agents)
- Model capabilities (Anthropic, OpenAI documentation)
- LLM application APIs (Fire, Crawl, LlamaIndex, etc.)
- Subject Matter Expert identification (curated SMEs provided in system prompt)

**Architect-Researcher Loop**:
- Architect identifies knowledge gaps ("I need more info on X SDK/API, I need to know more about this model's capabilities and the correct way to use these model-specific APIs.")
- Requests targeted research from Researcher
- Waits for Researcher completion before proceeding with final design

**Architect's Design Deliverables**:
- Full application design and specification
- Complete tool schemas
- System prompts and tool messages
- Zero-ambiguity architecture documentation
- Has full rein on designing his own designs. Is fully versed in an elegant approach to creating LLM applications. Is ambitious and confident enough to create novel designs that don't currently exist and has a full inventory of existing repos so that it can see how other production agents handle semantically similar situations that the architect may be facing when building his own target harness or application.
- Context for downstream planner agent

#### **Phase 3: Architect → Planner Handoff**
1. **Architect completes** full design specification (may be multiple documents):
   - Requirements document
   - Design document  
   - Task list with phases
2. **Harness Engineer re-engagement** before planner receives work:
   - May have questions for the architect when creating eval harness, evaluation logic, data sets, etc.
   - Evaluates new tools/system prompts introduced by architect
   - Creates evaluation criteria for target harness components
   - Designs evaluation harness for development phase
   - Manages dataset strategy (public vs held-out)
   - Establishes LangSmith upload strategy for visibility

**Data Management Principle**: All agent artifacts and memory must exist in the filesystem (virtual or disk-based)

#### **Phase 4: Planner → Developer Handoff**
- **Planner receives**: Full design, spec, public eval criteria, public datasets
- **Planner creates**: End-to-end development plan with structured phases
- **Note**: Held-out datasets remain exclusively with Harness Engineer for final testing

#### **Phase 5: Development & Evaluation Loop**
- **Developer role**: Execute plan using spec as reference, orchestrate subagents, maintain context isolation
- **Developer as optimizer**: Pause between phases for evaluation and experimentation
- **Evaluation triggers**: Phase completion, major milestones

**Dual Evaluation System**:
1. **Harness Engineer**: Runs technical evaluations on target harness
2. **Evaluator Agent**: 
   - Validates code alignment with design spec and plan
   - Ensures naming conventions and SDK compliance
   - Tests UX/UI components (spins up frontend, records interactions)
   - Hard fails/passes development phases

#### **Final Delivery**
- Both Harness Engineer and Evaluator Agent run final acceptance tests
- Create comprehensive screen recordings of application interaction
- Bundle all deliverables including final artifacts and documentation

## Naming Rules
- New function names must match their canonical SDK/API equivalent. Communicate the aligned SDK name to Jason and justify any net-new function — what it does and why it belongs.
- Before defining a constant, check if an existing one covers the same contract — if so, import it. If semantically distinct, name it to make the distinction clear and communicate it to Jason in your reply or commit.
- New classes must be documented in the commit message with what they represent and why they were added. Surface non-trivial abstractions to Jason before merging.
- Renaming a function, class, or constant requires a deprecation alias or a note to Jason — silent renames break callers.
- New module and file names must be approved by Jason before merging.

## Canonical SDK References

Before implementing anything touching these SDKs, read local source first. Do
not rely on training data or general knowledge. See `local-docs/SDK_REFERENCE.md`
for the full path index and specific line-range references.

## Local Workflows And Commands



## What "Taste" Looks Like

Good DeepAgents code has the following properties:

- **One factory per agent.** Each agent is assembled in exactly one place. No
  configuration spread across multiple files or assembled conditionally at runtime.
- **System prompts in `.md` files.** No multi-line Python strings for prompts.
- **Memory through files, not state.** Cross-task learning is encoded in
  `/AGENT.md` and `/memories/`. The agent writes to these files;
  `MemoryMiddleware` loads them on the next invocation.


## Documentation Hierarchy

### Normative sources

- `AGENTS.md` — the normative convention contract (this file).
- `AD.md` — architecture decision baseline. Active decisions, open questions,
  and rationale. Closed decisions move to `DECISIONS.md`; open questions stay
  inline.
- `DECISIONS.md` — frozen rationale, reference material, not active content.
- `CHANGELOG.md` — historical change audit trail.

### Documentation tree

- `docs/` is the product documentation tree. **Subfolders are created only
  when concrete content exists. Empty scaffolds are not permitted.**
  - `docs/specs/` — implementation contracts derived from `AD.md` decisions
    (*how* and *what fields/values*). `AD.md` locks *what* and *why*.
  - `docs/archive/` — superseded source documents kept for historical
    context only. Not normative; do not cite as authority. Cite the
    AD/DECISIONS/AGENTS.md entry that superseded them.
- Reserved `docs/` subfolders, created only on first real need:
  - `docs/operations/` — operational runbooks (deploy, debug, eval runs).
  - `docs/integrations/` — third-party surface contracts (sandbox providers,
    LangSmith, Supabase, GitHub).
  - `docs/reference/` — standalone reference material (glossary, enum
    tables, shared diagrams).
- `local-docs/` owns local coding-agent reference material (SDK paths, dev
  setup, harness philosophy). Not part of the shipped product docs.

New top-level subfolders under `docs/` require Jason's approval before
creation, same gate as renaming a module.

### Doc types

Every doc under `docs/` declares a `doc_type` in its YAML frontmatter. v1
values:

- `spec` — lives in `docs/specs/`; interface contract derived from AD.
- `runbook` — lives in `docs/operations/`; operational procedure.
- `integration` — lives in `docs/integrations/`; third-party surface spec.
- `reference` — lives in `docs/reference/`; standalone reference material.
- `archive` — lives in `docs/archive/`; superseded source, not normative.

### `docs/specs/` governance

Every doc under `docs/specs/` must satisfy all of the following. Failure on
any point is a rejection condition under the Review Standard.

1. **Provenance header.** YAML frontmatter with `doc_type: spec`,
   `derived_from: [<AD sections>]`, `status: draft|active|deprecated`,
   `last_synced: YYYY-MM-DD`, `owners: ["@handle", ...]`. A visible
   provenance block (`> **Provenance:** Derived from ...`) repeats this for
   human readers at the top of the document.
2. **AD §9 registration.** The spec is registered in `AD.md §9 Decision
   Index → Derived Specs` with file path, parent AD sections, status, and
   last-synced date.
3. **Parent AD pointer.** The parent AD section(s) include a one-line
   pointer: `> Implementation detail: see [`docs/specs/<file>.md`](...)`.

### Direction of flow

Decisions originate in `AD.md` and flow *into* specs. **Specs never
introduce architectural decisions.** If spec writing surfaces a decision,
raise it against AD first, land the AD change, then update the spec and
bump `last_synced`. Specs are free to detail *how* and *what
fields/values*, but cannot contradict AD. If a spec and AD conflict, AD
wins and the spec is repaired.

### Co-modification rule

- A PR that modifies an AD section with a downstream spec must update that
  spec in the same PR and bump `last_synced`.
- A PR that renames or moves a spec file must update the AD pointer and
  the `§9 Decision Index` entry in the same PR.
- Silent renames, orphaned specs, and stale `last_synced` dates are
  rejection conditions.

### Deprecation

- A spec is deprecated, not deleted. Set `status: deprecated`, move content
  to a superseding doc or `docs/archive/`, and leave a short pointer stub
  in the original file describing what replaced it.
- Deprecated specs remain registered in `§9 Decision Index` with their
  final `last_synced` date and a note pointing to the successor.

### Cross-cutting invariants

- If `AD.md` and `AGENTS.md` conflict, treat `AGENTS.md` as authoritative
  for active implementation and update `AD.md` to match.
- Any PR that changes architecture, runtime policy, or agent behavior must
  update at least one of: `AGENTS.md`, `AD.md`, or the relevant spec doc.
- **Deferral verification:** When encountering any text that defers,
  delegates, or scopes a feature to "v2+", "spec", "future", or "later",
  **always surface it to Jason for confirmation** — never assume deferral
  is correct.

AD governance details (status changes, changelog requirements, citation
conventions) are documented inline in `AD.md`.

## Review Standard

- New code should be rejected if it adds a second source of truth without a clear
  reason.
- New files should be rejected if their names do not describe their ownership.
- New agent runtime code should be rejected if it bypasses the SDK harness without
  explaining why.
- New observability behavior should be rejected if it makes trajectory debugging
  worse.
- Specs under `docs/specs/` without a provenance header, without `AD.md §9`
  registration, or without a parent AD pointer must be rejected.
- Specs that introduce new architectural decisions must be rejected; the
  decision is raised against `AD.md` first, then the spec updates.
- PRs that modify an AD section with a downstream spec must update the spec
  in the same PR. Unsynced specs (stale `last_synced`) are a rejection
  condition.
- Silent renames or moves of spec files without updating the AD pointer and
  `§9` registration must be rejected.
- New subfolders under `docs/` without prior approval must be rejected.
- New or modified `local-docs/` files must be referenced from `AGENTS.md`
  with a one-line pointer explaining what the file owns and when to read
  it. Orphan local-docs files with no `AGENTS.md` reference are stale by
  definition.
