---
ticket_id: PLAN-003
title: "Specify plan_phase_id contract"
status: proposed
priority: high
role: planner
execution_phase: phase-4-role-contracts
depends_on: ["PLAN-002"]
blocks: ["DEV-001"]
same_owner_with: ["PLAN-002"]
execution_mode: decision_cluster
decision_cluster: planner-phase-contracts
decision_owner: Jason
normative: false
---

# PLAN-003 — Specify plan_phase_id contract

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer phase tools use model-visible phase values that map to HandoffRecord.plan_phase_id; free-form ambiguity must be removed.

## Decision To Make

Define identifier format, uniqueness, versioning, and display-name policy.

## Dependencies

- `PLAN-002`

## Blocks

- `DEV-001`

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

- [ ] Developer phase tools use stable IDs, not ambiguous labels.
- [ ] Phase IDs survive plan revisions.
- [ ] Handoff records associate submissions with phase plan entries.

## Docs To Update Or Create

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
