# Meta Harness Web — Closed Decision Records

Frozen decisions archived from `AD.md`. Reference material, not active content.

---

### D8: Internal Tool Scope — No Landing Page for v1

**Decision:** v1 is an internal tool for Jason + client portal for progress visibility. No public SaaS, no marketing landing page needed for v1. Simple login screen suffices for authentication.

**Rationale:** Primary use cases are (1) recording demos of the full web app and agents executing e2e, seeing how artifacts are stored in the ui, seeing eval results, experiment results and direct links to traces in langsmith, etc (2) giving clients visibility into what they're paying for. These are internal/admin workflows, not consumer onboarding flows.

**Tradeoffs:** Skips landing page design effort for v1. If public SaaS becomes a goal later, landing page can be added as a separate concern without affecting core app architecture.

**Source:** User requirement (2026-04-15)

---

*(D1–D7 remain active in `AD-WebApp.md` §1. D9–D16 below added 2026-04-16 from brand/positioning interview.)*

---

### D9: Brand Posture — Premium Orchestration Layer

**Decision:** Meta Harness is positioned as a **premium orchestration layer** that sits visibly *above* the LangChain ecosystem. Our brand is the hero; LangChain/LangSmith are credited but visually subordinate. We share *some* design vocabulary with the LangChain family (enough that LangChain-literate users trust us on sight) but our own identity dominates — distinct color palette, typographic voice, and iconography.

**Rationale:** Two alternatives were rejected: (a) "LangChain-native tool" posture would collapse our brand into LangChain's, losing differentiation and pricing power; (b) "fully independent product" posture would forfeit the trust dividend of signaling ecosystem fluency to our AI-literate buyer. Premium-orchestration-layer threads the needle — we inherit LangChain's credibility without being confused for it.

**Tradeoffs:** Requires a distinct visual identity — we cannot copy LangSmith's chrome to save design effort. Accepted cost.

**Source:** Q1 of 2026-04-16 brand interview; see `POSITIONING.md` §"Brand Posture".

---

### D10: Product Philosophy — Executive Summary, Not Trace Reimplementation

**Decision:** Meta Harness is the *executive summary layer* on top of the LangChain observability stack. We surface **distilled signal** — eval criteria, scoring rubrics, dataset previews, experiment results, pipeline status, handoff narratives. We do **not** reimplement LangSmith's trace/trajectory viewer. When a user needs raw trajectory-level forensics, we hand them off to LangSmith via a deep link.

**Catchphrase:** *"We provide all of the signal. If you need to zoom in on trajectories, we link you directly to where you need to be inside LangSmith."*

**Rationale:** LangSmith already ships an excellent (if rigorous) trace viewer. Re-implementing it would be commodity work with no competitive advantage, and would lock us to LangSmith's data-model shape. Layering a *narrative* on top of raw traces is the value nobody else ships. This mirrors the Bloomberg-vs-Reuters / Datadog-vs-raw-Prometheus pattern: the curator wins as long as the curation is honest and the hand-off to detail is graceful.

**Scope clarification:** "We do not preview traces/threads/runs" means we do not embed or re-render LangSmith's trace viewer UI. It does **not** preclude us from surfacing our own first-class views of PCG state (phase indicator, handoff log narrative, current-agent display) or eval outcomes (scorecards, rubric-score breakdowns, dataset browsers) — those are curated views of our own signal, not previews of LangSmith's trace data.

**Tradeoffs:** We are dependent on LangSmith for detail-level observability. If LangSmith degrades or pivots, our power-user workflow is affected. Accepted — LangSmith is core LangChain infrastructure and extremely unlikely to be deprecated.

**Source:** Q4 of 2026-04-16 brand interview; see `POSITIONING.md` §"Product Philosophy".

---

### D11: LangSmith Relationship — Link-Out Only, No Embeds

**Decision:** LangSmith artifacts (traces, threads, runs, experiments) are surfaced in Meta Harness as **deep links only**. No iframes, no embedded viewers, no preview cards that render LangSmith data. Every LangSmith reference in the UI is a consistent "↗ View in LangSmith" affordance that opens LangSmith in a new tab.

**Rationale:** Direct consequence of D10. If we're the executive summary and LangSmith is the audit trail, the correct UI treatment is a hand-off link, not an embed. This also maximizes our visual independence — because LangSmith never appears inside our chrome, we have zero obligation to share visual vocabulary with it. The three visual families under exploration (Linear / Bloomberg / Stripe) can go fully their own direction.

**Tradeoffs:** Users context-switch (new tab) when drilling into a trace. Accepted — the context switch is a *feature* here: it signals "you are now in the raw-detail tool." Tab-switch fatigue is mitigated by the fact that stakeholders rarely need trace detail (summary is enough for them), and builders are fluent at tab-switching.

**Source:** Q4 of 2026-04-16 brand interview; derived from D10.

---

### D12: Surface Strategy — Two-Surface Role-Adaptive (Client Portal + Developer Cockpit)

**Decision:** Meta Harness is **one web app with two role-adaptive surfaces**:

- **Client Portal** — for external stakeholders (clients, founders, executives). Shows distilled signal: current phase, eval results, packaged deliverables, approval gates, and a chat affordance to the Project Manager agent for scoping/aftercare conversations. Does not expose raw agent chatter or cockpit density.
- **Developer Cockpit** — for the operator (initially Jason, eventually handed-over clients). Full pipeline visibility, all 7 agents' activity, handoff log, eval authoring surfaces, drill-down into any artifact, LangSmith deep links. High density, high leverage.

Both surfaces read from the **same PCG state, same project thread (`thread_id = project_id`), same data sources**. They differ in layout hierarchy, density, access-controlled affordances, and voice register (see D15). Role is assigned per-user per-project via access control; a single human can have cockpit access on their own projects and client access on projects they are the stakeholder for.

**Stickiness mechanism — soft handover:** At project delivery, the operator chooses (a) **retainer** — operator retains cockpit, client retains portal; or (b) **full handover** — client is granted cockpit access; the delivered project's UUID becomes seed context for their next scoped work with the PM. The web app is the product asset being transferred. Cockpit handover is a monetizable product feature, not just a UX pattern.

**Rationale:** Q5-clarify resolved this: stakeholders are external parties (clients of Jason's consulting practice, and eventually of any operator using Meta Harness) who require access-controlled separation from cockpit internals. The retainer-vs-handover split creates genuine product stickiness — clients either pay ongoing for operator-managed projects, or pay for the handover that grants them self-service capability. Both lanes monetize the app; a role-adaptive surface strategy is what enables both.

**Scope note:** This decision *extends* D8 (Internal Tool Scope — No Landing Page for v1) rather than replacing it. D8 correctly locked "v1 = internal tool + client portal." D12 specifies *how* that dual-audience product is organized structurally.

**Tradeoffs:** Two surfaces means roughly 2× the mockup work per visual family, and two sets of components to maintain in production. Mitigated by: shared data layer (same `useStream`, same reactive reads), shared component library (eval scorecard, dataset browser, LangSmith link treatment), and explicit design discipline — the two surfaces must share brand tokens even when they diverge in layout and density.

**Source:** Q5 + Q5-clarify of 2026-04-16 brand interview; extends D8.

---

### D13: Surface Interaction Model — Context-Adaptive Within Each Surface

**Decision:** Within each of the two surfaces (portal and cockpit), the UI is **context-adaptive** — it reshapes itself based on project state, not user action:

- **Ambient mode** (nothing blocking) — monitoring posture. Pipeline/status is center; chat is collapsed.
- **Action-required mode** (approval gate pending, interrupt fired, agent asked a question) — a hero callout dominates the viewport until resolved. Everything else dims.
- **Conversational mode** (user engaged in chat with PM) — chat pane expands; pipeline state compresses to a status strip.
- **Drill-down mode** (user clicked an eval, dataset, artifact, or handoff record) — selected entity takes over with Bloomberg-grade density; breadcrumb back.

**Rationale:** Role-adaptive (D12) handles *who* is using the app; context-adaptive (D13) handles *what is happening right now*. These are orthogonal dimensions and both are required. Context-adaptive replaces the inferior "single static hero screen" pattern and avoids the complexity of "user-toggleable modes" — the app decides what to emphasize based on state, and the user is never asked to choose a layout.

**Tradeoffs:** Transitions between modes must feel smooth, not jarring. Motion design is elevated from decoration to load-bearing functionality. Accepted.

**Source:** Q5 of 2026-04-16 brand interview; my opinionated counter-proposal to role-adaptive-as-landing-page.

---

### D14: TUI ↔ Web Relationship — Parallel Windows Into Same Project Thread

**Decision:** The CLI TUI (`meta_harness/` backend) and the web app (`meta_harness_web/`) are **two parallel entry points into the same project thread**, not substitutes for each other. Both read/write the same checkpointed state via the shared `thread_id = project_id` contract. The web app is full-capability; it does not provide a reduced surface relative to the TUI.

**Implications:**
- Work started in the TUI is fully resumable in the web app, and vice versa, within the same project thread.
- The web app cockpit surface must expose every capability the TUI exposes (agent interaction, handoff inspection, artifact browsing, eval authoring, etc.) — the TUI is not a superset.
- The client portal surface is *only* available in the web app (no TUI client-facing mode). The TUI is an operator-only interface.

**Rationale:** User requirement: seamless cross-window workflows. "I should be able to make project progress inside the terminal and have all the information emitted to the web app." This aligns with the LangGraph Platform checkpointer model — state lives in the checkpointer, not in a particular UI — so this is architecturally free as long as both UIs are disciplined about reading/writing through the SDK, not through UI-local caches.

**Tradeoffs:** Requires the web app to ship full cockpit capability, which is a larger scope than a "status-display companion" to the TUI would be. Accepted — the operator audience (initially Jason, eventually handed-over clients) demands web-first cockpit parity.

**Source:** User clarification in 2026-04-16 brand interview.

---

### D15: Voice Principle — "Always Land The Plane"

**Decision:** Every agent output in Meta Harness — client-facing or cockpit-facing — must **take a stance**. Never enumerate options without ranking them. Never describe without recommending. Never hand the user a list of paths without telling them which one the agent would take and why. The user retains the right to disagree; the agent must have a position.

**Register-adaptation:** The voice principle is register-agnostic. Implementation varies by surface:

- **Client Portal (warm-knowledgeable-peer register)** — complete sentences, light warmth, explanatory "why" included. Example: *"I've drafted the PRD. I have concerns about scope item 3 — the external-data dependency adds roughly two weeks. My recommendation is to cut it from v1 and revisit in v1.1. Want me to proceed with that trim?"*
- **Developer Cockpit (precise-technical-operator register)** — spare, fragmented, telegraphic, no softeners. Example: *"PRD scoped. Blocker: scope item 3 adds 2wk external-data integration. Recommend cut from v1. Approve trim?"*

Same backbone (opinionation + recommendation); different bandwidth (warmth + explanation vs. precision + terseness).

**Rationale:** The default behavior of LLMs is to hedge — to produce enumeration-without-recommendation, description-without-stance, list-without-ranking. This default is *adversarial* to user leverage. Every output that hedges is an output that pushes decision-making back onto the user and forfeits the agent's value. "Always Land The Plane" is the system-wide antidote and must be encoded in every agent's system prompt.

**Tradeoffs:** Opinionated agents occasionally recommend the wrong thing. Mitigated by: (a) recommendation always includes the "why" so the user can inspect the reasoning; (b) users can still override; (c) an agent that is wrong-with-reasoning is more useful than an agent that is merely-correct-by-not-committing.

**Source:** Q6 of 2026-04-16 brand interview; user-articulated pain with LLM hedging.

---

### D16: Naming Status — Open, Tested Per Visual Family

**Decision:** "Meta Harness" is a **working codename, not a final product name**. The final name is deferred until after the three-family visual mockup exploration completes. Each family's mockup brief will propose 2–3 candidate names that align with that family's visual/emotional register; naming decisions are made in context with visual identity, not in isolation.

**Constraints on the final name:**
- Must work in both surfaces — sounds natural on a client-facing portal header *and* in a developer's cockpit chrome.
- Must support ownership-transfer semantics (the "soft handover" model) — a client receiving cockpit keys should feel they now "own" the named product, not that they've been granted temporary access to Jason's tool.
- Must not be "Client Portal," "Dashboard," "Console," or any other category-word that erodes product identity.

**Rationale:** Names carry emotional weight and brand-family association. Testing names alongside visual mockups is cheaper than committing to a name first and then discovering the visuals contradict its register (e.g., "Forge" + a soft pastel palette would be dissonant).

**Tradeoffs:** All pre-launch documents, code identifiers, and AGENTS files continue to use "Meta Harness" as placeholder. Accepted — rename is a finite refactor cost once the winning name is selected.

**Source:** Q3 of 2026-04-16 brand interview.

