---
ticket_id: T-HARNESS-005
title: "Finalize role-specific provider and server-side tool policy"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-003"]
blocks: ["DEV-003", "EVAL-003", "RES-003", "role_factory_implementation"]
same_owner_with: ["T-HARNESS-003"]
execution_mode: isolated_sdk_review
decision_cluster: provider-tooling-specialist
decision_owner: Jason
normative: false
---

# T-HARNESS-005 — Finalize role-specific provider and server-side tool policy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

AD requires provider-specific server-side tools, but final role assignments and launch defaults remain incomplete.

## Decision To Make

Lock launch model defaults and provider-specific server-side tool availability per role.

## Dependencies

- `T-HARNESS-003`

## Blocks

- `DEV-003`
- `EVAL-003`
- `RES-003`
- `role_factory_implementation`

## Assignment Continuity Guidance

**Execution mode:** `isolated_sdk_review`  
**Decision cluster:** `provider-tooling-specialist`

Recommended same-owner follow-up:

- `T-HARNESS-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Launch model defaults are explicit.
- [ ] Provider-specific tool descriptors are injected by provider profile, not scattered across role factories.
- [ ] Each role has tests proving disallowed provider tools are absent.

## Docs To Update Or Create

- `AD.md §4 Agent Primitive Decisions`
- `DECISIONS.md Q11/Q13`
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
