---
ticket_id: HE-004
title: "Specify HE private/public artifact taxonomy"
status: proposed
priority: high
role: harness_engineer
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-009", "T-HARNESS-010"]
blocks: ["HE-006", "DEV-002", "ARCH-004"]
same_owner_with: ["T-HARNESS-009", "T-HARNESS-010", "HE-006", "ARCH-004"]
execution_mode: hybrid_security_review
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# HE-004 — Specify HE private/public artifact taxonomy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

HE owns artifacts with different visibility classes; Developer-safe, stakeholder-visible, HE-private, and internal boundaries must be explicit.

## Decision To Make

Define artifact kinds and visibility for HE evaluation science outputs.

## Dependencies

- `T-HARNESS-009`
- `T-HARNESS-010`

## Blocks

- `HE-006`
- `DEV-002`
- `ARCH-004`

## Assignment Continuity Guidance

**Execution mode:** `hybrid_security_review`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `T-HARNESS-009`
- `T-HARNESS-010`
- `HE-006`
- `ARCH-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer-visible package excludes private eval internals.
- [ ] PM/internal surfaces can inspect summaries.
- [ ] Stakeholder-visible promotion is PM-owned.

## Docs To Update Or Create

- `docs/specs/project-data-contracts.md`
- `docs/specs/harness-engineer-evaluation-analytics.md`
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
