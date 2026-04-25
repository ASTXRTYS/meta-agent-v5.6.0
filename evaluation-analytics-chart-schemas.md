## 1. Purpose

This document defines supported chart-family schemas for `evaluation_analytics_views`.

The Harness Engineer may recommend chart families, but the UI renders only supported schemas.

## 2. Shared Envelope

Every analytics source JSON should include a shared envelope.

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

All schemas must be validated before publication.

Required validations:

```txt
schema_version is supported
view_type matches evaluation_analytics_views.recommended_view_type
analytics_kind matches evaluation_analytics_views.analytics_kind
required fields for view_type exist
numeric fields are finite numbers
labels do not contain private eval leakage
source artifacts exist
LangSmith refs exist when required
visibility policy is satisfied
```
