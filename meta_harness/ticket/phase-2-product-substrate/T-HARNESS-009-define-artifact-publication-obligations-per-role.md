---
ticket_id: T-HARNESS-009
title: "Define artifact publication obligations per role"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-2-product-substrate
depends_on: []
blocks: ["HE-004", "RES-002", "ARCH-001", "PLAN-002", "DEV-002", "EVAL-002", "T-HARNESS-003", "T-HARNESS-010", "PM-005", "T-HARNESS-008"]
same_owner_with: ["T-HARNESS-010", "HE-004", "EVAL-002", "DEV-002"]
execution_mode: decision_cluster
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# T-HARNESS-009 — Define artifact publication obligations per role

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Project Records Layer is specified, but each role’s artifact obligations are scattered as prose.

## Decision To Make

Define required artifact kinds, visibility, ownership, content refs, and registration timing per role.

## Dependencies

- None

## Blocks

- `HE-004`
- `RES-002`
- `ARCH-001`
- `PLAN-002`
- `DEV-002`
- `EVAL-002`
- `T-HARNESS-003`
- `T-HARNESS-010`
- `PM-005`
- `T-HARNESS-008`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `T-HARNESS-010`
- `HE-004`
- `EVAL-002`
- `DEV-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Each role has required artifact kinds, visibility policy, and registration timing.
- [ ] Artifact-producing tools cannot return success before registration succeeds or recoverable feedback is returned.
- [ ] Visibility labels preserve Developer-safe and stakeholder-visible boundaries.

## Docs To Update Or Create

- `docs/specs/project-data-contracts.md`
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
