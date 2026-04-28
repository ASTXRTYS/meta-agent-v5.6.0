---
ticket_id: T-HARNESS-006
title: "Convert StagnationGuardMiddleware into a buildable role contract"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-003"]
blocks: ["role_factory_implementation"]
same_owner_with: ["T-HARNESS-003"]
execution_mode: isolated_sdk_review
decision_cluster: middleware-specialist
decision_owner: Jason
normative: false
---

# T-HARNESS-006 — Convert StagnationGuardMiddleware into a buildable role contract

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

StagnationGuard is listed as universal middleware, but remains more design vision than implementation contract.

## Decision To Make

Define exact state schema, progress signals, thresholds, nudge text, hard-stop behavior, and tests for StagnationGuardMiddleware.

## Dependencies

- `T-HARNESS-003`

## Blocks

- `role_factory_implementation`

## Assignment Continuity Guidance

**Execution mode:** `isolated_sdk_review`  
**Decision cluster:** `middleware-specialist`

Recommended same-owner follow-up:

- `T-HARNESS-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Each role has tuned thresholds.
- [ ] Progress signals include role-appropriate artifacts, todo updates, file writes, test runs, trace/eval analysis, and handoff tool calls.
- [ ] False positives are tested for Researcher, HE, and Developer long-running legitimate work.

## Docs To Update Or Create

- `AD.md §4 Agent Primitive Decisions`
- `DECISIONS.md Q12`
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
