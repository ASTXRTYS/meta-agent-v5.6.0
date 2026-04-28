---
ticket_id: DEV-004
title: "Resolve Developer HITL through PM relay"
status: proposed
priority: high
role: developer
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-007"]
blocks: ["DEV-006"]
same_owner_with: ["PM-003", "T-HARNESS-007"]
execution_mode: decision_cluster
decision_cluster: developer-hitl-routing
decision_owner: Jason
normative: false
---

# DEV-004 — Resolve Developer HITL through PM relay

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer should route stakeholder/scope questions through PM by default to preserve PM as POC.

## Decision To Make

Close OQ-1 by choosing PM relay unless a restricted direct Developer HITL mode is explicitly accepted.

## Dependencies

- `T-HARNESS-007`

## Blocks

- `DEV-006`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `developer-hitl-routing`

Recommended same-owner follow-up:

- `PM-003`
- `T-HARNESS-007`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer routes stakeholder/scope questions through PM by default.
- [ ] PM decides whether to ask user.
- [ ] Direct Developer HITL is rejected or gated behind explicit opt-in.

## Docs To Update Or Create

- `AD.md OQ-1`
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
