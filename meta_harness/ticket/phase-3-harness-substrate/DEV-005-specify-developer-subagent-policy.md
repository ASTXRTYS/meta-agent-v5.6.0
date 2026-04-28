---
ticket_id: DEV-005
title: "Specify Developer subagent policy"
status: proposed
priority: medium_high
role: developer
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-011", "T-HARNESS-010"]
blocks: []
same_owner_with: ["DEV-003"]
execution_mode: decision_cluster
decision_cluster: execution-permissions
decision_owner: Jason
normative: false
---

# DEV-005 — Specify Developer subagent policy

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer may benefit from ephemeral workers, but they must not become durable project roles or leak private artifacts.

## Decision To Make

Decide whether Developer receives ephemeral coding/test/research subagents through Deep Agents task tool.

## Dependencies

- `T-HARNESS-011`
- `T-HARNESS-010`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `execution-permissions`

Recommended same-owner follow-up:

- `DEV-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Subagents receive complete instructions per call.
- [ ] Subagents do not inherit private skills/memory unless configured.
- [ ] Subagents cannot access private eval artifacts.
- [ ] Developer remains responsible for integration and final tool calls.

## Docs To Update Or Create

- `docs/specs/agent-harness-contracts.md`
- `AGENTS.md`

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
