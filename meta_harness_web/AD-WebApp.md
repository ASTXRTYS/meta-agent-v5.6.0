# Meta Harness Web — Architecture Decision Record

**Status:** Proposed
**Last Updated:** 2026-04-15
**Companion:** `AGENTS.md` (normative conventions), `DECISIONS.md` (frozen decisions), `CHANGELOG.md` (audit trail)

---

## §1 — Closed Decisions

### D1: Two-Tier Streaming Architecture

**Decision:** The frontend recognizes two distinct tiers of agent composition inherited from the backend. Tier 1 (PCG → 7 peer agents via `add_node`) requires custom pipeline awareness. Tier 2 (agent → internal subagents via `task` tool) is handled by the SDK's `SubagentManager`.

**Rationale:** The JS SDK's `SubagentManager` tracks subagents by detecting `task` tool calls and routing messages with `"tools:"` namespace segments. PCG-mounted child graphs produce `run_agent:<task_id>` namespaces that do NOT contain `"tools:"` — no configuration option bridges this gap. Pretending both tiers are the same produces a leaky abstraction.

**Tradeoffs:** Tier 1 requires custom code; Tier 2 is zero-cost. The cost is in the mental model, not the implementation.

**Source:** `.reference/libs/langgraphjs/libs/sdk/src/ui/subagents.ts:31-43` — `isSubagentNamespace` checks for `"tools:"` segments only.

**Locked by:** AGENTS.md §"Highest-Level Decision: Two-Tier Streaming Architecture"

---

### D2: `useStream` as the Reactive State Architecture

**Decision:** `useStream` from `@langchain/react` is the sole reactive state source for the frontend. No polling, no custom fetch, no WebSocket bridges. Components mirror the shape of streaming state, not REST API calls.

**Rationale:** `useStream` provides reactive state for messages, custom agent state (`stream.values`), subagent tracking (`stream.subagents`), and interrupts (`stream.interrupts`). Re-implementing any of this fights the SDK.

**Locked by:** AGENTS.md §"Stream-First Frontend (Core Thesis)"

---

### D3: Framework Selection

**Decision:** React + Tailwind CSS + shadcn/ui.

**Rationale:**
- **React** — aligned with `@langchain/react` SDK (first-class `useStream` hook, `StreamProvider`, suspense streaming). Vue/Svelte/Angular have SDK packages but React has the richest integration surface.
- **Tailwind CSS** — utility-first styling, composable with shadcn/ui, no custom CSS classes when utilities suffice.
- **shadcn/ui** — component primitives that are composable and not opinionated about layout. Copy-paste ownership model, no package dependency lock-in.

**Tradeoffs:** Locks to React ecosystem. If a different framework were needed later, the SDK supports Vue/Svelte/Angular but the component layer would need rewriting. Choosing early is high-leverage because framework determines SDK integration surface.

**Locked by:** AGENTS.md §"UI/UX Exploration → Framework Selection (Locked)"

---

### D4: `streamSubgraphs: true` Mandatory

**Decision:** Every `submit()` call must pass `{ streamSubgraphs: true }`. Without it, PCG child graph events are invisible to the frontend.

**Rationale:** The PCG's 7 peer agents are mounted child graphs. Their events only surface when subgraph streaming is enabled. This is a non-negotiable configuration requirement.

**Locked by:** AGENTS.md §"Submitting with Subgraph Streaming"

---

### D5: `filterSubagentMessages: true` for Tier 2

**Decision:** `useStream` must be configured with `filterSubagentMessages: true`. This separates coordinator messages from Tier 2 subagent output. It does NOT affect Tier 1 messages.

**Rationale:** Without filtering, coordinator and subagent tokens interleave into unreadable output. This is essential for Tier 2 only — Tier 1 requires custom namespace-based attribution.

**Locked by:** AGENTS.md §"`filterSubagentMessages`"

---

### D6: Agent Identification via `lc_agent_name`

**Decision:** Agent attribution in the UI uses `lc_agent_name` from message metadata. This is the same mechanism the backend mandates via `name=` on every agent.

**Rationale:** The `name` parameter on `create_deep_agent()` propagates to `lc_agent_name` in streamed chunk metadata. This is the SDK-provided identification mechanism — no custom mapping needed.

**Source:** `.reference/libs/deepagents/tests/unit_tests/test_subagents.py:1119` — `agent_name = metadata.get("lc_agent_name")`

**Locked by:** AGENTS.md §"Agent Identification via Namespace"

---

### D7: Tier-Prefix Naming Convention

**Decision:** Components and hooks consuming Tier 1 data use `Pipeline` prefix. Those consuming Tier 2 data use `Subagent` prefix. Hook names must reveal which reactive state source they bind to.

**Rationale:** Makes tier boundaries legible at a glance. Prevents ambiguous components that consume both tiers without documenting the dependency.

**Locked by:** AGENTS.md §"Naming Rules → Tier-prefix convention"

---

## §2 — Open Questions

These questions require UI/UX exploration (mockups) before they can be resolved. They are ordered by dependency: earlier questions constrain later ones.

### Q1: Layout Structure

What is the primary layout of the application?

**Options:**
- A) Single-panel chat (like ChatGPT) — pipeline state as inline indicators
- B) Split-panel (chat + sidebar) — pipeline state in a dedicated sidebar
- C) Multi-panel IDE — chat, pipeline state, file viewer, code viewer
- D) Hybrid — chat-primary with collapsible/expanding panels for pipeline state

**Depends on:** None (foundational)
**Blocks:** Q2, Q3, Q4, Q5

---

### Q2: Pipeline State Visibility

How does the user see which phase is active, which agent is running, and the handoff history?

**Information requirements** (from AGENTS.md):
- `stream.values.current_phase` — which phase
- `stream.values.current_agent` — which agent
- `stream.values.handoff_log` — handoff history
- `lc_agent_name` — message attribution

**Depends on:** Q1 (layout determines where pipeline state lives)
**Blocks:** Q3, Q4

---

### Q3: Approval Flow Interaction

How does the user approve or reject a handoff interrupt? What does the approval UI look like?

**Information requirements:**
- `stream.interrupts` — HITL interrupt state
- `pending_handoff` — handoff awaiting approval

**Depends on:** Q1, Q2 (approval must fit within the layout and pipeline state display)
**Blocks:** Q5

---

### Q4: Tier 2 Subagent Visibility

How are internal subagent activities (when an agent spawns subagents via `task` tool) displayed within an agent's turn?

**SDK provides:** `SubagentCard`, `SubagentProgress`, `MessageWithSubagents` patterns. But visual integration with the pipeline-aware layout is open.

**Depends on:** Q1, Q2 (subagent display must fit within the layout)
**Blocks:** None

---

### Q5: Autonomous Mode Toggle

What changes in the UI when the user toggles between autonomous and approval-required modes? Where does the toggle live?

**Depends on:** Q1, Q2, Q3 (toggle affects approval flow visibility)
**Blocks:** None

---

### Q6: Todo/Plan Progress Display

How is `stream.values.todos` displayed alongside pipeline state? Is it per-agent, global, or both?

**Depends on:** Q1, Q2
**Blocks:** None

---

### Q7: Sandbox Visual Form (v1 Scope)

When agents run with sandbox backends, what does the IDE experience look like? Three-panel layout? File tree + code viewer + chat?

**Depends on:** Q1 (sandbox layout must be consistent with or an extension of the primary layout)
**Blocks:** None

---

## §3 — Decision Dependency Map

```
Q1 (Layout) ──→ Q2 (Pipeline State) ──→ Q3 (Approval Flow) ──→ Q5 (Autonomous Mode)
              │                       └──→ Q4 (Tier 2 Visibility)
              └──→ Q6 (Todo Progress)
              └──→ Q7 (Sandbox Form)
```

Q1 is the highest-priority open question. Resolving it cascades into all others.

## §4 — Resolution Process

1. **Mockups resolve open questions.** Each mockup scenario (defined in AGENTS.md §"UI/UX Exploration") exercises one or more open questions.
2. **When a question is resolved**, the decision record moves to `DECISIONS.md` and the question is removed from this section.
3. **Locked decisions** (§1) are not re-opened without a proposal in `CHANGELOG.md` and Jason's approval.
4. **AGENTS.md is authoritative** — if this AD and AGENTS.md conflict, AGENTS.md wins.
