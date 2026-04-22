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

Consider:
  
1. Query Auggie by concept, not just by symbol name.
2. For architecture questions, triangulate: docs for intent, SDK repos for
   implementation, production apps for usage patterns.
3. For evaluation or experiment design, inspect both `openevals` and
   `langsmith-sdk` before inventing evaluator contracts or feedback schemas.
4. For coding-agent, sandbox, local-first, or TUI design, inspect
   `deepagents/libs/cli/deepagents_cli` and `open-swe` before inventing local
   patterns. `open-swe` is the ultimate reference for a headless agent. Puts into practice agent server deployment patterns and more.
5. Verify exact imports, call signatures, middleware behavior, and runtime
   semantics in local `.reference/` or `.venv/` source before changing specs or
   code.
6. Persist reusable patterns and anti-patterns as memory or skills. Surface
   transient repo/doc corrections to Jason instead of storing them as generic
   memory.

## Product Roles and Workflow

Agent roles, handoff phases, and communication architecture are resolved in
`AD.md` §2 and §4. Do not invent new roles or handoff sequences without updating
those sources first. The original product vision articulation is archived at
`docs/archive/product-roles-and-workflow-source.md` for historical context only —
it is not normative.

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

## In-Flight Working Analyses (local-docs)

- `local-docs/pcg-state-schema-rewrite-working.md` — record of reasoning for the
  PCG state schema clean-slate rewrite resolving `OQ-HO` / `OQ-H2` / `OQ-H4`
  (folding in `OQ-H1` / `OQ-H3`). Temporary; archive or delete once the Phase 2
  AD + spec pass lands.

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
