# Agent Harness Decision Surface Audit

## Status

Working `local-docs/` audit produced on 2026-04-27.

This document is local coding-agent reference material, not a product spec and not an AD decision. It is intended to help Jason and future Meta Harness agents convert underspecified harness decisions into:

1. AD decisions.
2. Derived implementation specs under `docs/specs/`.
3. Ticket-ready implementation work.

Per `AGENTS.md`, decisions originate in `AD.md` and flow into specs. Any proposed decision below must be raised against `AD.md` before a derived spec is treated as authoritative.

## Source basis

Primary sources reviewed:

- `Vision.md:20-42` — product invariants.
- `README.md:35-159` — operational story, role boundaries, optimization loop, visible proof, headless-first surfaces.
- `meta_harness/AGENTS.md:150-329` — coding-agent governance, docs hierarchy, local-docs role, downstream development readiness.
- `meta_harness/AD.md:115-231` — open PM/HITL questions.
- `meta_harness/AD.md:915-960` — specialist loops and agent primitive summary.
- `meta_harness/docs/specs/handoff-tools.md:85-91`, `116-254` — terminal-exit invariant and 23-tool matrix.
- `meta_harness/docs/specs/handoff-tool-definitions.md:223-326` — concrete role toolsets and gate middleware contract.
- `meta_harness/docs/specs/pcg-data-contracts.md:18-34`, `109-180` — PCG state and mount-as-subgraph contract.
- `meta_harness/docs/specs/project-data-contracts.md:395-479` — product record read/write APIs and role boundaries.
- `meta_harness/docs/specs/repo-and-workspace-layout.md:28-83`, `111-279`, `285-339` — intended future agent package layout, factory shape, workspace/memory tree.
- `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md:193-397` — HE analytics operations and visibility policy.
- `meta_harness/docs/specs/evaluation-evidence-workbench.md:220-318` — HE evidence workbench, EBDR boundary, minimal tooling stance.
- `meta_harness/local-docs/SDK_REFERENCE.md` — SDK verification map.
- `meta_harness/local-docs/langsmith-he-reference.md` — HE LangSmith/OpenEvals capability matrix.

Auggie was intentionally not used for this pass per Jason's instruction.

## Executive conclusion

The existing docs correctly lock the macro-architecture:

- Seven peer Deep Agent role graphs.
- One thin PCG coordination node.
- Explicit `Command.PARENT` handoffs.
- Role-scoped checkpoint namespaces and memory.
- Project Records Layer for durable user-visible product records.
- Developer blindness to private eval artifacts.

The next decision surface is not PCG topology. It is the **seven role harnesses**:

- What each role can see.
- What each role can call.
- What each role must produce.
- How each role recovers from failures.
- Which tools are product operations versus procedural skills.
- Which subagents are allowed and whether they are durable peer agents or ephemeral workers.
- Which middleware is structural, which is prompt steering, and which is still only a design vision.
- How the role's outputs become Project Records Layer artifacts, analytics views, acceptance stamps, or feedback packets.

The most important finding is broader than F1.

**Critical:** several documented specialist loops have no reciprocal handoff path in the current concrete tool catalog. The README and AD promise loops like Developer -> Evaluator -> Developer, Developer -> HE -> Developer, Planner -> HE/Evaluator -> Planner, Architect/HE/PM -> Researcher -> requester, and specialist -> PM -> specialist. The handoff matrix mostly defines the request side but often lacks the return side.

That means the role harness decision surface is not complete. We should treat this as the top ticket before implementing role factories.

## Harness decision rubric

A role harness is not just a prompt. For each of the seven agents, the buildable contract should specify these primitives:

1. **Role mission and authority boundary** — what the role owns and must not do.
2. **Entry contexts** — which handoff records, project records, files, and memories the role receives.
3. **Model profile** — default model, provider constraints, server-side tool injection, and experiment protocol.
4. **Model-visible tools** — handoff tools, product-record tools, execution tools, analysis tools, and approval/HITL tools.
5. **Hidden runtime tools/helpers** — backend-owned operations, record assembly helpers, trace metadata helpers, artifact registration.
6. **Middleware** — universal stack, role-specific gates, final-turn guard, HITL, permissions, shell allowlist, progress/stagnation behavior.
7. **Filesystem/backend permissions** — read/write roots, project memory roots, private roots, sandbox/local/devbox differences.
8. **Memory and skills** — role `AGENTS.md`, `/memories/`, skill directories, when memory is read, what learning is allowed.
9. **Ephemeral subagents** — allowed `task` workers, their tools, visibility, and whether they can see private artifacts.
10. **Artifact obligations** — required deliverables, artifact kinds, visibility, Project Records Layer registration, stale/update semantics.
11. **Trace/observability contract** — LangSmith metadata, project/handoff IDs, allowed trace access, trace links in artifacts.
12. **Feedback/acceptance semantics** — who can pass/fail, who gives directional feedback, who can ask the PM, and what happens after rejection.
13. **Conformance tests** — behavioral tests and architectural tests that fail when the role harness silently reverses an architecture decision.

## Top cross-agent tickets

### T-HARNESS-001 — Critical — Add reciprocal response paths for specialist loops

**Problem:** The docs promise multiple specialist loops, but the concrete handoff tool catalog does not provide return tools for several of them.

**Evidence:**

- `README.md:59-67` says the Developer submits each phase to Evaluator and HE, receives pass/fail plus EBDR-1 feedback, then iterates.
- `README.md:101-117` diagrams Developer -> Evaluator / HE -> Developer loop.
- `AD.md:915-947` explicitly lists Developer -> Evaluator -> Developer, Developer -> HE -> Developer, Architect -> Researcher -> Architect, Planner -> HE/Evaluator, and specialist -> PM clarification loops.
- `handoff-tools.md:191-206` defines Developer -> Evaluator/HE submit tools and consultation/question tools.
- `handoff-tool-definitions.md:291-297` gives Evaluator only rows 12, 22, 23; HE only rows 6, 11, 14, 21, 22, 23; Researcher only rows 7, 22; Planner only rows 9, 19, 20, 22.
- There is no Evaluator -> Developer phase-review return tool, no HE -> Developer EBDR return tool, no Researcher -> Architect/HE targeted-research return tool, no HE/Evaluator -> Planner gate recommendation return tool, and no PM -> specialist answer tool.

**Decision to make:** Choose the response primitive for non-pipeline loops.

**Options:**

1. **Concrete reciprocal tools** — add explicit return tools for each loop, e.g. `return_phase_review_to_developer`, `return_harness_feedback_to_developer`, `return_research_findings_to_architect`, `return_gate_recommendations_to_planner`, `answer_question_to_developer`, etc.
2. **Active-handoff response primitive** — add role-specific generic response tools whose target is derived from the inbound handoff record, not model-supplied.
3. **PM-mediated responses** — force all specialist responses through PM, preserving PM as POC but slowing technical loops.

**Recommended direction:** Prefer **concrete reciprocal tools** for blocking/phase loops and a carefully bounded **answer-current-question** primitive for PM clarification responses if concrete PM answer tools become too many. The current architecture already values explicit tool names over hidden router intelligence; the default should remain concrete.

**Acceptance criteria:**

- Every loop named in `AD.md:915-947` has both request and response paths.
- Developer can receive Evaluator phase findings without PM mediation.
- Developer can receive HE EBDR-1 feedback without seeing hidden eval artifacts.
- Planner can receive gate recommendations from HE and Evaluator.
- Architect and HE can receive targeted Researcher findings from their own consultation requests.
- PM can answer specialist questions and route the answer back to the asking specialist.
- `handoff-tools.md`, `handoff-tool-definitions.md`, `approval-and-gate-contracts.md`, and `pcg-data-contracts.md` are updated together.
- Conformance tests assert no documented loop is one-way unless explicitly non-returning.

**Docs to update:**

- `AD.md §4 Specialist Loops`.
- `AD.md §4 Handoff Protocol`.
- `docs/specs/handoff-tools.md`.
- `docs/specs/handoff-tool-definitions.md`.
- `docs/specs/approval-and-gate-contracts.md`.
- `docs/specs/pcg-data-contracts.md` if new record fields are needed.

### T-HARNESS-002 — High — Resolve PM-session project awareness and live monitoring

**Problem:** F1 remains correct: PM-session usefulness depends on project awareness, project memory reads, Project Records Layer reads, and live snapshot semantics.

**Evidence:**

- `Vision.md:28-33` makes PM the primary POC across headless surfaces.
- `README.md:128-150` promises shared state, artifacts, file trees, diffs, command logs, and PR status across web/TUI/API/channel surfaces.
- `AD.md:171-231` leaves `OQ-PM1`, `OQ-PM2`, and `OQ-PM3` open.
- `project-data-contracts.md:425-445` defines read APIs but says PM session tools are thin wrappers; the PM harness ergonomics remain unresolved.

**Decision to make:** Define the PM session harness for project awareness.

**Recommended direction:** Hybrid:

- Inject a compact active-project summary into PM session context.
- Expose explicit Project Records Layer read tools for deep queries.
- Surface project memory through a virtual `/projects/{project_id}/...` read-only filesystem view where safe.
- Use `capture_project_snapshot` only for explicit live-state requests.

**Acceptance criteria:**

- PM can answer active project status from `pm_session`.
- PM can list artifacts and HE analytics from `pm_session`.
- PM can request read-only live snapshots when allowed.
- PM cannot write to project sandboxes from `pm_session`.
- `local_workspace` live snapshot requires explicit opt-in.
- Every read records `project_data_events`.

**Docs to update:**

- `AD.md` open questions.
- `docs/specs/pcg-server-contract.md`.
- `docs/specs/project-data-contracts.md`.
- New or expanded PM harness spec.

### T-HARNESS-003 — High — Create a first-class agent harness contract spec

**Problem:** The AD locks many agent primitives, but there is no single development-ready spec that tells a Developer how to assemble each role's full harness.

**Evidence:**

- `AD.md:949-960` summarizes model, middleware, prompts, tool assignments, and provider tools.
- `DECISIONS.md` describes universal `create_deep_agent()` shape with placeholders for `skills`, `memory`, `permissions`, and `subagents`.
- `repo-and-workspace-layout.md:28-83` gives the future package tree but not the full per-role factory contract.
- `repo-and-workspace-layout.md:285-339` gives workspace/memory directories but not concrete role memory/skill loading policy.

**Decision to make:** Decide whether role harness assembly is specified in one consolidated spec or seven role-specific specs.

**Recommended direction:** Create one derived spec, `docs/specs/agent-harness-contracts.md`, with one table per role. Split later only if a role grows a genuinely independent contract surface.

**Acceptance criteria:**

- For each role, the spec defines factory name, prompt path, role name, model default, handoff tools, product-record tools, execution tools, middleware, skills, memory roots, subagents, filesystem permissions, artifact obligations, and conformance tests.
- Spec is registered in `AD.md §9` and parent AD section has a pointer.
- No implementation agent must infer harness assembly from scattered prose.

### T-HARNESS-004 — High — Promote or block `approval-and-gate-contracts.md`

**Problem:** The gate contract is implementation-critical but still marked draft.

**Evidence:**

- `AD.md:955-956` depends on phase-gate middleware and `pcg_gate_context`.
- `handoff-tool-definitions.md:299-326` delegates exact gate behavior to `approval-and-gate-contracts.md`.
- The spec defines final-turn guard behavior and approval tool semantics, which are not optional.

**Decision to make:** Either promote the spec to active or list explicit blockers.

**Acceptance criteria:**

- Gate pass/fail, approval stamps, autonomous mode, final-turn guard, and `pcg_gate_context` projection are all testable.
- Gate failure returns `ToolMessage`, not `Command`.
- Final-turn guard is mandatory for all seven role harnesses.

### T-HARNESS-005 — High — Finalize role-specific provider/server-side tool policy

**Problem:** AD requires provider-specific server-side tools, but assignments are still guidance rather than a per-role buildable contract.

**Evidence:**

- `AD.md:958-960` says Architect/HE/Developer model defaults are TBD and server-side tool assignments are role-specific.
- `DECISIONS.md Q13` requires Anthropic server-side tools for v1 and delegates final per-agent provisioning.

**Decision to make:** Lock launch defaults and role-specific provider tool availability.

**Recommended direction:**

- PM: no web fetch by default; Project Records Layer and stakeholder tools dominate.
- HE: code execution plus LangSmith/OpenEvals skills; web search/fetch only for eval-method research.
- Researcher: web search/fetch primary.
- Architect: web search secondary, no broad execution unless needed for SDK verification.
- Planner: minimal external tools; may inspect artifacts and consult HE/Evaluator.
- Developer: code execution, shell/git, tool search, filesystem, test/browser tools.
- Evaluator: code/test/browser execution read-only; no write/edit code tools.

**Acceptance criteria:**

- Launch model defaults are explicit.
- Provider-specific tool descriptors are injected by provider profile, not scattered across role factories.
- Each role has tests proving disallowed provider tools are absent.

### T-HARNESS-006 — High — Convert `StagnationGuardMiddleware` into a buildable role contract

**Problem:** It is listed as universal middleware, but the design remains more vision than implementation contract.

**Evidence:**

- `AD.md:955` lists it in the universal baseline.
- `DECISIONS.md` describes design vision and notes implementation proof is still needed.

**Decision to make:** Define exact state schema, progress signals, thresholds, nudge text behavior, hard-stop behavior, and test cases.

**Acceptance criteria:**

- Each role has tuned thresholds.
- Progress signals include role-appropriate artifacts, todo updates, file writes, test runs, trace/eval analysis, and handoff tool calls.
- False positives are tested for Researcher/HE/Developer long-running legitimate work.

### T-HARNESS-007 — High — Resolve Developer HITL ownership

**Problem:** `OQ-1` asks who owns HITL during development phases.

**Evidence:**

- `AD.md:117-119` leaves this open.
- `DECISIONS.md Q8` gives `AskUserMiddleware` only to PM and Architect.
- `README.md:156-159` says harness engineering is participatory.

**Decision to make:** PM relay vs restricted Developer direct HITL.

**Recommended direction:** PM relay first. Developer uses `ask_pm` for stakeholder/scope/business questions; PM decides whether to ask the user. If this proves too slow, add a restricted Developer HITL tool later.

**Acceptance criteria:**

- Developer can resolve ambiguity without direct private user channel by default.
- PM remains primary POC.
- Scope-changing answers are recorded as project artifacts/events.

### T-HARNESS-008 — High — Finalize HE analytics product tools

**Problem:** HE analytics are a product promise, but model-visible publication tools are still described as future.

**Evidence:**

- `Vision.md:34-39` makes HE analytics first-class.
- `README.md:66-77` says HE publishes graphs, metrics, and scorecards.
- `harness-engineer-evaluation-analytics.md:193-255` defines operations but says future tools may expose them.

**Decision to make:** Decide which analytics operations become HE/Evaluator model-visible tools.

**Recommended direction:** Expose backend-owned tools for `publish_analytics_view`, `update_analytics_view`, `render_analytics_snapshot`, and `mark_analytics_view_stale`; do not expose direct database clients or raw LangSmith wrappers.

**Acceptance criteria:**

- HE can publish UI-renderable analytics from role work.
- Visibility policy is enforced structurally.
- Developer-safe leakage tests exist.

### T-HARNESS-009 — High — Define artifact publication obligations per role

**Problem:** Project Records Layer is specified, but each role's exact artifact obligations are not fully specified.

**Evidence:**

- `handoff-tools.md:71-83` requires artifact-producing tools to call `register_artifact`.
- `project-data-contracts.md:395-423` defines write APIs.
- Role deliverables are described in artifact-flow prose, not as a complete artifact-kind contract.

**Decision to make:** Define required artifact kinds, visibility, ownership, content refs, and registration timing per role.

**Acceptance criteria:**

- PM: PRD, approval packages, stakeholder decision records, final delivery summaries.
- HE: eval criteria, public datasets, held-out datasets, judge configs, eval harnesses, EBDR packets, analytics source JSON, analytics views.
- Researcher: research bundles, citations, SDK/API evidence.
- Architect: design specs, tool schemas, prompt contracts, state diagrams, evalability notes.
- Planner: phased plans, gate map, acceptance checks, risk/rollback notes.
- Developer: candidate snapshots, diffs, build logs, test results, PR refs, phase deliverables.
- Evaluator: phase findings, acceptance stamps, conformance reports, UI verification evidence.

### T-HARNESS-010 — Medium/High — Define role permissions and filesystem boundaries

**Problem:** The intended workspace tree exists, but role permissions are not locked.

**Evidence:**

- `repo-and-workspace-layout.md:285-339` describes role workspace/memory tree.
- `project-data-contracts.md:447-479` defines role/surface access boundaries.
- `DECISIONS.md` placeholder includes `permissions=[<role filesystem rules>]`.

**Decision to make:** Define read/write roots for every role and every execution mode.

**Acceptance criteria:**

- Developer cannot read HE held-out datasets/rubrics/judge prompts.
- Evaluator can inspect code/tests without modifying implementation.
- HE can read eval evidence and publish analytics but cannot bypass visibility policy.
- PM can read project artifacts and snapshots through brokered operations, not raw cross-thread mutable files.
- Local workspace mode has stricter write/shell approvals.

### T-HARNESS-011 — Medium/High — Define role memory and skill loading strategy

**Problem:** The docs say memory through files, skills via directories, and prompts in `.md`, but role-specific memory/skill policy is not complete.

**Evidence:**

- `AGENTS.md:150-155` defines one factory per agent, system prompts in `.md`, memory through files.
- `repo-and-workspace-layout.md:285-339` defines role `AGENTS.md`, `memory/`, `skills/`, and project directories.
- Deep Agents skills are not automatically inherited by custom subagents; role skills must be explicit.

**Decision to make:** Define role memory and skills directories, loading rules, and allowed learning behavior.

**Acceptance criteria:**

- Every role factory points to the correct prompt, memory, and skills path.
- Memory-reading order is specified per role.
- Private eval memories never leak into Developer-visible memory.
- HE LangSmith/OpenEvals workflows are skills by default unless explicit-tool criteria are met.

### T-HARNESS-012 — Medium — Clean stale deferral/security/deployment language

**Problem:** Several docs still use future/v2/local-first language that conflicts with current launch posture.

**Evidence:**

- `AGENTS.md:304-307` requires surfacing deferrals.
- `AD.md §8` still has stale local-first/single-user wording in tension with current web/headless production commitments.

**Acceptance criteria:**

- Deferrals are classified as launch blocker, implementation detail, post-launch enhancement, or historical rationale.
- Security/deployment posture matches Project Records Layer auth and web/headless product behavior.

## Per-agent harness decision surface

## 1. Project Manager harness

### What is already specified

- PM is primary point of contact: `Vision.md:31-33`, `README.md:91-99`.
- PM owns pipeline delivery tools, `finish_to_user`, and `request_approval`: `handoff-tool-definitions.md:291`.
- PM receives `AskUserMiddleware` and phase gate middleware: `AD.md:955`.
- PM session and project modes share the same role identity but different thread kinds: `AD.md:322-410`, `pcg-data-contracts.md:152-159`.

### What remains underspecified

- PM session project awareness and memory projection.
- PM's exact `spawn_project` / project creation harness primitive.
- PM's Project Records Layer read tools and ergonomics.
- PM's answer path back to specialists after `ask_pm`.
- PM approval package rendering and acceptance/rejection recovery loop.
- PM mode-specific prompt behavior: `pm_session` terminal conversation vs project thread lifecycle coordinator.
- PM artifact obligations: PRD, approval package, decision record, final delivery narrative.

### PM tickets

#### PM-001 — High — Specify PM dual-mode harness contract

**Decision:** Define how one PM role behaves differently in `pm_session` and `project` threads without creating two roles.

**Acceptance criteria:**

- `pm_session` tools include project portfolio/status/artifact/analytics reads and project spawn.
- `project` tools include lifecycle delivery, approval, PM answer, and terminal emission.
- The same PM memory identity is preserved without contaminating project-scoped state.

#### PM-002 — High — Specify PM project creation/spawn primitive

**Decision:** Define whether `spawn_project` is a PM model-visible tool, backend operation triggered by UI/headless ingress, or both.

**Acceptance criteria:**

- Calls `create_project_registry` idempotently.
- Creates LangGraph `project` thread with correct metadata.
- Seeds initial state without copying PM-session checkpoint history.
- Records project data event and trace correlation.

#### PM-003 — High — Specify PM answer-to-specialist response tools

**Decision:** Add PM response path for `ask_pm` queries from HE, Researcher, Architect, Planner, Developer, and Evaluator.

**Acceptance criteria:**

- Asking specialist receives answer in its own role context.
- PM can ask user first if stakeholder input is required.
- Scope-changing answer records a decision artifact.
- Non-scope answer can return directly without user interruption.

#### PM-004 — Medium/High — Specify approval package rendering and rejection recovery

**Decision:** Define exact approval package artifact shape for scoping->research and architecture->planning.

**Acceptance criteria:**

- `request_approval` package includes artifact refs, summary, risks, user-facing decision question, and approval type.
- Rejection path returns PM to the right revision activity, not an ambiguous state.
- Autonomous mode records approval without user prompt but preserves auditability.

#### PM-005 — Medium — Specify PM stakeholder decision record artifacts

**Decision:** Define durable records for user/stakeholder decisions, scope changes, and business-priority changes.

**Acceptance criteria:**

- Records are visible to PM and relevant project roles.
- Developer sees only safe/public consequences, not private stakeholder notes if flagged.
- Project Records Layer has artifact kind and visibility policy.

## 2. Harness Engineer harness

### What is already specified

- HE owns evaluation science: `Vision.md:34-36`, `README.md:45-49`.
- HE owns analytics and Developer-safe boundary: `harness-engineer-evaluation-analytics.md:357-394`.
- HE Evidence Workbench prefers CLI/SDK/OpenEvals/skills before product tools: `evaluation-evidence-workbench.md:293-316`.
- HE toolset currently includes eval-suite return, harness acceptance, eval coverage return, research request, ask_pm, and coordinate_qa: `handoff-tool-definitions.md:292`.

### What remains underspecified

- HE -> Developer feedback return path.
- HE model-visible analytics publication tools.
- HE evidence workbench skills versus explicit tools.
- HE internal analysis subagents.
- HE artifact taxonomy and private/public visibility boundaries.
- HE acceptance stamp criteria.
- HE access to code execution and LangSmith/OpenEvals evidence under sandbox constraints.

### HE tickets

#### HE-001 — Critical — Add HE-to-Developer EBDR feedback path

**Decision:** Define the concrete handoff return from HE phase review to Developer.

**Acceptance criteria:**

- Developer receives EBDR-1 packet after `submit_phase_to_harness_engineer`.
- Packet includes delta, boundary, localization, routing, uncertainty.
- Packet excludes hidden rubrics, held-out examples, judge prompts, private dataset rows, scoring logic, and HE-private reasoning.
- Feedback packet is registered as a project artifact with Developer-safe visibility.

#### HE-002 — High — Specify HE analytics tools

**Decision:** Expose `publish_analytics_view`, `update_analytics_view`, `render_analytics_snapshot`, and `mark_analytics_view_stale` as backend-owned HE tools or explicitly choose a different mechanism.

**Acceptance criteria:**

- HE can publish UI-renderable analytics without database access.
- Backend validates schema and visibility.
- Developer-safe views are separately authorized from stakeholder-visible views.

#### HE-003 — High — Specify HE Evidence Workbench harness profile

**Decision:** Define HE skills, allowed CLI/SDK workflows, explicit tool candidates, and permissions.

**Acceptance criteria:**

- HE uses LangSmith CLI when native.
- HE uses SDK/OpenEvals when precision/composition is needed.
- No raw wrapper tools for list/get/create operations unless repeated high-friction criteria are met.
- Outputs preserve stable LangSmith/OpenEvals identifiers.

#### HE-004 — High — Specify HE private/public artifact taxonomy

**Decision:** Define artifact kinds and visibility for eval criteria, public datasets, held-out datasets, rubrics, judge configs, calibration reports, experiment outputs, analytics source JSON, EBDR packets, and acceptance evidence.

**Acceptance criteria:**

- Developer-visible package excludes private eval internals.
- PM/internal surfaces can inspect summaries.
- Stakeholder-visible promotion is PM-owned.

#### HE-005 — Medium/High — Specify HE internal analysis subagents

**Decision:** Define whether HE receives ephemeral analysis workers for trace clustering, candidate comparison, regression analysis, and tool misuse detection.

**Acceptance criteria:**

- Subagents remain ephemeral and non-PCG.
- Subagents do not emit Developer-facing feedback.
- Subagents preserve LangSmith locator provenance.
- HE remains synthesizer.

#### HE-006 — Medium — Specify HE harness acceptance criteria

**Decision:** Define when `submit_harness_acceptance(accepted=True)` is allowed.

**Acceptance criteria:**

- Acceptance covers eval harness quality, dataset policy, judge calibration, analytics validity, and EBDR privacy.
- Rejection includes safe remediation routing.

## 3. Researcher harness

### What is already specified

- Researcher owns ecosystem research, SDK/API/model capability evidence: `README.md:51-53`, `README.md:91-99`.
- Researcher has `return_research_bundle_to_pm` and receives `request_research_from_researcher`: `handoff-tool-definitions.md:293`.
- Researcher is a primary recipient of web search/fetch provider tools per AD guidance: `AD.md:960`.

### What remains underspecified

- Researcher return path to Architect or HE after targeted consultation.
- Research artifact schema and citation/provenance requirements.
- Web search/fetch policy, source reliability, and citation validation.
- Researcher memory strategy for reusable SDK/API learnings.
- Researcher model defaults/tool provisioning.

### Researcher tickets

#### RES-001 — Critical — Add Researcher response path to consultation requester

**Decision:** Define how Researcher returns targeted findings to Architect, HE, or PM depending on who requested research.

**Acceptance criteria:**

- Architect research requests can return directly to Architect.
- HE research requests can return directly to HE.
- PM research requests can return to PM.
- Returned artifact preserves question, evidence, citations, uncertainty, and recommended next role.

#### RES-002 — High — Specify research bundle artifact schema

**Decision:** Define research bundle shape.

**Acceptance criteria:**

- Includes question/context, sources, findings, constraints, SDK/API version notes, uncertainty, implementation implications, and links.
- Distinguishes official docs/source-verified facts from speculative recommendations.
- Registers artifact in Project Records Layer.

#### RES-003 — Medium/High — Specify Researcher web tool policy

**Decision:** Define provider-neutral web search/fetch capabilities and source hierarchy.

**Acceptance criteria:**

- Official docs/source repos preferred for SDK behavior.
- Web facts include retrieval date/source URLs.
- External web results cannot override local source verification for SDK behavior.

#### RES-004 — Medium — Specify Researcher memory/skills policy

**Decision:** Define what reusable research learnings can be stored in Researcher memory.

**Acceptance criteria:**

- Cross-project memory stores stable SDK/API patterns, not project-private facts unless appropriately scoped.
- Researcher skills are explicit and not inherited by subagents accidentally.

## 4. Architect harness

### What is already specified

- Architect owns system design, tool schemas, system prompts, orchestration logic, component definitions: `README.md:51-53`, `README.md:91-99`.
- Architect can request research and submit spec to HE: `handoff-tool-definitions.md:294`.
- Architect receives `AskUserMiddleware` and phase gate middleware: `AD.md:955`.
- Architect must not do Researcher or Planner work: `DECISIONS.md` behavioral invariants.

### What remains underspecified

- Design package artifact schema.
- Architect `AskUserMiddleware` scope and toggle behavior.
- Research-gap loop return semantics.
- HE evalability review loop integration and revision semantics.
- Prompt contracts and tool schema artifact format.
- Architectural conformance tests that Evaluator later enforces.

### Architect tickets

#### ARCH-001 — High — Specify design package artifact schema

**Decision:** Define minimum design package contents.

**Acceptance criteria:**

- Includes architecture overview, component contracts, tool schemas, prompt contracts, state/data contracts, security/privacy notes, evalability hooks, observability plan, and open risks.
- Artifact is buildable by Planner without reverse-engineering hidden intent.

#### ARCH-002 — High — Specify Architect/Researcher research-gap loop

**Decision:** Define how Architect requests targeted research and resumes after Researcher returns findings.

**Acceptance criteria:**

- Architect's request includes exact knowledge gap, decision blocked, required evidence, and deadline/priority.
- Researcher returns directly to Architect.
- Architect records how research changed or did not change the design.

#### ARCH-003 — Medium/High — Specify Architect interactive spec HITL

**Decision:** Define when Architect may ask user directly versus ask PM.

**Recommended direction:** Architect direct user interaction only when an explicit interactive-spec mode is enabled; otherwise ask PM.

**Acceptance criteria:**

- User-facing design questions are narrow and decision-oriented.
- Scope/business changes route to PM.
- Interaction is traceable and represented in artifacts.

#### ARCH-004 — Medium/High — Specify HE evalability review integration

**Decision:** Define revision loop after `submit_spec_to_harness_engineer` and `return_eval_coverage_to_architect`.

**Acceptance criteria:**

- HE feedback can require design changes before planning.
- Architect must incorporate or explicitly reject HE evalability findings with rationale.
- PM approval package includes evalability status.

#### ARCH-005 — Medium — Specify prompt/tool contract artifact conventions

**Decision:** Define how Architect writes prompt contracts and tool schemas for downstream implementation.

**Acceptance criteria:**

- Prompts remain external `.md` files.
- Tool schemas distinguish model-visible fields from hidden runtime fields.
- Prompt contracts encode behavioral invariants, not final prose only.

## 5. Planner harness

### What is already specified

- Planner owns phased implementation plan with eval breakpoints: `README.md:91-99`.
- Planner can consult HE and Evaluator on gates: `handoff-tool-definitions.md:295`.
- Planner returns plan to PM: `handoff-tool-definitions.md:233`, `295`.

### What remains underspecified

- Plan artifact schema.
- Return path from HE/Evaluator consultations to Planner.
- `plan_phase_id` naming/versioning rules.
- How eval breakpoints map to Developer phase tools.
- Whether gate consultation is optional, recommended, or required for certain project types.
- Risk/rollback/dependency planning obligations.

### Planner tickets

#### PLAN-001 — Critical — Add HE/Evaluator gate-consultation response path to Planner

**Decision:** Define how HE and Evaluator return gate recommendations to Planner.

**Acceptance criteria:**

- Planner receives HE eval gate placement recommendations.
- Planner receives Evaluator application-quality gate recommendations.
- Plan records which recommendations were incorporated.

#### PLAN-002 — High — Specify implementation plan artifact schema

**Decision:** Define minimum plan contents.

**Acceptance criteria:**

- Includes phases, `plan_phase_id`s, dependencies, deliverables, eval breakpoints, required tests, acceptance criteria, rollback strategy, and expected artifacts.
- Developer can execute without needing hidden design intent.
- Evaluator can judge phase completion from the plan.

#### PLAN-003 — High — Specify `plan_phase_id` contract

**Decision:** Define identifier format, uniqueness, versioning, and display name policy.

**Acceptance criteria:**

- Developer phase tools use stable IDs, not ambiguous free-form labels.
- Phase IDs survive plan revisions.
- Handoff records can associate submissions with phase plan entries.

#### PLAN-004 — Medium/High — Specify gate consultation policy

**Decision:** Decide when Planner must consult HE/Evaluator.

**Acceptance criteria:**

- High-risk/eval-heavy projects require HE gate consultation.
- UI-heavy/application-conformance-heavy projects require Evaluator consultation.
- Planner prompt and conformance tests enforce the policy.

#### PLAN-005 — Medium — Specify risk and rollback planning obligations

**Decision:** Define how Planner captures sequencing risk, migration risk, and rollback/test checkpoints.

**Acceptance criteria:**

- Developer receives actionable rollback/test strategy.
- Evaluator can fail missing risk controls when relevant.

## 6. Developer harness

### What is already specified

- Developer is optimizer/implementer and remains blind to private eval artifacts: `README.md:55-67`, `101-117`.
- Developer owns phase announce/submit tools and final return to PM: `handoff-tool-definitions.md:296`.
- Developer receives phase gate middleware but not `AskUserMiddleware`: `AD.md:955`, `AD.md:117-119`.
- Developer final return requires Evaluator acceptance and HE acceptance if HE participated: `handoff-tools.md:155-176`.

### What remains underspecified

- Developer feedback return paths from HE and Evaluator.
- Developer HITL ownership.
- Developer optimization state/experience store/candidate snapshots.
- Developer sandbox/shell/git/PR permissions and tool approvals.
- Developer subagents and skills.
- Developer-safe trace/eval artifact access.
- Developer routing boundary among HE, Evaluator, and PM.

### Developer tickets

#### DEV-001 — Critical — Specify Developer phase-feedback loop

**Decision:** Define how Developer receives Evaluator pass/fail findings and HE EBDR feedback after phase submission.

**Acceptance criteria:**

- Developer cannot be stranded after submitting a phase.
- Evaluator can route pass/fail findings to Developer.
- HE can route EBDR feedback to Developer.
- Rejection creates clear next action for Developer.

#### DEV-002 — High — Specify Developer optimization experience store

**Decision:** Define candidate snapshots, diffs, score summaries, logs, hypotheses, and trace references available to Developer.

**Acceptance criteria:**

- Developer sees enough signal to optimize.
- Developer does not see hidden rubrics, held-out examples, judge prompts, or scoring logic.
- Candidate snapshots are versioned and registered.
- HE/Evaluator can reference allowed evidence without leaking private artifacts.

#### DEV-003 — High — Specify Developer execution tool and permission profile

**Decision:** Define Developer's filesystem, shell, git, package manager, test, browser, and PR tooling profile across `managed_sandbox`, `external_devbox`, and `local_workspace`.

**Acceptance criteria:**

- Developer can clone/build/test/commit/push/open draft PR in allowed modes.
- Dangerous shell/file operations respect approval/allowlist policy.
- Developer cannot access HE-private/evaluator-private roots.
- Local workspace mode is guarded.

#### DEV-004 — High — Resolve Developer HITL through PM relay

**Decision:** Close `OQ-1`.

**Acceptance criteria:**

- Developer routes stakeholder/scope questions through PM by default.
- PM decides whether to ask user.
- Direct Developer HITL is either explicitly rejected or gated behind a future opt-in mode.

#### DEV-005 — Medium/High — Specify Developer subagent policy

**Decision:** Decide whether Developer receives ephemeral coding/test/research subagents through Deep Agents `task` tool.

**Recommended direction:** Allow ephemeral workers only for isolated code/test/search subtasks, never as durable project roles.

**Acceptance criteria:**

- Subagents receive complete instructions per call.
- Subagents do not inherit private skills/memory unless explicitly configured.
- Subagents cannot access private eval artifacts.
- Developer remains responsible for integration and final tool calls.

#### DEV-006 — Medium/High — Specify Developer routing decision prompt contract

**Decision:** Encode when Developer routes to HE, Evaluator, or PM.

**Acceptance criteria:**

- HE for eval harness/dataset/judge/calibration issues.
- Evaluator for spec/plan/code/UI/test acceptance.
- PM for scope/business/user-facing tradeoffs.
- Tool descriptions and prompt examples prevent vague `request_evaluation` behavior.

## 7. Evaluator harness

### What is already specified

- Evaluator owns application/product acceptance: `README.md:59-64`, `91-99`.
- Evaluator owns `submit_application_acceptance`, `ask_pm`, and `coordinate_qa`: `handoff-tool-definitions.md:297`.
- Evaluator and HE are peer QA roles: HE owns harness/eval science, Evaluator owns app/spec/plan/code/UI acceptance.

### What remains underspecified

- Evaluator -> Developer phase findings return path.
- Evaluator phase review pass/fail criteria.
- Evaluator final acceptance criteria.
- Evaluator read-only execution/test/browser tool profile.
- Evaluator artifact visibility and private/public split.
- Evaluator/HE `coordinate_qa` protocol.
- Architectural conformance test catalog.

### Evaluator tickets

#### EVAL-001 — Critical — Add Evaluator-to-Developer phase review return path

**Decision:** Define the concrete handoff response from Evaluator to Developer after `submit_phase_to_evaluator`.

**Acceptance criteria:**

- Evaluator can return pass/fail findings to Developer.
- Findings cite spec/plan/test/UI evidence.
- Rejection gives actionable but not over-prescriptive remediation.
- Acceptance can advance Developer to the next phase or final readiness path.

#### EVAL-002 — High — Specify Evaluator acceptance criteria and evidence artifacts

**Decision:** Define when `submit_application_acceptance(accepted=True)` is allowed.

**Acceptance criteria:**

- Acceptance covers spec compliance, plan completion, naming/SDK conventions, tests, UI/UX/TUI behavior, security constraints, and artifact completeness.
- Rejection records deficiencies and evidence.
- Acceptance stamp artifacts are registered and visible to PM.

#### EVAL-003 — High — Specify Evaluator tool and permission profile

**Decision:** Define Evaluator's read-only code/test/browser/tool permissions.

**Recommended direction:** Evaluator can run tests, inspect diffs, use browser/UI verification, and read artifacts, but cannot modify code or design.

**Acceptance criteria:**

- Write/edit tools are absent or approval-blocked.
- Test/browser execution is allowed in sandbox.
- Evaluator cannot see HE-private eval internals unless coordination explicitly requires an HE-private review.

#### EVAL-004 — Medium/High — Specify `coordinate_qa` protocol with HE

**Decision:** Define what HE/Evaluator may coordinate and what remains private.

**Acceptance criteria:**

- Coordination aligns review strategy without collapsing role boundaries.
- Evaluator does not take over eval science.
- HE does not take over application acceptance.
- Developer-safe output remains redacted.

#### EVAL-005 — Medium/High — Specify architectural conformance test catalog

**Decision:** Define structural tests Evaluator must run or inspect.

**Acceptance criteria:**

- Tests cover mounted subgraph topology, no `.ainvoke()` role calls from dispatcher, final-turn guard, gate source-of-truth, role toolset subsets, Developer privacy, Project Records Layer writes, and artifact registration.
- Each AD non-negotiable has at least one behavioral or architectural test.

## Recommended derived spec map

Do not create these as authoritative specs until AD decisions land. The cleanest spec extraction plan is:

1. **`docs/specs/agent-harness-contracts.md`**
   - One consolidated role harness spec.
   - Tables for model, tools, middleware, skills, memory, permissions, subagents, artifacts, traces, and tests per role.

2. **`docs/specs/specialist-loop-response-contracts.md`** or expansion of `handoff-tools.md`
   - Owns reciprocal loop semantics for question, consultation, phase review, EBDR feedback, and QA coordination.
   - If response tools are small, expand existing handoff specs instead of creating a new file.

3. **`docs/specs/pm-session-project-awareness.md`** or expansion of `pcg-server-contract.md` + `project-data-contracts.md`
   - Owns PM session active-project summary, Project Records Layer read tools, project memory projection, and live snapshot UX.
   - If this remains tightly coupled to existing contracts, expand those specs rather than creating a new file.

4. **`docs/specs/developer-optimization-loop.md`** or expansion of the agent harness spec
   - Owns candidate snapshots, Developer-safe feedback, trace routing, experience store, and phase iteration state.

5. **`docs/specs/role-artifact-contracts.md`** or section inside agent harness spec
   - Owns artifact kinds, visibility, and registration obligations per role.

Recommended first move: create **one** `agent-harness-contracts.md` after the core AD decisions land, and only split it when concrete pressure appears.

## Decision order

Recommended order for the next workstream:

1. Close `T-HARNESS-001`: reciprocal loop response paths.
2. Close `T-HARNESS-002`: PM session project awareness.
3. Close `T-HARNESS-003`: one agent harness contract spec skeleton.
4. Close `T-HARNESS-009`: role artifact obligations.
5. Close Developer/HE/Evaluator loop tickets: `HE-001`, `DEV-001`, `EVAL-001`.
6. Close Planner/Researcher/PM response tickets: `PLAN-001`, `RES-001`, `PM-003`.
7. Close model/provider, permissions, memory/skills, and stagnation middleware.
8. Clean stale deferral/security/deployment wording.

## Principles that drove this audit

### Product-anchor preservation

The harness decisions must preserve:

- PM as primary POC.
- HE as evaluation science owner.
- Developer as optimizer blind to private eval artifacts.
- Evaluator as application acceptance gatekeeper.
- Visible artifacts and analytics over trace archaeology.
- Same lifecycle across headless surfaces.

### Loop completeness

Every promised loop must have:

- A request tool.
- A response tool.
- A durable artifact or record.
- A failure/rejection path.
- A testable state transition.

If a loop is only described in prose but not representable by tools, the harness is underspecified.

### Layer ownership

- LangGraph owns routing/checkpointing/`Command.PARENT` mechanics.
- Deep Agents owns the agent loop, base filesystem/todos/subagent/skills machinery, and compile-time schema filtering.
- Meta Harness owns handoff semantics, terminal-exit discipline, role boundaries, artifact contracts, visibility policy, and product-record operations.

### Explicit tools over hidden router intelligence

The current architecture intentionally favors concrete model-visible tools with fixed ownership and fixed target semantics. When in doubt, add explicit reciprocal tools rather than making the dispatcher infer social intent.

### Skills before tools

Procedural expertise should usually be a skill, not a product tool. HE LangSmith/OpenEvals work is the canonical example. Add explicit tools only when the workflow is repeated, high-friction, backend-owned, and product-critical.

### Trace-aware harness engineering

A coding/optimizer agent improves materially when it can inspect trace evidence. However, trace access must respect role visibility:

- HE gets private forensic depth.
- Developer gets allowed trace/evidence routing and score deltas, not hidden evaluator logic.
- PM/stakeholders get product analytics and artifact evidence, with LangSmith as link-out.

### Architectural conformance tests

For every non-negotiable harness decision, create at least one test that fails if the decision is silently reversed. Examples:

- Dispatcher never invokes role graphs directly.
- Every role includes final-turn guard.
- Developer lacks private eval artifact access.
- Role toolsets contain only allowed tools.
- Evaluator cannot write code.
- HE analytics publication cannot bypass validation.
- Every documented loop has request and response tools.

## Memory/principle sources that informed this pass

Relevant durable memories and principles:

- **Meta Harness current architecture invariants** — seven peer Deep Agents, one-node `dispatch_handoff`, Project Records Layer, Developer-safe boundaries.
- **AD-to-spec governance** — decisions originate in AD, flow into specs, specs cannot introduce decisions.
- **Governance layers** — local-docs are operating memory; docs/specs are shipped implementation contracts.
- **Mount-as-subgraph topology** — project roles must be mounted subgraphs, not `SubAgentMiddleware` workers.
- **Layer ownership decision tree** — do not duplicate SDK-owned enforcement; focus Meta Harness decisions on handoff semantics, role boundaries, product records, and visibility.
- **Trace-aware coding agents** — trace evidence should be a core optimization capability, with role-safe access.
- **HE/Evaluator/Developer separation** — HE owns harness/eval science, Evaluator owns application QA, Developer optimizes without hidden eval artifacts.
- **Architectural conformance tests** — behavioral tests alone are insufficient for harness architecture.

## Final note

The next best engineering move is not to implement role factories yet. The next best move is to close the loop-completeness gaps, especially `T-HARNESS-001`, because the current handoff catalog cannot execute several role interactions that the product story and AD explicitly promise.
