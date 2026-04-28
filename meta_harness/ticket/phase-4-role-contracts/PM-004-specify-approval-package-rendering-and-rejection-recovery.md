---
ticket_id: PM-004
title: "Specify approval package rendering and rejection recovery"
status: proposed
priority: medium_high
role: project_manager
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-004"]
blocks: []
same_owner_with: ["T-HARNESS-004"]
execution_mode: decision_cluster
decision_cluster: protocol-loop-architect
decision_owner: Jason
normative: false
---

# PM-004 — Specify approval package rendering and rejection recovery

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

request_approval requires a concrete package format and recovery path after rejection.

## Decision To Make

Define exact approval package artifact shape for scoping->research and architecture->planning.

## Dependencies

- `T-HARNESS-004`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `protocol-loop-architect`

Recommended same-owner follow-up:

- `T-HARNESS-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Package includes artifact refs, summary, risks, user-facing decision question, and approval type.
- [ ] Rejection path returns PM to the right revision activity.
- [ ] Autonomous mode records approval without user prompt but preserves auditability.

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
