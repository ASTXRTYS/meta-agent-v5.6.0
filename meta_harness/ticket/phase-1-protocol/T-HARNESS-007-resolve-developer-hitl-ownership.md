---
ticket_id: T-HARNESS-007
title: "Resolve Developer HITL ownership"
status: proposed
priority: high
role: developer
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001"]
blocks: ["DEV-004", "DEV-006", "PM-003", "ARCH-003"]
same_owner_with: ["PM-003", "DEV-004", "DEV-006", "ARCH-003"]
execution_mode: decision_cluster
decision_cluster: developer-hitl-routing
decision_owner: Jason
normative: false
---

# T-HARNESS-007 — Resolve Developer HITL ownership

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Vision promises participatory harness engineering, but Developer lacks AskUserMiddleware. The role boundary must be closed before Developer prompt/tool specs.

## Decision To Make

Choose PM relay, restricted Developer direct HITL, or hybrid for development-phase user clarification.

## Dependencies

- `T-HARNESS-001`

## Blocks

- `DEV-004`
- `DEV-006`
- `PM-003`
- `ARCH-003`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `developer-hitl-routing`

Recommended same-owner follow-up:

- `PM-003`
- `DEV-004`
- `DEV-006`
- `ARCH-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer can resolve ambiguity without direct private user channel by default.
- [ ] PM remains primary POC.
- [ ] Scope-changing answers are recorded as project artifacts/events.

## Docs To Update Or Create

- `AD.md OQ-1`
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
