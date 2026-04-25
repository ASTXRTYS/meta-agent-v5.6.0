# LangSmith Evaluation Evidence Workbench Architecture Recommendation

**Purpose**: Recommend architecture for Meta Harness to interact with LangSmith based on source-verified capability audit.

**Audited Version**: LangSmith SDK 0.7.25

**Recommendation**: **Option C - Hybrid: SDK wrapper tools for stable operations + CLI guidance for ad hoc/inspection operations**

---

## Executive Summary

Based on comprehensive source-verified audit of LangSmith SDK and CLI capabilities, the hybrid architecture (Option C) is recommended. This approach leverages the SDK's comprehensive programmatic capabilities for stable, complex operations while using the CLI for simple, ad hoc inspection and export tasks.

**Rationale**:
- SDK provides essential capabilities not available in CLI (dataset versioning, feedback management, complex filtering, security features)
- CLI provides agent-friendly JSON output and simple export workflows
- Hybrid approach aligns with Evaluation Evidence Workbench philosophy (tiered evidence ingestion, subagent pattern)
- Avoids redundant wrapper complexity while enabling both programmatic and human-in-the-loop workflows

---

## Architecture Options Considered

### Option A: Direct CLI Skill Guidance

**Description**: Provide LangSmith CLI commands directly to agents via skill guidance. No wrapper tools.

**Advantages**:
- Minimal implementation overhead
- Leverages existing CLI functionality
- Agent-friendly JSON output by default

**Disadvantages**:
- Missing critical capabilities (dataset versioning, feedback management, complex filtering)
- No programmatic access to security features (anonymizer, hide_inputs/outputs/metadata)
- Limited export control (no selective field inclusion in programmatic context)
- No bulk operations support
- Brittle dependency on CLI interface stability

**Verdict**: ❌ Not viable - missing essential capabilities for Evaluation Evidence Workbench

---

### Option B: Backend SDK Wrapper Tools

**Description**: Build comprehensive SDK wrapper tools for all LangSmith operations. No CLI usage.

**Advantages**:
- Full access to all SDK capabilities
- Consistent programmatic interface
- Can implement custom logic and validation
- Access to security features

**Disadvantages**:
- Significant implementation overhead
- Redundant with existing CLI for simple operations
- Must reimplement export logic already in CLI
- Increased maintenance burden
- Risk of diverging from LangSmith best practices

**Verdict**: ❌ Over-engineering - CLI already handles simple operations well

---

### Option C: Hybrid (Recommended)

**Description**: Use SDK wrapper tools for stable, complex operations + CLI guidance for ad hoc/inspection operations.

**Advantages**:
- Leverages SDK for capabilities not available in CLI
- Leverages CLI for simple, well-implemented operations
- Minimal implementation overhead
- Aligns with tiered evidence ingestion philosophy
- Supports both programmatic and human-in-the-loop workflows
- Maintains flexibility for future LangSmith enhancements

**Disadvantages**:
- Requires clear separation of concerns between SDK and CLI usage
- Agents must understand when to use which approach

**Verdict**: ✅ **Recommended** - optimal balance of capability and simplicity

---

## Recommended Architecture: Hybrid

### SDK Wrapper Tools (Stable Operations)

Build SDK wrapper tools for the following operations:

#### 1. Dataset Management
- **create_dataset()**: With schema support, transformations, metadata
- **read_dataset_version()**: For version management and diffing
- **list_dataset_versions()**: For version discovery
- **clone_public_dataset()**: For dataset sharing workflows

**Rationale**: CLI lacks dataset versioning and schema support. SDK provides comprehensive dataset lifecycle management.

#### 2. Feedback Management
- **create_feedback()**: With score normalization, source tracking
- **list_feedback()**: With filtering by key, source type
- **create_feedback_config()**: For metric schema definition
- **create_feedback_formula()**: For composite metrics

**Rationale**: CLI has no feedback management. Feedback is core to evaluation workflows.

#### 3. Complex Run/Trace Queries
- **list_runs()** with advanced filters: `trace_filter`, `tree_filter`, `select`
- **read_run()** with `load_child_runs=True`: For full run tree loading
- **read_thread()**: For multi-turn conversation queries

**Rationale**: CLI supports basic filtering but not advanced tree filters or selective field loading. SDK provides programmatic control.

#### 4. Security and Privacy
- **Client initialization** with `anonymizer`, `hide_inputs`, `hide_outputs`, `hide_metadata`
- Custom anonymizer functions for redaction

**Rationale**: CLI has no programmatic security controls. Privacy is critical for developer-safe outputs.

#### 5. Evaluation Execution
- **evaluate()**: For running evaluations and creating experiments

**Rationale**: CLI cannot create experiments. Evaluation is core to Harness Engineer role.

### CLI Guidance (Ad Hoc Operations)

Provide CLI command guidance for the following operations:

#### 1. Simple Listing
- `langsmith dataset list`: Quick dataset discovery
- `langsmith project list`: Project discovery
- `langsmith experiment list --dataset`: Experiment discovery
- `langsmith evaluator list`: Evaluator discovery

**Rationale**: CLI provides human-readable output and simple filtering. No need for SDK wrapper.

#### 2. Simple Export
- `langsmith dataset export`: Dataset export to JSON
- `langsmith trace export --include-metadata`: Trace export with selective field inclusion
- `langsmith run export --include-io`: Run export with inputs/outputs

**Rationale**: CLI export is well-implemented with field selection flags. No need to reimplement.

#### 3. Human Inspection
- `langsmith trace get <trace-id> --full`: Full trace inspection
- `langsmith run get <run-id> --full`: Run inspection
- `langsmith experiment get <experiment-name>`: Experiment result inspection

**Rationale**: CLI provides human-readable pretty-printed output. Useful for Harness Engineer review.

#### 4. Simple CRUD
- `langsmith dataset create`: Quick dataset creation
- `langsmith dataset delete`: Dataset deletion
- `langsmith example create`: Quick example creation
- `langsmith example delete`: Example deletion

**Rationale**: CLI provides simple CRUD for common operations. SDK wrappers not needed for basic cases.

---

## Tool Design Principles

### SDK Wrapper Tools

**Design guidelines**:
1. **Thin wrappers**: Minimize custom logic, delegate to SDK
2. **Identifier resolution**: Accept both names and IDs, resolve internally
3. **Pagination handling**: Use SDK iterators, return collected results
4. **Error handling**: Convert SDK exceptions to tool-specific errors
5. **Metadata defaults**: Apply Meta Harness metadata conventions automatically
6. **Security defaults**: Apply `hide_inputs`/`hide_outputs`/`hide_metadata` by default for developer safety

**Example wrapper signature**:
```python
def list_runs_filtered(
    project_name: str,
    trace_filter: Optional[str] = None,
    tree_filter: Optional[str] = None,
    select: Optional[list[str]] = None,
    limit: Optional[int] = None,
) -> list[Run]:
    """List runs with advanced filtering using SDK."""
    client = Client(hide_inputs=True, hide_outputs=True, hide_metadata=True)
    runs = list(client.list_runs(
        project_name=project_name,
        trace_filter=trace_filter,
        tree_filter=tree_filter,
        select=select,
        limit=limit,
    ))
    return runs
```

### CLI Guidance Tools

**Design guidelines**:
1. **Command templates**: Provide CLI command patterns with placeholders
2. **Output parsing**: Parse JSON output for programmatic use
3. **Flag guidance**: Recommend appropriate flags for safety (e.g., `--include-metadata` vs `--include-io`)
4. **Error handling**: Parse CLI error messages for actionable feedback

**Example guidance**:
```python
def export_trace_safe(trace_id: str, output_dir: str) -> str:
    """Export trace with metadata only (no inputs/outputs)."""
    cmd = [
        "langsmith",
        "trace",
        "export",
        output_dir,
        "--trace-ids", trace_id,
        "--include-metadata",  # Safe: no inputs/outputs
        "--limit", "1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Parse and validate output
    return output_dir
```

---

## Tiered Evidence Ingestion Alignment

The hybrid architecture aligns with the Evaluation Evidence Workbench philosophy:

### Tier 1: References Only
**SDK wrapper**: `list_datasets()`, `list_runs(project_name=..., select=["id", "trace_id"])`
**Purpose**: Fetch minimal identifiers for navigation

### Tier 2: Experiment Summary
**SDK wrapper**: `evaluate()` results, feedback aggregation
**CLI guidance**: `langsmith experiment get`
**Purpose**: Fetch summary statistics and scores

### Tier 3: Filtered Run Index
**SDK wrapper**: `list_runs()` with advanced filters
**Purpose**: Fetch run metadata without full traces

### Tier 4: Selected Trace Summaries
**SDK wrapper**: `read_run()` with selective field loading
**CLI guidance**: `langsmith trace get --include-metadata`
**Purpose**: Fetch trace structure without full inputs/outputs

### Tier 5: Selected Raw Traces
**SDK wrapper**: `read_run(load_child_runs=True)` with security controls
**CLI guidance**: `langsmith trace export --full` (with redaction)
**Purpose**: Fetch full trace data for subagent analysis

### Tier 6: Full Experiment Dump
**CLI guidance**: `langsmith trace export --full --limit` (with redaction)
**Purpose**: Bulk export for offline analysis (rare, explicit approval)

---

## Subagent Pattern Integration

The hybrid architecture supports the subagent pattern:

### Subagent Tools (SDK-based)
- **Trace Analyzer**: Receives full trace via SDK, produces summary
- **Feedback Aggregator**: Uses SDK feedback APIs to compute metrics
- **Dataset Curator**: Uses SDK dataset versioning for dataset management

### Harness Engineer Tools (SDK + CLI)
- **Evidence Fetcher**: SDK wrappers for tiered evidence ingestion
- **Export Manager**: CLI guidance for safe export workflows
- **Inspector**: CLI guidance for human-readable inspection

---

## Privacy and Security

### SDK Wrapper Security Defaults

**Client initialization**:
```python
client = Client(
    anonymizer=meta_harness_anonymizer,  # Custom redaction
    hide_inputs=True,  # Default: hide inputs
    hide_outputs=True,  # Default: hide outputs
    hide_metadata=True,  # Default: hide metadata
    omit_traced_runtime_info=True,  # Omit SDK version, etc.
)
```

**Override mechanism**: Provide `include_sensitive=True` parameter for cases where full data is needed (with explicit approval).

### CLI Guidance Security Defaults

**Export flags**:
- Default: `--include-metadata` only (no inputs/outputs)
- With approval: `--include-io` (inputs/outputs)
- Rare approval: `--full` (all fields)

**Guidance enforcement**: CLI guidance tools should validate flag combinations and warn on unsafe exports.

---

## Required Stored Identifiers

Based on the IDs and Metadata Contract, the hybrid architecture requires persisting:

**Primary identifiers** (required):
- `dataset.id`, `dataset.name`
- `example.id`, `example.dataset_id`
- `run.id`, `run.trace_id`, `run.session_id`
- `feedback.id`, `feedback.run_id`
- `experiment.id`, `experiment.dataset_id`

**Optional identifiers** (context-dependent):
- `run.parent_run_id` (for tree reconstruction)
- `run.reference_example_id` (for evaluation linkage)
- `thread_id` (for multi-turn conversations)

**Metadata** (for filtering and organization):
- Dataset metadata: project_id, purpose, domain
- Example metadata: difficulty, category, source
- Run metadata: revision_id, agent_role, environment
- Feedback metadata: evaluator_name, evaluation_type

---

## Implementation Roadmap

### Phase 1: SDK Wrapper Tools (Priority: High)

1. **Dataset Management Tools**
   - `create_dataset_with_schema()`
   - `read_dataset_version()`
   - `list_dataset_versions()`
   - `clone_public_dataset()`

2. **Feedback Management Tools**
   - `create_feedback_normalized()`
   - `list_feedback_filtered()`
   - `create_feedback_config()`
   - `create_feedback_formula()`

3. **Complex Query Tools**
   - `list_runs_advanced()`
   - `read_run_with_tree()`
   - `read_thread_runs()`

4. **Security Tools**
   - `create_secure_client()` (with anonymizer and hide defaults)
   - `redact_trace()` (custom anonymizer)

5. **Evaluation Tools**
   - `run_evaluation()`

### Phase 2: CLI Guidance Tools (Priority: Medium)

1. **Simple Listing Guidance**
   - `list_datasets_cli()`
   - `list_experiments_cli()`
   - `list_projects_cli()`

2. **Safe Export Guidance**
   - `export_dataset_safe()`
   - `export_trace_safe()`
   - `export_run_safe()`

3. **Inspection Guidance**
   - `inspect_trace_cli()`
   - `inspect_experiment_cli()`

### Phase 3: Integration (Priority: High)

1. **Tiered Evidence Ingestion Pipeline**
   - Implement 6-tier ingestion using SDK + CLI
   - Add identifier persistence to Project Data Plane

2. **Subagent Integration**
   - Provide SDK-based tools to subagents
   - Implement trace analysis workflow

3. **Privacy Enforcement**
   - Apply security defaults to all SDK wrappers
   - Validate CLI export flags

---

## Migration Path

### From CLI-Only to Hybrid

**Current state**: If existing tools use CLI only
**Migration steps**:
1. Identify CLI operations that require SDK capabilities
2. Build SDK wrappers for those operations
3. Update tool guidance to use SDK wrappers where appropriate
4. Keep CLI guidance for simple operations
5. Test with existing workflows

### From SDK-Only to Hybrid

**Current state**: If existing tools use SDK only
**Migration steps**:
1. Identify SDK operations that have CLI equivalents
2. Replace with CLI guidance for simple operations
3. Keep SDK wrappers for complex operations
4. Update documentation to clarify when to use which
5. Test with existing workflows

---

## Conclusion

The hybrid architecture (Option C) is recommended based on source-verified audit evidence. This approach:

- ✅ Provides access to all critical LangSmith capabilities
- ✅ Minimizes implementation overhead
- ✅ Aligns with Evaluation Evidence Workbench philosophy
- ✅ Supports both programmatic and human-in-the-loop workflows
- ✅ Enables tiered evidence ingestion
- ✅ Integrates with subagent pattern
- ✅ Enforces privacy and security defaults

**Next steps**:
1. Implement Phase 1 SDK wrapper tools (high priority)
2. Implement Phase 2 CLI guidance tools (medium priority)
3. Integrate with Project Data Plane for identifier persistence
4. Update Harness Engineer skill with tool guidance
5. Test with evaluation workflows

---

## Appendix: Decision Matrix

| Criterion | Option A (CLI) | Option B (SDK) | Option C (Hybrid) |
|-----------|----------------|----------------|-------------------|
| Capability coverage | ❌ Missing key features | ✅ Full coverage | ✅ Full coverage |
| Implementation overhead | ✅ Minimal | ❌ High | ⚠️ Medium |
| Maintenance burden | ✅ Low (external) | ❌ High (custom) | ⚠️ Medium |
| Programmatic control | ❌ Limited | ✅ Full | ✅ Full |
| Human-friendly output | ✅ Yes | ⚠️ Requires custom | ✅ Yes |
| Security features | ❌ None | ✅ Full | ✅ Full |
| Export flexibility | ⚠️ Limited | ✅ Full | ✅ Full |
| Alignment with tiered ingestion | ⚠️ Limited | ✅ Good | ✅ Excellent |
| Subagent support | ❌ Limited | ✅ Good | ✅ Excellent |
| **Overall** | ❌ Not viable | ❌ Over-engineered | ✅ **Recommended** |
