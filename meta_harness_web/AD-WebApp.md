# Meta Harness Web — Architecture Decision Record

**Status:** Proposed
**Last Updated:** 2026-04-16 (late evening: D18 pure-broadcast-portal locked; §2 rescoped accordingly)
**Companion:** `AGENTS.md` (normative conventions), `DECISIONS.md` (frozen decisions D1–D18), `POSITIONING.md` (brand/product source of truth), `ROADMAP.md` (current plan), `CHANGELOG.md` (audit trail)

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

> **Per §4 resolution process:** Resolved questions are *removed* from this section and live only in `DECISIONS.md`. Questions B1, B2, B4, B6, B7 were resolved on 2026-04-16 by D9–D16. Q9.3, Q9.4, Q9.6 were resolved the same day by D17 (portal first-login UX, scoped). Later that evening, **D18 (Pure Broadcast Portal)** resolved Q9.5 and Q11 and substantially rescoped Q3, Q4, Q6, Q7, Q8, Q12 to cockpit-only or narrowed them. The residual Q9 is now Q9 (Auth & Seats), pending the forthcoming D19 decision. Decision narratives live in `DECISIONS.md`; `POSITIONING.md` is the consolidated marketing source of truth; `ROADMAP.md` tracks the current plan.
>
> **Question series:**
> - **B-series** — brand/feel questions (B3, B5 still open)
> - **Q-series** — structural / product-feature questions (Q1–Q13, with Q11 resolved and several others narrowed per D18)

### B3: Agent Personification

Do the 7 agents have visual identities, and if so, how far?

**Options:**
- A) Abstract labels — text-only, no color coding, no icons
- B) Color-coded badges — each agent gets a distinct color, used for attribution
- C) Named avatars — icons/illustrations per agent, with color identity
- D) Full characters — illustrated personas, personality in copy and visuals

**Depends on:** None (each visual family has an implicit stance; final decision locks with family winner)
**Blocks:** Q2 (pipeline state visibility depends on whether agents have visual identity)

**Why this matters:** Affects every component that shows agent attribution — which is most of the UI. Retroactive personification means re-doing every component. Each of the three mockup briefs (`mockup_briefs/family-*.md`) will express an implicit personification stance; this question formally locks when the winning family is selected.

---

### B5: Density Philosophy

How much information is visible at once?

**Options:**
- A) Zen — whitespace, one thing at a time, progressive disclosure
- B) Balanced — primary content visible, details on demand
- C) Cockpit — everything visible, high density, glanceable

**Depends on:** None (each visual family has an explicit density baseline in its brief)
**Blocks:** Q1 (layout must respect density philosophy)

**Why this matters:** Related to Q1 but distinct — Q1 is *where* things go, this is *how much* goes there. Per `POSITIONING.md` §5 and D13, density also varies *within* a surface by context-adaptive mode (ambient vs. drill-down). The open question is whether the two surfaces (Portal and Cockpit) share a single density scale with dial-up/down semantics, or use separate scales.

---

### Q1: Layout Structure *(reframed by JOURNEY.md — there is no single layout)*

The original framing of Q1 asked "what is *the* primary layout?" — implying a single canonical answer (chat-only vs. split-panel vs. multi-panel cockpit). That framing was **wrong**.

**Resolved at a higher level via `JOURNEY.md`:** the UI is a **progressive reveal** across eight PCG-grounded journey states (J0 Virgin → J7 Acceptance & Delivery). There is no single canonical layout. Each state is a genuinely different composition:

- **J0 Virgin** — no project thread exists; operator sees identity chrome + PM-centered conversational surface.
- **J1 Scoping: PM <-> Stakeholder** — chat-dominant; first faint working-draft affordance appears.
- **J2 Scoping: HE Authors Eval Suite** — first multi-agent handoff; engaged-agent rail and slim handoff log materialize.
- **J3 Gate 1 Pending** — first-class PRD + eval-suite package; cockpit approval gate; portal appears for the first time as read-only Gate 1 surface.
- **J4 Research & Design Exploration** — specialist loops and research/design artifacts become visible.
- **J5 Gate 2 Pending** — first-class design package; second cockpit approval gate; portal informational rendering.
- **J6 Planning & Development** — rich cockpit density stabilizes; phase telemetry, todos, Tier 2 subagent visibility, and sandbox affordances surface.
- **J7 Acceptance & Delivery** — acceptance stamps, final deliverable hero, and cockpit-only satisfaction check.

Q1 is therefore **resolved by the journey-state framing**, not by picking one of the options. The original sub-questions below are still useful but reframe:

1. **Primary workflow bias** — *varies by state.* J0/J1 are chat-first. J4-J7 become workbench-first as PCG state accrues. The product supports both because the project supports both.
2. **Persistent vs. on-demand information** — *varies by state.* The agent rail and handoff rail begin at J2 and get denser through J7; before J2, they do not exist.
3. **Viewport minimums** — **still open.** Mockup work will determine.
4. **Phase-responsive layout** — *yes, emphatically.* This is the core JOURNEY.md thesis.
5. **Interrupt prominence** — **cockpit-only per D18, first rendered at J3/J5 and refined at J7.** Sessions 2 and 4 produce the visual answer.
6. **Entry pattern** — **operator enters at J0** (virgin chat), not at a project picker. Multi-project picker is Q10; emerges when the operator has >1 active project.

**Status:** Q1 as originally written is resolved. Residual layout questions are operational and resolve during mockup Sessions 1–4.

**Depends on:** `JOURNEY.md` (authoritative), `mockup_briefs/family-*.md` (rich-state J6/J7 specs per family), B5 (density — also reframed, per JOURNEY.md)
**Blocks:** Nothing structurally; individual state-layouts are session-bounded

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

### Q3: Approval Flow Interaction *(cockpit-only, rescoped by D18)*

How does the **operator** approve or reject a handoff interrupt from within the cockpit? What does the approval UI look like?

**Rescoped by D18:** approvals are a cockpit-only action. The portal shows gate moments as informational ("The Architect has delivered the design package; your operator is reviewing it with you"), with no action buttons on the stakeholder side. Sub-questions 1 and 3 below no longer apply (stakeholder doesn't approve in-portal and doesn't receive approval-via-email links for in-system actions). Sub-questions 4 and 5 also simplify since only the operator is the approver.

**Information requirements:**
- `stream.interrupts` — HITL interrupt state
- `pending_handoff` — handoff awaiting approval

**Residual sub-questions (all cockpit-side):**

1. **Rejection routing** — when the operator rejects a gate, does control return to the originating agent (e.g., Architect re-opens design), to the PM (who triages where to route), or does it open a PM chat to capture the rejection reason before routing?
2. **Timeout behavior** — if a gate approval sits unresolved, what happens in the cockpit? Escalating notifications to the operator? Silent wait?
3. **Partial approval / revise-in-place** — can the operator edit sections of the deliverable inline and submit as "approve with revisions," or is the choice binary?

**Depends on:** Q1, Q2 (approval must fit within the cockpit layout and pipeline state display); D13 (action-required mode, cockpit-only per D18)
**Blocks:** Q5

---

### Q4: Tier 2 Subagent Visibility *(cockpit-only, rescoped by D18)*

How are internal subagent activities (when an agent spawns subagents via `task` tool) displayed within an agent's turn in the **cockpit**? Portal does not expose subagent-level detail under D18.

**SDK provides:** `SubagentCard`, `SubagentProgress`, `MessageWithSubagents` patterns. But visual integration with the pipeline-aware cockpit layout is open.

**Depends on:** Q1, Q2 (subagent display must fit within the cockpit layout)
**Blocks:** None

---

### Q5: Autonomous Mode Toggle

What changes in the UI when the user toggles between autonomous and approval-required modes? Where does the toggle live?

**Depends on:** Q1, Q2, Q3 (toggle affects approval flow visibility)
**Blocks:** None

---

### Q6: Todo/Plan Progress Display *(cockpit-primary, rescoped by D18)*

How is `stream.values.todos` displayed in the **cockpit** alongside pipeline state? Is it per-agent, global, or both? Portal, under D18, shows progress at phase-level narrative abstraction ("The Architect is finalizing the design package"), not agent-level todos.

**Depends on:** Q1, Q2
**Blocks:** None

---

### Q7: Sandbox Visual Form *(cockpit-only, rescoped by D18)*

When agents run with sandbox backends, what does the **cockpit's** IDE experience look like? Three-panel layout? File tree + code viewer + chat? Portal does not expose the sandbox under D18 — stakeholders see narrative progress and packaged deliverables, not live agent filesystems.

**Depends on:** Q1 (sandbox layout must be consistent with or an extension of the primary cockpit layout)
**Blocks:** None

---

### Q8: Soft Handover UX Mechanics *(simplified by D18)*

How does an operator transfer cockpit access to a client at project delivery, and how does the client experience that upgrade?

**Context:** D12 establishes soft handover as a monetization feature. D18 sharpens the mechanic: handover = granting a new cockpit account for the client's organization. The capability delta is now structural (stakeholder-mode cannot transact with agents; cockpit-mode can), which makes the upgrade narrative concrete.

**Residual sub-questions:**

1. **Trigger mechanism** — UI button in the cockpit (operator: "promote stakeholder to cockpit")? CLI command? Instruction to the PM agent? Most likely a simple cockpit-side affordance.
2. **Client-side upgrade experience** — email notification ("You now have cockpit access to your Tavern Assistant project") + a first-cockpit-login orientation card explaining new capabilities. "Supervised cockpit" training-wheels mode deferred unless user research demands it.
3. **Operator residual access** — after full handover, does the operator retain read-only observer access, billing/support access, or no access at all? Open — likely a checkbox at handover time.
4. **Revocability** — can a handover be undone (e.g., retainer resumes)? If so, what happens to work the client did in the cockpit meanwhile?
5. **Seeding behavior** — D12 says the delivered project's UUID becomes seed context for the client's next PM-scoped work. Automatic on first new-project creation, or explicit "start new project from this context" action?
6. **Billing/commercial integration** — handled by D19 (auth & seats) + Stripe subscription primitives. Retainer = Stripe subscription on operator org; handover = new Stripe customer relationship with client org.

**Depends on:** D12, D14, D18, D19 (auth/seats); Q1 (integration points in the cockpit layout)
**Blocks:** Post-v1 monetization surfaces

**Why this matters:** Soft handover is the product's primary stickiness mechanism. Shipping a vague handover UX forfeits the monetization advantage D18 just made structural.

---

### Q9: Auth & Seats *(pending D19, residual after D17 + D18)*

After D17 (portal first-login UX) and D18 (pure broadcast portal), only two Q9 sub-questions remain open, both about auth architecture:

1. **Invite mechanism** — operator provisions a stakeholder organization in cockpit → sends email invite with magic link → recipient sets a password (or uses Google OAuth if shipped) → persistent session-based login thereafter. *Working model; finalized by D19.*
2. **Authentication architecture** — specific auth provider choice (Clerk / Supabase Auth / Auth.js / roll-our-own), session model, password-reset flow, Google OAuth inclusion in v1 or deferred. Scope simplified by D18: stakeholder seats are **viewer-only** (no write actions to model); operator seats have full cockpit-write capability; Stripe subscription primitives handle operator retainer billing and handover-to-client-org billing.

**Depends on:** D12 (two surfaces), D17 (first-login UX), D18 (viewer-only stakeholder seats)
**Blocks:** Nothing on canonical mockup screens (login/settings are out-of-scope in `mockup_briefs/*.md`). Blocks implementation work once mockups begin informing code.
**Pending record:** D19 (Auth & Seats)

---

### Q10: Multi-Project Navigation

How does an operator (or a handed-over client with multiple projects) manage and navigate between concurrent projects?

**Sub-questions:**

1. **Project picker surface** — `cmd-K` command palette? Dedicated projects index page? Top-bar dropdown? Left-rail project list?
2. **Cross-project overview** — does the cockpit ever show a "home" view listing all active projects with their status, or is the app always project-scoped with the picker as the only cross-project surface?
3. **Cross-project notifications** — when operator is in Project A's cockpit, how do they learn "Project B has a Gate 2 pending"? A universal notifications tray? A status bar indicator?
4. **Project-to-client cardinality** — is a project always 1:1 with a client, or can multiple clients co-view a project's portal (e.g., founder + their CTO)?
5. **Archival behavior** — delivered/archived projects surface as history? Hidden by default? Searchable?
6. **Operator project vs. client project** — when an operator has 10 active client projects and also personal/internal projects, do they mix in the same picker or live in separate workspaces?

**Depends on:** D8 (internal-tool scope), D12 (two surfaces), Q1 (layout)
**Blocks:** Q1 (entry-state design depends on whether there's a picker before/after login)

**Why this matters:** Consultants will have multiple simultaneous client projects from day one. No project picker = app is single-project only, which contradicts D8's "tool Jason uses for client work."

---

### Q12: Held-Out Dataset Access-Control Affordance *(largely resolved by D18; residual edge case)*

**Resolved by D18 (for the primary cases):**
- **Portal visibility:** hidden entirely — the portal shows eval results and public dataset previews only. Held-out dataset is invisible to stakeholders.
- **Cockpit visibility for operator:** full preview access (operator is acting as both operator and harness engineer in practice; role-separation ceremony deferred unless user research demands it).

**Residual edge cases (open):**

1. **Handover inheritance** — when a stakeholder receives cockpit via soft handover, do they inherit access to the held-out dataset? *Philosophically* the project is theirs now; *practically* this could undermine evaluation integrity if held-out data leaks into their iteration loops for subsequent work. Likely default: yes-they-inherit, because the project is theirs; flag as a known watch-item for commercial-agreement adjustment.
2. **Held-out regeneration** — if a handed-over client starts a new project using the delivered project as seed context (per D12), should the new project get a newly-generated held-out set, inherit the old one, or opt-out of held-out entirely? Open.

**Depends on:** D10, D12, D18, Q8 (handover mechanics)
**Blocks:** None

---

### Q13: TUI ↔ Web Active-Session Coordination

How does the web app behave when the TUI (backend) is simultaneously active on the same project thread? What's the conflict model?

**Context:** D14 establishes the TUI and web app as parallel windows into the same project thread. Two windows means potential simultaneous writes.

**Sub-questions:**

1. **Activity indication** — does the web app show a "TUI session active on this project" indicator (e.g., "Jason is currently driving this project from terminal")?
2. **Write conflict model** — last-write-wins? Optimistic locking with user-visible conflict resolution? Serialized writes via checkpointer ordering? The LangGraph checkpointer's actual semantics need to be verified (consult `.venv/lib/python3.11/site-packages/langgraph/pregel/main.py` before locking a choice).
3. **Read freshness** — does the web app subscribe to checkpointer deltas, poll on interval, or refresh-on-focus? Latency budget?
4. **Interrupt race** — if both TUI and web app try to resume the same HITL interrupt simultaneously, what resolves first? Is there a lock acquisition step, or does the checkpointer serialize?
5. **Read-only mode opt-in** — should the web app offer an explicit "Viewer" mode for projects actively being driven elsewhere, to prevent accidental double-writes?

**Depends on:** D14; SDK checkpointer semantics (must verify before deciding)
**Blocks:** None (operational concern, can launch with a conservative default)

**Why this matters:** A single-operator scenario (Jason only) makes race conditions rare but possible. Multi-operator scenarios (handed-over client + original operator both active) make them routine. An undefined model ships as last-write-wins by default, which may silently lose state.

---

## §3 — Decision Dependency Map

```
Resolved (see DECISIONS.md D9–D18):
  ✅ B1 Core Metaphor               → D12, D13
  ✅ B2 Brand Personality           → D9, D15
  ✅ B4 Color Strategy (framing)    → D11 (per-family palettes in mockup_briefs/)
  ✅ B6 Audience Self-Image         → D12, D13
  ✅ B7 Trust Signal                → D10
  ✅ Q9.3/Q9.4/Q9.6 (Portal first-login UX)       → D17
  ✅ Q9.5 (First meaningful action, no chat)       → D18
  ✅ Q11 (Chat-with-PM gating — moot, no chat)    → D18
  ✅ Q12 (primary cases — held-out hidden in portal, visible in cockpit) → D18

Rescoped to cockpit-only / narrowed (still open but constrained):
  Q3  (Approval Flow)        → cockpit-only per D18
  Q4  (Tier 2 Subagent Vis)  → cockpit-only per D18
  Q6  (Todo/Plan Display)    → cockpit-primary per D18
  Q7  (Sandbox IDE Form)     → cockpit-only per D18
  Q8  (Soft Handover UX)     → simplified by D18; handover = cockpit account provisioning
  Q12 (residual — handover inheritance, held-out regeneration)

Reframed by JOURNEY.md (no longer "open" as originally framed):
  ✅ Q1 (Layout Structure)   → resolved at higher level: eight PCG-grounded journey states, not one layout

Still open, resolved progressively via journey-state mockup sessions:

  B3 (Agent Personification) ─── first signal at J0 (PM chip), resolves across J0–J7
  B5 (Density Philosophy)    ─── each journey state has its own density; resolves across J0–J7
  Q2 (Pipeline State)        ─── first surfaces at J2 and becomes central by J4/J6
  Q3 (cockpit Approval Flow) ─── surfaces at J3/J5 and is refined by J7, cockpit-only per D18
  Q4 (cockpit Subagent Vis)  ─── surfaces at J6 depending on subagent usage
  Q5 (Autonomous Mode)       ─── surfaces around J3/J5/J6 gate and execution flows
  Q6 (cockpit Todo Progress) ─── surfaces at J6
  Q7 (cockpit Sandbox Form)  ─── surfaces at J6 when sandbox backend engages

Non-journey residuals:
  Q9  (Auth & Seats)         ─── D19 (pending, post-mockup)
  Q10 (Multi-Project Nav)    ─── deferred until operator has >1 active project
  Q13 (TUI↔Web Coordination) ─── operational, can defer
```

**Status (2026-04-17, post-J0-J7 nomenclature normalization):**

- **Resolved / locked:** D1–D18 (18 decisions). D18 is the newest and reshapes §2 substantially. **Q1 reframed by `JOURNEY.md`** — the "single canonical layout" question is resolved at a higher level by the progressive-reveal thesis (eight PCG-grounded journey states, not one layout).
- **Pending decision records:** D19 (Auth & Seats — resolves residual Q9).
- **Journey-state mockup-dependent (resolve via visual exploration across sessions 1–4):** B3 (agent personification — first signal at J0 PM chip), B5 (density — reframed: each state has its own density), Q2 (pipeline state visibility — starts at J2 and matures by J4/J6), Q5 (autonomous mode — gate/execution states), Q6 (cockpit todo progress — J6).
- **Cockpit-scoped residuals (mockup-dependent, surface at J3/J5/J6/J7):** Q3, Q4, Q7.
- **Operational residuals:** Q10 (multi-project nav — deferred until operator has >1 project), Q13 (TUI↔web coordination), Q12 residuals (handover inheritance), Q8 residual sub-questions — all tractable post-mockup or inline with mockups.

**Mockup production is no longer gated on further interviews.** D17 + D18 + `JOURNEY.md` together specify enough of the product-shape to scaffold the Next.js app and start building J0 Virgin across three families on a live dev server. See `ROADMAP.md` for the boot sequence and session plan.

## §4 — Resolution Process

1. **Mockups resolve open questions.** Journey-state mockups (defined in AGENTS.md §"UI/UX Exploration (Journey-State Design)" and ROADMAP.md session sequence) exercise open questions across J0-J7 states.
2. **When a question is resolved**, the decision record moves to `DECISIONS.md` and the question is removed from this section.
3. **Locked decisions** (§1) are not re-opened without a proposal in `CHANGELOG.md` and Jason's approval.
4. **AGENTS.md is authoritative** — if this AD and AGENTS.md conflict, AGENTS.md wins.
