---
ticket_id: PLAN-001
title: "Add HE/Evaluator gate-consultation response path to Planner"
status: proposed
priority: critical
role: planner
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001"]
blocks: ["PLAN-004"]
same_owner_with: ["T-HARNESS-001", "PLAN-004"]
execution_mode: decision_cluster
decision_cluster: planner-phase-contracts
decision_owner: Jason
normative: false
---

# PLAN-001 — Add HE/Evaluator gate-consultation response path to Planner

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Planner can consult HE/Evaluator, but there is no concrete response path back to Planner.

## Decision To Make

Define how HE and Evaluator return gate recommendations to Planner.

## Dependencies

- `T-HARNESS-001`

## Blocks

- `PLAN-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `planner-phase-contracts`

Recommended same-owner follow-up:

- `T-HARNESS-001`
- `PLAN-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Planner receives HE eval gate recommendations.
- [ ] Planner receives Evaluator application-quality gate recommendations.
- [ ] Plan records which recommendations were incorporated.

## Docs To Update Or Create

- `docs/specs/handoff-tools.md`
- `docs/specs/handoff-tool-definitions.md`
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
