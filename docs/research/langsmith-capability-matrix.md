# LangSmith Capability Matrix

**Purpose**: Matrix of LangSmith SDK and CLI capabilities with SDK/CLI support, source citations, required identifiers, and privacy risks.

**Audited Version**: LangSmith SDK 0.7.25

---

## Matrix

| Capability | SDK Support | CLI Support | Source Citation | Required Stored Identifiers | Privacy Risk | Notes / Gaps |
|------------|-------------|------------|----------------|----------------------------|--------------|--------------|
| **Datasets** | | | | | | |
| Create dataset | ✅ Full | ✅ Basic | client.py:4828-4899 | dataset.id (UUID), dataset.name | Low | SDK supports schemas, transformations; CLI basic only |
| List datasets | ✅ Full filtering | ✅ Basic | client.py:5075-5126 | None | Low | SDK: metadata, data_type, name_contains filters; CLI: list only |
| Read dataset | ✅ By name/ID | ✅ By name/ID | client.py:4925-4970 | dataset.id OR dataset.name | Low | CLI: `dataset get` |
| Delete dataset | ✅ | ✅ | client.py:5129-5155 | dataset.id OR dataset.name | Low | |
| Share dataset | ✅ | ❌ | client.py:4281-4319 | dataset.id OR dataset.name | Medium | Generates public share link |
| Unshare dataset | ✅ | ❌ | client.py:4321-4335 | dataset.id | Medium | |
| Clone public dataset | ✅ | ❌ | client.py:5301-5349 | share_token | Low | Idempotent operation |
| List dataset versions | ✅ | ❌ | client.py:5217-5250 | dataset.id OR dataset.name | Low | Supports search, limit |
| Read dataset version | ✅ | ❌ | client.py:5252-5299 | dataset.id OR dataset.name, tag OR as_of | Low | Supports timestamp or tag-based versioning |
| Diff dataset versions | ✅ | ❌ | client.py:4972-5000 | dataset.id OR dataset.name, from_version, to_version | Low | Returns DatasetDiffInfo |
| Export dataset (OpenAI format) | ✅ JSONL | ✅ JSON | client.py:5041-5073 | dataset.id OR dataset.name | Low | SDK: OpenAI finetuning JSONL; CLI: JSON |
| **Examples** | | | | | | |
| Create example | ✅ Full | ✅ Basic | client.py:6241-6320 | dataset.id OR dataset.name | Low | SDK: deterministic IDs, attachments, splits; CLI: basic only |
| Create examples (batch) | ✅ | ❌ | client.py:6007-6082 | dataset.id OR dataset.name | Low | Supports attachments, max_concurrency |
| Create example from run | ✅ | ❌ | client.py:5469-5550 | dataset.id OR dataset_name, run.id | Medium | Converts run based on dataset type |
| List examples | ✅ Full filtering | ✅ Basic | client.py:6384-6460 | dataset.id OR dataset_name | Low | SDK: as_of, splits, metadata, filter, attachments; CLI: list only |
| Read example | ✅ | ❌ | client.py:6350-6382 | example.id | Low | |
| Update example | ✅ | ❌ | client.py:6437-6467 | example.id | Low | |
| Delete example | ✅ | ✅ | client.py:6469-6499 | example.id | Low | CLI: `example delete` |
| **Runs/Traces** | | | | | | |
| Create run | ✅ Full | ❌ | client.py:2039-2150 | session_id (project) | Medium | Extensive parameters for tracing |
| Read run | ✅ | ✅ | client.py:3583-3620 | run.id | Medium | SDK: load_child_runs for full tree; CLI: `run get` |
| List runs | ✅ Extensive filtering | ✅ Extensive filtering | client.py:3678-3800 | project.id OR project.name | Medium | SDK: trace_filter, tree_filter, select; CLI: common filters |
| Read thread | ✅ | ✅ | client.py:3622-3676 | thread.id, project.id OR project.name | Medium | Multi-turn conversation queries |
| Load child runs (full tree) | ✅ | ✅ | client.py:3541-3581 | run.id | Medium | SDK: load_child_runs=True; CLI: `trace list --show-hierarchy` |
| Share run | ✅ | ❌ | client.py:4164-4183 | run.id | Medium | Generates public share link |
| Read shared run | ✅ | ❌ | client.py:4197-4220 | share_token | Medium | |
| List shared runs | ✅ | ❌ | client.py:4222-4240 | share_token | Medium | |
| **Experiments/Sessions** | | | | | | |
| List projects (sessions) | ❌ (via runs) | ✅ | client.py:3678-3800 | None | Low | SDK: discover via list_runs; CLI: `project list` |
| Create experiment | ✅ (evaluate) | ❌ | client.py:9213-9234 | dataset.id OR dataset.name | Low | SDK: `evaluate()` function creates experiments |
| List experiments | ❌ (via UI) | ✅ | CLI: experiment list | None | Low | CLI: filter by dataset; SDK: no direct method |
| Read experiment results | ❌ (via UI) | ✅ | CLI: experiment get | experiment.name | Low | CLI: `experiment get` |
| Compare experiments | ❌ (manual URL) | ❌ | N/A | experiment.ids | Low | No SDK/CLI method; must construct URL manually |
| **Feedback/Scores** | | | | | | |
| Create feedback | ✅ Full | ❌ | client.py:7193-7220 | run.id OR trace.id OR project.id | Low | Supports score, value, correction, comment, source_info |
| List feedback | ✅ Filtering | ❌ | client.py:7518-7559 | run.ids | Low | Filters: feedback_key, feedback_source_type |
| Read feedback | ✅ | ❌ | client.py:7487-7516 | feedback.id | Low | |
| Update feedback | ✅ | ❌ | client.py:7561-7577 | feedback.id | Low | |
| Delete feedback | ✅ | ❌ | client.py:7578-7605 | feedback.id | Low | |
| Create feedback from token | ✅ | ❌ | client.py:7578-7626 | share_token | Low | For external evaluators |
| Create presigned feedback token | ✅ | ❌ | client.py:7628-7675 | run.id, feedback_key | Low | |
| List feedback configs | ✅ | ❌ | client.py:8055-8100 | None | Low | Define feedback schemas (type, bounds, categories) |
| Create feedback config | ✅ | ❌ | client.py:7996-8053 | feedback_key | Low | |
| Update feedback config | ✅ | ❌ | client.py:8102-8139 | feedback_key | Low | |
| Delete feedback config | ✅ | ❌ | client.py:8141-8176 | feedback_key | Low | |
| List feedback formulas | ✅ | ❌ | client.py:7821-7859 | dataset.id OR session_id | Low | Composite metrics from weighted feedback keys |
| Create feedback formula | ✅ | ❌ | client.py:7880-7933 | feedback_key, dataset.id OR session_id | Low | |
| Update feedback formula | ✅ | ❌ | client.py:7935-7979 | feedback_formula.id | Low | |
| Delete feedback formula | ✅ | ❌ | client.py:7981-8026 | feedback_formula.id | Low | |
| **Evaluators** | | | | | | |
| List evaluators | ❌ | ✅ | CLI: evaluator list | None | Low | CLI: `evaluator list` |
| Upload evaluator | ❌ | ✅ | CLI: evaluator upload | evaluator file | Low | CLI: Python or TS functions |
| Delete evaluator | ❌ | ✅ | CLI: evaluator delete | evaluator.name | Low | |
| **Export/Local Mirror** | | | | | | |
| Export dataset | ✅ JSONL (OpenAI) | ✅ JSON | client.py:5041-5073 | dataset.id OR dataset.name | Low | SDK: OpenAI finetuning format; CLI: JSON |
| Export trace | ❌ | ✅ JSONL | CLI: trace export | project.name, filters | High | CLI: One JSONL file per trace, selective field inclusion |
| Export run | ❌ | ✅ JSONL | CLI: run export | project.name, filters | High | CLI: One JSON object per line, selective field inclusion |
| Export experiment | ❌ | ❌ | N/A | N/A | N/A | No direct export; must use experiment results |
| **Security/Privacy** | | | | | | |
| Anonymizer (custom redaction) | ✅ | ❌ | client.py:750, anonymizer.py:175-201 | None | Low | Custom function applied before API send |
| Hide inputs (global) | ✅ | ❌ | client.py:751, client.py:2349-2366 | None | Low | Boolean or function, env var HIDE_INPUTS |
| Hide outputs (global) | ✅ | ❌ | client.py:752, client.py:2358-2366 | None | Low | Boolean or function, env var HIDE_OUTPUTS |
| Hide metadata (global) | ✅ | ❌ | client.py:753, client.py:2368-2373 | None | Low | Boolean or function, env var HIDE_METADATA |
| Omit runtime info | ✅ | ❌ | client.py:754 | None | Low | Prevents SDK version, platform, Python version in extra.runtime |
| Selective field inclusion (export) | ❌ | ✅ | CLI: --include-io, --include-metadata | None | High | CLI export flags control what data is exported |
| **Pagination** | | | | | | |
| Automatic pagination (SDK) | ✅ | ❌ | client.py:1679-1709 | None | Low | Offset-based, auto-advance, default 100 |
| Explicit limit (CLI) | ❌ | ✅ | All CLI list commands | None | Low | --limit parameter, no auto-advance |
| Cursor pagination (SDK) | ✅ | ❌ | client.py:1711-1739 | None | Low | For some endpoints |

---

## Privacy Risk Legend

- **Low**: Minimal privacy risk (metadata, identifiers, structured data)
- **Medium**: Moderate privacy risk (inputs/outputs may contain sensitive data)
- **High**: High privacy risk (full trace data, potential PII in exported files)

---

## Notes on Gaps

### SDK Gaps

1. **No explicit `list_projects()` method**: Projects must be discovered via `list_runs()` with project filters
2. **No experiment comparison URL generation**: Must construct URLs manually using web URL format
3. **No dataset example count filtering**: Must list examples and count manually
4. **No bulk feedback deletion**: Must delete feedback individually
5. **No evaluator management**: Evaluator upload/delete is CLI-only

### CLI Gaps

1. **No example update command**: Can only create/delete/list examples
2. **No dataset version management**: Versioning is SDK-only
3. **No feedback management**: Feedback CRUD is SDK-only
4. **No experiment creation**: Experiments created via SDK `evaluate()` only
5. **No run creation**: Run creation is SDK-only (for tracing)
6. **No sharing management**: Dataset/run sharing is SDK-only

### Privacy Gaps

1. **No automatic hidden dataset redaction in exports**: Hidden examples may appear in traces if referenced by runs
2. **No automatic judge prompt redaction**: Judge prompts in trace metadata not automatically redacted
3. **No field-level redaction in CLI**: CLI exports must be post-processed for redaction
4. **Export defaults to minimal metadata**: CLI exports exclude inputs/outputs/feedback by default (safe default)

---

## Recommended Access Patterns

### For Dataset Operations

**Use SDK for**:
- Creating datasets with schemas (inputs_schema, outputs_schema)
- Version management (list/read/diff versions)
- Batch example operations with deterministic IDs
- Sharing/unsharing datasets

**Use CLI for**:
- Quick dataset listing
- Simple dataset export to JSON
- Example deletion by ID

### For Experiment Operations

**Use SDK for**:
- Running evaluations via `evaluate()`
- Creating feedback and formulas
- Managing feedback configs

**Use CLI for**:
- Listing experiments filtered by dataset
- Quick experiment result inspection
- Evaluator management (list/upload/delete)

### For Trace/Run Operations

**Use SDK for**:
- Complex filtering with `filter`, `trace_filter`, `tree_filter`
- Full run tree loading with `load_child_runs=True`
- Thread-based queries for multi-turn conversations
- Field selection for performance optimization
- Sharing runs

**Use CLI for**:
- Bulk trace/run export to JSONL
- Quick filtering with common flags
- Human-readable inspection with `--format pretty`
- Export with selective field inclusion (`--include-io`, `--include-metadata`)

### For Security

**Use SDK for**:
- Global privacy controls (anonymizer, hide_inputs/outputs/metadata)
- Custom redaction logic before data leaves the system
- Omitting runtime info

**Use CLI for**:
- Export with selective field inclusion (safe defaults)
- Post-processing redaction of exported files

---

## Required Identifiers Summary

### Must Persist

**Datasets**: `dataset.id` (UUID), `dataset.name` (for resolution)
**Examples**: `example.id` (UUID), `example.dataset_id` (UUID)
**Runs**: `run.id` (UUID), `run.trace_id` (UUID), `run.session_id` (UUID)
**Feedback**: `feedback.id` (UUID), `feedback.run_id` (UUID)
**Experiments**: `experiment.id` (UUID), `experiment.dataset_id` (UUID)

### Optional but Useful

**Runs**: `run.parent_run_id` (for tree structure), `run.reference_example_id` (for dataset linkage)
**Feedback**: `feedback.key` (for metric grouping)
**Examples**: `example.split` (for dataset partitioning)

---

## Source File Locations

All SDK citations refer to LangSmith SDK version 0.7.25 installed at:
`.venv/lib/python3.11/site-packages/langsmith/`

**Key Files**:
- `client.py`: Main SDK client implementation
- `schemas.py`: Pydantic schemas for entities
- `anonymizer.py`: Anonymization utilities

**CLI Binary**:
- `/Users/Jason/.local/bin/langsmith`
