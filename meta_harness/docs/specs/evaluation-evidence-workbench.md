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
> **Consumers:** Harness Engineer, evaluation-design workflow, LangSmith CLI/SDK skill material, OpenEvals evaluator workflow.

## 1. Purpose

The Evaluation Evidence Workbench is the Harness Engineer’s operating discipline
for using LangSmith CLI, LangSmith SDK, and OpenEvals to design, inspect, and
interpret harness evaluations.

It is not a new evidence platform, not a generic LangSmith wrapper, and not a
Product Data Plane expansion. Its job is to make the Harness Engineer excellent
at:

```txt
1. Knowing which LangSmith CLI commands handle routine evidence work.
2. Knowing when the SDK provides precision or composition beyond CLI.
3. Knowing when OpenEvals already owns evaluator construction.
4. Recording stable LangSmith identifiers needed for future inspection.
5. Producing optimizer feedback through the existing EBDR-1 skill.
6. Proposing explicit HE tools only for SDK-only, repeated, high-friction work.
```

LangSmith remains the forensic source of truth for datasets, examples,
experiments, runs, traces, and feedback. OpenEvals remains the reusable
evaluator-construction substrate. Meta Harness should not duplicate either
surface.

## 2. First-Principles Capability Map

The Workbench starts from the Harness Engineer’s job, not from tool names.

| HE responsibility | Native surface to check first | Escalation surface | Tool question |
|---|---|---|---|
| Create and inspect datasets/examples | LangSmith CLI dataset/example commands | SDK for deterministic IDs, splits, attachments, source-run linkage, version/tag workflows | Only if SDK-only dataset/example workflow is repeated and high-friction |
| Run or inspect experiments | CLI experiment/project commands where available | SDK/OpenEvals for `evaluate`, `aevaluate`, comparative experiments, metadata binding | Only if a standard repeated experiment runner needs ergonomic support |
| Locate runs and traces | CLI run/trace list/get/export commands | SDK for selected fields, structured filters, cursor pagination, custom tree hydration | Only if SDK-only filtering or trace-tree workflow is repeatedly needed |
| Inspect feedback and scores | CLI feedback support if available | SDK for feedback writes, configs, source metadata, comparative/group IDs | Only if feedback inspection/write workflow is SDK-only and frequent |
| Construct evaluators | OpenEvals docs/source | SDK/OpenEvals code | Only for repeated evaluator boilerplate after OpenEvals is checked |
| Emit optimizer feedback | `.agents/skills/langsmith-evaluator-feedback/SKILL.md` | LangSmith trace locators as inputs to the skill | Do not create a new Workbench EBDR tool |

The default answer is skill, CLI, or SDK code. An explicit HE tool is the
exception.

## 3. Boundary With LangSmith, OpenEvals, CLI Skills, And Meta Harness

Do not duplicate capabilities already owned by LangSmith or OpenEvals.

| Layer | Owns | Workbench stance |
|---|---|---|
| LangSmith CLI | Routine HE-facing operations for traces, runs, datasets, examples, experiments, and exports where first-party CLI supports them | Required HE expertise; local install absence is setup state only |
| LangSmith SDK | Programmatic evaluation, precise filters, field selection, pagination, feedback APIs, run-tree hydration, metadata binding | Use directly when CLI is insufficient or code is the natural medium |
| OpenEvals | Reusable evaluator constructors and `EvaluatorResult` shape | Check before custom evaluator logic |
| EBDR-1 skill | Evaluator-to-optimizer feedback format and leakage boundary | Use the skill; do not recreate as Workbench tooling |
| Meta Harness product surfaces | Existing product records, reports, links, and analytics when separately required | Only integrate when there is a concrete product requirement |

## 4. Source Of Truth

```txt
LangSmith = forensic evaluation substrate
OpenEvals = reusable evaluator construction substrate
LangSmith CLI = required HE operational surface
LangSmith SDK = programmatic extension surface
EBDR skill = evaluator-to-optimizer feedback boundary
```

The Workbench does not introduce a new Product Data Plane record family and does
not require a new Workbench tools spec unless TICKET-006 identifies concrete
SDK-only/high-friction HE workflows that survive CLI-vs-SDK reconciliation.

## 5. Core Abstractions

### 5.1 Evaluation program

The evaluation program is the HE-owned scientific contract for a target harness.

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

### 5.2 LangSmith locator

A LangSmith locator is the stable reference HE uses to return to evidence
without copying raw evidence into a new Meta Harness abstraction.

Examples:

```txt
langsmith_project_name
langsmith_dataset_id
langsmith_experiment_id
langsmith_run_id
langsmith_trace_url
feedback_key
feedback_id
reference_example_id
```

Locators are the default payload for routing and follow-up inspection. Raw
evidence is fetched through CLI or SDK only when the task requires it.

### 5.3 HE local working files

HE may create local working files during analysis. These are scratch or
role-workspace artifacts, not a new product storage model.

Useful formats:

```txt
JSONL for run/example/feedback lists
JSON for trace trees or experiment summaries
Markdown for human-authored analysis notes
```

When local files are created, include enough context to reproduce the source:
CLI command or SDK call, selected fields, filters, package version, and object
IDs.

### 5.4 HE finding

An HE finding is a claim the Harness Engineer derives from evaluation evidence.
It should cite LangSmith locators or local working files.

```txt
summary
langsmith_locators
affected_slice
confidence
open_questions
```

Findings may feed EBDR-1 feedback through the existing skill. This spec does not
define a separate Workbench feedback tool.

## 6. CLI-vs-SDK Escalation Rule

For every evidence task, HE should choose the lowest-friction native surface:

```txt
1. Use LangSmith CLI when first-party CLI covers the workflow.
2. Use LangSmith SDK when CLI lacks precision, output shape, or composition.
3. Use OpenEvals when the task is evaluator construction.
4. Use an existing skill when the task is feedback shaping or workflow guidance.
5. Consider an explicit HE tool only for repeated SDK-only/high-friction work.
```

This is the central Workbench rule. It prevents Meta Harness from wrapping
LangSmith merely because an SDK method exists.

## 7. Evaluation Design And OpenEvals Policy

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

## 8. HE-Internal Analysis Delegation

Dense trace analysis may be delegated to HE-internal analysis workers when the
evidence exceeds the main HE context budget.

Pattern:

```txt
HE main agent
  -> selects LangSmith locators or local working files
  -> delegates a narrow analysis task
  -> receives a structured finding summary
  -> verifies against the cited locators
  -> synthesizes HE judgment or EBDR-1 feedback
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
Subagents do not emit Developer-facing feedback.
Subagents do not receive hidden evaluation artifacts unless the task requires it and visibility remains HE-private.
Subagents return LangSmith locators or file refs with every claim.
HE remains the synthesizer.
```

These subagents are internal analysis workers, not core project-role agents. They
do not participate in the PCG handoff protocol and do not get peer-role
authority.

## 9. EBDR Boundary

Developer-facing optimizer feedback is owned by the existing EBDR-1 skill:

```txt
.agents/skills/langsmith-evaluator-feedback/SKILL.md
```

This Workbench spec may identify the LangSmith locators and evaluation outputs
that feed that skill. It must not recreate EBDR as a Workbench tool family.

EBDR-1 preserves these signal families:

```txt
delta: what improved or regressed
boundary: constraints that must continue to hold
localization: where to inspect
routing: trace/artifact references the Developer is allowed to see
uncertainty: confidence and alternative hypotheses
```

EBDR-1 must avoid:

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

## 10. Relationship To Evaluation Analytics

Evaluation analytics are adjacent, not the default output of this spec.

If HE needs UI-renderable analytics, use the separate analytics specs:

```txt
meta_harness/docs/specs/harness-engineer-evaluation-analytics.md
meta_harness/docs/specs/evaluation-analytics-chart-schemas.md
```

TICKET-006 must not import analytics publication as a reason to invent
LangSmith evidence tools. Analytics publication should be evaluated on its own
product need.

## 11. Minimal Tooling Stance

Default stance:

```txt
Use LangSmith CLI when native.
Use LangSmith SDK when CLI is insufficient.
Use OpenEvals before custom evaluator logic.
Use existing skills for feedback and workflow standards.
Add explicit HE tools only for SDK-only/high-friction repeated work.
```

An explicit HE tool is justified only when all are true:

```txt
The capability is not comfortably available through first-party LangSmith CLI.
The LangSmith SDK provides the needed capability or precision.
HE needs the capability repeatedly in normal work.
Writing SDK code each time would materially reduce reliability or speed.
The tool maps to the LangSmith capability; it does not invent parallel vocabulary.
```

Raw wrappers such as “list runs,” “get trace,” or “create dataset” should not be
introduced merely to rename LangSmith-native operations.

## 12. Open Implementation Questions

These are implementation questions, not reasons to build a policy platform:

```txt
Which first-party LangSmith CLI commands cover each HE workflow?
Which SDK capabilities exceed CLI capability or ergonomics?
Which of those SDK-only workflows are frequent enough to justify explicit tools?
Which HE workflows belong in skills instead of tools?
Which LangSmith IDs must be carried into EBDR feedback or reports?
```

The abstraction is stable only if it remains grounded in this question:

```txt
Make the Harness Engineer excellent at LangSmith CLI + SDK usage, then add only
minimal Meta Harness support where the product actually needs integration.
```
