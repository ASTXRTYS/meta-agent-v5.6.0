# Mockup Brief — Family C: Stripe / Notion / Retool

**Family archetype:** Calm authoritative clarity
**Primary hypothesis tested:** *A stakeholder-first aesthetic — calm, trustworthy, light-primary — can scale upward to cockpit-grade density by progressively adding panels, data, and affordances, without losing its core "grown-up software" register. The Portal is the home base; the Cockpit is the same brand with the knob turned up.*
**Primary audience bias:** Stakeholder — designed for the founder/executive who wants the product to feel safe, legible, and credible; the Cockpit inherits this gravitas and adds operator leverage on top.
**Governing docs:** `POSITIONING.md`, `DECISIONS.md` D9–D16, `AD-WebApp.md` §1

---

## §1 — Emotional DNA (the 5-second test)

When someone opens the app, they should feel: *"This is professional, grown-up software. The people who built this know what they're doing. I am in good hands. I don't need to be technical to use this."*

Light mode default. Generous breathing room without being airy. Strong hierarchy — the most important thing on the page is visually unambiguous. Subtle depth (soft shadows, gentle borders, modest elevation) rather than flat minimalism. Color is muted, institutional, confident — not playful, not corporate-boring, not tech-bro.

Think: *Stripe Dashboard, Notion (especially post-2023), Retool's editor chrome, Linear in light mode, Attio, Pylon, Ramp, Mercury Bank, Vercel's docs site.*

---

## §2 — Brand Tokens (proposed, to be refined)

### Palette

**Light-mode-primary. Dark mode is excellent and supported, not an afterthought.**
- Base: `#FAFAF8` (warm off-white — the Stripe trick, not pure white)
- Surface: `#FFFFFF`
- Surface elevated: `#FFFFFF` with `0 1px 2px rgba(0,0,0,0.04)` shadow (depth through shadow, not color)
- Border: `#E7E5E4` (subtle)
- Border emphasis: `#D6D3D1`
- Text primary: `#1C1917` (warm near-black — not pure black; softer on eyes)
- Text secondary: `#57534E`
- Text tertiary: `#A8A29E`
- **Brand accent: a single confident hue — candidates: Stripe-inspired indigo `#5469D4`, institutional deep-teal `#0E7490`, or warm-premium sunset `#CC4B2C`.** Used for CTAs, active states, brand moments.
- Semantic: success `#15803D` (muted, not neon), warning `#B45309`, danger `#B91C1C`, info `#0369A1`

**Dark mode (excellent, not afterthought)**
- Base: `#1C1917`
- Surface: `#262524`
- Text primary: `#FAFAF8`
- Accent unchanged, slightly brightened for dark-mode legibility

### Typography

- **Display/UI:** `Inter` (variable), **or** a serif-accented sans like `Söhne` / `GT America` / `Basis Grotesque` — the "confident adult" family. Fallback: system-ui.
- **Optional display accent for hero moments:** a soft serif like `Tiempos` or `GT Super` — used sparingly on marketing-adjacent surfaces (approval gate headers, PRD titles) to add human warmth. The Linear family avoids serifs; this family *selectively* uses them.
- **Monospace:** `JetBrains Mono` or `Geist Mono`. Used for code, IDs, technical data — but *less prominently* than Bloomberg. Mono is a specialist tool here, not a primary voice.
- **Scale:** 13 / 14 / 16 / 18 / 24 / 32 / 48 — spacious, legible. Body copy is 16px (larger than Linear/Bloomberg — this family trusts readability over density).
- **Weights:** 400 regular, 500 medium, 600 semibold. Bold reserved for hero moments.

### Motion

- **Timing:** 200–280ms — gentle, deliberate, confident. Nothing is instant; nothing is slow. State changes feel considered.
- **Easing:** `cubic-bezier(0.4, 0, 0.2, 1)` (Material-ish ease-in-out — soft on both ends).
- **Principle:** motion communicates *comfort* — the user is never jolted. Streaming tokens have a gentle ease-in per token, almost breathing.
- **Signature motion:** subtle parallax on scroll, gentle scale (1.0 → 1.02) on hover for cards, confident slide-in for drill-downs.

### Density baseline

- Default density: **medium-low.** Breathing room is *the* feature — it's how we communicate "take your time, this is important." The Cockpit surface increases density but preserves the light-mode palette and the generous type size.
- Line-height: 1.6 for body, 1.4 for tables.
- Minimum touch target: 40px (stakeholder-first, may be used on tablet or laptop away from primary workstation).

---

## §3 — Candidate Product Names (for this family)

| Name | Rationale | Risks |
|---|---|---|
| **Keystone** | Central support, architectural. "The piece that holds the whole project together." Warm, confident, institutional. Works as-is; scales to a suite ("Keystone Studio," "Keystone Cockpit" if needed). | Common word; .com unavailable likely, but brand trademark feasible. |
| **Beacon** | Signal, guidance, trust. Evokes navigation and clarity. Short, memorable, client-friendly. | Slight AI-category collision (many AI products use "Beacon"); check trademark. |
| **Clarion** | Classical, clear call. Uncommon in software. Premium connotation without being stuffy. | Lesser-known word; may need pronunciation help ("CLAIR-ee-un"). Could read as too-formal. |
| **Compass** | Universal navigation metaphor. Translates across cultures. Warm. | Very common; Compass the real-estate product exists, big collision. |

**Family leader: Keystone.** Architectural resonance (literally "the keystone of your project"), works across cultures, feels equally right for a founder looking at a PRD approval screen and an operator running phase deliverables. Scalable into a product line if Meta Harness ever branches (Keystone Portal, Keystone Cockpit as sub-products).

---

## §4 — Canonical Mockup Screens

Same canonical project state as Family A & B (see `family-linear.md` §4):

> Tavern Assistant project for Luma Tavern Group, currently in Architecture phase, Gate 2 approval pending.

### Screens required (both surfaces unless noted)

1. **Project landing** — ambient mode.
   - *Portal (primary for this family):* hero area displays the project name "Tavern Assistant" in display type (possibly a soft-serif accent), one-line status ("Architecture phase — design in progress"), a prominent "Recent activity" card with narrative entries ("The Architect submitted the design package for your review 12 minutes ago"), a deliverables-so-far card, a chat-with-PM card. Lots of breathing room. Light mode. Card-based layout with subtle shadows.
   - *Cockpit:* the same page with **additional panels revealed** — left rail shows all 7 agents, center still shows narrative but with more activity items, right rail shows eval status + handoff log. Density higher; chrome identical; brand tokens unchanged. "The Portal with the knob turned up."

2. **Approval gate moment** — action-required mode.
   - *Portal:* a hero callout card dominates the viewport. The design package renders as a beautifully-typeset first-class document (think: Stripe's email receipts, Mercury's invoice view, Notion's doc view). Approve / Request Revision / Discuss with PM buttons. The document *looks* like a formal deliverable the stakeholder would be proud to forward to their team.
   - *Cockpit:* same hero callout but positioned in the center column with pipeline/logs still visible in peripheral panels. The operator can see gate context + pipeline at once.

3. **Eval suite detail** — drill-down mode.
   - *Portal:* rendered as a beautifully-presented scrollable article: intro paragraph from HE ("For Luma Tavern's Tavern Assistant, we're evaluating five dimensions of quality..."), each rubric criterion as its own titled section with the per-score descriptions as nested cards, the binary tests as a clear checklist, a dataset preview section with representative examples rendered as quote-cards. This is the family's signature move: *eval science made stakeholder-readable*. No tables unless necessary.
   - *Cockpit:* the same content available in a denser "analytical view" — tables of criteria, tables of experiments, inline dataset previews. Operator can toggle between "Article View" and "Table View."

4. **Chat with PM** — conversational mode.
   - *Portal:* chat expands to ~75% viewport. Bubble-style messages with generous padding. Agent label is a small badge above the bubble. The chat feels like iMessage with the pro-dial turned up — inviting, not intimidating. Input field has a "Press ⏎ to send, or Shift⏎ for new line" hint.
   - *Cockpit:* chat still dominates but ~65% width, with pipeline state in a compact side panel. Timestamps visible by default. Agent labels more technical.

5. **Handoff log narrative** — drill-down mode.
   - *Portal:* renders the handoff log as a **narrative timeline** — "12:04 PM · The Harness Engineer returned the evaluation suite to the Project Manager." Plain-language, timeline-scrolled, each entry expandable into a longer narrative. No enum values ("reason: deliver"), no artifact paths — just story.
   - *Cockpit:* the denser version — table with columns for timestamps, agents, reason enums, briefs, artifact counts. Operator view. Can toggle "Narrative" / "Table."

6. **LangSmith link treatment.**
   - Consistent affordance: a soft pill-shaped button with `↗ View in LangSmith` text and a small LangSmith-square icon. Sits inline next to experiment references. Styled to feel like a respected external reference (citation-quality), not a technical debt hatch.

### Out-of-scope reminder

Login screens, project picker (D8), settings, billing not required for these mockups.

---

## §5 — Voice Exemplars

### Client Portal (warm-knowledgeable-peer register)

**Gate 2 approval hero:**
> *"The Architect's design package for **Tavern Assistant** is ready for your review.*
>
> *I've looked it over. It's thoughtful work, and the architecture lines up with what we scoped on the call. Two tradeoffs the Architect wants your opinion on are flagged in the document. My recommendation: both tradeoffs are sensible for the v1 scope — I'd approve.*
>
> *You can read it through, chat with me about any section, or approve directly."*
>
> [ Read the Design Package ] · [ Discuss with PM ] · [ Approve ]

**Empty state:**
> *"No projects yet. When you're ready, share what your client needs — a brief, a call transcript, a summary — and I'll scope the PRD with you. We'll refine it together before anything else happens."*

### Developer Cockpit (precise-technical-operator register, in Stripe chrome)

**Gate 2 action card:**
> ### Gate 2 — Design Package Ready
> **From** Architect · **Received** 14:32 · **Artifacts** 3 · **Tradeoffs flagged** 2
>
> Recommendation: **APPROVE**. Tradeoffs are sensible for v1 scope.
>
> [ Approve ] · [ Request revision ] · [ Inspect package ]

*(Note: even in cockpit register, the Stripe family doesn't go fully telegraphic like Bloomberg. Sentences are shorter, but still whole sentences. The restraint comes from typography and spacing, not from fragmentation.)*

### Anti-patterns in this family

- Tables where narrative would serve the stakeholder better
- Monospace for non-technical data (just because you *can* use monospace doesn't mean you *should*)
- Saccharine copy ("Great news! Your project is going amazing!") — confidence is calm, not peppy
- Emoji in system copy — reserve emoji for user-generated content if allowed at all

---

## §6 — Evaluation Criteria

When reviewing this family alongside the other two, judge on:

1. **Portal warmth** — does the Client Portal feel like a product a founder would be *proud* to receive as a deliverable view? Does it convey trust and craft?
2. **Cockpit leverage at light-mode density** — can this family scale up to genuine operator density, or does the "breathing room" principle cap how much data we can surface? This is the family's biggest risk.
3. **Cross-surface unity** — does the Portal-to-Cockpit transition feel like "same app, more knobs exposed," or like "different app in the same company's style"?
4. **Voice fit** — the Stripe family is *naturally* voice-friendly for warm copy. Can it support the telegraphic cockpit voice without feeling dissonant?
5. **Name resonance** — Keystone / Beacon / Clarion — do these sound right in the visual context, or do they feel like they belong with a different family?

---

## §7 — What This Family Is Weakest At (honest failure modes)

- **Cockpit density ceiling.** Light-mode palettes and generous spacing fight against cockpit data-per-pixel. We may find that the Cockpit needs to flip to dark mode to breathe — and if we do, we've split the brand across two modes, undermining the "one family, two surfaces" promise.
- **"AI-company taste" signal.** Stripe/Notion/Retool aesthetic reads "SaaS" more than "AI-native." AI-literate buyers may expect more novelty/exploration vibes. We could mitigate by using the serif display accent for hero AI moments — but that's a tightrope.
- **Operator-only features looking underwhelming.** Commands, log tails, multi-panel cockpits don't look their best in a breathe-easy aesthetic. Bloomberg family will look cooler on operator-dense screens than this family will.
- **Risk of looking "too dashboard."** Stripe's aesthetic is associated with *accounting* software in many minds. We must deliberately differentiate from payroll/invoicing chrome to avoid the "is this a fintech product?" confusion.
