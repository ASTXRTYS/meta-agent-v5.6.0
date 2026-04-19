---
[When working on the Meta Harness web repo]
---
**You have full agency.**
- Every step you take should be deliberate — choose the single next action that maximizes understanding of the specific problem at hand. Targeted searches beat breadth. Pause between each tool call to synthesize what you learned and determine if you truly need more context or if you're ready to proceed.

Before writing code or specs: **Parse intent, then consult this AGENTS.md**.

This file contains:
- **Naming Rules** — component, hook, and function naming conventions
- **Canonical SDK References** — local source paths for LangGraph SDK, Deep Agents, LangSmith API
- **Unified Stream with Specialized Projections** — the highest-level architectural decision for this frontend
- **Stream-First Frontend** — `useStream` is the architecture, equivalent of `create_deep_agent()` for the backend
- **External Reference Links** — documentation sites and npm packages

**Hard rules:**
1. If <95% confident on any SDK behavior (hook API, stream mode, namespace format), consult the canonical source in `.reference/libs/langgraphjs/` (JS SDK), `.venv/` (Python SDK), or `.reference/libs/deepagents/` (Deep Agents) before proceeding.
2. Do not hand-roll logic the SDK already handles — `useStream` provides reactive state; do not poll, do not re-implement message parsing, do not build custom WebSocket bridges when the SDK handles transport.
3. Targeted skill reading beats breadth — only load skills relevant to this specific request.

---

# Meta Harness Web — Frontend Agent Conventions

This directory `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web` is the frontend workspace for Meta Harness. The backend workspace is `meta_harness/` with its own `AGENTS.md` at the repo root. Frontend conventions are independent but must stay aligned with backend streaming contracts defined in the backend AGENTS.md Observability Contract section.

---

## Highest-Level Decision: Unified Stream with Specialized Projections

The Meta Harness architecture contract defines a **Project Coordination Graph (PCG)** — a pure LangGraph `StateGraph` with 7 peer Deep Agent child graphs mounted as nodes via `add_node` (as specified in backend AD/state-schema docs). LangGraph provides **one unified event stream** with multiple stream modes and optional subgraph visibility. The frontend builds **specialized projections** over this single stream to handle different composition styles:

| Projection | Data Source | SDK Support | Use Case |
|---|---|---|
| **PCG/Peer-Agent Execution** | `stream.values.current_agent`, `streamMetadata.langgraph_node` | Generic LangGraph streaming | PM, researcher, architect, planner, developer, evaluator |
| **Deep Agents Task Subagents** | `stream.subagents`, `getSubagentsByMessage` | SDK-provided SubagentManager | Runtime subagents spawned via `task` tool |
| **Artifact/Structured Output** | `stream.values.artifacts`, custom events, UI messages | Custom events API | Eval files, PRDs, specs, datasets |

**Key architectural insight:** LangGraph does not provide two different streaming transports. It provides one streaming system with multiple modes (`values`, `updates`, `messages`, `custom`). The distinction between PCG-mounted peer agents and runtime `task` subagents is in **UI interpretation layers**, not transport mechanisms.

The `SubagentManager` (`.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts`) tracks subagents by detecting tool calls in AI messages (`registerFromToolCalls`) and routing messages by checking for `"tools:"` segments in the namespace (`isSubagentNamespace`). Under the PCG contract, our 7 peer agents are mounted child graphs and do NOT go through a `tools` node, so their namespace segments look like `<pcg_node>:<task_id>` (current contract: `run_agent:<task_id>`), not `tools:<call_id>`. The `SubagentManager` will NOT detect them.

Therefore, peer-agent execution is modeled via **PCG state + graph metadata** (Projection A), while runtime subagents use the **Deep Agents subagent helpers** (Projection B). Artifacts use **state/custom events/UI messages** (Projection C).

**Final decision:** lock the mental model as **one stream, specialized projections**. "Two-tier streaming" may remain useful shorthand for explaining the two composition styles, but it is not the architecture. Do not build a second transport, do not build a custom WebSocket/SSE bridge, and do not make `stream.subagents` responsible for PCG-mounted peer agents.

### Why projections instead of tiers?

The backend contract composes agents two ways: **graph composition** (PCG `add_node` — pipeline peers) and **runtime composition** (`task` tool — on-demand workers). These are semantically different things. The frontend doesn't create this split — it inherits it.

LangGraph's streaming system treats all nested graphs uniformly via subgraph streaming with namespaces identifying hierarchy levels. Both mounted Deep Agents and runtime subagents emit events under `subgraphs=True`, distinguished by namespace prefixes:
- Empty tuple: PCG coordination
- `("run_agent:...",)`: Mounted peer agents
- `("tools:...",)`: Runtime task subagents

The JS SDK's `SubagentManager` is a **specialized convenience layer** for the Deep Agents `task`-delegation pattern only. It checks for `"tools:"` namespace segments. No configuration option bridges this gap for PCG-mounted child graphs. Verified in source: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31-43`.

**Implementation cost:** Runtime subagents (Projection B) are zero-cost (SDK handles it). Peer-agent execution (Projection A) is trivial reactive reads from `stream.values` plus optional message metadata. Artifacts (Projection C) require explicit emission patterns. The non-trivial cost is in the mental model shift from "tiers" to "projections", not the code.

**Peer-agent boundary:** `filterSubagentMessages` only diverts messages whose namespace contains `tools:`. PCG-mounted peer-agent messages still flow through `stream.messages`; they must be attributed with `stream.values.current_agent`, `streamMetadata.langgraph_node`, `lc_agent_name`, or an explicitly documented debug-only namespace adapter. Do not create a parallel React store that duplicates `stream.values` just to track the active peer role.

---

## Naming Rules

- **SDK name alignment**: When the SDK names a concept, use that name. If the SDK has `SubagentManager`, do not introduce `AgentTracker`. Net-new names require justification: what it represents and why no SDK equivalent exists.

- **Projection-prefix convention**: Components and hooks that consume PCG/peer-agent execution data (`stream.values.current_agent`, `streamMetadata.langgraph_node`) use a `PCG` or `Pipeline` prefix. Those that consume Deep Agents task subagent data (`stream.subagents`) use a `Subagent` prefix. Those that consume artifact/structured output data (`stream.values.artifacts`, custom events) use an `Artifact` prefix. This makes projection boundaries legible at a glance.

- **Type derivation pattern**: Import SDK types directly when they match. When extending, derive: `type PCGState = Pick<AgentState, 'current_agent' | 'current_phase' | ...>`. Do not define standalone interfaces that duplicate SDK fields — the SDK is the source of truth for wire shapes.

- **State source in hook names**: A hook that reads `stream.values.current_agent` is `usePCGAgent` or `usePipelineAgent`. A hook that reads `stream.subagents` is `useSubagentStatus`. A hook that reads `stream.values.artifacts` is `useArtifacts`. The name must reveal which reactive state source it binds to — `useAgentInfo` is banned (ambiguous projection).

---

## Canonical SDK References

Before implementing, planning, or writing specs for anything touching these SDKs, read the local source first. Do not rely on training data or general knowledge.

### Local SDK References

Topic | Local canonical source
---|---
LangGraph streaming (`stream()`, `astream()`, `subgraphs=True`, namespace tuples) | `.venv/lib/python3.11/site-packages/langgraph/pregel/main.py` — `stream()` method at ~line 2497, `subgraphs` parameter; `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py` — namespace construction at ~line 602 |
LangGraph namespace constants (`NS_SEP`, `NS_END`, `checkpoint_ns`) | `.venv/lib/python3.11/site-packages/langgraph/_internal/_constants.py` — `NS_SEP` (pipe separator) at ~line 75, `NS_END = ":"` at ~line 77, `CONFIG_KEY_CHECKPOINT_NS = "checkpoint_ns"` at ~line 55 |
LangGraph message streaming (subgraph message filtering, `TAG_NOSTREAM`, `TAG_HIDDEN`) | `.venv/lib/python3.11/site-packages/langgraph/pregel/_messages.py` |
LangGraph SDK client (`stream_subgraphs`, `StreamPart`, `StreamPartV2`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/_sync/runs.py` — `stream()` at ~line 196; `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py` — `stream()` at ~line 79
RemoteGraph streaming (`stream_subgraphs` for deployed agents) | `.venv/lib/python3.11/site-packages/langgraph/pregel/remote.py` — `stream()` at ~line 740, `astream()` at ~line 900
Deep Agents `SubAgentMiddleware` (`task` tool, `subagent_type`, `CompiledSubAgent`) | `.reference/libs/deepagents/deepagents/middleware/subagents.py` — `_build_task_tool()` at ~line 309, `TaskToolSchema` at ~line 140
Deep Agents streaming test (namespace + `lc_agent_name` verification) | `.reference/libs/deepagents/tests/unit_tests/test_subagents.py` — `test_subagent_streaming_emits_messages_and_updates_from_subgraph` at ~line 1058
Deep Agents graph assembly (`create_deep_agent()`, middleware stack, `name=` propagation) | `.reference/libs/deepagents/deepagents/graph.py` — lines 217–624
Deep Agents CLI TUI (streaming consumption pattern, Textual adapter) | `.reference/libs/cli/deepagents_cli/textual_adapter.py` — stream consumption at ~line 516; `.reference/libs/cli/deepagents_cli/non_interactive.py` — 3-tuple contract at ~line 76 and validation/unpack at ~line 420
Deep Agents async subagents (`AsyncSubAgentMiddleware`, `start_async_task`) | `.reference/libs/deepagents/deepagents/middleware/async_subagents.py`
LangGraph JS SDK — `useStream` hook (React entry point, delegates to `useStreamLGP` or `useStreamCustom`) | `.reference/libs/langgraphjs/libs/sdk/src/react/stream.tsx` — `useStream` router; `.reference/libs/langgraphjs/libs/sdk/src/react/stream.lgp.tsx` — `useStreamLGP` (LangGraph Platform) implementation; `.reference/libs/langgraphjs/libs/sdk/src/react/stream.custom.tsx` — custom transport implementation
LangGraph JS SDK — `@langchain/react` package (React-specific `useStream`, `StreamProvider`, `useStreamContext`, suspense streaming) | `.reference/libs/langgraphjs/libs/sdk-react/src/stream.tsx` — React `useStream`; `.reference/libs/langgraphjs/libs/sdk-react/src/context.tsx` — `StreamProvider` + `useStreamContext`; `.reference/libs/langgraphjs/libs/sdk-react/src/suspense-stream.tsx` — suspense cache pattern
LangGraph JS SDK — `SubagentManager` (subagent tracking, namespace routing, `subagentToolNames`, `isSubagentNamespace`, `extractToolCallIdFromNamespace`) | `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts` — full implementation; `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.ts` — `StreamManager` that creates and delegates to `SubagentManager`
LangGraph JS SDK — Stream orchestrator (event processing, namespace parsing, history restoration) | `.reference/libs/langgraphjs/libs/sdk/src/ui/orchestrator.ts` — run lifecycle; `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.ts` — `StreamManager` event routing
LangGraph JS SDK — Deep Agent stream types (`UseDeepAgentStream`, `UseDeepAgentStreamOptions`, `subagentToolNames`, `filterSubagentMessages`) | `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts` — `UseDeepAgentStream` interface + `UseDeepAgentStreamOptions` with `subagentToolNames` docs
LangGraph JS SDK — Agent stream types (`UseAgentStream`, `UseAgentStreamOptions`) | `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/agent.ts` — agent-specific stream interface
LangGraph JS SDK — UI types (all exported types, `SubagentStreamInterface`, `SubagentToolCall`, `MessageMetadata`) | `.reference/libs/langgraphjs/libs/sdk/src/ui/types.ts` — full type definitions
LangGraph JS SDK — React UI components (SDK exports vs examples) | SDK exports: `.reference/libs/langgraphjs/libs/sdk/src/react-ui/index.ts` (context/load helpers); example `SubagentCard`: `.reference/libs/langgraphjs/examples/ui-react/src/examples/deepagent/components/SubagentCard.tsx`; `SubagentProgress` / `MessageWithSubagents` are docs/example patterns in this snapshot, not exported SDK components
LangGraph JS SDK — Interrupt handling (HITL interrupt extraction, user-facing interrupt formatting) | `.reference/libs/langgraphjs/libs/sdk/src/ui/interrupts.ts`
LangGraph JS SDK — Client (LangGraph API client, thread/run/assistant management) | `.reference/libs/langgraphjs/libs/sdk/src/client.ts`
LangGraph JS SDK — Tests (subagent manager tests, stream manager tests, branching tests) | `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.test.ts` — `StreamManager` + `SubagentManager` integration tests; `.reference/libs/langgraphjs/libs/sdk/src/ui/branching.test.ts` — branching tests; `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts` has no separate test file
Backend AGENTS.md (observability contract, streaming contract, naming rules) | `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AGENTS.md` — Observability Contract at ~line 588

### External Reference Links

When in doubt, check these for recent releases, API changes, and version compatibility:

Policy: prefer canonical docs and official changelogs/releases; avoid support-portal URLs in this section unless no durable source exists.

Package / Resource | URL
---|---
Deep Agents frontend overview | https://docs.langchain.com/oss/python/deepagents/frontend/overview
Deep Agents subagent streaming | https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming
Deep Agents todo list pattern | https://docs.langchain.com/oss/python/deepagents/frontend/todo-list
Deep Agents sandbox pattern | https://docs.langchain.com/oss/python/deepagents/frontend/sandbox
LangGraph streaming (Python) | https://docs.langchain.com/oss/python/langgraph/streaming
LangGraph streaming (JavaScript) | https://docs.langchain.com/oss/javascript/langgraph/streaming
LangGraph subgraphs | https://docs.langchain.com/oss/python/langgraph/use-subgraphs
LangSmith Agent Server API | https://docs.langchain.com/langsmith/server-api-ref (also at deployment `/docs`)
LangSmith deployment | https://docs.langchain.com/langsmith/deployment
`@langchain/react` npm | https://www.npmjs.com/package/@langchain/react
`@langchain/langgraph-sdk` npm | https://www.npmjs.com/package/@langchain/langgraph-sdk
`@langchain/vue` npm | https://www.npmjs.com/package/@langchain/vue
`@langchain/svelte` npm | https://www.npmjs.com/package/@langchain/svelte
`@langchain/angular` npm | https://www.npmjs.com/package/@langchain/angular
LangGraph.js monorepo (source for all JS SDK packages) | https://github.com/langchain-ai/langgraphjs
LangGraph.js SDK source (local clone) | `.reference/libs/langgraphjs/`
LangSmith Agent Server environment variables | https://docs.langchain.com/langsmith/env-var
LangSmith Agent Server scale guide | https://docs.langchain.com/langsmith/agent-server-scale
LangSmith Agent Server changelog | https://docs.langchain.com/langsmith/agent-server-changelog
LangGraph.js releases | https://github.com/langchain-ai/langgraphjs/releases

---

## Decision Scope Boundary

This AGENTS.md owns **conventions and SDK contracts**. It does NOT own visual design, layout decisions, or component implementation details. The distinction matters because committing to specific components before exploring the UI/UX leads to building around assumptions instead of around what actually feels right.

### Locked (AGENTS.md owns these)

- Headless-first architecture (90% headless, 10% artifact emitter)
- Artifact-first visibility (transform LangSmith data into human-friendly artifacts)
- LangSmith integration (deep links only, no embeds)
- Unified Stream with Specialized Projections — PCG/peer-agent execution (Projection A), Deep Agents task subagents (Projection B), artifact/structured output (Projection C)
- `useStream` as the reactive state architecture
- SDK configuration contracts (`streamSubgraphs`, `filterSubagentMessages`, `subagentToolNames`, resumability options)
- Namespace format and agent identification mechanism (`lc_agent_name`, `streamMetadata.langgraph_node`)
- PCG state keys accessible via `stream.values` (contract mirrors backend state schema)
- Naming rules (SDK alignment, projection-based naming, type derivation)
- Canonical SDK references and source citations
- Review standard (what to reject)

### Open (emerges from UI/UX exploration)

- **Visual design** — layout, color, spacing, typography, animation
- **Artifact emitter component inventory** — which specific artifact display components exist
- **Interaction patterns** — how users navigate artifacts, access LangSmith links
- **Layout structure** — single-panel artifact browser, minimal chat interface
- **State-to-UI mapping** — how `stream.values.*` translates to visible artifact elements

### Explicitly Not Locked

The artifact emitter component names listed below are **candidates**, not commitments. They describe the *information requirements* — what data the UI must surface — not the visual form. The actual components may merge, split, or take entirely different shapes based on what we learn from mockups.

### Active Frontend Exploration Memory

Current frontend exploration is artifact-emitter focused. The web UI is minimal — a place to emit progress and ROI artifacts, not a comprehensive application interface.

- Use `FRONTEND_INTERACTION_TRUTH.md` as the primary interaction guidance before frontend optimizer work.
- Do not turn architecture docs into visible UI copy. Internal terms like PCG, J0/J1/J2/J3, command spine, scoping signal, snapshot, Gate package, and eval criteria stub must earn their place before appearing in product UI.
- The UI is not the primary interface — headless channels (Slack, Discord, email) are primary. The web UI exists to surface artifacts.
- The artifact browser should display PRDs, datasets, eval scorecards, and optimization trendlines with direct LangSmith links.
- Future passes must include meaningful artifact interactions: view artifacts, expand/collapse artifact sections, access LangSmith links.
- Keep essential AD, decision, roadmap, positioning, and changelog docs in place. Organize transient iteration artifacts under `mockup_iterations/` and worker instructions under `worker_contracts/`.

---

## Stream-First Frontend (Core Thesis)

The central insight for this frontend is that **`useStream` is the architecture**. It is the frontend's equivalent of `create_deep_agent()` — it defines the entire reactive state surface: what messages the UI sees, what agent state is accessible, what interrupts surface, and how subagent activity is tracked.

You do not build *around* `useStream` — you build *into* it by configuring its options and consuming its reactive state. The practical consequence: **the shape of your React components should mirror the shape of the streaming state, not the shape of REST API calls.** A pipeline phase tracker reads `stream.values.current_phase`; an agent activity indicator reads `stream.values.current_agent`; a subagent card reads `stream.subagents`. No polling, no custom fetch, no WebSocket bridge.

### The `useStream` Hook

```tsx
import { useStream } from "@langchain/react";
```

**Package:** `@langchain/react` (npm) is the React-specific package. It re-exports `useStream` from `@langchain/langgraph-sdk/react` with React-specific additions (`StreamProvider`, `useStreamContext`, suspense streaming). For Vue/Svelte/Angular, use `@langchain/vue`, `@langchain/svelte`, `@langchain/angular` respectively — all wrap the same `@langchain/langgraph-sdk` core.

Source: `.reference/libs/langgraphjs/libs/sdk-react/src/index.ts` — re-exports from `@langchain/langgraph-sdk`

`useStream` is **UI-framework-agnostic** — identical API surface for React, Vue, Svelte, Angular. It connects to a LangSmith Agent Server deployment and provides reactive state:

| Reactive State | Description | Projection |
|---|---|---|
| `stream.messages` | Agent message stream (coordinator-level) | All |
| `stream.values` | Custom agent state — any key in the agent's state schema | All |
| `stream.values.todos` | Todo list / plan progress from agent state | All |
| `stream.values.current_agent` | PCG state key: which of 7 agents is active | PCG/Peer-Agent Execution |
| `stream.values.current_phase` | PCG state key: current pipeline phase | PCG/Peer-Agent Execution |
| `stream.values.handoff_log` | PCG state key: audit trail of agent handoffs | PCG/Peer-Agent Execution |
| `stream.values.pending_handoff` | PCG state key: handoff awaiting approval | PCG/Peer-Agent Execution |
| `stream.subagents` | Map of internal subagent instances (keyed by `task` tool call) | Deep Agents Task Subagents |
| `stream.interrupts` | HITL interrupt state (approval gates, `ask_user`) | All |
| `stream.isLoading` | Whether a run is in progress | All |

### Submitting with Subgraph Streaming

```tsx
stream.submit(
  { messages: [{ type: "human", content: text }] },
  { streamSubgraphs: true }  // Required for PCG/peer-agent visibility + full subgraph visibility
);
```

**`streamSubgraphs: true` is mandatory for Meta Harness PCG/peer-agent visibility (Projection A) and recommended as the default for runtime subagent fidelity (Projection B).** Without it, mounted PCG child-graph events/namespaces are invisible to the frontend. Runtime subagents can still register some top-level tool call/result transitions, but you lose live subgraph namespace/message/value streams.

### `filterSubagentMessages`

```tsx
const stream = useStream<AgentState>({
  apiUrl: AGENT_URL,
  assistantId: "meta_harness_pcg",
  filterSubagentMessages: true,  // Separate coordinator from subagent messages
});
```

**`filterSubagentMessages: true` is essential for Projection B (Deep Agents Task Subagents).** Without it, coordinator and subagent tokens interleave into unreadable output. This only affects messages from `SubAgentMiddleware`-spawned subagents (Projection B). PCG/peer-agent messages (Projection A) are NOT filtered by this — they require custom attribution via `stream.values` and message metadata.

**Important:** This option is not a generic "hide all nested graphs" switch. It checks Deep Agents task-subagent namespaces (`tools:<call_id>`) and routes those messages into `stream.subagents`. Mounted peer agents under `run_agent:<task_id>` remain graph-execution output and must not be expected to appear in `stream.subagents`.

### `subagentToolNames`

```tsx
const stream = useStream<PCGState>({
  apiUrl: AGENT_URL,
  assistantId: "meta_harness_pcg",
  filterSubagentMessages: true,
  subagentToolNames: ["task"],  // Default — only "task" tool triggers subagent tracking
});
```

The `subagentToolNames` option controls which tool names the `SubagentManager` treats as subagent invocations. Defaults to `["task"]`. When an AI message contains tool calls with these names, they are automatically tracked as subagent executions.

**For Meta Harness, the default is correct for Projection B.** Our 7 peer agents are NOT invoked via tool calls, so adding handoff tool names here would not help PCG/peer-agent tracking (Projection A). However, if any agent uses custom tool names to spawn subagents (beyond the default `task`), register those names here for Projection B extensibility.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts:276–301` — `UseDeepAgentStreamOptions.subagentToolNames` documentation; `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:20–21` — `DEFAULT_SUBAGENT_TOOL_NAMES = ["task"]`

### Resumability Options (Recommended for Long-Running Workflows)

```tsx
const stream = useStream<AgentState>({
  apiUrl: AGENT_URL,
  assistantId: "meta_harness_pcg",
  onDisconnect: "continue",  // Continue backend execution if client disconnects
  streamResumable: true,     // Enable resumable runs for long workflows
  reconnectOnMount: true,     // Auto-reconnect on page refresh
});
```

**These options are recommended for long-running multi-agent workflows.** `onDisconnect: "continue"` ensures backend execution continues if the client disconnects. `streamResumable: true` enables run resumption after disconnects. `reconnectOnMount: true` auto-reconnects on page refresh. These are critical for Meta Harness workflows that may run for extended periods.

**Disconnect policy:** For durable Meta Harness workflows, prefer `streamResumable: true` with `onDisconnect: "continue"` and `reconnectOnMount: true`. Use `"cancel"` only for disposable preview/mockup runs or operations where continuing after client disconnect would be incorrect. Mitigate zombie-run risk with `multitaskStrategy: "interrupt"`, run/thread TTLs, ownership checks, and resumable-stream TTL configuration.

Source: `.reference/libs/langgraphjs/libs/sdk/src/react/stream.lgp.tsx:571–587` — `useStream` defaults `onDisconnect` to `"continue"` when a resumable stream is active and `"cancel"` otherwise.

---

## State Management Governance

The frontend has three state sources. Using the wrong one produces bugs, stale data, or unnecessary re-renders.

### State Source Hierarchy

| State Source | Use When | Examples |
|---|---|---|
| `stream.values.*` | Data originates from the backend agent state and must be reactive to agent execution | `current_agent`, `current_phase`, `handoff_log`, `todos`, `pending_handoff` |
| `stream.messages` | Message data from the agent stream (coordinator + subagent messages) | Chat message list, tool call display |
| `stream.subagents` | Deep Agents task-subagent tracking data (Projection B only) | Subagent status, subagent messages |
| `stream.interrupts` | HITL interrupt state | Approval gates, `ask_user` prompts |
| Local React state (`useState`) | UI-only state with no backend counterpart — ephemeral, not persisted, not shared across components | Modal open/closed, accordion expanded, selected tab index, form input before submit |
| URL state (search params) | State that must survive page reload and be shareable via deep link | Active thread ID, selected agent filter, view mode |

### Rules

- **Do not duplicate `stream.values` in `useState`.** If `stream.values.current_agent` exists, `const [activeAgent, setActiveAgent] = useState()` is a bug — it will go stale the moment the stream updates. Read the stream directly.
- **Derived state must derive, not store.** If you need "is the PM agent currently running", compute it: `const isPM = stream.values.current_agent === "project-manager"`. Do not maintain a separate boolean in state that must be kept in sync.
- **UI-only state is the only valid use of `useState`.** If the state has no backend counterpart and no other component needs it, local state is correct. Examples: is a dropdown open, which tab is selected, hover state.
- **`useMemo` for expensive derivations, not as a state cache.** Deriving from `stream.values` is cheap (it's already reactive). Use `useMemo` only when the derivation itself is expensive (e.g., filtering large arrays, computing aggregates).
- **Thread ID belongs in URL state.** The active thread ID should be a search param so users can share direct links to specific conversations and the page survives reload without `sessionStorage` hacks.
- **Do not write back to `stream.values`.** The stream is a read-only reactive surface. Mutations go through `stream.submit()`. If you need to update agent state, submit a message — do not mutate the stream object.

---

## Component Ownership Policy

Components belong in one catalog. The catalog answers:
- What is the component called?
- Which projection does it serve (PCG/peer-agent execution, Deep Agents task subagents, or artifact/structured output)?
- Which stream state source does it consume?
- Where does it live in the file tree?
- Is it SDK-provided, app-level, or mockup-only?

### Rules

- **One component, one primary state source.** A component that reads `stream.values.current_agent` should not also read `stream.subagents` without documenting why. If it reads both, it's a PCG/peer-agent component with a documented Deep Agents task subagent dependency.
- **Component file location mirrors ownership.** PCG/peer-agent execution components live in `components/pipeline/` or `components/pcg/`. Deep Agents task subagent components that wrap SDK patterns live in `components/subagent/`. Artifact components live in `components/artifact/`. Shared primitives (buttons, cards, inputs) live in `components/ui/`.
- **Do not scatter component definitions.** A component used in more than one page must live in the shared component tree, not inline in a page file. Page-specific components are allowed only if they're truly single-use.
- **SDK utilities are not re-implemented.** If the SDK already provides streaming/state primitives (e.g., `useStream`, `useStreamContext`, `uiMessageReducer`), use them directly. If you adopt docs/example components (e.g., `SubagentCard`), treat them as app-owned components.
- **Mockup components are disposable.** Components created during mockup exploration live in `mockups/` and are not imported by production code. When a mockup component graduates to production, it moves to the shared component tree and follows the ownership rules above.

---

## Projection A: PCG/Peer-Agent Execution

The PCG is a pure LangGraph `StateGraph` with 7 Deep Agent child graphs mounted as nodes. The frontend models this as a **graph-execution UI** driven by PCG state and graph metadata, not as a subagent list. The SDK's subagent abstractions do not track mounted child graphs—they are specialized for the `task`-delegation pattern only.

### PCG State Schema (via `stream.values`)

| State Key | Type | Description |
|---|---|---|
| `current_agent` | `string` | Enum: `project-manager`, `harness-engineer`, `researcher`, `architect`, `planner`, `developer`, `evaluator` |
| `current_phase` | `string` | Current pipeline phase |
| `handoff_log` | `array` | Audit trail of agent handoffs (see backend AGENTS.md for locked field set) |
| `pending_handoff` | `object | null` | Handoff awaiting approval (if any) |
| `project_id` | `string` | Doubles as root `thread_id` |

These state keys update reactively via `stream.values`. Every UI component that needs to know "which agent is active" reads `stream.values.current_agent`, not `stream.subagents`.

### Agent Identification via State and Metadata

**Primary contract:** Use `stream.values.current_agent` and message metadata (`streamMetadata.langgraph_node`, `lc_agent_name`) for agent attribution. This is the documented React pattern for graph-execution UI.

### Namespace Parsing (Low-Level Debugging Tool)

**Namespace parsing is documented at the low-level graph and SDK stream layer, but it is NOT the centerpiece of the documented React `useStream` patterns.** The React patterns push you toward `stream.values`, `toolCalls`, `history`, `interrupt`, and `getMessagesMetadata`. Raw namespace parsing should be a **thin optional adapter for advanced debugging or a custom live execution tree**, not the primary way your React app knows which peer role is active.

**Namespace format** (from LangGraph source):

When `streamSubgraphs: true` is set, streamed events from child graphs include namespace metadata that identifies which child graph produced the event.

```
NS_SEP = "|"   — separates hierarchy levels
NS_END = ":"   — separates node name from task ID
```

For the PCG running the PM agent, a namespace would look like:
```
<pcg_node>:<task_id>|model:<task_id>
```
Where `<pcg_node>` is the mounted PCG child node name (current contract: `run_agent`) and `model` is the internal Deep Agent node.

**Critical distinction:** The JS SDK's `isSubagentNamespace()` checks for `"tools:"` segments — it returns `true` only for namespaces that pass through a `tools` node (e.g., `tools:call_abc123`). Mounted child graph namespaces like `<pcg_node>:<task_id>` (current contract: `run_agent:<task_id>`) do NOT contain `"tools:"` and will NOT be detected as subagent namespaces. This is why `SubagentManager` cannot track PCG-mounted peer agents.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31–43` — `isSubagentNamespace` checks `namespace.includes("tools:")` or `namespace.some((s) => s.startsWith("tools:"))`

In `messages` stream mode, each chunk includes metadata with:
- `langgraph_checkpoint_ns` — the full namespace string
- `lc_agent_name` — the agent's `name=` parameter (set via `create_deep_agent(name=...)`)

**Agent identification rule:** Use `lc_agent_name` from message metadata for agent attribution. This is the same mechanism the backend AGENTS.md mandates with `name=` on every agent — the `name` propagates to `lc_agent_name` in streamed chunk metadata.

Source: `.reference/libs/deepagents/tests/unit_tests/test_subagents.py:1119` — `agent_name = metadata.get("lc_agent_name")`

### PCG/Peer-Agent Information Requirements (Artifact Emitter Scope)

These are the *information requirements* the artifact emitter UI must surface. Given the headless-first architecture, the web UI focuses on artifact emission, not pipeline monitoring:

| Information Requirement | State Source | Working Label |
|---|---|---|
| Artifact browser (PRDs, datasets, specs, rubrics) | Backend filesystem + `stream.values` | Artifact display component |
| Eval scorecards and results | Backend eval outputs | Scorecard component |
| Optimization loop trendlines | Backend experiment history | Trendline visualization |
| LangSmith deep links | Backend run/trace IDs | Link affordance component |

**Pipeline monitoring (agent activity, handoffs, phase tracking) is a headless concern.** The web UI does not surface these — they are managed via headless channels (Slack, Discord, email).

---

## Artifact Emitter UI Scope

**Purpose:** The web UI exists solely to emit progress and ROI artifacts — PRDs, datasets, eval scorecards, and optimization trendlines. It is not a comprehensive application interface; it is the visibility layer for invisible work done via headless channels.

### Framework Selection (Locked)

- **React** — primary UI framework (aligned with `@langchain/react` SDK)
- **Next.js 15** — App Router for routing structure
- **Tailwind CSS** — utility-first styling
- **shadcn/ui** — component primitives (composable, not opinionated about layout)

This is locked because it determines the SDK integration surface and the component authoring pattern. The framework serves the minimal artifact emitter scope; changing it later is costly.

### Mockup Approach: Artifact-First Design

Frontend exploration focuses on artifact emission patterns. Mockups should demonstrate:

- Artifact browser layout (PRDs, datasets, specs, rubrics)
- Eval scorecard presentation
- Optimization trendline visualization
- LangSmith deep link affordances (consistent "↗ View in LangSmith" pattern)

Rejected mockup iterations live under `meta_harness_web/mockup_iterations/`. Screenshots, verdicts, and optimizer context live beside those iterations.

### What Mockups Must Not Do

- Connect to a real backend (hardcoded data only)
- Implement production streaming logic
- Commit to final component APIs
- Replace the AGENTS.md conventions
- Build comprehensive pipeline monitoring UI (agent activity, handoff trails, phase tracking)
- Surface internal architecture terms as product copy unless they have earned their place
- Assume the web UI is the primary interface (headless channels are primary)

### Parallel Frontend Iteration

The frontend development track runs independently of backend harness construction. While droids implement the PCG and 7 peer agents, humans or frontend workers iterate on artifact emitter patterns using live hot reload.

**Prerequisites:** None. No backend connection required.

**Workflow:**
1. Improve artifact emitter patterns in the active app.
2. Use `FRONTEND_INTERACTION_TRUTH.md` before assigning or implementing frontend optimizer work.
3. Keep dev server usage stable when possible; use `npm run dev -- --port 3201` from the active app unless occupied.
4. Capture screenshots and notes under `mockup_iterations/<family>/pass-###/` after the artifact patterns work.
5. Keep worker instruction packets under `worker_contracts/`; they are execution history, not product docs.

---

## Projection B: Deep Agents Task Subagents (SDK-Provided)

When any of the 7 peer agents spawns internal subagents via the `task` tool, the Deep Agents frontend SDK provides specialized tracking for this runtime delegation pattern. Full live subgraph visibility requires `streamSubgraphs: true`.

### SubagentStreamInterface (Core Fields)

```typescript
interface SubagentStreamInterface {
  id: string;
  status: "pending" | "running" | "complete" | "error";
  messages: Message[];
  result: string | null;
  toolCall: {
    id: string;
    name: string;
    args: {
      description?: string;
      subagent_type?: string;
      [key: string]: unknown;
    };
  };
  namespace: string[];
  parentId: string | null;
  depth: number;
  startedAt: Date | null;
  completedAt: Date | null;
}
```

The snippet above highlights the core fields most Projection B UI components read directly. The canonical interface extends `StreamBase`, so it also includes `values`, `error`, `isLoading`, `toolCalls`, `getToolCalls`, `interrupt`, `interrupts`, and thread/subagent helper methods.

**Key:** `toolCall.args.subagent_type` identifies the specialist type (e.g., `"researcher"`, `"analyst"`). This is the `subagent_type` field from `TaskToolSchema` in the backend — the same name, same contract. Only valid tracked subagents are exposed; entries without a valid-looking `subagent_type` are filtered as streaming artifacts.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/types.ts` — `SubagentStreamInterface`; `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:412–447` and `:624–628` — valid `subagent_type` gating; `.reference/libs/deepagents/deepagents/middleware/subagents.py:149` — `subagent_type: str = Field(description=...)`

### Key APIs

| API | Returns | Purpose |
|---|---|---|
| `stream.getSubagentsByMessage(msg.id)` | `SubagentStreamInterface[]` | Link coordinator messages to subagents they spawned |
| `stream.subagents` | `Map<string, SubagentStreamInterface>` | All tracked subagent streams (keyed by tool-call ID) — useful for dashboards |
| `filterSubagentMessages: true` | — | Keep `stream.messages` main-agent-only; route runtime subagent output (`tools:` namespaces) to `stream.subagents` |

### UI Patterns (Examples, Not SDK Exports)

| Pattern | Source/status in local snapshot | Purpose |
|---|---|---|
| `SubagentCard` | Concrete example component in `.reference/libs/langgraphjs/examples/ui-react/src/examples/deepagent/components/SubagentCard.tsx` (example only; not exported from SDK `react-ui`) | Shows specialist name, task description, streaming content, timing |
| `SubagentProgress` | JSDoc/example pattern name in `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts` (not exported from `.reference/libs/langgraphjs/libs/sdk/src/react-ui/`) | Progress bar + counter: `{completed}/{total} complete` |
| `MessageWithSubagents` | Project/docs pattern name; no concrete component symbol by this name in local `.reference` snapshot, and not exported from `.reference/libs/langgraphjs/libs/sdk/src/react-ui/` | Renders coordinator message + attached subagent cards |

---

## Projection C: Artifact/Structured Output

LangChain does **NOT** automatically give the frontend access to files agents write. For sandbox-backed UIs, the documented pattern is explicit: the agent can read and write files, but the frontend also needs direct access to browse the filesystem via a custom API layer. The right pattern is: **file bytes live in the filesystem or sandbox; file metadata lives in the stream.**

### Artifact Manifest Contract

**Every time a role writes a meaningful artifact, the backend must do three things in the same logical step:**
1. Keep the file where it belongs (filesystem or sandbox)
2. Append or update an artifact manifest in graph state or Store
3. Emit a custom event for immediate UI

This gives you instant rendering during the run plus clean rehydration after refresh or later thread access.

**Manifest persistence rule:** keep durable artifact indexes in graph state or LangGraph Store as compact JSON manifests. Do not store large artifact bodies in `StateBackend` or checkpointed state; state is for descriptors, summaries, metrics, and links. Large bodies stay in local disk, sandbox storage, or durable object storage and are fetched by explicit API endpoints.

### Artifact Emission Patterns

**Pattern 1: Custom state keys in `stream.values`**
- Put a compact manifest in `stream.values.artifacts` or `stream.values.eval_report`
- Custom state keys are automatically exposed through `stream.values`
- Best for simple artifact manifests that don't need complex event routing

**Pattern 2: Custom events**
- Emit incremental progress via `custom` events (e.g., `eval.started`, `eval.case_completed`, `eval.finalized`)
- Use `dispatch_custom_event` (Python) or `get_stream_writer` with `stream_mode="custom"`
- Frontend hooks into `onCustomEvent` callback
- Best for live progress updates and complex artifact lifecycles
- Custom event payloads must stay UI-sized: descriptors, progress, compact previews, metrics, and IDs. Do not stream full PRDs, datasets, or large eval JSON bodies as custom events.

**Pattern 3: UI messages / Generative UI**
- Use `push_ui_message` and `LoadExternalComponent` for rich inline widgets
- Frontend renders with `onCustomEvent` plus `uiMessageReducer`
- Best for premium UX: mini dashboards, sortable score tables, artifact previews rendered inline

### Artifact Envelope Schema

For JSON eval files specifically, emit a typed artifact envelope like:

```typescript
type EvalArtifactEnvelope = {
  artifactId: string
  kind: "eval_report"
  producerAgent: "harness-engineer" | "evaluator"
  path: string
  mimeType: "application/json"
  schemaVersion: string
  status: "running" | "complete" | "failed"
  summary: string
  metrics: {
    passRate?: number
    score?: number
    latencyMs?: number
    tokenCost?: number
  }
  slices?: Array<{
    label: string
    score?: number
    count?: number
  }>
}
```

### File Access Pattern

**Do NOT rely on filesystem mirroring or token streaming for artifacts.** The frontend should:
1. Receive artifact descriptor events from the stream
2. Render the descriptor immediately in the UI
3. Fetch file contents or previews from your own API endpoints only when needed
4. Serve files separately via HTTP endpoints (local/sandbox URLs) for download/preview

For persistent discovery and hydration, use the LangGraph Store for JSON manifests (not as a blob store for large artifacts). For ephemeral or large artifact bodies, do not put them in StateBackend—checkpoint the manifest and keep the full file in sandbox or durable storage.

### Artifact API Security

Custom artifact routes must enforce the same thread/run/project ownership checks as the Agent Server APIs. A file path in an artifact envelope is not an authorization token. All preview/download routes must resolve paths through the backend's project or sandbox namespace, reject traversal, and verify the requesting user can access the referenced thread/run before reading local or sandbox files.

---

## Synthesis Phase Detection

When all subagents are in terminal states (`status === "complete"` or `status === "error"`) but `stream.isLoading` is still `true`, the coordinator is synthesizing results. Display a synthesis indicator.

---

## Custom State via `stream.values`

`stream.values` exposes keys from the backend agent state schema reactively. No special configuration is required for custom keys. Define a TypeScript interface matching your agent's state schema and pass it as the type parameter:

```tsx
interface PCGState {
  messages: BaseMessage[];
  current_agent: string;
  current_phase: string;
  handoff_log: HandoffRecord[];
  pending_handoff: HandoffRecord | null;
  project_id: string;
  todos: TodoItem[];
}

const stream = useStream<PCGState>({
  apiUrl: AGENT_URL,
  assistantId: "meta_harness_pcg",
  filterSubagentMessages: true,
});
```

### TodoItem Interface (Canonical `TodoListMiddleware` Contract)

```typescript
interface TodoItem {
  content: string;
  status: "pending" | "in_progress" | "completed";
  [key: string]: unknown;
}
```

`TodoListMiddleware` writes `todos` with required fields `content` and `status`. Additional fields may appear from app-specific extensions; frontend code must treat them as optional. Do not rename the canonical wire field `content` to `title` in shared contracts.

Source: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/todo.py:25-50`

---

## Deployment Transport

The frontend connects to a **LangSmith Agent Server** deployment. The `useStream` hook communicates with these API endpoints under the hood:

| API Group | Purpose | Frontend Relevance |
|---|---|---|
| **Assistants** | Configured instances of a graph | `assistantId` in `useStream` |
| **Threads** | Accumulated outputs of a group of runs | Thread management, `threadId` persistence |
| **Thread Runs** | Invocations of a graph on a thread | `submit()` triggers runs, streams responses |
| **Store** | Persistent key-value store | Backend for `StoreBackend` persistence |

### Operational Requirements

- **Durable workflow disconnect policy** — use `streamResumable: true` plus `onDisconnect: "continue"` for real Meta Harness workflows so long-running agent work survives refreshes and transient disconnects.
- **Disposable workflow disconnect policy** — use `onDisconnect: "cancel"` for previews, mockups, or throwaway runs where continuing server-side would produce stale work.
- **Resumable streams** — `RESUMABLE_STREAM_TTL_SECONDS` controls how long a stream can be resumed after disconnect. Configure for production reconnection and cleanup.
- **`multitask_strategy="interrupt"`** — prevents queue buildup of stale runs when multiple runs target the same thread.
- **`BG_JOB_ISOLATED_LOOPS=true`** — required in container environments when running sync code; prefer async `ainvoke` for multi-LLM parallelism inside nodes.
- **Thread TTL** — runs/threads are stored durably by default. Configure TTL or cleanup strategies for transient runs.
- **Resource authorization** — all thread, run, Store, and custom artifact API reads must enforce user/project ownership before returning metadata or file bytes.

### Custom API Routes

The LangSmith deployment can serve custom FastAPI routes alongside the agent API via `http.app` in `langgraph.json`:

```json
{
  "graphs": { "meta_harness_pcg": "./src/pcg.py:pcg" },
  "env": ".env",
  "http": { "app": "./src/api/server.py:app" }
}
```

This is the mechanism for sandbox file browsing APIs and any custom endpoints the frontend needs beyond the agent streaming API. These routes are allowed for artifact previews/downloads, but they must not become a second streaming transport.

### LangSmith Integration Constraints

**Deep links only (Vision.md D11):** All LangSmith artifact references (traces, threads, runs, experiments) must be surfaced as deep links only. No iframes, no embedded viewers, no preview cards that render LangSmith data. Every LangSmith reference in the UI must use a consistent "↗ View in LangSmith" affordance that opens LangSmith in a new tab.

**Rationale:** The web UI is the executive summary and LangSmith is the audit trail. The correct UI treatment is a hand-off link, not an embed. This maximizes visual independence — because LangSmith never appears inside our chrome, we have zero obligation to share visual vocabulary with it.

### Thread Persistence

Thread lifecycle management (creation, persistence across reloads, switching) is an implementation detail, not a convention. The SDK provides the API surface (`threadId`, `switchThread`); the storage strategy is open.

---

## Sandbox Pattern (v1 Scope — Deferred)

**Status:** Deferred given headless-first priority. Sandbox IDE experience is secondary to artifact emission.

When agents run with sandbox backends, the frontend could display an IDE-like experience. The SDK provides the mechanism; the visual form is an open decision for future consideration.

**SDK contract:** Custom API routes served via `http.app` in `langgraph.json` alongside the agent API. Thread-scoped sandboxes via `resolve=` lambda pattern. Real-time file sync via `ToolMessage` watching (not polling).

Source: `meta_harness_web/research_frontend_sdk/findings_sandbox.md`

---

## Source Citations

The unified streaming architecture and the distinction between mounted subgraphs and SubAgentMiddleware subagents:

[1] LangGraph `stream()` method with `subgraphs` parameter — events emitted as `(namespace, data)` tuples where `namespace` is the path to the node where a subgraph is invoked: `.venv/lib/python3.11/site-packages/langgraph/pregel/main.py:2497–2548`

[2] LangGraph namespace constants — `NS_SEP = "|"`, `NS_END = ":"`, `CONFIG_KEY_CHECKPOINT_NS`: `.venv/lib/python3.11/site-packages/langgraph/_internal/_constants.py:55–78`

[3] Namespace construction for child graph tasks — `task_ns = f"{task.name}{NS_END}{task.id}"`, parent prefix via `NS_SEP`: `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:599–637`

[4] LangGraph SDK `stream_subgraphs` parameter mapping — synchronous client: `.venv/lib/python3.11/site-packages/langgraph_sdk/_sync/runs.py:196–197`; async client: `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py:79–80`

[5] RemoteGraph `stream_subgraphs` support — confirms feature propagates to remote execution: `.venv/lib/python3.11/site-packages/langgraph/pregel/remote.py:740–800`

[6] `SubAgentMiddleware` `task` tool invokes subagent via `subagent.invoke()` — NOT via LangGraph streaming mechanism; subagent runs as a tool call within the parent graph's `tools` node: `.reference/libs/deepagents/deepagents/middleware/subagents.py:363–376`

[7] `TaskToolSchema` with `subagent_type` field — the contract that `SubagentStreamInterface.toolCall.args.subagent_type` keys on: `.reference/libs/deepagents/deepagents/middleware/subagents.py:140–149`

[8] Streaming test confirming `lc_agent_name` propagation and namespace-based agent identification: `.reference/libs/deepagents/tests/unit_tests/test_subagents.py:1058–1150`

[9] Backend AGENTS.md `name=` policy — `name` propagates to `lc_agent_name` metadata used in traces and streamed chunk metadata: `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AGENTS.md:530–544`

[10] Backend AGENTS.md canonical streaming contract — 3-tuple `(namespace, stream_mode, data)` pattern: `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AGENTS.md:602–614`

[11] `SubagentStreamInterface` shape — `id`, `status`, `messages`, `result`, `toolCall`, `startedAt`, `completedAt`: `meta_harness_web/research_frontend_sdk/findings_subagent_streaming.md:42–58`

[12] `filterSubagentMessages` and `streamSubgraphs` configuration: `meta_harness_web/research_frontend_sdk/findings_subagent_streaming.md:20–35`

[13] `TodoItem` interface — `content`, `status`, optional extension fields: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/todo.py:25–50`

[14] `stream.values` universal custom state accessor: `meta_harness_web/research_frontend_sdk/findings_todolist.md:111–116`

[15] Sandbox `resolve=` lambda pattern and `http.app` configuration: `meta_harness_web/research_frontend_sdk/findings_sandbox.md:31–71`

[16] Real-time file sync via `ToolMessage` watching: `meta_harness_web/research_frontend_sdk/findings_sandbox.md:80–84`

[17] `useStream` resumability and disconnect behavior — `streamResumable` defaults from resumable-run storage and `onDisconnect` defaults to `"continue"` only when resumability is active, otherwise `"cancel"`: `.reference/libs/langgraphjs/libs/sdk/src/react/stream.lgp.tsx:571–587`

[18] `SubagentManager` tracks subagents by detecting tool calls in AI messages — `registerFromToolCalls` creates pending entries for each tool call whose name matches `subagentToolNames`: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:564–668`

[19] `isSubagentNamespace()` checks for `"tools:"` segments — returns `true` only for namespaces originating from a `tools` node, not from mounted child graph nodes like `run_agent`: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31–43`

[20] `DEFAULT_SUBAGENT_TOOL_NAMES = ["task"]` — the default list of tool names that trigger subagent tracking; configurable via `subagentToolNames` option: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:20–21`

[21] `useStream` delegates to `useStreamLGP` (LangGraph Platform) or `useStreamCustom` (custom transport) based on whether `transport` is in options: `.reference/libs/langgraphjs/libs/sdk/src/react/stream.tsx:40–51`

[22] `@langchain/react` re-exports `useStream` from `@langchain/langgraph-sdk/react` plus React-specific additions (`StreamProvider`, `useStreamContext`, suspense streaming): `.reference/libs/langgraphjs/libs/sdk-react/src/index.ts:1–116`

[23] `UseDeepAgentStreamOptions` with `subagentToolNames` and `filterSubagentMessages` options — first-class configuration for Deep Agent streaming: `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts:276–328`

[24] `StreamManager` creates `SubagentManager` with `subagentToolNames` from options and routes messages using `isSubagentNamespace`: `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.ts:224–227` (construction), `:779–787` (namespace routing)

[25] `SubagentManager.matchSubgraphToSubagent` — multi-pass matching strategy (exact description → partial → fallback) to map namespace IDs to tool call IDs: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:324–399`

[26] `useStream` adds `custom` stream mode when `onCustomEvent` is provided: `.reference/libs/langgraphjs/libs/sdk/src/react/stream.lgp.tsx:238–250`

[27] LangGraph `get_stream_writer()` emits custom stream payloads from graph nodes/tasks: `.venv/lib/python3.11/site-packages/langgraph/config.py:126–166`

[28] `StreamManager` routes `custom` events to `onCustomEvent` with namespace and mutate context: `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.ts:850–852`

---

## Documentation Policy

### AD Document Suite

The frontend follows the same document governance pattern as the backend:

| Document | Purpose | Location |
|---|---|---|
| `AD.md` | Architecture decision baseline — active decisions, open questions, rationale | `meta_harness_web/AD.md` |
| `DECISIONS.md` | Closed (frozen) decision records — reference material, not active content | `meta_harness_web/DECISIONS.md` |
| `CHANGELOG.md` | Historical change audit trail — who changed what, when | `meta_harness_web/CHANGELOG.md` |
| `AGENTS.md` | Normative convention contract — SDK rules, naming, review standard | `meta_harness_web/AGENTS.md` (this file) |

### AD Governance

- `AGENTS.md` is the normative convention contract; `AD.md` is the architecture decision baseline and rationale record.
- When a decision in `AD.md` is resolved, the decision record moves to `DECISIONS.md` and the question is removed from `AD.md`. Open questions remain in `AD.md` inline — they are active decision-making context.
- Any edit that changes architecture, UI policy, or component contracts must update at least one of: `AGENTS.md`, `AD.md`, or the relevant spec doc.
- `AD.md` status changes (`Proposed`, `Accepted`, `Superseded`, `Deprecated`) must be reflected in the header and `CHANGELOG.md` in the same edit.
- Any contributor who touches `AD.md` must append a row to `CHANGELOG.md` with their author ID, date, and a one-line summary.
- If `AD.md` and `AGENTS.md` conflict, treat `AGENTS.md` as authoritative for active implementation and update `AD.md` to match.

---

## Review Standard

- New code should be rejected if it polls when `useStream` provides the same data reactively.
- New code should be rejected if it uses `stream.subagents` to track PCG peer agents — that API is for Deep Agents task subagents only.
- New code should be rejected if it builds a custom WebSocket/SSE bridge when `useStream` + LangSmith deployment handles transport.
- New components should be rejected if their names do not describe their ownership or collide with SDK-provided component names.
- New TypeScript interfaces should be rejected if they redefine SDK-exported types with different field names.
- New agent state keys on the backend must be reflected in the frontend's `PCGState` interface — state schema is a shared contract.
- Production component code should be rejected if it commits to a visual design that hasn't been explored through mockups first — mockups are the decision surface, not the code editor.
- New code should be rejected if it duplicates `stream.values` data in `useState` — the stream is the source of truth, local state is for UI-only concerns.
- New components should be rejected if they consume more than one primary state source without documenting why — one component, one primary source.
- New components should be rejected if they re-implement an SDK-provided component instead of wrapping or extending it.
