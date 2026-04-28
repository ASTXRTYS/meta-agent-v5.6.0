---
ticket_id: EVAL-002
title: "Specify Evaluator acceptance criteria and evidence artifacts"
status: proposed
priority: high
role: evaluator
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-009", "T-HARNESS-004", "EVAL-001", "PLAN-002"]
blocks: []
same_owner_with: ["HE-006", "DEV-002", "T-HARNESS-009"]
execution_mode: decision_cluster
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# EVAL-002 — Specify Evaluator acceptance criteria and evidence artifacts

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Evaluator acceptance stamp needs concrete application-quality criteria and evidence artifacts.

## Decision To Make

Define when submit_application_acceptance(accepted=True) is allowed.

## Dependencies

- `T-HARNESS-009`
- `T-HARNESS-004`
- `EVAL-001`
- `PLAN-002`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `HE-006`
- `DEV-002`
- `T-HARNESS-009`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Acceptance covers spec compliance, plan completion, naming/SDK conventions, tests, UI/UX/TUI behavior, security constraints, and artifact completeness.
- [ ] Rejection records deficiencies and evidence.
- [ ] Acceptance stamp artifacts are registered and visible to PM.

## Docs To Update Or Create

- `docs/specs/approval-and-gate-contracts.md`
- `docs/specs/agent-harness-contracts.md`

## Source References

- `Vision.md:20-42`
- `README.md:35-159`
- `meta_harness/AD.md:115-231`
- `meta_harness/AD.md:915-960`
- `meta_harness/docs/specs/handoff-tools.md:85-254`
- `meta_harness/docs/specs/handoff-tool-definitions.md:223-326`
- `meta_harness/local-docs/agent-harness-decision-audit.md`

## Closure Checklist

- [ ] AD decision updated or explicit decision recorded in the correct parent AD section.
- [ ] Derived spec updated or created if implementation details are affected.
- [ ] This ticket's downstream blockers reviewed for dependency changes.
- [ ] Conformance tests identified for any non-negotiable architecture or role-boundary decision.
- [ ] Ticket status updated in frontmatter and `ticket/README.md` if execution order changes.
