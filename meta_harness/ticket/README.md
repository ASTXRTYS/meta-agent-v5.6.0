# Meta Harness Ticket Backlog

## Purpose

This folder contains standalone planning tickets extracted from `local-docs/agent-harness-decision-audit.md`.

These files are **not normative architecture** and are **not implementation specs**. They are execution packets for deciding, specifying, and then implementing the remaining Meta Harness agent-harness surface area.

Accepted ticket decisions must be promoted into:

1. `AD.md` for architectural decisions.
2. `docs/specs/` for implementation contracts.
3. Code/tests only after the relevant AD/spec changes land.

## Required Execution Rule

A ticket cannot be implemented until every `depends_on` ticket is closed or explicitly waived by Jason in the ticket file.

If a ticket changes architecture, runtime policy, role behavior, tool visibility, artifact visibility, permissions, or evaluation analytics, it must update at least one of:

- `AD.md`
- the relevant `docs/specs/` contract
- this folder's dependency/index metadata

## Status Lifecycle

Use the `status` field in each ticket frontmatter:

```txt
proposed -> ad_decision_needed -> spec_needed -> ready_for_implementation -> in_progress -> done
```

Optional terminal statuses:

```txt
blocked | superseded | rejected
```

## Dependency-First Execution Phases

1. **Phase 1 — protocol blockers:** close reciprocal loop and gate/HITL decisions.
2. **Phase 2 — product substrate:** close PM session, Project Records Layer, artifact, analytics, and permission decisions.
3. **Phase 3 — harness substrate:** close shared agent harness spec, provider tooling, middleware, memory, skills, and execution profiles.
4. **Phase 4 — role contracts:** close per-role harness tickets in lifecycle order.
5. **Phase 5 — cleanup:** clean stale deferral/security/deployment wording after the real decisions land.

## Assignment Continuity vs Isolated Review

Use `execution_mode` and `decision_cluster` in ticket frontmatter.

- **`decision_cluster`** — best handled by the same agent because the tickets share one conceptual decision surface.
- **`isolated_*_review`** — best handled by a focused agent or reviewer because it is security-sensitive, SDK-sensitive, or architecture-sensitive.
- **`hybrid_*_review`** — cluster owner drafts; isolated reviewer approves before downstream consumption.

## Decision-Continuity Clusters

- **`agent-harness-spec-architect`** — `T-HARNESS-003`
- **`artifact-visibility-contracts`** — `T-HARNESS-009`, `T-HARNESS-010`, `HE-004`, `HE-006`, `ARCH-004`, `EVAL-002`
- **`conformance-tests`** — `EVAL-005`
- **`dev-he-eval-loop`** — `HE-001`, `DEV-001`, `DEV-002`, `DEV-006`, `EVAL-001`, `EVAL-004`
- **`developer-hitl-routing`** — `T-HARNESS-007`, `ARCH-003`, `DEV-004`
- **`docs-cleanup`** — `T-HARNESS-012`
- **`execution-permissions`** — `DEV-003`, `DEV-005`, `EVAL-003`
- **`he-analytics-workbench`** — `T-HARNESS-008`, `HE-002`, `HE-003`, `HE-005`
- **`memory-skills-substrate`** — `T-HARNESS-011`
- **`middleware-specialist`** — `T-HARNESS-006`
- **`planner-phase-contracts`** — `PLAN-001`, `PLAN-002`, `PLAN-003`, `PLAN-004`, `PLAN-005`
- **`pm-session-substrate`** — `T-HARNESS-002`, `PM-001`, `PM-002`, `PM-005`
- **`protocol-loop-architect`** — `T-HARNESS-001`, `T-HARNESS-004`, `PM-003`, `PM-004`
- **`provider-tooling-specialist`** — `T-HARNESS-005`
- **`research-architect-loop`** — `RES-001`, `RES-002`, `RES-003`, `RES-004`, `ARCH-001`, `ARCH-002`, `ARCH-005`

## Ticket Index

The index is dependency-first reading order, not the full scheduler. Within a
phase, `depends_on` is authoritative. Tickets with closed dependencies may be
executed in parallel unless they share a `decision_cluster` or `same_owner_with`
relationship that calls for assignment continuity.

Use the fields this way:

1. Start with the first unclosed ticket whose `depends_on` list is empty or
already closed.
2. Check its `blocks` list to understand the direct downstream tickets that list it in `depends_on`.
3. Keep tickets in the same `decision_cluster` with the same owner when the
decision surface should stay coherent.
4. Use `same_owner_with` as the local handoff hint for the current ticket; it is
not a complete replacement for the cluster map above.

### `phase-1-protocol` — Protocol blockers and reciprocal loop completion

- [T-HARNESS-001 — Add reciprocal response paths for specialist loops](phase-1-protocol/T-HARNESS-001-add-reciprocal-response-paths-for-specialist-loops.md) — **critical**, `decision_cluster`, cluster `protocol-loop-architect`
- [T-HARNESS-004 — Promote or block approval-and-gate-contracts.md](phase-1-protocol/T-HARNESS-004-promote-or-block-approval-and-gate-contracts.md) — **high**, `decision_cluster`, cluster `protocol-loop-architect`
- [T-HARNESS-007 — Resolve Developer HITL ownership](phase-1-protocol/T-HARNESS-007-resolve-developer-hitl-ownership.md) — **high**, `decision_cluster`, cluster `developer-hitl-routing`
- [PM-003 — Specify PM answer-to-specialist response tools](phase-1-protocol/PM-003-specify-pm-answer-to-specialist-response-tools.md) — **high**, `decision_cluster`, cluster `protocol-loop-architect`
- [HE-001 — Add HE-to-Developer EBDR feedback path](phase-1-protocol/HE-001-add-he-to-developer-ebdr-feedback-path.md) — **critical**, `decision_cluster`, cluster `dev-he-eval-loop`
- [RES-001 — Add Researcher response path to consultation requester](phase-1-protocol/RES-001-add-researcher-response-path-to-consultation-requester.md) — **critical**, `decision_cluster`, cluster `research-architect-loop`
- [PLAN-001 — Add HE/Evaluator gate-consultation response path to Planner](phase-1-protocol/PLAN-001-add-he-evaluator-gate-consultation-response-path-to-planner.md) — **critical**, `decision_cluster`, cluster `planner-phase-contracts`
- [EVAL-001 — Add Evaluator-to-Developer phase review return path](phase-1-protocol/EVAL-001-add-evaluator-to-developer-phase-review-return-path.md) — **critical**, `decision_cluster`, cluster `dev-he-eval-loop`

### `phase-2-product-substrate` — PM session, project records, artifacts, analytics, and permissions

- [T-HARNESS-002 — Resolve PM-session project awareness and live monitoring](phase-2-product-substrate/T-HARNESS-002-resolve-pm-session-project-awareness-and-live-monitoring.md) — **high**, `decision_cluster`, cluster `pm-session-substrate`
- [T-HARNESS-008 — Finalize HE analytics product tools](phase-2-product-substrate/T-HARNESS-008-finalize-he-analytics-product-tools.md) — **high**, `hybrid_security_review`, cluster `he-analytics-workbench`
- [T-HARNESS-009 — Define artifact publication obligations per role](phase-2-product-substrate/T-HARNESS-009-define-artifact-publication-obligations-per-role.md) — **high**, `decision_cluster`, cluster `artifact-visibility-contracts`
- [T-HARNESS-010 — Define role permissions and filesystem boundaries](phase-2-product-substrate/T-HARNESS-010-define-role-permissions-and-filesystem-boundaries.md) — **high**, `isolated_security_review`, cluster `artifact-visibility-contracts`
- [PM-001 — Specify PM dual-mode harness contract](phase-2-product-substrate/PM-001-specify-pm-dual-mode-harness-contract.md) — **high**, `decision_cluster`, cluster `pm-session-substrate`
- [PM-002 — Specify PM project creation and spawn primitive](phase-2-product-substrate/PM-002-specify-pm-project-creation-and-spawn-primitive.md) — **high**, `decision_cluster`, cluster `pm-session-substrate`
- [PM-005 — Specify PM stakeholder decision record artifacts](phase-2-product-substrate/PM-005-specify-pm-stakeholder-decision-record-artifacts.md) — **medium**, `decision_cluster`, cluster `pm-session-substrate`
- [HE-002 — Specify HE analytics tools](phase-2-product-substrate/HE-002-specify-he-analytics-tools.md) — **high**, `hybrid_security_review`, cluster `he-analytics-workbench`
- [HE-004 — Specify HE private/public artifact taxonomy](phase-2-product-substrate/HE-004-specify-he-private-public-artifact-taxonomy.md) — **high**, `hybrid_security_review`, cluster `artifact-visibility-contracts`

### `phase-3-harness-substrate` — Shared harness substrate: specs, providers, middleware, memory, skills, tools

- [T-HARNESS-003 — Create a first-class agent harness contract spec](phase-3-harness-substrate/T-HARNESS-003-create-a-first-class-agent-harness-contract-spec.md) — **high**, `decision_cluster`, cluster `agent-harness-spec-architect`
- [T-HARNESS-005 — Finalize role-specific provider and server-side tool policy](phase-3-harness-substrate/T-HARNESS-005-finalize-role-specific-provider-and-server-side-tool-policy.md) — **high**, `isolated_sdk_review`, cluster `provider-tooling-specialist`
- [T-HARNESS-006 — Convert StagnationGuardMiddleware into a buildable role contract](phase-3-harness-substrate/T-HARNESS-006-convert-stagnationguardmiddleware-into-a-buildable-role-contract.md) — **high**, `isolated_sdk_review`, cluster `middleware-specialist`
- [T-HARNESS-011 — Define role memory and skill loading strategy](phase-3-harness-substrate/T-HARNESS-011-define-role-memory-and-skill-loading-strategy.md) — **high**, `decision_cluster`, cluster `memory-skills-substrate`
- [HE-003 — Specify HE Evidence Workbench harness profile](phase-3-harness-substrate/HE-003-specify-he-evidence-workbench-harness-profile.md) — **high**, `decision_cluster`, cluster `he-analytics-workbench`
- [HE-005 — Specify HE internal analysis subagents](phase-3-harness-substrate/HE-005-specify-he-internal-analysis-subagents.md) — **medium_high**, `decision_cluster`, cluster `he-analytics-workbench`
- [RES-003 — Specify Researcher web tool policy](phase-3-harness-substrate/RES-003-specify-researcher-web-tool-policy.md) — **medium_high**, `decision_cluster`, cluster `research-architect-loop`
- [RES-004 — Specify Researcher memory and skills policy](phase-3-harness-substrate/RES-004-specify-researcher-memory-and-skills-policy.md) — **medium**, `decision_cluster`, cluster `research-architect-loop`
- [DEV-003 — Specify Developer execution tool and permission profile](phase-3-harness-substrate/DEV-003-specify-developer-execution-tool-and-permission-profile.md) — **high**, `isolated_security_review`, cluster `execution-permissions`
- [DEV-005 — Specify Developer subagent policy](phase-3-harness-substrate/DEV-005-specify-developer-subagent-policy.md) — **medium_high**, `decision_cluster`, cluster `execution-permissions`
- [EVAL-003 — Specify Evaluator tool and permission profile](phase-3-harness-substrate/EVAL-003-specify-evaluator-tool-and-permission-profile.md) — **high**, `isolated_security_review`, cluster `execution-permissions`

### `phase-4-role-contracts` — Per-role harness contracts and artifact/evaluation details

- [PM-004 — Specify approval package rendering and rejection recovery](phase-4-role-contracts/PM-004-specify-approval-package-rendering-and-rejection-recovery.md) — **medium_high**, `decision_cluster`, cluster `protocol-loop-architect`
- [HE-006 — Specify HE harness acceptance criteria](phase-4-role-contracts/HE-006-specify-he-harness-acceptance-criteria.md) — **medium**, `decision_cluster`, cluster `artifact-visibility-contracts`
- [RES-002 — Specify research bundle artifact schema](phase-4-role-contracts/RES-002-specify-research-bundle-artifact-schema.md) — **high**, `decision_cluster`, cluster `research-architect-loop`
- [ARCH-001 — Specify design package artifact schema](phase-4-role-contracts/ARCH-001-specify-design-package-artifact-schema.md) — **high**, `decision_cluster`, cluster `research-architect-loop`
- [ARCH-002 — Specify Architect/Researcher research-gap loop](phase-4-role-contracts/ARCH-002-specify-architect-researcher-research-gap-loop.md) — **high**, `decision_cluster`, cluster `research-architect-loop`
- [ARCH-003 — Specify Architect interactive spec HITL](phase-4-role-contracts/ARCH-003-specify-architect-interactive-spec-hitl.md) — **medium_high**, `hybrid_pm_review`, cluster `developer-hitl-routing`
- [ARCH-004 — Specify HE evalability review integration](phase-4-role-contracts/ARCH-004-specify-he-evalability-review-integration.md) — **medium_high**, `decision_cluster`, cluster `artifact-visibility-contracts`
- [ARCH-005 — Specify prompt/tool contract artifact conventions](phase-4-role-contracts/ARCH-005-specify-prompt-tool-contract-artifact-conventions.md) — **medium**, `decision_cluster`, cluster `research-architect-loop`
- [PLAN-002 — Specify implementation plan artifact schema](phase-4-role-contracts/PLAN-002-specify-implementation-plan-artifact-schema.md) — **high**, `decision_cluster`, cluster `planner-phase-contracts`
- [PLAN-003 — Specify plan_phase_id contract](phase-4-role-contracts/PLAN-003-specify-plan-phase-id-contract.md) — **high**, `decision_cluster`, cluster `planner-phase-contracts`
- [PLAN-004 — Specify gate consultation policy](phase-4-role-contracts/PLAN-004-specify-gate-consultation-policy.md) — **medium_high**, `decision_cluster`, cluster `planner-phase-contracts`
- [PLAN-005 — Specify risk and rollback planning obligations](phase-4-role-contracts/PLAN-005-specify-risk-and-rollback-planning-obligations.md) — **medium**, `decision_cluster`, cluster `planner-phase-contracts`
- [DEV-001 — Specify Developer phase-feedback loop](phase-4-role-contracts/DEV-001-specify-developer-phase-feedback-loop.md) — **critical**, `decision_cluster`, cluster `dev-he-eval-loop`
- [DEV-002 — Specify Developer optimization experience store](phase-4-role-contracts/DEV-002-specify-developer-optimization-experience-store.md) — **high**, `hybrid_security_review`, cluster `dev-he-eval-loop`
- [DEV-004 — Resolve Developer HITL through PM relay](phase-4-role-contracts/DEV-004-resolve-developer-hitl-through-pm-relay.md) — **high**, `decision_cluster`, cluster `developer-hitl-routing`
- [DEV-006 — Specify Developer routing decision prompt contract](phase-4-role-contracts/DEV-006-specify-developer-routing-decision-prompt-contract.md) — **medium_high**, `decision_cluster`, cluster `dev-he-eval-loop`
- [EVAL-002 — Specify Evaluator acceptance criteria and evidence artifacts](phase-4-role-contracts/EVAL-002-specify-evaluator-acceptance-criteria-and-evidence-artifacts.md) — **high**, `decision_cluster`, cluster `artifact-visibility-contracts`
- [EVAL-004 — Specify coordinate_qa protocol with HE](phase-4-role-contracts/EVAL-004-specify-coordinate-qa-protocol-with-he.md) — **medium_high**, `decision_cluster`, cluster `dev-he-eval-loop`
- [EVAL-005 — Specify architectural conformance test catalog](phase-4-role-contracts/EVAL-005-specify-architectural-conformance-test-catalog.md) — **medium_high**, `isolated_architecture_review`, cluster `conformance-tests`

### `phase-5-cleanup` — Documentation cleanup and stale deferral removal

- [T-HARNESS-012 — Clean stale deferral, security, and deployment language](phase-5-cleanup/T-HARNESS-012-clean-stale-deferral-security-and-deployment-language.md) — **medium**, `isolated_doc_cleanup`, cluster `docs-cleanup`


## Review Rules

- Do not close a ticket by only editing the ticket file.
- Do not implement code from a ticket whose accepted decision is absent from `AD.md` or the appropriate spec.
- Do not split a coherent decision cluster across agents unless the split is explicitly for review.
- Do isolate security/privacy/provider/tooling review when `execution_mode` requests it.
- When dependency order changes, update both the ticket frontmatter and this README.
