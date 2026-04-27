---
doc_type: spec
derived_from:
  - AD §6 Observability & Evaluation
  - AD §4 Project-Scoped Execution Environment
status: draft
last_synced: 2026-04-26
owners: ["@Jason"]
---

# Evaluation Evidence Workbench Specification

> **Provenance:** Derived from `AD.md §6 Observability & Evaluation` and `§4 Project-Scoped Execution Environment`.
> **Status:** Draft · **Last synced with AD:** 2026-04-26.
> **Consumers:** Harness Engineer, Project Data Plane implementation, Evidence Workbench tooling, Developer-safe feedback pipeline, evaluation analytics pipeline.

## 1. Purpose

The Evaluation Evidence Workbench is the Harness Engineer’s private-to-internal operating surface for turning requirements, target-harness designs, LangSmith experiments, OpenEvals evaluator outputs, traces, and feedback scores into scientific evaluation decisions.

It is not a generic LangSmith wrapper and not a dashboard feature. Its job is to let the Harness Engineer:

```txt
1. Design the evaluation program.
2. Validate evaluator and dataset readiness.
3. Run or receive candidate experiment results.
4. Inspect evidence at the smallest useful depth.
5. Delegate bounded trace analysis without overloading the main HE context.
6. Synthesize evidence into analytics source data and EBDR-1 feedback.
7. Preserve information isolation between HE-private eval artifacts and Developer-safe signals.
```

LangSmith remains the forensic source of truth for traces, run trees, datasets, experiments, and feedback when evaluation runs through LangSmith. The Workbench is the Meta Harness layer that binds those raw capabilities to project phase, artifact visibility, redaction, and Harness Engineer judgment.

## 2. First-Principles Capability Map

The Harness Engineer participates at four project stages plus final acceptance. The Workbench must support each stage without assuming that “evidence” only means post-hoc trace dumps.

| HE stage | HE responsibility | Workbench capability required | Primary outputs |
|---|---|---|---|
| Stage 1 — PRD finalization | Convert PM-scoped success criteria into an evaluation program | Dataset design, public/held-out split planning, rubric and judge design, calibration evidence capture | `eval_suite`, `dataset`, `rubric`, readiness analytics |
| Stage 2 — Spec evaluation coverage | Cover Architect-introduced prompts, tools, middleware, agent behaviors, and programmatic checks | Coverage matrix, evaluator selection, run-function shape inspection, trajectory capture plan | eval coverage package, coverage analytics |
| Stage 3 — Gate placement | Decide when development phases are evaluated and what evidence is needed at each gate | Phase-to-eval mapping, thresholds, regression gates, cost/latency tracking plan | eval gate plan inside Planner package |
| Development loop | Evaluate candidate target harnesses and guide hill-climbing without leaking private eval internals | Experiment execution/lookup, candidate comparison, run filtering, trace inspection, failure clustering, EBDR-1 synthesis | `experiment_summary`, `filtered_run_index`, `failure_cluster_report`, EBDR-1 feedback |
| Acceptance | Decide whether the target harness is scientifically acceptable | Final scorecard, regression check, held-out/generalization review, redaction-safe summary | harness acceptance stamp, stakeholder-visible evidence package |

The Workbench is effective only if it supports both pre-development evaluation design and post-evaluation empirical diagnosis.

## 3. Boundary With LangSmith, OpenEvals, CLI Skills, And Meta Harness

Do not duplicate capabilities already owned by LangSmith or OpenEvals.

| Layer | Owns | Workbench stance |
|---|---|---|
| LangSmith SDK | Datasets, examples, experiments, run trees, feedback, project/session reads, experiment evaluation | Use directly or through thin helpers; do not invent parallel storage |
| OpenEvals | Reusable evaluator constructors and `EvaluatorResult` shape | Prefer for judge, JSON match, exact match, code, and similarity evaluators before custom evaluator code |
| LangSmith CLI/skills | Agent-facing ergonomic commands when installed | Treat as an optional operator surface; product contracts must not depend on a local CLI existing |
| Meta Harness Project Data Plane | Product records, artifact manifest, analytics views, access policy, visibility | Register durable artifacts and published analytics here |
| HE role filesystem | Private working mirror, scratch analysis, evaluator code drafts, bounded evidence bundles | Useful workspace, not authoritative product storage |

Local SDK anchors:

```txt
LangSmith Client.read_run(load_child_runs=True) supports complete run-tree loading.
Source: .venv/lib/python3.11/site-packages/langsmith/client.py:3583-3620

LangSmith Client.list_runs supports project, run_type, trace_id, filter, trace_filter, tree_filter,
is_root, parent_run_id, error, run_ids, select, and limit.
Source: .venv/lib/python3.11/site-packages/langsmith/client.py:3678-3698

LangSmith evaluate() accepts target, data, evaluators, summary_evaluators, metadata,
experiment_prefix, max_concurrency, num_repetitions, and existing/comparative experiments.
Source: .venv/lib/python3.11/site-packages/langsmith/evaluation/_runner.py:137-156

OpenEvals EvaluatorResult is keyed score/comment/metadata/source_run_id output.
Source: .venv/lib/python3.11/site-packages/openevals/types.py:16-22
```

These anchors document the first-pass source checks that shaped this abstraction. They do not close `TICKET-001`; final Evidence Workbench tool design still depends on the dedicated LangSmith SDK / CLI / OpenEvals capability audit with line-number citations.

This spec may define Meta Harness orchestration and privacy policy around those primitives. It must not re-specify LangSmith or OpenEvals APIs as if Meta Harness owned them.

## 4. Source Of Truth

```txt
LangSmith = forensic evaluation substrate
OpenEvals = reusable evaluator construction substrate
HE filesystem = private working analysis workspace
Project Data Plane = product-facing metadata, artifacts, access policy, analytics records
```

The Workbench does not introduce a new Product Data Plane record family. Durable Workbench outputs are stored through existing `artifact_manifest` kinds and, when UI-renderable, published through `evaluation_analytics_views`.

Workbench-supported artifact kinds already exist in `project-data-contracts.md`:

```txt
eval_suite
dataset
rubric
analytics_source_data
experiment_summary
run_index
filtered_run_index
trace_bundle
trace_summary_bundle
failure_cluster_report
candidate_comparison_report
```

## 5. Core Abstractions

### 5.1 Evaluation program

The evaluation program is the HE-owned scientific contract for a target harness. It is represented by the `eval_suite`, `dataset`, and `rubric` artifact family, not by a new product table.

It includes:

```txt
success dimensions
dataset plan and public/held-out split policy
evaluator inventory
judge model and scoring strategy
trajectory or behavioral checks
calibration evidence
phase-gate thresholds
known risks and expected failure modes
```

### 5.2 Evidence reference

An evidence reference is a lightweight pointer to LangSmith or Project Data Plane evidence.

Examples:

```txt
langsmith_project_name
langsmith_dataset_id
langsmith_experiment_id
langsmith_run_id
langsmith_trace_url
artifact_id
handoff_id
plan_phase_id
```

Evidence references are the default context payload. Raw evidence is fetched only when a task requires it.

### 5.3 Evidence bundle

An evidence bundle is a bounded local mirror of selected evidence for HE analysis. It may contain summaries, run indexes, selected run trees, or raw traces depending on ingestion tier.

Every bundle must declare:

```txt
purpose
source references
selection criteria
visibility
included fields
excluded/redacted fields
size or row count
creation timestamp
```

### 5.4 Finding

A finding is an HE-private or internal evidence-bounded claim derived from one or more references or bundles.

Minimum fields:

```txt
finding_kind
summary
evidence_refs
affected_slice
confidence
visibility
developer_safe_allowed: bool
```

Findings become Developer-visible only after redaction and EBDR-1 formatting.

### 5.5 Analytics source data

Analytics source data is chart/table-ready JSON derived from evaluation program artifacts or empirical evidence. It is registered as `kind="analytics_source_data"` and may be published through `evaluation_analytics_views`.

The Workbench prepares the source data. `harness-engineer-evaluation-analytics.md` owns the publication contract.

## 6. Evidence Ingestion Tiers

The Workbench uses progressive evidence disclosure. It should load the shallowest tier that can answer the HE’s current question.

| Tier | Name | Contents | Default visibility | Use when |
|---|---|---|---|---|
| 0 | References | IDs, URLs, artifact refs, metadata only | `internal` or `he_private` | Routing, provenance, linking |
| 1 | Evaluation program summary | Success dimensions, dataset/rubric/judge summaries, calibration status | `internal`; private fields omitted | PRD/spec/planning stages |
| 2 | Experiment summary | Aggregate scores, feedback stats, cost/latency, candidate metadata | `internal` | Candidate scorecards and trendlines |
| 3 | Filtered run index | Selected run rows with IDs, inputs/outputs policy, scores, errors, latency, tags | `he_private` by default | Slice selection and inspection planning |
| 4 | Trace summary bundle | Summaries of selected traces, tool-call trajectory sketches, failure snippets | `internal` or `he_private` | Failure clustering and EBDR synthesis |
| 5 | Selected raw trace bundle | Full selected run trees for bounded forensic inspection | `he_private` | Root-cause diagnosis requiring raw context |
| 6 | Full experiment dump | Exhaustive export/mirror | `he_private` | Explicit forensic/debug operation only |

Escalation rules:

```txt
Start at references or summaries.
Escalate to indexes before raw traces.
Escalate to selected raw traces before full dumps.
Never auto-load a full dump into the main HE model context.
Never expose raw private trace bundles to Developer.
```

## 7. Evidence Selection Filters

The Workbench should prefer LangSmith-native filters and selected fields before local post-processing. Exact syntax belongs to implementation code and the installed SDK/CLI version.

Required selection dimensions:

```txt
project or experiment
candidate identifier
dataset or split
plan_phase_id
metric or feedback key
score threshold
regression direction
error status
latency or token threshold
run_ids or trace_ids
root run vs child/tool run
limit
selected fields
```

If a filter cannot be expressed directly in LangSmith, the Workbench may fetch a bounded superset and produce a `filtered_run_index` artifact that records both the LangSmith query and the local post-filter.

## 8. Evaluation Design And OpenEvals Policy

Before writing custom evaluator logic, the Harness Engineer must check whether OpenEvals already provides the evaluator primitive.

OpenEvals primitives relevant to Meta Harness include:

```txt
exact match
LLM-as-judge
structured JSON match
list matching modes: superset, subset, same_elements, ordered
code evaluators such as pyright/mypy-backed checks
prompt templates such as plan_adherence
```

Local anchors:

```txt
OpenEvals JSON match supports list_match_mode values including superset, subset,
same_elements, and ordered.
Source: .venv/lib/python3.11/site-packages/openevals/json/match.py:68-70

OpenEvals pyright evaluator exposes create_pyright_evaluator(...).
Source: .venv/lib/python3.11/site-packages/openevals/code/pyright.py:99-106

OpenEvals plan_adherence prompt evaluates whether execution actions align with a declared plan.
Source: .venv/lib/python3.11/site-packages/openevals/prompts/plan_adherence.py:1-30
```

Custom evaluator code is justified only when:

```txt
OpenEvals does not provide the behavior.
The evaluator depends on domain-specific success criteria.
The evaluator needs Meta Harness-specific trajectory semantics.
The evaluator must enforce a deterministic business rule.
```

Evaluator development must follow inspect-before-implement discipline:

```txt
1. Run or inspect a representative target invocation.
2. Inspect actual outputs and LangSmith trace shape.
3. Align run-function output to dataset schema when possible.
4. Only then write evaluator extraction/comparison logic.
```

## 9. Subagent Analysis Pattern

Dense trace-bundle analysis should be delegated to bounded HE-internal analysis workers when the evidence exceeds the main HE context budget.

Pattern:

```txt
HE main agent
  -> selects evidence references and ingestion tier
  -> prepares bounded evidence bundle
  -> delegates a narrow analysis task
  -> receives a structured finding summary
  -> verifies against evidence references
  -> synthesizes analytics source data or EBDR-1 feedback
```

Allowed subagent tasks:

```txt
Cluster failures across these selected failed traces.
Compare candidate B against candidate A on grounding failures.
Inspect selected traces for tool misuse patterns.
Summarize recurring handoff or trajectory issues.
Find regressions introduced after iteration N.
```

Constraints:

```txt
Subagents do not publish analytics views.
Subagents do not emit Developer-facing feedback.
Subagents do not receive hidden evaluation artifacts unless the task requires it and visibility remains HE-private.
Subagents return evidence references with every claim.
HE remains the synthesizer and publisher.
```

These subagents are internal analysis workers, not core project-role agents. They do not participate in the PCG handoff protocol and do not get peer-role authority.

## 10. Developer-Safe Feedback Boundary

Developer-visible feedback must preserve optimization signal without leaking private evaluation contracts.

Allowed signal families:

```txt
delta: what improved or regressed
boundary: constraints that must continue to hold
localization: where to inspect
routing: trace/artifact references the Developer is allowed to see
uncertainty: confidence and alternative hypotheses
```

Forbidden in Developer-visible feedback:

```txt
held-out examples
hidden rubrics
judge prompts
private dataset rows
private evaluator instructions
hidden task IDs or gold answers
raw private trace content
HE-private reasoning not necessary for optimization
direct disclosure of scoring logic
```

A Workbench-produced `failure_cluster_report` or `candidate_comparison_report` may be marked `developer_safe` only after redaction. The report must state that redaction occurred and list the categories of information removed without revealing the removed content.

## 11. Relationship To Evaluation Analytics

The Workbench prepares evidence-derived artifacts. The analytics spec publishes UI-renderable views.

```txt
LangSmith / OpenEvals / project artifacts
  -> evidence references
  -> bounded evidence bundle
  -> HE finding or comparison report
  -> analytics source JSON
  -> evaluation_analytics_view
  -> UI renderer
```

The Workbench may produce:

```txt
success criteria profile data
eval coverage matrix data
dataset composition data
judge profile matrix data
candidate scorecard data
optimization timeline data
failure cluster summary data
cost/latency tradeoff data
regression report data
```

Publication through `publish_analytics_view` is governed by `harness-engineer-evaluation-analytics.md` and `project-data-contracts.md`.

## 12. Minimal Tooling Stance

The first implementation should avoid a large bespoke wrapper-tool surface.

Default stance:

```txt
Use LangSmith SDK/OpenEvals directly from HE-owned scripts where code is needed.
Use local LangSmith CLI/skills opportunistically when installed and useful.
Use existing Project Data Plane operations to register artifacts and publish analytics.
Add new model-visible tools only when they enforce Meta Harness-specific provenance,
visibility, redaction, or data-plane policy that LangSmith/OpenEvals do not own.
```

Net-new Workbench tools are justified only if they do at least one of:

```txt
Bind LangSmith evidence to project_id, handoff_id, plan_phase_id, and artifact_id.
Validate visibility and Developer-safe policy before exposure.
Register durable artifact_manifest rows.
Produce analytics source data that conforms to chart schemas.
Create bounded evidence bundles with explicit inclusion/exclusion policy.
Record an auditable evidence access event.
```

Raw wrappers such as “list runs,” “get trace,” or “create dataset” should not be introduced as Meta Harness product tools unless they add one of the policy/value layers above.

## 13. Full Trace Dumps

Full trace dumps are allowed only as explicit HE-private operations.

Policy:

```txt
Allowed: explicit HE-private full export for forensic/debug use
Default: no full export
Not allowed: auto-load full dump into model context
Not allowed: stakeholder visibility by default
Not allowed: Developer visibility
```

A full dump must record:

```txt
why it was needed
who/what requested it
source experiment/project
included runs or traces
visibility
storage location
retention expectation
```

## 14. Conformance Tests

Workbench implementation must satisfy these checks:

1. Evidence artifacts are registered through `artifact_manifest`; the Workbench does not create a new Product Data Plane record family.
2. `evaluation_analytics_views` records never contain raw private evidence; they point to validated analytics source data artifacts.
3. Developer-visible reports reject hidden rubrics, judge prompts, held-out examples, private dataset rows, and raw private traces.
4. Full experiment dumps require explicit HE-private intent and are never default ingestion behavior.
5. Filtered evidence export records source query, local post-filter if any, selection criteria, and visibility.
6. Every empirical finding cites at least one evidence reference.
7. Candidate comparison reports preserve candidate/run/experiment provenance.
8. OpenEvals primitives are checked before custom evaluator logic is introduced.
9. Run-function/evaluator extraction logic is written only after inspecting actual target outputs or trace shape.
10. New model-visible tools are rejected if they merely duplicate LangSmith SDK/CLI operations without adding Meta Harness provenance, visibility, redaction, or artifact policy.

## 15. Open Implementation Questions

These are implementation questions, not reasons to defer the Workbench abstraction:

```txt
Which local environments will have the LangSmith CLI installed versus SDK-only access?
Which HE workflows become scripts, skills, or model-visible tools after implementation proves the shape?
What exact artifact directory layout should HE use for evidence bundles inside its role filesystem?
What retention policy should apply to HE-private raw trace bundles in hosted deployments?
Which evaluator profiles should be prebuilt from OpenEvals for v1?
```

The abstraction is stable even if these implementation choices change: the HE needs evidence references, bounded bundles, evaluator construction, experiment comparison, analysis findings, analytics source data, and Developer-safe feedback.
