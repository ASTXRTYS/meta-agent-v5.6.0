# LangSmith Harness Engineer Reference

## Status

Durable `local-docs/` operating reference for Harness Engineer LangSmith and OpenEvals work.

This is not a product spec, not a Project Records Layer record family, and not an implementation plan. It is coding-agent operating memory for deciding what the Harness Engineer can do through LangSmith CLI skills, LangSmith SDK/API, OpenEvals, or future Meta Harness tools.

## Purpose

This reference has two jobs:

1. It is the capability matrix for deciding what Harness Engineer-facing capabilities the Meta Harness agent should expose directly, learn as skills, or leave to native LangSmith/OpenEvals surfaces.
2. It is also a compact source map for what is possible through LangSmith CLI skills, the LangSmith SDK/API, OpenEvals, and related LangSmith evidence workflows.

Future agents should read this before proposing LangSmith wrapper tools, Evidence Workbench tooling, evaluator/dataset flows, feedback APIs, trace export utilities, or analytics publication helpers.

## Access-path rule

The corrected Evidence Workbench access pattern is:

1. **CLI-first where native.** LangSmith CLI is required Harness Engineer operational expertise. Local absence of a `.venv/bin/langsmith` executable is setup state only; it is not evidence that LangSmith CLI workflows are out of scope.
2. **SDK/API-direct where precision or composition is needed.** Use the LangSmith SDK/API directly when CLI coverage is missing, too coarse, or when code is the natural medium.
3. **OpenEvals-direct before custom evaluator logic.** Use OpenEvals for LLM-as-judge, exact/JSON/code/trajectory evaluators before inventing local evaluator contracts.
4. **Skills before product tools.** If a workflow is mostly procedural CLI/SDK competence, encode it as Harness Engineer skill guidance rather than a Meta Harness product tool.
5. **Explicit HE tools are exceptional.** A tool is justified only when the workflow is not comfortable through CLI, the SDK/API supports it, HE needs it repeatedly, and direct SDK code each time would materially reduce reliability or speed.
6. **Do not create raw wrappers.** Do not introduce tools merely to rename LangSmith operations such as listing runs, creating datasets, or fetching traces.

## Classification vocabulary

- `cli_native` — first-party LangSmith CLI skills cover the HE workflow; teach it as required HE operational expertise.
- `sdk_native` — the LangSmith SDK/API or OpenEvals covers the capability cleanly; use it directly in HE scripts or backend code when code is the natural medium.
- `sdk_extends_cli` — the SDK/API provides precision, composition, or programmatic control beyond CLI; investigate a tool only if the workflow is frequent and high-friction.
- `he_skill` — the right answer is procedural competence, prompt/skill guidance, or a repeatable CLI/SDK workflow, not a product tool.
- `explicit_tool_candidate` — exceptional: the capability is not comfortable through CLI, the SDK/API provides it, HE needs it repeatedly, and a direct tool would materially improve reliability or speed.

## Source basis

- Project dependency floor at audit time: Python `>=3.12`, `langsmith>=0.7.25`.
- Installed LangSmith at audit time: `langsmith==0.7.37`.
- Installed OpenEvals at audit time: `openevals==0.2.0`.
- Local CLI setup at audit time had no `.venv/bin/langsmith`; this is setup state only.
- Local LangSmith skills used as HE-facing CLI workflow sources:
  - `langsmith-dataset`
  - `langsmith-trace`
  - `langsmith-evaluator`
- SDK behavior was source-audited from installed `.venv/lib/python3.12/site-packages/langsmith/` and `.venv/lib/python3.12/site-packages/openevals/`.

## Capability matrix

| Capability | Native / preferred surface | SDK/API extensions | HE relevance | Classification | Tool guidance |
|---|---|---|---|---|---|
| Dataset list/get/create/delete/export/upload | LangSmith CLI skills for routine lifecycle | Dataset schemas, metadata, version diff, tag movement, CSV ingestion, precise programmatic control | Core eval dataset creation, inspection, export, upload | `cli_native`; `sdk_extends_cli` for precision | No tool for basic CRUD/export/upload; possible later tool only for repeated version/tag/schema workflows |
| Example list/create/delete | LangSmith CLI skills for simple rows | Deterministic IDs, bulk create/update, splits, attachments, source-run linkage, `as_of` reads | Turning traces into optimization/regression datasets | `cli_native`; `sdk_extends_cli` for provenance precision | Possible only for repeated deterministic bulk/source-run-derived workflows |
| Experiment list/get | LangSmith CLI skills for inspection | Evaluation execution, metadata binding, preview summaries, comparative experiments, concurrency, repetitions, programmable result iteration | Candidate comparison and result review | `cli_native` for inspection; `sdk_native` / `sdk_extends_cli` for execution/comparison | Possible only for repeated standard evaluation/comparison workflows |
| Evaluation execution | SDK/OpenEvals local `evaluate()` / `aevaluate()` workflows | Evaluators, metadata, experiment prefixes, concurrency, repetitions, comparative workflows | Offline development evals and regression gates | `sdk_native` / `he_skill` | No generic evaluation wrapper; possible project-standard runner only after repeated friction |
| Trace list/get/export | LangSmith CLI skills for complete trace inspection/export | Selected fields, custom serialization, cursor pagination, SDK-controlled tree hydration | Primary forensic workflow | `cli_native`; `sdk_extends_cli` for precision exports | Possible only for repeated selected-field trace-tree extraction |
| Run list/get/export | LangSmith CLI skills for span-level querying | `select`, `trace_filter`, `tree_filter`, parent/root/reference-example filters, pagination | Focused diagnostics, performance/cost, evaluator debugging | `cli_native`; `sdk_extends_cli` for structured filters | Possible only for high-friction structured filter/index generation |
| Thread list/get and project list | LangSmith CLI skills for lookup | Thread filter composition, project/session metadata and stats | Online evals and project-scoped investigation | `cli_native`; `sdk_extends_cli` for metadata/stat queries | Usually no tool; teach as HE skill |
| Evaluator list/upload/delete | LangSmith CLI skills for uploaded code evaluator lifecycle | Local LLM-as-judge, package-rich evaluator development, structured evaluator constructors, local debugging | Automated scoring | `cli_native` for uploaded code evaluator lifecycle; `sdk_native` / `he_skill` for local and LLM judges | Possible only for repeated evaluator-construction boilerplate |
| LLM-as-judge evaluator construction | SDK/OpenEvals, not CLI upload in current local skill evidence | OpenEvals LLM evaluators and local structured-output judges | Subjective quality evaluation | `sdk_native` / `he_skill` | Possible only for repeated boilerplate mapping to OpenEvals/LangSmith primitives |
| Feedback list/create/filter | SDK/API based on current local skill evidence; trace/run filters can inspect feedback-like predicates indirectly | `Client.create_feedback`, `list_feedback`, feedback configs, presigned feedback token APIs | Score/comment analysis, comparative feedback, evaluator routing | `sdk_extends_cli` | Strongest later candidate if direct feedback workflows become frequent and CLI remains insufficient |
| Dataset-from-traces workflow | CLI export + local processing + dataset upload skill workflow | Deterministic IDs, source-run linkage, splits, attachment handling | Turning production failures into evals | `he_skill`; `sdk_extends_cli` for provenance precision | Possible only for strict provenance/redaction trace-to-dataset compiler |
| Redaction/anonymizer configuration | Procedural discipline and SDK configuration | `Client(anonymizer=..., hide_inputs=..., hide_outputs=..., hide_metadata=...)` | Leakage prevention in tracing and exports | `sdk_native` / `he_skill` | Possible only for narrow repeated redaction profile helper |
| EBDR evaluator-to-optimizer feedback | Existing evaluator-feedback skill, not LangSmith CLI/API | LangSmith evidence refs feed the skill | Safe optimizer feedback | `he_skill` | Do not recreate EBDR as Workbench tooling |

## Final capability classifications

```txt
cli_native:
  - routine dataset list/get/create/delete/export/upload
  - routine example list/create/delete
  - experiment list/get inspection
  - trace list/get/export for complete execution trees
  - run list/get/export for span-level inspection
  - thread list/get and project list lookup
  - code evaluator list/upload/delete

sdk_native:
  - evaluation execution with evaluate()/aevaluate()
  - local LLM-as-judge and OpenEvals evaluator construction
  - comparative evaluation and programmatic experiment/result iteration
  - SDK privacy/anonymizer configuration

sdk_extends_cli:
  - deterministic/bulk example IDs, splits, attachments, source-run linkage
  - dataset version diff/tag/schema workflows
  - selected-field run indexes, structured filters, cursor pagination
  - custom trace-tree hydration/serialization
  - feedback create/list/config/source metadata/comparative IDs
  - experiment preview summaries and comparison URL workflows

he_skill:
  - trace-first forensic workflow
  - dataset-from-traces workflow
  - evaluator upload workflow and sandbox constraints
  - EBDR-1 feedback shaping via the existing evaluator-feedback skill

explicit_tool_candidate:
  - none currently approved
  - possible later candidates must satisfy the SDK-only/high-friction/frequent-use rule
```

## Identifier preservation contract

Preserve LangSmith/OpenEvals identifiers in existing project artifacts, analytics source data, or metadata fields. Do not duplicate LangSmith as a parallel evidence database.

### Dataset identifiers

| Field | Required | Purpose |
|---|---:|---|
| `langsmith_dataset_id` | Yes | Stable dataset UUID |
| `langsmith_dataset_name` | Yes | Human-readable lookup name; not sufficient alone |
| `langsmith_dataset_url` | Recommended | Evidence reference / UI routing |
| `langsmith_dataset_data_type` | Recommended | Eval/run-function alignment |
| `langsmith_dataset_version_as_of` | Required for immutable references | Reproducible row set |
| `langsmith_dataset_version_tag` | Recommended | Named split/version pointer such as `optimization`, `holdout`, `baseline` |
| `langsmith_dataset_schema_ref` | Recommended | Schema hash/ref without exposing full schema in Developer-safe output |

### Example identifiers

| Field | Required | Purpose |
|---|---:|---|
| `langsmith_example_id` | Yes | Stable row reference |
| `langsmith_dataset_id` | Yes | Dataset linkage |
| `langsmith_example_split` | Recommended | Optimization/holdout/calibration isolation |
| `langsmith_source_run_id` | Required when trace-derived | Production-trace-to-example provenance |
| `langsmith_example_as_of` | Required for immutable row sets | Versioned reproducibility |
| `langsmith_example_metadata` | HE-private or internal | Redact before Developer-safe output |

### Experiment / session identifiers

LangSmith SDK names these objects projects/sessions; in evaluation workflows they serve as experiment sessions.

| Field | Required | Purpose |
|---|---:|---|
| `langsmith_experiment_id` / `langsmith_project_id` / `langsmith_session_id` | Yes | Stable experiment/session reference |
| `langsmith_experiment_name` / `project_name` | Yes | Human-readable; not sufficient alone |
| `langsmith_reference_dataset_id` | Yes for eval experiments | Binds experiment to dataset |
| `langsmith_experiment_url` | Recommended | UI reference |
| `langsmith_comparison_url` | Recommended | Dataset comparison routing |
| `langsmith_comparative_experiment_id` | Required for pairwise comparisons | Comparative feedback/results linkage |
| `langsmith_experiment_metadata` | Required | Meta Harness correlation keys |

### Run / trace identifiers

| Field | Required | Purpose |
|---|---:|---|
| `langsmith_run_id` | Yes | Primary span ID |
| `langsmith_trace_id` | Yes for trace-level routing | Root trace ID |
| `langsmith_parent_run_id` | Required for non-root runs | Hierarchy reconstruction |
| `langsmith_session_id` | Yes | Experiment/project linkage |
| `langsmith_reference_example_id` | Required for eval runs | Dataset-row linkage |
| `langsmith_thread_id` | Recommended if present | Online eval / multi-turn trace grouping |
| `langsmith_run_url` | Recommended for allowed viewers | Visibility-gated UI reference |
| `langsmith_child_run_ids` | Required when analyzing full trace trees | Do not imply child runs are present in shallow indexes |
| `langsmith_run_select_fields` | Required for exports/indexes | Records included/excluded fields |
| `langsmith_run_query` / `filter` / `trace_filter` / `tree_filter` | Required for filtered analysis | Evidence reproducibility |

### Feedback / score identifiers

| Field | Required | Purpose |
|---|---:|---|
| `langsmith_feedback_id` | Yes for persisted feedback | Stable feedback object ID |
| `langsmith_feedback_key` | Yes | Metric name |
| `langsmith_feedback_score` | Required for numeric/binary metrics | Developer-safe only if metric is allowed |
| `langsmith_feedback_value` | Optional | Categorical/freeform display value |
| `langsmith_feedback_comment_ref` | Optional/private | Do not expose raw judge reasoning by default |
| `langsmith_feedback_source_type` | Recommended | Separates human/API/judge feedback |
| `langsmith_feedback_source_run_id` | Recommended for judge feedback | Judge trace routing while redacting content |
| `langsmith_feedback_config` | Required for new metric definitions | Private scoring contract unless approved |
| `langsmith_comparative_experiment_id` | Required for comparative feedback | Pairwise/preference linkage |
| `langsmith_feedback_group_id` | Recommended for rankings/preferences | Groups comparative feedback rows |

### OpenEvals fields

| Field | Required | Purpose |
|---|---:|---|
| `openevals_evaluator_key` | Yes | Maps to LangSmith feedback key |
| `openevals_score` | Yes | Normalize before publishing |
| `openevals_comment_ref` | Optional/private | May contain judge reasoning |
| `openevals_metadata` | Optional/private | May contain rubric/extraction details |
| `openevals_source_run_id` | Recommended | Links evaluator output to judge/source run |
| `openevals_evaluator_config_ref` | Recommended | Store config hash/ref, not hidden prompt text in Developer-safe output |

## Recommended metadata keys

Attach these to LangSmith datasets, experiments/sessions, runs, or feedback where applicable.

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

## Visibility and redaction defaults

### HE-private by default

- Raw examples and reference outputs.
- Held-out dataset row IDs when IDs themselves could reveal hidden sets.
- Raw run inputs/outputs/events/extra/serialized/error details.
- Full trace trees and full experiment dumps.
- Judge prompts, rubric text, evaluator reasoning/comments.
- Attachments and source-run-derived examples.

### Internal candidates after field selection

- Experiment aggregate run stats and feedback stats.
- Run indexes with inputs/outputs/events/comments omitted.
- Dataset-level composition summaries.
- Cost/latency/token summaries.
- Failure cluster summaries with evidence references but no raw private content.

### Developer-safe candidates after EBDR redaction

- Directional deltas and allowed metric summaries.
- Bounded failure-mode categories.
- Trace/run references only if access policy permits.
- Candidate snapshot/diff references.
- Redaction reports that state what was withheld.

Developer-safe output must not include evaluator prompts, hidden examples, gold answers, judge reasoning, raw trace trees, or hidden scoring logic.

## When to update this reference

Update this document when:

- LangSmith CLI skill coverage changes.
- LangSmith SDK/API or OpenEvals capabilities materially change.
- HE repeatedly experiences friction that may justify an explicit tool.
- A new approved explicit HE tool changes the capability classification.
- Visibility or redaction policy changes for evidence artifacts.

Do not update this document merely because a one-off ticket completed. Completed ticket rationale belongs in commits, ticket history, or `docs/archive/` only when historically important.
