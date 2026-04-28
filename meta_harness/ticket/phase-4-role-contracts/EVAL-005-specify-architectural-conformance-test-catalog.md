---
ticket_id: EVAL-005
title: "Specify architectural conformance test catalog"
status: proposed
priority: medium_high
role: evaluator
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-003", "T-HARNESS-004", "T-HARNESS-010"]
blocks: []
same_owner_with: ["T-HARNESS-003"]
execution_mode: isolated_architecture_review
decision_cluster: conformance-tests
decision_owner: Jason
normative: false
---

# EVAL-005 — Specify architectural conformance test catalog

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Evaluator should enforce architecture commitments with structural tests, not only output checks.

## Decision To Make

Define structural tests Evaluator must run or inspect.

## Dependencies

- `T-HARNESS-003`
- `T-HARNESS-004`
- `T-HARNESS-010`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `isolated_architecture_review`  
**Decision cluster:** `conformance-tests`

Recommended same-owner follow-up:

- `T-HARNESS-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Tests cover mounted subgraph topology, no direct role invoke, final-turn guard, gate source-of-truth, role toolsets, Developer privacy, Project Records Layer writes, and artifact registration.
- [ ] Each AD non-negotiable has at least one behavioral or architectural test.

## Docs To Update Or Create

- `docs/specs/pcg-data-contracts.md`
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
