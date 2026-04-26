---
doc_type: spec
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 Project-Scoped Execution Environment
status: draft
last_synced: 2026-04-26
owners: ["@Jason"]
---

# Evaluation Evidence Workbench Specification

> **Provenance:** Derived from `AD.md §6 Observability & Evaluation` and `§4 Project-Scoped Execution Environment`.
> **Status:** Draft · **Last synced with AD:** 2026-04-26.
> **Consumers:** Harness Engineer, Developer, Evaluator, Evidence Workbench tooling, LangSmith evidence mirror implementation.

## 1. Purpose

The Evaluation Evidence Workbench is the Harness Engineer capability for fetching, filtering, mirroring, summarizing, and inspecting LangSmith-backed eval evidence without blindly loading entire trajectory dumps into the main agent context.

This workbench exists because full trajectories are dense, high-risk, and expensive to analyze naively. The Harness Engineer needs structured ways to inspect evidence, delegate dense analysis to subagents, and produce sanitized analytics/feedback.

## 2. Source Of Truth

LangSmith is the source-of-truth for eval execution, experiment results, runs, traces, and feedback when evaluations run through LangSmith.

The Harness Engineer’s local virtual filesystem is an analysis workspace, not the primary source of truth.

```txt
LangSmith = eval truth
HE filesystem = working mirror / local analysis workspace
Project Data Plane = product-facing records, references, audit, visibility
```

## 3. Evidence Ingestion Philosophy

Do not dump full trajectories by default.

Use tiered evidence ingestion:

```txt
Tier 0: LangSmith references only
Tier 1: experiment summary
Tier 2: filtered run index
Tier 3: selected trace summaries
Tier 4: selected raw traces
Tier 5: full experiment dump
```

The Harness Engineer should escalate only as needed.

## 4. Evidence Artifacts

Possible HE-private or internal artifacts:

```txt
experiment_summary
run_index
filtered_run_index
trace_bundle
trace_summary_bundle
failure_cluster_report
regression_report
candidate_comparison_report
```

Visibility defaults:

| Artifact                    | Default visibility                               |
| --------------------------- | ------------------------------------------------ |
| raw trace bundle            | `he_private`                                     |
| full experiment dump        | `he_private`                                     |
| experiment summary          | `internal`                                       |
| run index                   | `he_private` or `internal` depending on contents |
| trace summary bundle        | `internal` unless it includes private examples   |
| failure cluster report      | `developer_safe` only after redaction            |
| candidate comparison report | `internal` or `developer_safe` after redaction   |

## 5. Subagent Pattern

Dense trace-bundle analysis should be delegated to subagents.

Pattern:

```txt
HE main agent
  -> obtains LangSmith experiment/run references
  -> mirrors selected evidence locally
  -> spawns subagent with bounded analysis task
  -> subagent reads bounded evidence bundle
  -> subagent writes summary artifact
  -> HE synthesizes result
  -> HE publishes analytics view or Developer-safe feedback
```

Example subagent tasks:

```txt
Analyze failed traces for tool misuse.
Cluster failure modes across these failed runs.
Compare candidate_2 against candidate_1 on grounding failures.
Inspect trace bundle and summarize recurring handoff issues.
Find regressions introduced after iteration_4.
```

Subagents should not publish final product analytics directly. They produce intermediate evidence summaries. The Harness Engineer remains the synthesizer and publisher.

## 6. TBD: LangSmith CLI/SDK Source Audit

This spec intentionally defers exact tool design until LangSmith CLI/SDK capabilities are source-audited.

The audit must answer:

```txt
What can the LangSmith SDK query directly?
What can the LangSmith CLI export directly?
Can experiments be exported wholesale?
Can individual traces/runs be dumped locally?
Can run trees/tool calls/messages be fetched selectively?
Can feedback/scores/evaluator outputs be queried by experiment/session?
Can comparison views be queried or only linked?
What metadata filters are supported?
What pagination/rate-limit patterns exist?
What is the recommended artifact format for datasets/eval examples?
What IDs should Meta Harness store for datasets, experiments, sessions, runs, traces, and feedback?
```

## 7. Provisional Tool Families

These are provisional and must not be treated as final until source audit is complete.

### 7.1 LangSmith Evidence Query Tools

Potential tools:

```txt
get_eval_experiment_summary
query_eval_runs
inspect_eval_run
list_eval_feedback
```

### 7.2 Local Evidence Mirror Tools

Potential tools:

```txt
mirror_eval_trace_bundle
mirror_failed_runs
mirror_regressed_runs
export_full_experiment_bundle
```

### 7.3 Evidence Summarization Tools

Potential tools:

```txt
summarize_trace_bundle
cluster_failure_modes
compare_candidate_runs
produce_developer_safe_failure_summary
```

These may be implemented as HE tools, HE skills, or subagent task patterns depending on source-audited LangSmith capabilities.

## 8. Full Trace Dumps

Full trace dumps should be allowed only as explicit HE-private operations.

Policy:

```txt
Allowed: explicit HE-private full export
Default: no full export
Not allowed: auto-load full dump into model context
Not allowed: stakeholder visibility by default
Not allowed: Developer visibility
```

## 9. Filtered Export Preference

The workbench should prefer filtered exports before full dumps.

Potential filters:

```txt
failed_only
regressed_only
candidate_id
metric_key
score_below
latency_above
tool_call_contains
error_contains
run_ids
limit
```

Exact filter syntax depends on LangSmith SDK/CLI support and must be source-audited.

## 10. Relationship To Evaluation Analytics Views

The Evidence Workbench produces or supports evidence artifacts.

`evaluation_analytics_views` consumes those artifacts and LangSmith references.

```txt
LangSmith experiment/run/trace
  -> evidence query/mirror
  -> HE/subagent analysis artifact
  -> analytics source JSON
  -> evaluation_analytics_view
  -> UI renderer
```