# Meta Harness Web — Architecture Decision Record

**Status:** Proposed
**Last Updated:** 2026-04-16
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

> **Resolution note (2026-04-16):** The 2026-04-16 brand/positioning interview (archived in `DECISIONS.md` D9–D16 and consolidated in `POSITIONING.md`) resolved B1, B2, B4, B6, B7. Those subsections are retained below for historical context and each carries a **✅ RESOLVED** banner pointing to the governing decision. B3, B5, and Q1–Q7 remain open pending the three-family mockup exploration (`mockup_briefs/`).

### B1: Core Metaphor

> **✅ RESOLVED by D12 + D13.** The organizing metaphor is **"two adaptive surfaces of one project studio"** — not a single metaphor from the original option list. The Client Portal surface biases toward options B/D/E (workshop / orchestra / war room — collaborative, stakeholder-visible); the Developer Cockpit surface biases toward options A/C (mission control / assembly line — dense, phase-gated). Each of the three visual families will express these biases in its own emotional register. See `POSITIONING.md` §1, §4, §5.

What is the organizing metaphor for the application?

**Options:**
- A) Mission control — dark cockpit, dense status, operators monitoring autonomous systems
- B) Workshop / workbench — light, spacious, tools laid out for hands-on work
- C) Assembly line — phase-gated, sequential, progress-forward motion
- D) Orchestra — conductor + specialists, harmonious coordination
- E) War room — collaborative, high-stakes, shared situational awareness

**Depends on:** None (foundational — upstream of all visual decisions)
**Blocks:** B2, B3, Q1

**Why this matters:** The metaphor shapes naming, iconography, transitions, and layout instinct before any structural question is answered. A "mission control" metaphor makes a dark cockpit layout feel right; a "workshop" metaphor makes a light, spacious workbench feel right.

---

### B2: Brand Personality / Emotional Tone

> **✅ RESOLVED by D9 + D15.** Brand posture is **premium orchestration layer** (D9). Voice principle is **"Always Land The Plane"** — opinionated, register-adaptive (warm-knowledgeable-peer in the Client Portal, precise-technical-operator in the Developer Cockpit) (D15). The three visual families test three distinct expressions of that posture; the winning family will lock the final personality. See `POSITIONING.md` §2, §6.

What is the emotional register of the UI?

**Options:**
- A) Precise and clinical — scientific instrument, minimal decoration, data-dense
- B) Calm and authoritative — executive dashboard, confident spacing, muted palette
- C) Alive and kinetic — streaming, animated, breathing, real-time pulse
- D) Warm and conversational — chat-forward, human, approachable

**Depends on:** B1 (metaphor constrains personality — mission control is not warm)
**Blocks:** B4, Q1

**Why this matters:** Determines animation philosophy, spacing, and whether the UI feels like it's *observing* agents or *conversing* with them.

---

### B3: Agent Personification

Do the 7 agents have visual identities, and if so, how far?

**Options:**
- A) Abstract labels — text-only, no color coding, no icons
- B) Color-coded badges — each agent gets a distinct color, used for attribution
- C) Named avatars — icons/illustrations per agent, with color identity
- D) Full characters — illustrated personas, personality in copy and visuals

**Depends on:** B1 (metaphor constrains how far personification makes sense)
**Blocks:** Q2 (pipeline state visibility depends on whether agents have visual identity)

**Why this matters:** Affects every component that shows agent attribution — which is most of the UI. Retroactive personification means re-doing every component.

---

### B4: Color Strategy

> **✅ RESOLVED at the framing level by D11.** Because LangSmith is link-out only (D11), we have **zero constraint to share LangSmith's palette**. The final palette is deferred to family-winner selection. Each of the three mockup briefs (`mockup_briefs/family-*.md`) proposes its own palette consistent with its emotional register; comparison happens in Phase B. Options A/B/C/D/E from the original list are all still on the table *per family* — Bloomberg family leans A (dark primary), Stripe leans B (light primary), Linear often C (dual mode). D (phase-responsive) and E (agent-attributed) remain candidates for specific components within a family, not whole-app strategies.

**Options:**
- A) Dark mode primary — dark background, light text, accent color for actions
- B) Light mode primary — light background, dark text, accent color for actions
- C) Dual mode — both dark and light, user toggle
- D) Phase-responsive — color shifts with `current_phase` (e.g., research = blue, development = green)
- E) Agent-attributed — each agent's color identity pervades its turn/section

**Depends on:** B1, B2 (metaphor + personality constrain color strategy)
**Blocks:** Q1 (layout mockups need a color system to evaluate)

**Why this matters:** Color is the fastest brand signal. It needs intent, not default. Mocking up in the wrong mode and then switching is a full rework.

---

### B5: Density Philosophy

How much information is visible at once?

**Options:**
- A) Zen — whitespace, one thing at a time, progressive disclosure
- B) Balanced — primary content visible, details on demand
- C) Cockpit — everything visible, high density, glanceable

**Depends on:** B1, B2 (metaphor + personality set density expectations)
**Blocks:** Q1 (layout must respect density philosophy)

**Why this matters:** Related to Q1 but distinct — Q1 is *where* things go, this is *how much* goes there. A client-facing view may want zen; a Jason-facing view may want cockpit.

---

### B6: Audience Self-Image

> **✅ RESOLVED by D12 + D13.** The user's self-image is **determined by surface, not by the app as a whole**. In the Developer Cockpit the user is **Conductor/Developer** (option A + C from the original list — directing agents, debugging the harness). In the Client Portal the user is **Stakeholder** (option B — reviewing deliverables, checking progress, providing input). Option D ("all of the above — UI adapts to role/context") is essentially the answer, resolved via D12 (role-adaptive surface) + D13 (context-adaptive within surface). See `POSITIONING.md` §4.

When you or a client looks at this app, who are you?

**Options:**
- A) Conductor — directing agents, approving handoffs, setting vision
- B) Stakeholder — reviewing deliverables, checking progress, providing input
- C) Developer — debugging a harness, inspecting traces, iterating on prompts
- D) All of the above — the UI adapts to role/context

**Depends on:** B1 (metaphor implies a user role)
**Blocks:** Q1, Q3 (approval flow design depends on whether the user sees themselves as conductor or stakeholder)

**Why this matters:** The answer changes whether the UI is a *control panel*, an *observation deck*, or a *workbench*.

---

### B7: Trust Signal

> **✅ RESOLVED by D10.** Trust is signaled by **the quality of distillation** — we are the executive summary above raw observability. Option C (transparency of process) is correct *in essence* but realized as **curated narrative over raw traces**, not raw-trace exposure. Options A/B/D are tactics each family will apply in its own register. See `POSITIONING.md` §3.

How does the UI project competence and reliability for autonomous agent work?

**Options:**
- A) Precision of layout — tight grid, consistent spacing, nothing misaligned
- B) Granular status — every agent action visible, streaming logs, trace links
- C) Transparency of process — showing the work, intermediate artifacts, reasoning
- D) Confidence — showing only results, clean summaries, minimal noise

**Depends on:** B2, B5 (personality + density constrain trust expression)
**Blocks:** Q2 (pipeline state visibility is partially a trust signal decision)

**Why this matters:** Agents work autonomously. The UI must project that the system is competent and reliable. This is a brand decision, not just a UX decision.

---

### Q1: Layout Structure

What is the primary layout of the application?

**Options:**
- A) Single-panel chat (like ChatGPT) — pipeline state as inline indicators
- B) Split-panel (chat + sidebar) — pipeline state in a dedicated sidebar
- C) Multi-panel IDE — chat, pipeline state, file viewer, code viewer
- D) Hybrid — chat-primary with collapsible/expanding panels for pipeline state

**Depends on:** B1, B2, B4, B5 (metaphor, personality, color, density constrain layout)
**Blocks:** Q2, Q3, Q4, Q5

**Sub-questions to resolve Q1:**

1. **Primary Workflow Bias** — Is this a "chat-first" app where users mainly converse, or a "workbench" where users watch agents work? (Biases toward A/B vs C/D)

2. **Persistent vs. On-Demand Information** — Which must stay visible during active work: pipeline phase, current agent, handoff history? Which can hide behind hover/click?

3. **Viewport Minimums** — What's the narrowest meaningful width? (Determines if split-panel is viable or if we need collapsible/drawer patterns)

4. **Phase-Responsive Layout** — Does the layout change shape based on `current_phase`? (e.g., file viewer expands during Developer phase, shrinks during PM phase)

5. **Interrupt Prominence** — Where do approval interrupts surface? Modal overlay? Inline banner? Dedicated "action zone"?

6. **Entry Pattern** — Does the user land in a project picker first, or straight into chat? (Determines if sidebar starts collapsed)

7. **Secondary Content Strategy** — File tree, code viewer, agent state — these compete for space. Are they panels, tabs, or floating overlays?

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
✅ B1 (Metaphor)  ─→ ✅ B2 (Personality) ─→ ✅ B4 (Color) ──┐
                  └→    B3 (Personification) ────────────┤
                  └→    B5 (Density) ───────────────────┤
                  └→ ✅ B6 (Audience Self-Image) ────────┼─→ Q1 (Layout) ─→ Q2 (Pipeline State) ─→ Q3 (Approval Flow) ─→ Q5 (Autonomous Mode)
                  └→ ✅ B7 (Trust Signal) ──────────────┘              │                        └─→ Q4 (Tier 2 Visibility)
                                                                         └─→ Q6 (Todo Progress)
                                                                         └─→ Q7 (Sandbox Form)
```

**Status (2026-04-16):** B1, B2, B4, B6, B7 resolved by `DECISIONS.md` D9–D16 and `POSITIONING.md`. B3 (Agent Personification) and B5 (Density Philosophy) remain open — they are expressed differently per visual family and will be decided during family-winner selection. Q1–Q7 remain open pending mockup production; they are now unblocked because their brand-feel upstream dependencies have been resolved.

## §4 — Resolution Process

1. **Mockups resolve open questions.** Each mockup scenario (defined in AGENTS.md §"UI/UX Exploration") exercises one or more open questions.
2. **When a question is resolved**, the decision record moves to `DECISIONS.md` and the question is removed from this section.
3. **Locked decisions** (§1) are not re-opened without a proposal in `CHANGELOG.md` and Jason's approval.
4. **AGENTS.md is authoritative** — if this AD and AGENTS.md conflict, AGENTS.md wins.
