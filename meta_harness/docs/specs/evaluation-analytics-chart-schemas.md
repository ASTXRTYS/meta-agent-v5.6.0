---
doc_type: spec
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 Project-Scoped Execution Environment
status: active
last_synced: 2026-04-27
owners: ["@Jason"]
---

# Evaluation Analytics Chart Schemas

> **Provenance:** Derived from `AD.md §6 Observability & Evaluation` and `§4 Project-Scoped Execution Environment`.
> **Status:** Active · **Last synced with AD:** 2026-04-27.
> **Consumers:** UI renderer, analytics schema validator, Harness Engineer analytics publication tools, Project Records Layer implementation.

## 1. Purpose

This document defines supported chart-family schemas and validation responsibilities for `evaluation_analytics_views`.

The Harness Engineer may recommend chart families, but the UI renders only supported schemas. Publication operations must validate analytics source JSON against this contract before setting `render_status="valid"`.

## 2. Shared Envelope

Every analytics source JSON must include the shared envelope.

```json
{
  "schema_version": 1,
  "view_type": "radar_chart",
  "analytics_kind": "success_criteria_profile",
  "title": "Target Harness Success Profile",
  "description": "Target success dimensions derived from architecture and eval design artifacts.",
  "data": {}
}
```

Required envelope validations:

```txt
schema_version is supported
view_type is supported
analytics_kind is supported
view_type is compatible with analytics_kind
title is non-empty
description, when present, is a display string
data is an object
```

Supported `schema_version` values:

```txt
1
```

Supported `view_type` values:

```txt
radar_chart
line_chart
bar_chart
stacked_bar_chart
scatter_plot
bubble_chart
heatmap
scorecard
matrix
table
```

Supported `analytics_kind` values:

```txt
success_criteria_profile
eval_coverage_matrix
rubric_weight_distribution
dataset_composition
judge_profile_matrix
risk_map
eval_readiness_scorecard
candidate_scorecard
optimization_timeline
capability_actual_vs_target
failure_cluster_summary
cost_latency_tradeoff
regression_report
```

Compatibility map:

| `analytics_kind` | Allowed `view_type` values |
|---|---|
| `success_criteria_profile` | `radar_chart`, `scorecard` |
| `eval_coverage_matrix` | `heatmap`, `matrix`, `table` |
| `rubric_weight_distribution` | `stacked_bar_chart`, `bar_chart`, `table` |
| `dataset_composition` | `bar_chart`, `stacked_bar_chart`, `table` |
| `judge_profile_matrix` | `matrix`, `table` |
| `risk_map` | `bubble_chart`, `scatter_plot`, `table` |
| `eval_readiness_scorecard` | `scorecard`, `table` |
| `candidate_scorecard` | `scorecard`, `table` |
| `optimization_timeline` | `line_chart`, `table` |
| `capability_actual_vs_target` | `radar_chart`, `bar_chart`, `scorecard` |
| `failure_cluster_summary` | `bar_chart`, `stacked_bar_chart`, `table` |
| `cost_latency_tradeoff` | `scatter_plot`, `bubble_chart`, `line_chart`, `table` |
| `regression_report` | `table`, `bar_chart`, `line_chart`, `scorecard` |

## 3. Radar Chart

Use for success criteria profiles, capability actual-vs-target views, and weighted dimension views.

```json
{
  "schema_version": 1,
  "view_type": "radar_chart",
  "analytics_kind": "success_criteria_profile",
  "title": "Target Harness Success Profile",
  "data": {
    "scale": {"min": 0, "max": 5},
    "dimensions": [
      {
        "key": "tool_discipline",
        "label": "Tool Discipline",
        "target": 5,
        "actual": null,
        "weight": 0.2
      },
      {
        "key": "grounding",
        "label": "Grounding",
        "target": 5,
        "actual": null,
        "weight": 0.25
      }
    ]
  }
}
```

Pre-development analytics may set `actual` to `null`.

## 4. Line Chart

Use for optimization timelines, pass-rate movement, cost movement, latency movement, and other metric series.

```json
{
  "schema_version": 1,
  "view_type": "line_chart",
  "analytics_kind": "optimization_timeline",
  "title": "Harness Pass Rate Over Candidate Iterations",
  "data": {
    "x_axis": {"key": "iteration", "label": "Iteration"},
    "series": [
      {
        "key": "harness_pass_rate",
        "label": "Harness Pass Rate",
        "unit": "percent",
        "points": [
          {"x": "candidate_1", "y": 0.62},
          {"x": "candidate_2", "y": 0.74}
        ]
      }
    ]
  }
}
```

## 5. Heatmap

Use for eval coverage matrices and requirement/category coverage views.

```json
{
  "schema_version": 1,
  "view_type": "heatmap",
  "analytics_kind": "eval_coverage_matrix",
  "title": "Requirement Coverage By Eval Category",
  "data": {
    "x_axis": {
      "label": "Eval Categories",
      "values": ["routing", "grounding", "tool_use"]
    },
    "y_axis": {
      "label": "Requirements",
      "values": ["R1", "R2", "R3"]
    },
    "cells": [
      {"x": "routing", "y": "R1", "value": 1.0, "label": "covered"},
      {"x": "grounding", "y": "R2", "value": 0.5, "label": "partial"}
    ]
  }
}
```

## 6. Scorecard

Use for eval readiness, candidate scorecards, quality gates, and stakeholder-friendly summaries.

```json
{
  "schema_version": 1,
  "view_type": "scorecard",
  "analytics_kind": "eval_readiness_scorecard",
  "title": "Eval Readiness Scorecard",
  "data": {
    "cards": [
      {
        "metric_key": "eval_readiness",
        "label": "Eval Readiness",
        "value": 0.86,
        "target": 0.8,
        "unit": "ratio",
        "status": "passing"
      },
      {
        "metric_key": "heldout_coverage",
        "label": "Held-out Coverage",
        "value": 0.42,
        "target": 0.6,
        "unit": "ratio",
        "status": "at_risk"
      }
    ]
  }
}
```

Allowed status values:

```txt
passing
at_risk
failing
unknown
```

## 7. Bar Chart

Use for category totals, failure cluster counts, dataset composition, and score breakdowns.

```json
{
  "schema_version": 1,
  "view_type": "bar_chart",
  "analytics_kind": "failure_cluster_summary",
  "title": "Failure Clusters",
  "data": {
    "x_axis": {"key": "cluster", "label": "Failure Cluster"},
    "y_axis": {"key": "count", "label": "Count"},
    "bars": [
      {"x": "tool_misuse", "y": 12, "label": "Tool Misuse"},
      {"x": "grounding", "y": 7, "label": "Grounding"}
    ]
  }
}
```

## 8. Stacked Bar Chart

Use for rubric weights, dataset composition by split/category, and failure distribution over candidates.

```json
{
  "schema_version": 1,
  "view_type": "stacked_bar_chart",
  "analytics_kind": "rubric_weight_distribution",
  "title": "Rubric Weight Distribution",
  "data": {
    "x_axis": {"key": "rubric", "label": "Rubric"},
    "stacks": ["grounding", "tool_discipline", "artifact_quality"],
    "bars": [
      {
        "x": "overall_quality",
        "segments": {
          "grounding": 0.35,
          "tool_discipline": 0.4,
          "artifact_quality": 0.25
        }
      }
    ]
  }
}
```

## 9. Scatter Plot

Use for cost/latency/quality tradeoffs.

```json
{
  "schema_version": 1,
  "view_type": "scatter_plot",
  "analytics_kind": "cost_latency_tradeoff",
  "title": "Cost vs Quality",
  "data": {
    "x_axis": {"key": "cost_per_run", "label": "Cost Per Run", "unit": "usd"},
    "y_axis": {"key": "quality_score", "label": "Quality Score", "unit": "ratio"},
    "points": [
      {"id": "candidate_1", "x": 0.21, "y": 0.72, "label": "Candidate 1"},
      {"id": "candidate_2", "x": 0.28, "y": 0.84, "label": "Candidate 2"}
    ]
  }
}
```

## 10. Bubble Chart

Use for risk maps or multidimensional cost/quality/risk views.

```json
{
  "schema_version": 1,
  "view_type": "bubble_chart",
  "analytics_kind": "risk_map",
  "title": "Harness Risk Map",
  "data": {
    "x_axis": {"key": "likelihood", "label": "Likelihood"},
    "y_axis": {"key": "impact", "label": "Impact"},
    "size_key": "priority",
    "bubbles": [
      {
        "id": "reward_hacking",
        "x": 0.7,
        "y": 0.95,
        "size": 0.9,
        "label": "Reward Hacking"
      }
    ]
  }
}
```

## 11. Matrix

Use for judge profile matrices and rubric/eval mappings.

```json
{
  "schema_version": 1,
  "view_type": "matrix",
  "analytics_kind": "judge_profile_matrix",
  "title": "Judge Profile Matrix",
  "data": {
    "columns": ["grounding", "tool_discipline", "artifact_quality"],
    "rows": [
      {
        "key": "judge_grounding_v1",
        "label": "Grounding Judge v1",
        "values": {
          "grounding": "primary",
          "tool_discipline": "none",
          "artifact_quality": "secondary"
        }
      }
    ]
  }
}
```

## 12. Table

Use for general fallback rendering and dense structured summaries.

```json
{
  "schema_version": 1,
  "view_type": "table",
  "analytics_kind": "regression_report",
  "title": "Regression Report",
  "data": {
    "columns": [
      {"key": "metric", "label": "Metric"},
      {"key": "previous", "label": "Previous"},
      {"key": "current", "label": "Current"},
      {"key": "change", "label": "Change"}
    ],
    "rows": [
      {
        "metric": "tool_discipline",
        "previous": 0.82,
        "current": 0.76,
        "change": "regressed"
      }
    ]
  }
}
```

## 13. Validation Rules

All schemas must be validated before publication. Publication operations must not set `render_status="valid"` unless source data resolves, passes the shared envelope rules, matches the target `evaluation_analytics_views` record fields, passes the chart-family rules below, and satisfies the requested visibility boundary.

Future implementation should expose a backend-callable boundary equivalent to:

```python
validate_analytics_source(
    source: Mapping[str, Any],
    *,
    expected_view_type: SupportedViewType | None = None,
    expected_analytics_kind: AnalyticsKind | None = None,
    visibility: AnalyticsVisibility = "internal",
) -> ValidationResult
```

The exact module path, implementation library, and concrete class names are future development decisions.

### 13.1 Shared Validation Result Shape

The validation layer must return structured diagnostics:

```python
class ValidationErrorDetail(TypedDict):
    path: str
    code: str
    message: str

class ValidationWarningDetail(TypedDict):
    path: str
    code: str
    message: str

class ValidationResult(TypedDict):
    valid: bool
    errors: list[ValidationErrorDetail]
    warnings: list[ValidationWarningDetail]
```

Errors must be actionable for backend developers and for agents producing analytics source JSON. Warnings may flag non-blocking rendering or quality issues, but warnings must not allow invalid source data to be published as valid.

### 13.2 Per-Chart Required Fields

| `view_type` | Required `data` fields | Required child fields |
|---|---|---|
| `radar_chart` | `scale`, `dimensions` | `scale.min`, `scale.max`; each dimension has `key`, `label`, `target`, `actual`, `weight` |
| `line_chart` | `x_axis`, `series` | `x_axis.key`, `x_axis.label`; each series has `key`, `label`, `points`; each point has `x`, `y` |
| `heatmap` | `x_axis`, `y_axis`, `cells` | axis `label` and `values`; each cell has `x`, `y`, `value` |
| `scorecard` | `cards` | each card has `metric_key`, `label`, `value`, `target`, `status` |
| `bar_chart` | `x_axis`, `y_axis`, `bars` | axis `key` and `label`; each bar has `x`, `y`, `label` |
| `stacked_bar_chart` | `x_axis`, `stacks`, `bars` | each bar has `x`, `segments`; every segment key appears in `stacks` |
| `scatter_plot` | `x_axis`, `y_axis`, `points` | axis `key` and `label`; each point has `id`, `x`, `y`, `label` |
| `bubble_chart` | `x_axis`, `y_axis`, `size_key`, `bubbles` | each bubble has `id`, `x`, `y`, `size`, `label` |
| `matrix` | `columns`, `rows` | each row has `key`, `label`, `values`; value keys must be declared columns |
| `table` | `columns`, `rows` | each column has `key`, `label`; each row may only use declared column keys plus implementation-owned metadata keys |

### 13.3 Semantic Rules

Validators must reject:

```txt
NaN and Infinity numeric values
negative values where the chart family requires non-negative values
empty required arrays
missing labels for displayed dimensions, series, cards, bars, points, bubbles, rows, or columns
invalid scorecard status values
heatmap cells whose x/y references do not exist in axis values
matrix row values whose keys do not exist in columns
stacked bar segment keys not declared in stacks
view_type mismatches against expected_view_type
analytics_kind mismatches against expected_analytics_kind
analytics_kind/view_type pairs not present in the compatibility map
payloads above the configured product limit
```

Allowed scorecard status values:

```txt
passing
at_risk
failing
unknown
```

### 13.4 Deterministic Leakage Marker Guard

The validation layer must provide a deterministic obvious-leakage marker check for display strings when `visibility` is `developer_safe` or `stakeholder_visible`.

Forbidden markers include:

```txt
heldout_example
hidden_rubric
judge_prompt
private_dataset_row
private_evaluation_instruction
raw_trace
private_trace
private_he_reasoning
```

The guard applies to titles, descriptions, labels, summaries, table cells, row labels, column labels, series labels, card labels, point labels, bubble labels, and other displayed strings. This is not a generalized privacy or redaction system; publication and access-control layers still own visibility authorization and promotion policy.

### 13.5 Future Fixture Expectations

Future implementation should add valid and invalid fixtures for each chart family. This spec defines fixture expectations only.

Expected fixture coverage:

```txt
one valid example per chart family
shared envelope failures
unsupported schema_version
view_type mismatch
analytics_kind mismatch
analytics_kind/view_type incompatibility
non-finite numeric values
empty required arrays
bad enum values
bad heatmap/matrix references
bad stacked-bar segment references
leakage marker rejection for developer_safe/stakeholder_visible
```

### 13.6 Future Conformance Test Expectations

Future implementation should add behavioral and architectural conformance tests covering:

```txt
valid fixtures pass
invalid fixtures fail with actionable errors
all chart families enforce schema_version
view_type must match selected validator
analytics_kind compatibility is enforced
numeric fields must be finite
developer_safe and stakeholder_visible reject obvious private leakage markers
publish_analytics_view cannot mark invalid source data valid
renderer implementations do not bypass validation status
```
