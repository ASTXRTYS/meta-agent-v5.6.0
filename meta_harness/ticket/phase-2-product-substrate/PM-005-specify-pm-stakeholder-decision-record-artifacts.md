---
ticket_id: PM-005
title: "Specify PM stakeholder decision record artifacts"
status: proposed
priority: medium
role: project_manager
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-002", "T-HARNESS-009", "PM-001"]
blocks: []
same_owner_with: ["PM-001", "PM-002", "T-HARNESS-002"]
execution_mode: decision_cluster
decision_cluster: pm-session-substrate
decision_owner: Jason
normative: false
---

# PM-005 — Specify PM stakeholder decision record artifacts

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

PM decisions must become durable artifacts/events so specialists can act on them without relying on hidden conversation context.

## Decision To Make

Define durable records for user/stakeholder decisions, scope changes, and business-priority changes.

## Dependencies

- `T-HARNESS-002`
- `T-HARNESS-009`
- `PM-001`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `pm-session-substrate`

Recommended same-owner follow-up:

- `PM-001`
- `PM-002`
- `T-HARNESS-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Records are visible to PM and relevant project roles.
- [ ] Developer sees only safe/public consequences when needed.
- [ ] Project Records Layer has artifact kind and visibility policy.

## Docs To Update Or Create

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
