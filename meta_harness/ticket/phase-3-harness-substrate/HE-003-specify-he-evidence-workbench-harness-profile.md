---
ticket_id: HE-003
title: "Specify HE Evidence Workbench harness profile"
status: proposed
priority: high
role: harness_engineer
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-011", "T-HARNESS-010"]
blocks: ["HE-005"]
same_owner_with: ["HE-002", "HE-005"]
execution_mode: decision_cluster
decision_cluster: he-analytics-workbench
decision_owner: Jason
normative: false
---

# HE-003 — Specify HE Evidence Workbench harness profile

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

HE should use LangSmith/OpenEvals native surfaces and skills before product tools except when high-friction repeated workflows justify tools.

## Decision To Make

Define HE skills, CLI/SDK workflows, explicit tool candidates, and permissions.

## Dependencies

- `T-HARNESS-011`
- `T-HARNESS-010`

## Blocks

- `HE-005`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `he-analytics-workbench`

Recommended same-owner follow-up:

- `HE-002`
- `HE-005`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] HE uses LangSmith CLI when native.
- [ ] HE uses SDK/OpenEvals when precision/composition is needed.
- [ ] No raw wrappers for list/get/create operations unless justified.
- [ ] Outputs preserve stable LangSmith/OpenEvals identifiers.

## Docs To Update Or Create

- `local-docs/langsmith-he-reference.md`
- `docs/specs/evaluation-evidence-workbench.md`
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
