---
ticket_id: DEV-002
title: "Specify Developer optimization experience store"
status: proposed
priority: high
role: developer
execution_phase: phase-4-role-contracts
depends_on: ["T-HARNESS-009", "T-HARNESS-010", "DEV-001", "EVAL-001", "HE-001", "HE-004"]
blocks: []
same_owner_with: ["HE-001", "EVAL-001", "DEV-001"]
execution_mode: hybrid_security_review
decision_cluster: dev-he-eval-loop
decision_owner: Jason
normative: false
---

# DEV-002 — Specify Developer optimization experience store

## Status

Proposed ticket. This file is not normative architecture. Accepted decisions must be promoted into `AD.md` and any derived `docs/specs/` contracts before implementation begins.

## Summary

Developer needs enough evidence to optimize while staying blind to private eval artifacts.

## Decision To Make

Define candidate snapshots, diffs, score summaries, logs, hypotheses, and trace references available to Developer.

## Dependencies

- `T-HARNESS-009`
- `T-HARNESS-010`
- `DEV-001`
- `EVAL-001`
- `HE-001`
- `HE-004`

## Blocks

- None

## Assignment Continuity Guidance

**Execution mode:** `hybrid_security_review`  
**Decision cluster:** `dev-he-eval-loop`

Recommended same-owner follow-up:

- `HE-001`
- `EVAL-001`
- `DEV-001`

## Isolation Guidance

- If `execution_mode` is `decision_cluster`, assign this ticket to the same agent handling the listed cluster so shared decisions stay coherent.
- If `execution_mode` contains `isolated`, assign this to a focused agent and require review before downstream tickets consume it.
- If `execution_mode` contains `hybrid`, let the cluster owner draft the decision and require a privacy/security or architecture review before closing.

## Acceptance Criteria

- [ ] Developer sees enough signal to optimize.
- [ ] Developer does not see hidden rubrics, held-out examples, judge prompts, or scoring logic.
- [ ] Candidate snapshots are versioned and registered.
- [ ] HE/Evaluator can reference allowed evidence without leakage.

## Docs To Update Or Create

- `docs/specs/project-data-contracts.md`
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
