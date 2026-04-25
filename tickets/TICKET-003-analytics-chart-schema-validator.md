# TICKET-003 — Implement Evaluation Analytics Chart Schema Validation Contract

## Status

Proposed

## Priority

P1 — backend contract prerequisite for analytics publication tools

## Owner

Developer + Evaluator

## Depends On

- `docs/specs/evaluation-analytics-chart-schemas.md`
- `docs/specs/harness-engineer-evaluation-analytics.md`
- TICKET-002 Project Data Plane migration

## Blocks

- `publish_analytics_view`
- `update_analytics_view`
- UI renderer contract
- Safe Python transform output path

## Problem

The Harness Engineer may choose from supported chart families and may prepare analytics source JSON directly or via sandboxed Python transforms. The UI must not ingest arbitrary agent-generated chart code or malformed JSON.

A deterministic schema-validation boundary is required before any analytics view is published.

## Goal

Implement or specify the backend validation layer for all supported `evaluation_analytics_views` chart schemas.

## Scope

Supported chart families:

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

## Required Design

### 1. Shared Envelope

Every analytics source JSON must validate:

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

Validation rules:

```txt
schema_version supported
view_type supported
analytics_kind supported
view_type compatible with analytics_kind
title non-empty
data object present
```

### 2. Per-Chart Validators

Implement validators for:

```txt
validate_radar_chart
validate_line_chart
validate_bar_chart
validate_stacked_bar_chart
validate_scatter_plot
validate_bubble_chart
validate_heatmap
validate_scorecard
validate_matrix
validate_table
```

### 3. Semantic Validation

Validators must reject:

```txt
NaN / Infinity numeric values
negative values where invalid
missing labels
empty required arrays
invalid status enums
mismatched axis/cell references
view_type mismatches
analytics_kind mismatches
oversized payloads beyond configured limit
```

### 4. Leakage-Guard Hook

Add a deterministic or pluggable guard boundary for labels/summaries.

At minimum, validators should flag obvious forbidden strings/fields if present:

```txt
heldout_example
hidden_rubric
judge_prompt
private_dataset_row
private_evaluation_instruction
raw_trace
```

This is not a complete privacy solution, but it prevents obvious schema misuse.

Developer-safe and stakeholder-visible views should require stricter validation.

### 5. Fixtures

Add valid and invalid fixtures for each chart family.

Example layout:

```txt
tests/fixtures/evaluation_analytics/
  radar_chart.valid.json
  radar_chart.invalid.missing_dimensions.json
  line_chart.valid.json
  line_chart.invalid.nan.json
  heatmap.valid.json
  heatmap.invalid.bad_cell_ref.json
  scorecard.valid.json
  scorecard.invalid.bad_status.json
```

### 6. Tests

Add conformance tests:

```txt
valid fixtures pass
invalid fixtures fail with actionable errors
all chart families enforce schema_version
view_type must match selected validator
analytics_kind compatibility enforced
numeric fields must be finite
developer_safe visibility rejects obvious private leakage markers
```

## Implementation Notes

Prefer Pydantic models or JSON Schema if consistent with the repo’s existing validation style.

The validation layer should return structured errors, not only strings:

```python
class ValidationErrorDetail(TypedDict):
    path: str
    code: str
    message: str
```

## Acceptance Criteria

- [ ] All 10 chart families have validators.
- [ ] Shared envelope validation exists.
- [ ] Fixture suite exists.
- [ ] Invalid fixtures produce actionable errors.
- [ ] Numeric finite-value validation exists.
- [ ] Compatibility between `analytics_kind` and `view_type` is enforced.
- [ ] Obvious private-leakage markers are rejected for `developer_safe` / `stakeholder_visible`.
- [ ] Validator is callable by future `publish_analytics_view`.
