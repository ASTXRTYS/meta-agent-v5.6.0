---
ticket_id: DEV-003
title: "Specify Developer execution tool and permission profile"
status: proposed
priority: high
role: developer
execution_phase: phase-3-harness-substrate
depends_on: ["T-HARNESS-010", "T-HARNESS-005"]
blocks: []
same_owner_with: ["EVAL-003"]
execution_mode: isolated_security_review
decision_cluster: execution-permissions
decision_owner: Jason
normative: false
---

# DEV-003 — Specify Developer execution tool and permission profile

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer needs strong execution powers, but they must be sandboxed and separated from private eval roots.

## Decision To Make

Define Developer filesystem, shell, git, package manager, test, browser, and PR tooling across execution modes.

## Dependencies

- `T-HARNESS-010`
- `T-HARNESS-005`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `isolated_security_review`  
**Decision cluster:** `execution-permissions`

Recommended same-owner follow-up:

- `EVAL-003`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer can clone/build/test/commit/push/open draft PR in allowed modes.
- [ ] Dangerous shell/file operations respect approval/allowlist policy.
- [ ] Developer cannot access HE-private/evaluator-private roots.
- [ ] Local workspace mode is guarded.

## Docs To Update Or Create

- `docs/specs/repo-and-workspace-layout.md`
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
