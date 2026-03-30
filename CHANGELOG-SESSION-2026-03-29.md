# Session Changelog — 2026-03-29: Research-Agent PRD Alignment + Experiment Workflow

## Summary

This session aligned the technical specification and development plan with the enhanced research-agent PRD, added incremental experiment checkpoints to Phase 3, documented the experiment execution pattern (how to run real agent experiments via LangSmith `evaluate()`), and built a markdown report generator so experiment results are persisted as readable artifacts.

**Trigger:** The research-agent PRD (`workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md`) defines significantly richer behavior than what the spec previously captured. The 38-eval research evaluation suite and synthetic calibration dataset were already aligned with the PRD; the spec and dev plan needed to catch up.

---

## Changes by File

### Spec: `technical-specification-v5.6.0-final.md`

**v5.6.1 Changelog added** (6 items: C1–C6)

| Section | Change | Why |
|---------|--------|-----|
| 3.3 RESEARCH stage | Rewritten: PRD-aligned entry/exit conditions, 5 output artifacts, 2 HITL checkpoints, expanded tool list, 10-phase protocol reference | Old version had thin description, single artifact, generic HITL |
| 5.3 Research Bundle Schema | Expanded from 6 to 13 required sections organized by topic. Added YAML frontmatter requirements. | PRD FR J requires topic-organized bundle with ecosystem options, model matrix, SME perspectives, confidence assessments, citation index, etc. |
| 5.3.1 (new) | Research Decomposition Schema | PRD FR B requires persisted decomposition with domains, PRD line citations, eval ID mappings, skills mappings, progress tracker |
| 5.3.2 (new) | Research Cluster Schema | PRD FR I requires HITL cluster artifact with themed groups, PRD requirement ties, effort estimates |
| 6.1 research-agent | Rewritten with full PRD design: description, non-goals, tools (including server-side distinction), skills posture | Old version was ~15 lines with no behavioral detail |
| 6.1.2 (new) | Research Protocol — 10-phase pipeline | PRD Core User Workflows 1–6 mapped to explicit protocol phases |
| 6.1.3 (new) | Sub-Agent Topology — reasoning requirements | PRD FR D + Stakeholder Design Intent on intentional delegation |
| 6.1.4 (new) | Required Output Artifacts — 5 files | PRD Required Outputs section |
| 6.1.5 (new) | Configuration — SME handles, skills paths, agent config | PRD Configuration section |
| 6.1.6 (new) | Spec-Writer Feedback Loop | PRD FR K |

### Dev Plan: `development-plan-v5.6.0.md`

| Section | Change | Why |
|---------|--------|-----|
| 3.1 Overview | Updated spec section references to include new subsections | Stale refs after spec changes |
| 3.2.1 Research-Agent | Full rewrite: 15 PRD-derived tasks with protocol phase mapping, eval coverage IDs per task, canonical PRD reference | Old version had ~30 lines missing most PRD features |
| 3.2.4 RESEARCH wiring | Updated: eval suite as input, 2 HITL checkpoints, feedback loop wiring | Old version didn't reflect updated Section 3.3 |
| 3.2.6 | Added two-layer eval architecture explanation (7 phase-gate + 38 behavioral) | Builder wouldn't know which evals to run without this |
| 3.2.7 (new) | Experiment Execution Pattern: 3 actors (dataset, agent, evaluators), run function code, LangSmith `evaluate()` wiring, HITL handling, two modes | Critical gap: no explanation of HOW to run real experiments |
| 3.2.8 (new) | Incremental Experiment Checkpoints: 5 gates with specific eval IDs, commands, pass criteria | Builder would otherwise wait until end of phase to run experiments |
| 3.2.9 (new) | Experiment Reporting Workflow: dual-channel (markdown + LangSmith UI), code-agent compatibility | No way to read judge feedback without LangSmith UI |
| 3.3.1 | Renamed to "Phase Gate Evals (Layer 1)", added 3.3.1.1 for Layer 2 with category table | Relationship between 7 phase-gate and 38 behavioral evals was unclear |
| 3.3.5 | Pass criteria split into Layer 1 + Layer 2 + Regression | Only mentioned 7 structural evals |
| 3.3.6 | Remediation protocol updated with Layer 1 vs Layer 2 diagnosis | Generic "fix and rerun" not actionable |
| 3.3.7 | Phase Complete Checklist expanded: artifacts, agents, wiring, evals, experiment reports, git | Missing output artifacts and report checklist items |

### Code: `meta_agent/evals/research/`

| File | Change | Why |
|------|--------|-----|
| `report.py` (new) | Markdown experiment report generator. Two input modes: runner dict (full reasoning/evidence) and LangSmith `ExperimentResults` (`.key`, `.score`, `.comment`). Failures at top with full judge output, passing as summary table. | No way to persist or read experiment results without LangSmith UI |
| `runner.py` | Added `import os`, `from report import generate_report`, `--report-dir` CLI flag, `generate_report()` call after `run_suite()` | Wire report generation into existing runner |
| `langsmith_experiment.py` | Added `from report import generate_report_from_experiment_results`, `--report-dir` CLI flag, `blocking=True` on `evaluate()`, `generate_report_from_experiment_results()` call, `report_dir` parameter on `run_experiment()` | Wire report generation into LangSmith experiment script |

---

## Traceability Verification

All 11 PRD functional requirements (A–K) verified as traceable: PRD → Spec → Dev Plan → Evals.

| PRD FR | Spec Section | Plan Task | Evals |
|--------|-------------|-----------|-------|
| A. PRD/Eval Consumption | 6.1.2 Phase 1 | 3.2.1 Protocol Phase 1 | RB-001, RB-002, RS-001, RS-002 |
| B. Decomposition | 6.1.2 Phase 2, 5.3.1 | 3.2.1 Protocol Phase 2 | RB-003, RQ-001 |
| C. Skills Utilization | 6.1.2 Phase 3 | 3.2.1 Protocol Phase 3 | RB-007, RQ-007–009 |
| D. Sub-Agent Delegation | 6.1.2 Phase 4, 6.1.3 | 3.2.1 Protocol Phase 4 | RB-008–010, RQ-010 |
| E. SME Consultation | 6.1.2 Phase 8, 6.1.5 | 3.2.1 Protocol Phase 8 | RQ-006 |
| F. Anthropic Model Research | 6.1.2 Phase 9 | 3.2.1 Synthesis | RB-006 |
| G. Citations | 5.3 section 13 | 3.2.1 Synthesis | RB-005, RINFRA-004, RQ-004 |
| H. Gap Remediation | 6.1.2 Phase 5 | 3.2.1 Protocol Phase 5 | RQ-013 |
| I. HITL Clusters | 6.1.2 Phase 6, 5.3.2 | 3.2.1 Protocol Phase 6 | RB-011, RQ-012 |
| J. Research Bundle | 6.1.2 Phase 9, 5.3 | 3.2.1 Synthesis | RINFRA-001–003, RQ-005, RQ-011 |
| K. Feedback Loop | 6.1.6 | 3.2.1 Feedback Loop | RI-001 |

38 evals total: 28 mapped to FRs, 10 additional coverage (breadth, depth, reasoning, integration).

---

## SDK Verification

All patterns verified against:
- **Deep Agents SDK**: `create_deep_agent()` → `CompiledStateGraph`, `.invoke()` with messages + config, `interrupt_on` requires `checkpointer`, `skills` requires `backend`
- **LangSmith Python SDK**: `evaluate()` returns `ExperimentResults`, iterable with `result["run"].outputs`, `result["evaluation_results"]["results"]` (list of `EvaluationResult` with `.key`, `.score`, `.comment`), `blocking=True/False`
- **LangSmith CLI**: `langsmith experiment list/get`, `langsmith trace list/get`

---

## Files Not Changed (already aligned)

- `workspace/projects/meta-agent/evals/eval-suite-prd.json` — 38 evals already PRD-aligned
- `workspace/projects/meta-agent/datasets/synthetic-research-agent.json` — 5 scenarios already PRD-aligned
- `meta_agent/evals/research/evaluators.py` — evaluator registry unchanged
- `meta_agent/evals/research/judge_infra.py` — judge infrastructure unchanged
- `meta_agent/evals/research/rubrics.py` — rubrics unchanged

---

## Open Items

1. **PRD UQ4** (bundle versioning on spec-writer follow-up) — not addressed in spec or plan; design decision deferred
2. **Run function implementation** — Section 3.2.7 provides the pattern and code sketch; actual `run_function.py` is a Phase 3 implementation task, not created in this session
3. **HITL auto-approve for eval mode** — Section 3.2.7 recommends Option A (`eval_mode=True` flag); implementation is a Phase 3 task
