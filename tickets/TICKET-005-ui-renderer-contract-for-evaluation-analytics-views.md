# TICKET-005 — Define UI Renderer Contract For `evaluation_analytics_views`

## Status

Completed — docs-phase contract

## Priority

P1 — product surface contract

## Owner

Frontend + Architect + Evaluator

## Depends On

- TICKET-002 Project Data Plane migration
- TICKET-003 chart schema validation contract
- `meta_harness/docs/specs/evaluation-analytics-chart-schemas.md`
- `meta_harness/docs/specs/evaluation-analytics-renderer-contract.md`

## Blocks

- Future web dashboard rendering of HE analytics
- Future TUI analytics cards/panels
- Future headless summary formatting
- PM project observability over analytics surfaces

## Problem

The Harness Engineer will publish `evaluation_analytics_views` product records that point to analytics source data. The UI needs a deterministic contract for rendering those records.

Without a renderer contract, frontend developers may infer incompatible behavior from artifacts, chart schemas, LangSmith links, or legacy trendline terminology.

## Goal

Define how first-party product surfaces render `evaluation_analytics_views`.

## Docs-Phase Boundary

This ticket is a specification ticket, not a frontend implementation ticket.

Do not create React components, TUI widgets, backend endpoints, renderer modules,
fixtures, or tests in this phase. Define the product rendering contract,
surface-specific expectations, read paths, fallback behavior, and acceptance
criteria that future development work must satisfy.

The concrete frontend framework components, TUI widget implementation, snapshot
renderer implementation, and adapter module layout are future development
decisions.

## Required Surfaces

### 1. Web App

Future web surfaces must support dashboard rendering for:

```txt
scorecard
table
line_chart
radar_chart
heatmap
```

Future progressive renderer support should include:

```txt
bar_chart
stacked_bar_chart
matrix
scatter_plot
bubble_chart
```

### 2. TUI

Future TUI surfaces must support compact textual summaries for all chart
families.

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

Future headless adapters must support concise summaries, not full chart
rendering.

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

Future renderers should receive an input equivalent to:

```python
class AnalyticsRendererInput(TypedDict):
    analytics_view: EvaluationAnalyticsView
    source_data: dict
```

Future renderers must:

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

- [x] UI read path is specified.
- [x] Web/TUI/headless behavior is specified.
- [x] Renderer input contract is specified.
- [x] Unsupported renderer fallback is specified.
- [x] Invalid source-data fallback is specified.
- [x] Artifact-unavailable behavior is specified.
- [x] Initial renderer priority is specified.
- [x] No UI surface reads LangGraph Store or role filesystem directly.
- [x] Frontend components, TUI widgets, backend endpoints, renderer modules,
      fixtures, and tests are left out of scope for this docs phase.

## Completion Notes

Completed by creating `meta_harness/docs/specs/evaluation-analytics-renderer-contract.md` and registering it in `AD.md` §6 and §9. The renderer spec defines the Product Data Plane read path, renderer input, web/TUI/headless expectations, unsupported/invalid/stale/unavailable/denied fallback behavior, visibility handling, conformance expectations, and initial renderer priority: `scorecard`, `table`, `line_chart`, `radar_chart`, `heatmap`.
