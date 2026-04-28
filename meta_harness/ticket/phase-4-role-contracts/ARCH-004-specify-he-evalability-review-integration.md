---
ticket_id: ARCH-004
title: "Specify HE evalability review integration"
status: proposed
priority: medium_high
role: architect
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-004", "HE-004"]
blocks: ["PLAN-004"]
same_owner_with: ["HE-006", "HE-004"]
execution_mode: decision_cluster
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# ARCH-004 — Specify HE evalability review integration

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

HE evalability findings must either revise the design or be explicitly dispositioned before planning.

## Decision To Make

Define revision loop after submit_spec_to_harness_engineer and return_eval_coverage_to_architect.

## Dependencies

- `T-HARNESS-004`
- `HE-004`

## Blocks

- `PLAN-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `HE-006`
- `HE-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] HE feedback can require design changes before planning.
- [ ] Architect incorporates or rejects HE findings with rationale.
- [ ] PM approval package includes evalability status.

## Docs To Update Or Create

- `docs/specs/handoff-tools.md`
- `docs/specs/approval-and-gate-contracts.md`
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
