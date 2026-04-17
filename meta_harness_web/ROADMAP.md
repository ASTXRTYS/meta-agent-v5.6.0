# Meta Harness Web — Current Roadmap

**Status:** Active
**Last Updated:** 2026-04-17 (J0-J7 journey nomenclature normalized)
**Working codename:** `meta-harness-web` — formal name deferred until J0-J3 mockups render in all three families
**Owner:** Jason (product) + Cascade (design + execution)
**Companion documents:** `POSITIONING.md` (product vision), `JOURNEY.md` (design spec — progressive reveal states), `DECISIONS.md` (locked decisions D1–D18), `AD-WebApp.md` (open questions), `CHANGELOG.md` (audit trail)

---

## Where We Are

**18 decisions locked.** Architecture (D1–D7), brand posture + product philosophy + surface strategy + voice (D9–D16), portal first-login UX (D17), and the product thesis — **Pure Broadcast Portal** (D18) — are all committed. Together these define *what* Meta Harness is, *who* it serves, *how* the two surfaces relate, and *how* the voice expresses.

**Design approach locked (same evening):**

- **Journey-state, not screen-by-screen.** UI is a *progressive reveal* across eight PCG-grounded states (J0 Virgin → J7 Acceptance & Delivery). See `JOURNEY.md` for the full spec. Each state is a genuinely different composition, not a collapsed version of the final layout.
- **Three separate repos, not shared theme system.** Each family (Linear, Bloomberg, Stripe) gets its own independent Next.js app with genuine architectural and stylistic differences. No shared theme abstraction that encourages recoloring. Each repo is a full implementation of the journey states in its own style.
- **Live dev servers, not static HTML.** Each repo runs its own dev server. You inhabit each state at its own URL in Windsurf's browser preview, annotate in-context, iterate with hot reload per repo.
- **Working codename:** `meta-harness-web`. Name selection deferred — we'll pick a name once visual evidence from sequential family explorations supports a confident decision.

---

## First Session Boot Sequence

Open the IDE. Read this section. Choose the first family to explore. Approve one command. One dev server up within ~30 minutes of sitting down.

### Step 1 — Choose first family and scaffold one Next.js app

You choose which family to start with (Linear, Bloomberg, or Stripe). agent will propose one `create-next-app` command to scaffold into the corresponding directory:

- `meta_harness_web/app/linear/` — Linear family
- `meta_harness_web/app/bloomberg/` — Bloomberg family
- `meta_harness_web/app/stripe/` — Stripe family

With:
- Framework: Next.js 15, App Router
- TypeScript: yes
- Tailwind CSS: yes
- ESLint: yes
- `src/` directory: yes
- Import alias: `@/*`

You approve the command; agent runs it; one project scaffolded.

### Step 2 — Install shadcn/ui for this family 

agent proposes `shadcn@latest init` for this repo, with family-specific configuration sourced from the chosen `mockup_briefs/family-*.md` §2 palette + typography + motion tokens. This repo owns its own design system implementation.

You approve; agent installs + configures.

### Step 3 — Build J0 Virgin state

agent builds the first page: the virgin state per `JOURNEY.md` §4 (J0):

- Identity chrome (header with `Meta Harness` codename, minimal profile menu)
- Centered conversational input with the canonical placeholder from `JOURNEY.md`
- Small PM identity chip above or below the input
- PM-voiced opening message (from the voice exemplars per family)
- Full-viewport, styled per family's aesthetic

The repo kicks off its dev server. You open Windsurf's browser preview at the URL and react. You annotate; we iterate. First real design review.

---

## Sequential Family Exploration Process

Explore one family at a time through the journey states. Build progressively, close questions, discover new ones, then move to the next family. The process is open-ended — you decide when to stop exploring a family and move to the next, or when to commit to a family and build deeper.

### First Family Exploration

**Goal:** Choose one family (Linear, Bloomberg, or Stripe). Scaffold one repo. Build journey states progressively through that family's aesthetic. Inhabit each state in browser preview, annotate, iterate.

**Process:**
- Start with J0 Virgin state
- Build subsequent journey states (J1, J2, J3, etc.) as you decide
- Close questions that this family's approach resolves
- Discover new questions that arise from this family's implementation
- Decide when to stop this family's exploration and move to the next

**Design review:** At each journey state, inhabit the page in Windsurf's browser preview. Annotate reactions directly in-context. Iterate based on your feedback.

**Questions closed/discovered:** Document which questions from `AD-WebApp.md` this family's approach closes, and which new questions arise. This informs the next family's exploration.

### Second Family Exploration

**Goal:** Scaffold a second repo. Apply lessons learned from the first family. Build the same journey states through the second family's aesthetic lens.

**Process:**
- Scaffold the second family's Next.js app
- Build journey states, applying lessons from first family
- Compare: what questions closed differently? What new questions arose?
- Decide when to stop this family's exploration

**Design review:** Same process — inhabit, annotate, iterate per state.

**Learning transfer:** Document how lessons from the first family informed this family's exploration, and where this family diverged.

### Third Family Exploration (optional)

**Goal:** Scaffold the third repo. Apply lessons learned from the first two families. Build journey states through the third family's aesthetic lens.

**Process:**
- Scaffold the third family's Next.js app (if you want to explore all three)
- Build journey states, applying lessons from previous families
- Full comparison across all families at the journey states you've explored

**Design review:** Same process — inhabit, annotate, iterate per state.

### Family Commitment and Deep Exploration

**Goal:** Commit to one family based on evidence from sequential explorations. Build the full journey through rich state (J4-J7 if not already reached).

**Process:**
- Choose the winning family based on visual evidence and question closure
- Continue building remaining journey states in that family's repo
- Lock brand tokens (palette, typography, motion system codified)
- **Select the product name** from the winning family's candidate list (or a fresh proposal if visuals demand it). Per `DECISIONS.md` D16 naming policy.
- Any D13 / D17 amendments based on visual evidence
- Begin the style guide

### Post-Mockup — D19 (Auth & Seats)

Once visual family + name are selected and mockups stabilize, run the **D19 session**: grounded research into auth-provider options (Clerk / Supabase Auth / Auth.js / roll-our-own), Stripe subscription primitives for operator retainer billing, stakeholder viewer-only seat model. Lock D19 and begin implementation planning.

---

## Decisions Explicitly Revisitable During Mockup Phase

These were locked in prose; mockup evidence can overturn or amend them. If a mockup surfaces evidence that contradicts one, the revision path is: record the challenge in `CHANGELOG.md` → propose the revision → Jason approves → amend `DECISIONS.md`.

- **D13** (four context-adaptive modes) — already amended by D18 (portal is ambient + drill-down only). The journey-state work in `JOURNEY.md` extends D13 by specifying *between-state* composition changes; a formal D13 amendment may land once visual evidence arrives.
- **D17** (portal first-login UX) — Gate 1 hero framing, source-material visibility default, PM-as-face treatment. All three become visual hypotheses the moment J3 portal is rendered in Session 2.
- **D18** (pure broadcast portal) — **the single most important decision under test**. If mockups reveal the Portal feels hollow / purposeless / disengaging without any interaction affordance, we re-open. Known watch-item.

## Decisions Locked (Not Under Revision)

These are structural. Mockups express them; mockups should not challenge them.

- **D1–D7** — architecture, SDK contracts, framework selection.
- **D8** — internal-tool scope for v1.
- **D9–D12, D14–D16** — brand posture, product philosophy, LangSmith relationship, two-surface strategy, TUI↔web parallelism, voice principle, naming process.

---

## Current Known Risks

1. **D18 hollowness risk** — if the portal mockups feel disengaging without any stakeholder-initiated interaction, we need to fix the problem through richer narrative, better artifact rendering, selective animation, etc. — not by re-opening D18 unless evidence is overwhelming.
2. **Bloomberg-family stakeholder-readability risk** (per `mockup_briefs/family-bloomberg.md:164`) — family could feel intimidating to non-technical founders. The portal state in Bloomberg is the highest-signal artifact for evaluating this risk.
3. **Stripe-family cockpit-density ceiling** (per `mockup_briefs/family-stripe.md:166`) — light-mode, generous-spacing aesthetic may cap cockpit leverage at rich development states. This becomes visible when building deeper journey states.
4. **Linear-family warmth risk** — Linear aesthetic is cool/precise by default; Client Portal must find warmth through copy + spacing alone. The portal state in Linear is the highest-signal test.
5. **Sequential commitment risk** — risk that you invest deeply in one family's journey states before seeing the others, and later discover a different family would have been better. Mitigation: the process is open-ended — you decide when to stop exploring a family and move to the next. You're not locked into building all states for one family before seeing others.
6. **Learning transfer overhead** — lessons learned from one family must be consciously applied to the next. Without side-by-side comparison, you rely on memory and documentation. Mitigation: document observations and question closures per family as you go.

Each family brief's §7 documents its own honest failure modes. Track any of these that materialize during sequential explorations; they inform family selection.

---

## Quick-Reference: What's Where

| Document | Purpose |
|---|---|
| `POSITIONING.md` | Brand/product source of truth. Read this first. |
| `JOURNEY.md` | Design spec — eight PCG-grounded journey states (J0 Virgin → J7 Acceptance & Delivery). The *what-to-build* for every mockup session. |
| `DECISIONS.md` | D1–D18, full rationale per decision. |
| `AD-WebApp.md` | Residual open questions (§2), decision dependency map (§3). |
| `ROADMAP.md` (this file) | Current plan + tomorrow's boot sequence. |
| `AGENTS.md` | Frontend engineering conventions, SDK references. |
| `CHANGELOG.md` | Full audit trail of every edit to the above. |
| `mockup_briefs/family-*.md` | Three visual-family briefs — rich-state (J6/J7) visual specifications per family. Voice exemplars and candidate names remain useful; "canonical screens" are the endpoint of the reveal, not the starting point. |

---

## One-Line Summary

> Next: choose one family to explore, scaffold one Next.js app, build the **J0 Virgin state**, inhabit it in Windsurf's browser preview, annotate, iterate. Explore journey states progressively, close questions, discover new ones, then move to the next family. Open-ended process — you decide when to stop exploring a family and when to commit.
