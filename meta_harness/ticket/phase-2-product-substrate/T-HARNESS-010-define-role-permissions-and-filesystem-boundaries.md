---
ticket_id: T-HARNESS-010
title: "Define role permissions and filesystem boundaries"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-009"]
blocks: ["DEV-003", "EVAL-003", "HE-003", "HE-004", "T-HARNESS-003", "T-HARNESS-008", "DEV-005", "T-HARNESS-011", "DEV-002", "EVAL-005", "T-HARNESS-012"]
same_owner_with: ["T-HARNESS-009", "HE-004"]
execution_mode: isolated_security_review
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# T-HARNESS-010 — Define role permissions and filesystem boundaries

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

The workspace tree exists, but role-specific permissions and private-artifact boundaries are not locked.

## Decision To Make

Define read/write roots for every role and every execution mode.

## Dependencies

- `T-HARNESS-009`

## Blocks

- `DEV-003`
- `EVAL-003`
- `HE-003`
- `HE-004`
- `T-HARNESS-003`
- `T-HARNESS-008`
- `DEV-005`
- `T-HARNESS-011`
- `DEV-002`
- `EVAL-005`
- `T-HARNESS-012`

## Assignment Continuity Guidance

**Execution mode:** `isolated_security_review`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `T-HARNESS-009`
- `HE-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer cannot read HE held-out datasets, rubrics, or judge prompts.
- [ ] Evaluator can inspect code/tests without modifying implementation.
- [ ] HE can read eval evidence and publish analytics but cannot bypass visibility policy.
- [ ] PM reads project artifacts and snapshots through brokered operations.
- [ ] Local workspace mode has stricter write/shell approvals.

## Docs To Update Or Create

- `docs/specs/repo-and-workspace-layout.md`
- `docs/specs/project-data-contracts.md`
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
