# Meta Harness Web — Journey States & Progressive-Reveal Design Spec

**Status:** Active — foundational design document
**Last Updated:** 2026-04-17 (full restructure around PCG canonical phases; every state cross-cited to `meta_harness/AD.md` or `meta_harness/DECISIONS.md`)
**Owner:** Jason (product) + Cascade (design)
**Working codename:** `meta-harness-web` — formal name deferred until J1–J3 are rendered across all three families
**Companion documents:** `POSITIONING.md` (product vision), `DECISIONS.md` (D1–D18), `AD-WebApp.md` (architecture), `ROADMAP.md` (execution plan)
**Backend source of truth:** `../meta_harness/AD.md` (PCG topology, phase enum, handoff tools) and `../meta_harness/DECISIONS.md` (closed decisions Q1–Q14)

---

## §1 — What This Document Is

This is the design spec for **how Meta Harness's UI evolves as Project Coordination Graph (PCG) state accrues.** The UI is not a set of screens that exist all at once with panels showing or hiding — it is a **progressive reveal** across well-defined PCG states, where every new affordance earns its presence because the PCG state that justifies it now exists.

The implication: the app a user sees 2 minutes after login (fresh, no projects, chatting with the PM for the first time) is **structurally different** from the app the same user sees 3 days later (multiple agents engaged, pipeline dense, acceptance stamps accruing). Not the-same-layout-with-panels-shown — a genuinely different composition.

**Ground truth.** Every journey state in this document is a specific point in the backend's PCG lifecycle. The PCG is a deterministic LangGraph `StateGraph` whose state schema is locked at `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:195-219`. The UI reads three PCG keys to know where it is in the journey:

- `current_phase` — one of `scoping | research | architecture | planning | development | acceptance` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:203`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:353`)
- `current_agent` — one of `project_manager | harness_engineer | researcher | architect | planner | developer | evaluator` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:204`)
- `handoff_log` — append-only audit trail of every handoff + acceptance stamp (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:205`)

Every journey state below names the `(current_phase, current_agent)` pair it represents and cites the handoff tool(s) that trigger the transition into and out of it. If an assertion in this doc cannot be traced back to the AD or DECISIONS, it is a bug; file it.

This is Meta Harness's core design thesis. It is what makes the product memorable instead of conventional.

---

## §2 — Why Progressive Reveal

Three reasons, each load-bearing:

1. **Honesty.** At J0, the project has no pipeline, no handoffs, no agents active. Rendering a pipeline-timeline strip that's empty is a lie; it implies work where no work is happening. Showing only the PM at J0–J1 is truthful — one agent is the `current_agent`, one agent is visible.

2. **Respect.** A stakeholder (per D18) or a new operator opening the app for the first time shouldn't be drowned in a cockpit that assumes expertise they don't yet have. They should meet the product through a single, warm conversational surface. Complexity is earned by the PCG actually reaching the state that introduces it, not imposed up front.

3. **Craft signal.** Products that reshape as PCG state accrues feel alive. Products with static chrome feel dead, regardless of how good the static chrome is. The adaptive reveal is a premium signal no static design can match — and it aligns directly with the "premium orchestration layer" positioning (D9 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:23-31`).

The progressive reveal is **not a hidden-panels pattern**. It is a compositional pattern — each state is its own layout, not a collapsed version of the final layout.

---

## §3 — Grounding: PCG State + Agent Definitions Are Journey Ground Truth

Ground truth is two-fold:

1. **PCG state** — the deterministic coordination state that tells the UI where it is in the project lifecycle:
   - `current_phase` — one of `scoping | research | architecture | planning | development | acceptance` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:203`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:353`)
   - `current_agent` — one of `project_manager | harness_engineer | researcher | architect | planner | developer | evaluator` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:204`)
   - `handoff_log` — append-only audit trail of every handoff + acceptance stamp (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:205`)

2. **Agent definitions** — the role, identity, and capabilities of each agent as defined in `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md`:
   - Agent role and tool ownership matrix (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:468-481`) — which tools each agent owns and can call
   - Agent identity — what each agent does, its scope, its relationship to other agents
   - Points in time where each agent becomes relevant — the pipeline flow determines when an agent first appears and what it does
   - Agent-to-agent communication patterns — which specialists can loop directly vs. which must route through PM

The UI reads PCG state to know *where* it is in the journey. It reads agent definitions to know *who* is present, *what* they can do, and *how* they relate to each other. Both are ground truth — the journey states in §4 are defined by the intersection of PCG state and agent role definitions.

The PCG pipeline flow is fixed and is defined by the agent-scoped tool-ownership matrix at `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:468-481` and the pipeline flow diagram at `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:485-533`. The normative lifecycle:

```
Stakeholder → PM
  ├─ scoping    : PM scopes PRD with stakeholder via ask_user middleware
  │              (AskUserMiddleware on PM per AD:720)
  ├─ scoping    : PM → HE        deliver_prd_to_harness_engineer   (AD:417, D1)
  │              HE authors eval suite + rubrics + public/held-out datasets + calibrated judges
  │              HE may loop back: ask_pm → PM → ask_user → answer  (AD:465 C-tool; AD:1128-1135)
  │              HE → PM         return_eval_suite_to_pm           (AD:427, R6)
  ├─ GATE 1     : PM packages {PRD + eval suite + business-logic datasets} and presents to user
  │              (scoping → research approval gate per AD:359, AD:355)
  │              Approval recorded as (PM, PM, submit, accepted=true/false) per DECISIONS:563-573
  ├─ research   : PM → Researcher deliver_prd_to_researcher        (AD:418, D2; gated per DECISIONS:551)
  │              Researcher → PM return_research_bundle_to_pm      (AD:428, R7)
  ├─ architecture: PM → Architect deliver_design_package_to_architect  (AD:419, D3)
  │              ↪ Architect ↔ Researcher request_research_from_researcher (AD:464, C3; specialist loop per AD:676)
  │              ↪ Architect ↔ HE submit_spec_to_harness_engineer   (AD:446, S1 — Stage 2)
  │                              return_eval_coverage_to_architect  (AD:447, S2)
  │              Architect → PM  return_design_package_to_pm        (AD:429, R8)
  ├─ GATE 2     : PM packages {design spec + tool schemas + system prompts} and presents to user
  │              (architecture → planning approval gate per AD:360, AD:355)
  ├─ planning   : PM → Planner   deliver_planning_package_to_planner  (AD:420, D4; gated per DECISIONS:553)
  │              ↪ Planner may consult_harness_engineer_on_gates    (AD:462, C1, non-blocking)
  │              ↪ Planner may consult_evaluator_on_gates            (AD:463, C2, non-blocking)
  │              Planner → PM    return_plan_to_pm                   (AD:430, R9)
  ├─ development: PM → Developer deliver_development_package_to_developer  (AD:421, D5)
  │              Loop per plan phase (AD:535-547):
  │                 Developer announce_phase_to_evaluator            (AD:453, P1, non-blocking)
  │                 Developer announce_phase_to_harness_engineer     (AD:454, P2, non-blocking)
  │                 Developer executes phase
  │                 Developer submit_phase_to_evaluator              (AD:455, P3, BLOCKING — pass/fail)
  │                 Developer submit_phase_to_harness_engineer       (AD:456, P4, advisory per DECISIONS:595-597)
  │                 Developer may ask_pm                             (AD:465, C6; AD:480)
  ├─ acceptance : Evaluator submit_application_acceptance            (AD:438, A2, accepted=true/false per DECISIONS:579-593)
  │              HE submit_harness_acceptance (if HE participated)   (AD:437, A1; gate derives HE relevance per AD:440)
  │              Developer return_product_to_pm                      (AD:431, R10; gated on acceptance stamps)
  └─ END        : PM presents finished product to user
                  PM uses ask_user middleware for satisfaction check (AD:216, AD:532-533)
                  PM finishes normally → END
```

The journey states in §4 are the UI compositions that correspond to distinct regions of this lifecycle. Each one is defined by the `(current_phase, current_agent)` pair plus which gate (if any) is pending.

---

## §4 — The Eight Canonical Journey States

Eight states, seven transitions. Each transition corresponds to a specific PCG state change and introduces a new **class** of affordance. The classes, in order of introduction, are: *memory hint* → *first multi-agent handoff* → *first-class deliverable* → *approval gate* → *specialist loops* → *phase-execution telemetry* → *acceptance stamps* → *final product + satisfaction*.

### J0 — Virgin (pre-PCG)

**PCG state:** No project thread exists. `project_id` has not been assigned. `current_phase`, `current_agent`, and `handoff_log` do not exist.

**What the cockpit shows:**
- Identity chrome: product name in header (currently `Meta Harness` as working codename), minimal profile menu, nothing else.
- Centered conversational surface that dominates the viewport.
- Placeholder in the input: *"Tell me about your client. Share a summary, a transcript, or a brief — I'll scope the PRD with you."*
- Small PM identity chip: *"Speaking with: the Project Manager"*.
- No sidebar. No project picker (no projects to pick). No dashboard. No empty-state illustration. No task chips.

**Portal:** Does not exist. Stakeholders only see the portal once a project thread has been created and a scoped PRD is available (per D18 + D17 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:158`).

**Voice register (D15 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:119-134`):** Warm knowledgeable peer, opinionated from the first sentence. PM's opening turn lands the plane.

**Transition to J1:** Operator sends first message. `process_handoff` creates a synthetic handoff record from the user's message, sets `current_agent = project_manager`, `current_phase = scoping` (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:192`).

---

### J1 — Scoping: PM ↔ Stakeholder

**PCG state:** `current_phase = "scoping"`, `current_agent = "project_manager"`. The PM is engaging the operator via its `AskUserMiddleware` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:720`). Context accruing in PM's role checkpoint namespace. `handoff_log` has only the synthetic bootstrap record.

**What the cockpit shows:**
- Same identity chrome as J0.
- Conversation dominates (~75–80% of the viewport).
- **New affordance — memory hint.** A faint "Working draft" artifact card appears in a previously-empty area (top-right or a slim right rail materializing for the first time). Ghosted text: *"PRD draft — the PM is taking notes as you talk."* Not yet a first-class document; no click-through.
- No left rail (only one agent has ever been active).
- No pipeline timeline.

**Portal:** Still does not exist. Scoping is operator ↔ PM; the stakeholder has not been invited to the portal yet.

**Transition to J2:** PM calls `deliver_prd_to_harness_engineer` (D1 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:417`). The handoff tool's middleware gate verifies `artifact_paths` contains the PRD (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:346`). `current_agent` flips to `harness_engineer`; `current_phase` stays `scoping` (Stage 1 HE work is intra-scoping).

---

### J2 — Scoping: HE Authors Eval Suite

**PCG state:** `current_phase = "scoping"` (still), `current_agent = "harness_engineer"`. HE is authoring refined eval criteria, rubrics, public datasets, held-out datasets, and calibrating LLM judges (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:417` artifact flow column).

> **Critical correction from the prior version of this doc:** the HE does its Stage 1 work *before* Gate 1, not after. Gate 1 is the moment the PM presents the *already-completed* eval suite to the user for approval, per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:359` ("Trigger: PM receives completed eval suite from HE, packages it, presents to user").

**What the cockpit shows:**
- **New affordance class — first multi-agent handoff visible.** A minimal left rail materializes showing two agents: PM (idle / observing) and HE (active / authoring). Only engaged agents appear, per progressive-reveal restraint.
- **New affordance — slim handoff log rail.** Shows the 1–3 most recent handoff records as a narrative timeline ("12:04 PM · PM handed the PRD to the Harness Engineer. HE is authoring the evaluation suite.").
- Chat compresses to a secondary panel but remains accessible — preserves conversation history trust signal.
- Draft "Eval suite — authoring in progress" card appears next to the PRD card.

**HE clarification loop (non-blocking sub-state):** HE may invoke `ask_pm` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:465`, C-tool). The handoff routes through PCG to the PM; PM uses its `AskUserMiddleware` to relay the question to the operator. Answer flows back the same path. Cockpit UI surfaces this as a momentary `current_agent = "project_manager"` interstitial + an inline PM-voiced question in the conversation log (sequence per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:1128-1135`).

**Portal:** Still does not exist — no PRD has been approved yet; stakeholder has not been invited.

**Transition to J3:** HE calls `return_eval_suite_to_pm` (R6 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:427`). PM receives the full package and begins assembling the Gate 1 document.

---

### J3 — Gate 1 Pending (scoping → research approval)

**PCG state:** `current_phase = "scoping"`, `current_agent = "project_manager"`. `handoff_log` contains `(HE, PM, return)` record. PM has assembled the stakeholder-facing package: **PRD + eval suite + business-logic datasets** (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:359`).

**Gate mechanics.** Gate 1 is the `scoping → research` transition; one of the two approval gates that require explicit user approval per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:355-356`. The PM owns a dedicated approval tool that presents the document package (docx/pdf/pptx format delegated to spec) for review (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:362`). Approval is recorded as the self-referential handoff triple `(PM, PM, submit, accepted=true|false)` per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:563-573`. Autonomous mode auto-approves by creating `accepted=true` records without pausing (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:364`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:573`).

**What the cockpit shows:**
- **New affordance class — first-class deliverable rendering.** The Gate 1 package becomes the hero of the viewport. Three linked tabs or stacked sections: PRD, Eval Suite (rubrics + scoring criteria + judge configs), Business-Logic Datasets Preview. Strong typography, formal document hierarchy, PM-voiced introduction at the top.
- Chat compresses to a side panel (~30% width).
- **Action-required mode** (D13 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:84-98`): approval callout dominates with Approve / Revise actions. Revise routes back to PM with the user's rejection reasoning (exact rejection flow delegated to spec per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:466`).
- Left rail: PM + HE visible (both have participated). HE shows as "returned — awaiting next stage." Pipeline timeline begins to render: scoping marker (filled), research marker (pending Gate 1).

**What the portal shows (first stakeholder surface):** D17 first-login UX applies. Gate 1 hero document is pre-rendered for the stakeholder to review. **No action buttons** — approvals are cockpit-only per D18 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:185`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:201`). Portal copy is PM-voiced monologue: *"Your operator is reviewing the scoped PRD and evaluation plan with you. Read through it; share feedback with your operator directly."* Held-out datasets hidden per D18 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:204`). Source-material visibility is operator-toggleable per D17 point 2 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:160`).

**Transition to J4:** Operator approves in cockpit. PM calls `deliver_prd_to_researcher` (D2 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:418`). Middleware gate verifies `(HE, PM, return)` AND `(PM, PM, submit, accepted=true)` in `handoff_log` (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:551`). `current_phase` advances to `research`; `current_agent` flips to `researcher`.

---

### J4 — Research & Design Exploration

**PCG state:** Two sequential phases compressed into one UI composition because the visual shape is similar — a single specialist is active with the handoff log accruing and specialist loops beginning to fire.

- **J4a `current_phase = "research"`, `current_agent = "researcher"`**: Researcher received PRD + refined eval criteria + public datasets via D2. Producing the research bundle. Returns via `return_research_bundle_to_pm` (R7 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:428`).
- **J4b `current_phase = "architecture"`, `current_agent = "architect"`**: After PM calls `deliver_design_package_to_architect` (D3 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:419`, gated on research complete). Architect designs the target application. **Specialist loops fire here, not through PM** (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:670-686`):
  - Architect → Researcher via `request_research_from_researcher` (C3 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:464`) for SDK/API gaps. Non-blocking.
  - Architect → HE via `submit_spec_to_harness_engineer` (S1 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:446`, Stage 2 intervention). HE returns `return_eval_coverage_to_architect` (S2 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:447`). Blocking for Architect's next step.

**What the cockpit shows:**
- Left rail now shows the full set of *engaged* agents: PM, HE, Researcher, Architect (as they enter). Idle ghost rows for Planner / Developer / Evaluator are a mockup-phase open question (§7).
- **New affordance class — specialist-loop visibility.** When the Architect loops out to Researcher or HE (non-PM-mediated), the handoff log distinguishes these visually from PM-hub deliveries. Example narrative line: *"3:12 PM · The Architect asked the Harness Engineer to review the design spec for eval coverage (Stage 2)."*
- Deliverables area shows: PRD (approved), Eval Suite (approved public portion; held-out hidden per D18 cockpit-operator exception), Research Bundle (in progress → complete), Design Spec (in progress).
- Pipeline timeline strip: scoping (done ✓), research (active or done), architecture (active), remaining phases as ghost markers.
- Chat remains accessible as a collapsed pane.

**What the portal shows:** Ambient mode. Phase-level narrative updates only ("*The Researcher has joined your project and is mapping the technical options.*" → "*The Architect is now drafting the design.*"). No sub-agent detail, no specialist-loop detail — per D18 Q4 rescoping (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:202`). PM-voiced monologue register throughout.

**Transition to J5:** Architect calls `return_design_package_to_pm` (R8 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:429`). PM assembles the Gate 2 package.

---

### J5 — Gate 2 Pending (architecture → planning approval)

**PCG state:** `current_phase = "architecture"`, `current_agent = "project_manager"`. `handoff_log` contains `(Architect, PM, return)`. PM packaging **full design spec + tool schemas + system prompts** for stakeholder-friendly presentation (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:360`).

**Gate mechanics.** Second of the two user-approval gates (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:355-356`). Same approval-tool mechanism as Gate 1; approval record is `(PM, PM, submit, accepted=true|false)`.

**What the cockpit shows:** Structurally similar to J3 (first-class deliverable hero, action-required approval callout) but richer right rail because more handoffs have accrued. Design package renders as a formal document with sections for spec, tool schemas, prompts, and HE's Stage 2 eval coverage report. Pipeline timeline: scoping + research done; architecture done; planning pending Gate 2.

**What the portal shows:** Same pattern as J3 portal — informational Gate 2 rendering, no action buttons, PM-voiced monologue.

**Transition to J6:** Operator approves. PM calls `deliver_planning_package_to_planner` (D4 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:420`). Middleware gate verifies `(Architect, PM, return)` AND `(PM, PM, submit, accepted=true)` in `handoff_log` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:553`). `current_phase` advances to `planning`; `current_agent` flips to `planner`.

---

### J6 — Planning & Development

**PCG state:** Two phases compressed into one journey composition because the cockpit's rich-state shape stabilizes here. Density peaks in this composition.

- **J6a `current_phase = "planning"`, `current_agent = "planner"`**: Planner received design spec + public eval criteria + public datasets via D4. Authoring the phased implementation plan. Non-blocking consults to HE (`consult_harness_engineer_on_gates`, C1 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:462`) and Evaluator (`consult_evaluator_on_gates`, C2 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:463`). Returns via `return_plan_to_pm` (R9 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:430`).
- **J6b `current_phase = "development"`, `current_agent = "developer"`**: After PM calls `deliver_development_package_to_developer` (D5 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:421`, gated on plan accepted). Developer runs the phase loop (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:535-547`):
  1. `announce_phase_to_evaluator` (P1) and `announce_phase_to_harness_engineer` (P2) — non-blocking intents (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:453-454`).
  2. Developer executes the phase.
  3. `submit_phase_to_evaluator` (P3 — blocking pass/fail, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:455`) and `submit_phase_to_harness_engineer` (P4 — advisory-only per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:595-597`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:456`).
  4. Developer may call `ask_pm` (C-tool — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:465`, Developer-owned per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:480`).
  5. Loop for next plan phase.

**What the cockpit shows:**
- **New affordance class — phase-execution telemetry.** A plan timeline materializes showing the Planner's phases (P1, P2, P3…) with status: announced / executing / awaiting-QA / passed / revising. Each phase row expands to show the announce → execute → submit → review micro-cycle.
- Left rail now includes Planner, Developer, Evaluator. HE remains present (Stage 2 + ongoing P4 advisory).
- **Tier 2 subagent visibility** (Q4 — cockpit-only per D18): when the Developer spawns subagents via its `task` tool, `SubagentCard` / `SubagentProgress` SDK components surface under the Developer's active row (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:203`; SDK path in `AGENTS.md`).
- **Sandbox IDE surface** (Q7 — cockpit-only per D18): when the Developer runs with a sandbox backend, a three-panel IDE-like composition becomes available (file tree + code viewer + chat). Exact layout is a mockup Session 4+ open question (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:204`).
- Right rail: handoff log gets dense. Todo progress display (Q6 — cockpit-primary per D18, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:203`) surfaces the Developer's active `todos` list.
- EBDR-1 feedback rendering: when HE returns advisory feedback on P4, it renders as an inline callout, not a blocking gate (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:595-597`).

**What the portal shows:** Ambient mode, abstracted to phase narrative ("*The Planner has decomposed the design into 6 implementation phases. The Developer is now building Phase 1.*"). No todo-level detail, no sandbox, no subagent telemetry — per D18 rescoping. Phase completion milestones surface as PM-voiced narrative updates.

**Transition to J7:** Developer finishes the final plan phase. QA agents begin acceptance work.

---

### J7 — Acceptance & Delivery

**PCG state:** `current_phase = "acceptance"`. Multiple `current_agent` transitions as QA agents stamp, then back to PM for final presentation.

**QA stamp accrual** (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:437-440`):
- Evaluator calls `submit_application_acceptance` (A2 — always required). `accepted=true|false` per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:579-593`.
- HE calls `submit_harness_acceptance` (A1 — required only if HE participated in the project, derived from `handoff_log` scan per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:440`).

**Return gated on stamps.** Developer calls `return_product_to_pm` (R10 — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:431`). Middleware gate scans `handoff_log` for `(Evaluator, PM, submit, accepted=true)` AND, if HE participated, `(HE, PM, submit, accepted=true)` (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:555`). An `accepted=false` stamp is an audit record only and does NOT satisfy the gate (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:586-589`).

**PM presents + satisfaction check** (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:216`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:532-533`): PM receives final product + artifacts, writes a lifecycle-bookend `AIMessage` into `messages` (the only write to that channel during the project lifecycle per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:201`, `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:210`), and uses its `AskUserMiddleware` for a satisfaction check. On satisfied user response, PM finishes → END.

**What the cockpit shows:**
- **New affordance class — acceptance stamps as first-class records.** Two stamp cards appear in the right rail: Application Acceptance (Evaluator — accepted/rejected with reasoning + evidence) and Harness Acceptance (HE — if applicable). Each stamp renders its `brief` and links to its `artifact_paths` (eval results, test outputs).
- **Final deliverable hero.** Once stamps are green and Developer returns the product, the viewport re-composes around a delivery hero — the finished artifact(s) + PM-voiced delivery summary. Plan timeline shows all phases green.
- **Satisfaction check** renders as an `ask_user` interrupt: a PM-voiced question ("Everything land the way you wanted? Want me to close the project, or is there one more pass?") with Confirm / Continue options. The cockpit's handling of this interrupt mirrors Gate 1 / Gate 2 approval UX but without the revision-document weight.
- If a stamp is `accepted=false`, the cockpit surfaces an audit card and the `return_product_to_pm` gate stays closed. The Developer is responsible for a next-phase revision (routing delegated to implementation spec per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:466`).

**What the portal shows:** Ambient mode. PM-voiced narrative arc: *"The team has completed the build and passed quality review. Your operator is preparing the final handoff."* → *"Your project is delivered. Here's the finished work and a summary of what was built."* Final artifacts render as packaged deliverables (eval results as articles, product as a browsable artifact per D10/D18). No interactive satisfaction check in the portal — operator conducts that in the cockpit and relays outcome out-of-band. Held-out dataset remains hidden (D18, held-out-regeneration handover edge-case per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:206` + `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/AD-WebApp.md:300-302`).

**Transition out of J7:** Graph reaches END. Subsequent operator interaction starts a new project thread (returning to J0) unless the delivered project is picked up for a retainer continuation or soft handover per D12 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:72`).

---

## §5 — What Transitions Look Like

Transitions are **not animations of panels appearing**. They are new compositions that replace the previous one with visual continuity (shared header, shared palette, preserved conversation history) and deliberate change (new affordances, repositioned hierarchy).

**Design guidance:**
- A transition should take 300–500ms, with a choreographed reveal — not simultaneous appearance of multiple new elements.
- The conversation history must persist through every transition. A scrollable conversation log that remains accessible is a trust signal (and matches the PCG invariant that child-agent history lives in role-scoped checkpoint namespaces — `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md:215`).
- Each transition should be accompanied by a PM-voiced event narration — either written into PCG `messages` at lifecycle bookends (J0→J1 start, J7 final product) or derived from `handoff_log` records for intra-pipeline transitions (J1→J2, J2→J3, etc.).
- Transitions are **PCG-state-driven**, not user-action-driven. The operator doesn't click "show me the pipeline rail" — the pipeline rail materializes when `handoff_log` contains its first non-synthetic record (PM → HE delivery).

**State-regression handling.** If a user rejects Gate 1 or Gate 2 (`(PM, PM, submit, accepted=false)` recorded per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:591-593`), the UI stays in the gate-pending journey state (J3 or J5) with a prominent "revising" affordance rather than retreating to an earlier state. The PCG does not structurally retreat; it re-runs the packaging work under the same `current_phase`. Exact revision UX is a mockup Session 4 open question.

---

## §6 — Portal Journey States (D18-Compliant)

The Client Portal, per D18 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:178-223`), is observation-only. Its journey states are a subset of the cockpit states — the portal doesn't exist until the PCG has reached a state worth showing to a stakeholder.

| Cockpit state | Portal state | Why |
|---|---|---|
| J0 (Virgin, pre-PCG) | **does not exist** | No project thread; no stakeholder invitation yet |
| J1 (PM ↔ stakeholder scoping) | **does not exist** | Scoping is operator↔PM; stakeholder not invited yet |
| J2 (HE authoring) | **does not exist** | Nothing stakeholder-appropriate yet; Gate 1 package still being assembled |
| J3 (Gate 1 pending) | **first stakeholder surface (per D17)** | Gate 1 hero document is pre-rendered for stakeholder review; no action buttons; PM voice is monologue |
| J4 (Research & Architecture) | Ambient narrative updates | Phase-level narrative only; no specialist-loop detail |
| J5 (Gate 2 pending) | Gate 2 informational rendering | Same pattern as J3; no action buttons |
| J6 (Planning & Development) | Ambient narrative, phase milestones | No todo-level, no subagent, no sandbox |
| J7 (Acceptance & Delivery) | Final deliverable + arc narrative | Packaged artifacts render; satisfaction check is cockpit-only |

**The cockpit progressive reveal is 8 states; the portal progressive reveal is 5 states (J3 through J7) because the portal doesn't exist before the first Gate 1 document is ready.**

All portal composition is **ambient or drill-down only** — per D18's amendment to D13 (`@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness_web/DECISIONS.md:220`). Action-required and conversational modes do not exist in the portal.

---

## §7 — Known Unknowns (to be tested via mockups, not resolved in prose)

1. **How aggressive is the sparseness at J0?** Manus-minimal (input-only, almost no chrome) vs. Meta-Harness-minimal (input + identity chrome + small PM chip)? Session 1 mockups across three families answer this.
2. **Does the "Working draft" artifact hint at J1 feel earned or decorative?** Risk: too subtle = user doesn't notice; too present = violates the sparseness thesis. Mockup.
3. **At J2 and J4, should the left rail show only engaged agents, or should it show all 7 with clear visual differentiation between "engaged" and "not yet reached"?** The strict progressive-reveal thesis says "engaged only." Counter-argument: showing the full 7 in a ghost state signals the system's topology earlier and helps the operator form a mental model. Mockup to test both.
4. **Gate-revision UX at J3 / J5.** When the operator picks "Revise" instead of "Approve," how does the rejection reasoning get captured and routed back to the PM? Inline comment threads on the rendered document? A rejection-reason prompt? The PCG records `(PM, PM, submit, accepted=false)` with the reasoning in `brief` (per `@/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/DECISIONS.md:593`); the UI must capture that reasoning well.
5. **Specialist-loop rendering at J4.** Architect↔Researcher (C3) and Architect↔HE Stage 2 (S1/S2) are non-PM-mediated. The handoff log needs a distinct visual treatment for these — but how distinct? A second column? An indentation? A tag? Mockup.
6. **Phase-loop density at J6.** The Developer phase loop (announce → execute → submit → review) repeats N times where N = number of plan phases. How does the plan timeline render N=3 vs. N=12 without becoming unreadable? Session 4 mockup.
7. **Sandbox surface at J6.** Q7 (cockpit-only per D18) — when to reveal the three-panel IDE-like composition, whether it replaces the cockpit's rich-state chrome or is a drill-down from it. Mockup Session 4+.
8. **Acceptance-stamp UX at J7.** How prominent are the stamp cards? How does `accepted=false` visually differ from a pending stamp? How is the evidence linked? Mockup.
9. **Satisfaction check at J7.** PM's `ask_user` satisfaction prompt is the very last interaction before END. Does it read as a modal? An inline final question? Something between? Mockup.
10. **Concurrent multi-project navigation × journey states.** Q10 in `AD-WebApp.md` — if an operator has 5 projects each in different journey states (one in J1, two in J6, one in J7…), the project picker becomes a journey-state-diverse view. Model once Q10 enters scope.

---

## §8 — What This Document Is Not

- **Not a component specification.** Per-component APIs, state shapes, and file layouts live in code once scaffolding begins.
- **Not a style guide.** Family-specific visual tokens live in `mockup_briefs/family-*.md`.
- **Not the final word.** Every journey state listed here is a hypothesis to be tested by live mockups. Amend this doc freely as mockup evidence surfaces new understanding — but any amendment must trace back to a line in `meta_harness/AD.md` or `meta_harness/DECISIONS.md`, or it is design over-reach.
- **Not a replacement for the mockup briefs.** The briefs remain the authoritative visual specification for **rich-state (J6 / J7)** composition in each family. This document specifies the PCG-grounded progression through which the UI reveals itself.

---

## §9 — Relationship to Existing Docs

- **`POSITIONING.md` §5** (interaction model — context-adaptive modes) — complementary, not redundant. The four modes (ambient / action-required / conversational / drill-down) are **within-state** UI responses. The journey states are **between-state** compositional changes. Every journey state supports whichever subset of modes applies to it (per D18, portal supports only ambient + drill-down).
- **`DECISIONS.md` D13** (context-adaptive modes) — this doc extends D13 without contradicting it. D13 defines *what happens within a state*; this doc defines *how states progress*.
- **`DECISIONS.md` D17** (portal first-login UX) — D17 locks the *content* of J3 portal (Gate 1 hero document, operator-toggleable source-material visibility, PM-as-narrative-voice). This doc situates J3 in the larger eight-state progression.
- **`DECISIONS.md` D18** (pure broadcast portal) — this doc respects D18 throughout. All portal states are observation-only; all approval and action-required UX is cockpit-only.
- **`AD-WebApp.md` Q1** (layout) — this doc **resolves** the "single-canonical-layout" framing of Q1 at a higher level: there is no single layout; there are eight cockpit states and five portal states. Residual layout sub-questions resolve in mockup sessions.
- **`AD-WebApp.md` Q3 / Q4 / Q6 / Q7** — rescoped to cockpit-only per D18; this doc assigns each rescoped question to the journey state where it surfaces (Q3 at J3/J5/J7; Q4 + Q6 + Q7 at J6).
- **`mockup_briefs/family-*.md`** — remain valid as rich-state visual specifications per family. Now understood as the endpoint of the reveal (J6 / J7), not the starting point.
- **`ROADMAP.md`** — the execution plan for building these journey states across three separate repos (one per family). The session sequence maps onto journey states: Session 1 = J0; Session 2 = J1–J3; Session 3 = J4–J6a; Session 4 = J6b–J7.
- **`../meta_harness/AD.md`** and **`../meta_harness/DECISIONS.md`** — the backend source of truth. Every assertion in this document is cross-cited against these files.

---

## §10 — Canonical Summary (TL;DR)

> Meta Harness's UI is a **progressive reveal** across eight journey states (J0 virgin through J7 acceptance-and-delivery), each one grounded in a specific region of the PCG's six-phase lifecycle (`scoping → research → architecture → planning → development → acceptance`). The UI reshapes itself as `current_phase`, `current_agent`, and `handoff_log` evolve in the backend. Every new affordance (memory hint → first multi-agent handoff → first-class deliverable → approval gate → specialist loops → phase-execution telemetry → acceptance stamps → final product + satisfaction) appears only when PCG state justifies it. The portal is a subset of five observation-only states (J3 through J7) per D18. The mockup briefs remain the authoritative visual spec for rich-state composition (J6 / J7); this document specifies the full progression through which the UI reaches them.

