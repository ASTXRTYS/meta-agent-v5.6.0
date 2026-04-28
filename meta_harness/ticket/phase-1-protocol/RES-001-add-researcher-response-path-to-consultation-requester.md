---
ticket_id: RES-001
title: "Add Researcher response path to consultation requester"
status: proposed
priority: critical
role: researcher
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001"]
blocks: ["ARCH-002"]
same_owner_with: ["T-HARNESS-001", "ARCH-002"]
execution_mode: decision_cluster
decision_cluster: research-architect-loop
decision_owner: Jason
normative: false
---

# RES-001 — Add Researcher response path to consultation requester

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Researcher receives targeted consultation requests but only has return_research_bundle_to_pm.

## Decision To Make

Define how Researcher returns targeted findings to Architect, HE, or PM depending on requester.

## Dependencies

- `T-HARNESS-001`

## Blocks

- `ARCH-002`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `research-architect-loop`

Recommended same-owner follow-up:

- `T-HARNESS-001`
- `ARCH-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Architect research requests can return directly to Architect.
- [ ] HE research requests can return directly to HE.
- [ ] PM research requests can return to PM.
- [ ] Returned artifact preserves question, evidence, citations, uncertainty, and recommended next role.

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
