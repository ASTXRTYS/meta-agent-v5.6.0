# LangSmith CLI / SDK Capability Audit For Evaluation Evidence Workbench

## Status

Source-audited for SDK/OpenEvals on 2026-04-26 and updated from local
LangSmith skills for CLI coverage on 2026-04-27.

This is a `local-docs/` research artifact, not a product spec and not an implementation plan.

## Source preflight

### Local environment inspected

- **Project requirement:** `meta_harness/pyproject.toml` requires Python `>=3.12` and `langsmith>=0.7.25` (`meta_harness/pyproject.toml:9`, `meta_harness/pyproject.toml:20`).
- **Installed Python path:** `.venv/lib/python3.12/site-packages/` is the active source root. Existing first-pass citations in `evaluation-evidence-workbench.md` point at `.venv/lib/python3.11/...`; those path anchors are stale for this environment even if the cited concepts still exist.
- **Installed LangSmith:** `langsmith==0.7.37` (`.venv/lib/python3.12/site-packages/langsmith-0.7.37.dist-info/METADATA:2-4`).
- **Installed OpenEvals:** `openevals==0.2.0` (`.venv/lib/python3.12/site-packages/openevals-0.2.0.dist-info/METADATA:2-4`).
- **Installed AgentEvals:** `agentevals==0.0.9`, present but not the primary target of this ticket (`.venv/lib/python3.12/site-packages/agentevals-0.0.9.dist-info/METADATA:2-4`).
- **Local reference repos:** no local `.reference` LangSmith SDK or OpenEvals repo was present in this checkout; implementation-facing claims below therefore prioritize installed `.venv` package source.
- **Local LangSmith skills:** `langsmith-dataset`
  (`/Users/Jason/.claude/skills/langsmith-dataset`), `langsmith-trace`
  (`/Users/Jason/.claude/skills/langsmith-trace`), and `langsmith-evaluator`
  (`/Users/Jason/.claude/skills/langsmith-evaluator`) define the HE-facing CLI
  workflows audited on 2026-04-27.
- **Auggie:** resource listing was unavailable for the `auggie` MCP server, so Auggie was not used as authority. This audit uses local package source plus official docs entry pages as secondary intent.

### Official docs intent check

The LangSmith evaluation entry page frames the intended product workflow as: create a dataset, define evaluators, run an experiment, analyze results, configure online evaluators, monitor runs/threads, and establish feedback loops (`https://docs.langchain.com/langsmith/evaluation`). The observability entry page identifies tracing/observability as the product area (`https://docs.langchain.com/langsmith/observability`). These docs were used for product semantics only; API behavior below is verified against installed source.

## Executive conclusion

The corrected Evidence Workbench access pattern is **CLI-first where native,
SDK-direct where programmatic precision is needed, and explicit HE tools only
for SDK-only or high-friction recurring work**:

1. **LangSmith CLI is required HE expertise.** The local `.venv` did not expose
   a `langsmith` console script, but that is a setup fact, not proof that
   LangSmith CLI workflows are out of scope. The local `langsmith-dataset`,
   `langsmith-trace`, and `langsmith-evaluator` skills define broad
   CLI-native coverage for routine HE workflows.
2. **Use the LangSmith SDK directly** when CLI coverage is missing, too coarse,
   or when HE needs programmatic composition: datasets, examples, experiments,
   runs, run trees, feedback, summaries, comparison URLs, and evaluator
   constructors.
3. **Use OpenEvals directly** before inventing evaluator logic.
4. **Introduce explicit HE tools only after CLI-vs-SDK comparison.** A tool is
   justified when a needed capability is not comfortably available through CLI,
   the SDK provides it, HE needs it repeatedly, and writing SDK code each time
   would materially reduce reliability or speed.
5. **Do not introduce raw wrapper tools** merely to rename LangSmith operations.
   Tool candidates must map to specific SDK-only or high-friction HE workflows,
   not to a parallel Meta Harness evidence-platform vocabulary.
6. **TICKET-001 approves no explicit HE tools.** Its output is evidence for
   TICKET-006, which may decide whether any SDK-only/high-friction workflow
   justifies a tool.

## Capability audit

### 1. Datasets and examples

#### What exists

LangSmith SDK has first-class dataset and example lifecycle APIs:

- `Client.create_dataset(...)` creates datasets with `description`, `data_type`, input/output schemas, transformations, and metadata (`client.py:4990-5000`). It adds runtime metadata and source information into `extra.metadata` / `extra.source` before POSTing to `/datasets` (`client.py:5025-5053`) and returns a `Dataset` object (`client.py:5055-5061`).
- `Client.read_dataset(...)` resolves by exactly one of `dataset_name` or `dataset_id` (`client.py:5086-5092`) and GETs `/datasets` or `/datasets/{id}` (`client.py:5104-5116`).
- `Client.list_datasets(...)` supports ID, type, exact/contains name, metadata, and limit filters (`client.py:5237-5246`), serializes metadata to JSON (`client.py:5277-5278`), paginates through `_get_paginated_list` (`client.py:5279-5288`), and returns `Dataset` objects.
- `Client.diff_dataset_versions(...)` compares two tagged or timestamped versions (`client.py:5134-5141`) via `/datasets/{id}/versions/diff` (`client.py:5182-5201`).
- `Client.update_dataset_tag(...)` moves a tag to the exact `as_of` dataset version (`client.py:5319-5334`) by PUTing `/datasets/{id}/tags` (`client.py:5368-5377`).
- `Client.upload_csv(...)` exists for CSV ingestion with input/output column keys and optional dataset name/description/type (`client.py:1913-1922`), sending to `/datasets/upload` and returning a `Dataset` (`client.py:1965-2008`).

Examples support bulk, single-row, deterministic IDs, splits, metadata, source-run linkage, and attachments:

- `Client.create_examples(...)` accepts exactly one of `dataset_name` or `dataset_id`, a list of `ExampleCreate`/dict rows, `dangerously_allow_filesystem`, bounded `max_concurrency`, and legacy `inputs`/`outputs`/`metadata`/`splits`/`source_run_ids`/`ids` kwargs (`client.py:6170-6200`). Return includes `count`, `example_ids`, and `as_of` (`client.py:6204-6206`, `client.py:6356-6358`).
- The preferred modern shape is a list where each example carries its full fields in one object; source notes this changed in `langsmith` 0.3.11 (`client.py:6207-6215`).
- Legacy bulk creation supports deterministic example IDs through `ids`; if no ID is provided it generates `uuid.uuid4()` (`client.py:6254-6261`, `client.py:6291-6309`).
- `Client.create_example(...)` supports a single `example_id`, `source_run_id`, `use_source_run_io`, `use_source_run_attachments`, and `attachments` (`client.py:6402-6417`, `client.py:6424-6449`).
- `Client.list_examples(...)` supports dataset ID/name, example IDs, `as_of` version/tag/timestamp, splits, metadata, structured `filter`, attachments opt-in, offset, and limit (`client.py:6546-6560`, `client.py:6564-6583`).
- `Client.update_example(...)` updates inputs, outputs, metadata, split, dataset, and attachments (`client.py:6671-6682`) and patches `/examples/{id}` in the non-multipart fallback path (`client.py:6727-6756`).
- `Client.update_examples(...)` bulk-updates rows and explicitly says unspecified fields are not updated (`client.py:6758-6780`).

#### Identifiers and fields

- Dataset fields include `id`, `created_at`, `modified_at`, counts, schemas, transformations, and `metadata` (`schemas.py:247-259`).
- Example base fields are `dataset_id`, `inputs`, `outputs`, and `metadata` (`schemas.py:81-88`).
- Example creation fields include optional `id`, `created_at`, `inputs`, `outputs`, `metadata`, `split`, `attachments`, `use_source_run_io`, `use_source_run_attachments`, and `source_run_id` (`schemas.py:102-115`).
- Persist at minimum: `dataset_id`, `dataset_name`, `dataset_url`, `dataset_version_tag/as_of`, `example_id`, `example_split`, and any `source_run_id` used to derive examples.

#### Expansion, pagination, privacy

- Dataset/example listing is paginated through `_get_paginated_list`, which defaults `limit` to 100 and uses offset pagination (`client.py:1780-1810`).
- Example attachments are excluded by default and only selected if `include_attachments=True` (`client.py:6559`, `client.py:6653-6654`).
- Dataset rows may include hidden examples, gold answers, metadata, attachments, source traces, and private splits. Raw examples should default to `he_private`; Developer-safe outputs should contain only allowed references and aggregate facts.

#### Recommended access path

- Routine dataset/example work: use LangSmith CLI when first-party CLI coverage
  is sufficient.
- SDK extension path: use the SDK for deterministic IDs, splits, attachments,
  source-run linkage, version/tag workflows, and other precision the CLI does
  not expose comfortably.
- Explicit tool candidate only if HE repeatedly needs one of those SDK-only
  workflows and direct SDK code is too error-prone or slow.

### 2. Experiments / sessions / evaluation execution

#### What exists

LangSmith uses `TracerSession` objects for projects/sessions, and experiments are represented by sessions associated with reference datasets:

- `Client.create_project(...)` creates a project/session with `description`, `metadata`, `project_extra`, `upsert`, and `reference_dataset_id` (`client.py:4587-4596`). It stores metadata in `extra.metadata`, generates an ID, and POSTs to `/sessions` (`client.py:4610-4633`).
- `Client.read_project(...)` resolves by exactly one of `project_id` or `project_name`, optionally including aggregate stats (`client.py:4710-4717`, `client.py:4731-4750`).
- `Client.list_projects(...)` supports filters for project IDs, name, name contains, reference dataset, dataset version, stats, limit, and metadata (`client.py:4886-4898`, `client.py:4899-4917`).
- `langsmith.evaluation.evaluate(...)` accepts target functions/runnables/existing experiments/experiment tuples, `data`, evaluators, summary evaluators, metadata, experiment prefix, description, concurrency, repetitions, existing experiment, upload control, and error handling (`evaluation/_runner.py:137-156`). The method docs confirm `data` can be a dataset name, list of examples, or generator (`evaluation/_runner.py:165-167`) and return `ExperimentResults` or `ComparativeExperimentResults` (`evaluation/_runner.py:199-201`).
- `Client.evaluate(...)` delegates to `langsmith.evaluation._runner.evaluate(...)` with the client injected (`client.py:9666-9725`, `client.py:9910-9929`).
- `ExperimentResults` exposes `experiment_name`, `experiment_id`, `get_dataset_id()`, `url`, and `comparison_url` (`evaluation/_runner.py:536-592`). The comparison URL is constructed as `/datasets/{dataset_id}/compare?selectedSessions={experiment.id}` when the experiment URL is available (`evaluation/_runner.py:573-582`).
- `Client.get_experiment_results(...)` fetches aggregate experiment data by name or project ID, supports lightweight `preview`, comparative experiment IDs, filters, and limit (`client.py:10241-10249`). It returns feedback stats, run stats, and an iterator of examples-with-runs (`client.py:10250-10269`, `client.py:10310-10334`).
- `evaluate_comparative(...)` compares existing experiments with row-level comparative evaluators, metadata, nested-run loading, and randomized order (`evaluation/_runner.py:673-684`). It requires shared reference datasets (`evaluation/_runner.py:874-878`) and creates a comparative experiment via `Client.create_comparative_experiment(...)` (`evaluation/_runner.py:887-894`).
- `Client.create_comparative_experiment(...)` creates a comparative experiment over two or more experiment IDs plus reference dataset, metadata, and optional explicit ID (`client.py:8569-8579`), then POSTs to `/datasets/comparative` (`client.py:8605-8626`).

#### Identifiers and fields

Persist at minimum:

- `langsmith_project_id` / `session_id` / experiment ID.
- `langsmith_project_name` / experiment name.
- `reference_dataset_id`.
- `experiment_url` and `comparison_url` when available.
- `comparative_experiment_id` for pairwise runs.
- Evaluation metadata keys binding experiment to Meta Harness project/candidate/phase.

`TracerSession` fields include `id`, `start_time`, `end_time`, `description`, `name`, `extra`, `tenant_id`, and `reference_dataset_id` (`schemas.py:701-722`). `TracerSessionResult` adds run counts, latency, token/cost stats, feedback stats, run facets, and error rate (`schemas.py:755-784`, `schemas.py:1400-1401`).

#### Expansion, pagination, privacy

- `get_experiment_results(preview=True)` intentionally fetches `inputs_preview`/`outputs_preview` instead of full inputs/outputs from S3 for lower bandwidth (`client.py:10257-10259`).
- `examples_with_runs` is an iterator, not a materialized list (`schemas.py:1404-1415`, `client.py:10298-10334`).
- Experiment results may include hidden examples, reference outputs, feedback comments, and run outputs. Aggregate summaries can be `internal`; row-level examples and full runs default `he_private`.

#### Recommended access path

- Use CLI for routine experiment inspection if first-party CLI coverage is
  sufficient.
- Use SDK/OpenEvals code for evaluation execution, comparative experiments,
  metadata binding, preview summaries, and programmatic comparison workflows.
- Explicit tool candidate only for a repeated standard evaluation or comparison
  workflow that is SDK-only and high-friction.

### 3. Runs / traces / run trees

#### What exists

- `Client.read_run(run_id, load_child_runs=False)` reads a run by ID and returns a `Run` (`client.py:3745-3782`). If `load_child_runs=True`, it calls `_load_child_runs` before returning (`client.py:3780-3781`).
- `Client.list_runs(...)` supports project ID/name, run type, trace ID, reference example ID, query, structured filter, `trace_filter`, `tree_filter`, root selection, parent run ID, start time, error, explicit run IDs, selected fields, limit, and extra kwargs (`client.py:3840-3860`).
- The docs in source show filter syntax examples for run type, latency, token count, feedback key/score, error, tags, and timestamp (`client.py:3924-3948`).
- `list_runs` resolves project names to IDs (`client.py:3951-3961`), supplies a default selected field set (`client.py:3962-3990`), sends `/runs/query` through cursor pagination (`client.py:4000-4023`), and returns `Run` objects (`client.py:4024-4032`).
- `_get_cursor_paginated_list` follows response `cursors.next` until exhausted (`client.py:1812-1851`).
- `Client.read_thread(...)` is a convenience wrapper around `list_runs` for `thread_id`, requiring project ID/name and building a structured `eq(thread_id, ...)` filter (`client.py:3784-3838`).
- `Client.get_run_url(...)` constructs a UI URL from run and project/session identifiers but is explicitly “not recommended” inside agent runtime and more for after-the-fact analysis/ETL (`client.py:4246-4282`).

#### Default fields and expansion

Default `list_runs` fields are:

```txt
app_path, completion_cost, completion_tokens, dotted_order, end_time, error,
events, extra, feedback_stats, first_token_time, id, inputs, name, outputs,
parent_run_id, parent_run_ids, prompt_cost, prompt_tokens, reference_example_id,
run_type, session_id, start_time, status, tags, total_cost, total_tokens, trace_id
```

This list is source-defined at `client.py:3962-3990`. `child_runs` are not populated by default; the `Run` schema states they are loaded only when instructed and are heavier (`schemas.py:393-403`). Use `read_run(load_child_runs=True)` for full selected run trees.

#### Identifiers and fields

`RunBase` fields include `id`, `name`, `start_time`, `run_type`, `end_time`, `extra`, `error`, `serialized`, `events`, `inputs`, `outputs`, `reference_example_id`, `parent_run_id`, `tags`, and `attachments` (`schemas.py:306-365`). `Run` adds `session_id`, `child_run_ids`, `child_runs`, `feedback_stats`, `app_path`, `manifest_id`, `status`, token counts, costs, and first-token time (`schemas.py:393-436`). Persist `run_id`, `trace_id`, `parent_run_id`, `session_id`, `reference_example_id`, and any `thread_id` stored in run metadata.

#### Privacy

Raw runs can contain user inputs, model outputs, tool call arguments/results, serialized objects, metadata, events, errors, stack traces, attachments, feedback stats, and reference example IDs. Raw traces and full trees are `he_private` by default. EBDR-1 feedback should route only allowed references and permitted metrics.

#### Recommended access path

- Use CLI for routine run/trace listing, inspection, and export when first-party
  CLI coverage is sufficient.
- Use SDK code for selected fields, structured filters, cursor pagination,
  custom serialization, or child-run hydration beyond CLI coverage.
- Explicit tool candidate only for repeated SDK-only filtering or trace-tree
  workflows that HE needs often and that are cumbersome to write each time.

### 4. Feedback / scores / evaluator outputs

#### What exists

- `Client.create_feedback(...)` supports `run_id`, `trace_id`, `project_id`, `key`, `score`, `value`, `correction`, `comment`, `source_info`, source type, `source_run_id`, explicit `feedback_id`, `feedback_config`, comparative experiment ID, feedback group ID, extra, error, session ID, and start time (`client.py:7355-7382`).
- Source docs state `trace_id` enables batched/backgrounded feedback ingestion and is encouraged for latency-sensitive environments (`client.py:7383-7389`).
- Feedback may be API or model sourced; `source_run_id` is written into `feedback_source.metadata.__run.run_id` when provided (`client.py:7507-7525`).
- `FeedbackConfig` supports `continuous`, `categorical`, and `freeform` feedback, with min/max and categorical choices (`schemas.py:665-676`).
- `Client.list_feedback(...)` filters by run IDs, feedback keys, source type, limit, and extra kwargs, and paginates through `/feedback` (`client.py:7680-7721`).
- Presigned feedback token APIs exist for browser-side feedback without exposing API keys (`client.py:7790-7853`).
- OpenEvals `EvaluatorResult` is a typed dict with `key`, `score`, `comment`, `metadata`, and `source_run_id` (`openevals/types.py:18-24`). `score` is `float | bool` (`openevals/types.py:15`).

#### Normalization guidance

- Binary pass/fail maps cleanly to `score: bool` or numeric 0/1.
- Reward/continuous metrics map to numeric `score` with a `FeedbackConfig(type="continuous", min=..., max=...)` when persisted.
- Categorical/freeform values belong in `value` and/or categorical `FeedbackConfig` rather than overloading numeric score.
- Judge explanations may appear in `comment` or evaluator metadata and must be treated as HE-private until redacted.

#### Recommended access path

- Use CLI for feedback inspection if first-party CLI coverage exists.
- Use SDK code for feedback writes, configs, source metadata, comparative/group
  IDs, and score/comment queries not comfortably exposed by CLI.
- Use `.agents/skills/langsmith-evaluator-feedback/SKILL.md` for EBDR-1
  evaluator-to-optimizer feedback. Do not recreate EBDR as a Workbench tool.
- Explicit tool candidate only if feedback inspection/write workflows are
  SDK-only, frequent, and materially helped by a direct HE tool.

### 5. CLI capability correction

#### What exists

In the installed Python SDK environment inspected by TICKET-001, the
`langsmith==0.7.37` package did **not** expose a local `langsmith` console
script:

- The installed LangSmith distribution metadata identifies the package as the client library (`METADATA:2-4`).
- Its entry points file contains only `[pytest11] langsmith_plugin = langsmith.pytest_plugin` (`entry_points.txt:1-2`). There is no `[console_scripts]` group and no `langsmith` CLI entry point.
- `.venv/bin/langsmith` is absent in the checked environment.

That finding only describes this repo’s local Python package setup. It does not
answer what first-party LangSmith CLI tooling provides, and it must not be used
to classify CLI workflows as out of scope.

#### Skill-grounded CLI coverage

The local LangSmith skills define the practical first-party CLI workflows HE is
expected to know:

- `langsmith-dataset` covers dataset list/get/create/delete/export/upload,
  example list/create/delete, experiment list/get, dataset upload/export JSON
  shape, `--limit`, `--yes`, and destructive-operation confirmation behavior.
- `langsmith-trace` covers trace list/get/export, run list/get/export,
  thread list/get, project list, trace-vs-run semantics, hierarchy behavior,
  JSONL export shape, root-vs-flat filtering, and common filters such as
  `--project`, `--limit`, `--include-metadata`, `--include-io`, `--full`,
  `--show-hierarchy`, `--run-type`, `--trace-ids`, `--last-n-minutes`,
  `--since`, `--error`, `--no-error`, `--name`, latency/token filters,
  `--tags`, and raw `--filter`.
- `langsmith-evaluator` covers evaluator list/upload/delete, offline evaluator
  upload with `--dataset`, online evaluator upload with `--project`, code-only
  CLI upload, sandbox limits, one-metric-per-evaluator behavior, local
  `evaluate()` preference for LLM-as-judge, and the rule to never use `--yes`
  unless explicitly requested.

No local skill describes direct `langsmith feedback ...` lifecycle commands.
Feedback can be queried indirectly through trace/run filters in some cases, but
feedback creation, list APIs, configs, source metadata, comparative IDs, and
presigned feedback token workflows remain SDK-extension territory based on this
audit.

#### Recommended access path

Treat LangSmith CLI as required Harness Engineer operational expertise. The
skill-grounded CLI coverage above is enough for TICKET-006 to compare routine
command workflows against SDK extension points. Do not approve explicit tools
from this ticket.

### 6. Export / local working files

#### What exists

LangSmith export and inspection should be approached as a CLI-vs-SDK capability
question, not as a new product abstraction. SDK-returned Pydantic objects and
typed dicts can be serialized by HE scripts when code is the right medium.

- Runs/examples/datasets are Pydantic models or typed dicts returned by SDK methods shown above.
- `list_runs(select=[...])` supports field narrowing (`client.py:3840-3860`, `client.py:3912-3915`, `client.py:3962-3992`).
- `read_run(load_child_runs=True)` supports complete run-tree loading for a selected trace (`client.py:3745-3782`).
- `get_experiment_results(preview=True)` supports preview-mode summaries that avoid full input/output S3 fetches (`client.py:10241-10259`).
- `get_test_results(...)` can materialize record-level experiment information as a Pandas DataFrame, but source warns it is beta and DB results may lag evaluation completion (`client.py:4772-4797`). It flattens rows through `pd.json_normalize` (`client.py:4881-4884`).

#### Practical local formats

For HE-private local analysis files:

- JSONL for streaming collections: run index, feedback index, example index.
- JSON for structured summaries: experiment summary, selected trace tree.
- Markdown only for human/subagent-generated analysis summaries.
- When local files are produced, include enough context for HE to reproduce the
  query: source command or SDK call, selected fields, local post-filter if any,
  created timestamp, source package version, and object IDs.

Do **not** auto-load raw full experiments into model context. Full exports are
for explicit HE forensic/debug work.

#### Recommended access path

- Prefer CLI export when first-party CLI output is sufficient.
- Use SDK serialization when HE needs selected fields, custom filters, or
  programmatic composition beyond CLI.
- Consider an explicit HE tool only if the SDK workflow is repeated,
  high-friction, and not comfortably covered by CLI.

### 7. Security / privacy / redaction

#### What exists

LangSmith has ingestion-time privacy hooks:

- `Client.__init__` accepts `anonymizer`, `hide_inputs`, `hide_outputs`, `hide_metadata`, `omit_traced_runtime_info`, and buffered run processing hooks (`client.py:821-849`, `client.py:856-923`).
- Constructor docs state `anonymizer` masks serialized run inputs/outputs before sending, `hide_inputs` hides or transforms run inputs, `hide_outputs` hides or transforms outputs, and `hide_metadata` hides or transforms metadata (`client.py:875-892`).
- `_hide_run_inputs`, `_hide_run_outputs`, and `_hide_run_metadata` implement the behavior: `True` drops the whole field, an anonymizer transforms JSON copies of inputs/outputs, `False` returns original, and callable hooks transform fields (`client.py:2456-2481`).
- `_run_transform` applies input/output/metadata hiding before upload, filters streaming token event payloads, and strips serialized graph data for non-LLM/prompt runs (`client.py:2026-2063`).
- `_filter_new_token_events` removes `kwargs` from new token events to prevent streaming LLM output from being uploaded through events (`client.py:2483-2500`).

#### Privacy risks

Raw evidence-bearing outputs may include:

- Hidden dataset examples and private splits.
- Gold/reference outputs.
- Judge prompts and rubric text.
- Evaluator reasoning in comments or run outputs.
- User inputs, model outputs, tool arguments/results.
- Serialized chain/config metadata.
- Errors, stack traces, runtime metadata, attachments, and possibly credentials if upstream code logged them.

#### Visibility defaults

- **Raw traces / run trees / examples / full dumps:** `he_private`.
- **Filtered run indexes with inputs/outputs omitted:** `he_private` or `internal`, depending on fields.
- **Aggregate experiment summaries:** `internal` by default; `stakeholder_visible` only after analytics-source validation.
- **Developer feedback:** `developer_safe` only after explicit EBDR-1 redaction.

#### Recommended access path

- Ingestion-time privacy hooks are SDK configuration.
- EBDR-1 feedback shaping belongs to `.agents/skills/langsmith-evaluator-feedback/SKILL.md`.
- A helper tool is only a candidate if HE repeatedly needs a narrow SDK
  configuration workflow and direct SDK code is too error-prone.

### 8. OpenEvals primitives

#### What exists

OpenEvals is installed and provides reusable evaluator primitives:

- `EvaluatorResult` shape is `key`, `score`, `comment`, `metadata`, `source_run_id`; score type is `float | bool` (`openevals/types.py:15-24`).
- Exact match compares JSON-normalized outputs and reference outputs and returns an `EvaluatorResult` (`openevals/exact.py:8-19`, `openevals/exact.py:31-39`).
- JSON structured match supports `list_match_mode` values `superset`, `subset`, `same_elements`, and `ordered` (`openevals/json/match.py:61-70`).
- LLM-as-judge scoring constructs boolean or continuous score schemas and optional reasoning (`openevals/llm.py:70-117`).
- Pyright code evaluator exposes `create_pyright_evaluator(...)` with extraction strategies `none`, `llm`, and `markdown_code_blocks` (`openevals/code/pyright.py:99-153`).
- Trajectory match evaluator exposes strict, unordered, subset, and superset modes plus tool-argument match modes (`openevals/trajectory/match.py:21-29`, `openevals/trajectory/match.py:67-104`).

#### Recommended access path

OpenEvals evaluator construction is `sdk_native` / `he_skill`. Prefer these
primitives before custom evaluator logic. Only consider an explicit HE tool for
repeated evaluator-construction boilerplate that is materially safer or faster
as a direct tool.

## Final access-path recommendation

Use a **CLI-vs-SDK HE capability matrix**:

```txt
cli_native:
  first-party LangSmith CLI covers the workflow; teach HE the command workflow

sdk_native:
  SDK/OpenEvals code is the natural medium for evaluator execution,
  programmatic composition, or API precision

sdk_extends_cli:
  SDK provides capability or precision beyond CLI; evaluate HE frequency and
  friction

he_skill:
  teach the workflow in skills/prompts/docs; no product tool

explicit_tool_candidate:
  SDK-only/high-friction HE workflow that is repeated often enough to justify a
  direct tool
```

This corrects the earlier conclusion. The useful hybrid is **LangSmith CLI +
LangSmith SDK/OpenEvals expertise**, with explicit HE tools only for carefully
identified SDK-only or high-friction gaps. TICKET-001 identifies no approved
explicit tool candidates; it forwards possible SDK-extension areas to
TICKET-006 for reconciliation.

## Follow-up validation steps

Live LangSmith credentials are not required for this ticket. If runtime validation is later desired, run a small non-private dataset/experiment and verify:

1. `create_dataset` / `create_examples` returned IDs and `as_of` values.
2. `evaluate(blocking=False)` returns an experiment ID and comparison URL.
3. `get_experiment_results(preview=True)` omits heavy full inputs/outputs.
4. `list_runs(select=[...])` returns only selected fields.
5. `read_run(load_child_runs=True)` hydrates `child_runs` for a known nested trace.
6. Redaction hooks remove inputs/outputs/metadata before upload.
