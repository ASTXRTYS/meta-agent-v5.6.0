---
ticket_id: ARCH-005
title: "Specify prompt/tool contract artifact conventions"
status: proposed
priority: medium
role: architect
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-003", "ARCH-001"]
blocks: []
same_owner_with: ["ARCH-001"]
execution_mode: decision_cluster
decision_cluster: research-architect-loop
decision_owner: Jason
normative: false
---

# ARCH-005 — Specify prompt/tool contract artifact conventions

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Architect owns tool schemas and prompt contracts, but artifact conventions are not fully specified.

## Decision To Make

Define how Architect writes prompt contracts and tool schemas for downstream implementation.

## Dependencies

- `T-HARNESS-003`
- `ARCH-001`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `research-architect-loop`

Recommended same-owner follow-up:

- `ARCH-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Prompts remain external .md files.
- [ ] Tool schemas distinguish model-visible fields from hidden runtime fields.
- [ ] Prompt contracts encode behavioral invariants, not final prose only.

## Docs To Update Or Create

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
