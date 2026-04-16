---
[When working on the Meta Harness web repo]
---
**You have full agency.**
- Every step you take should be deliberate — choose the single next action that maximizes understanding of the specific problem at hand. Targeted searches beat breadth. Pause between each tool call to synthesize what you learned and determine if you truly need more context or if you're ready to proceed.

Before writing code or specs: **Parse intent, then consult this AGENTS.md**.

This file contains:
- **Naming Rules** — component, hook, and function naming conventions
- **Canonical SDK References** — local source paths for LangGraph SDK, Deep Agents, LangSmith API
- **Two-Tier Streaming Architecture** — the highest-level architectural decision for this frontend
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

## Highest-Level Decision: Two-Tier Streaming Architecture

The Meta Harness architecture contract defines a **Project Coordination Graph (PCG)** — a pure LangGraph `StateGraph` with 7 peer Deep Agent child graphs mounted as nodes via `add_node` (as specified in backend AD/state-schema docs). This creates two distinct levels of "subagent-ness" that the frontend must handle differently:

| | **Tier 1: PCG → 7 Peer Agents** | **Tier 2: Agent → Internal Subagents** |
|---|---|---|
| Spawning mechanism | `add_node` in PCG (mounted child graph) | `task` tool via `SubAgentMiddleware` |
| Frontend tracking | `stream.values.current_agent` + namespace parsing | `stream.subagents` + `SubagentStreamInterface` |
| Message filtering | **Custom** (namespace-based) | `filterSubagentMessages: true` ✅ |
| UI components | **Custom** (pipeline-aware) | SDK `stream.subagents` APIs + app-level components (often adapted from docs/examples) ✅ |
| Agent identification | `lc_agent_name` metadata + `current_agent` state key | `toolCall.args.subagent_type` |
| Stream enablement | `streamSubgraphs: true` in `submit()` options | Same — inherited from Tier 1 setting |

**Tier 1 is custom. Tier 2 is SDK-provided.** The `SubagentManager` (`.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts`) tracks subagents by detecting tool calls in AI messages (`registerFromToolCalls`) and routing messages by checking for `"tools:"` segments in the namespace (`isSubagentNamespace`). Under the PCG contract, our 7 peer agents are mounted child graphs and do NOT go through a `tools` node, so their namespace segments look like `<pcg_node>:<task_id>` (current contract: `run_agent:<task_id>`), not `tools:<call_id>`. The `SubagentManager` will NOT detect them even with custom `subagentToolNames`.

**However**, the `subagentToolNames` option (defaults to `["task"]`, configurable) means we CAN register additional subagent-spawning tool names for Tier 2 tracking if those tool calls emit valid subagent args (especially `toolCall.args.subagent_type`, with `description` recommended). This is a future extensibility point, not a Tier 1 solution.

This is the architectural insight that everything else flows from. Every frontend component that needs to know "which agent is active" or "what phase are we in" must read from PCG state via `stream.values`, not from `stream.subagents`.

### Why two tiers?

The backend contract composes agents two ways: **graph composition** (PCG `add_node` — pipeline peers) and **runtime composition** (`task` tool — on-demand workers). These are semantically different things. The frontend doesn't create this split — it inherits it.

The JS SDK's `SubagentManager` tracks subagents by detecting tool calls in AI messages and routing messages with `"tools:"` namespace segments. Our PCG agents are mounted child graphs and produce `<pcg_node>:<task_id>` namespaces (current contract: `run_agent:<task_id>`), not `tools:<call_id>`. No configuration option bridges this gap. Verified in source: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31-43`.

The alternatives are worse: pretending both tiers are the same means either losing pipeline control (making PCG agents into subagents) or building a leaky abstraction that fights the SDK. Naming the thing honestly beats hiding it.

**Implementation cost**: Tier 2 is zero-cost (SDK handles it). Tier 1 is mostly trivial reactive reads (`stream.values.current_agent`, `stream.values.current_phase`) plus one namespace-parsing utility. The non-trivial cost is in the mental model, not the code.

---

## Naming Rules

- **SDK name alignment**: When the SDK names a concept, use that name. If the SDK has `SubagentManager`, do not introduce `AgentTracker`. Net-new names require justification: what it represents and why no SDK equivalent exists.

- **Tier-prefix convention**: Components and hooks that consume Tier 1 data (`stream.values.*`) use a `Pipeline` prefix. Those that consume Tier 2 data (`stream.subagents.*`) use `Subagent` prefix. Ambiguous components (reading both) use `Pipeline` and document the Tier 2 dependency internally. This makes tier boundaries legible at a glance.

- **Type derivation pattern**: Import SDK types directly when they match. When extending, derive: `type PCGState = Pick<AgentState, 'current_agent' | 'current_phase' | ...>`. Do not define standalone interfaces that duplicate SDK fields — the SDK is the source of truth for wire shapes.

- **State source in hook names**: A hook that reads `stream.values.current_agent` is `usePipelineAgent`. A hook that reads `stream.subagents` is `useSubagentStatus`. The name must reveal which reactive state source it binds to — `useAgentInfo` is banned (ambiguous tier).

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
Backend AGENTS.md (observability contract, streaming contract, naming rules) | `/Users/Jason/2026/v4/meta-agent-v5.6.0/AGENTS.md` — Observability Contract at ~line 578

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

- Two-tier streaming architecture — Tier 1 custom, Tier 2 SDK-provided
- `useStream` as the reactive state architecture
- SDK configuration contracts (`streamSubgraphs`, `filterSubagentMessages`, `subagentToolNames`)
- Namespace format and agent identification mechanism (`lc_agent_name`)
- PCG state keys accessible via `stream.values` (contract mirrors backend state schema)
- Naming rules (SDK alignment, tier prefix convention, type derivation)
- Canonical SDK references and source citations
- Review standard (what to reject)

### Open (emerges from UI/UX exploration)

- **Visual design** — layout, color, spacing, typography, animation
- **Component inventory** — which specific Tier 1 components exist and what they look like
- **Interaction patterns** — how users approve handoffs, toggle autonomous mode, navigate pipeline state
- **Layout structure** — single-panel chat, split-panel, multi-panel IDE, etc.
- **State-to-UI mapping** — how `stream.values.*` translates to visible UI elements

### Explicitly Not Locked

The Tier 1 component names listed below (`PipelinePhaseTracker`, `AgentActivityIndicator`, etc.) are **candidates**, not commitments. They describe the *information requirements* — what data the UI must surface — not the visual form. The actual components may merge, split, or take entirely different shapes based on what we learn from mockups.

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

| Reactive State | Description | Tier |
|---|---|---|
| `stream.messages` | Agent message stream (coordinator-level) | Both |
| `stream.values` | Custom agent state — any key in the agent's state schema | Both |
| `stream.values.todos` | Todo list / plan progress from agent state | Both |
| `stream.values.current_agent` | PCG state key: which of 7 agents is active | Tier 1 |
| `stream.values.current_phase` | PCG state key: current pipeline phase | Tier 1 |
| `stream.values.handoff_log` | PCG state key: audit trail of agent handoffs | Tier 1 |
| `stream.values.pending_handoff` | PCG state key: handoff awaiting approval | Tier 1 |
| `stream.subagents` | Map of internal subagent instances (keyed by `task` tool call) | Tier 2 |
| `stream.interrupts` | HITL interrupt state (approval gates, `ask_user`) | Both |
| `stream.isLoading` | Whether a run is in progress | Both |

### Submitting with Subgraph Streaming

```tsx
stream.submit(
  { messages: [{ type: "human", content: text }] },
  { streamSubgraphs: true }  // Required for Tier 1 + full subgraph visibility
);
```

**`streamSubgraphs: true` is mandatory for Meta Harness Tier 1 visibility and recommended as the default for Tier 2 fidelity.** Without it, mounted PCG child-graph events/namespaces are invisible to the frontend. Tier 2 can still register some top-level tool call/result transitions, but you lose live subgraph namespace/message/value streams.

### `filterSubagentMessages`

```tsx
const stream = useStream<AgentState>({
  apiUrl: AGENT_URL,
  assistantId: "meta_harness_pcg",
  filterSubagentMessages: true,  // Separate coordinator from subagent messages
});
```

**`filterSubagentMessages: true` is essential for Tier 2.** Without it, coordinator and subagent tokens interleave into unreadable output. This only affects messages from `SubAgentMiddleware`-spawned subagents (Tier 2). Tier 1 PCG agent messages are NOT filtered by this — they require custom namespace-based attribution.

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

**For Meta Harness, the default is correct for Tier 2.** Our 7 peer agents are NOT invoked via tool calls, so adding handoff tool names here would not help Tier 1 tracking. However, if any agent uses custom tool names to spawn subagents (beyond the default `task`), register those names here.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts:276–301` — `UseDeepAgentStreamOptions.subagentToolNames` documentation; `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:20–21` — `DEFAULT_SUBAGENT_TOOL_NAMES = ["task"]`

---

## State Management Governance

The frontend has three state sources. Using the wrong one produces bugs, stale data, or unnecessary re-renders.

### State Source Hierarchy

| State Source | Use When | Examples |
|---|---|---|
| `stream.values.*` | Data originates from the backend agent state and must be reactive to agent execution | `current_agent`, `current_phase`, `handoff_log`, `todos`, `pending_handoff` |
| `stream.messages` | Message data from the agent stream (coordinator + subagent messages) | Chat message list, tool call display |
| `stream.subagents` | Subagent tracking data (Tier 2 only) | Subagent status, subagent messages |
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
- Which tier does it serve (Pipeline or Subagent)?
- Which stream state source does it consume?
- Where does it live in the file tree?
- Is it SDK-provided, app-level, or mockup-only?

### Rules

- **One component, one primary state source.** A component that reads `stream.values.current_agent` should not also read `stream.subagents` without documenting why. If it reads both, it's a `Pipeline` component with a documented Tier 2 dependency.
- **Component file location mirrors ownership.** Pipeline components live in `components/pipeline/`. Subagent components that wrap SDK patterns live in `components/subagent/`. Shared primitives (buttons, cards, inputs) live in `components/ui/`.
- **Do not scatter component definitions.** A component used in more than one page must live in the shared component tree, not inline in a page file. Page-specific components are allowed only if they're truly single-use.
- **SDK utilities are not re-implemented.** If the SDK already provides streaming/state primitives (e.g., `useStream`, `useStreamContext`, `uiMessageReducer`), use them directly. If you adopt docs/example components (e.g., `SubagentCard`), treat them as app-owned components.
- **Mockup components are disposable.** Components created during mockup exploration live in `mockups/` and are not imported by production code. When a mockup component graduates to production, it moves to the shared component tree and follows the ownership rules above.

---

## Tier 1: PCG Pipeline Awareness (Custom Layer)

The PCG is a pure LangGraph `StateGraph` with 7 Deep Agent child graphs mounted as nodes. The frontend must build a custom pipeline awareness layer because the SDK's subagent abstractions do not track mounted child graphs.

### PCG State Schema (via `stream.values`)

| State Key | Type | Description |
|---|---|---|
| `current_agent` | `string` | Enum: `project-manager`, `harness-engineer`, `researcher`, `architect`, `planner`, `developer`, `evaluator` |
| `current_phase` | `string` | Current pipeline phase |
| `handoff_log` | `array` | Audit trail of agent handoffs (see backend AGENTS.md for locked field set) |
| `pending_handoff` | `object | null` | Handoff awaiting approval (if any) |
| `project_id` | `string` | Doubles as root `thread_id` |

These state keys update reactively via `stream.values`. Every UI component that needs to know "which agent is active" reads `stream.values.current_agent`, not `stream.subagents`.

### Agent Identification via Namespace

When `streamSubgraphs: true` is set, streamed events from child graphs include namespace metadata that identifies which child graph produced the event.

**Namespace format** (from LangGraph source):

```
NS_SEP = "|"   — separates hierarchy levels
NS_END = ":"   — separates node name from task ID
```

For the PCG running the PM agent, a namespace would look like:
```
<pcg_node>:<task_id>|model:<task_id>
```
Where `<pcg_node>` is the mounted PCG child node name (current contract: `run_agent`) and `model` is the internal Deep Agent node.

**Critical distinction:** The JS SDK's `isSubagentNamespace()` checks for `"tools:"` segments — it returns `true` only for namespaces that pass through a `tools` node (e.g., `tools:call_abc123`). Mounted child graph namespaces like `<pcg_node>:<task_id>` (current contract: `run_agent:<task_id>`) do NOT contain `"tools:"` and will NOT be detected as subagent namespaces. This is why `SubagentManager` cannot track Tier 1.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31–43` — `isSubagentNamespace` checks `namespace.includes("tools:")` or `namespace.some((s) => s.startsWith("tools:"))`

In `messages` stream mode, each chunk includes metadata with:
- `langgraph_checkpoint_ns` — the full namespace string
- `lc_agent_name` — the agent's `name=` parameter (set via `create_deep_agent(name=...)`)

**Agent identification rule:** Use `lc_agent_name` from message metadata for agent attribution. This is the same mechanism the backend AGENTS.md mandates with `name=` on every agent — the `name` propagates to `lc_agent_name` in streamed chunk metadata.

Source: `.reference/libs/deepagents/tests/unit_tests/test_subagents.py:1119` — `agent_name = metadata.get("lc_agent_name")`

### Tier 1 Information Requirements (Candidates, Not Locked)

These are the *information requirements* the UI must surface for Tier 1. The specific components that fulfill them will emerge from UI/UX exploration. Names are working labels:

| Information Requirement | State Source | Working Label |
|---|---|---|
| Which pipeline phase is active | `stream.values.current_phase` | Pipeline phase indicator |
| Which agent is currently running | `stream.values.current_agent` + `lc_agent_name` | Agent activity indicator |
| History of agent handoffs | `stream.values.handoff_log` | Handoff audit trail |
| HITL interrupts awaiting user action | `stream.interrupts` | Approval gate |
| Toggle autonomous vs. approval-required mode | Controls `ask_user` interrupt surfacing | Autonomous mode toggle |

**These are not component specs.** They are signals the frontend must consume. The visual form — whether it's a sidebar, a banner, a collapsible panel, or something else entirely — is an open decision.

---

## UI/UX Exploration (Next Step)

Before committing to component implementation, we need to explore what the UI should *look and feel* like. This is the frontend equivalent of the backend's AD process — we lock the "what" (information requirements) before designing the "how" (visual form).

### Framework Selection (Locked)

- **React** — primary UI framework (aligned with `@langchain/react` SDK)
- **Tailwind CSS** — utility-first styling
- **shadcn/ui** — component primitives (composable, not opinionated about layout)

This is locked because it determines the SDK integration surface and the component authoring pattern. Changing frameworks after implementation is costly; choosing early is high-leverage.

### Mockup Approach

Static mockups using React + Tailwind + shadcn/ui with **hardcoded stream data** (no backend required). Purpose: explore layout, interaction, and information density before writing production code.

Mockups should demonstrate:
1. **Pipeline awareness** — user can see which phase is active, which agent is running, handoff history
2. **Chat experience** — primary interaction surface, agent messages attributed to the correct agent
3. **Approval flow** — what happens when an interrupt surfaces, how the user approves/rejects
4. **Autonomous mode** — what changes when the user toggles between autonomous and approval-required
5. **Tier 2 subagent visibility** — how internal subagent activity appears within an agent's turn
6. **Todo/plan progress** — `stream.values.todos` displayed alongside pipeline state

Mockups live in `meta_harness_web/mockups/`. They are disposable — the goal is learning, not shipping.

### What Mockups Must Not Do

- Connect to a real backend (hardcoded data only)
- Implement production streaming logic
- Commit to final component APIs
- Replace the AGENTS.md conventions

### Parallel Frontend Iteration

The frontend development track runs independently of backend harness construction. While droids implement the PCG and 7 peer agents, humans (or frontend agents) iterate on layout, components, and flows using live hot-reload.

**Prerequisites:** None. No backend connection required.

**Workflow:**
1. Scaffold Next.js + shadcn/ui project
2. Create mock components with hardcoded stream data matching PCG state schema
3. `npm run dev` → iterate visually on layout (Q1), pipeline visibility (Q2), approval flows (Q3)
4. Commit refined components to `mockups/` — disposable learning artifacts
5. Graduate to production component tree when backend contract stabilizes

**Decision trigger:** Q1 (Layout Structure) resolution requires visual validation. Start this track immediately — layout exploration is not blocked by backend completion.

---

## Tier 2: Deep Agent Internal Subagents (SDK-Provided)

When any of the 7 peer agents spawns internal subagents via the `task` tool, the Deep Agents frontend SDK provides Tier 2 tracking. Full live subgraph visibility requires `streamSubgraphs: true`.

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

The snippet above highlights the core fields most Tier 2 UI components read directly. The canonical interface extends `StreamBase`, so it also includes `values`, `error`, `isLoading`, `toolCalls`, `getToolCalls`, `interrupt`, `interrupts`, and thread/subagent helper methods.

**Key:** `toolCall.args.subagent_type` identifies the specialist type (e.g., `"researcher"`, `"analyst"`). This is the `subagent_type` field from `TaskToolSchema` in the backend — the same name, same contract. Only valid tracked subagents are exposed; entries without a valid-looking `subagent_type` are filtered as streaming artifacts.

Source: `.reference/libs/langgraphjs/libs/sdk/src/ui/types.ts` — `SubagentStreamInterface`; `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:412–447` and `:624–628` — valid `subagent_type` gating; `.reference/libs/deepagents/deepagents/middleware/subagents.py:149` — `subagent_type: str = Field(description=...)`

### Key APIs

| API | Returns | Purpose |
|---|---|---|
| `stream.getSubagentsByMessage(msg.id)` | `SubagentStreamInterface[]` | Link coordinator messages to subagents they spawned |
| `stream.subagents` | `Map<string, SubagentStreamInterface>` | All tracked subagent streams (keyed by tool-call ID) — useful for dashboards |
| `filterSubagentMessages: true` | — | Keep `stream.messages` main-agent-only; route Tier 2 subagent output (`tools:` namespaces) to `stream.subagents` |

### UI Patterns (Examples, Not SDK Exports)

| Pattern | Source/status in local snapshot | Purpose |
|---|---|---|
| `SubagentCard` | Concrete example component in `.reference/libs/langgraphjs/examples/ui-react/src/examples/deepagent/components/SubagentCard.tsx` (example only; not exported from SDK `react-ui`) | Shows specialist name, task description, streaming content, timing |
| `SubagentProgress` | JSDoc/example pattern name in `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts` (not exported from `.reference/libs/langgraphjs/libs/sdk/src/react-ui/`) | Progress bar + counter: `{completed}/{total} complete` |
| `MessageWithSubagents` | Project/docs pattern name; no concrete component symbol by this name in local `.reference` snapshot, and not exported from `.reference/libs/langgraphjs/libs/sdk/src/react-ui/` | Renders coordinator message + attached subagent cards |
| `SynthesisIndicator` | App-level pattern (inline in `.reference/libs/langgraphjs/examples/ui-react/src/examples/deepagent/index.tsx`; not an SDK export) | Shows when all subagents are terminal but coordinator is still synthesizing |

### Synthesis Phase Detection

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

- **`on_disconnect="cancel"`** — always set to prevent zombie runs when clients disconnect. Without this, runs continue server-side producing stale work.
- **Resumable streams** — `RESUMABLE_STREAM_TTL_SECONDS` controls how long a stream can be resumed after disconnect. Configure for production reconnection.
- **`multitask_strategy="interrupt"`** — prevents queue buildup of stale runs when multiple runs target the same thread.
- **`BG_JOB_ISOLATED_LOOPS=true`** — required in container environments when running sync code; prefer async `ainvoke` for multi-LLM parallelism inside nodes.
- **Thread TTL** — runs/threads are stored durably by default. Configure TTL or cleanup strategies for transient runs.

### Custom API Routes

The LangSmith deployment can serve custom FastAPI routes alongside the agent API via `http.app` in `langgraph.json`:

```json
{
  "graphs": { "meta_harness_pcg": "./src/pcg.py:pcg" },
  "env": ".env",
  "http": { "app": "./src/api/server.py:app" }
}
```

This is the mechanism for sandbox file browsing APIs and any custom endpoints the frontend needs beyond the agent streaming API.

### Thread Persistence

Thread lifecycle management (creation, persistence across reloads, switching) is an implementation detail, not a convention. The SDK provides the API surface (`threadId`, `switchThread`); the storage strategy is open.

---

## Sandbox Pattern (v1 Scope — Information Only)

When agents run with sandbox backends, the frontend can display an IDE-like experience. The SDK provides the mechanism; the visual form is an open decision.

**SDK contract:** Custom API routes served via `http.app` in `langgraph.json` alongside the agent API. Thread-scoped sandboxes via `resolve=` lambda pattern. Real-time file sync via `ToolMessage` watching (not polling).

Source: `meta_harness_web/research_frontend_sdk/findings_sandbox.md`

---

## Source Citations

The two-tier streaming architecture and the distinction between mounted subgraphs and SubAgentMiddleware subagents:

[1] LangGraph `stream()` method with `subgraphs` parameter — events emitted as `(namespace, data)` tuples where `namespace` is the path to the node where a subgraph is invoked: `.venv/lib/python3.11/site-packages/langgraph/pregel/main.py:2497–2548`

[2] LangGraph namespace constants — `NS_SEP = "|"`, `NS_END = ":"`, `CONFIG_KEY_CHECKPOINT_NS`: `.venv/lib/python3.11/site-packages/langgraph/_internal/_constants.py:55–78`

[3] Namespace construction for child graph tasks — `task_ns = f"{task.name}{NS_END}{task.id}"`, parent prefix via `NS_SEP`: `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:599–637`

[4] LangGraph SDK `stream_subgraphs` parameter mapping — synchronous client: `.venv/lib/python3.11/site-packages/langgraph_sdk/_sync/runs.py:196–197`; async client: `.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py:79–80`

[5] RemoteGraph `stream_subgraphs` support — confirms feature propagates to remote execution: `.venv/lib/python3.11/site-packages/langgraph/pregel/remote.py:740–800`

[6] `SubAgentMiddleware` `task` tool invokes subagent via `subagent.invoke()` — NOT via LangGraph streaming mechanism; subagent runs as a tool call within the parent graph's `tools` node: `.reference/libs/deepagents/deepagents/middleware/subagents.py:363–376`

[7] `TaskToolSchema` with `subagent_type` field — the contract that `SubagentStreamInterface.toolCall.args.subagent_type` keys on: `.reference/libs/deepagents/deepagents/middleware/subagents.py:140–149`

[8] Streaming test confirming `lc_agent_name` propagation and namespace-based agent identification: `.reference/libs/deepagents/tests/unit_tests/test_subagents.py:1058–1150`

[9] Backend AGENTS.md `name=` policy — `name` propagates to `lc_agent_name` metadata used in traces and streamed chunk metadata: `/Users/Jason/2026/v4/meta-agent-v5.6.0/AGENTS.md:520`

[10] Backend AGENTS.md canonical streaming contract — 3-tuple `(namespace, stream_mode, data)` pattern: `/Users/Jason/2026/v4/meta-agent-v5.6.0/AGENTS.md:578–590`

[11] `SubagentStreamInterface` shape — `id`, `status`, `messages`, `result`, `toolCall`, `startedAt`, `completedAt`: `meta_harness_web/research_frontend_sdk/findings_subagent_streaming.md:42–58`

[12] `filterSubagentMessages` and `streamSubgraphs` configuration: `meta_harness_web/research_frontend_sdk/findings_subagent_streaming.md:20–35`

[13] `TodoItem` interface — `title`, `status`, `description`: `meta_harness_web/research_frontend_sdk/findings_todolist.md:21–25`

[14] `stream.values` universal custom state accessor: `meta_harness_web/research_frontend_sdk/findings_todolist.md:111–116`

[15] Sandbox `resolve=` lambda pattern and `http.app` configuration: `meta_harness_web/research_frontend_sdk/findings_sandbox.md:31–71`

[16] Real-time file sync via `ToolMessage` watching: `meta_harness_web/research_frontend_sdk/findings_sandbox.md:80–84`

[17] `on_disconnect="cancel"` and resumable stream configuration: `meta_harness_web/SME_INPUT/Streaming.md:57–59` (SME #2, confirmed by SDK source)

[18] `SubagentManager` tracks subagents by detecting tool calls in AI messages — `registerFromToolCalls` creates pending entries for each tool call whose name matches `subagentToolNames`: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:564–668`

[19] `isSubagentNamespace()` checks for `"tools:"` segments — returns `true` only for namespaces originating from a `tools` node, not from mounted child graph nodes like `run_agent`: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31–43`

[20] `DEFAULT_SUBAGENT_TOOL_NAMES = ["task"]` — the default list of tool names that trigger subagent tracking; configurable via `subagentToolNames` option: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:20–21`

[21] `useStream` delegates to `useStreamLGP` (LangGraph Platform) or `useStreamCustom` (custom transport) based on whether `transport` is in options: `.reference/libs/langgraphjs/libs/sdk/src/react/stream.tsx:40–51`

[22] `@langchain/react` re-exports `useStream` from `@langchain/langgraph-sdk/react` plus React-specific additions (`StreamProvider`, `useStreamContext`, suspense streaming): `.reference/libs/langgraphjs/libs/sdk-react/src/index.ts:1–116`

[23] `UseDeepAgentStreamOptions` with `subagentToolNames` and `filterSubagentMessages` options — first-class configuration for Deep Agent streaming: `.reference/libs/langgraphjs/libs/sdk/src/ui/stream/deep-agent.ts:276–328`

[24] `StreamManager` creates `SubagentManager` with `subagentToolNames` from options and routes messages using `isSubagentNamespace`: `.reference/libs/langgraphjs/libs/sdk/src/ui/manager.ts:224–227` (construction), `:779–787` (namespace routing)

[25] `SubagentManager.matchSubgraphToSubagent` — multi-pass matching strategy (exact description → partial → fallback) to map namespace IDs to tool call IDs: `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:324–399`

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
- New code should be rejected if it uses `stream.subagents` to track Tier 1 (PCG peer agents) — that API is for Tier 2 only.
- New code should be rejected if it builds a custom WebSocket/SSE bridge when `useStream` + LangSmith deployment handles transport.
- New components should be rejected if their names do not describe their ownership or collide with SDK-provided component names.
- New TypeScript interfaces should be rejected if they redefine SDK-exported types with different field names.
- New agent state keys on the backend must be reflected in the frontend's `PCGState` interface — state schema is a shared contract.
- Production component code should be rejected if it commits to a visual design that hasn't been explored through mockups first — mockups are the decision surface, not the code editor.
- New code should be rejected if it duplicates `stream.values` data in `useState` — the stream is the source of truth, local state is for UI-only concerns.
- New components should be rejected if they consume more than one primary state source without documenting why — one component, one primary source.
- New components should be rejected if they re-implement an SDK-provided component instead of wrapping or extending it.
