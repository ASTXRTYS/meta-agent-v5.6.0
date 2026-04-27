---
doc_type: spec
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 Project-Scoped Execution Environment
status: active
last_synced: 2026-04-27
owners: ["@Jason"]
---

# Harness Engineer Evaluation Analytics Specification

> **Provenance:** Derived from `AD.md §6 Observability & Evaluation` and `§4 Project-Scoped Execution Environment`.
> **Status:** Active · **Last synced with AD:** 2026-04-27.
> **Consumers:** Harness Engineer, PM surface, UI analytics renderer, Project Data Plane implementation, Developer-safe feedback pipeline.

## 1. Purpose

This specification defines the Harness Engineer’s visual analytics capability. The goal is to give the Harness Engineer a bounded, auditable way to publish UI-renderable analytics surfaces derived from evaluation artifacts, success criteria, rubrics, datasets, judge profiles, risk maps, LangSmith eval results, failure-mode analysis, and optimization findings.

This is not a generic charting feature. It is a harness-engineering capability for externalizing the Harness Engineer’s evaluation model and empirical findings into the product surface.

## 2. Baseline Harness Engineer Responsibilities

The Harness Engineer is responsible for:

```txt
Harness Engineer
  1. Constructs the evaluation program
  2. Defines success dimensions and quality gates
  3. Defines visual analytics views for the evaluation program
  4. Publishes UI-renderable analytics surfaces
  5. Runs or receives eval results
  6. Interprets deltas, regressions, and failure modes
  7. Updates analytics surfaces with empirical results
  8. Emits Developer-safe optimization feedback
```

## 3. Pre-Development Analytics

Before the Developer/generator begins implementing a target harness, the Harness Engineer receives architecture/specification artifacts and constructs the evaluation program.

The Harness Engineer may publish analytics views before any target harness has been evaluated.

Examples:

| Analytics kind               | Purpose                                                     | Recommended visualization                 |
| ---------------------------- | ----------------------------------------------------------- | ----------------------------------------- |
| `success_criteria_profile`   | Shows the target profile of success dimensions              | `radar_chart`, `scorecard`                |
| `eval_coverage_matrix`       | Shows how eval cases cover requirements                     | `heatmap`, `matrix`, `table`              |
| `rubric_weight_distribution` | Shows how scoring weights are allocated                     | `stacked_bar_chart`, `bar_chart`          |
| `dataset_composition`        | Shows public/held-out/category composition                  | `bar_chart`, `stacked_bar_chart`, `table` |
| `judge_profile_matrix`       | Shows which judges evaluate which criteria                  | `matrix`, `table`                         |
| `risk_map`                   | Shows expected failure risks and impact                     | `bubble_chart`, `scatter_plot`, `table`   |
| `eval_readiness_scorecard`   | Shows whether the eval program is ready to gate development | `scorecard`, `table`                      |

These analytics are part of the Harness Engineer’s context construction. They are not merely decorative dashboard widgets.

## 4. Post-Eval Analytics

After candidate harnesses are evaluated, the Harness Engineer may update or publish empirical analytics views.

Examples:

| Analytics kind                | Purpose                                            | Recommended visualization                    |
| ----------------------------- | -------------------------------------------------- | -------------------------------------------- |
| `candidate_scorecard`         | Shows candidate performance against thresholds     | `scorecard`, `table`                         |
| `optimization_timeline`       | Shows metric movement across candidates/iterations | `line_chart`                                 |
| `capability_actual_vs_target` | Shows candidate capability vs target profile       | `radar_chart`, `bar_chart`                   |
| `failure_cluster_summary`     | Shows recurring failure categories                 | `bar_chart`, `stacked_bar_chart`, `table`    |
| `cost_latency_tradeoff`       | Shows quality/cost/latency tradeoffs               | `scatter_plot`, `bubble_chart`, `line_chart` |
| `regression_report`           | Shows improvements/regressions between candidates  | `table`, `bar_chart`, `line_chart`           |

## 5. Supported Chart Families

The Harness Engineer may only publish analytics views using supported chart families.

V1 supported families:

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

No arbitrary custom chart code is accepted as a canonical UI output.

The UI may progressively implement renderers. Schema support may exist before all renderers are visually polished. Renderer implementation priority and fallback behavior are owned by `docs/specs/evaluation-analytics-renderer-contract.md`.

## 6. Storage Model

Analytics views use a dual storage model:

```txt
analytics source data = artifact
published analytics view = product record
```

The Harness Engineer writes source analytics data as a file, usually JSON, to the working filesystem. That file is registered as an artifact. The published analytics view is a Product Data Plane record pointing to that artifact.

This gives the Harness Engineer durable local context while giving the UI a stable product record to render.

## 7. Product Data Plane Record

Canonical record family: `evaluation_analytics_views`.

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

## 8. Product Operation Contracts

The canonical analytics operations are backend-owned product operations. Future model-visible tools may expose these operations to Harness Engineer or Evaluator agents, but agents do not write product database rows directly and do not bypass schema validation.

### 8.1 `publish_analytics_view`

The Harness Engineer publishes a view after creating and registering analytics source data.

Model-visible input must be equivalent to:

```python
class PublishAnalyticsViewInput(TypedDict):
    title: str
    phase: ProjectPhase
    analytics_kind: AnalyticsKind
    recommended_view_type: SupportedViewType
    visibility: AnalyticsVisibility
    data_ref: str
    data_ref_kind: Literal["artifact_id", "object_store_key", "filesystem_path"]
    source_artifact_ids: list[str]
    summary: str
    langsmith_dataset_id: str | None
    langsmith_experiment_id: str | None
    langsmith_project_name: str | None
    langsmith_run_id: str | None
    langsmith_trace_url: str | None
```

The backend owns:

```txt
org_id
project_id
analytics_view_id
owner_agent
handoff_id
created_at
updated_at
schema_version
render_status
trace_context
```

The backend must:

```txt
1. Resolve org_id, project_id, thread identity, role_name, and trace_context from runtime context.
2. Validate caller is Harness Engineer, Evaluator, or an authorized system analytics helper.
3. Resolve data_ref through the Product Data Plane or approved object/filesystem adapter.
4. Validate every source_artifact_id exists and is allowed for the caller.
5. Load analytics source JSON.
6. Validate source JSON against evaluation-analytics-chart-schemas.md.
7. Validate recommended_view_type matches source_data.view_type.
8. Validate analytics_kind matches source_data.analytics_kind.
9. Validate visibility policy, including Developer-safe leakage marker checks when applicable.
10. Validate LangSmith refs when present and preserve them as locators.
11. Insert evaluation_analytics_views.
12. Write a project_data_events audit row.
13. Return analytics_view_id, render_status, and structured warnings.
```

`publish_analytics_view` must not set `render_status="valid"` unless source data resolves, validates, and satisfies the requested visibility policy.

### 8.2 `update_analytics_view`

Updates a previously published analytics view by pointing it to a new source data artifact or by changing supported metadata.

Model-visible input must be equivalent to:

```python
class UpdateAnalyticsViewInput(TypedDict):
    analytics_view_id: str
    title: str | None
    visibility: AnalyticsVisibility | None
    data_ref: str | None
    data_ref_kind: Literal["artifact_id", "object_store_key", "filesystem_path"] | None
    source_artifact_ids: list[str] | None
    summary: str | None
    langsmith_dataset_id: str | None
    langsmith_experiment_id: str | None
    langsmith_project_name: str | None
    langsmith_run_id: str | None
    langsmith_trace_url: str | None
```

Rules:

```txt
owner_agent cannot be changed
analytics_kind cannot be changed in v1
recommended_view_type cannot be changed in v1 unless a later contract explicitly allows it
source data must be revalidated when data_ref or source_artifact_ids change
visibility promotion must re-run visibility policy and leakage checks
historical source artifacts remain available through artifact history
updates write project_data_events audit rows
```

### 8.3 `render_analytics_snapshot`

Creates a static snapshot artifact for reports, delivery packages, or stakeholder updates.

Model-visible input must be equivalent to:

```python
class RenderAnalyticsSnapshotInput(TypedDict):
    analytics_view_id: str
    snapshot_title: str | None
    visibility: AnalyticsVisibility
    format: Literal["json", "markdown", "png", "svg"]
```

Rules:

```txt
snapshot does not replace canonical analytics view
source analytics view must be readable by the caller
source analytics view must be valid or the snapshot must explicitly encode invalid/stale status
snapshot is registered as artifact_manifest.kind = "evaluation_analytics_snapshot"
snapshot references analytics_view_id
snapshot visibility cannot exceed source view visibility without PM/admin promotion
snapshot generation writes a project_data_events audit row
```

Renderer behavior for live UI surfaces and fallback display is specified in `docs/specs/evaluation-analytics-renderer-contract.md`.

### 8.4 `mark_analytics_view_stale`

System, Harness Engineer, or Evaluator callers may mark a view stale when the source artifact, schema version, LangSmith experiment reference, or source analysis becomes outdated.

Rules:

```txt
stale status preserves the analytics_view_id
stale status does not delete source artifacts
stale views are excluded from default dashboard views unless explicitly requested
stale status changes write project_data_events audit rows
```

## 9. Python Transform Policy

The Harness Engineer may use Python as a sandboxed data-preparation step.

Allowed:

```txt
HE writes Python transform
  -> reads eval artifacts / mirrored evidence
  -> computes chart-ready JSON
  -> writes analytics source JSON to disk
  -> registers it as an artifact
  -> calls publish_analytics_view
```

Not allowed:

```txt
HE writes arbitrary custom UI component
HE publishes arbitrary chart code as canonical UI output
HE bypasses schema validation
HE exposes private eval data through chart labels/summaries
```

The canonical UI contract remains structured JSON validated against supported chart schemas.

## 10. Visibility Policy

Policy:

| Visibility            | Meaning                                                             |
| --------------------- | ------------------------------------------------------------------- |
| `he_private`          | Only Harness Engineer, PM/internal privileged surfaces may inspect  |
| `evaluator_private`   | Only Evaluator, PM/internal privileged surfaces may inspect         |
| `internal`            | Internal project team visibility, not stakeholder-facing by default |
| `developer_safe`      | Safe to expose to Developer without private eval leakage            |
| `stakeholder_visible` | Safe for client/user-facing dashboard/reporting                     |

Decision:

```txt
HE may publish internal analytics.
PM decides what becomes stakeholder-visible.
```

Future policy may refine promotion rules, but v1 implementation must preserve this visibility boundary.

## 11. Developer-Safe Boundary

The Developer must not receive hidden eval internals.

Analytics and feedback must not expose:

```txt
held-out examples
hidden rubrics
judge prompts
private dataset rows
private evaluation instructions
raw private trace content
private HE reasoning intended only for diagnosis
```

Developer-safe feedback should describe failure categories, behavioral deltas, and remediation directions without leaking private evaluator contracts.

## 12. Relationship To LangSmith

LangSmith is the source-of-truth for eval execution when evals are run through LangSmith.

Meta Harness records should reference LangSmith entities when applicable:

```txt
dataset
experiment/session
run
trace
feedback
comparison URL
```

Exact LangSmith SDK/CLI capabilities and identifiers must be source-audited before final implementation.

This spec intentionally does not finalize the LangSmith tool surface yet.
