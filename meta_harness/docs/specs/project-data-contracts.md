---
doc_type: spec
derived_from:
  - AD §4 PM Session And Project Entry Model
  - AD §4 LangGraph Project Coordination Graph
  - AD §4 Project-Scoped Execution Environment
  - AD §6 Observability & Evaluation
  - AD §8 Security / Privacy / Compliance
status: active
last_synced: 2026-04-27
owners: ["@Jason"]
---

# Project Data Plane Specification

> **Provenance:** Derived from `AD.md §4 PM Session And Project Entry Model`, `§4 LangGraph Project Coordination Graph`, `§4 Project-Scoped Execution Environment`, `§6 Observability & Evaluation`, and `§8 Security / Privacy / Compliance`.
> **Status:** Active · **Last synced with AD:** 2026-04-27 (created for Ticket 6 / `OQ-H5` closure; renamed from project-data-plane 2026-04-26; synced analytics validation/publication/renderer spec links 2026-04-27).
> **Consumers:** Developer (backend/data-access implementation), PM session tools, web/TUI/headless surfaces, Harness Engineer, Evaluator, UI analytics renderer, access-policy conformance tests.

## 1. Purpose

The Project Data Plane is the product-owned contract for durable project facts
that must be visible across `pm_session` threads, project threads, the web app,
TUI, and headless ingress adapters. It owns the project registry, artifact
manifest, UI-renderable evaluation analytics views, access audit trail, and
read-only snapshot records.

This spec replaces the earlier LangGraph `Store` namespaces previously listed
in `docs/specs/pcg-data-contracts.md`. PCG state still owns deterministic
routing state (`handoff_log`, `current_agent`, `current_phase`,
`acceptance_stamps`). The Project Data Plane owns cross-surface product records.

`evaluation_analytics_views` is the canonical product record family for
published evaluation analytics surfaces. `optimization_timeline` is supported
only as an `analytics_kind` inside this record family; it is not a standalone
Product Data Plane primitive.

## 2. SDK Alignment

LangGraph `Store` remains useful for cross-thread memory, queues, and caches, but
it is not the authoritative project data plane:

- `BaseStore` is a hierarchical key-value API with `get`, `search`, `put`,
  `delete`, and `list_namespaces`; it has no per-role or per-field permission
  contract (`.venv/lib/python3.11/site-packages/langgraph/store/base/__init__.py:700-929`).
- `InMemoryStore` loses data when the process exits and points persistent use
  toward database-backed stores (`.venv/lib/python3.11/site-packages/langgraph/store/memory/__init__.py:91-93`).
- Deep Agents `StoreBackend` validates namespace strings and exposes Store
  items as files; namespace resolution is not an authorization model
  (`.reference/libs/deepagents/deepagents/backends/store.py:102-150`).
- Open SWE uses LangGraph Store for a narrow active-thread message queue
  (`.reference/open-swe/agent/webapp.py:416-458`) consumed by before-model
  middleware (`.reference/open-swe/agent/middleware/check_message_queue.py:48-94`),
  while execution resources such as sandbox IDs and credentials are anchored in
  thread metadata and backend APIs (`.reference/open-swe/agent/server.py:192-263`).
- LangSmith traces support searchable metadata on runs
  (`.venv/lib/python3.11/site-packages/langsmith/run_trees.py:140-152`,
  `run_trees.py:415-420`); data-plane operations must attach the same
  correlation identifiers to trace metadata and access-event rows.

## 3. Source Of Truth

| Record family | Authoritative substrate | Non-authoritative mirrors |
|---|---|---|
| Project registry | Product database table `project_registry` | LangGraph thread metadata, LangGraph Store cache |
| Artifact manifest metadata | Product database table `artifact_manifest` | Role filesystem directory listings, LangGraph Store cache |
| Artifact bytes/content | Role filesystem, sandbox/devbox filesystem, object storage, or external URL named by manifest `content_ref` | Manifest metadata |
| Evaluation analytics views | Product database table `evaluation_analytics_views` | UI cache, LangGraph Store cache, rendered snapshot artifacts |
| Data-plane access audit | Product database table `project_data_events` | LangSmith metadata |
| Read-only live snapshots | Product database table `project_snapshots` plus generated artifact rows | Sandbox/devbox filesystem at capture time |

LangGraph Store may cache derived slices for low-latency agent reads, but every
cache entry is write-through from the product database and invalidatable. A cache
miss must read the product database. A cache hit must not bypass product
authorization.

## 4. Common Fields

Every Project Data Plane row has these fields:

```python
class DataPlaneBase(TypedDict):
    schema_version: Literal[1]
    org_id: str
    project_id: str
    created_at: str  # RFC3339 UTC
    updated_at: str  # RFC3339 UTC
```

Rules:

- `org_id` is mandatory on every row and is part of every primary or unique key.
- `project_id` is mandatory except for organization-level query indexes.
- `schema_version` is mandatory and starts at `1`.
- `created_at` and `updated_at` are system-owned. Agents and clients never
  supply them directly.

## 5. Schemas

### 5.1 `project_registry`

Primary key: `(org_id, project_id)`.

```python
class ProjectRegistryRecord(DataPlaneBase):
    project_thread_id: str
    pm_session_thread_id: str | None
    created_by_user_id: str | None
    current_phase: ProjectPhase
    current_agent: AgentName | None
    last_handoff_id: str | None
    last_handoff_at: str | None
    artifact_count: int
    execution_environment_id: str | None
    execution_mode: Literal["managed_sandbox", "external_devbox", "local_workspace"]
    local_workspace_snapshot_opt_in: bool
    status: Literal["active", "paused", "completed", "archived", "deleted"]
    archived_at: str | None
    deleted_at: str | None
```

Indexes:

- `(org_id, status, updated_at desc)`
- `(org_id, pm_session_thread_id, updated_at desc)`
- `(org_id, project_thread_id)` unique

`project_registry` is the source of truth for project listing, project status,
PM-session spawn lineage, and project-thread lookup by durable project identity.
LangGraph thread metadata is a runtime hint and must be repaired from this table
when it drifts.

### 5.2 `artifact_manifest`

Primary key: `(org_id, project_id, artifact_id, version)`.

```python
class ArtifactManifestRecord(DataPlaneBase):
    artifact_id: str
    version: int
    kind: Literal[
        "prd",
        "eval_suite",
        "research_bundle",
        "design_spec",
        "plan",
        "phase_deliverable",
        "final_product",
        "dataset",
        "rubric",
        "analytics_source_data",
        "evaluation_analytics_snapshot",
        "experiment_summary",
        "run_index",
        "filtered_run_index",
        "trace_bundle",
        "trace_summary_bundle",
        "failure_cluster_report",
        "candidate_comparison_report",
        "live_snapshot",
        "repo_evidence",
        "check_log",
    ]
    title: str
    owner_agent: AgentName
    visibility: Literal[
        "stakeholder_visible",
        "developer_safe",
        "internal",
        "role_private",
        "he_private",
        "evaluator_private",
    ]
    content_ref: str
    content_ref_kind: Literal["role_filesystem_path", "sandbox_path", "object_store_key", "external_url"]
    content_status: Literal["available", "unavailable", "deleted"]
    size_bytes: int | None
    checksum_sha256: str | None
    handoff_id: str | None
    langsmith_run_id: str | None
    created_by_agent: AgentName | Literal["system"] | None
    deleted_at: str | None
```

Indexes:

- `(org_id, project_id, kind, updated_at desc)`
- `(org_id, project_id, visibility, updated_at desc)`
- `(org_id, project_id, owner_agent, updated_at desc)`
- `(org_id, project_id, handoff_id)`

The manifest is the source of truth for artifact surfacing and metadata. The
named content backend is the source of truth for bytes. A surface may show an
artifact only when `content_status="available"` and the read path validates
that `content_ref` still resolves. If validation fails, the read operation
marks `content_status="unavailable"`, records a `project_data_events` row, and
returns a recoverable "artifact unavailable" response rather than silently
dropping the artifact.

Analytics source JSON is stored as an artifact with
`kind="analytics_source_data"`. Rendered chart/table snapshots are stored as
artifacts with `kind="evaluation_analytics_snapshot"`. A legacy
`trendline_snapshot` artifact kind must be migrated to
`evaluation_analytics_snapshot` with `analytics_kind="optimization_timeline"`
in the associated analytics view.

### 5.3 `evaluation_analytics_views`

Primary key: `(org_id, project_id, analytics_view_id)`.

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

Indexes:

- `(org_id, project_id, analytics_kind, updated_at desc)`
- `(org_id, project_id, owner_agent, updated_at desc)`
- `(org_id, project_id, visibility, updated_at desc)`
- `(org_id, project_id, phase, updated_at desc)`
- `(org_id, project_id, langsmith_experiment_id)`
- `(org_id, project_id, handoff_id)`

`evaluation_analytics_views` contains the canonical product record for a
published analytics surface. It does not contain arbitrary chart code and does
not contain raw private eval evidence. The `data_ref` points to schema-validated
chart/table source data, normally an `artifact_manifest` row with
`kind="analytics_source_data"`.

The backend must validate that `recommended_view_type` is supported for the
referenced source data schema before setting `render_status="valid"`. Unsupported
or invalid analytics data must be rejected at publication time or marked with
`render_status="invalid"` / `"unsupported"` and excluded from default UI views.
The chart-family source-data schema and validation result contract are owned by
`evaluation-analytics-chart-schemas.md`; Harness Engineer publication/update
operation contracts are owned by `harness-engineer-evaluation-analytics.md`.

`visibility="developer_safe"` means the analytics view may be exposed to the
Developer only after both the view summary and referenced source data pass the
Developer-safe boundary checks. Developer-safe analytics must not include hidden
rubrics, judge prompts, held-out examples, private dataset rows, private eval
instructions, raw private trace content, or HE/evaluator-private reasoning.

### 5.4 `project_snapshots`

Primary key: `(org_id, project_id, snapshot_id)`.

```python
class ProjectSnapshotRecord(DataPlaneBase):
    snapshot_id: str
    requested_by_thread_id: str
    requested_by_user_id: str | None
    source_execution_environment_id: str
    source_execution_mode: Literal["managed_sandbox", "external_devbox", "local_workspace"]
    snapshot_kind: Literal["file", "directory_listing", "diff", "command_log", "preview"]
    source_path: str
    artifact_id: str
    langsmith_run_id: str | None
```

`pm_session`, web, TUI, and headless readers do not get raw cross-thread
filesystem access. Live inspection is a brokered read-only snapshot operation:
the backend validates project membership and execution mode, reads the requested
path from the project execution environment, writes an artifact manifest row
with `kind="live_snapshot"`, and returns that artifact. For `local_workspace`,
snapshot capture requires explicit project-level opt-in recorded on
`project_registry`; otherwise it is rejected.

### 5.5 `project_data_events`

Primary key: `(org_id, event_id)`.

```python
class ProjectDataEvent(DataPlaneBase):
    event_id: str
    operation: Literal[
        "create_project_registry",
        "update_project_progress",
        "register_artifact",
        "mark_artifact_unavailable",
        "publish_analytics_view",
        "update_analytics_view",
        "list_evaluation_analytics_views",
        "get_evaluation_analytics_view",
        "get_analytics_source_data",
        "render_analytics_snapshot",
        "mark_analytics_view_stale",
        "capture_project_snapshot",
        "archive_project",
        "delete_project",
    ]
    record_family: Literal[
        "project_registry",
        "artifact_manifest",
        "evaluation_analytics_views",
        "project_snapshots",
    ]
    record_id: str
    actor_kind: Literal["user", "agent", "system", "headless_adapter"]
    actor_id: str | None
    role_name: AgentName | Literal["system"] | None
    thread_id: str | None
    project_thread_id: str | None
    pm_session_thread_id: str | None
    run_id: str | None
    langsmith_run_id: str | None
    handoff_id: str | None
    tool_call_id: str | None
    outcome: Literal["allowed", "denied", "failed"]
```

Every read and write operation records one access event. Denied reads are
recorded with `outcome="denied"` and no private payload.

## 6. Write APIs

All writes go through backend-owned operations. Agents never call product
database clients directly from model-visible tools.

| Operation | Caller | Effect |
|---|---|---|
| `create_project_registry(input)` | UI onboarding, PM `spawn_project`, headless ingress | Inserts `project_registry`; idempotent on `(org_id, project_id)` only when `project_thread_id` matches |
| `update_project_progress(input)` | `dispatch_handoff`, `finish_to_user` hook | Updates `current_phase`, `current_agent`, last handoff fields, `artifact_count`, and `status` |
| `register_artifact(input)` | System-owned handoff/artifact helper | Validates content reference and inserts or versions `artifact_manifest` |
| `mark_artifact_unavailable(input)` | Artifact read path | Marks a dangling reference unavailable and records the failed read |
| `publish_analytics_view(input)` | Harness Engineer, Evaluator, system analytics helper | Validates schema-compatible source data, inserts `evaluation_analytics_views`, and records source artifact/LangSmith provenance |
| `update_analytics_view(input)` | Owning analytics role or system | Updates title, summary, visibility, source refs, or render status subject to role policy and Developer-safe boundary checks |
| `mark_analytics_view_stale(input)` | System, Harness Engineer, Evaluator | Marks a view stale when source artifacts, LangSmith experiment refs, or schema versions drift |
| `render_analytics_snapshot(input)` | System analytics renderer | Renders a deterministic snapshot artifact from a valid analytics view and registers `kind="evaluation_analytics_snapshot"` |
| `capture_project_snapshot(input)` | PM session tool, web/TUI/headless backend | Creates a read-only snapshot artifact for allowed execution modes |
| `archive_project(input)` | PM/user/system policy | Sets registry `status="archived"` and hides project from active views while retaining manifest, analytics views, snapshot, and access-event history |
| `delete_project(input)` | authorized user/system policy | Sets registry `status="deleted"`, marks manifest/snapshot content deleted, removes records from normal reads, and schedules hard deletion after retention |

`register_artifact` is structurally paired with artifact publication. A handoff
or artifact-producing tool that claims a new visible artifact must not return a
successful `Command.PARENT` until the artifact has either been registered or the
tool has returned recoverable feedback to the agent explaining why registration
failed.

`publish_analytics_view` is structurally paired with analytics source data. A
Harness Engineer or Evaluator cannot publish a valid analytics view unless the
referenced source data exists, resolves, validates against the analytics chart
schema family, and satisfies the requested visibility policy.

## 7. Read APIs

All consumers use the same backend-owned read operations.

| Operation | Consumers | Developer role allowed? |
|---|---|---|
| `list_projects(org_id, filters)` | PM session, web, TUI, headless | No |
| `get_project_status(org_id, project_id)` | PM session, web, TUI, headless | No |
| `list_project_artifacts(org_id, project_id, filters)` | PM session, web, TUI, headless, project roles | Yes, excluding non-developer-visible records |
| `get_project_artifact(org_id, project_id, artifact_id, version=None)` | PM session, web, TUI, headless, project roles | Yes, excluding non-developer-visible records |
| `list_evaluation_analytics_views(org_id, project_id, filters)` | PM session, web, TUI, headless, Harness Engineer, Evaluator | Yes, only when `visibility="developer_safe"` and explicitly exposed |
| `get_evaluation_analytics_view(org_id, project_id, analytics_view_id)` | PM session, web, TUI, headless, Harness Engineer, Evaluator | Yes, only when `visibility="developer_safe"` and explicitly exposed |
| `get_analytics_source_data(org_id, project_id, analytics_view_id)` | PM session, web, TUI, headless, Harness Engineer, Evaluator | Yes, only through Developer-safe policy and source-data redaction checks |
| `capture_project_snapshot(...)` | PM session, web, TUI, headless | No |

PM session tools are thin wrappers around these operations. The web app, TUI,
and headless adapters call the same backend operations; they do not read
LangGraph Store directly. LangGraph Studio is an inspection surface
for graph state and traces, not a supported product data-plane reader.
First-party renderer behavior for these reads is specified in
`evaluation-analytics-renderer-contract.md`.

## 8. Auth, Tenant, And Role Boundaries

Authorization is structural:

- Product database rows are scoped by `org_id`; first-party user reads use
  Supabase row-level security in web deployments. Local/dev runs as a
  single-user deployment but still writes `org_id` and exercises the same
  org-scoped query predicates in conformance fixtures.
- Agent-side writes run with a service role, but every call carries
  `org_id`, `project_id`, `thread_id`, `project_thread_id`, and `role_name`.
  The data-access layer rejects role/operation combinations outside the matrix
  below before touching the database.
- Developer-role runtime does not receive private analytics views,
  `capture_project_snapshot`, HE/evaluator-private artifact read tools, or raw
  analytics source data unless the view and source artifact are explicitly
  `developer_safe`.
- HE-private and Evaluator-private artifacts are surfaced only to owning roles,
  PM session, and authorized first-party surfaces. They are never copied into
  Developer-visible packages.
- `stakeholder_visible` analytics may be shown in product/UI surfaces for the
  owning org. `developer_safe` analytics may be exposed to Developer-role agents
  for optimization guidance. These are separate policies.

| Role/surface | Registry | Artifact manifest | Evaluation analytics views | Live snapshot |
|---|---|---|---|---|
| PM session | Read | Read visible + private summaries | Read internal/stakeholder-visible/sanitized private summaries; promote visibility only if authorized | Capture/read |
| Web/TUI/headless surface | Read by org membership | Read by org membership and visibility | Read by org membership and visibility | Capture/read |
| Harness Engineer | Read own project | Read/write HE-owned artifacts | Read/write HE-owned analytics | No |
| Evaluator | Read own project | Read/write evaluator-owned artifacts | Read/write evaluator-owned analytics, future/conditional | No |
| Developer | No portfolio reads | Read developer-visible artifacts only | Read only `developer_safe` analytics explicitly exposed to Developer | No |
| `dispatch_handoff` | Write progress only | No | No | No |
| System | Read/write derived state | Read/write derived artifact rows | Read/write render/stale status and generated snapshots | Capture/read by policy |

## 9. Retention, Archival, Deletion, And Migration

- `status="completed"` keeps the project visible in completed-project views.
- `status="archived"` removes the project from active views but keeps registry,
  manifest, analytics views, snapshots, and access events.
- `status="deleted"` soft-deletes project records immediately from normal reads.
  Hard deletion removes content backends and database rows after the deployment's
  configured retention window. Local-dev retention is user-managed.
- Artifact deletion sets `content_status="deleted"` and `deleted_at`; readers
  return a deleted-artifact response instead of falling back to filesystem scans.
- Evaluation analytics views remain queryable until project archive or deletion.
  Source artifacts may be versioned independently; a view must be marked stale
  when its referenced source artifact, schema version, or LangSmith provenance is
  no longer current.
- Schema changes add a new `schema_version` and a migration. Readers must reject
  rows with unknown future versions and must support the current version during
  a rolling deploy.

### 9.1 Legacy Optimization Trendline Migration

The prior top-level trendline primitive is deprecated. Migration must preserve
historical intent without preserving the old substrate:

```txt
legacy top-level trendline table
  -> evaluation_analytics_views row
     analytics_kind = "optimization_timeline"
     recommended_view_type = "line_chart"
     visibility = previous sanitized visibility policy
     data_ref = artifact containing migrated line-chart source JSON
```

Legacy trendline snapshot artifacts migrate as:

```txt
legacy trendline_snapshot artifact
  -> artifact_manifest.kind = "evaluation_analytics_snapshot"
  -> associated evaluation_analytics_views.analytics_kind = "optimization_timeline"
```

No new code should write legacy trendline records. Any compatibility reader must
be migration-only and must emit deprecation telemetry through
`project_data_events`.

## 10. Trace Correlation

Every operation accepts a `trace_context` payload:

```python
class DataPlaneTraceContext(TypedDict, total=False):
    thread_id: str
    project_thread_id: str
    pm_session_thread_id: str | None
    run_id: str | None
    langsmith_run_id: str | None
    handoff_id: str | None
    tool_call_id: str | None
    source_agent: AgentName | Literal["system"] | None
    user_turn_id: str | None
```

The backend writes these fields into `project_data_events` and adds the same
stable identifiers to the current LangSmith run metadata when a run is active.
If LangSmith tracing is disabled, `langsmith_run_id` is `None` and the access
event still records the local run/thread identifiers.

Evaluation analytics operations must attach LangSmith provenance when available:
`langsmith_dataset_id`, `langsmith_experiment_id`, `langsmith_project_name`,
`langsmith_run_id`, and/or `langsmith_trace_url`. These references are
provenance pointers only; private LangSmith evidence is not copied into
Developer-visible analytics unless explicitly sanitized into source artifacts.

## 11. Conformance Tests

Minimum checks for implementation:

1. `project_registry` is idempotent: creating the same `(org_id, project_id)`
   with a different `project_thread_id` fails.
2. `dispatch_handoff` calls `update_project_progress` on every handoff and the
   registry row matches the last `HandoffRecord`.
3. `finish_to_user` marks the project completed without writing PCG
   `handoff_log`.
4. `register_artifact` validates `content_ref`; a missing path fails the write.
5. A dangling artifact read marks `content_status="unavailable"` and records a
   denied/failed access event.
6. Developer-role reads cannot fetch HE-private artifacts, Evaluator-private
   artifacts, live snapshots, private analytics views, or non-redacted analytics
   source data.
7. Harness Engineer can publish schema-valid analytics views only when the
   referenced analytics source data exists and validates against the supported
   chart/table schema family.
8. `optimization_timeline` is accepted only as
   `evaluation_analytics_views.analytics_kind`, never as a top-level record
   family.
9. Developer-safe analytics reject hidden rubrics, judge prompts, held-out
   examples, private dataset row contents, raw private trace content, private HE
   reasoning, and private evaluation instructions.
10. PM session, web, TUI, and headless adapters all read through the same backend
    operations for registry, artifact manifest, and evaluation analytics views.
11. `render_analytics_snapshot` creates an `evaluation_analytics_snapshot`
    artifact from a valid analytics view and records the operation in
    `project_data_events`.
12. `mark_analytics_view_stale` flips `render_status="stale"` when source data,
    schema version, or LangSmith provenance changes.
13. `capture_project_snapshot` succeeds for allowed `managed_sandbox` and
    `external_devbox` projects, rejects `local_workspace` without explicit
    opt-in, writes a `project_snapshots` row, and registers a `live_snapshot`
    artifact.
14. Every read/write creates a `project_data_events` row with `org_id`,
    `project_id`, operation name, outcome, and trace context.
15. LangGraph Store cache entries are invalidated or refreshed after product DB
    writes; direct Store reads are not accepted as source-of-truth reads in
    product code.
