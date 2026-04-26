# TICKET-002 — Migrate Project Data Plane From `optimization_trendline` To `evaluation_analytics_views`

## Status

PENDING
P0 — architecture consistency / schema repair

## Owner

Architect + Developer

## Depends On

- `meta_harness/docs/archive/replace-optimization-trendline-with-evaluation-analytics-views.md` (historical rationale only)
- `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md`
- `meta_harness/docs/specs/evaluation-analytics-chart-schemas.md`

## Blocks

- HE analytics publication tools
- UI analytics renderer
- Product Data Plane schema implementation
- Artifact visibility policy for analytics views
- Removal of stale trendline terminology

## Problem

`optimization_trendline` is now known to be over-narrow. It incorrectly treats optimization progress as the root product primitive, when the real requirement is a broader `evaluation_analytics_views` record family.

The Project Data Plane spec still needs to be repaired so downstream implementation does not build the wrong substrate.

## Goal

Update Project Data Plane docs/specs so `evaluation_analytics_views` is the canonical product record family for UI-renderable evaluation analytics.

`optimization_timeline` remains supported only as an `analytics_kind`.

## Required Changes

### 1. Remove / Deprecate Old Language

Search active specs for:

```txt
optimization_trendline
record_trendline_point
get_optimization_trendline
trendline_snapshot
OptimizationTrendlinePoint
```

Replace with the new model unless the reference is part of explicit migration history.

### 2. Add Record Family: `evaluation_analytics_views`

Add to Product Data Plane source-of-truth table.

Proposed source-of-truth row:

```txt
Record family: evaluation_analytics_views
Authoritative substrate: product database table evaluation_analytics_views
Non-authoritative mirrors: UI cache, LangGraph Store cache, rendered snapshot artifacts
```

### 3. Add Schema

Add `EvaluationAnalyticsView`:

```python
class EvaluationAnalyticsView(DataPlaneBase):
    analytics_view_id: str
    owner_agent: Literal["harness_engineer", "evaluator", "system"]

    phase: Literal[
        "scoping",
        "research",
        "architecture",
        "planning",
        "development",
        "acceptance",
    ]

    analytics_kind: Literal[
        "success_criteria_profile",
        "eval_coverage_matrix",
        "rubric_weight_distribution",
        "dataset_composition",
        "judge_profile_matrix",
        "risk_map",
        "eval_readiness_scorecard",
        "candidate_scorecard",
        "optimization_timeline",
        "capability_actual_vs_target",
        "failure_cluster_summary",
        "cost_latency_tradeoff",
        "regression_report",
    ]

    recommended_view_type: Literal[
        "radar_chart",
        "line_chart",
        "bar_chart",
        "stacked_bar_chart",
        "scatter_plot",
        "bubble_chart",
        "heatmap",
        "scorecard",
        "matrix",
        "table",
    ]

    visibility: Literal[
        "he_private",
        "evaluator_private",
        "internal",
        "developer_safe",
        "stakeholder_visible",
    ]

    title: str
    summary: str

    data_ref: str
    data_ref_kind: Literal[
        "artifact_id",
        "object_store_key",
        "filesystem_path",
    ]

    source_artifact_ids: list[str]

    langsmith_dataset_id: str | None
    langsmith_experiment_id: str | None
    langsmith_project_name: str | None
    langsmith_run_id: str | None
    langsmith_trace_url: str | None

    handoff_id: str | None

    render_status: Literal[
        "valid",
        "invalid",
        "unsupported",
        "stale",
    ]
```

### 4. Define Indexes

Minimum indexes:

```txt
(org_id, project_id, analytics_kind, updated_at desc)
(org_id, project_id, owner_agent, updated_at desc)
(org_id, project_id, visibility, updated_at desc)
(org_id, project_id, phase, updated_at desc)
(org_id, project_id, langsmith_experiment_id)
(org_id, project_id, handoff_id)
```

### 5. Add Write APIs

Add:

```txt
publish_analytics_view(input)
update_analytics_view(input)
mark_analytics_view_stale(input)
render_analytics_snapshot(input)
```

### 6. Add Read APIs

Add:

```txt
list_evaluation_analytics_views(org_id, project_id, filters)
get_evaluation_analytics_view(org_id, project_id, analytics_view_id)
get_analytics_source_data(org_id, project_id, analytics_view_id)
```

### 7. Update Role Access Matrix

Preliminary:

| Role/surface | Read | Write |
|---|---|---|
| PM session | sanitized/internal/stakeholder-visible by policy | promote visibility only if authorized |
| Web/TUI/headless | by org membership + visibility | no |
| Harness Engineer | read/write HE-owned analytics | yes |
| Evaluator | read/write evaluator-owned analytics | future/conditional |
| Developer | read only `developer_safe` analytics if explicitly exposed | no |
| System | read/write derived/snapshot/stale status | yes |

### 8. Update Artifact Manifest Kinds

Add:

```txt
analytics_source_data
evaluation_analytics_snapshot
experiment_summary
run_index
filtered_run_index
trace_bundle
trace_summary_bundle
failure_cluster_report
candidate_comparison_report
```

Deprecate or map:

```txt
trendline_snapshot -> evaluation_analytics_snapshot with analytics_kind="optimization_timeline"
```

### 9. Update `project_data_events`

Add record family:

```txt
evaluation_analytics_views
```

Operations should include:

```txt
publish_analytics_view
update_analytics_view
list_evaluation_analytics_views
get_evaluation_analytics_view
render_analytics_snapshot
mark_analytics_view_stale
```

## Acceptance Criteria

- [ ] Active Product Data Plane spec no longer treats `optimization_trendline` as a top-level record family.
- [ ] `evaluation_analytics_views` is defined as canonical record family.
- [ ] `optimization_timeline` is represented only as an `analytics_kind`.
- [ ] Read/write APIs are specified.
- [ ] Auth/visibility matrix is specified.
- [ ] Artifact manifest kinds are updated.
- [ ] Access audit events include analytics view operations.
- [ ] Migration mapping is documented.
- [ ] Developer-safe boundary is preserved.
