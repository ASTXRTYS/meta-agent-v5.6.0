# LangSmith CLI vs SDK Capability Matrix For Harness Engineer

Source-audited for `TICKET-001` on 2026-04-26, corrected after the
alignment review for `TICKET-006`, and updated from the local LangSmith skills
on 2026-04-27. This is a `local-docs/` research artifact, not a product spec.

## Corrected access classification

- `cli_native` — first-party LangSmith CLI covers the HE workflow; teach it as
  required Harness Engineer operational expertise.
- `sdk_native` — the SDK covers the capability cleanly; use it directly in HE
  scripts or backend code when code is the natural medium.
- `sdk_extends_cli` — the SDK provides precision, composition, or programmatic
  control beyond the CLI; investigate as a possible HE ergonomic tool only if
  the workflow is frequent and high-friction.
- `he_skill` — the right answer is procedural competence, prompt/skill
  guidance, or a repeatable CLI/SDK workflow, not a product tool.
- `explicit_tool_candidate` — exceptional: the capability is not comfortable
  through CLI, the SDK provides it, HE needs it repeatedly, and a direct tool
  would materially improve reliability or speed.

## Source preflight matrix

| Item | Finding | Citation | Impact |
|---|---|---|---|
| Project dependency floor | `langsmith>=0.7.25`; Python `>=3.12` | `meta_harness/pyproject.toml:9`, `meta_harness/pyproject.toml:20` | Installed SDK source path is `.venv/lib/python3.12/...`, not stale `.venv/lib/python3.11/...` anchors. |
| Installed LangSmith SDK | `langsmith==0.7.37` | `.venv/lib/python3.12/site-packages/langsmith-0.7.37.dist-info/METADATA:2-4` | Primary source for SDK behavior already audited in TICKET-001. |
| Installed OpenEvals | `openevals==0.2.0` | `.venv/lib/python3.12/site-packages/openevals-0.2.0.dist-info/METADATA:2-4` | Primary source for evaluator primitives. |
| Local CLI setup | The audited `.venv` had no `langsmith` console script; the SDK package entry points exposed only the pytest plugin. | `.venv/lib/python3.12/site-packages/langsmith-0.7.37.dist-info/entry_points.txt:1-2` | Setup fact only. It does not prove LangSmith CLI is unsupported or out of scope. |
| Local skill source | `langsmith-dataset`, `langsmith-trace`, and `langsmith-evaluator` define the HE-facing CLI workflows audited below. | Local skill invocations on 2026-04-27 | These skills are sufficient for TICKET-001’s CLI workflow audit except direct feedback CLI coverage, which they do not define. |

## Required CLI-vs-SDK capability matrix

| Capability | CLI command(s) | Skill source | CLI output / behavior notes | Relevant flags | Safety / non-interactive notes | Equivalent SDK method(s) | SDK extends CLI? | HE workflow relevance | Classification | Explicit tool candidate rationale |
|---|---|---|---|---|---|---|---|---|---|---|
| Dataset list/get/create/delete/export/upload | `langsmith dataset list`; `langsmith dataset get <name-or-id>`; `langsmith dataset create --name <name>`; `langsmith dataset delete <name-or-id>`; `langsmith dataset export <name-or-id> <output-file>`; `langsmith dataset upload <file> --name <name>` | `langsmith-dataset`; also listed in `langsmith-trace` command structure | Routine dataset lifecycle is CLI-native. Upload expects local JSON examples with `inputs` and optional `outputs`; export writes a local JSON file. | `--limit`; `--yes`; `--description` in examples | Delete and overwrite-style flows prompt. For agent workflows, do not pass `--yes` unless the user explicitly approved the destructive operation. | `Client.create_dataset`; `read_dataset`; `list_datasets`; `upload_csv`; `diff_dataset_versions`; `update_dataset_tag` | Yes, for schemas, metadata, version diff, tag movement, CSV ingestion details, and precise programmatic control. | Core HE work for eval dataset creation, inspection, export, and upload. | `cli_native` for routine lifecycle; `sdk_extends_cli` for version/schema/tag precision. | Candidate only for repeated SDK-only dataset version/tag/schema workflows. No tool for basic CRUD/export/upload. |
| Example list/create/delete | `langsmith example list --dataset <name>`; `langsmith example create --dataset <name> --inputs <json>`; `langsmith example delete <example-id>` | `langsmith-dataset`; also listed in `langsmith-trace` command structure | Basic example inspection, creation, and deletion are CLI-native. Skill examples show `--outputs` for expected outputs. | `--dataset`; `--inputs`; `--outputs`; `--limit` | Delete prompts; avoid `--yes` unless explicitly approved. Raw examples may contain hidden eval material. | `Client.create_examples`; `create_example`; `list_examples`; `update_example`; `update_examples` | Yes, for deterministic IDs, bulk create/update, splits, attachments, source-run linkage, and `as_of` version reads. | Core HE work for creating optimization/regression datasets from traces. | `cli_native` for simple rows; `sdk_extends_cli` for precise row provenance and reproducibility. | Candidate only if deterministic bulk example operations or source-run-derived examples become frequent and CLI cannot express them safely. |
| Experiment list/get | `langsmith experiment list --dataset <name>`; `langsmith experiment get <name>` | `langsmith-dataset`; `langsmith-trace` command structure | Experiment inspection is CLI-native in the skills. The skills do not define CLI experiment creation or comparative experiment creation. | `--dataset` | Read-only inspection is safe; specify dataset/project context to avoid ambiguity. | `create_project`; `read_project`; `list_projects`; `evaluate`; `aevaluate`; `evaluate_comparative`; `get_experiment_results`; `create_comparative_experiment` | Yes, for execution, metadata binding, preview summaries, comparative experiments, concurrency, repetitions, and programmable result iteration. | Required for candidate comparison and evaluation result review. | `cli_native` for inspection; `sdk_native` / `sdk_extends_cli` for evaluation execution and comparisons. | Candidate only for a repeated standard evaluation/comparison workflow where direct SDK invocation is boilerplate-heavy. |
| Evaluation execution | No direct CLI evaluation-run command is defined by the local skills; uploaded evaluators auto-run when experiments are run through SDK/local `evaluate()` workflows. | `langsmith-evaluator` | Skill directs HE to use local `evaluate()` / TypeScript `evaluate()` for experiments and uploaded evaluators for automatic execution. | SDK args, not CLI flags: evaluators, metadata, experiment prefix, concurrency, repetitions | Evaluation runs can expose hidden examples, judge prompts, model outputs, and comments. Keep raw outputs HE-private. | `langsmith.evaluate`; `Client.evaluate`; `aevaluate`; OpenEvals evaluator constructors | SDK is the natural surface. | Central HE capability for offline development evals and regression gates. | `sdk_native` / `he_skill` | Candidate only for repeated project-standard run shapes after CLI-vs-SDK reconciliation; not for generic evaluation. |
| Trace list/get/export | `langsmith trace list`; `langsmith trace get <trace-id>`; `langsmith trace export <dir>` | `langsmith-trace` | Trace means complete execution tree. `trace get` returns hierarchy; `trace export` creates one JSONL file per trace with one run per line. Trace filters apply to the root run. | `--project`; `--limit`; `--include-metadata`; `--include-io`; `--full`; `--show-hierarchy`; `--trace-ids`; `--last-n-minutes`; `--since`; `--error`; `--no-error`; `--name`; `--min-latency`; `--max-latency`; `--min-tokens`; `--tags`; `--filter` | Prefer explicit `--project`. `--include-io` / `--full` can expose user inputs, model outputs, tool data, and private eval material. Full exports default `he_private`. | `Client.read_run(load_child_runs=True)`; `list_runs(trace_id=...)`; selected-field serialization | Yes, for selected fields, custom serialization, cursor pagination, and SDK-controlled tree hydration. | Primary HE forensic workflow; start with traces for trajectory/debug analysis. | `cli_native` for routine trace inspection/export; `sdk_extends_cli` for precision exports. | Candidate only for repeated selected-field trace-tree extraction not comfortable through CLI. |
| Run list/get/export | `langsmith run list`; `langsmith run get <run-id>`; `langsmith run export <file>` | `langsmith-trace` | Run means a single node/span. Run listing is flat and filters can match any run. Run export writes a single JSONL file. | `--project`; `--limit`; `--run-type`; `--trace-ids`; `--last-n-minutes`; `--since`; `--error`; `--no-error`; `--name`; `--min-latency`; `--max-latency`; `--min-tokens`; `--tags`; `--filter` | Prefer explicit `--project`. Flat run exports can include sensitive inputs/outputs when `--include-io` / `--full` is used. | `Client.list_runs`; `read_run`; `get_run_url` | Yes, for `select`, `trace_filter`, `tree_filter`, root/parent constraints, reference-example filters, and cursor pagination. | Needed for focused span-level diagnostics, performance/cost queries, and evaluator debugging. | `cli_native` for common querying; `sdk_extends_cli` for structured filters/field selection. | Candidate only for high-friction structured filter construction or selected-field run indexes. |
| Thread list/get and project list | `langsmith thread list`; `langsmith thread get`; `langsmith project list` | `langsmith-trace` | Threads represent conversation-level grouping; projects scope traces/runs. | `--project`; `--limit` where applicable | Always resolve project context before trace/run work to avoid cross-project evidence mixing. | `Client.read_thread`; `list_projects`; `read_project` | Yes, for thread filter composition and project/session metadata/stats. | Important for online production evals and project-scoped investigations. | `cli_native` for lookup; `sdk_extends_cli` for metadata/stat queries. | Usually no explicit tool; teach as HE operational skill. |
| Evaluator list/upload/delete | `langsmith evaluator list`; `langsmith evaluator upload <file> --name <name> --function <function> --dataset <dataset> --replace`; `langsmith evaluator upload <file> --name <name> --function <function> --project <project> --replace`; `langsmith evaluator delete <name>` | `langsmith-evaluator`; also listed in `langsmith-trace` command structure | CLI uploads code evaluators. Offline evaluators target datasets and use `(run, example)`. Online evaluators target projects and use `(run)`. Uploaded evaluators run in a sandbox and return one metric per evaluator. | `--name`; `--function`; `--dataset`; `--project`; `--replace`; `--yes` mentioned only as a destructive-operation bypass to avoid unless explicitly requested | Uploaded evaluators are code-only in this skill. LLM-as-judge upload is not supported by CLI. Delete prompts; never use `--yes` unless explicitly requested. | Local `evaluate(evaluators=[...])`; OpenEvals exact/JSON/LLM/code/trajectory evaluators; LangSmith evaluator execution APIs | Yes, for local LLM-as-judge, package-rich evaluator development, structured evaluator constructors, and local debugging. | Core HE work for automated scoring. | `cli_native` for uploaded code evaluator lifecycle; `sdk_native` / `he_skill` for local and LLM-as-judge evaluators. | Candidate only for repeated evaluator-construction boilerplate; not for evaluator upload/list/delete. |
| LLM-as-judge evaluator construction | No CLI upload support in the local skill. | `langsmith-evaluator` | Skill explicitly says LLM-as-judge upload is currently not supported by CLI; prefer local evaluators with `evaluate(evaluators=[...])`. | Not CLI-native | Judge prompts, rubrics, comments, and reasoning default HE-private. | OpenEvals LLM evaluators; local LangChain/OpenAI structured-output judges | SDK/OpenEvals are the correct surface. | High-value HE work for subjective quality evaluation. | `sdk_native` / `he_skill` | Candidate only for repeated boilerplate that maps directly to OpenEvals/LangSmith primitives. |
| Feedback list/create/filter | No direct `langsmith feedback ...` commands are described by the local skills. Trace filtering examples can query feedback-like predicates through `--filter`, but that is not a feedback lifecycle command. | Absence across `langsmith-dataset`, `langsmith-trace`, and `langsmith-evaluator` | CLI skill coverage is incomplete for direct feedback objects. HE can inspect feedback indirectly through trace/run/experiment outputs and raw filters, but feedback writes/configs are SDK territory based on current skill evidence. | `--filter 'and(eq(feedback_key, ...), gte(feedback_score, ...))'` on trace/run queries | Feedback comments may contain judge reasoning/rubric-sensitive material. Developer-visible feedback must go through EBDR redaction. | `Client.create_feedback`; `list_feedback`; feedback configs; presigned feedback token APIs | Yes. | Required for score/comment analysis, comparative feedback, and evaluator result routing. | `sdk_extends_cli` | Candidate only if direct feedback inspection/write workflows are frequent and CLI/source remains insufficient after TICKET-006. |
| Dataset-from-traces workflow | `langsmith trace export ./traces --project <project> --limit <n> --full`; process JSONL locally; `langsmith dataset upload /tmp/dataset.json --name <name>` | `langsmith-dataset`; `langsmith-trace` | Skill-defined CLI+code workflow for turning traces into datasets. Export writes JSONL per trace; local processing extracts root inputs/outputs; upload expects array of examples. | `--project`; `--limit`; `--full`; upload `--name` | `--full` includes I/O and may expose private data. Process in `/tmp` or HE-private workspace; do not load full exports into model context by default. | `list_runs`; `read_run(load_child_runs=True)`; `create_examples`; `create_dataset` | Yes, for deterministic IDs, source-run linkage, splits, and attachment handling. | Core HE loop for turning production failures into evals. | `he_skill` using CLI + SDK as needed; `sdk_extends_cli` for provenance precision. | Candidate only for a repeated trace-to-dataset compiler with strict provenance/redaction needs. |
| Redaction/anonymizer configuration | No export redaction command is described beyond selective inclusion flags like `--include-io` / `--full`. | `langsmith-trace`; SDK audit source | CLI controls whether I/O is included in trace exports, but SDK ingestion-time privacy hooks are the richer control plane. | `--include-io`; `--full`; `--include-metadata` | Default raw evidence to `he_private`; omit I/O unless needed. | `Client(anonymizer=..., hide_inputs=..., hide_outputs=..., hide_metadata=...)` | Yes. | Needed to prevent leakage in production tracing and local exports. | `sdk_native` / `he_skill` | Candidate only for a narrow, repeated SDK redaction profile helper. |
| EBDR evaluator-to-optimizer feedback | Not a LangSmith CLI concern. | `.agents/skills/langsmith-evaluator-feedback/SKILL.md` referenced by TICKET-001 | Existing skill owns evaluator-to-optimizer packet shaping. LangSmith trace/score IDs can feed the skill, but Workbench must not recreate EBDR. | Not applicable | Must not leak rubrics, hidden examples, judge reasoning, or scoring logic. | Not a LangSmith SDK wrapper; uses LangSmith evidence references as inputs. | Not applicable. | Required for safe optimizer feedback. | `he_skill` | Not an explicit Workbench tool candidate. |

## Final TICKET-001 classifications for TICKET-006

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
  - none approved by TICKET-001
  - possible later candidates must survive TICKET-006 and satisfy the
    SDK-only/high-friction/frequent-use rule
```

## Summary decision

The Harness Engineer should become excellent at LangSmith CLI, LangSmith SDK,
and OpenEvals usage. The local skills establish broad CLI-native coverage for
routine dataset, example, experiment, trace, run, thread, project, and uploaded
code-evaluator workflows. SDK/OpenEvals remain the right surfaces for
programmatic evaluation, precise filtering, feedback APIs, local/LLM evaluators,
comparison workflows, and privacy configuration. No explicit HE tool is approved
by this ticket.
