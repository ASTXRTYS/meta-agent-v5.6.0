# Meta Harness Web — Current Roadmap

**Status:** Active
**Last Updated:** 2026-04-16 (late evening: D18 locked + journey-state/parallel-brand approach adopted)
**Working codename:** `meta-harness-web` — formal name deferred until t=0–t=2 mockups render in all three families
**Owner:** Jason (product) + Cascade (design + execution)
**Companion documents:** `POSITIONING.md` (product vision), `JOURNEY.md` (design spec — progressive reveal states), `DECISIONS.md` (locked decisions D1–D18), `AD-WebApp.md` (open questions), `CHANGELOG.md` (audit trail)

---

## Where We Are

**18 decisions locked.** Architecture (D1–D7), brand posture + product philosophy + surface strategy + voice (D9–D16), portal first-login UX (D17), and the product thesis — **Pure Broadcast Portal** (D18) — are all committed. Together these define *what* Meta Harness is, *who* it serves, *how* the two surfaces relate, and *how* the voice expresses.

**Design approach locked (same evening):**

- **Journey-state, not screen-by-screen.** UI is a *progressive reveal* across five canonical states (t=0 virgin → t=4 rich). See `JOURNEY.md` for the full spec. Each state is a genuinely different composition, not a collapsed version of the final layout.
- **Parallel-branded, not family-sequential.** All three families (Linear, Bloomberg, Stripe) get themed simultaneously via a shared theme system. Every journey-state mockup produces three family variants near-free. Down-selection happens on evidence across states, not on depth-first commitment to one family.
- **Live dev server, not static HTML.** One Next.js app with route-based addressing (`/[family]/[surface]/[state]`). You inhabit each state at its own URL in Windsurf's browser preview, annotate in-context, iterate with hot reload.
- **Working codename:** `meta-harness-web`. Name selection deferred — we'll pick a name once we've seen t=0–t=2 rendered across families and the visual evidence supports a confident decision.

---

## Tomorrow Morning Boot Sequence

Open the IDE. Read this section. Approve three commands. Dev server is up within ~30 minutes of sitting down.

### Step 1 — Scaffold the Next.js app (~5 min after approval)

Cascade will propose a `create-next-app` command to scaffold into `meta_harness_web/app/`:

- Framework: Next.js 15, App Router
- TypeScript: yes
- Tailwind CSS: yes
- ESLint: yes
- `src/` directory: yes
- Import alias: `@/*`

You approve the command; Cascade runs it; project scaffolds.

### Step 2 — Install shadcn/ui + theme infrastructure (~5 min)

Cascade proposes:

- `shadcn@latest init` (per D3)
- Three family theme configurations (Tailwind config + CSS variable sets for `linear`, `bloomberg`, `stripe` — sourced from each `mockup_briefs/family-*.md` §2 palette + typography + motion tokens)
- A `<FamilyProvider>` context component that reads the family from the URL and applies the corresponding theme
- Route structure: `src/app/[family]/[surface]/[state]/page.tsx`

You approve; Cascade installs + configures.

### Step 3 — Build the t=0 virgin state (~20 min)

Cascade builds the first page: the virgin state per `JOURNEY.md` §3 (t=0):

- Identity chrome (header with `Meta Harness` codename, minimal profile menu)
- Centered conversational input with the canonical placeholder from `JOURNEY.md`
- Small PM identity chip above or below the input
- PM-voiced opening message (from the voice exemplars per family)
- Full-viewport, themed three ways

Routes go live:
- `/linear/operator/virgin`
- `/bloomberg/operator/virgin`
- `/stripe/operator/virgin`

Cascade kicks off `pnpm dev`; you open Windsurf's browser preview at each URL and react. You annotate; we iterate. First real design review inside of ~45 minutes of starting the session.

---

## Session Sequence (Journey-State, Parallel-Branded)

Each session builds **one or two journey states across all three families in parallel** (not one family deep). Down-selection of families happens gradually, on evidence across states — not on premature commitment to a single family.

### Session 1 (tomorrow, ~90 min) — t=0 Virgin × 3 families

**Goal:** three inhabitable t=0 virgin-state pages, live on dev server. Operator surface only (portal doesn't exist at t=0 per D18 + `JOURNEY.md` §5).

**Artifacts produced:** 3 routes. `/linear/operator/virgin`, `/bloomberg/operator/virgin`, `/stripe/operator/virgin`.

**Design review:** You inhabit each URL. Compare *inside* the page, not in a gallery. Annotate reactions ("the Bloomberg header feels cold here," "Stripe's breathing room is perfect for this moment," "Linear's accent color on the PM chip is too loud," etc.). Cascade iterates in response.

**Closes / informs:** B5 (density philosophy) — t=0 is the most honest test of how each family handles restraint. Possible early signal on B3 (agent personification) since the PM chip is the product's first agent expression.

**Stretch goal if time remains:** begin t=1 (scoping) for whichever family felt strongest at t=0. Not committing to a family; just exploring whether the transition t=0 → t=1 lands in that family.

---

### Session 2 (day 2, ~90 min) — t=1 Scoping + t=2 Scoped × 3 families

**Goal:** render the transitions that show the UI actually adapting.

- **t=1 Scoping** — working draft card materializing in previously-empty space. Three family variants of the first memory-hint affordance.
- **t=2 Scoped** — PRD renders as a first-class document. Chat compresses to a side panel. First handoff prompt. **This is where the portal also appears for the first time** per `JOURNEY.md` §5; so t=2 doubles up — 3 families × (operator + portal) = 6 artifacts.

**Routes added:** 9 new routes.

**Design review:** Does the transition *feel* earned? Does the PRD-as-first-class-document land with craft? Does the portal at t=2 feel empty-in-a-good-way (per D18) or empty-in-a-bad-way?

**Closes / informs:** D17 (portal first-login UX) — now rendered, not imagined. Possible D17 amendment based on visual evidence. First evidence on B3 (agent personification) as the PM's voice meets the PM's visual treatment.

**Down-select signal:** if one family is clearly weakest after t=0 and t=1–t=2, we may **eliminate** it at end of Session 2 rather than continue carrying it through t=3 and t=4. Not a forced elimination — only if evidence is decisive.

---

### Session 3 (day 3, ~90 min) — t=3 Pipeline-Emergent

**Goal:** the first appearance of the left rail (engaged agents) and right rail (handoff log, emergent). This is where the cockpit *shape* becomes recognizable — but sparse. Portal variant shows narrative updates.

**Routes added:** 6 if all 3 families survive Session 2, 4 if one was eliminated.

**Design review:** Does the left rail land at the right scale? (Showing 3 engaged agents, not 7 ghost-idle ones, per `JOURNEY.md` §3 t=3 restraint.) Does the right rail feel informative without being overwhelming?

**Closes / informs:** Q2 (pipeline state display), Q4 (Tier 2 subagent visibility — if subagents surface in the left rail at this state), Q6 (todo progress display — first appearance in cockpit).

---

### Session 4 (day 4, ~90 min) — t=4 Rich + state-transitions

**Goal:** the full cockpit state that the mockup briefs described. This is the *endpoint* of the reveal, not the starting point. Rich state for both surfaces (per D18: cockpit = interactive, portal = observation-only).

**Artifacts produced:** the full canonical screens from each family brief, but now understood in the context of having been reached through the journey.

**Design review:** Does t=4 feel like the natural destination of the reveal? Does it feel overwhelming (failure mode) or empowering? Does the transition t=3 → t=4 land?

**Closes / informs:** Q1 (layout at rich-state), Q3 (approval flow interaction, cockpit-only per D18), Q5 (autonomous mode toggle — likely lives in the rich state).

---

### Session 5+ — Final family selection + brand-token lock

- Down-select to the one family that survives the full journey.
- Lock brand tokens (palette, typography, motion system codified).
- **Select the product name** from the winning family's candidate list (or a fresh proposal if visuals demand it). Per `DECISIONS.md` D16 naming policy.
- Any D13 / D17 amendments based on visual evidence.
- Begin the style guide.

### Post-Mockup — D19 (Auth & Seats)

Once visual family + name are selected and mockups stabilize, run the **D19 session**: grounded research into auth-provider options (Clerk / Supabase Auth / Auth.js / roll-our-own), Stripe subscription primitives for operator retainer billing, stakeholder viewer-only seat model. Lock D19 and begin implementation planning.

---

## Decisions Explicitly Revisitable During Mockup Phase

These were locked in prose; mockup evidence can overturn or amend them. If a mockup surfaces evidence that contradicts one, the revision path is: record the challenge in `CHANGELOG.md` → propose the revision → Jason approves → amend `DECISIONS.md`.

- **D13** (four context-adaptive modes) — already amended by D18 (portal is ambient + drill-down only). The journey-state work in `JOURNEY.md` extends D13 by specifying *between-state* composition changes; a formal D13 amendment may land once visual evidence arrives.
- **D17** (portal first-login UX) — Gate 1 hero framing, source-material visibility default, PM-as-face treatment. All three become visual hypotheses the moment t=2 portal is rendered in Session 2.
- **D18** (pure broadcast portal) — **the single most important decision under test**. If mockups reveal the Portal feels hollow / purposeless / disengaging without any interaction affordance, we re-open. Known watch-item.

## Decisions Locked (Not Under Revision)

These are structural. Mockups express them; mockups should not challenge them.

- **D1–D7** — architecture, SDK contracts, framework selection.
- **D8** — internal-tool scope for v1.
- **D9–D12, D14–D16** — brand posture, product philosophy, LangSmith relationship, two-surface strategy, TUI↔web parallelism, voice principle, naming process.

---

## Current Known Risks

1. **D18 hollowness risk** — if the portal mockups at t=2 / t=3 / t=4 feel disengaging without any stakeholder-initiated interaction, we need to fix the problem through richer narrative, better artifact rendering, selective animation, etc. — not by re-opening D18 unless evidence is overwhelming.
2. **Bloomberg-family stakeholder-readability risk** (per `mockup_briefs/family-bloomberg.md:164`) — family could feel intimidating to non-technical founders. t=2 portal in Bloomberg is the single highest-signal artifact for evaluating the risk; it lands in Session 2.
3. **Stripe-family cockpit-density ceiling** (per `mockup_briefs/family-stripe.md:166`) — light-mode, generous-spacing aesthetic may cap cockpit leverage at t=4. Rendered first in Session 4.
4. **Linear-family warmth risk** — Linear aesthetic is cool/precise by default; Client Portal must find warmth through copy + spacing alone. t=2 portal in Linear is the highest-signal test.
5. **Parallel-branding infrastructure cost** — the theme-provider + three-family Tailwind configuration is front-loaded work in Session 1. If the abstraction is wrong, later sessions pay for it. Mitigation: keep the theme system thin (palette + type + motion as CSS variables), avoid forcing shared components through complex family-prop gymnastics.
6. **Journey-state thrashing** — risk that t=0 looks great in Family A but t=3 looks great in Family B, and we can't commit. Mitigation: weighted evaluation — t=4 (rich state) carries the most weight because it's where users spend the most time; t=0 matters but is a 30-second moment.

Each family brief's §7 documents its own honest failure modes. Track any of these that materialize during Sessions 1–4; they feed the progressive down-select.

---

## Quick-Reference: What's Where

| Document | Purpose |
|---|---|
| `POSITIONING.md` | Brand/product source of truth. Read this first. |
| `JOURNEY.md` | Design spec — five progressive-reveal journey states (t=0 virgin → t=4 rich). The *what-to-build* for every mockup session. |
| `DECISIONS.md` | D1–D18, full rationale per decision. |
| `AD-WebApp.md` | Residual open questions (§2), decision dependency map (§3). |
| `ROADMAP.md` (this file) | Current plan + tomorrow's boot sequence. |
| `AGENTS.md` | Frontend engineering conventions, SDK references. |
| `CHANGELOG.md` | Full audit trail of every edit to the above. |
| `mockup_briefs/family-*.md` | Three visual-family briefs — now understood as the **rich-state (t=4)** visual specifications per family. Voice exemplars and candidate names remain useful; "canonical screens" are the endpoint of the reveal, not the starting point. |

---

## One-Line Summary

> Tomorrow: scaffold Next.js, build the **t=0 virgin state** across all three families as themed routes on a live dev server. You inhabit each URL in Windsurf's browser preview, annotate, iterate. No galleries, no static HTML, no screen-by-screen — we design the journey, and the UI proves it adapts.
