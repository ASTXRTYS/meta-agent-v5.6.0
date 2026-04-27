# TICKET-006 — Design Evaluation Evidence Workbench Tools After LangSmith Audit

## Status

READY FOR POST-AUDIT RECONCILIATION

## Priority

P2 — follow-up design ticket after source audit

## Owner

Harness Engineer + Architect + Developer

## Depends On

- TICKET-001 LangSmith CLI/SDK capability audit
- `meta_harness/docs/specs/evaluation-evidence-workbench.md`

## Blocks

- Evidence Workbench implementation
- HE subagent trace-bundle analysis workflows
- Post-eval analytics generation from LangSmith evidence
- Developer-safe failure cluster packet generation

## Problem

The Evaluation Evidence Workbench is conceptually scoped, and TICKET-001 has now source-audited the installed LangSmith SDK, OpenEvals package, and local CLI availability.

We now need to translate verified LangSmith capabilities into the minimal deterministic harness HE needs without creating raw wrapper tools around SDK operations that LangSmith already owns.

## Goal

Design the minimal Evidence Workbench access pattern, deciding which operations are:

```txt
sdk_direct calls from HE-owned scripts or backend code
policy_tool operations with Meta Harness provenance/redaction/artifact/audit policy
skill_or_script procedural workflows
subagent task patterns
not supported in v1
```

## Inputs

From completed TICKET-001:

```txt
meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md
meta_harness/local-docs/langsmith-capability-matrix.md
meta_harness/local-docs/langsmith-ids-and-metadata-contract.md
```

Key audit conclusions:

```txt
Use sdk_direct for HE-owned scripts/backend code that call LangSmith SDK or OpenEvals primitives.
Use policy_tool only when Meta Harness adds provenance, visibility/redaction, artifact registration, analytics validation, bounded export, or audit logging.
Treat LangSmith CLI workflows as not_supported_v1 in this environment: installed langsmith==0.7.37 exposes no langsmith console script.
Do not introduce raw LangSmith wrapper tools merely because an SDK method exists.
Raw traces, full run trees, hidden examples, judge prompts/rubrics, evaluator reasoning/comments, attachments, and full dumps default he_private.
```

## Required Decisions (CANDIDATE ONLY)

The sections below are candidate design notes, not implementation authority. They must be reconciled with the completed TICKET-001 audit and with `meta_harness/docs/specs/evaluation-evidence-workbench.md`, which rejects model-visible tools that merely duplicate LangSmith SDK/CLI operations without adding Meta Harness provenance, visibility, redaction, artifact registration, analytics-schema validation, or audit policy.

### 1. Tool vs Skill Split (CANDIDATE)

**Decision status:** Candidate; must now be reconciled against the completed TICKET-001 audit and may shrink substantially before any formal spec or implementation.

| Capability | Implementation | Decision Rationale |
|------------|---------------|-------------------|
| SDK queries | **Backend tools only if policy-bearing** | Direct API access alone is not enough; tools must add project provenance, visibility, redaction, artifact registration, or audit policy |
| Filesystem mirror | **Backend tools only if policy-bearing** | File I/O and local persistence must create bounded evidence bundles with explicit inclusion/exclusion policy |
| Local analysis | **Scripts, skills, or backend tools depending on proof** | Structured computation should start in HE-owned scripts/skills unless deterministic backend policy is required |
| Subagent spawning | **Skill guidance** | Deep Agents SDK provides `task` tool natively |
| Filter syntax | **Backend helper** | Convert dict → LangSmith filter string |
| Redaction | **Backend tool** + SDK config | Multi-level redaction support |
| HE workflow | **Skill guidance** | Procedural knowledge for HE agent |

**Source-verification result:** TICKET-001 confirmed installed LangSmith/OpenEvals package capabilities against `.venv/lib/python3.12/site-packages/...` and found no usable installed LangSmith CLI console script for v1 product contracts.

### 2. Evidence Query Tools (CANDIDATE)

**Decision status:** Candidate operations for audit comparison, not an accepted 6-tool family. Each operation must be rejected unless it adds Meta Harness-specific policy/value beyond a raw SDK method call.

| Tool | SDK Method | Source |
|------|-----------|--------|
| `get_experiment_summary` | `get_experiment_results()` | `client.py:9750-9843` |
| `list_experiment_runs` | `list_runs(project_id=...)` | `client.py:3678-3870` |
| `read_run_trace` | `read_run(load_child_runs=True)` | `client.py:3583-3620` |
| `list_run_feedback` | `list_feedback(run_ids=...)` | `client.py:7518-7559` |
| `query_runs_by_filter` | `list_runs(filter=...)` | `client.py:3678-3870` |
| `get_dataset_info` | `read_dataset()` + `list_examples()` | `client.py:4925-4970`, `client.py:6384-6507` |

The source line references above are historical candidate anchors. The reconciliation pass must use the completed TICKET-001 audit artifacts as the current source of truth, especially where Python 3.11 path anchors have been superseded by Python 3.12 installed-source citations.

**Exact schemas:** Deferred. Do not create model-visible schemas until TICKET-001 proves the operation needs a policy-bearing product tool.

### 3. Local Mirror Tools (CANDIDATE)

**Decision status:** Candidate mirror operations, not an accepted 5-tool family. Local mirrors should be introduced only as bounded evidence-bundle operations with recorded source refs, selection criteria, included/excluded fields, visibility, and retention expectations.

| Tool | Purpose |
|------|---------|
| `mirror_experiment_runs` | Mirror all runs to JSONL |
| `mirror_failed_runs` | Filtered mirror (`neq(error, null)`) |
| `mirror_trace_bundle` | Full trace trees for specified runs |
| `export_experiment_summary` | Export summary (JSON + optional CSV) |
| `load_mirrored_evidence` | Load previously mirrored evidence |

**Candidate file layout for future bounded evidence bundles:**

```
/langsmith_mirror/experiments/{experiment_id}/
  experiment_summary.json
  runs_index.jsonl
  feedback_index.jsonl
  filtered/failed_runs.jsonl
  traces/{run_id}.json
  summaries/{run_id}.summary.md
```

### 4. Subagent Analysis Pattern (CANDIDATE)

**Decision status:** Candidate skill guidance, not a new tool surface.

**Rationale:** Deep Agents SDK provides `task` tool for subagent spawning. No wrapper needed.

**Pattern:**
```
1. HE mirrors evidence locally
2. HE bounds bundle (select specific trace files)
3. HE spawns subagent via task tool with explicit constraints
4. Subagent writes intermediate artifacts (summaries/)
5. HE synthesizes and redacts before publication
```

**Subagent output types:**
- `trace_summary_bundle` → `summaries/{run_id}.summary.md`
- `failure_cluster_report` → `clusters/failure_cluster_report.md`
- `candidate_comparison_report` → `comparison_report.md`
- `regression_report` → `filtered/regressed_runs.jsonl`

**Critical:** Subagents must NOT publish final analytics directly.

### 5. Redaction Boundary (CANDIDATE)

**Decision status:** Candidate redaction model. Must be verified against LangSmith SDK redaction/anonymizer behavior and Meta Harness Developer-safe policy before formalization.

| Level | Redacted Fields | Use Case |
|-------|-----------------|----------|
| `internal` | None | HE-private analysis |
| `stakeholder_visible` | `inputs` (PII policy), full `events` | Product analytics |
| `developer_safe` | `inputs`, `outputs`, `serialized`, `extra`, stack traces | Developer feedback (EBDR-1) |

**Implementation:**
- SDK client config: `hide_inputs`, `hide_outputs`, `anonymizer` (`client.py:748-755`)
- Per-tool redaction: `produce_developer_safe_summary` tool (spec §6.4)
- Output format: EBDR-1 packet structure

**Developer-safe fields preserved:**
- Feedback scores (metrics)
- Latency/cost (efficiency)
- Run IDs, Example IDs (routing/localization)
- Tool call names (behavior analysis)

## File Layout For Mirrored Evidence (CANDIDATE)

**Candidate layout** for future bounded evidence bundles:

```txt
/langsmith_mirror/
  experiments/
    {experiment_id}/
      experiment_summary.json          # Aggregated stats
      runs_index.jsonl                 # Streaming run list
      feedback_index.jsonl             # Streaming feedback list
      filtered/
        failed_runs.jsonl              # Error-filtered runs
        regressed_runs.jsonl           # Regression-flagged runs
      traces/
        {run_id}.json                  # Full trace trees
      summaries/
        {run_id}.summary.md            # Subagent-generated summaries
      clusters/
        failure_cluster_report.md      # HE-synthesized analysis
```

**Format notes:**
- JSONL for streaming collections (runs, feedback) — appendable, grep-friendly
- JSON for structured objects (summary, traces) — random access
- Markdown for narrative analysis (summaries, clusters) — human-readable

## Acceptance Criteria

- [x] TICKET-001 source audit is complete with SDK/CLI/OpenEvals line-number citations.
- [ ] Raw LangSmith wrapper operations are rejected unless they add Meta Harness provenance, visibility, redaction, artifact registration, analytics-schema validation, or audit policy.
- [ ] Tool-vs-skill split is minimized and documented after audit.
- [ ] Any local mirror file layout is documented as a bounded evidence-bundle layout, not a default full export path.
- [ ] Full-dump policy is documented in the formal spec.
- [ ] Filtered-export policy is documented in the formal spec.
- [ ] Subagent analysis pattern is operationalized without granting subagents publication authority.
- [ ] Redaction policy is integrated and verified against LangSmith SDK behavior.
- [ ] Developer-safe output boundary is preserved.
- [ ] Deferred capabilities are identified.

## Deliverables

1. **Updated Ticket** (this file) — Status: ready for post-audit reconciliation.
2. **Post-audit recommendation** — decide whether `meta_harness/docs/specs/evidence-workbench-tools-spec.md` is necessary or whether existing Workbench + analytics specs are sufficient.
3. **Survivor list** — name only the policy-bearing tools, scripts, or skills that survive the audit reconciliation, with access path classification for each.

## Next Steps

1. Reconcile this candidate tool list against the TICKET-001 audit and the minimal-tooling stance in `evaluation-evidence-workbench.md`.
2. Classify every candidate operation as `sdk_direct`, `policy_tool`, `skill_or_script`, or `not_supported_v1`.
3. Decide whether a formal `evidence-workbench-tools-spec.md` is warranted.
4. If warranted, add AD §9 registration and parent AD pointer before implementation.
5. Create separate implementation tickets only for policy-bearing tools that survive review.
