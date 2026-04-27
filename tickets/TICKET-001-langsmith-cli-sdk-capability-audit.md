# TICKET-001 — Source-Audit LangSmith CLI/SDK Capabilities For Evaluation Evidence Workbench

## Status
COMPLETED

## Owner

Researcher + Harness Engineer

## Human Decision Bias

Jason’s current bias is that the correct outcome is likely a hybrid architecture:

- Use LangSmith SDK / OpenEvals directly where stable programmatic operations are needed.
- Use CLI/skill/procedural guidance only for ad hoc operator workflows if the CLI is actually capable and non-brittle.
- Add Meta Harness model-visible tools only when they add product policy: project provenance, artifact registration, visibility/redaction enforcement, analytics schema validation, or audit-event recording.

This bias is not a conclusion. The audit must verify or overturn it with source citations.

## Depends On

- `meta_harness/docs/specs/evaluation-evidence-workbench.md`
- `meta_harness/local-docs/langsmith-capability-audit-plan.md`
- Current LangSmith official docs / SDK source / CLI source

## Blocks

- Final Evaluation Evidence Workbench tool design
- LangSmith evidence mirror implementation
- HE trace-bundle analysis workflow
- Any production wrapper tools around LangSmith eval evidence
- Post-eval analytics publication requirements that depend on experiment/run/trace refs

## Problem

The Evaluation Evidence Workbench is now named and conceptually scoped, but exact tool wrappers must not be finalized until LangSmith CLI/SDK capabilities are source-audited.

The key unresolved question:

```txt
Should HE use LangSmith CLI directly, SDK wrapper tools, or a hybrid?
```

We need to know exactly what LangSmith already provides for:

```txt
datasets
examples
experiments/sessions
runs/traces
run trees
feedback/scores
metadata filters
export/local mirror
trace dumps
comparison URLs
```

Without this audit, implementation risks either:

1. wrapping capabilities LangSmith already exposes cleanly,
2. teaching the agent brittle CLI usage,
3. inventing a parallel eval evidence model,
4. designing local mirrors that do not match LangSmith object identities.

## Goal

Produce a source-verified LangSmith capability matrix that determines the correct Evidence Workbench architecture.

## Non-Goals

- Do not implement Evidence Workbench tools in this ticket.
- Do not implement analytics publishing tools in this ticket.
- Do not define final LangSmith wrapper schemas yet.
- Do not rely on memory or plausible SDK behavior; verify against current source/docs.

## Required Research Questions

### 1. Datasets / Examples

Answer:

```txt
How does the SDK create datasets?
How does the SDK create examples?
How are examples versioned or updated?
What fields are supported in inputs/outputs/metadata?
What is the recommended JSON/JSONL representation?
Can examples be created deterministically with IDs?
How are dataset IDs/names resolved?
What identifiers must Meta Harness persist?
```

### 2. Experiments / Sessions

Answer:

```txt
How are experiments/sessions created?
How are experiments associated with datasets?
What metadata can be attached?
Can experiments be listed/searched by metadata?
What are the stable identifiers?
Can comparison URLs be generated deterministically?
Can comparison results be fetched programmatically or only linked?
```

### 3. Runs / Traces

Answer:

```txt
Can runs be listed by project?
Can runs be listed by experiment/session?
Can runs be filtered by metadata?
Can runs be filtered by feedback/score?
Can only root runs be fetched?
Can child runs/tool calls/messages be fetched selectively?
Can full run trees be fetched?
What fields return by default?
What requires explicit expansion?
What pagination/rate-limit patterns exist?
```

### 4. Feedback / Scores / Evaluator Outputs

Answer:

```txt
How does the SDK list feedback?
How does it create feedback?
Can feedback be filtered by key/score/source?
How are evaluator outputs represented?
How should binary/pass/fail/reward/score/comment fields be normalized?
```

### 5. CLI Capabilities

Answer:

```txt
What does LangSmith CLI expose today?
Can it create/list datasets?
Can it run or inspect experiments?
Can it export traces?
Can it export datasets/examples?
Can it dump run trees?
Can it filter runs?
Can it operate non-interactively for agents?
```

### 6. Export / Local Mirror

Answer:

```txt
Can experiment summaries be downloaded?
Can selected traces be exported by run IDs?
Can full experiments be exported?
Can run trees be dumped as JSON?
What is the most stable local mirror format?
What data should not be mirrored by default?
```

### 7. Security / Privacy

Answer:

```txt
What sensitive fields can appear in traces?
Can hidden dataset rows appear in exported traces?
Can judge prompts or rubric text appear in traces?
What redaction hooks/features exist?
What must Meta Harness redact before developer_safe outputs?
```

## Deliverable Responsibilities

1. `langsmith-cli-sdk-capability-audit.md`
   - Narrative audit.
   - Explains what was inspected, how, source locations, and major conclusions.

2. `langsmith-capability-matrix.md`
   - Tabular capability matrix.
   - One row per capability.
   - Must include SDK support, CLI support, citations, recommended Meta Harness access path, stored IDs, privacy risk, and gaps.

3. `langsmith-ids-and-metadata-contract.md`
   - Stable identifiers Meta Harness must persist.
   - Recommended metadata keys to attach to LangSmith runs/experiments/datasets.
   - Mapping from LangSmith IDs to Project Data Plane fields/artifacts.

Minimum matrix columns:

```txt
Capability
SDK support
CLI support
Official source citation
Recommended Meta Harness access path
Required stored identifiers
Privacy risk
Notes / gaps
```
## Access Path Decision Rules

For each capability, recommend one access path:

- `sdk_direct`: HE-owned script or backend code should use the LangSmith/OpenEvals SDK directly.
- `cli_skill`: agent/operator may use CLI guidance; do not depend on it for product correctness.
- `policy_tool`: Meta Harness should expose a model-visible/backend tool because it adds provenance, visibility, redaction, artifact registration, analytics validation, or audit policy.
- `not_supported_v1`: capability is unavailable, too brittle, too risky, or unnecessary for v1.

Raw SDK parity is not sufficient justification for `policy_tool`.


## Privacy Review Requirement

For each evidence-bearing capability, identify whether outputs may include:
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

State whether the capability is safe for:
- `he_private`,
- `internal`,
- `developer_safe`,
- `stakeholder_visible`.

Default raw traces and full exports to `he_private`.

## Acceptance Criteria

- [x] Current LangSmith SDK capabilities are verified from official docs/source.
- [x] Current LangSmith CLI capabilities are verified from official docs/source.
- [x] Dataset/example lifecycle is documented.
- [x] Experiment/session lifecycle is documented.
- [x] Run/trace querying capabilities are documented.
- [x] Feedback/score capabilities are documented.
- [x] Export/local mirror capabilities are documented.
- [x] Required Meta Harness stored identifiers are listed.
- [x] Privacy/redaction risks are listed.
- [x] Recommended Evidence Workbench access pattern is stated.
- [x] No wrapper tools are finalized without evidence.
- [x] No product spec is created or updated except to record source-verified conclusions in a follow-up ticket.


## Hard Boundary

This ticket is research/audit only.

Do not:
- Implement Evidence Workbench tools.
- Create final tool schemas.
- Modify product specs except to note source-verified conclusions if explicitly requested.
- Create a new Product Data Plane record family.
- Introduce raw LangSmith wrapper tools as accepted design.
- Treat candidate tool names in TICKET-006 as approved.

## Source Quality Standard

Every capability claim must include:
- package/repo inspected,
- file path,
- line range,
- function/class/command name,
- what the capability does,
- how it works or is invoked,
- important limitations or missing support.

Do not cite only prose docs when local SDK/source is available.
If docs and source disagree, record the discrepancy and prefer source for behavior.