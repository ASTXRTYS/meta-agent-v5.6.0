---
ticket_id: EVAL-004
title: "Specify coordinate_qa protocol with HE"
status: proposed
priority: medium_high
role: evaluator
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-001", "HE-001", "HE-006"]
blocks: []
same_owner_with: ["HE-006", "EVAL-002", "HE-001"]
execution_mode: decision_cluster
decision_cluster: dev-he-eval-loop
decision_owner: Jason
normative: false
---

# EVAL-004 — Specify coordinate_qa protocol with HE

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

coordinate_qa should align review strategy without collapsing HE and Evaluator authority boundaries.

## Decision To Make

Define what HE/Evaluator may coordinate and what remains private.

## Dependencies

- `T-HARNESS-001`
- `HE-001`
- `HE-006`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `dev-he-eval-loop`

Recommended same-owner follow-up:

- `HE-006`
- `EVAL-002`
- `HE-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Coordination aligns review strategy without collapsing role boundaries.
- [ ] Evaluator does not take over eval science.
- [ ] HE does not take over application acceptance.
- [ ] Developer-safe output remains redacted.

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
