# TICKET-005 — Define UI Renderer Contract For `evaluation_analytics_views`

## Status

Proposed

## Priority

P1 — product surface contract

## Owner

Frontend + Architect + Evaluator

## Depends On

- TICKET-002 Project Data Plane migration
- TICKET-003 chart schema validation contract
- `docs/specs/evaluation-analytics-chart-schemas.md`

## Blocks

- Web dashboard rendering of HE analytics
- TUI analytics cards/panels
- Headless summary formatting
- PM project observability over analytics surfaces

## Problem

The Harness Engineer will publish `evaluation_analytics_views` product records that point to analytics source data. The UI needs a deterministic contract for rendering those records.

Without a renderer contract, frontend developers may infer incompatible behavior from artifacts, chart schemas, LangSmith links, or legacy trendline terminology.

## Goal

Define how first-party product surfaces render `evaluation_analytics_views`.

## Required Surfaces

### 1. Web App

Must support dashboard rendering for:

```txt
radar_chart
line_chart
heatmap
scorecard
table
```

Progressive renderer support for:

```txt
bar_chart
stacked_bar_chart
matrix
scatter_plot
bubble_chart
```

### 2. TUI

Must support compact textual summaries for all chart families.

Minimum TUI display:

```txt
title
analytics_kind
phase
visibility
summary
render_status
source artifact count
LangSmith ref presence
fallback table/text summary
```

### 3. Headless Adapters

Must support concise summaries, not full chart rendering.

Example:

```txt
Harness analytics updated: Candidate Scorecard
Status: valid
Summary: Candidate 2 improved grounding but regressed latency.
Open dashboard for chart.
```

## UI Read Path

All surfaces read through backend operations:

```txt
list_evaluation_analytics_views(org_id, project_id, filters)
get_evaluation_analytics_view(org_id, project_id, analytics_view_id)
get_analytics_source_data(org_id, project_id, analytics_view_id)
```

No surface reads LangGraph Store directly.

No surface scans role filesystems for analytics views.

## Renderer Contract

Renderer receives:

```python
class AnalyticsRendererInput(TypedDict):
    analytics_view: EvaluationAnalyticsView
    source_data: dict
```

Renderer must:

```txt
validate source_data schema_version
validate source_data.view_type matches analytics_view.recommended_view_type
display unsupported views with graceful fallback
never expose hidden source fields
respect visibility filters
show stale/invalid render status visibly
```

## Fallback Behavior

If renderer unsupported:

```txt
show title
show summary
show analytics_kind
show "Unsupported visualization type"
show source artifact link if allowed
```

If source data invalid:

```txt
show title
show "Invalid analytics source data"
show validation error summary to internal users
hide detailed errors from stakeholder-visible views
```

If source artifact unavailable:

```txt
show "Analytics source unavailable"
record access event
do not silently drop analytics view
```

## Initial Renderer Priority

```txt
1. scorecard
2. table
3. line_chart
4. radar_chart
5. heatmap
```

This order is chosen because scorecards/tables are easiest to implement and provide immediate product value while more visual renderers mature.

## Acceptance Criteria

- [ ] UI read path is specified.
- [ ] Web/TUI/headless behavior is specified.
- [ ] Renderer input contract is specified.
- [ ] Unsupported renderer fallback is specified.
- [ ] Invalid source-data fallback is specified.
- [ ] Artifact-unavailable behavior is specified.
- [ ] Initial renderer priority is specified.
- [ ] No UI surface reads LangGraph Store or role filesystem directly.
