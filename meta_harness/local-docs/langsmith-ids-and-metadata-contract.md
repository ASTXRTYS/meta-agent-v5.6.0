# LangSmith IDs And Metadata Contract For Evaluation Evidence Workbench

Source-audited for `TICKET-001` on 2026-04-26. This is a `local-docs/` research artifact, not a product spec and not a new Project Data Plane record family.

## Purpose

This document states which LangSmith/OpenEvals identifiers Meta Harness should persist when the Evidence Workbench uses LangSmith as the forensic substrate. It also recommends metadata keys to attach to LangSmith datasets, experiments/sessions, runs, feedback, and local evidence bundles so Evidence Workbench outputs can be traced back to Project Data Plane artifacts without duplicating LangSmith storage.

## Source basis

- Installed LangSmith is `0.7.37` (`.venv/lib/python3.12/site-packages/langsmith-0.7.37.dist-info/METADATA:2-4`).
- Installed OpenEvals is `0.2.0` (`.venv/lib/python3.12/site-packages/openevals-0.2.0.dist-info/METADATA:2-4`).
- Dataset schema fields include stable `id`, counts, schemas, transformations, and metadata (`.venv/lib/python3.12/site-packages/langsmith/schemas.py:247-259`).
- Example fields include `dataset_id`, `inputs`, `outputs`, `metadata`, `id`, `created_at`, `modified_at`, `source_run_id`, and attachments (`schemas.py:81-88`, `schemas.py:138-149`).
- Run fields include `id`, `name`, `start_time`, `run_type`, `extra`, `error`, `serialized`, `events`, `inputs`, `outputs`, `reference_example_id`, `parent_run_id`, tags, attachments, `session_id`, `child_runs`, feedback stats, token/cost stats, and status (`schemas.py:306-365`, `schemas.py:393-436`).
- Project/session fields include `id`, `name`, `extra`, `tenant_id`, and `reference_dataset_id`; hydrated results add run/latency/token/cost/feedback/error stats (`schemas.py:701-745`, `schemas.py:755-784`, `schemas.py:1400-1401`).
- Feedback fields/configs include feedback IDs, source metadata, continuous/categorical/freeform configs, score/value/comment/correction concepts, and feedback source linkage (`schemas.py:665-699`, `client.py:7355-7423`).
- OpenEvals `EvaluatorResult` has `key`, `score`, `comment`, `metadata`, and `source_run_id` (`openevals/types.py:18-24`).

## Identifier contract

### Dataset identifiers

Persist these when creating or referencing a LangSmith dataset:

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `langsmith_dataset_id` | Yes | `Dataset.id` is the stable dataset UUID (`schemas.py:247-250`). | Primary stable reference. |
| `langsmith_dataset_name` | Yes | `read_dataset` and `list_datasets` resolve/filter by name (`client.py:5086-5110`, `client.py:5237-5246`). | Human-readable; not sufficient alone. |
| `langsmith_dataset_url` | Recommended | `Dataset.url` is constructed from host/tenant/dataset ID (`schemas.py:283-291`). | Evidence reference / UI routing. |
| `langsmith_dataset_data_type` | Recommended | `create_dataset` accepts `data_type` (`client.py:4990-5000`). | Useful for eval/run-function alignment. |
| `langsmith_dataset_version_as_of` | Required for immutable references | `list_examples(as_of=...)` accepts tag or timestamp (`client.py:6546-6571`). | Use for held-out/optimization split reproducibility. |
| `langsmith_dataset_version_tag` | Recommended | `update_dataset_tag(as_of, tag)` moves tag to a version (`client.py:5319-5377`). | Examples: `optimization`, `holdout`, `baseline`. |
| `langsmith_dataset_schema_ref` | Recommended | Dataset stores input/output schemas (`schemas.py:256-257`). | Persist hash/ref, not necessarily full schema in Developer-safe outputs. |

### Example identifiers

Persist these for row-level evidence:

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `langsmith_example_id` | Yes | Example model has `id`; create APIs return example IDs (`schemas.py:138-149`, `client.py:6204-6206`). | Primary row reference. |
| `langsmith_dataset_id` | Yes | `ExampleBase.dataset_id` (`schemas.py:81-88`). | Required to locate row. |
| `langsmith_example_split` | Recommended | Create/list APIs support `split` / `splits` (`client.py:6194-6199`, `client.py:6551-6553`). | Needed for optimization/holdout isolation. |
| `langsmith_source_run_id` | Required when derived from trace | Create APIs support `source_run_id` / `source_run_ids` (`client.py:6194-6199`, `client.py:6412-6415`). | Tracks production-trace-to-example provenance. |
| `langsmith_example_as_of` | Required for immutable row sets | `list_examples(as_of=...)` returns examples present at a version (`client.py:6567-6571`). | Store with eval runs and exported bundles. |
| `langsmith_example_metadata` | HE-private or internal | Example metadata is first-class (`schemas.py:81-88`, `schemas.py:102-115`). | Redact before Developer-safe output. |

### Experiment / session identifiers

LangSmith SDK names these objects projects/sessions; in evaluation workflows they serve as experiment sessions.

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `langsmith_experiment_id` / `langsmith_project_id` / `langsmith_session_id` | Yes | `TracerSession.id`; `ExperimentResults.experiment_id` (`schemas.py:701-708`, `evaluation/_runner.py:563-570`). | Treat these as aliases with clear naming at call sites. |
| `langsmith_experiment_name` / `project_name` | Yes | `TracerSession.name`; `ExperimentResults.experiment_name` (`schemas.py:713-716`, `evaluation/_runner.py:563-565`). | Human-readable; not sufficient alone. |
| `langsmith_reference_dataset_id` | Yes for eval experiments | Project/session stores `reference_dataset_id` (`schemas.py:719-722`). | Binds experiment to dataset. |
| `langsmith_experiment_url` | Recommended | `TracerSession.url` constructs project URL (`schemas.py:733-738`). | UI reference. |
| `langsmith_comparison_url` | Recommended | `ExperimentResults.comparison_url` returns dataset comparison URL (`evaluation/_runner.py:573-592`). | Store as evidence reference. |
| `langsmith_comparative_experiment_id` | Required for pairwise comparisons | `evaluate_comparative` creates UUID and calls `create_comparative_experiment` (`evaluation/_runner.py:887-894`). | Used for comparative feedback/results. |
| `langsmith_experiment_metadata` | Required | `create_project` and `evaluate` accept metadata (`client.py:4587-4596`, `evaluation/_runner.py:137-156`). | Store Meta Harness correlation keys here. |

### Run / trace identifiers

Persist these for run indexes and trace bundles:

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `langsmith_run_id` | Yes | `RunBase.id` (`schemas.py:315-316`). | Primary run/span ID. |
| `langsmith_trace_id` | Yes for trace-level routing | `list_runs` supports `trace_id` and default-select includes `trace_id` (`client.py:3840-3857`, `client.py:3962-3990`). | Root trace ID. |
| `langsmith_parent_run_id` | Required for non-root runs | `RunBase.parent_run_id`; `list_runs` supports `parent_run_id` (`schemas.py:353-354`, `client.py:3852-3854`). | Reconstruct hierarchy. |
| `langsmith_session_id` | Yes | `Run.session_id` is project ID (`schemas.py:393-397`). | Links run to experiment/project. |
| `langsmith_reference_example_id` | Required for eval runs | `RunBase.reference_example_id`; list default includes it (`schemas.py:350-351`, `client.py:3962-3990`). | Links run to dataset row. |
| `langsmith_thread_id` | Recommended if present | `read_thread` builds `eq(thread_id, ...)` filters (`client.py:3784-3838`). | Useful for online eval / multi-turn traces. |
| `langsmith_run_url` | Recommended for allowed viewers | `get_run_url` constructs UI URL from run/project (`client.py:4246-4282`). | Visibility-gated reference. |
| `langsmith_child_run_ids` | Required for trace bundles | `Run.child_runs` loads only when instructed (`schemas.py:393-403`, `client.py:3780-3781`). | Do not imply children are present in shallow indexes. |
| `langsmith_run_select_fields` | Required for exports/indexes | `list_runs` supports `select`; default select includes sensitive fields (`client.py:3840-3860`, `client.py:3962-3992`). | Records what was included/excluded. |
| `langsmith_run_query` / `filter` / `trace_filter` / `tree_filter` | Required for filtered artifacts | `list_runs` supports structured filters (`client.py:3848-3851`, `client.py:3924-3948`). | Store exact source query for evidence reproducibility. |

### Feedback / score identifiers

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `langsmith_feedback_id` | Yes for persisted feedback | `create_feedback` accepts explicit `feedback_id`; `Feedback.id` exists (`client.py:7355-7382`, `schemas.py:689-699`). | Primary feedback object ID. |
| `langsmith_feedback_key` | Yes | `create_feedback(key=...)`; `list_feedback(feedback_key=...)` (`client.py:7355-7360`, `client.py:7680-7699`). | Metric name. |
| `langsmith_feedback_score` | Required for numeric/binary metrics | `create_feedback(score=...)`; OpenEvals `score` is float/bool (`client.py:7361-7362`, `openevals/types.py:15-24`). | Developer-safe only if metric is allowed. |
| `langsmith_feedback_value` | Optional | `create_feedback(value=...)` supports scalar/string/dict values (`client.py:7361-7363`). | Use for categorical/freeform display. |
| `langsmith_feedback_comment_ref` | Optional/private | `create_feedback(comment=...)` can include justification/reasoning (`client.py:7405-7409`). | Do not expose raw comments by default. |
| `langsmith_feedback_source_type` | Recommended | Supports API or MODEL source type (`client.py:7366-7369`, `client.py:7507-7519`). | Helps separate human/API/judge feedback. |
| `langsmith_feedback_source_run_id` | Recommended for judge feedback | `source_run_id` is embedded in feedback source metadata (`client.py:7415-7419`, `client.py:7520-7525`). | Preserve judge trace routing while redacting content. |
| `langsmith_feedback_config` | Required for new metric definitions | Feedback config supports continuous/categorical/freeform (`schemas.py:665-676`). | Private scoring contract unless approved. |
| `langsmith_comparative_experiment_id` | Required for comparative feedback | `create_feedback` accepts comparative experiment ID (`client.py:7373-7377`). | Pairwise/preference linkage. |
| `langsmith_feedback_group_id` | Recommended for rankings/preferences | `create_feedback` accepts feedback group ID (`client.py:7375-7377`, `client.py:7430-7435`). | Groups comparative feedback rows. |

### OpenEvals identifiers and fields

| Field | Required | Source / rationale | Notes |
|---|---:|---|---|
| `openevals_evaluator_key` | Yes | `EvaluatorResult.key` (`openevals/types.py:18-24`). | Maps to LangSmith feedback key. |
| `openevals_score` | Yes | `EvaluatorResult.score`, `ScoreType = float | bool` (`openevals/types.py:15-24`). | Normalize before publishing. |
| `openevals_comment_ref` | Optional/private | `EvaluatorResult.comment` (`openevals/types.py:18-24`). | May contain judge reasoning. |
| `openevals_metadata` | Optional/private | `EvaluatorResult.metadata` (`openevals/types.py:18-24`). | May contain rubric/extraction details. |
| `openevals_source_run_id` | Recommended | `EvaluatorResult.source_run_id` (`openevals/types.py:18-24`). | Links evaluator output to judge/source run. |
| `openevals_evaluator_config_ref` | Recommended | Exact/JSON/LLM/code/trajectory evaluators expose config parameters (`openevals/exact.py:17-19`, `openevals/json/match.py:61-70`, `openevals/llm.py:70-117`, `openevals/code/pyright.py:99-153`, `openevals/trajectory/match.py:21-29`). | Store config hash/ref, not hidden prompt text in Developer-safe output. |

## Recommended LangSmith metadata keys

Attach these to LangSmith datasets, experiments/sessions, runs, or feedback where applicable. These keys bind LangSmith forensic evidence to Meta Harness concepts without creating a parallel evidence database.

### Common keys

```txt
meta_harness.project_id
meta_harness.project_thread_id
meta_harness.handoff_id
meta_harness.plan_phase_id
meta_harness.artifact_id
meta_harness.artifact_kind
meta_harness.visibility
meta_harness.created_by_agent
meta_harness.source_ticket_id
meta_harness.schema_version
```

### Candidate / optimization keys

```txt
meta_harness.candidate_id
meta_harness.candidate_label
meta_harness.baseline_candidate_id
meta_harness.optimization_iteration
meta_harness.search_set_id
meta_harness.holdout_policy
meta_harness.eval_gate_id
meta_harness.eval_suite_id
```

### Dataset / example keys

```txt
meta_harness.dataset_role          # optimization | holdout | calibration | smoke | regression
meta_harness.dataset_split_policy
meta_harness.example_origin        # human_label | production_trace | synthetic | regression
meta_harness.source_langsmith_run_id
meta_harness.source_langsmith_trace_id
meta_harness.private_eval_artifact  # true/false
```

### Experiment / run keys

```txt
meta_harness.target_harness_id
meta_harness.target_harness_version
meta_harness.run_function_ref
meta_harness.evaluator_profile_id
meta_harness.evaluator_config_ref
meta_harness.judge_model
meta_harness.redaction_profile
meta_harness.trace_visibility
```

### Feedback keys

```txt
meta_harness.feedback_visibility
meta_harness.feedback_family       # correctness | trajectory | cost | latency | safety | preference
meta_harness.developer_safe_allowed
meta_harness.redaction_required
meta_harness.evaluator_source      # openevals | custom_code | human | langsmith_online
meta_harness.evaluator_result_key
```

## Mapping to existing Project Data Plane artifacts

This audit does not add a new Product Data Plane record family. Store LangSmith references inside existing artifact manifests and analytics source artifacts.

| Project Data Plane artifact kind | LangSmith references to store | Visibility default | Notes |
|---|---|---|---|
| `eval_suite` | Dataset IDs, evaluator config refs, feedback keys, experiment metadata conventions | `internal` / `he_private` | No hidden examples in Developer-safe view. |
| `dataset` | Dataset ID/name/url, version tag/as_of, split policy, example count | `internal` unless hidden | Row-level example IDs stay HE-private if held out. |
| `rubric` | Evaluator key/config refs, judge model refs, feedback config IDs/keys | `he_private` | Judge prompts/rubrics are not Developer-safe. |
| `experiment_summary` | Experiment ID/name/url, comparison URL, run stats, feedback stats | `internal` | Stakeholder-visible only after analytics validation. |
| `run_index` | Query/filter, selected fields, run IDs, trace IDs, example IDs, aggregate metrics | `he_private` by default | Can become internal if inputs/outputs/comments omitted. |
| `filtered_run_index` | Source query + local post-filter, selected run IDs, criteria, visibility | `he_private` | Must record source query and post-filter. |
| `trace_bundle` | Root run IDs, trace IDs, child run IDs, selected fields, source query | `he_private` | Raw trees are never Developer-visible. |
| `trace_summary_bundle` | Trace refs, summary files, redaction profile, evidence refs | `internal` or `he_private` | Developer-safe only after EBDR redaction. |
| `failure_cluster_report` | Run refs, feedback keys, cluster IDs, redaction report | `internal`; optional `developer_safe` | No hidden examples/rubrics/judge prompts. |
| `candidate_comparison_report` | Experiment IDs, comparative experiment ID, comparison URL, allowed deltas | `internal`; optional `developer_safe` | Preserve candidate/run/experiment provenance. |
| `analytics_source_data` | Aggregated metrics, chart schema ID, source experiment/run refs | `internal` / `stakeholder_visible` | Never contain raw private traces. |

## Visibility and redaction contract

### HE-private by default

These are `he_private` unless explicitly transformed:

- Raw examples and reference outputs.
- Held-out dataset row IDs when IDs themselves could reveal hidden sets.
- Raw run inputs/outputs/events/extra/serialized/error details.
- Full trace trees and full experiment dumps.
- Judge prompts, rubric text, evaluator reasoning/comments.
- Attachments and source-run-derived examples.

### Internal candidates

These may be `internal` after field selection/redaction:

- Experiment aggregate run stats and feedback stats.
- Run indexes with inputs/outputs/events/comments omitted.
- Dataset-level composition summaries.
- Cost/latency/token summaries.
- Failure cluster summaries with evidence references but no raw private content.

### Developer-safe candidates

Developer-safe artifacts may include only bounded signals:

- Metric deltas and aggregate scores approved for Developer visibility.
- Allowed run/trace references, if those traces are themselves Developer-visible.
- Localization/routing references without hidden examples or gold answers.
- Redaction reports listing removed categories, not removed content.

Developer-safe artifacts must exclude hidden rubrics, judge prompts, held-out examples, private dataset rows, raw private traces, evaluator reasoning, hidden task IDs/gold answers, and scoring logic.

### Stakeholder-visible candidates

Stakeholder-visible analytics should contain only chart/table-ready aggregate source data and links approved for the audience. They should point back to evidence artifacts rather than embedding raw evidence.

## Required metadata on evidence bundles

Every durable local evidence bundle should include a manifest with:

```txt
bundle_id
created_at
created_by_agent
purpose
source_package_versions
langsmith_project_id
langsmith_experiment_id
langsmith_dataset_id
source_query
source_query_language
selected_fields
local_post_filter
included_run_ids
included_trace_ids
included_example_ids
visibility
redaction_profile
included_fields
excluded_fields
artifact_id
retention_expectation
audit_event_id
```

## Access-path implications

- Persisting references and running SDK calls is `sdk_direct`.
- Creating a durable bundle, artifact, analytics view, Developer-safe report, or stakeholder-visible package is `policy_tool` because the value is the Meta Harness policy envelope, not the raw SDK call.
- LangSmith CLI is `not_supported_v1` in this environment because no installed console script exists.
