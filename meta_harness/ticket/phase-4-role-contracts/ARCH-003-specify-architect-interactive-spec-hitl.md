---
ticket_id: ARCH-003
title: "Specify Architect interactive spec HITL"
status: proposed
priority: medium_high
role: architect
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-007"]
blocks: []
same_owner_with: ["PM-003", "T-HARNESS-007"]
execution_mode: hybrid_pm_review
decision_cluster: developer-hitl-routing
decision_owner: Jason
normative: false
---

# ARCH-003 — Specify Architect interactive spec HITL

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Architect has AskUserMiddleware, but scope/business changes should remain PM-owned.

## Decision To Make

Define when Architect may ask user directly versus ask PM.

## Dependencies

- `T-HARNESS-007`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `hybrid_pm_review`  
**Decision cluster:** `developer-hitl-routing`

Recommended same-owner follow-up:

- `PM-003`
- `T-HARNESS-007`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Direct user interaction only when interactive-spec mode is enabled.
- [ ] Scope/business changes route to PM.
- [ ] Interaction is traceable and represented in artifacts.

## Docs To Update Or Create

- `AD.md Q8/Q12`
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
