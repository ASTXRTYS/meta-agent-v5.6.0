# Meta Harness Product, Brand & Positioning 
        Technical Decisions @meta_harness/AD.md & meta_harness/DECISIONS.md


---

## D1: Product Purpose 

**Decision:** 
- The website/app for the meta harness will serve as the public face of the application and may potentially be the first in a series of different applications that will be built as extention of the meta harness wich will extend the scope of what we offer as an Agents as a Service platform. The distinction and important thing to not is that we are bootstrapping an *AGENT FIRST BUSINESS THAT PUTS AI IN THE HANDS OF ENTERPRISES, SMALL-TO-MEDIUM BUSINESSES, INDIE DEVS AND AI AGENCIES; IN THE FORM OF AGENTIC AI (agents-as-a-service)*. 

- The first service we are offering is a team of agents that scope business, enterprise, individual needs and ultimatley output agent harnesses that automate workflows, augment staff productivity, enrich processes and ultimately deliver measurable ROI. This is what we precieve to be the main purpose businesses, big or small, are seeking the implementaion of ai in their organizations. 

- It is becoming more and more apparent that the path to driving real world value to humans via our product is to go headless. *mainly headless*
    - This will allow our agent team to go where the user needs them to go, not just where we build them to go.
    - This will also allow us to scale our product to multiple platforms and devices without having to build separate applications for each platform and device.
    - This also allows for a simpler approach to our Frontend/UI/UX

### Thesis: By being headless we focus on the harnesses we develop and spend most of our efforts in building the best possible sota hanress for our specific task. This means we can take a minimal approach to the UI/UX i.e(A web app that allows users, via a chat which langchain provides all the frontend primitaves for, to interact with our pm for scoping or interactively weighing in on decisions during spec phase or dataset building. The ux can be reduced to a chat with two side rails, displaying the highest level artifacts our agents produce in their own filesystem, and maybe some project management. The intuitiveness of this can be further fleshed our in the actual design phase of our front end. my vision is that wether headless or in the tui, artifacts, datasets, experiment results, and insights can all be captured easily becasue the agents output all of this anyway in thier composite filesystem backend).

- The "leader" of our first agent team is the Product manager (Open to changing name to LEADER), who serves as the main poc for the operator and or users to communicate with the team. other agents have the ability to ask questions but ultimatley the PM is the direct poc

***In the future we could have a team thats for GTM, sales, Product Design, etc. our ultimate premium offering could be a full offering where different divisions work together to deliver business interests effectively giving birth to a Native Agentic Ai Business***

**Note:** The idea behind this product began some time ago; see: https://www.langchain.com/blog/agentic-engineering-redefining-software-engineering?utm_source=twitter&utm_medium=social which is a blog dropped by langchain where top technical officers from cisco quite literally describe a take on agents that fully adds social proof that our concept is not only valid but also aligns with industry leaders.



thread=project id and due to this a dev who wants to actively play a role in the dataset curation, spec design and optimization loop can interact with the agent via the TUI and then pick up where he left off in the in the web app. or for example upon agreeance with the pm or harness engineer that a data set seems satisfactory and ready to be used as the training data for the target harness i.e(it gets accepted) it becomes surfaced in the web app, as a stored artifact that is easy to see, read and shows transperancy, it will most likey make the user feel something, seeing an actual artifact be emmited and know that the artifact plays as key component in the process of creating the target agent/harness. this same logic can be applied to any artifact that gets produced. 
Furthermore, when the agent runs experiments and is in an optimization loop, users can see a visualization of how each loop where the developer agetn optimizes the harness begins trending toward the desired behavior and capabilites desired in the target harness, these insights can be emitted in a truly delightful manner to our ui. its for these reasons that a sole purely headless approach is not appropraite for our product. 

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

### D12: Surface Strategy — Two-Surface Role-Adaptive (Stakeholder Portal + Developer Cockpit)

**Decision:** Meta Harness is **one web app with two role-adaptive surfaces**:

- **Stakeholder Portal** — for external clients, founders, executives, or internal executives in a company deployment. Shows distilled signal: current phase, eval results, packaged deliverables, gate moments rendered as read-only documents, and PM-authored narrative. Per D18, it has no chat, no approval buttons, and no state-changing affordances.
- **Developer Cockpit** — for the operator (initially Jason; eventually a handed-over client, internal developer team, or company operator). Full pipeline visibility, all 7 agents' activity, handoff log, eval authoring surfaces, drill-down into any artifact, LangSmith deep links, approval controls, and PM chat. High density, high leverage.

Both surfaces read from the **same PCG state, same project thread (`thread_id = project_id`), same data sources**. This is one product with two role-scoped sides, not two unrelated websites. They differ in layout hierarchy, density, access-controlled affordances, and voice register (see D15). Role is assigned per-user per-project via access control; a single human can have cockpit access on their own projects and stakeholder access on projects they are observing.

**Stickiness mechanism — soft handover:** At project delivery, the operator chooses (a) **retainer** — operator retains cockpit, client retains portal; or (b) **full handover** — client is granted cockpit access; the delivered project's UUID becomes seed context for their next scoped work with the PM. The web app is the product asset being transferred. Cockpit handover is a monetizable product feature, not just a UX pattern.

**Rationale:** Q5-clarify resolved this: stakeholders are external parties (clients of Jason's consulting practice, and eventually of any operator using Meta Harness) who require access-controlled separation from cockpit internals. The retainer-vs-handover split creates genuine product stickiness — clients either pay ongoing for operator-managed projects, or pay for the handover that grants them self-service capability. Both lanes monetize the app; a role-adaptive surface strategy is what enables both.

**Scope note:** This decision *extends* D8 (Internal Tool Scope — No Landing Page for v1) rather than replacing it. D8 correctly locked "v1 = internal tool + stakeholder portal." D12 specifies *how* that dual-audience product is organized structurally.

**Tradeoffs:** Two surfaces means roughly 2× the mockup work per visual family, and two sets of components to maintain in production. Mitigated by: shared data layer (same `useStream`, same reactive reads), shared component library (eval scorecard, dataset browser, LangSmith link treatment), and explicit design discipline — the two surfaces must share brand tokens even when they diverge in layout and density.

**Source:** Q5 + Q5-clarify of 2026-04-16 brand interview; extends D8. Extended by D18 on 2026-04-16. Clarified by Jason on 2026-04-17 that the same split applies to external-client and internal-company deployments.

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
- The stakeholder portal surface is *only* available in the web app (no TUI stakeholder-facing mode). The TUI is an operator-only interface.

**Rationale:** User requirement: seamless cross-window workflows. "I should be able to make project progress inside the terminal and have all the information emitted to the web app." This aligns with the LangGraph Platform checkpointer model — state lives in the checkpointer, not in a particular UI — so this is architecturally free as long as both UIs are disciplined about reading/writing through the SDK, not through UI-local caches.

**Tradeoffs:** Requires the web app to ship full cockpit capability, which is a larger scope than a "status-display companion" to the TUI would be. Accepted — the operator audience (initially Jason, eventually handed-over clients) demands web-first cockpit parity.

**Source:** User clarification in 2026-04-16 brand interview.

---

### D15: Voice Principle — "Always Land The Plane"

**Decision:** Every agent output in Meta Harness — client-facing or cockpit-facing — must **take a stance**. Never enumerate options without ranking them. Never describe without recommending. Never hand the user a list of paths without telling them which one the agent would take and why. The user retains the right to disagree; the agent must have a position.

**Register-adaptation:** The voice principle is register-agnostic. Implementation varies by surface:

- **Stakeholder Portal (warm-knowledgeable-peer register)** — complete sentences, light warmth, explanatory "why" included. Example: *"I've drafted the PRD. I have concerns about scope item 3 — the external-data dependency adds roughly two weeks. My recommendation is to cut it from v1 and revisit in v1.1. Want me to proceed with that trim?"*
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

---

### D17: Portal First-Login UX (Scoped)

**Decision:** Three aspects of first-time stakeholder portal entry are locked; the remainder of Q9 is deferred to dedicated decisions (D18, D20) noted below.

1. **First-login state** — a newly-invited stakeholder lands on a **pre-populated portal at the Gate 1 hero**: the scoped PRD is already rendered as a first-class in-app document, ready for review. No empty states, no guided tour. The PM's voice (per D15) carries any explanation inline.

2. **Operator-fed source material visibility** — raw inputs the operator fed to the PM during pre-scoping (call transcripts, summaries, briefs) live under a **collapsed "Source material" section, hidden by default, operator-controlled per-project toggle to reveal**. Default posture is "show the scoped output, not the sausage." Operators may enable source-material visibility when transparency is commercially advantageous (e.g., showing the client "here is what I heard you say, here is how I translated it" as a trust move).

3. **Identity & trust signaling** — the **PM agent is the face of the portal chrome** (header, navigation, primary conversational voice). The operator is named in a **small "Operated by" credit** with photo, clickable to reveal operator context. Not hidden, not dominant. This preserves the product's transferability (D12 soft handover, D16 name ownership-transfer constraint) — a handed-over client must feel they own the named product, not an operator's tool.

**Rationale:** These three points are the portal's first-impression contract and descend directly from D9 (premium orchestration layer), D12 (two surfaces, handover-as-feature), D15 (opinionated voice), and D16 (name must support ownership-transfer). They resolve cleanly and independently of the larger auth/billing architecture and commercial-discipline questions, so locking them tonight is low-risk and unblocks the first stakeholder-facing J3 mockups across all three visual families.

**Scope exclusions — deferred to dedicated decisions:**

- **D18 — Pure Broadcast Portal (Stakeholder-Side Product Shape)** *(see below, locked 2026-04-16 late evening).* Supersedes what was originally going to be D19's chat-gating question by resolving the underlying product-shape question: the portal has no chat affordance at all. D17's point 3 ("PM as portal chrome face") was written anticipating a conversational portal; under D18, "PM is the face" means PM is the **narrative voice** of the portal — all copy the stakeholder reads is PM-authored — not a conversational partner.

- **D20 (pending) — Auth & Seats.** Covers Q9.1 (invite mechanism) and Q9.2 (authentication + multi-seat). Scope simplified substantially by D18: stakeholder seats are **viewer-only** (no write actions to model); operator seats retain full cockpit-write capability; Stripe subscription primitives are for the operator-retainer relationship. Still requires a grounded research session (Clerk / Supabase Auth / Auth.js tradeoffs) before locking. Does NOT block canonical mockup screens (login/settings are out-of-scope in `mockup_briefs/*.md`).

**Tradeoffs:** Splitting Q9 across D17, D18, D20 produces more audit trail entries than a single monolithic onboarding decision would. Accepted — each record stays small enough to revise independently, and forcing closure on auth/billing/chat at 9:30pm on interview day would have locked decisions we would re-open within two weeks. In fact, the D18 scope-narrowing (which happened later that same evening) validated this caution: locking the originally-planned "chat-gating with per-project operator toggle" would have been overturned within hours by the product-shape conversation.

**Source:** Q9.3, Q9.4, Q9.6 of 2026-04-16 Q9 mini-interview; companion to `AD-WebApp.md` §2 Q9 residual sub-questions. Forward-references amended 2026-04-16 late evening when D18 locked.

---

### D18: Pure Broadcast Portal — Stakeholder-Side Product Shape

**Decision:** The Stakeholder Portal is a **pure observation window**, not a collaboration surface. Stakeholders read, view, and receive. They do not submit, approve, revise, reject, or converse *into* the system. The operator is the **100% exclusive interaction channel** between stakeholder and agent team. This is the product thesis for the stakeholder side.

**What this means concretely:**

- **No chat affordance on the portal side.** Does not exist. Not hidden, not toggleable, not feature-flagged — simply absent from the Stakeholder Portal surface. Chat-with-PM is a cockpit affordance only.
- **No approval / revision / rejection buttons on the portal side.** Stakeholders view rendered artifacts (PRDs, design packages, eval rubrics, packaged deliverables) but submit **no** state-changing actions.
- **All `ask_user` agent interrupts route to the operator.** Gate approvals, clarifying questions, every human-in-the-loop checkpoint is the operator's responsibility. The stakeholder never receives an agent interrupt directly.
- **Stakeholder feedback flows out-of-band and is carried in by the operator.** Email, calls, document markup, Slack — whatever channel the commercial relationship uses. The operator translates that feedback into cockpit actions.
- **PM agent is the narrative voice of the portal**, not a conversational partner. Every piece of copy the stakeholder reads (phase status, artifact introductions, eval explanations, handoff summaries) is PM-voiced and carries the "Always Land The Plane" opinionation (D15) — but the stakeholder consumes, never responds through the UI.

**Rationale:** This shape is the cleanest expression of the "premium orchestration layer" positioning (D9) and the "executive summary, not trace reimplementation" product philosophy (D10). It matches the Bloomberg Terminal / Datadog / Reuters reference pattern — curated signal for the reader, not a chat with the analysts. It eliminates commercial-scope-creep **by design, not by policy** — stakeholders literally cannot initiate scope expansion because they cannot message into the system. It sharpens the soft-handover monetization (D12) — handing over cockpit keys becomes a genuine capability unlock (stakeholder-mode cannot transact with agents; cockpit-mode can), not a permissions toggle. And it lets the voice principle (D15) express as pure monologue-with-stance in the portal, which is a tighter creative constraint and a stronger brand signal.

**What this closes:**

- **Q9.5** (first meaningful action, pre-gate chat semantics) — resolved. No chat exists; the stakeholder's "meaningful action" is *reading* the rendered PRD and conveying any response out-of-band.
- **Q11** (chat-with-PM availability gating) — resolved as inapplicable to the portal.
- **Previously-planned D19 (Commercial Scope Discipline & Chat Gating)** — moot. The question "when should chat be gated?" is answered by "portal has no chat."

**What this simplifies:**

- **D20 (auth) scope:** stakeholder seats are viewer-only. No write-scope permissions to model. Auth architecture shrinks.
- **Q3 (approval flow interaction, `AD-WebApp.md` §2):** becomes **cockpit-only**. Approvals are an operator action. The portal's rendering of a gate moment is purely informational ("The Architect has delivered the design package; your operator is reviewing it with you").
- **Q4 (Tier 2 subagent visibility):** **cockpit-only** in practice. Stakeholders don't need sub-agent detail.
- **Q6 (todo progress):** **cockpit-only** or heavily abstracted in portal (phase-level, not agent-level).
- **Q7 (sandbox IDE form):** **cockpit-only**. Stakeholders don't see agent filesystems.
- **Q8 (soft handover):** mechanism gets cleaner — granting cockpit credentials is a genuine capability unlock. The "upgrade experience" question is easier to answer.
- **Q12 (held-out datasets):** largely resolved by D18 — portal = hidden (stakeholders don't see the held-out set at all); cockpit = full operator access. Handover-inheritance edge case persists but narrows.
- **Mockup scope:** each family's **Screen 4 (Chat with PM)** becomes cockpit-only. Portal canonical screens shrink. Screen 2 (approval gate) portal treatment loses its action buttons and becomes a beautifully-presented informational view.

**Tradeoffs:**

- Clients who would specifically want to converse with the PM agent as a product feature cannot do so in v1. **Accepted** — the commercial discipline payoff and the positioning clarity are worth more than that feature. Clients who want direct agent access can pay for the soft handover and get *full* cockpit access, which is a stronger commercial story than "limited-chat tier."
- Some stakeholders may feel a lack of agency on first login ("I can't do anything in here"). **Accepted** — the portal's job is transparency and trust-signaling, not interactive agency. Agency lives in the paying relationship with the operator, who is named and reachable.
- If user research later reveals that stakeholders strongly want direct PM access, we'd need to revisit. **Accepted as a known watch-item** — this is a product-shape commitment that the visual mockup phase will stress-test; if the Stakeholder Portal feels hollow without chat in mockups, we re-open the question.

**Relationship to other decisions:**
- **Strengthens D9** (premium orchestration layer) — instruments don't chat back.
- **Strengthens D10** (executive summary) — summaries are read, not conversed with.
- **Strengthens D12** (soft handover monetization) — the capability delta between stakeholder-mode and cockpit-mode is now maximal.
- **Strengthens D15** (Always Land The Plane) — portal voice is pure opinionated monologue; cockpit voice is telegraphic operator dialog. The two registers are now structurally different, not just tonally.
- **Amends D13** (context-adaptive modes) — the Stakeholder Portal supports only **ambient** and **drill-down** modes. *Action-required* mode doesn't apply to the portal (actions are operator-owned). *Conversational* mode doesn't exist in the portal. Cockpit retains all four.
- **Amends D17 point 3** — PM is the **narrative voice** of the portal (always monologue), not a conversational face.

**Source:** 2026-04-16 late-evening scope-narrowing conversation following the Q9 mini-interview. Locked in response to Jason's product-lead judgment that the cleanest product shape is the one that makes commercial discipline structural rather than procedural. No interview prep; decision emerged from direct product reasoning about scope, positioning, and monetization alignment.

---

### D19: Mockup Scope — Two Product Sides Per Family Through Gate 1

**Decision:** The first meaningful mockup milestone for each visual family is **J0 through J3**, ending at the Gate 1 package: the Harness Engineer has returned the completed evaluation suite to the Project Manager, and the Project Manager now has the PRD, business-logic datasets, evaluation criteria, scoring rubrics, testing methodology, hypotheses, and related scoping artifacts ready for operator approval.

Each family must design **both product sides** by that milestone:

- **Developer Cockpit:** J0, J1, J2, and J3. The operator starts with the PM, sees the first working-draft hint, watches the PM hand the PRD to the Harness Engineer, then reviews/approves or requests revision on the Gate 1 package.
- **Stakeholder Portal:** J3 only for the first milestone, because the portal does not exist before Gate 1. It renders the same Gate 1 package as a read-only observation window with PM-authored narrative and no action affordances.

**Execution shape:** Originally, each visual family got an isolated Next.js app under `meta_harness_web/app/<family>/`, starting with Stripe. As of 2026-04-18, the frontend iteration convention has changed: active work happens in `meta_harness_web/app/meta-harness-web/`, while rejected or superseded source snapshots live under `meta_harness_web/mockup_iterations/<family>/pass-###/source/`. The D19 milestone remains the product coverage target; the source-tree convention is now active-app plus evidence archive.

**Rationale:** Stopping at J0 alone tests little beyond empty-state taste. Stopping at J3 tests the first real Meta Harness product moment: the operator has meaningful work to approve, the stakeholder has a real observation artifact, and D18's pure-broadcast portal thesis can be judged against a concrete deliverable instead of prose. Designing both sides is required because the Stakeholder Portal is a real product surface, not a reduced cockpit skin.

**Tradeoffs:** This makes each family pass heavier than a single operator-only J0 mockup. Accepted — a family cannot be evaluated without seeing whether its visual language can carry both cockpit control and stakeholder trust at the first gate.

**Source:** Jason clarification on 2026-04-17 frontend iteration session.
