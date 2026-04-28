---
ticket_id: T-HARNESS-012
title: "Clean stale deferral, security, and deployment language"
status: proposed
priority: medium
role: cross_agent
execution_phase: phase-5-cleanup
depends_on: ["T-HARNESS-002", "T-HARNESS-010"]
blocks: []
same_owner_with: []
execution_mode: isolated_doc_cleanup
decision_cluster: docs-cleanup
decision_owner: Jason
normative: false
---

# T-HARNESS-012 — Clean stale deferral, security, and deployment language

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Several docs still use future/v2/local-first wording that can obscure current launch-critical behavior.

## Decision To Make

Classify and repair stale future/v2/local-first/security wording after core harness decisions land.

## Dependencies

- `T-HARNESS-002`
- `T-HARNESS-010`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `isolated_doc_cleanup`  
**Decision cluster:** `docs-cleanup`

Recommended same-owner follow-up:

- None

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Deferrals classified as launch blocker, implementation detail, post-launch enhancement, or historical rationale.
- [ ] Security/deployment posture matches Project Records Layer auth and web/headless product behavior.
- [ ] Frozen DECISIONS rationale is clearly marked when superseded.

## Docs To Update Or Create

- `AD.md §8`
- `DECISIONS.md`
- `docs/specs/*`

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
