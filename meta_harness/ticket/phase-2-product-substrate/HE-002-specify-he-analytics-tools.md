---
ticket_id: HE-002
title: "Specify HE analytics tools"
status: proposed
priority: high
role: harness_engineer
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-008"]
blocks: []
same_owner_with: ["T-HARNESS-008", "HE-003"]
execution_mode: hybrid_security_review
decision_cluster: he-analytics-workbench
decision_owner: Jason
normative: false
---

# HE-002 — Specify HE analytics tools

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

HE needs a model-visible path to publish/update/render analytics without direct database access.

## Decision To Make

Expose analytics operations as backend-owned HE tools or explicitly choose a different mechanism.

## Dependencies

- `T-HARNESS-008`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `hybrid_security_review`  
**Decision cluster:** `he-analytics-workbench`

Recommended same-owner follow-up:

- `T-HARNESS-008`
- `HE-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] HE can publish UI-renderable analytics.
- [ ] Backend validates schema and visibility.
- [ ] Developer-safe and stakeholder-visible policies remain distinct.

## Docs To Update Or Create

- `docs/specs/harness-engineer-evaluation-analytics.md`
- `docs/specs/project-data-contracts.md`

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
