---
ticket_id: DEV-006
title: "Specify Developer routing decision prompt contract"
status: proposed
priority: medium_high
role: developer
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-001", "T-HARNESS-007", "HE-001", "EVAL-001", "PM-003", "DEV-001", "DEV-004"]
blocks: []
same_owner_with: ["DEV-001", "PM-003", "HE-001", "EVAL-001"]
execution_mode: decision_cluster
decision_cluster: dev-he-eval-loop
decision_owner: Jason
normative: false
---

# DEV-006 — Specify Developer routing decision prompt contract

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer must not collapse all feedback into one vague request_evaluation path.

## Decision To Make

Encode when Developer routes to HE, Evaluator, or PM.

## Dependencies

- `T-HARNESS-001`
- `T-HARNESS-007`
- `HE-001`
- `EVAL-001`
- `PM-003`
- `DEV-001`
- `DEV-004`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `dev-he-eval-loop`

Recommended same-owner follow-up:

- `DEV-001`
- `PM-003`
- `HE-001`
- `EVAL-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] HE for eval harness/dataset/judge/calibration issues.
- [ ] Evaluator for spec/plan/code/UI/test acceptance.
- [ ] PM for scope/business/user-facing tradeoffs.
- [ ] Tool descriptions and prompt examples prevent vague routing.

## Docs To Update Or Create

- `AD.md Specialist Loops`
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
