---
ticket_id: HE-006
title: "Specify HE harness acceptance criteria"
status: proposed
priority: medium
role: harness_engineer
execution_phase: phase-4-role-contracts
depends_on: ["HE-004", "T-HARNESS-004"]
blocks: ["EVAL-004"]
same_owner_with: ["HE-004", "EVAL-002"]
execution_mode: decision_cluster
decision_cluster: artifact-visibility-contracts
decision_owner: Jason
normative: false
---

# HE-006 — Specify HE harness acceptance criteria

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

HE acceptance stamp needs criteria for target-harness quality and privacy-safe feedback.

## Decision To Make

Define when submit_harness_acceptance(accepted=True) is allowed.

## Dependencies

- `HE-004`
- `T-HARNESS-004`

## Blocks

- `EVAL-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `artifact-visibility-contracts`

Recommended same-owner follow-up:

- `HE-004`
- `EVAL-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Acceptance covers eval harness quality, dataset policy, judge calibration, analytics validity, and EBDR privacy.
- [ ] Rejection includes safe remediation routing.

## Docs To Update Or Create

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
