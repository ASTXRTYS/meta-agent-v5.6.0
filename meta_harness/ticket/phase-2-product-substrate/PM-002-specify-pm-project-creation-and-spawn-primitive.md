---
ticket_id: PM-002
title: "Specify PM project creation and spawn primitive"
status: proposed
priority: high
role: project_manager
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-002", "PM-001"]
blocks: []
same_owner_with: ["T-HARNESS-002", "PM-001"]
execution_mode: decision_cluster
decision_cluster: pm-session-substrate
decision_owner: Jason
normative: false
---

# PM-002 — Specify PM project creation and spawn primitive

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Project creation must bridge pm_session intake to project thread execution without merging checkpoint histories.

## Decision To Make

Define whether spawn_project is PM model-visible, backend-triggered by UI/headless ingress, or both.

## Dependencies

- `T-HARNESS-002`
- `PM-001`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `pm-session-substrate`

Recommended same-owner follow-up:

- `T-HARNESS-002`
- `PM-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Calls create_project_registry idempotently.
- [ ] Creates LangGraph project thread with correct metadata.
- [ ] Seeds initial state without copying PM-session checkpoint history.
- [ ] Records project data event and trace correlation.

## Docs To Update Or Create

- `docs/specs/pcg-server-contract.md`
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
