---
ticket_id: T-HARNESS-002
title: "Resolve PM-session project awareness and live monitoring"
status: proposed
priority: high
role: project_manager
execution_phase: phase-2-product-substrate
depends_on: []
blocks: ["PM-001", "PM-002", "PM-005", "T-HARNESS-003", "T-HARNESS-012"]
same_owner_with: ["PM-001", "PM-002", "PM-005"]
execution_mode: decision_cluster
decision_cluster: pm-session-substrate
decision_owner: Jason
normative: false
---

# T-HARNESS-002 — Resolve PM-session project awareness and live monitoring

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

PM must remain primary POC across web/TUI/API/channel surfaces. PM-session needs a safe, ergonomic way to answer project status, artifact, analytics, memory, and live-state questions.

## Decision To Make

Define the PM session harness for project awareness: active-project summary, project-record read tools, project memory projection, and live snapshot access.

## Dependencies

- None

## Blocks

- `PM-001`
- `PM-002`
- `PM-005`
- `T-HARNESS-003`
- `T-HARNESS-012`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `pm-session-substrate`

Recommended same-owner follow-up:

- `PM-001`
- `PM-002`
- `PM-005`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] PM can answer active project status from pm_session.
- [ ] PM can list artifacts and HE analytics from pm_session.
- [ ] PM can request read-only live snapshots when allowed.
- [ ] PM cannot write to project sandboxes from pm_session.
- [ ] local_workspace live snapshot requires explicit opt-in.
- [ ] Every read records project_data_events.

## Docs To Update Or Create

- `AD.md Open Questions OQ-PM1/OQ-PM2/OQ-PM3`
- `docs/specs/pcg-server-contract.md`
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
