---
ticket_id: T-HARNESS-001
title: "Add reciprocal response paths for specialist loops"
status: proposed
priority: critical
role: cross_agent
execution_phase: phase-1-protocol
depends_on: []
blocks: ["PM-003", "RES-001", "PLAN-001", "HE-001", "EVAL-001", "DEV-001", "T-HARNESS-004", "T-HARNESS-003", "T-HARNESS-007", "ARCH-002", "DEV-006", "EVAL-004"]
same_owner_with: ["T-HARNESS-004", "PM-003", "RES-001", "PLAN-001", "HE-001", "EVAL-001"]
execution_mode: decision_cluster
decision_cluster: protocol-loop-architect
decision_owner: Jason
normative: false
---

# T-HARNESS-001 — Add reciprocal response paths for specialist loops

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Current docs promise specialist loops that the concrete 23-tool catalog cannot complete. The handoff catalog needs reciprocal response paths before role harnesses are implementable.

## Decision To Make

Choose the response primitive for non-pipeline loops: concrete reciprocal tools, active-handoff response primitive, PM-mediated responses, or a hybrid.

## Dependencies

- None

## Blocks

- `PM-003`
- `RES-001`
- `PLAN-001`
- `HE-001`
- `EVAL-001`
- `DEV-001`
- `T-HARNESS-004`
- `T-HARNESS-003`
- `T-HARNESS-007`
- `ARCH-002`
- `DEV-006`
- `EVAL-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `protocol-loop-architect`

Recommended same-owner follow-up:

- `T-HARNESS-004`
- `PM-003`
- `RES-001`
- `PLAN-001`
- `HE-001`
- `EVAL-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Every loop named in AD specialist loops has request and response paths.
- [ ] Developer can receive Evaluator phase findings and HE EBDR feedback without PM mediation.
- [ ] Researcher can return targeted findings to Architect, HE, or PM.
- [ ] Planner can receive HE/Evaluator gate recommendations.
- [ ] PM can answer specialist questions and route answers back to the asking specialist.
- [ ] Handoff specs and role toolsets are updated together.
- [ ] Conformance tests assert no documented loop is one-way unless explicitly non-returning.

## Docs To Update Or Create

- `AD.md §4 Specialist Loops`
- `AD.md §4 Handoff Protocol`
- `docs/specs/handoff-tools.md`
- `docs/specs/handoff-tool-definitions.md`
- `docs/specs/approval-and-gate-contracts.md`
- `docs/specs/pcg-data-contracts.md`

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
