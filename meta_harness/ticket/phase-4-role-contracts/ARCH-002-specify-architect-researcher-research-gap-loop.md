---
ticket_id: ARCH-002
title: "Specify Architect/Researcher research-gap loop"
status: proposed
priority: high
role: architect
execution_phase: phase-4-role-contracts
depends_on: ["RES-001", "T-HARNESS-001"]
blocks: []
same_owner_with: ["RES-001"]
execution_mode: decision_cluster
decision_cluster: research-architect-loop
decision_owner: Jason
normative: false
---

# ARCH-002 — Specify Architect/Researcher research-gap loop

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Architect can request research, but the return/resume semantics are not yet closed.

## Decision To Make

Define how Architect requests targeted research and resumes after Researcher returns findings.

## Dependencies

- `RES-001`
- `T-HARNESS-001`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `research-architect-loop`

Recommended same-owner follow-up:

- `RES-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Request includes exact knowledge gap, blocked decision, required evidence, and priority.
- [ ] Researcher returns directly to Architect.
- [ ] Architect records how research changed or did not change the design.

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
