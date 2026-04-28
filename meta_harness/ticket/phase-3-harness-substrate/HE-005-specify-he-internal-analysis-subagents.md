---
ticket_id: HE-005
title: "Specify HE internal analysis subagents"
status: proposed
priority: medium_high
role: harness_engineer
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-011", "HE-003"]
blocks: []
same_owner_with: ["HE-003"]
execution_mode: decision_cluster
decision_cluster: he-analytics-workbench
decision_owner: Jason
normative: false
---

# HE-005 — Specify HE internal analysis subagents

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Evidence Workbench allows internal analysis workers, but they must remain non-PCG and HE-synthesized.

## Decision To Make

Define whether HE receives ephemeral analysis workers for trace clustering, candidate comparison, regression analysis, and tool misuse detection.

## Dependencies

- `T-HARNESS-011`
- `HE-003`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `he-analytics-workbench`

Recommended same-owner follow-up:

- `HE-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Subagents remain ephemeral and non-PCG.
- [ ] Subagents do not emit Developer-facing feedback.
- [ ] Subagents preserve LangSmith locator provenance.
- [ ] HE remains synthesizer.

## Docs To Update Or Create

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
