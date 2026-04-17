# Meta Harness — Brand & Product Positioning

**Status:** Active source of truth
**Last Updated:** 2026-04-16 (late evening update: D18 pure-broadcast-portal locked)
**Owner:** Jason (product vision) + Cascade (marketing/design)
**Companion documents:** `DECISIONS.md` (locked decisions D1–D18), `AD-WebApp.md` (architecture), `ROADMAP.md` (current plan), `CHANGELOG.md` (audit trail), `mockup_briefs/` (visual family explorations)

---

> **Read this document first** if you are designing, writing copy for, building components for, or naming features in this product. Every mockup, every system prompt, every agent output, every marketing asset descends from what is written here.

---

## §1 — What Meta Harness Is

Meta Harness is an **LLM application development studio operated by a team of AI agents.** The user (initially Jason, a consultant) brings a client's idea; the agents — Project Manager, Researcher, Architect, Planner, Developer, Harness Engineer, Evaluator — scope, design, plan, build, and evaluate the resulting LLM application. The user directs them. The clients watch them work.

It is simultaneously:

- **A tool** — a working environment Jason uses to deliver LLM applications to clients faster and with higher quality than he could as a solo operator.
- **A product** — a client-facing **observation window** that gives stakeholders real-time transparency into work-in-progress. Stakeholders watch, review artifacts, and consume progress narratives; they do not transact with the agent team directly. All stakeholder↔agent interaction is mediated by the operator (see D18).
- **A transferable asset** — at project delivery, the user can hand the client the "keys to the cockpit," upgrading them from stakeholder (observation-only) to self-service operator (full agent-interaction capability). This capability delta is the soft-handover monetization mechanism.

---

## §2 — Brand Posture *(→ D9)*

**Meta Harness is a premium orchestration layer that sits visibly above the LangChain ecosystem.**

- Our brand is the hero. LangChain and LangSmith are credited but visually subordinate.
- We share *some* design vocabulary with the LangChain family — enough that an AI-literate buyer recognizes "this team knows the stack." We do **not** copy LangSmith's chrome.
- Our color palette, typography, and iconography are our own. A user switching from LangSmith to Meta Harness should feel a clear tier-change — "this is the premium instrument above the raw-observability layer."

### Reference posture in other categories

| Category | Equivalent move |
|---|---|
| Design & code | Linear sits *above* GitHub. Same ecosystem, premium identity. |
| Analytics | Datadog sits *above* raw Prometheus. Curation, not raw data. |
| Finance | Bloomberg Terminal sits *above* Reuters wire feeds. Narrative over pipe. |

The pattern is consistent: the curator of signal beats the provider of raw data *as long as the curation is honest and the hand-off is graceful*.

### What we are *not*

- We are **not** a LangChain reseller, a LangSmith skin, or a LangGraph tutorial.
- We are **not** a general-purpose AI chat product (ChatGPT, Claude.ai) — we are a *project-structured* environment with a specific workflow.
- We are **not** a trace-viewer, a prompt IDE, or a model-evaluation tool in isolation. We are the *executive layer* that coordinates all of those.

---

## §3 — Product Philosophy *(→ D10, D11)*

### The Catchphrase

> **We provide all of the signal. If you need to zoom in on trajectories, we link you directly to where you need to be inside LangSmith.**

### What Meta Harness Surfaces (First-Class)

- **Eval criteria** — what is the target application being tested against?
- **Scoring rubrics** — full rubric with per-score descriptions ("score 1 means X, score 5 means Y"), binary test descriptions, and pass/fail thresholds.
- **Experiment results** — scorecards, pass/fail summaries, attempt counts, trends across runs.
- **Datasets** — public and held-out dataset previews (with appropriate access control — held-out is cockpit-only per D18), row-level inspection of business-logic examples.
- **Pipeline state** — current phase, current active agent, handoff history as a readable narrative.
- **Packaged deliverables** — PRDs, design specs, implementation plans, final artifacts — rendered as first-class in-app documents. *Cockpit:* approve/reject/revise actions available to the operator. *Portal:* rendered for stakeholder review only; no interactive submissions (D18).
- **Agent conversations** — **cockpit-only.** The operator talks to the PM (or currently active agent) in a chat surface. *The Client Portal has no chat affordance by design (D18).*

### What Meta Harness Does *Not* Surface (Link Out To LangSmith)

- Raw trace timelines, tool-call sequences, token-level streams.
- Thread/run viewers as LangSmith renders them.
- Anything that would require embedding LangSmith UI.

### The Operational Test

When proposing any new feature, ask: **"Is this providing distilled signal, or is this re-implementing LangSmith's trace viewer?"**

- If the former — ship it.
- If the latter — stop. Link to LangSmith instead.

---

## §4 — Audiences *(→ D12)*

Meta Harness serves two primary audiences inside a single app via **role-adaptive surfaces**:

### Audience A: The Operator (Developer Cockpit)

**Who:** Jason in v1. Eventually any operator who uses Meta Harness to build LLM applications for clients. Also: any client who has been granted cockpit access via soft handover.

**Mindset:** *"I am directing a team of agents. I need full visibility, high leverage, and direct routes to every artifact and affordance."*

**Surface:** Developer Cockpit — high density, all 7 agents visible, handoff log, eval authoring, drill-down into any artifact, LangSmith deep links inline.

**Register:** Precise technical operator (see §6).

### Audience B: The Client (Client Portal)

**Who:** External stakeholders — founders of small-to-medium businesses, executives at enterprises, occasionally their AI-savvy technical leads. Most are AI-literate enough to have written ChatGPT prompts; few are deeply technical. They are paying for an outcome, not a tool.

**Mindset:** *"I want to see my project progressing, review the work my operator is doing on my behalf, and read what the agent team has produced. I'll give feedback through my operator when something needs my input."*

**Surface:** Client Portal — **pure observation window** (D18). Distilled signal, packaged deliverables rendered as first-class documents, phase status, eval results, handoff narratives. **No chat, no approval buttons, no interactive submissions.** All feedback, approvals, and clarifying questions flow through the operator as exclusive intermediary. This is by design: the portal's job is transparency and trust-signaling; agency lives in the paying relationship with the operator.

**Register:** Warm knowledgeable peer (see §6) — in **monologue form only**. The PM agent narrates; the stakeholder consumes.

### Access model

- Role is assigned per-user per-project. A single human can be an operator on their own projects *and* a stakeholder (via client view) on projects someone else is operating.
- **Soft handover is a product feature**: at delivery, the operator grants the client cockpit access — a genuine capability unlock under D18 (stakeholder-mode cannot transact with agents; cockpit-mode can). The client's next project uses the delivered project's UUID as seed context.

---

## §5 — Interaction Model *(→ D13)*

The UI is **context-adaptive** — it reshapes based on project state, not user action. Four modes exist, but their scope differs per surface under D18:

| Mode | Trigger | Hero | De-emphasized | Portal? | Cockpit? |
|---|---|---|---|---|---|
| **Ambient** | Nothing blocking | Pipeline / project status | Chat (collapsed, cockpit only) | ✅ | ✅ |
| **Action-required** | Gate pending, interrupt fired, agent asked a question | Hero callout card dominates viewport | Everything else dims | ❌ (no stakeholder actions per D18) | ✅ |
| **Conversational** | User engages chat | Chat pane expands | Pipeline compresses to status strip | ❌ (portal has no chat per D18) | ✅ |
| **Drill-down** | User clicks an eval / dataset / artifact / handoff | Selected entity fills viewport | Breadcrumb trail back | ✅ | ✅ |

**Portal supports *ambient* and *drill-down* only.** Cockpit supports all four. When a gate is pending in the portal, the stakeholder sees the deliverable rendered as a beautifully-presented read-only document — they can drill into it, but there's no "required action" framing because no action is theirs to take.

### Progressive Reveal Across Project States *(→ `JOURNEY.md`)*

Within any surface, the four modes above describe *within-state* UI responses. Between states — i.e., as a project progresses from freshly-scoped through architecture through development — the UI undergoes **compositional change**, not just panel-toggle change. The product is a **progressive reveal** across five journey states (t=0 virgin through t=4 rich). At t=0, the operator sees a single conversational surface and nothing else; at t=4, they see the full cockpit. Each state is a genuinely different composition earned by the project state that now exists. Full specification lives in `JOURNEY.md`.

---

## §6 — Voice *(→ D15)*

### The Universal Principle: "Always Land The Plane"

Every agent output must take a stance. The default LLM failure mode is to enumerate options without ranking them, describe without recommending, and hand the user lists-without-guidance. This is adversarial to user leverage. **Our agents have positions.** Users can override; agents must not abdicate.

### Register by Surface

| | **Client Portal** | **Developer Cockpit** |
|---|---|---|
| Persona | Warm knowledgeable peer, **in monologue** | Precise technical operator, in dialog |
| Mode | One-way narration (stakeholder reads; no reply channel per D18) | Two-way interaction (operator chats, approves, drills, overrides) |
| Sentence shape | Complete sentences, contractions OK, explanatory "why" | Fragments, declarative, no hedging |
| Warmth | Light — friendly consultant, not bubbly | Minimal — respect the reader's time |
| Recommendation style | *"My recommendation: X. Because Y. Your operator will carry this back."* | *"Recommend X. Blocker: Y. Approve?"* |
| Opinionation | Required | Required |

### Anti-patterns (do not ship)

- *"Here are a few options you could consider..."* (no recommendation)
- *"There are several ways to think about this..."* (hedging)
- *"It depends on your priorities..."* (abdication)
- *"I could go either way, but..."* (false modesty that forfeits value)

### Approved patterns

- *"I recommend X because Y."*
- *"X is the right move here. Proceed?"*
- *"Two options. Pick X over Y because Z. Override if you disagree."*

---

## §7 — Relationship to the LangChain Ecosystem

We are **ecosystem-native without being ecosystem-bound**.

### What we inherit

- **Technical credibility** with the AI-literate buyer. When a founder sees us built on LangGraph + Deep Agents + LangSmith, they trust the stack.
- **Best-in-class observability** via LangSmith deep links. We don't compete with LangSmith; we point to it.
- **Deep Agents harness** as our agent runtime. We do not reimplement agent middleware, memory, filesystems, summarization, or sub-agent composition — LangChain ships those.

### What we provide on top

- **Multi-agent project coordination** via the Project Coordination Graph (PCG). Six specialist agents plus a PM, working through phase gates.
- **Narrative layer on observability.** LangSmith shows raw trajectories; we show "what this agent accomplished and whether it's above threshold."
- **Client-facing surface.** LangSmith has no concept of an external stakeholder who watches work without seeing agent internals — we do.
- **Project artifact lifecycle.** PRDs, specs, plans, deliverables as first-class artifacts with approval workflows.

### What this means visually

**No shared chrome.** Because LangSmith never appears inside our app (D11), we are not constrained to match LangSmith's palette, typography, or layout metaphors. The three visual families under exploration (Linear, Bloomberg, Stripe) are all fair game — none of them need to look like LangSmith to function.

---

## §8 — Competitive Position

| Segment | Example products | How we differ |
|---|---|---|
| LLM chat products | ChatGPT, Claude.ai, Perplexity | They are *open-ended assistants*. We are a *project-structured agent team* with phase gates and multi-agent coordination. Buyers choose us when the job is "build an LLM application," not "answer my question." |
| Prompt IDEs | PromptLayer, Humanloop, Vellum | They focus on *prompt iteration*. We focus on the *full project lifecycle* — scope, design, plan, build, evaluate, deliver. Prompt iteration is one step in our pipeline, not the product. |
| Agent frameworks | LangChain, LlamaIndex, CrewAI | They are *libraries for developers*. We are a *product for operators*. We are built on LangChain; we are not competing with it. |
| Evaluation platforms | LangSmith, Braintrust, Arize Phoenix | They focus on *observability and evaluation*. We focus on *coordinated building* — observability is one layer of our stack, provided by LangSmith, surfaced through our summary views. |
| AI consulting services | boutique agencies, solo consultants | We are the *tool that makes a solo consultant more capable than a boutique*. We don't compete with consulting — we empower it. Jason's own consulting practice is the first customer of Meta Harness. |

### The unique wedge

> Meta Harness is the first product that combines **project-coordinated multi-agent build** with a **client-facing portal** and a **cockpit-handover monetization model**. No competitor currently ships all three in one environment.

---

## §9 — Naming *(→ D16)*

"Meta Harness" is a **working codename** (specifically: `meta-harness-web` for the product itself; `meta_harness` for the backend harness). The final name is deferred until after t=0–t=2 journey-state mockups render across all three visual families and the visual evidence supports a confident selection. Each family brief proposes 2–3 candidate names aligned with its visual register.

### Constraints

- Works in both surfaces — natural on client-portal header *and* in developer-cockpit chrome.
- Supports ownership-transfer semantics — the client receiving cockpit keys should feel they now *own* the named product.
- Is not a category word (no "Console," "Dashboard," "Studio," "Portal," "Platform" as the primary name).

### Disallowed name patterns

- Anything ending in *"AI"* — hackneyed, category commodity.
- Anything prefixed with *"Meta"* — ambiguous (Facebook), cliché for multi-agent systems.
- Anything that requires a tagline to explain — if a founder can't remember the name after one introduction, it's wrong.

---

## §10 — The Three Visual Families Under Exploration

All three families share this positioning document. They differ in visual execution of the same positioning.

| Family | What it tests | Primary audience bias |
|---|---|---|
| **Linear / Vercel / Arc** | *One visual language flexes across both surfaces.* Sophisticated near-monochrome. Dark-primary. Precise motion. | Unified — tests whether a single design scales from client to cockpit. |
| **Bloomberg / Palantir / Datadog** | *Cockpit-primary; client portal is softened cockpit.* Dense, instrument-grade, semantic color, monospace/semi-monospace. | Operator-biased — tests whether an instrument brand can soften gracefully. |
| **Stripe / Notion / Retool** | *Client-primary; cockpit is densified portal.* Light-primary, confident spacing, refined sans-serif, calm authority. | Stakeholder-biased — tests whether a stakeholder brand can scale to power-user density. |

See `mockup_briefs/family-linear.md`, `mockup_briefs/family-bloomberg.md`, `mockup_briefs/family-stripe.md` for detailed per-family briefs.

### Decision process

Each family produces mockups of the same canonical screens for both the Client Portal and the Developer Cockpit. We compare side by side and select based on:

1. **Brand coherence** — does the family's execution actually project "premium orchestration layer"?
2. **Cross-surface fit** — does the gap between Portal and Cockpit within a family feel like *one brand, two modes* or *two different products*?
3. **Voice compatibility** — does the visual register fit the "Always Land The Plane" voice in both its warm and precise forms?
4. **Naming resonance** — do the candidate names proposed with the family feel right *with* the visuals?

---

## §11 — What This Document Is Not

- This document is **not a UX specification.** It does not define component APIs, state shapes, or pixel-level layouts. Those live in `AD-WebApp.md` and future component specs.
- This document is **not a style guide.** It does not lock colors, fonts, or spacing scales. Those are invented per-family in the mockup briefs and consolidated in a style guide only after a family is selected.
- This document is **not the backend architecture.** The agent topology, PCG contract, and middleware stack are defined in `meta_harness/AD.md`.
- This document **can be challenged.** If a decision here is wrong, open an entry in `CHANGELOG.md` and propose the revision. Positioning is load-bearing and deserves rigor, not reverence.

---

## §12 — Canonical Summary (TL;DR for new contributors)

> Meta Harness is a **premium orchestration layer** above the LangChain ecosystem. It is an **LLM application development studio** where **a team of AI agents** scope, design, plan, build, and evaluate LLM applications for clients. It has **two surfaces**: a **client portal** (pure observation window, warm PM-narrated monologue) and a **developer cockpit** (dense, instrument-grade, full-leverage, operator-interactive). Per D18, stakeholders watch and read; operators are the 100% exclusive interaction channel with the agent team. Portal is ambient/drill-down only; cockpit supports all four context-adaptive modes. All agents speak with opinionated voice (**"Always Land The Plane"**) — warm monologue to clients, precise dialog to operators, never hedging. We **link out to LangSmith** for raw trajectory detail; we never embed LangSmith's UI. Our differentiation is **project-coordinated build + observation-only client portal + cockpit-handover stickiness** — no competitor ships all three, and the observation-only posture is what makes the handover a genuine capability unlock instead of a permissions toggle.
