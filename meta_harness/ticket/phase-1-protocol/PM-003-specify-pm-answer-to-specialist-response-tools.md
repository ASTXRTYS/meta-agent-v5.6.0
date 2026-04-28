---
ticket_id: PM-003
title: "Specify PM answer-to-specialist response tools"
status: proposed
priority: high
role: project_manager
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001", "T-HARNESS-007"]
blocks: ["DEV-006"]
same_owner_with: ["T-HARNESS-001", "T-HARNESS-007"]
execution_mode: decision_cluster
decision_cluster: protocol-loop-architect
decision_owner: Jason
normative: false
---

# PM-003 — Specify PM answer-to-specialist response tools

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Specialists can ask PM questions, but PM currently lacks a concrete response path back to the requester.

## Decision To Make

Add PM response path for ask_pm queries from specialists.

## Dependencies

- `T-HARNESS-001`
- `T-HARNESS-007`

## Blocks

- `DEV-006`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `protocol-loop-architect`

Recommended same-owner follow-up:

- `T-HARNESS-001`
- `T-HARNESS-007`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Asking specialist receives answer in its own role context.
- [ ] PM can ask user first if stakeholder input is required.
- [ ] Scope-changing answer records a decision artifact.
- [ ] Non-scope answer can return directly without user interruption.

## Docs To Update Or Create

- `docs/specs/handoff-tools.md`
- `docs/specs/handoff-tool-definitions.md`
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
