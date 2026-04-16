# Mockup Brief — Family A: Linear / Vercel / Arc

**Family archetype:** Sleek contemporary premium
**Primary hypothesis tested:** *A single tasteful design language can flex across both surfaces (Client Portal and Developer Cockpit) without needing two different brand expressions. The surfaces differ in density and chrome, but share palette, type, and motion.*
**Primary audience bias:** Unified — designed for the AI-literate operator who appreciates that their tools look as good as the product they're shipping; the client portal inherits the same taste and feels like a peer product.
**Governing docs:** `POSITIONING.md`, `DECISIONS.md` D9–D16, `AD-WebApp.md` §1

---

## §1 — Emotional DNA (the 5-second test)

When someone opens the app, they should feel: *"This is a serious modern software product. The people who built this care about craft. It is fast, precise, and quietly confident."*

No ornament. No stock illustrations. No rounded corners larger than necessary. The design breathes but never sprawls. Information is dense when it needs to be, restrained when it doesn't. Motion is present but never decorative — every transition communicates state change.

Think: *Linear's Inbox, Vercel's deployment dashboard, Arc's command bar, Raycast, Height, Cron (pre-Notion), Perplexity Pro's chat UI*.

---

## §2 — Brand Tokens (proposed, to be refined)

### Palette

**Default mode: Dark (primary development environment)**
- Base: `#0A0A0A` (near-black, warm)
- Surface: `#121214` (subtle elevation)
- Surface elevated: `#1A1A1E`
- Border: `#232326` (barely-there separators)
- Text primary: `#EDEDEF`
- Text secondary: `#A1A1AA`
- Text tertiary: `#52525B`
- Accent (brand): **ONE precise color — candidates: electric indigo `#6366F1`, precise violet `#8B5CF6`, or signal green `#22C55E`. Single accent; used sparingly for brand moments and active affordances.**
- Semantic: success `#10B981`, warning `#F59E0B`, danger `#EF4444`, info `#06B6D4`

**Light mode (excellent, not an afterthought)**
- Base: `#FAFAFA`
- Surface: `#FFFFFF`
- Border: `#E4E4E7`
- Text primary: `#09090B`
- Accent unchanged from dark mode

### Typography

- **Display/UI:** `Inter` (variable), optical sizes, or the custom Linear-like sans that some agencies license. Fallback: system-ui. Crisp at small sizes, weight flexibility.
- **Monospace:** `JetBrains Mono` or `Geist Mono`. Used for code, IDs, timestamps, any structured data.
- **Scale:** 12 / 13 / 14 / 16 / 20 / 24 / 32 / 48 — compact, deliberate. Body copy is 14px, not 16px.
- **Weights:** 400 regular, 500 medium, 600 semibold. No bold.

### Motion

- **Timing:** 120–180ms for state changes, 220ms for layout reflows, 400ms *max* for drill-downs.
- **Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` (Linear's signature feel — fast start, soft settle).
- **Principle:** every motion communicates *causality* (this changed *because* that happened). Nothing moves for decoration.
- **Streaming token animation:** gentle fade-in of each token, never jittery, never mechanical.

### Density baseline

- Default density: **medium-high.** Clear hierarchy but not cockpit-dense. The Cockpit surface increases density; the Client Portal reduces it — but both surfaces share baseline spacing tokens.
- Generous line-height (1.5–1.6 for body copy) even at compact sizes.
- Minimum touch target 32px — this is a power-user tool primarily, not a mobile-first experience.

---

## §3 — Candidate Product Names (for this family)

| Name | Rationale | Risks |
|---|---|---|
| **Atlas** | Cartographic, structural — implies mapping complex projects. Short. Web-available as product name is crowded (Atlas GraphQL exists) but pronunciation-instant. | Some ecosystem collision; may need a qualifier. |
| **Meridian** | Precise, cardinal, orientation. Uncommon as a software brand. Sounds premium without being pretentious. Works as a URL (`meridian.dev`). | 9 letters — slightly long for a logo. |
| **Lattice** | Structural, technical, modern. Implies interconnected agents. Lattice HR exists as a brand collision — may need to be "Lattice Studio" or similar. | Biggest collision risk. |

**Family leader: Meridian.** Works in both surface registers, carries a "sophisticated instrument" connotation, isn't already a commodity tech word.

---

## §4 — Canonical Mockup Screens

All three families mock up the **same canonical project state** for apples-to-apples comparison:

> **Project:** "Tavern Assistant" — a conversational restaurant-menu agent for Luma Tavern Group (fictional midmarket restaurant chain client).
> **Current phase:** Architecture. Architect has returned a design package to the PM. PM is packaging for stakeholder approval (Gate 2).
> **Pipeline so far:** PM → HE (eval suite authored) → PM → Researcher (research bundle returned) → PM → Architect (design package returned) → PM (now packaging for stakeholder review).
> **Eval suite:** 5 rubric criteria (score 1–5), 3 binary tests (pass/fail). 2 experiments already run during eval calibration.
> **Datasets:** 1 public dataset (60 examples of real customer queries), 1 held-out dataset (20 examples, locked to HE).

### Screens required (both surfaces unless noted)

1. **Project landing** — ambient mode, user just logged in, no action required.
   - *Cockpit:* pipeline status timeline + active agent + recent handoffs + eval status card + chat pane (collapsed).
   - *Portal:* current phase prominently, "Next action from you" card (none pending yet), deliverables-so-far list, chat-with-PM card.

2. **Approval gate moment** — action-required mode, Gate 2 approval is waiting on the user.
   - *Cockpit:* hero callout "Gate 2 — Design Package ready for your review" with the packaged deliverable inline, approve/revise/reject buttons.
   - *Portal:* same hero callout, but wrapped in warmer language, with the packaged design document (rendered as a first-class in-app document) and a chat affordance to ask the PM questions about it.

3. **Eval suite detail** — drill-down mode, user clicked into the HE's eval suite.
   - *Cockpit:* full rubric with all 5 criteria, per-score descriptions, 3 binary tests, both dataset previews (public + held-out), experiment history table, "↗ View run in LangSmith" links per experiment.
   - *Portal:* same rubric but with HE's authored narrative paragraph at the top explaining *why* these criteria matter for Luma Tavern's use case; public dataset shown, held-out dataset shown as "Held-out (operator-only)" with no preview.

4. **Chat with PM** — conversational mode, user is mid-scoping conversation.
   - *Cockpit:* chat pane takes ~60% of width, PM conversation with timestamps and `lc_agent_name` attribution, collapsed right rail with phase/handoff compact view.
   - *Portal:* chat takes ~70% of width, softer framing, "You are chatting with: the Project Manager" header, no right rail at all.

5. **Handoff log narrative** — drill-down mode, user clicked on the handoff timeline.
   - *Cockpit only:* full `handoff_log` entries as a table with source/target agents, reason enums, briefs, artifact paths, timestamps. Each row expandable for full brief text.

6. **LangSmith link treatment** — a component specimen, rendered in context (on an experiment card).
   - Both surfaces: the consistent `↗ View in LangSmith` affordance. Small, understated, not competing for attention.

### Out of scope for this brief

- Login / auth screens
- Project picker (D8 — no landing page for v1, but there may be a multi-project switcher if applicable)
- Settings, billing, onboarding

---

## §5 — Voice Exemplars

The family's visual register must support both voice modes from D15. Sample microcopy rendered in this family's aesthetic:

### Client Portal (warm-knowledgeable-peer register)

**Gate 2 approval hero:**
> *"Meridian's design package is ready for your review. The Architect flagged two tradeoffs worth your opinion — both are marked in the document. My recommendation: approve as-written; the tradeoffs are sensible for v1. Want to review?"*
> [ Review Design Package ] [ Chat with PM ]

**Empty state (no projects yet):**
> *"No projects yet. To start, share what your client needs — a summary, a transcript, a brief — and I'll scope the PRD with you."*

### Developer Cockpit (precise-technical-operator register)

**Gate 2 approval hero:**
> *"Gate 2 pending. Design package ready. 2 tradeoffs flagged. Recommend: approve. Override?"*
> [ Approve ] [ Request revision ] [ Inspect package ]

**Empty state:**
> *"No project loaded. `cmd-K` to open project picker."*

### Anti-patterns (do not ship — these are what we're avoiding)

- *"There are a few things you could do next..."* (no recommendation)
- *"Please review the design package at your convenience..."* (soft, unowned)
- *"The Architect has completed its work..."* (passive, no stance)

---

## §6 — Evaluation Criteria

When reviewing the Linear-family mockups alongside the other two families, judge on:

1. **Cross-surface coherence** — does the Client Portal feel like the same product as the Cockpit, or like two products that share a logo? (Linear's hypothesis is that they *should* feel like the same product.)
2. **Premium signal** — does the UI project "premium orchestration layer" (D9) without pretension? Is it obviously better-crafted than LangSmith without copying LangSmith?
3. **Voice fit** — does the typography and spacing support both warm and precise copy registers? Or does it force the voice toward one or the other?
4. **Stakeholder readability** — can a non-technical founder navigate the Client Portal on first sight, or does it feel hostile to non-developers?
5. **Name resonance** — do the candidate names (Atlas, Meridian, Lattice) sound right *in* the visuals, or do they clash?

---

## §7 — What This Family Is Weakest At (honest failure modes)

- **Cockpit density** — Linear's aesthetic prefers breathing room. The Cockpit surface will need to *push* the family toward its density ceiling. If we find we can't get enough data per pixel, this family loses to Bloomberg.
- **Stakeholder warmth** — Linear's default is cool and precise. The Client Portal must find warmth through copy and spacing alone, not through illustration or color-warmth. If it feels sterile to clients, this family loses to Stripe.
- **Agent personification** — Linear's restraint means no illustrated agent avatars. Agent identity is expressed through color-coded badges and name labels only. If agent personification ends up critical, this family is constrained.
