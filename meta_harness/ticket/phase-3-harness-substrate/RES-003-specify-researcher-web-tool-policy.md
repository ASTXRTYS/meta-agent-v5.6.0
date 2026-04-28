---
ticket_id: RES-003
title: "Specify Researcher web tool policy"
status: proposed
priority: medium_high
role: researcher
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-005"]
blocks: []
same_owner_with: ["RES-002"]
execution_mode: decision_cluster
decision_cluster: research-architect-loop
decision_owner: Jason
normative: false
---

# RES-003 — Specify Researcher web tool policy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Researcher is primary web-search/fetch role, but source reliability and SDK verification rules must be explicit.

## Decision To Make

Define provider-neutral web search/fetch capabilities and source hierarchy.

## Dependencies

- `T-HARNESS-005`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `research-architect-loop`

Recommended same-owner follow-up:

- `RES-002`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Official docs/source repos preferred for SDK behavior.
- [ ] Web facts include retrieval date/source URLs.
- [ ] External web results cannot override local source verification for SDK behavior.

## Docs To Update Or Create

- `AGENTS.md`
- `local-docs/SDK_REFERENCE.md`
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
