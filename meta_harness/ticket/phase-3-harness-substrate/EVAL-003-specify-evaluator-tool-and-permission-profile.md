---
ticket_id: EVAL-003
title: "Specify Evaluator tool and permission profile"
status: proposed
priority: high
role: evaluator
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-010", "T-HARNESS-005"]
blocks: []
same_owner_with: ["DEV-003"]
execution_mode: isolated_security_review
decision_cluster: execution-permissions
decision_owner: Jason
normative: false
---

# EVAL-003 — Specify Evaluator tool and permission profile

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Evaluator must inspect and run tests/UI checks without modifying code or design.

## Decision To Make

Define Evaluator read-only code/test/browser/tool permissions.

## Dependencies

- `T-HARNESS-010`
- `T-HARNESS-005`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `isolated_security_review`  
**Decision cluster:** `execution-permissions`

Recommended same-owner follow-up:

- `DEV-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Write/edit tools are absent or approval-blocked.
- [ ] Test/browser execution is allowed in sandbox.
- [ ] Evaluator cannot see HE-private eval internals unless coordination explicitly requires HE-private review.

## Docs To Update Or Create

- `docs/specs/project-data-contracts.md`
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
