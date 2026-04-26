# TICKET-004 — Specify Harness Engineer Analytics Publication Tools

## Status

Proposed

## Priority

P1 — tool contract / HE capability

## Owner

Harness Engineer + Developer

## Depends On

- TICKET-002 Project Data Plane migration
- TICKET-003 chart schema validation contract
- `meta_harness/docs/specs/harness-engineer-evaluation-analytics.md`

## Blocks

- Harness Engineer prompt/skill authoring for analytics publication
- UI dashboard population through HE-published analytics
- Developer-safe feedback packet derivation from analytics evidence

## Problem

The Harness Engineer needs a bounded tool surface for publishing UI-renderable evaluation analytics. The tool surface must preserve HE judgment while enforcing deterministic product boundaries.

The HE should not publish arbitrary chart code. HE should publish structured analytics views that reference registered source artifacts and optionally LangSmith refs.

## Goal

Define concrete model-visible and backend-owned tool contracts for:

```txt
publish_analytics_view
update_analytics_view
render_analytics_snapshot
```

## Tool 1: `publish_analytics_view`

### Purpose

Publish a new UI-renderable evaluation analytics surface.

### Model-Visible Input

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

Tool helper populates:

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

Create a static artifact snapshot of an analytics view for reports, delivery packets, or stakeholder summaries.

### Model-Visible Input

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

- [ ] Tool contracts are written into specs.
- [ ] Model-visible fields and system-owned fields are separated.
- [ ] Backend validation steps are specified.
- [ ] Visibility escalation policy is specified.
- [ ] LangSmith refs are optional but supported.
- [ ] `publish_analytics_view` requires valid analytics source data.
- [ ] `update_analytics_view` preserves history.
- [ ] `render_analytics_snapshot` registers artifact snapshot.
- [ ] Developer-safe boundary is preserved.
