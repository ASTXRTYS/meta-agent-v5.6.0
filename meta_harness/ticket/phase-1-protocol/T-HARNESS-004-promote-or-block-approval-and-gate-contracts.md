---
ticket_id: T-HARNESS-004
title: "Promote or block approval-and-gate-contracts.md"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001"]
blocks: ["PM-004", "HE-006", "EVAL-002", "T-HARNESS-003", "ARCH-004", "EVAL-005", "PLAN-004"]
same_owner_with: ["T-HARNESS-001", "PM-004"]
execution_mode: decision_cluster
decision_cluster: protocol-loop-architect
decision_owner: Jason
normative: false
---

# T-HARNESS-004 — Promote or block approval-and-gate-contracts.md

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Gate behavior is implementation-critical but currently draft. It governs approval stamps, phase gates, final-turn guard, and autonomous mode.

## Decision To Make

Either promote approval-and-gate-contracts.md to active or list explicit blockers.

## Dependencies

- `T-HARNESS-001`

## Blocks

- `PM-004`
- `HE-006`
- `EVAL-002`
- `T-HARNESS-003`
- `ARCH-004`
- `EVAL-005`
- `PLAN-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `protocol-loop-architect`

Recommended same-owner follow-up:

- `T-HARNESS-001`
- `PM-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Gate pass/fail, approval stamps, autonomous mode, final-turn guard, and pcg_gate_context projection are testable.
- [ ] Gate failure returns ToolMessage, not Command.
- [ ] Final-turn guard is mandatory for all seven role harnesses.

## Docs To Update Or Create

- `docs/specs/approval-and-gate-contracts.md`
- `AD.md §9 Derived Specs`

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
