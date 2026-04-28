---
ticket_id: PLAN-005
title: "Specify risk and rollback planning obligations"
status: proposed
priority: medium
role: planner
execution_phase: phase-4-role-contracts
depends_on: ["PLAN-002"]
blocks: []
same_owner_with: ["PLAN-002"]
execution_mode: decision_cluster
decision_cluster: planner-phase-contracts
decision_owner: Jason
normative: false
---

# PLAN-005 — Specify risk and rollback planning obligations

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Planner should produce plans that are safe to execute and evaluate, not just ordered task lists.

## Decision To Make

Define how Planner captures sequencing risk, migration risk, rollback, and test checkpoints.

## Dependencies

- `PLAN-002`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `planner-phase-contracts`

Recommended same-owner follow-up:

- `PLAN-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer receives actionable rollback/test strategy.
- [ ] Evaluator can fail missing risk controls when relevant.

## Docs To Update Or Create

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
