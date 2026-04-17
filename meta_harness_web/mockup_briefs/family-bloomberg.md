# Mockup Brief — Family B: Bloomberg / Palantir / Datadog

**Family archetype:** Dense authoritative instrument
**Primary hypothesis tested:** *An instrument-grade cockpit can be the product's primary identity, with the Client Portal serving as a "softened instrument" — muted chrome, alerts made more prominent, telemetry hidden — without feeling like a different product.*
**Primary audience bias:** Operator — designed for the power user who lives in the app, measures UI by data-per-pixel, and wants cockpit leverage; the client portal inherits this gravitas but strips cockpit noise.
**Governing docs:** `POSITIONING.md`, `JOURNEY.md` (progressive-reveal journey states), `DECISIONS.md` D1–D18 (**note D18: Pure Broadcast Portal — the client portal has no chat and no action buttons; stakeholder side is observation-only**), `AD-WebApp.md` §1, `ROADMAP.md`

> **Status note (2026-04-17, updated):** This brief's "canonical mockup screens" in §4 are now understood as the **rich-state (J6 / J7) visual specification** per `JOURNEY.md`. They remain the authoritative visual target for rich-state work. Earlier journey states (J0 virgin through J5 Gate 2 pending) are built first and reveal progressively into this endpoint. J6 covers Planning & Development; J7 covers Acceptance & Delivery. Voice exemplars in §5 and candidate names in §3 remain fully valid.

---

## §1 — Emotional DNA (the 5-second test)

When someone opens the app, they should feel: *"This is a serious instrument. People use this for consequential work. It rewards expertise, it does not apologize for density, and it does not waste my time with decoration."*

Everything glanceable at once. Status everywhere. Semantic color carries real meaning — red means blocked, amber means attention, green means passing, blue means informational. Dark chrome with functional color. Typography leans monospace/semi-monospace for structured data; a clean sans-serif handles prose.

Think: *Bloomberg Terminal (the 2020s reimagining, not the DOS nostalgia), Palantir Foundry, Datadog dashboards, Grafana, Sentry's event detail, cockpit flight displays.*

---

## §2 — Brand Tokens (proposed, to be refined)

### Palette

**Dark-mode-primary (always). Light mode is optional and low-priority.**
- Base: `#0B0D10` (deep blue-black — Bloomberg/Datadog reference)
- Surface: `#13161B`
- Surface elevated: `#1B1F26`
- Surface selected: `#242933`
- Border: `#2A2F38` (visible separators — this is a cockpit, we show structure)
- Text primary: `#E8EAED`
- Text secondary: `#9BA3AF`
- Text tertiary: `#5C6370`
- **Semantic palette is the primary brand expression, not an accent:**
  - Success (passing, on-track): `#26C281`
  - Warning (attention needed): `#F5A623`
  - Danger (blocked, failed): `#E5484D`
  - Info (neutral activity): `#3B82F6`
  - Critical (escalation): `#C026D3` (rare, high-signal)
- Brand accent (for logos, hero moments only): **amber-gold `#D4A53A`** or **bloomberg-orange `#FA7901`** — deployed sparingly.

### Typography

- **Display/UI:** `IBM Plex Sans` or `Söhne` — precise, technical, slightly mechanical. Fallback: system-ui.
- **Monospace:** `IBM Plex Mono` or `Berkeley Mono` — **used prominently**, not just for code. All IDs, timestamps, numeric data, status lines are monospace.
- **Scale:** 11 / 12 / 13 / 14 / 16 / 20 / 28 — **tight**. Body copy is 13px. Table rows are 12px. This is intentional — the Cockpit audience reads fast and wants more on screen.
- **Weights:** 400 regular, 500 medium, 700 bold (used for hierarchy, not decoration).

### Motion

- **Timing:** 80–120ms — fast, telegraphic. State changes feel immediate.
- **Easing:** `cubic-bezier(0.2, 0, 0, 1)` — accelerate and stop, mechanical feel.
- **Principle:** motion communicates *change*, never *arrival*. No "welcome" animations. No "nice-to-haves." Streaming tokens appear instantly, no fade.
- **Status indicators use motion sparingly:** pulse on active agent, blink (subtle) on new critical alert. Nothing else animates.

### Density baseline

- Default density: **high.** Multi-panel layouts are default, not optional. Tables with 30+ rows visible. Sidebars have real content, not navigation padding.
- Line-height: 1.4 for body, 1.25 for tables.
- Minimum row height in tables: 24px. Minimum touch target: 28px (power-user tool, keyboard-first).
- **Keyboard-primary.** Every action has a shortcut. `cmd-K` palette is the nervous system.

---

## §3 — Candidate Product Names (for this family)

| Name | Rationale | Risks |
|---|---|---|
| **Forge** | Industrial, muscular, "where things get made." Short, strong, instantly memorable. Aligns with "build LLM applications" core activity. | Common name; .com domain likely taken, branding may need qualifier ("Forge Labs," "Forge Studio"). |
| **Foundry** | Heavy-industry connotation, "casting molds at scale." Palantir already has a product called Foundry — **strong collision risk, probably eliminates this**. Listed for completeness. | Direct Palantir collision. |
| **Keel** | Shipbuilding — the structural spine of a vessel. Novel in software. Implies "the backbone your project is built on." Suits the cockpit aesthetic. | Lesser-known word; may require explanation on first hearing. |
| **Anvil** | Iron-on-iron, precision shaping. Evocative but slightly macho. | Anvil CI/CD exists; collision possible. Might feel aggressive for the Client Portal. |

**Family leader: Keel.** Unique, evocative, pronounceable, aligns with the "spine of a project" metaphor and feels equally right in the Cockpit (operator's structural backbone) and the Portal (the project's stable core).

---

## §4 — Canonical Mockup Screens

Same canonical project state as Family A (see `family-linear.md` §4):

> Tavern Assistant project for Luma Tavern Group, currently in Architecture phase, Gate 2 approval pending.

### Screens required (both surfaces unless noted)

1. **Project landing** — ambient mode.
   - *Cockpit:* full multi-panel layout. Left rail: all 7 agents with activity indicators (idle/active/blocked, semantic color). Center: phase progress bar + live event stream (timestamp-prefixed, monospace, like a log tail). Right rail: compact eval status + dataset counts + handoff log (last 10). Bottom status bar: project ID, thread ID, checkpoint namespace, model, connection state.
   - *Portal:* the same layout but **heavily muted** — only 3 agents visible (PM, and whichever two are currently/recently active), no log tail (instead: narrative cards describing recent activity), no status bar. Still dark. Still monospace for timestamps. But density knob turned from 10 down to 5.

2. **Approval gate moment** — action-required mode in cockpit; **informational mode in portal** per D18.
   - *Cockpit:* the live event stream pauses and a prominent red-bordered callout card appears at top: *"GATE 2 PENDING — Design Package (awaiting operator decision)"* with timestamp, source agent, and inline approve/revise/inspect buttons. No modal overlay — the cockpit doesn't block you, it escalates one panel. Everything else remains readable. **This is where the operator decides.**
   - *Portal:* same information rendered as a muted-amber-bordered "Recent activity" card, with the packaged design document below it. **No action buttons.** PM-voiced narrative introduction ("The Architect delivered this design package; your operator is reviewing it with you"). Read-only. Any stakeholder feedback flows out-of-band through the operator (per D18).

3. **Eval suite detail** — drill-down mode.
   - *Cockpit:* a dedicated panel with 4 sub-tabs: `RUBRIC`, `BINARY TESTS`, `DATASETS`, `EXPERIMENTS`. Rubric tab shows all 5 criteria in a compact table with per-score descriptions in expandable rows. Experiments tab shows a table of runs with scores, timestamps, `lc_agent_name`, and `↗` links to LangSmith. Monospace is heavy here. This is where power-users live.
   - *Portal:* the same information but re-rendered as **narrative cards**, not tables. "Luma Tavern's agent will be tested against five criteria," then each criterion as a card with the HE's authored explanation. Held-out dataset section says "Operator-only" with a subtle lock icon.

4. **Chat with PM** — **cockpit-only** (portal has no chat per D18).
   - *Cockpit:* chat is a *panel*, not the hero. It takes the center column but left rail and right rail remain present. Chat messages have monospace timestamps and colored `lc_agent_name` labels. Terminal-feel without being LARPy.

5. **Handoff log narrative** — drill-down mode.
   - *Cockpit only:* a full-viewport table of `handoff_log` entries. Sortable, filterable, keyboard-navigable. Columns: timestamp, source → target, reason (colored by enum), brief (truncated), artifact count. Row expand shows full brief text in monospace with artifact paths as clickable file-tree links.

6. **LangSmith link treatment.**
   - Consistent small affordance: `[LS↗]` in a muted brand color, sits inline next to run IDs, experiment names, and any artifact reference with an underlying LangSmith resource. Appears dozens of times across the Cockpit; once or twice in the Portal.

7. **Cockpit-only: Command palette (`cmd-K`).**
   - Keyboard-first navigation. Fuzzy-searchable across agents, phases, artifacts, experiments, datasets, settings. This is the Bloomberg-family *signature screen* — render it as a mockup even though the other families may not have one.

---

## §5 — Voice Exemplars

### Client Portal (warm-knowledgeable-peer register, in Bloomberg chrome, **monologue only** per D18)

**Gate 2 informational hero (D18 framing):**
> *"The Architect has returned the design package for **Tavern Assistant**. I've reviewed it — it's solid. Two tradeoffs are flagged for attention; both are reasonable. My recommendation to your operator: approve. You can read the full package below — share any reactions directly with your operator, who will carry them back to me."*
> [ Read the Design Package ]

*(Notice: even in Bloomberg chrome, the Client Portal's copy is warm. The dense visual language does the heavy lifting of signaling "instrument quality"; the warmth is carried by words. No chat affordance, no approval buttons — per D18, portal is observation-only.)*

### Developer Cockpit (precise-technical-operator register, in Bloomberg chrome)

**Gate 2 hero callout:**
```
GATE 2 — DESIGN PACKAGE
recv: 14:32:08 UTC  ·  src: architect  ·  artifacts: 3
2 tradeoffs flagged · Recommend APPROVE
[APPROVE]  [REVISE]  [INSPECT]
```

**Log-tail live event:**
```
14:35:22  [architect]     submit_spec_to_harness_engineer  → running
14:35:45  [harness_eng]   accepted · calibrating judge v3.2
14:36:12  [harness_eng]   eval_coverage_ok  →  return_eval_coverage_to_architect
14:36:13  [architect]     ✓ received · resuming design finalization
```

The Cockpit voice is literally formatted like a log file in many surfaces. This is intentional — power users read logs faster than prose.

### Anti-patterns in this family

- Soft language in cockpit chrome ("I think perhaps we should..." — no. This is an instrument.)
- Decorative monospace (using monospace for brand moments, not for structured data)
- Unsemantic color (red used for a "Primary Action" button — red means BLOCKED/FAILED here)

---

## §6 — Evaluation Criteria

When reviewing this family alongside the other two, judge on:

1. **Cockpit power** — does the Cockpit deliver genuine operator leverage? (Keyboard navigation, data density, semantic color, glanceability.) This family should *win* this axis by a wide margin.
2. **Portal gracefulness** — does the Portal version of this aesthetic feel hostile or intimidating to a non-technical founder? This is the family's biggest risk.
3. **Cross-surface gap** — how different do the Portal and Cockpit feel within this family? If they feel like two different products, the hypothesis fails.
4. **Premium signal** — Bloomberg-family aesthetics can drift toward "enterprise-boring." Does our execution feel premium, or does it feel like a compliance tool?
5. **Voice fit** — does the chrome support *warm* copy in the Portal? Or does it force the voice to be clinical even when we want it to be friendly?

---

## §7 — What This Family Is Weakest At (honest failure modes)

- **Non-technical stakeholder onboarding.** If the Client Portal feels intimidating on first sight, we've lost the founder before they've clicked anything. This is the single biggest risk of the family.
- **Voice flexibility in Portal.** Dense monospace chrome and warm copy fight each other. We may find the Portal *has* to be less monospace than the Cockpit to land warmth.
- **Mobile / tablet experience.** Cockpits don't shrink well. If stakeholders want portal-on-phone, this family struggles.
- **"AI-company taste" signal.** Bloomberg aesthetic reads "finance/infra," not "AI studio." AI-literate buyers may expect warmer, more "lab-native" visuals. This family risks seeming *off-category*.
