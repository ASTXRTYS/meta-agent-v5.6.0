---
ticket_id: T-HARNESS-003
title: "Create a first-class agent harness contract spec"
status: proposed
priority: high
role: cross_agent
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-001", "T-HARNESS-002", "T-HARNESS-009", "T-HARNESS-010", "PM-001", "T-HARNESS-004", "T-HARNESS-008"]
blocks: ["role_factory_implementation", "T-HARNESS-005", "T-HARNESS-006", "T-HARNESS-011", "ARCH-005", "EVAL-005"]
same_owner_with: ["T-HARNESS-005", "T-HARNESS-006", "T-HARNESS-011"]
execution_mode: decision_cluster
decision_cluster: agent-harness-spec-architect
decision_owner: Jason
normative: false
---

# T-HARNESS-003 — Create a first-class agent harness contract spec

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

AD locks many primitives but no single development-ready spec tells a Developer how to assemble each role harness.

## Decision To Make

Decide whether role harness assembly is specified in one consolidated spec or seven role-specific specs.

## Dependencies

- `T-HARNESS-001`
- `T-HARNESS-002`
- `T-HARNESS-009`
- `T-HARNESS-010`
- `PM-001`
- `T-HARNESS-004`
- `T-HARNESS-008`

## Blocks

- `role_factory_implementation`
- `T-HARNESS-005`
- `T-HARNESS-006`
- `T-HARNESS-011`
- `ARCH-005`
- `EVAL-005`

## Assignment Continuity Guidance

**Execution mode:** `decision_cluster`  
**Decision cluster:** `agent-harness-spec-architect`

Recommended same-owner follow-up:

- `T-HARNESS-005`
- `T-HARNESS-006`
- `T-HARNESS-011`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Spec defines factory name, prompt path, role name, model default, handoff tools, product-record tools, execution tools, middleware, skills, memory roots, subagents, filesystem permissions, artifact obligations, and conformance tests per role.
- [ ] Spec is registered in AD §9 and parent AD section has a pointer.
- [ ] No implementation agent must infer harness assembly from scattered prose.

## Docs To Update Or Create

- `AD.md §4 Agent Primitive Decisions`
- `docs/specs/repo-and-workspace-layout.md`
- `new docs/specs/agent-harness-contracts.md`

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
