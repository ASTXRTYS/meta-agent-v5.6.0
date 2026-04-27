# TICKET-003 — Define Evaluation Analytics Validation Contract

## Status

Completed — docs-phase contract

## Priority

P1 — product validation contract prerequisite for analytics publication tools

## Owner

Developer + Evaluator

## Depends On

- `meta_harness/docs/specs/evaluation-analytics-chart-schemas.md`
- `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md`
- `meta_harness/docs/specs/project-data-contracts.md`
- TICKET-002 Project Data Plane migration

## Blocks

- Future implementation ticket for analytics source validation
- `publish_analytics_view` implementation
- `update_analytics_view` implementation
- UI renderer implementation
- Safe Python transform output path implementation

## Problem

The Harness Engineer may choose from supported chart families and may prepare analytics source JSON directly or via sandboxed Python transforms. The UI must not ingest arbitrary agent-generated chart code or malformed JSON.

A deterministic schema-validation boundary is required before any analytics view is published.

## Goal

Define the validation contract future development must implement for all
supported `evaluation_analytics_views` chart schemas.

This ticket creates the validation boundary that future analytics publication
tools call before setting an analytics view to `render_status="valid"`.

## Docs-Phase Boundary

This ticket is a specification ticket, not an application-code implementation
ticket.

Do not create Python modules, fixtures, or tests in this phase. Define the
contract, validation responsibilities, expected callable boundary, fixture
expectations, and acceptance criteria that future development work must satisfy.

## Non-Goals

- Do not implement validator application code.
- Do not create actual fixture files or test files.
- Do not implement `publish_analytics_view`, `update_analytics_view`, or
  `render_analytics_snapshot`.
- Do not implement UI rendering.
- Do not implement Product Data Plane persistence.
- Do not implement role authorization or visibility promotion policy.
- Do not create a new analytics schema family beyond the chart families in
  `evaluation-analytics-chart-schemas.md`.
- Do not build a generalized privacy/redaction system. TICKET-003 specifies
  only deterministic obvious-leakage marker checks for analytics source JSON.

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

## Required Contract

### 1. Shared Envelope

Future validation must require every analytics source JSON to use the shared
envelope:

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

Future implementation should expose a backend-callable API equivalent to:

```python
validate_analytics_source(
    source: Mapping[str, Any],
    *,
    expected_view_type: SupportedViewType | None = None,
    expected_analytics_kind: AnalyticsKind | None = None,
    visibility: AnalyticsVisibility = "internal",
) -> ValidationResult
```

The exact module path, implementation library, and concrete class names are
future development decisions. Prefer the smallest maintainable design consistent
with the repo’s implementation style at that time.

### 2. Per-Chart Validation Responsibilities

Future implementation must define validation coverage for:

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

Validators should enforce the fields and semantics currently specified in
`evaluation-analytics-chart-schemas.md`. If a chart family lacks enough detail
for exhaustive validation, implement the conservative minimum that protects
renderer assumptions and document the gap in future implementation tests or
validator code.

Future implementation must define an explicit compatibility map between `analytics_kind` and allowed
`view_type` values, derived from `evaluation-analytics-chart-schemas.md` and
`project-data-contracts.md`. The map may allow more than one view type per
analytics kind when the specs support multiple renderings.

### 3. Semantic Validation

Future validators must reject:

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

Specify a deterministic obvious-leakage marker boundary for labels/summaries.

At minimum, future validators should flag obvious forbidden strings/fields if
present:

```txt
heldout_example
hidden_rubric
judge_prompt
private_dataset_row
private_evaluation_instruction
raw_trace
```

This is not a complete privacy solution, but it prevents obvious schema misuse.

For `developer_safe` and `stakeholder_visible` views, the future validator must
apply the deterministic marker guard to titles, descriptions, labels, summaries,
table cells, and other displayed strings. Full visibility authorization,
promotion policy, and redaction remain the responsibility of
publication/access-control layers.

### 5. Future Fixture Expectations

Future implementation should add valid and invalid fixtures for each chart
family. This ticket specifies fixture expectations only.

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

Fixture coverage should prioritize:

```txt
one valid example per chart family
shared envelope failures
view_type mismatch
analytics_kind mismatch
non-finite numeric values
empty required arrays
bad enum values
bad heatmap/matrix references
leakage marker rejection for developer_safe/stakeholder_visible
```

### 6. Future Conformance Test Expectations

Future implementation should add conformance tests covering:

```txt
valid fixtures pass
invalid fixtures fail with actionable errors
all chart families enforce schema_version
view_type must match selected validator
analytics_kind compatibility enforced
numeric fields must be finite
developer_safe visibility rejects obvious private leakage markers
```

## Future Implementation Guidance

Prefer Pydantic models, JSON Schema, or lightweight typed validators based on the
repo’s implementation style when development begins.

The future validation layer should return structured errors, not only strings:

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

Validation errors should be actionable for both backend developers and agents
producing analytics source JSON.

## Acceptance Criteria

- [x] All 10 chart families have required validation responsibilities specified.
- [x] Shared envelope validation contract is specified.
- [x] Fixture suite requirements are specified.
- [x] Invalid fixture expectations are specified.
- [x] Numeric finite-value validation is required.
- [x] Compatibility between `analytics_kind` and `view_type` is specified.
- [x] Obvious private-leakage marker checks are specified for `developer_safe` / `stakeholder_visible`.
- [x] Structured error and warning shape is specified.
- [x] Future validator callable boundary for `publish_analytics_view` is specified.
- [x] Application code, fixture files, test files, publication tools, UI
      rendering, persistence, role authorization, and generalized
      privacy/redaction are left out of scope for this docs phase.

## Completion Notes

Completed in `meta_harness/docs/specs/evaluation-analytics-chart-schemas.md` by adding the shared envelope validation contract, supported enums, compatibility map, per-chart required fields, semantic rules, deterministic leakage marker guard, future fixture expectations, future conformance expectations, and structured validation result shape. Cross-spec ownership is referenced from `project-data-contracts.md`.
