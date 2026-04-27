# TICKET-001 — Audit LangSmith CLI Capabilities For Harness Engineer

## Status

COMPLETED

## Owner

Researcher + Harness Engineer

## Human Decision Bias

Jason’s intended architecture is:

- The Harness Engineer must ship with strong LangSmith CLI expertise.
- LangSmith SDK / OpenEvals are the programmatic extension surfaces when CLI
  lacks capability, precision, output shape, or composition.
- Explicit HE tools are exceptional ergonomic aids for SDK-only or high-friction
  recurring workflows.

This ticket must verify or revise that bias by auditing the actual LangSmith
CLI workflows available to HE.

## Depends On

- `meta_harness/docs/specs/evaluation-evidence-workbench.md`
- Local LangSmith skills:
  - `langsmith-dataset`
  - `langsmith-evaluator`
  - `langsmith-trace`
- Current LangSmith official docs / CLI source when skill coverage is ambiguous
- Existing SDK/OpenEvals source facts in:
  - `meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md`
  - `meta_harness/local-docs/langsmith-capability-matrix.md`

## Blocks

- TICKET-006 CLI-vs-SDK capability reconciliation
- Any Evidence Workbench explicit-tool proposal
- Any HE LangSmith operations skill or runbook
- Any production wrapper around LangSmith eval evidence

## Problem

The previous audit incorrectly treated absence of a local `.venv/bin/langsmith`
binary as evidence about LangSmith CLI capability. That is not the right source
of truth.

The correct audit source is the local LangSmith skill set plus official CLI
docs/source when needed. The three local skills already describe the practical
CLI surface HE is expected to know:

```txt
langsmith-dataset   -> dataset, example, and experiment dataset workflows
langsmith-evaluator -> evaluator upload/list/delete and evaluation execution guidance
langsmith-trace     -> trace/run/thread/project querying and export workflows
```

This ticket exists to turn those skill-defined CLI workflows into a
source-grounded CLI capability matrix.

## Goal

Produce a verified LangSmith CLI capability audit that TICKET-006 can compare
against the already useful SDK/OpenEvals source findings.

The central question:

```txt
What does LangSmith CLI provide natively for HE, and what does the SDK provide
beyond that CLI surface?
```

## Non-Goals

- Do not inspect local Python package entry points as proof of CLI capability.
- Do not implement Evidence Workbench tools.
- Do not create final tool schemas.
- Do not create a new Product Data Plane record family.
- Do not introduce a Meta Harness evidence-platform vocabulary.
- Do not rerun the full SDK/OpenEvals audit unless a CLI comparison requires a
  specific SDK behavior check.

## Primary Audit Sources

### 1. `langsmith-dataset` skill

Audit its CLI coverage for:

```txt
langsmith dataset list
langsmith dataset get <name-or-id>
langsmith dataset create --name <name>
langsmith dataset delete <name-or-id>
langsmith dataset export <name-or-id> <output-file>
langsmith dataset upload <file> --name <name>

langsmith example list --dataset <name>
langsmith example create --dataset <name> --inputs <json>
langsmith example delete <example-id>

langsmith experiment list --dataset <name>
langsmith experiment get <name>
```

Also capture safety behavior:

```txt
--limit
--yes
confirmation prompts before destructive operations
```

### 2. `langsmith-trace` skill

Audit its CLI coverage for:

```txt
langsmith trace list
langsmith trace get
langsmith trace export

langsmith run list
langsmith run get
langsmith run export

langsmith thread list
langsmith thread get
langsmith project list
```

Also capture:

```txt
trace vs run semantics
hierarchy behavior
export format
--include-metadata
--include-io
--full
--show-hierarchy
--run-type
--trace-ids
--project
--limit
--last-n-minutes
--since
--error / --no-error
--name
--min-latency / --max-latency
--min-tokens
--tags
--filter
```

### 3. `langsmith-evaluator` skill

Audit its CLI coverage for:

```txt
langsmith evaluator list
langsmith evaluator upload <file> --name <name> --function <function> --dataset <dataset> --replace
langsmith evaluator upload <file> --name <name> --function <function> --project <project> --replace
langsmith evaluator delete <name>
```

Also capture constraints:

```txt
code evaluators only for CLI upload
LLM-as-judge upload is not currently supported by CLI
uploaded evaluators run in sandboxed environment
offline evaluators use --dataset
online evaluators use --project
one metric per evaluator
uploaded evaluator return-shape differences
NEVER use --yes unless explicitly requested
```

## Required Research Questions

### 1. Dataset and example CLI coverage

Answer:

```txt
What dataset operations are CLI-native?
What example operations are CLI-native?
Can CLI create/update/delete/list/export/upload the needed objects?
What JSON shapes does CLI expect?
What safety prompts exist?
Which dataset/example workflows still require SDK precision?
```

### 2. Trace and run CLI coverage

Answer:

```txt
What trace operations are CLI-native?
What run operations are CLI-native?
How does CLI preserve trace hierarchy?
What filters are exposed directly?
What export formats exist?
When should HE query traces vs runs?
Which filtering/export workflows still require SDK precision?
```

### 3. Experiment and project CLI coverage

Answer:

```txt
What experiment inspection commands are CLI-native?
Can CLI list experiments by dataset?
Can CLI get experiment results?
Can CLI list tracing projects?
What comparison/result details are available through CLI?
Which experiment summary/comparison workflows still require SDK precision?
```

### 4. Evaluator CLI coverage

Answer:

```txt
What evaluator operations are CLI-native?
What evaluator types can CLI upload?
What evaluator types require SDK/local code/UI?
What return-shape and sandbox constraints matter?
When should HE use local evaluate() instead of uploaded evaluators?
```

### 5. Feedback CLI coverage

Answer:

```txt
Do the local skills describe direct feedback list/get/create CLI commands?
If not, does trace/run/experiment output expose feedback enough for HE workflows?
Which feedback workflows require SDK APIs?
```

### 6. Non-interactive HE suitability

Answer:

```txt
Which commands are safe/non-interactive by default?
Which commands prompt for confirmation?
When is --yes available?
Which commands require explicit user approval before destructive use?
Which commands need LANGSMITH_PROJECT or project flags to avoid ambiguity?
```

## Deliverables

1. Update `meta_harness/local-docs/langsmith-capability-matrix.md` with a
   CLI-vs-SDK comparison grounded in the three local LangSmith skills.
2. Update `meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md` with
   a concise narrative summary of CLI-native capabilities and SDK-extension
   gaps.
3. If needed, update `meta_harness/local-docs/langsmith-ids-and-metadata-contract.md`
   only for identifier implications discovered during CLI audit.
4. Provide TICKET-006 with a final list of capabilities classified as:

```txt
cli_native
sdk_native
sdk_extends_cli
he_skill
explicit_tool_candidate
```

## Required Matrix Columns

```txt
Capability
CLI command(s)
Skill source
CLI output / behavior notes
Relevant flags
Safety / non-interactive notes
Equivalent SDK method(s)
SDK extends CLI?
HE workflow relevance
Classification
Explicit tool candidate rationale
```

## Tool-Candidate Rule

An explicit HE tool is justified only when all of these are true:

1. First-party LangSmith CLI does not comfortably cover the workflow.
2. LangSmith SDK or OpenEvals provides the needed capability.
3. HE needs the capability repeatedly in normal work.
4. Writing SDK code each time would materially reduce reliability or speed.
5. The tool maps directly to the native LangSmith/OpenEvals capability instead
   of inventing a parallel Meta Harness abstraction.

## Privacy Review Requirement

For each evidence-bearing CLI workflow, identify whether outputs may include:

- hidden dataset examples,
- judge prompts,
- rubric text,
- evaluator reasoning,
- user inputs,
- model outputs,
- tool call arguments/results,
- serialized chain/config metadata,
- stack traces or errors,
- credentials/secrets.

Default raw traces, examples, full exports, evaluator comments, and judge
reasoning to `he_private`.

## Acceptance Criteria

- [x] `langsmith-dataset` skill command coverage is audited.
- [x] `langsmith-trace` skill command coverage is audited.
- [x] `langsmith-evaluator` skill command coverage is audited.
- [x] Official CLI docs/source are consulted only where local skill coverage is
      ambiguous or incomplete.
- [x] Local `.venv` CLI installation state is not used as capability evidence.
- [x] Dataset/example CLI-native workflows are classified.
- [x] Trace/run/thread/project CLI-native workflows are classified.
- [x] Experiment/project CLI-native workflows are classified.
- [x] Evaluator CLI-native workflows and limitations are classified.
- [x] Feedback CLI coverage or SDK gap is explicitly stated.
- [x] CLI safety/non-interactive behavior is documented.
- [x] SDK-only or SDK-extends-CLI gaps are listed.
- [x] No explicit HE tools are approved in this ticket.
- [x] TICKET-006 has enough evidence to decide whether any explicit tools are
      justified.

## Completion Notes

Completed on 2026-04-27 by updating:

- `meta_harness/local-docs/langsmith-capability-matrix.md`
- `meta_harness/local-docs/langsmith-cli-sdk-capability-audit.md`
- `meta_harness/local-docs/langsmith-ids-and-metadata-contract.md`

Final result: broad routine HE workflows are `cli_native`; SDK/OpenEvals remain
the programmatic extension surfaces for evaluation execution, precise filtering,
feedback APIs, local/LLM evaluators, comparison workflows, and privacy
configuration. No explicit HE tool is approved by this ticket.

## Hard Boundary

This ticket is audit/research only.

Do not:

- Implement tools.
- Create tool schemas.
- Treat local CLI absence as product capability evidence.
- Use `policy_tool` or `not_supported_v1` as framing categories.
- Design a Meta Harness evidence platform.
- Recreate EBDR; use `.agents/skills/langsmith-evaluator-feedback/SKILL.md`
  for evaluator-to-optimizer feedback.