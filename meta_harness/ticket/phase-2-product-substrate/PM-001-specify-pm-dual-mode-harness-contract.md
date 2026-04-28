---
ticket_id: PM-001
title: "Specify PM dual-mode harness contract"
status: proposed
priority: high
role: project_manager
execution_phase: phase-2-product-substrate
depends_on: ["T-HARNESS-002"]
blocks: ["PM-002", "PM-005", "T-HARNESS-003"]
same_owner_with: ["T-HARNESS-002", "PM-002", "PM-005"]
execution_mode: decision_cluster
decision_cluster: pm-session-substrate
decision_owner: Jason
normative: false
---

# PM-001 — Specify PM dual-mode harness contract

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

PM must serve as both session-facing POC and project lifecycle coordinator while preserving one role identity.

## Decision To Make

Define how one PM role behaves differently in pm_session and project threads without creating two roles.

## Dependencies

- `T-HARNESS-002`

## Blocks

- `PM-002`
- `PM-005`
- `T-HARNESS-003`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `pm-session-substrate`

Recommended same-owner follow-up:

- `T-HARNESS-002`
- `PM-002`
- `PM-005`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] pm_session tools include project portfolio/status/artifact/analytics reads and project spawn.
- [ ] project tools include lifecycle delivery, approval, PM answer, and terminal emission.
- [ ] Same PM memory identity is preserved without contaminating project-scoped state.

## Docs To Update Or Create

- `AD.md PM Session And Project Entry Model`
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
