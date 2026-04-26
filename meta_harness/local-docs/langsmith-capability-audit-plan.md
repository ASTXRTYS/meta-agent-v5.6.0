## 1. Purpose

Before finalizing the Evaluation Evidence Workbench tool family, Meta Harness must source-audit the LangSmith CLI and SDK.

The goal is to avoid prematurely wrapping capabilities that LangSmith already provides well, and to avoid teaching the Harness Engineer brittle CLI habits when stable SDK calls or official export patterns exist.

## 2. Questions To Answer

### 2.1 Datasets

```txt
How does the SDK create datasets?
How does the SDK create examples?
How are examples versioned?
What fields are allowed in inputs/outputs/metadata?
What is the recommended JSON/JSONL format?
How are dataset IDs and names resolved?
How should Meta Harness store dataset references?
```

### 2.2 Experiments / Sessions

```txt
How does the SDK create experiments/sessions?
How are experiments associated with datasets?
What metadata can be attached?
How are experiments listed/searched?
What identifiers should be stored locally?
Can experiment comparison URLs be generated or fetched?
```

### 2.3 Runs / Traces

```txt
Can the SDK list runs by project, experiment, dataset, metadata, feedback, score, or time?
Can it fetch complete run trees?
Can it fetch child runs/tool calls/messages?
Can it fetch only root runs?
What filtering syntax is supported?
What pagination/rate limits apply?
What fields are returned by default?
What requires explicit expansion?
```

### 2.4 Feedback / Scores

```txt
How does the SDK list feedback for runs?
How does it create feedback?
Can feedback be filtered by key/score/source?
How are evaluator outputs represented?
How should pass/fail, reward, score, and comments be normalized?
```

### 2.5 Export / Local Mirror

```txt
Does the CLI support experiment export?
Does the SDK support trace export?
Can run trees be dumped as JSON?
Can selected traces be exported by run IDs?
Can experiment summaries be downloaded?
What format should local mirrors use?
```

### 2.6 Security / Privacy

```txt
What sensitive fields can appear in traces?
Can hidden dataset rows or judge prompts appear in exported traces?
What redaction features exist?
What should Meta Harness redact before Developer-visible summaries?
```

## 3. Output Of Audit

The audit should produce:

```txt
1. LangSmith SDK capability matrix
2. LangSmith CLI capability matrix
3. Recommended HE tool wrappers
4. Recommended direct-CLI skill guidance
5. Required stored identifiers
6. Export/mirroring strategy
7. Redaction strategy
8. Open questions requiring LangSmith docs/source verification
```

## 4. Provisional Decision Boundary

Do not finalize the Evidence Workbench tool family until this audit is complete.

Allowed now:

```txt
Name the capability: Evaluation Evidence Workbench
Define its purpose
Define tiered ingestion philosophy
Define subagent analysis pattern
Define relation to evaluation_analytics_views
```

Deferred:

```txt
Exact LangSmith SDK calls
Exact CLI commands
Exact wrapper tool schemas
Exact trace export format
Exact metadata filter syntax
```
