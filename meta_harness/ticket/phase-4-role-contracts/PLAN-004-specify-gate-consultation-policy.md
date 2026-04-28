---
ticket_id: PLAN-004
title: "Specify gate consultation policy"
status: proposed
priority: medium_high
role: planner
execution_phase: phase-4-role-contracts
depends_on: ["PLAN-001", "T-HARNESS-004", "ARCH-004"]
blocks: []
same_owner_with: ["PLAN-001", "ARCH-004"]
execution_mode: decision_cluster
decision_cluster: planner-phase-contracts
decision_owner: Jason
normative: false
---

# PLAN-004 — Specify gate consultation policy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Consultation is modeled but not policy-bound; high-risk projects may require explicit QA gate advice.

## Decision To Make

Decide when Planner must consult HE/Evaluator.

## Dependencies

- `PLAN-001`
- `T-HARNESS-004`
- `ARCH-004`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `planner-phase-contracts`

Recommended same-owner follow-up:

- `PLAN-001`
- `ARCH-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] High-risk/eval-heavy projects require HE gate consultation.
- [ ] UI-heavy/application-conformance-heavy projects require Evaluator consultation.
- [ ] Planner prompt and conformance tests enforce the policy.

## Docs To Update Or Create

- `docs/specs/handoff-tools.md`
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
