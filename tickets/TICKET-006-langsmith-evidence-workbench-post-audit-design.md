# TICKET-006 — Reconcile LangSmith CLI vs SDK Capabilities For Harness Engineer

## Status

COMPLETED — NO WORKBENCH TOOL SPEC NEEDED

## Priority

P1 — reconciliation ticket before any Evidence Workbench tool design or implementation

## Owner

Harness Engineer + Architect

## Completed On

2026-04-27

## Depends On

- TICKET-001 LangSmith CLI/SDK capability audit, completed with the CLI conclusion corrected
- `meta_harness/local-docs/langsmith-capability-matrix.md`
- `meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md`
- `meta_harness/local-docs/langsmith-ids-and-metadata-contract.md`
- `meta_harness/docs/specs/evaluation-evidence-workbench.md`
- `.agents/skills/langsmith-evaluator-feedback/SKILL.md`

## Problem

The Evidence Workbench docs previously drifted from the original audit intent.
They treated local absence of a `langsmith` console script in this repo’s
`.venv` as if LangSmith CLI workflows were out of scope, then replaced the
missing CLI/SDK comparison with an over-broad Meta Harness evidence platform.

TICKET-001 corrected that premise. It audited the HE-facing LangSmith CLI
workflows from local LangSmith skills, preserved the useful SDK/OpenEvals source
findings, and produced the initial CLI-vs-SDK matrix this ticket consumes.

The Harness Engineer must ship with strong LangSmith CLI and SDK expertise. The
reason to audit LangSmith was to answer:

```txt
1. What does LangSmith CLI provide natively?
2. What does the LangSmith SDK provide beyond the CLI?
3. Which SDK-only or high-friction capabilities does HE need to do the job well?
4. Which of those, if any, deserve explicit HE tools so the agent does not have
   to write SDK code repeatedly?
```

This ticket reconciles the completed TICKET-001 outputs before implementation.

## Goal

Produce a CLI-vs-SDK capability reconciliation for the Harness Engineer.

Every candidate operation is classified as one of:

```txt
cli_native                 # first-party LangSmith CLI should cover the HE workflow
sdk_native                 # SDK covers it; use SDK in HE scripts/code
sdk_extends_cli            # SDK adds precision/composition beyond CLI
he_skill                   # teach the workflow; no product tool
explicit_tool_candidate    # consider only for SDK-only/high-friction HE work
```

## Corrected Source Premise

TICKET-001 is the baseline source for this ticket. Its corrected premise is that
local absence of a `langsmith` console script is setup state only, not a
product-capability conclusion.

Correct premise:

```txt
LangSmith CLI is a core HE expertise surface.
LangSmith SDK is the programmatic extension surface.
Meta Harness explicit tools are exceptional ergonomic aids for SDK-only or
high-friction HE workflows.
```

## Reconciliation Matrix

TICKET-006 starts from the completed TICKET-001 matrix and local-doc outputs.
No capability below survives as an approved explicit tool candidate.

| Capability probe | CLI-native support | SDK support beyond CLI | HE job relevance | Classification | Explicit tool candidate? |
|---|---|---|---|---|---|
| List experiment runs | `langsmith experiment list --dataset <name>` and `langsmith experiment get <name>` cover experiment inspection. `langsmith run list` covers flat run listing with project, time, error, name, token, tag, trace ID, and raw filter flags. | `Client.list_runs(...)` adds `select`, `trace_filter`, `tree_filter`, root/parent constraints, reference-example filters, cursor pagination, and programmatic composition. | Needed for locating candidate evidence, focused diagnostics, and evaluator debugging. | `cli_native` for common inspection; `sdk_extends_cli` for selected-field indexes and structured filters. | No approved tool. Revisit only if repeated selected-field or structured-filter indexes become high-friction in real HE work. |
| Read run trace / tree | `langsmith trace get <trace-id>` and `langsmith trace export <dir>` cover complete execution tree inspection/export. Trace export writes JSONL per trace with one run per line. | `Client.read_run(load_child_runs=True)` hydrates child runs; SDK scripts can serialize selected fields and control tree shape. | Needed for trace inspection and trajectory debugging. | `cli_native` for routine trace inspection/export; `sdk_extends_cli` for precision tree hydration and custom serialization. | No approved tool. Revisit only for a repeated selected-field trace-tree extraction workflow not comfortably handled through CLI or short SDK scripts. |
| List run feedback | Local LangSmith skills do not define direct feedback lifecycle CLI commands. Trace/run filtering can query feedback-like predicates through raw filters in some cases. | `Client.list_feedback(...)`, `Client.create_feedback(...)`, feedback configs, source metadata, comparative experiment IDs, feedback group IDs, and presigned feedback token APIs are SDK-extension territory. | Needed for score/comment analysis, comparative feedback, evaluator result routing, and feedback visibility review. | `sdk_extends_cli` | No approved tool now. This is the strongest possible later candidate, but only after real HE workflows prove direct feedback inspection/write is frequent and too error-prone as SDK code. |
| Get dataset information | `langsmith dataset list/get/export/upload` and `langsmith example list/create/delete` cover routine dataset/example lifecycle. | `read_dataset`, `list_examples(as_of=...)`, deterministic IDs, bulk create/update, splits, attachments, source-run linkage, dataset version diff, and tag movement add precision beyond CLI. | Needed for eval program understanding, optimization/holdout split hygiene, and trace-to-dataset provenance. | `cli_native` for routine lifecycle; `sdk_extends_cli` for reproducible row/version/split workflows. | No approved tool. Revisit only for repeated deterministic bulk example or dataset-version/tag operations. |
| Query runs by filter | `langsmith trace list` and `langsmith run list` expose common filters plus raw `--filter`; trace filters apply to root runs and run filters can match flat spans. | SDK adds typed composition around `filter`, `trace_filter`, `tree_filter`, `select`, root/parent/reference-example constraints, and cursor pagination. | Needed for focused investigation, performance/cost analysis, and slice-specific trace retrieval. | `cli_native` for common filters; `sdk_extends_cli` for precise programmatic query construction. | No approved tool. Revisit only if structured filter construction repeatedly causes reliability problems. |
| Get experiment summary | `langsmith experiment get <name>` covers inspection in the skill-grounded CLI surface. | `get_experiment_results(...)` adds preview mode, feedback stats, run stats, example-with-runs iteration, comparative IDs, and comparison URL workflows. | Needed for candidate comparison, regression analysis, and aggregate experiment review. | `cli_native` for inspection; `sdk_native` / `sdk_extends_cli` for programmatic summaries and comparisons. | No approved tool. Revisit only for a repeated standard comparison workflow where direct SDK invocation is boilerplate-heavy. |

## SDK Capabilities That Genuinely Extend CLI Capability

- **Dataset/example precision:** deterministic and bulk example IDs, splits,
  attachments, source-run linkage, immutable `as_of` reads, dataset version diff,
  dataset tag movement, and schema/metadata control.
- **Experiment execution and comparison:** `evaluate()`, `aevaluate()`,
  `evaluate_comparative()`, `get_experiment_results(...)`, preview summaries,
  comparison URLs, concurrency, repetitions, metadata binding, and programmable
  result iteration.
- **Run and trace precision:** selected fields, structured filters,
  `trace_filter`, `tree_filter`, root/parent/reference-example constraints,
  cursor pagination, and SDK-controlled child-run hydration.
- **Feedback APIs:** feedback creation, direct listing, feedback configs,
  source-run metadata, comparative experiment IDs, feedback group IDs, and
  presigned feedback token workflows.
- **Privacy configuration:** SDK ingestion-time anonymizer and input/output/
  metadata hiding controls.
- **Evaluator construction:** OpenEvals exact, JSON, LLM-as-judge, code, and
  trajectory evaluator primitives plus local evaluator debugging.

## HE Workflows To Teach As Skills

- **Trace-first forensic workflow:** use `langsmith trace list/get/export` for
  trajectory inspection before reaching for SDK code.
- **Run-level focused query workflow:** use `langsmith run list/get/export` for
  span-level debugging, cost/latency filters, tags, errors, and project-scoped
  slices.
- **Dataset/example lifecycle workflow:** use CLI for routine list/get/create/
  delete/export/upload and example list/create/delete.
- **Dataset-from-traces workflow:** export traces, process JSONL locally, then
  upload examples, escalating to SDK only for deterministic provenance.
- **Evaluator upload workflow:** use CLI for code evaluator list/upload/delete
  and SDK/OpenEvals for local or LLM-as-judge evaluators.
- **EBDR-1 workflow:** use `.agents/skills/langsmith-evaluator-feedback/SKILL.md`
  for evaluator-to-optimizer feedback. LangSmith locators can feed the skill,
  but this ticket does not define a separate feedback tool family.

## SDK-Only Or High-Friction Workflows

These are extension areas, not approved tools:

| Workflow | Why SDK matters | Decision |
|---|---|---|
| Direct feedback inspection/write/configuration | Local skills do not define direct feedback lifecycle CLI commands; SDK exposes feedback list/create/config/source/comparative/group APIs. | Possible later candidate only after repeated HE usage proves high friction. |
| Selected-field trace-tree extraction | CLI exports full trace trees; SDK can hydrate child runs and serialize only selected fields. | Keep as SDK competence for now. |
| Structured run filter indexes | CLI exposes common flags and raw filter; SDK composes filters with selected fields, pagination, root/parent/reference-example constraints. | Keep as SDK competence for now. |
| Deterministic trace-to-dataset compilation | SDK supports deterministic IDs, source-run linkage, splits, attachments, and immutable version references. | Teach CLI+SDK workflow; no product tool yet. |
| Programmatic experiment comparison summaries | SDK exposes preview summaries, feedback/run stats, comparison URLs, and comparative experiment IDs. | Keep as SDK competence unless a repeated standard comparison workflow emerges. |
| SDK redaction/anonymizer profile setup | SDK owns ingestion-time privacy hooks. | Teach as SDK setup skill; no product tool yet. |

## Tool-Creation Rule

An explicit HE tool is justified only when all of these are true:

1. The capability is not comfortably available through first-party LangSmith
   CLI.
2. The LangSmith SDK provides the needed capability or precision.
3. The Harness Engineer needs the capability repeatedly in normal work.
4. Requiring HE to write SDK code each time would materially reduce reliability
   or speed.
5. The tool name maps directly to the LangSmith capability it exposes; do not
   invent a parallel Meta Harness evidence-platform vocabulary.

If a capability is CLI-native, teach it as HE LangSmith CLI competence. If it is
SDK-native but rare, keep it as HE script/code competence. If it is SDK-native,
frequent, and high-friction, then consider a tool.

Do not reclassify CLI-native workflows as tool candidates unless this ticket
identifies a concrete SDK-only extension that is frequent, high-friction, and
not comfortably handled by HE skill or direct SDK code.

This ticket does not implement tools, create schemas, or introduce a new
Evidence Workbench tool family.

## EBDR Boundary

Do not design a new Developer-safe Evidence Workbench packet tool in this
ticket. EBDR-1 is already a skill:

```txt
.agents/skills/langsmith-evaluator-feedback/SKILL.md
```

Use that skill for evaluator-to-optimizer feedback. TICKET-006 may identify
LangSmith trace/score identifiers that feed the skill, but it must not recreate
EBDR as a Workbench tool family.

## Recommendation

No new Workbench tools spec is needed now.

The right next step is operational skill hardening:

1. Teach HE the LangSmith CLI workflows documented by `langsmith-dataset`,
   `langsmith-trace`, and `langsmith-evaluator`.
2. Teach HE the SDK/OpenEvals extension workflows documented in
   `meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md`.
3. Track real HE friction around feedback APIs, selected-field trace extraction,
   structured run filters, deterministic trace-to-dataset compilation, and
   experiment comparison summaries.
4. Create future implementation tickets only for concrete workflows that satisfy
   the five-part tool-creation rule above.

## Deliverables

1. Corrected CLI-vs-SDK matrix using the ticket taxonomy: complete.
2. List of SDK capabilities that genuinely extend or exceed CLI capability:
   complete.
3. List of HE workflows that should be taught as CLI skills: complete.
4. List of SDK-only/high-friction workflows, if any, that are explicit tool
   candidates: complete; none approved now.
5. Recommendation on whether a new Workbench tools spec is needed: complete; no
   new Workbench tools spec is needed.

## Acceptance Criteria

- [x] TICKET-001’s corrected CLI audit outputs are used as the baseline.
- [x] LangSmith CLI is treated as required HE expertise, not optional or future.
- [x] Local CLI installation absence is recorded only as setup state.
- [x] Every candidate operation is classified by CLI support, SDK support, HE
      job relevance, and tool-candidate rationale.
- [x] Superseded access-category framing is absent from the reconciliation.
- [x] EBDR remains delegated to the existing skill.
- [x] No new Product Data Plane concepts, artifact families, or audit/event
      subsystems are introduced by this ticket.

## Follow-Up Tickets

No implementation ticket is created from TICKET-006.

Future tickets may be opened only after HE work produces concrete evidence that
one of the SDK-extension workflows is repeated, high-friction, and not
comfortably handled through LangSmith CLI, direct SDK code, or HE skill
guidance.
