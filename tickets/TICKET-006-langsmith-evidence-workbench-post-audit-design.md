# TICKET-006 — Design Evaluation Evidence Workbench Tools After LangSmith Audit

## Status

Proposed

## Priority

P2 — follow-up design ticket after source audit

## Owner

Harness Engineer + Architect + Developer

## Depends On

- TICKET-001 LangSmith CLI/SDK capability audit
- `docs/specs/evaluation-evidence-workbench.md`

## Blocks

- Evidence Workbench implementation
- HE subagent trace-bundle analysis workflows
- Post-eval analytics generation from LangSmith evidence
- Developer-safe failure cluster packet generation

## Problem

The Evaluation Evidence Workbench is conceptually scoped, but exact tools must wait until LangSmith capabilities are source-audited.

After TICKET-001 completes, we need to translate verified LangSmith capabilities into the minimal deterministic harness HE needs.

## Goal

Design the actual Evidence Workbench tool family, deciding which operations are:

```txt
direct SDK wrapper tools
direct CLI guidance through skill/procedural knowledge
sandboxed Python/CLI operations
subagent task patterns
not supported in v1
```

## Inputs

From TICKET-001:

```txt
LangSmith SDK capability matrix
LangSmith CLI capability matrix
recommended access path
required stored identifiers
export/mirror strategy
redaction strategy
```

## Required Decisions

### 1. Tool vs Skill Split

For each capability, decide:

```txt
Backend tool
HE skill guidance
Subagent task pattern
Deferred
```

### 2. Evidence Query Tools

Possible tools:

```txt
get_eval_experiment_summary
query_eval_runs
inspect_eval_run
list_eval_feedback
```

Determine exact schemas from source-audited LangSmith APIs.

### 3. Local Mirror Tools

Possible tools:

```txt
mirror_eval_trace_bundle
mirror_failed_runs
mirror_regressed_runs
export_full_experiment_bundle
```

Determine exact schemas, limits, visibility, and file layout.

### 4. Subagent Analysis Pattern

Define how HE delegates dense analysis.

Required outputs from subagents:

```txt
trace_summary_bundle
failure_cluster_report
candidate_comparison_report
regression_report
developer_safe_failure_summary
```

Subagents must not publish final analytics views directly.

### 5. Redaction Boundary

Define required redaction before:

```txt
developer_safe feedback
stakeholder_visible analytics
internal analytics
```

## Proposed File Layout For Mirrored Evidence

Subject to audit:

```txt
/langsmith_mirror/
  experiments/
    {experiment_id}/
      experiment_summary.json
      runs_index.jsonl
      feedback_index.jsonl
      filtered/
        failed_runs.jsonl
        regressed_runs.jsonl
      traces/
        {run_id}.json
      summaries/
        {run_id}.summary.md
      clusters/
        failure_cluster_report.md
```

## Acceptance Criteria

- [ ] Exact Evidence Workbench tools are specified.
- [ ] Exact tool schemas are source-aligned with LangSmith.
- [ ] Tool-vs-skill split is documented.
- [ ] Local mirror file layout is documented.
- [ ] Full-dump policy is documented.
- [ ] Filtered-export policy is documented.
- [ ] Subagent analysis pattern is operationalized.
- [ ] Redaction policy is integrated.
- [ ] Developer-safe output boundary is preserved.
