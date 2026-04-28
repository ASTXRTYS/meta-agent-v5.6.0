---
ticket_id: T-HARNESS-011
title: "Define role memory and skill loading strategy"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-003", "T-HARNESS-010"]
blocks: ["HE-003", "HE-005", "RES-004", "DEV-005", "role_factory_implementation"]
same_owner_with: ["T-HARNESS-003"]
execution_mode: decision_cluster
decision_cluster: memory-skills-substrate
decision_owner: Jason
normative: false
---

# T-HARNESS-011 — Define role memory and skill loading strategy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Docs say memory through files and skills via directories, but role-specific loading and isolation policy is incomplete.

## Decision To Make

Define role memory and skills directories, loading rules, and allowed learning behavior.

## Dependencies

- `T-HARNESS-003`
- `T-HARNESS-010`

## Blocks

- `HE-003`
- `HE-005`
- `RES-004`
- `DEV-005`
- `role_factory_implementation`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `memory-skills-substrate`

Recommended same-owner follow-up:

- `T-HARNESS-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Every role factory points to correct prompt, memory, and skills path.
- [ ] Memory-reading order is specified per role.
- [ ] Private eval memories never leak into Developer-visible memory.
- [ ] HE LangSmith/OpenEvals workflows are skills by default unless explicit-tool criteria are met.

## Docs To Update Or Create

- `AGENTS.md`
- `docs/specs/repo-and-workspace-layout.md`
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
