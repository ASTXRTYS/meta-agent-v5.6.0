---
doc_type: archive
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 Project-Scoped Execution Environment
status: archived
last_synced: 2026-04-26
owners: ["@Jason"]
---

# ADR: Replace `optimization_trendline` With Evaluation Analytics Views

> **Archive metadata:** Historical rationale for replacing `optimization_trendline` with `evaluation_analytics_views`.
> **Status:** Archived source material · **Last synced with AD:** 2026-04-26.
> **Current authority:** `AD.md`, `docs/specs/project-data-contracts.md`, `docs/specs/harness-engineer-evaluation-analytics.md`, and `docs/specs/evaluation-analytics-chart-schemas.md`.

## Status

Approved.

## Context

The existing architecture introduced `optimization_trendline` as a Project Data Plane record intended to capture progress across optimization iterations. That term is now understood to be an over-narrow artifact of earlier scoping. The actual product capability needed is broader: the Harness Engineer needs a bounded way to publish UI-renderable evaluation analytics derived from evaluation context, success criteria, rubrics, datasets, judge profiles, risk maps, eval results, failure-mode analysis, and optimization findings.

The Harness Engineer’s responsibilities include, at minimum:

```txt
Harness Engineer
  creates eval suite
  defines success dimensions
  defines analytics views
  runs evals / receives eval results
  publishes sanitized analytics state
  updates UI dashboards
  emits Developer-safe feedback packets
```

This responsibility exists both before and after target harness development begins.

Before development, the Harness Engineer receives architecture/specification artifacts and constructs the evaluation program. This may include public datasets, held-out datasets, judge profiles, scoring rubrics, metric definitions, failure taxonomies, quality gates, and evaluation harness files. The Harness Engineer also needs to surface visual analytics derived from this evaluation model, such as success-criteria radar charts, coverage matrices, rubric-weight views, dataset composition charts, and risk maps.

After candidate harnesses are generated and evaluated, the Harness Engineer needs to analyze LangSmith-backed eval results, reason over failure modes, compare progress/regressions, update analytics surfaces, and emit Developer-safe feedback packets.

Therefore, `optimization_trendline` should not be the root product primitive. Optimization timelines are one analytics view type within a broader Evaluation Analytics system.

## Decision

Replace the top-level `optimization_trendline` concept with `evaluation_analytics_views`.

`evaluation_analytics_views` is the product-owned record family for UI-renderable analytics surfaces published by authorized evaluation roles. It supports pre-development target/context analytics and post-evaluation empirical analytics.

`optimization_timeline` becomes one `analytics_kind` under `evaluation_analytics_views`, usually rendered as a `line_chart`.

## Decision Summary

```txt
evaluation_analytics_views = canonical product records for published analytics surfaces
analytics source JSON/files = artifacts referenced by analytics views
optimization_timeline = one analytics kind, not the root concept
```

## Architectural Principles

1. **LangSmith-first eval truth.** Evaluation execution, experiments, runs, traces, and feedback are source-of-truth in LangSmith when LangSmith provides the first-class primitive.
2. **Meta Harness mirrors/references evidence.** Meta Harness stores references, summaries, local mirrors, derived analytics data, and UI-facing analytics records.
3. **Artifacts remain artifacts.** Datasets, rubrics, judge profiles, eval harness files, trace bundles, and analytics source JSON are persisted as files/artifacts and registered through the artifact system.
4. **Analytics views are product records.** A published UI analytics surface is a Product Data Plane record pointing to source artifacts and, when applicable, LangSmith references.
5. **HE chooses semantic visual framing.** The Harness Engineer chooses the analytics kind and recommended supported chart family.
6. **UI renders deterministically.** The UI renders only supported visualization types from validated schemas. No arbitrary custom chart code is accepted as a canonical product output.
7. **Agent freedom exists inside preparation, not at the UI boundary.** The Harness Engineer may use Python transforms in a sandbox to prepare analytics JSON, but the published output must validate against supported schemas.
8. **Developer-safe boundary remains structural.** Developer-facing feedback packets must not expose held-out examples, hidden rubrics, judge prompts, private dataset rows, private evaluation instructions, or raw private trace data.

## Replaces

* `optimization_trendline` as top-level Product Data Plane record family.
* `record_trendline_point` as the primary Harness Engineer analytics publication tool.
* `get_optimization_trendline` as the primary analytics read API.
* `trendline_snapshot` as the only analytics artifact shape.

## Introduces

* `evaluation_analytics_views`
* `publish_analytics_view`
* `update_analytics_view`
* `render_analytics_snapshot`
* `evaluation_analytics_snapshot` artifact kind
* `analytics_source_data` artifact kind
* `Evaluation Evidence Workbench` as a named future capability for LangSmith evidence ingestion, mirroring, trace-bundle analysis, and subagent-assisted failure synthesis.

## Consequences

### Positive

* Aligns product data model with actual Harness Engineer responsibilities.
* Supports pre-development analytics before eval results exist.
* Supports post-eval optimization analytics without overfitting to line charts.
* Keeps UI deterministic while preserving HE judgment.
* Gives PM/product surfaces a richer analytics substrate.
* Preserves Developer anti-leakage boundary.
* Creates a clear path for LangSmith-backed empirical evidence and local HE working context.

### Tradeoffs

* Requires schema definitions for supported chart families.
* Requires a validation layer for analytics source JSON.
* Requires a policy layer for visibility and audience boundaries.
* Requires later source-audit of LangSmith CLI/SDK capabilities before finalizing Evidence Workbench tools.

## Migration Notes

Any references to `optimization_trendline` should be reviewed and either removed or migrated:

| Old concept                  | New concept                                                                |
| ---------------------------- | -------------------------------------------------------------------------- |
| `optimization_trendline`     | `evaluation_analytics_views` with `analytics_kind="optimization_timeline"` |
| `record_trendline_point`     | `publish_analytics_view` / `update_analytics_view`                         |
| `get_optimization_trendline` | `list_evaluation_analytics_views` / `get_evaluation_analytics_view`        |
| `trendline_snapshot`         | `evaluation_analytics_snapshot`                                            |
| trendline point rows         | analytics source JSON + metric series schema                               |
