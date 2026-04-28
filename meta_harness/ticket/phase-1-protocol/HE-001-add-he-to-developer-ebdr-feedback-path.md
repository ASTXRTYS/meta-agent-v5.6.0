---
ticket_id: HE-001
title: "Add HE-to-Developer EBDR feedback path"
status: proposed
priority: critical
role: harness_engineer
execution_phase: phase-1-protocol
depends_on: ["T-HARNESS-001"]
blocks: ["DEV-001", "DEV-002", "DEV-006", "EVAL-004"]
same_owner_with: ["EVAL-001", "DEV-001", "DEV-002", "DEV-006", "EVAL-004"]
execution_mode: decision_cluster
decision_cluster: dev-he-eval-loop
decision_owner: Jason
normative: false
---

# HE-001 — Add HE-to-Developer EBDR feedback path

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer submits phase work to HE, but no HE -> Developer EBDR return path exists.

## Decision To Make

Define concrete handoff return from HE phase review to Developer.

## Dependencies

- `T-HARNESS-001`

## Blocks

- `DEV-001`
- `DEV-002`
- `DEV-006`
- `EVAL-004`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `dev-he-eval-loop`

Recommended same-owner follow-up:

- `EVAL-001`
- `DEV-001`
- `DEV-002`
- `DEV-006`
- `EVAL-004`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer receives EBDR-1 packet after submit_phase_to_harness_engineer.
- [ ] Packet includes delta, boundary, localization, routing, and uncertainty.
- [ ] Packet excludes hidden eval internals.
- [ ] Feedback packet is registered as Developer-safe artifact.

## Docs To Update Or Create

- `docs/specs/handoff-tools.md`
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
