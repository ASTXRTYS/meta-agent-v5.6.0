# TICKET-001 — Source-Audit LangSmith CLI/SDK Capabilities For Evaluation Evidence Workbench

## Status

Proposed

## Priority

P0 — blocking research/spec ticket

## Owner

Researcher + Harness Engineer

## Depends On

- `docs/specs/evaluation-evidence-workbench.md`
- `docs/specs/langsmith-capability-audit-plan.md`
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

## Deliverables

Create:

```txt
docs/research/langsmith-cli-sdk-capability-audit.md
docs/research/langsmith-capability-matrix.csv or .md
docs/research/langsmith-ids-and-metadata-contract.md
```

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

## Decision Output

The audit must conclude with one recommended architecture:

```txt
A. Direct CLI skill guidance
B. Backend SDK wrapper tools
C. Hybrid: SDK wrapper tools for stable operations + CLI guidance for ad hoc/inspection operations
```

Expected likely outcome: **C**, but this must be source-verified.

## Acceptance Criteria

- [ ] Current LangSmith SDK capabilities are verified from official docs/source.
- [ ] Current LangSmith CLI capabilities are verified from official docs/source.
- [ ] Dataset/example lifecycle is documented.
- [ ] Experiment/session lifecycle is documented.
- [ ] Run/trace querying capabilities are documented.
- [ ] Feedback/score capabilities are documented.
- [ ] Export/local mirror capabilities are documented.
- [ ] Required Meta Harness stored identifiers are listed.
- [ ] Privacy/redaction risks are listed.
- [ ] Recommended Evidence Workbench access pattern is stated.
- [ ] No wrapper tools are finalized without evidence.
