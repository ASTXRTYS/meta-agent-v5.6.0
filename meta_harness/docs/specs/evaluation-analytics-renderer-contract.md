---
doc_type: spec
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 User Interface Surface
  - AD §4 Project-Scoped Execution Environment
status: active
last_synced: 2026-04-27
owners: ["@Jason"]
---

# Evaluation Analytics Renderer Contract

> **Provenance:** Derived from `AD.md §6 Observability & Evaluation`, `§4 User Interface Surface`, and `§4 Project-Scoped Execution Environment`.
> **Status:** Active · **Last synced with AD:** 2026-04-27.
> **Consumers:** Web app, TUI, headless adapters, analytics schema validator, Project Records Layer implementation, Evaluator conformance review.

## 1. Purpose

This specification defines how first-party Meta Harness surfaces render `evaluation_analytics_views` product records.

The renderer contract is not a charting-library implementation contract. It defines the read path, input shape, fallback behavior, visibility handling, and initial renderer priority future implementation must preserve across web, TUI, and headless surfaces.

## 2. Source Of Truth

First-party surfaces render analytics from the Project Records Layer:

```txt
evaluation_analytics_views row
  -> data_ref
  -> analytics source data artifact
  -> source JSON validated against evaluation-analytics-chart-schemas.md
  -> renderer input
```

Surfaces must not infer analytics views from LangSmith links, role workspaces, LangGraph Store state, local files, or legacy trendline records.

## 3. Required Surfaces

### 3.1 Web App

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

Web renderers should provide visual charts when supported and graceful fallback cards when unsupported, invalid, stale, or unavailable.

### 3.2 TUI

Future TUI surfaces must support compact textual summaries for all chart families.

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

The TUI may render simple tables, status cards, sparklines, or text summaries. It is not required to match web visual fidelity.

### 3.3 Headless Adapters

Future headless adapters must support concise summaries, not full chart rendering.

Example:

```txt
Harness analytics updated: Candidate Scorecard
Status: valid
Summary: Candidate 2 improved grounding but regressed latency.
Open dashboard for chart.
```

Headless summaries must preserve visibility rules and must not include hidden source details beyond the caller's allowed view.

## 4. UI Read Path

All surfaces read through backend-owned operations:

```txt
list_evaluation_analytics_views(org_id, project_id, filters)
get_evaluation_analytics_view(org_id, project_id, analytics_view_id)
get_analytics_source_data(org_id, project_id, analytics_view_id)
```

No surface reads LangGraph Store directly.

No surface scans role filesystems for analytics views.

No surface reads LangSmith as the primary analytics-rendering substrate. LangSmith links are provenance locators, not chart source data.

## 5. Renderer Input Contract

Future renderers should receive an input equivalent to:

```python
class AnalyticsRendererInput(TypedDict):
    analytics_view: EvaluationAnalyticsView
    source_data: dict
```

The backend operation that prepares renderer input must:

```txt
1. Authorize the caller for the analytics view.
2. Load the evaluation_analytics_views row.
3. Resolve data_ref through the Project Records Layer or approved object/filesystem adapter.
4. Load analytics source JSON.
5. Validate source_data.schema_version.
6. Validate source_data.view_type matches analytics_view.recommended_view_type.
7. Validate source_data.analytics_kind matches analytics_view.analytics_kind.
8. Return renderer input or a structured unavailable/invalid response.
9. Write a project_data_events row for allowed, denied, or failed access.
```

Renderers must treat `analytics_view.render_status` as authoritative. A renderer may perform defensive validation of the source payload shape, but it must not silently promote invalid, unsupported, stale, or unavailable data into a valid chart.

## 6. Renderer Responsibilities

Future renderers must:

```txt
validate source_data.schema_version before rendering
validate source_data.view_type matches analytics_view.recommended_view_type
render supported view types using the chart-family schema contract
show unsupported views with graceful fallback
show invalid/stale/unavailable statuses visibly
respect visibility filters
never expose hidden source fields
avoid direct filesystem, LangGraph Store, or LangSmith reads
```

Renderer implementations may choose different visual libraries per surface, provided the contract above is preserved.

## 7. Fallback Behavior

### 7.1 Unsupported renderer

If a renderer does not support the requested view type:

```txt
show title
show summary
show analytics_kind
show recommended_view_type
show "Unsupported visualization type"
show source artifact link only if allowed
record access event
```

Unsupported renderer fallback must not drop the analytics view silently.

### 7.2 Invalid source data

If source data is invalid:

```txt
show title
show render_status = invalid
show "Invalid analytics source data"
show validation error summary to internal users
hide detailed validation errors from stakeholder-visible views
record failed render/access event
```

Detailed validation errors must not reveal private eval internals to Developer or stakeholder-visible surfaces.

### 7.3 Stale analytics view

If `render_status="stale"`:

```txt
show title
show summary
show "Analytics view may be outdated"
show stale reason if the caller is allowed to inspect it
continue to offer source/provenance links only when allowed
```

Stale views are excluded from default dashboard views unless explicitly requested.

### 7.4 Source artifact unavailable

If the source artifact cannot be loaded:

```txt
show "Analytics source unavailable"
record access event
mark stale or unavailable through backend policy when appropriate
do not silently drop analytics view
```

Surfaces must not fall back to scanning role filesystems or LangGraph Store state.

### 7.5 Denied by visibility policy

If caller visibility does not permit access:

```txt
return no private payload
record denied access event
show only generic unavailable/unauthorized state if the surface requires a placeholder
```

Denied reads must not reveal that a private analytics view exists unless the caller is allowed to know private summaries exist.

## 8. Initial Renderer Priority

Initial implementation priority:

```txt
1. scorecard
2. table
3. line_chart
4. radar_chart
5. heatmap
```

This order is chosen because scorecards and tables provide immediate product value with low visualization complexity, while line/radar/heatmap renderers cover the highest-value visual analytics families after the textual/card baseline.

Progressive support after the initial priority:

```txt
bar_chart
stacked_bar_chart
matrix
scatter_plot
bubble_chart
```

Schema support may exist before all visual renderers are implemented. Unsupported visual renderers must use the fallback behavior in this spec.

## 9. Relationship To Other Specs

`evaluation-analytics-chart-schemas.md` owns source JSON schemas, compatibility maps, validation responsibilities, leakage-marker validation, fixture expectations, and future validator callable shape.

`harness-engineer-evaluation-analytics.md` owns Harness Engineer responsibilities and analytics publication/update/snapshot operation contracts.

`project-data-contracts.md` owns product record schemas, read/write APIs, role authorization, tenant scoping, retention, and access-event auditing.

This spec owns renderer input, read path expectations for first-party surfaces, renderer fallback behavior, and renderer implementation priority.

## 10. Future Conformance Expectations

Future implementation should add behavioral and architectural conformance tests covering:

```txt
web/TUI/headless read analytics through backend operations
no first-party surface reads LangGraph Store for analytics rendering
no first-party surface scans role filesystems for analytics rendering
renderer rejects source_data.view_type mismatch
renderer rejects source_data.analytics_kind mismatch
unsupported view types use fallback display
invalid source data uses invalid fallback display
stale views show stale status
source-unavailable views are not silently dropped
visibility-denied reads return no private payload
initial supported renderers include scorecard, table, line_chart, radar_chart, heatmap
```

## 11. Non-Goals

This spec does not implement:

```txt
React components
TUI widgets
backend endpoints
renderer modules
charting-library adapters
fixture files
test files
Project Records Layer persistence
role authorization logic
```
