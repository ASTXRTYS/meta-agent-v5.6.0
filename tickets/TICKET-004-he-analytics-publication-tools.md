# TICKET-004 — Define Harness Engineer Analytics Publication Tool Contract

## Status

Completed — docs-phase contract

## Priority

P1 — product operation contract / HE capability

## Owner

Harness Engineer + Developer

## Depends On

- TICKET-002 Project Data Plane migration
- TICKET-003 chart schema validation contract
- `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md`
- `meta_harness/docs/specs/project-data-contracts.md`

## Blocks

- Harness Engineer prompt/skill authoring for analytics publication
- UI dashboard population through HE-published analytics
- EBDR-compatible optimizer feedback that may cite published analytics
- Future implementation tickets for analytics publication operations

## Problem

The Harness Engineer needs a bounded tool surface for publishing UI-renderable evaluation analytics. The tool surface must preserve HE judgment while enforcing deterministic product boundaries.

The HE should not publish arbitrary chart code. HE should publish structured analytics views that reference registered source artifacts and optionally LangSmith refs.

## Goal

Define the model-visible and backend-owned operation contracts for:

```txt
publish_analytics_view
update_analytics_view
render_analytics_snapshot
```

## Docs-Phase Boundary

This ticket is a specification ticket, not an application-code implementation
ticket.

Do not create Python modules, tool registrations, database code, UI code, or
tests in this phase. Define the product operation boundaries, model-visible
inputs, system-owned fields, backend responsibilities, and acceptance criteria
that future development work must satisfy.

The concrete module layout, function/class names, persistence implementation,
and tool-registration mechanism are future development decisions.

## Tool 1: `publish_analytics_view`

### Purpose

Publish a new UI-renderable evaluation analytics surface.

### Model-Visible Input

The eventual model-visible input should be equivalent to:

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

### System-Owned Fields

The backend, not the model, owns:

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

### Backend Steps

Future implementation must perform the equivalent of:

```txt
1. Resolve org_id/project_id from runtime context.
2. Validate caller is Harness Engineer or authorized owner.
3. Resolve data_ref.
4. Validate source artifacts exist.
5. Load analytics source JSON.
6. Validate chart schema.
7. Validate visibility policy.
8. Validate LangSmith refs if present.
9. Write evaluation_analytics_views row.
10. Write project_data_events row.
11. Return analytics_view_id, render_status, and any warnings.
```

## Tool 2: `update_analytics_view`

### Purpose

Update an existing analytics view, usually after new eval results or candidate comparisons.

### Model-Visible Input

The eventual model-visible input should be equivalent to:

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

### Rules

```txt
owner_agent cannot be changed
analytics_kind cannot be changed in v1
recommended_view_type cannot be changed in v1 unless explicitly allowed
updates must revalidate source data if data_ref changes
historical source artifacts remain in artifact history
```

## Tool 3: `render_analytics_snapshot`

### Purpose

Create a static artifact snapshot of an analytics view for reports, delivery
packages, or stakeholder summaries.

### Model-Visible Input

The eventual model-visible input should be equivalent to:

```python
class RenderAnalyticsSnapshotInput(TypedDict):
    analytics_view_id: str
    snapshot_title: str | None
    visibility: AnalyticsVisibility
    format: Literal["json", "markdown", "png", "svg"]  # supported output depends on renderer
```

### Rules

```txt
snapshot does not replace canonical analytics view
snapshot is registered as artifact_manifest.kind = "evaluation_analytics_snapshot"
snapshot references analytics_view_id
snapshot visibility cannot exceed source view visibility without PM/admin promotion
```

## Visibility Rules

Initial policy:

```txt
HE can publish he_private and internal analytics.
HE cannot directly publish stakeholder_visible unless policy later permits.
PM can promote internal analytics to stakeholder_visible.
developer_safe requires leakage validation.
```

## Acceptance Criteria

- [x] Publication operation contracts are written into specs.
- [x] Model-visible fields and system-owned fields are separated.
- [x] Backend validation steps are specified.
- [x] Visibility escalation policy is specified.
- [x] LangSmith refs are optional but supported.
- [x] `publish_analytics_view` requires valid analytics source data.
- [x] `update_analytics_view` preserves history.
- [x] `render_analytics_snapshot` registers artifact snapshot.
- [x] Developer-safe boundary is preserved.
- [x] Application code, tool registrations, database code, UI code, and tests are
      left out of scope for this docs phase.

## Completion Notes

Completed in `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md` by replacing the loose tooling section with backend-owned product operation contracts for `publish_analytics_view`, `update_analytics_view`, `render_analytics_snapshot`, and `mark_analytics_view_stale`. The spec now separates model-visible input from system-owned fields, requires schema/visibility/LangSmith validation before publication, preserves artifact history on update, and points live rendering behavior to `evaluation-analytics-renderer-contract.md`.
