# TICKET-006 — Design Evaluation Evidence Workbench Tools After LangSmith Audit

## Status

In Progress → Blocked pending formal spec

## Priority

P2 — follow-up design ticket after source audit

## Owner

Harness Engineer + Architect + Developer

## Depends On

- TICKET-001 LangSmith CLI/SDK capability audit
- `meta_harness/docs/specs/evaluation-evidence-workbench.md`

## Blocks

- Evidence Workbench implementation
- HE subagent trace-bundle analysis workflows
- Post-eval analytics generation from LangSmith evidence
- Developer-safe failure cluster packet generation

## Problem

The Evaluation Evidence Workbench is conceptually scoped, but exact tools must wait until LangSmith capabilities are source-audited.

After TICKET-001 completes, we need to translate verified LangSmith capabilities into the minimal deterministic harness HE needs.

## Goal

Design the actual Evidence Workbench tool family, deciding which operations are:

```txt
direct SDK wrapper tools
direct CLI guidance through skill/procedural knowledge
sandboxed Python/CLI operations
subagent task patterns
not supported in v1
```

## Inputs

From TICKET-001:

```txt
LangSmith SDK capability matrix
LangSmith CLI capability matrix
recommended access path
required stored identifiers
export/mirror strategy
redaction strategy
```

## Required Decisions (PROPOSED)

### 1. Tool vs Skill Split (PROPOSED)

**Decision:** Proposed; must be captured in `meta_harness/docs/specs/evidence-workbench-tools-spec.md` before implementation.

| Capability | Implementation | Decision Rationale |
|------------|---------------|-------------------|
| SDK queries | **Backend tools** | Direct API access, structured returns |
| Filesystem mirror | **Backend tools** | File I/O, streaming, local persistence |
| Local analysis | **Backend tools** | Structured computation, synthesis |
| Subagent spawning | **Skill guidance** | Deep Agents SDK provides `task` tool natively |
| Filter syntax | **Backend helper** | Convert dict → LangSmith filter string |
| Redaction | **Backend tool** + SDK config | Multi-level redaction support |
| HE workflow | **Skill guidance** | Procedural knowledge for HE agent |

**Source-verification required:** Confirm installed LangSmith package capabilities and any CLI surface before finalizing wrapper tools.

### 2. Evidence Query Tools (PROPOSED)

**Decision:** Proposed 6-tool family; formal schemas must be defined in `meta_harness/docs/specs/evidence-workbench-tools-spec.md` before implementation.

| Tool | SDK Method | Source |
|------|-----------|--------|
| `get_experiment_summary` | `get_experiment_results()` | `client.py:9750-9843` |
| `list_experiment_runs` | `list_runs(project_id=...)` | `client.py:3678-3870` |
| `read_run_trace` | `read_run(load_child_runs=True)` | `client.py:3583-3620` |
| `list_run_feedback` | `list_feedback(run_ids=...)` | `client.py:7518-7559` |
| `query_runs_by_filter` | `list_runs(filter=...)` | `client.py:3678-3870` |
| `get_dataset_info` | `read_dataset()` + `list_examples()` | `client.py:4925-4970`, `client.py:6384-6507` |

**Exact schemas:** Pending formal spec with parameters aligned to SDK signatures.

### 3. Local Mirror Tools (PROPOSED)

**Decision:** Proposed 5-tool family; formal schemas must be defined in `meta_harness/docs/specs/evidence-workbench-tools-spec.md` before implementation.

| Tool | Purpose |
|------|---------|
| `mirror_experiment_runs` | Mirror all runs to JSONL |
| `mirror_failed_runs` | Filtered mirror (`neq(error, null)`) |
| `mirror_trace_bundle` | Full trace trees for specified runs |
| `export_experiment_summary` | Export summary (JSON + optional CSV) |
| `load_mirrored_evidence` | Load previously mirrored evidence |

**Proposed file layout for future `meta_harness/docs/specs/evidence-workbench-tools-spec.md`:**

```
/langsmith_mirror/experiments/{experiment_id}/
  experiment_summary.json
  runs_index.jsonl
  feedback_index.jsonl
  filtered/failed_runs.jsonl
  traces/{run_id}.json
  summaries/{run_id}.summary.md
```

### 4. Subagent Analysis Pattern (PROPOSED)

**Decision:** Proposed skill guidance, NOT tools. Must be captured in `meta_harness/docs/specs/evidence-workbench-tools-spec.md`.

**Rationale:** Deep Agents SDK provides `task` tool for subagent spawning. No wrapper needed.

**Pattern:**
```
1. HE mirrors evidence locally
2. HE bounds bundle (select specific trace files)
3. HE spawns subagent via task tool with explicit constraints
4. Subagent writes intermediate artifacts (summaries/)
5. HE synthesizes and redacts before publication
```

**Subagent output types:**
- `trace_summary_bundle` → `summaries/{run_id}.summary.md`
- `failure_cluster_report` → `clusters/failure_cluster_report.md`
- `candidate_comparison_report` → `comparison_report.md`
- `regression_report` → `filtered/regressed_runs.jsonl`

**Critical:** Subagents must NOT publish final analytics directly.

### 5. Redaction Boundary (PROPOSED)

**Decision:** Proposed 3-level redaction system. Must be captured in `meta_harness/docs/specs/evidence-workbench-tools-spec.md`.

| Level | Redacted Fields | Use Case |
|-------|-----------------|----------|
| `internal` | None | HE-private analysis |
| `stakeholder_visible` | `inputs` (PII policy), full `events` | Product analytics |
| `developer_safe` | `inputs`, `outputs`, `serialized`, `extra`, stack traces | Developer feedback (EBDR-1) |

**Implementation:**
- SDK client config: `hide_inputs`, `hide_outputs`, `anonymizer` (`client.py:748-755`)
- Per-tool redaction: `produce_developer_safe_summary` tool (spec §6.4)
- Output format: EBDR-1 packet structure

**Developer-safe fields preserved:**
- Feedback scores (metrics)
- Latency/cost (efficiency)
- Run IDs, Example IDs (routing/localization)
- Tool call names (behavior analysis)

## File Layout For Mirrored Evidence (PROPOSED)

**Proposed layout** for future `meta_harness/docs/specs/evidence-workbench-tools-spec.md`:

```txt
/langsmith_mirror/
  experiments/
    {experiment_id}/
      experiment_summary.json          # Aggregated stats
      runs_index.jsonl                 # Streaming run list
      feedback_index.jsonl             # Streaming feedback list
      filtered/
        failed_runs.jsonl              # Error-filtered runs
        regressed_runs.jsonl           # Regression-flagged runs
      traces/
        {run_id}.json                  # Full trace trees
      summaries/
        {run_id}.summary.md            # Subagent-generated summaries
      clusters/
        failure_cluster_report.md      # HE-synthesized analysis
```

**Format notes:**
- JSONL for streaming collections (runs, feedback) — appendable, grep-friendly
- JSON for structured objects (summary, traces) — random access
- Markdown for narrative analysis (summaries, clusters) — human-readable

## Acceptance Criteria

- [ ] Exact Evidence Workbench tools are specified in `meta_harness/docs/specs/evidence-workbench-tools-spec.md`.
- [ ] Exact tool schemas are source-aligned with LangSmith and cited to local source.
- [ ] Tool-vs-skill split is documented in the formal spec.
- [ ] Local mirror file layout is documented in the formal spec.
- [ ] Full-dump policy is documented in the formal spec.
- [ ] Filtered-export policy is documented in the formal spec.
- [ ] Subagent analysis pattern is operationalized.
- [ ] Redaction policy is integrated.
- [ ] Developer-safe output boundary is preserved.
- [ ] Deferred capabilities are identified.

## Deliverables

1. **Updated Ticket** (this file) — Status: Blocked pending formal spec
2. **Formal Spec** — `meta_harness/docs/specs/evidence-workbench-tools-spec.md` — still required before implementation.

## Next Steps

1. AD §9 registration: Add spec to Decision Index → Derived Specs
2. Parent AD pointer: Add `> Implementation: see meta_harness/docs/specs/evidence-workbench-tools-spec.md` to relevant AD sections
3. Implementation: Backend tool development (separate ticket)
4. Skill documentation: HE agent skill for subagent analysis workflow
