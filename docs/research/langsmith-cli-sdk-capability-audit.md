# LangSmith CLI/SDK Capability Audit

**Purpose**: Source-verified audit of LangSmith CLI and SDK capabilities to inform Evaluation Evidence Workbench architecture design.

**Audited Version**: LangSmith SDK 0.7.25 (installed in `.venv`)

**Audit Date**: 2026-04-XX

**Scope**: Datasets, Examples, Experiments/Sessions, Runs/Traces, Feedback/Scores, CLI capabilities, Export/Local Mirror, Security/Privacy

---

## Executive Summary

The LangSmith SDK provides comprehensive programmatic access to all LangSmith entities with rich filtering, pagination, and export capabilities. The CLI offers a subset of these capabilities optimized for human interaction and scripting, with JSON output by default for agent compatibility.

**Key Findings:**
- SDK supports all CRUD operations for datasets, examples, runs, feedback with extensive filtering
- CLI provides focused export capabilities (JSON/JSONL) with filtering
- SDK supports deterministic example IDs, dataset versioning, and full run tree loading
- Security features include anonymizer hooks and hide_inputs/outputs/metadata parameters
- Export formats: JSON (datasets), JSONL (traces/runs), OpenAI finetuning format
- No native experiment comparison URL generation in SDK; experiments are accessed via project/session
- Pagination is automatic via iterators (SDK) and limit parameters (CLI)

---

## 1. Datasets / Examples

### SDK Capabilities

#### Dataset Creation
**Method**: `client.create_dataset()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:4828-4899`

**Parameters:**
- `dataset_name` (str): Required
- `description` (Optional[str])
- `data_type` (DataType): Default `DataType.kv`, options: `kv`, `llm`, `chat`
- `inputs_schema` (Optional[dict]): Schema definition for inputs
- `outputs_schema` (Optional[dict]): Schema definition for outputs
- `transformations` (Optional[list[DatasetTransformation]])
- `metadata` (Optional[dict])

**Returns**: `Dataset` schema with `id`, `name`, `description`, `data_type`, `created_at`, `modified_at`, `example_count`, `session_count`, `inputs_schema`, `outputs_schema`, `transformations`, `metadata`

**Identifiers to persist**: `dataset.id` (UUID), `dataset.name` (for resolution)

#### Dataset Reading
**Method**: `client.read_dataset()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:4925-4970`

**Parameters**: `dataset_name` (Optional[str]) OR `dataset_id` (Optional[ID_TYPE])

**Resolution**: Accepts either name or ID; resolves name to ID internally

#### Dataset Listing
**Method**: `client.list_datasets()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:5075-5126`

**Filters:**
- `dataset_ids` (Optional[list[ID_TYPE]])
- `data_type` (Optional[str])
- `dataset_name` (Optional[str]): Exact match
- `dataset_name_contains` (Optional[str]): Substring search
- `metadata` (Optional[dict])
- `limit` (Optional[int])

**Pagination**: Automatic iterator, default limit 100, paginates via offset

#### Dataset Versioning
**Method**: `client.list_dataset_versions()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:5217-5250`

**Parameters:**
- `dataset_id` (Optional[ID_TYPE]) OR `dataset_name` (Optional[str])
- `search` (Optional[str])
- `limit` (Optional[int])

**Method**: `client.read_dataset_version()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:5252-5299`

**Parameters:**
- `dataset_id` (Optional[ID_TYPE]) OR `dataset_name` (Optional[str])
- `as_of` (Optional[datetime.datetime]): Timestamp-based version
- `tag` (Optional[str]): Tag-based version (e.g., "latest", "prod")

**Constraint**: Exactly one of `as_of` or `tag` must be specified

**Method**: `client.diff_dataset_versions()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:4972-5000`

**Parameters:**
- `dataset_id` (Optional[ID_TYPE]) OR `dataset_name` (Optional[str])
- `from_version` (Union[str, datetime.datetime])
- `to_version` (Union[str, datetime.datetime])

**Returns**: `DatasetDiffInfo`

#### Dataset Export Formats
**Method**: `client.read_dataset_openai_finetuning()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:5041-5073`

**Returns**: `list[dict]` in OpenAI JSONL format

#### Example Creation
**Method**: `client.create_example()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:6241-6320`

**Parameters:**
- `inputs` (Optional[Mapping[str, Any]]): Required unless `use_source_run_io=True`
- `dataset_id` (Optional[ID_TYPE]) OR `dataset_name` (Optional[str])
- `created_at` (Optional[datetime.datetime])
- `outputs` (Optional[Mapping[str, Any]])
- `metadata` (Optional[Mapping[str, Any]])
- `split` (Optional[str | list[str]]): Dataset splits (e.g., "train", "test", "validation")
- `example_id` (Optional[ID_TYPE]): **Deterministic ID support** - if provided, uses this ID; otherwise generates UUID
- `source_run_id` (Optional[ID_TYPE])
- `use_source_run_io` (bool): Use inputs/outputs/attachments from source run
- `use_source_run_attachments` (Optional[list[str]]): Selective attachment copying
- `attachments` (Optional[Attachments])

**Deterministic IDs**: Supported via `example_id` parameter. If not provided, SDK generates UUID.

**Method**: `client.create_examples()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:6007-6082`

**Batch creation with `examples` parameter (list of ExampleCreate dicts). Supports attachments.**

**Method**: `client.create_example_from_run()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:5469-5550`

**Converts run to example based on dataset type (kv/llm/chat).**

#### Example Listing
**Method**: `client.list_examples()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:6384-6460`

**Filters:**
- `dataset_id` (Optional[ID_TYPE]) OR `dataset_name` (Optional[str])
- `example_ids` (Optional[Sequence[ID_TYPE]])
- `as_of` (Optional[Union[datetime.datetime, str]]): Version/time-based filtering
- `splits` (Optional[Sequence[str]])
- `inline_s3_urls` (bool): Default True
- `offset` (int): Default 0
- `limit` (Optional[int])
- `metadata` (Optional[dict])
- `filter` (Optional[str]): Structured filter string
- `include_attachments` (bool): Default False

**Pagination**: Automatic iterator with offset/limit

#### Example Update/Delete
**Method**: `client.update_example()`
**Method**: `client.delete_example()`

### CLI Capabilities

#### Dataset Commands
**Source**: `/Users/Jason/.local/bin/langsmith dataset --help`

**Commands:**
- `create`: Create new empty dataset
- `delete`: Delete dataset by name or UUID
- `export`: Export dataset examples to JSON file
  - Parameters: `NAME_OR_ID`, `OUTPUT_FILE`, `--limit` (default 100)
  - Format: JSON
- `get`: Get dataset details by name or UUID
- `list`: List all datasets in workspace
- `upload`: Upload JSON file as new dataset

#### Example Commands
**Source**: `/Users/Jason/.local/bin/langsmith example --help`

**Commands:**
- `create`: Create example in dataset with `--dataset`, `--inputs`
- `delete`: Delete example by UUID
- `list`: List examples in dataset with `--dataset`

---

## 2. Experiments / Sessions

### SDK Capabilities

**Note**: LangSmith uses "projects" (sessions) as tracing namespaces. "Experiments" are evaluation runs created via the `evaluate()` function.

#### Project/Session Listing
The SDK refers to projects as "sessions" in tracing context. Projects are namespaces for grouping traces.

**Method**: `client.list_runs()` with `project_id` or `project_name` parameter
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:3678-3800`

**Parameters:**
- `project_id` (Optional[Union[ID_TYPE, Sequence[ID_TYPE]]])
- `project_name` (Optional[Union[str, Sequence[str]]])

**No explicit `list_projects()` method in SDK** - projects are discovered via runs.

#### Evaluation (Experiment Creation)
**Method**: `client.evaluate()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:9213-9234`

**Parameters:**
- `target` (Union[TARGET_T, Runnable, EXPERIMENT_T, tuple]): System to evaluate
- `data` (DATA_T): Dataset (name, list of examples, or generator)
- `evaluators` (Optional[Sequence[EVALUATOR_T]]): List of evaluators
- `summary_evaluators` (Optional[Sequence[SUMMARY_EVALUATOR_T]]): Summary evaluators
- `metadata` (Optional[dict]): Metadata to attach to experiment
- `experiment_prefix` (Optional[str]): Prefix for experiment name
- `description` (Optional[str])
- `max_concurrency` (Optional[int])
- `num_repetitions` (int): Default 1
- `blocking` (bool): Default True
- `experiment` (Optional[EXPERIMENT_T]): Existing experiment
- `upload_results` (bool): Default True
- `error_handling` (Literal["log", "ignore"]): Default "log"

**Returns**: `ExperimentResults` or `ComparativeExperimentResults`

**No explicit experiment comparison URL generation in SDK** - comparison is done via LangSmith UI.

### CLI Capabilities

#### Experiment Commands
**Source**: `/Users/Jason/.local/bin/langsmith experiment --help`

**Commands:**
- `get`: Get detailed results for specific experiment
- `list`: List experiments, optionally filtered by dataset
  - Parameters: `--dataset`, `--limit` (default 20), `--output`

#### Project Commands
**Source**: `/Users/Jason/.local/bin/langsmith project --help`

**Commands:**
- `list`: List tracing projects in workspace
  - Parameters: `--limit`, `--name-contains`

**Note**: Projects are tracing namespaces (sessions), not experiments.

---

## 3. Runs / Traces

### SDK Capabilities

#### Run Creation
**Method**: `client.create_run()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:2039-2150`

**Parameters**: Extensive parameters for run creation including inputs, outputs, metadata, tags, parent_run_id, etc.

#### Run Reading
**Method**: `client.read_run()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:3583-3620`

**Parameters:**
- `run_id` (ID_TYPE): Required
- `load_child_runs` (bool): Default False - **Load full run tree**

**Returns**: `Run` schema. If `load_child_runs=True`, loads nested child runs recursively via `_load_child_runs()`.

**Method**: `client._load_child_runs()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:3541-3581`

**Implementation**: Fetches all non-root runs in the same session/trace, builds tree structure using `dotted_order` and `parent_run_id`.

#### Run Listing
**Method**: `client.list_runs()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:3678-3800`

**Filters:**
- `project_id` (Optional[Union[ID_TYPE, Sequence[ID_TYPE]]])
- `project_name` (Optional[Union[str, Sequence[str]]])
- `run_type` (Optional[str])
- `trace_id` (Optional[ID_TYPE])
- `reference_example_id` (Optional[ID_TYPE])
- `query` (Optional[str])
- `filter` (Optional[str]): Raw filter DSL
- `trace_filter` (Optional[str]): Filter on ROOT run in trace tree
- `tree_filter` (Optional[str]): Filter on OTHER runs in trace tree (siblings, children)
- `is_root` (Optional[bool]): Filter for root runs only
- `parent_run_id` (Optional[ID_TYPE])
- `start_time` (Optional[datetime.datetime])
- `error` (Optional[bool])
- `run_ids` (Optional[Sequence[ID_TYPE]])
- `select` (Optional[Sequence[str]]): Field selection for performance
- `limit` (Optional[int])

**Pagination**: Automatic iterator via `_get_paginated_list()` with offset/limit

**Method**: `client._get_paginated_list()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:1679-1709`

**Implementation**: Uses offset-based pagination, default limit 100, auto-advances until empty result.

#### Thread Reading
**Method**: `client.read_thread()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:3622-3676`

**Parameters:**
- `thread_id` (str): Required
- `project_id` (Optional[Union[ID_TYPE, Sequence[ID_TYPE]]]) OR `project_name` (Optional[Union[str, Sequence[str]]])
- `is_root` (bool): Default True
- `limit` (Optional[int])
- `select` (Optional[Sequence[str]])
- `filter` (Optional[str])
- `order` (Literal["asc", "desc"]): Default "asc"

**Purpose**: Fetch all runs (turns) in a multi-turn conversation thread.

#### Run Sharing
**Method**: `client.read_run_shared_link()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:4164-4183`

**Returns**: Shareable URL or None

**Method**: `client.run_is_shared()`
**Method**: `client.read_shared_run()`
**Method**: `client.list_shared_runs()`

### CLI Capabilities

#### Trace Commands
**Source**: `/Users/Jason/.local/bin/langsmith trace --help`

**Commands:**
- `export`: Export traces to directory as JSONL files (one file per trace)
  - Parameters: `OUTPUT_DIR`
  - Filters: `--error`, `--no-error`, `--filter`, `--full` (shorthand for include-metadata/io/feedback), `--include-feedback`, `--include-io`, `--include-metadata`, `--last-n-minutes`, `--limit`, `--max-latency`, `--metadata`, `--min-latency`, `--min-tokens`, `--name`, `--project`, `--since`, `--tags`, `--trace-ids`
  - Format: JSONL per trace, supports `--filename-pattern` with `{trace_id}` and `{name}` placeholders
- `get`: Fetch every run in a single trace
  - Parameters: `<trace-id>`, `--project`, `--full`
- `list`: List traces (root runs) matching filter criteria
  - Filters: Same as export plus `--show-hierarchy` (fetch full run tree), `--output` (write to file)

**Note**: `--show-hierarchy` fetches full run tree for each trace.

#### Run Commands
**Source**: `/Users/Jason/.local/bin/langsmith run --help`

**Commands:**
- `export`: Export runs to JSONL file (one JSON object per line)
  - Parameters: `OUTPUT_FILE`
  - Filters: Same as trace export plus `--run-type`
- `get`: Fetch single run by run ID
  - Parameters: `<run-id>`, `--full`
- `list`: List runs matching filter criteria (any run type at any depth)
  - Filters: Same as export plus `--run-type`, `--output`

#### Thread Commands
**Source**: `/Users/Jason/.local/bin/langsmith thread --help`

**Commands:**
- `get`: Fetch all runs (turns) in a single conversation thread
  - Parameters: `<thread-id>`, `--project`, `--full`
- `list`: List conversation threads in a project
  - Parameters: `--project`, `--limit`

---

## 4. Feedback / Scores / Evaluator Outputs

### SDK Capabilities

#### Feedback Creation
**Method**: `client.create_feedback()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7193-7220`

**Parameters:**
- `run_id` (Optional[ID_TYPE]): At least one of run_id, trace_id, or project_id required
- `key` (str): Feedback metric name, default "unnamed"
- `score` (Optional[Union[float, int, bool]]): Numeric score
- `value` (Optional[Union[float, int, bool, str, dict]]): Display value or non-numeric value
- `trace_id` (Optional[ID_TYPE]): Required for background batching
- `correction` (Optional[dict]): Ground truth correction
- `comment` (Optional[str]): Justification or CoT trajectory
- `source_info` (Optional[dict[str, Any]]): Source metadata
- `feedback_source_type` (Union[FeedbackSourceType, str]): Default `FeedbackSourceType.API`, options: "model", "api"
- `source_run_id` (Optional[ID_TYPE])
- `feedback_id` (Optional[ID_TYPE])
- `feedback_config` (Optional[FeedbackConfig])
- `stop_after_attempt` (int): Default 10
- `project_id` (Optional[ID_TYPE])
- `comparative_experiment_id` (Optional[ID_TYPE])
- `feedback_group_id` (Optional[ID_TYPE])
- `extra` (Optional[dict])
- `error` (Optional[bool])
- `session_id` (Optional[ID_TYPE])
- `start_time` (Optional[datetime.datetime])

**Normalization**: SDK handles score formatting via `_format_feedback_score()` (truncates float to 4 decimal places).

**Method**: `client.create_feedback_from_token()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7578-7626`

**Purpose**: Create feedback from presigned token (for external evaluators).

**Method**: `client.create_presigned_feedback_token()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7628-7675`

**Purpose**: Create presigned URL for feedback submission.

#### Feedback Listing
**Method**: `client.list_feedback()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7518-7559`

**Filters:**
- `run_ids` (Optional[Sequence[ID_TYPE]])
- `feedback_key` (Optional[Sequence[str]]): Union (OR logic)
- `feedback_source_type` (Optional[Sequence[FeedbackSourceType]])
- `limit` (Optional[int])

**Pagination**: Automatic iterator, default limit 100

#### Feedback Configurations (Schema Definitions)
**Method**: `client.create_feedback_config()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7996-8053`

**Parameters:**
- `feedback_key` (str)
- `feedback_config` (FeedbackConfig): Type, bounds, categories
- `is_lower_score_better` (Optional[bool]): Default False

**Purpose**: Define how feedback with a given key should be interpreted (type, bounds, categories).

**Method**: `client.list_feedback_configs()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:8055-8100`

**Filters:**
- `feedback_key` (Optional[Sequence[str]])
- `name_contains` (Optional[str])
- `limit` (Optional[int])
- `offset` (int)

**Method**: `client.update_feedback_config()`
**Method**: `client.delete_feedback_config()`

#### Feedback Formulas (Aggregation)
**Method**: `client.create_feedback_formula()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7880-7933`

**Parameters:**
- `feedback_key` (str)
- `aggregation_type` (Literal["sum", "avg"])
- `formula_parts` (Sequence[FeedbackFormulaWeightedVariable | dict])
- `dataset_id` (Optional[ID_TYPE])
- `session_id` (Optional[ID_TYPE])

**Purpose**: Create composite metrics from weighted feedback keys.

**Method**: `client.list_feedback_formulas()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7821-7859`

**Filters:**
- `dataset_id` (Optional[ID_TYPE])
- `session_id` (Optional[ID_TYPE])
- `limit` (Optional[int])
- `offset` (int)

#### Evaluator Functions
**Method**: `client.evaluate_run()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:7053-7092`

**Purpose**: Evaluate a single run with a RunEvaluator.

**Method**: `client.evaluate()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:9213-9234`

**Purpose**: Evaluate a target system on a dataset, creating an experiment.

### CLI Capabilities

#### Evaluator Commands
**Source**: `/Users/Jason/.local/bin/langsmith evaluator --help`

**Commands:**
- `list`: List all evaluator rules in workspace
- `upload`: Upload evaluator function (Python or TS) to LangSmith
  - Parameters: `eval.py` or `eval.ts`, `--name`, `--function`, `--dataset`
- `delete`: Delete evaluator rule by display name
  - Parameters: `--name`, `--yes`

**Purpose**: Manage online/offline evaluator rules that automatically score runs.

---

## 5. Export / Local Mirror

### Export Formats

#### Dataset Export
**SDK**: `client.read_dataset_openai_finetuning()` returns OpenAI JSONL format
**CLI**: `langsmith dataset export NAME_OR_ID OUTPUT_FILE` exports to JSON

**Format**: JSON array of example objects

#### Trace Export
**CLI**: `langsmith trace export OUTPUT_DIR` exports to JSONL files (one per trace)

**Format**: JSONL, one line per run in the trace tree

**Flags for content control:**
- `--full`: Shorthand for `--include-metadata --include-io --include-feedback`
- `--include-metadata`: Add status, duration_ms, token_usage, costs, tags, custom_metadata (incl. revision_id)
- `--include-io`: Add inputs, outputs, and error fields
- `--include-feedback`: Add feedback_stats field

**Default**: Minimal metadata only (no inputs/outputs/feedback by default)

#### Run Export
**CLI**: `langsmith run export OUTPUT_FILE` exports to JSONL

**Format**: JSONL, one JSON object per line

**Content flags**: Same as trace export

### Stable Mirror Format Recommendations

**For datasets**: JSON (CLI export) or OpenAI JSONL (SDK method)
**For traces**: JSONL per trace (CLI export) with `--include-metadata --include-io --include-feedback` for full mirror
**For runs**: JSONL (CLI export) with selective field inclusion

**Pagination handling**: Both SDK (iterators) and CLI (limit parameters) handle pagination automatically.

---

## 6. Security / Privacy

### SDK Privacy Features

#### Anonymizer
**Parameter**: `anonymizer` (Optional[Callable[[dict], dict]]) in `Client.__init__()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:750`

**Purpose**: Custom function applied for masking serialized run inputs and outputs before sending to API.

**Implementation**: `.venv/lib/python3.11/site-packages/langsmith/anonymizer.py`

**Features**:
- `create_anonymizer(replacer, max_depth)`: Creates anonymizer function
- Supports regex-based rules (`RuleNodeProcessor`)
- Supports callable functions (`CallableNodeProcessor`)
- Traverses data structure to configurable depth (default 10)
- Replaces string nodes matching patterns or custom logic

**Usage**:
```python
from langsmith.anonymizer import create_anonymizer

anonymizer = create_anonymizer([
    {"pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "replace": "[email]"},
    {"pattern": r"\b\d{3}-\d{2}-\d{4}\b", "replace": "[ssn]"},
])
client = Client(anonymizer=anonymizer)
```

#### Hide Inputs/Outputs/Metadata
**Parameters** in `Client.__init__()`:
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:751-753`

- `hide_inputs` (Optional[Union[Callable[[dict], dict], bool]]): If True, hides entire inputs. If function, applied to all run inputs.
- `hide_outputs` (Optional[Union[Callable[[dict], dict], bool]]): If True, hides entire outputs. If function, applied to all run outputs.
- `hide_metadata` (Optional[Union[Callable[[dict], dict], bool]]): If True, hides entire metadata. If function, applied to all run metadata.

**Environment variables**: `HIDE_INPUTS`, `HIDE_OUTPUTS`, `HIDE_METADATA` (set to "true")

**Implementation**: `.venv/lib/python3.11/site-packages/langsmith/client.py:2349-2373`

- `_hide_run_inputs()`: Returns {} if True, applies anonymizer if set, applies function if callable
- `_hide_run_outputs()`: Same logic
- `_hide_run_metadata()`: Returns {} if True, applies function if callable

#### Omit Traced Runtime Info
**Parameter**: `omit_traced_runtime_info` (bool) in `Client.__init__()`
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:754`

**Purpose**: If True, runtime information (SDK version, platform, Python version, etc.) will not be stored in `extra.runtime` field.

### Privacy Risks

#### Hidden Dataset Exposure
**Finding**: No explicit SDK mechanism to prevent hidden dataset rows from appearing in exported traces. If a run references a hidden example via `reference_example_id`, the example data may appear in the run's inputs/outputs depending on tracing configuration.

**Mitigation**: Use `hide_inputs`/`hide_outputs` at Client level to prevent sensitive data from being sent to LangSmith in the first place.

#### Judge Prompt/Rubric Exposure
**Finding**: Judge prompts and rubric text can appear in trace metadata if evaluators log this information. No automatic redaction.

**Mitigation**: Use custom `anonymizer` to redact judge prompts from traces, or use `hide_metadata` to prevent metadata from being sent.

#### Developer-Safe Outputs
**Requirement**: Meta Harness must redact sensitive fields before developer-safe outputs.

**Recommended approach**:
1. Use SDK `hide_inputs`/`hide_outputs`/`hide_metadata` for production tracing
2. For exported traces, apply additional redaction via custom anonymizer or post-processing
3. Never export full traces with `--include-io` without redaction for developer access

---

## 7. Identifiers and Metadata

### Required Identifiers to Persist

**Datasets:**
- `dataset.id` (UUID): Primary identifier
- `dataset.name` (str): For human-readable resolution

**Examples:**
- `example.id` (UUID): Primary identifier
- `example.dataset_id` (UUID): Foreign key to dataset
- `example.split` (str): For dataset partitioning

**Runs/Traces:**
- `run.id` (UUID): Primary identifier
- `run.trace_id` (UUID): Root run ID (for trace grouping)
- `run.session_id` (UUID): Project/session ID
- `run.parent_run_id` (UUID): For tree structure
- `run.reference_example_id` (UUID): Link to dataset example

**Feedback:**
- `feedback.id` (UUID): Primary identifier
- `feedback.run_id` (UUID): Link to run
- `feedback.key` (str): Metric name

**Experiments:**
- `experiment.id` (UUID): Primary identifier
- `experiment.dataset_id` (UUID): Link to dataset
- `experiment.project_id` (UUID): Link to project/session

### Metadata Fields

**Dataset metadata**: Custom dict, searchable via `list_datasets(metadata=...)`

**Example metadata**: Custom dict, searchable via `list_examples(metadata=...)`, supports `filter` parameter for structured queries

**Run metadata**: Custom dict in `extra.metadata`, searchable via `list_runs(metadata=...)` and `filter` parameter

**Feedback metadata**: Custom dict in `source_info` or `extra`

### Resolution Patterns

**Name-to-ID resolution**: Supported for datasets (`read_dataset(dataset_name=...)`), examples (`list_examples(dataset_name=...)`), projects (`list_runs(project_name=...)`)

**ID-to-name lookup**: Not directly supported; must fetch entity by ID and read name field

---

## 8. Pagination and Rate Limits

### SDK Pagination

**Pattern**: Automatic iterator with internal pagination

**Implementation**: `_get_paginated_list()` uses offset-based pagination
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:1679-1709`

**Default limit**: 100 items per page
**Auto-advance**: Continues fetching until empty result

**Cursor pagination**: `_get_cursor_paginated_list()` for some endpoints
**Source**: `.venv/lib/python3.11/site-packages/langsmith/client.py:1711-1739`

### CLI Pagination

**Pattern**: Explicit `--limit` parameter

**Default**: Varies by command (typically 20-100)
**No auto-advance**: Must increase limit for more results

### Rate Limits

**No explicit rate limit configuration in SDK**: Relies on server-side rate limiting and retry logic

**Retry configuration**: `retry_config` parameter in `Client.__init__()` for HTTPAdapter retry behavior

---

## 9. Comparison URLs

### SDK Comparison URL Generation

**Finding**: No explicit SDK method to generate experiment comparison URLs.

**Workaround**: Construct URLs manually using web URL format:
```
{web_url}/comparisons/{experiment_id_1}...{experiment_id_n}
```

**Web URL**: Available via `client._host_url` or inferred from API URL

### CLI Comparison URL Generation

**Finding**: CLI does not generate comparison URLs.

**Recommendation**: Use LangSmith UI for experiment comparisons, or construct URLs manually.

---

## 10. CLI Non-Interactive Usage

### JSON Output Default

**Default format**: `--format json` (machine-readable JSON)

**Alternative**: `--format pretty` (human-readable tables, trees, syntax-highlighted JSON)

**Environment variables**: `LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT`, `LANGSMITH_PROJECT`

### Agent-Friendly Design

**Design intent**: "Designed for AI coding agents and developers who need fast, scriptable access"

**All commands output JSON by default** for easy parsing

**No interactive prompts**: All parameters via flags or environment variables

---

## 11. Gaps and Limitations

### SDK Gaps

1. **No explicit `list_projects()` method**: Projects discovered via runs
2. **No experiment comparison URL generation**: Must construct manually
3. **No dataset example count filtering**: Must list and count manually
4. **No bulk feedback deletion**: Must delete individually

### CLI Gaps

1. **No example update command**: Can only create/delete/list
2. **No dataset version listing via CLI**: Must use SDK
3. **No feedback management via CLI**: Must use SDK
4. **No experiment creation via CLI**: Must use SDK `evaluate()`

### Privacy Gaps

1. **No automatic hidden dataset redaction in exports**: Hidden examples may appear in traces
2. **No automatic judge prompt redaction**: Must use anonymizer
3. **No field-level redaction hooks in CLI**: Must post-process exports

---

## 12. Recommended Meta Harness Access Paths

### For Dataset Operations

**Use SDK for**:
- Creating datasets with schemas
- Version management and diffing
- Batch example operations
- Deterministic example IDs

**Use CLI for**:
- Quick dataset listing
- Simple dataset export to JSON

### For Experiment Operations

**Use SDK for**:
- Running evaluations via `evaluate()`
- Fetching experiment results
- Managing feedback and formulas

**Use CLI for**:
- Listing experiments filtered by dataset
- Quick experiment result inspection

### For Trace/Run Operations

**Use SDK for**:
- Complex filtering with `filter`, `trace_filter`, `tree_filter`
- Full run tree loading with `load_child_runs=True`
- Thread-based queries for multi-turn conversations
- Field selection for performance

**Use CLI for**:
- Bulk trace/run export to JSONL
- Quick filtering with common flags
- Human-readable inspection with `--format pretty`

### For Security

**Use SDK for**:
- Global privacy controls via `anonymizer`, `hide_inputs/outputs/metadata`
- Custom redaction logic

**Use CLI for**:
- Export with selective field inclusion (`--include-io`, `--include-metadata`)
- Post-processing redaction of exported files

---

## 13. Source Citations

All citations refer to LangSmith SDK version 0.7.25 installed at:
`.venv/lib/python3.11/site-packages/langsmith/`

### Key Files

- `client.py`: Main SDK client implementation
- `schemas.py`: Pydantic schemas for entities
- `anonymizer.py`: Anonymization utilities
- `cli/`: CLI implementation (external binary at `/Users/Jason/.local/bin/langsmith`)

### Method Citations

- `create_dataset()`: client.py:4828-4899
- `list_datasets()`: client.py:5075-5126
- `read_dataset()`: client.py:4925-4970
- `list_dataset_versions()`: client.py:5217-5250
- `read_dataset_version()`: client.py:5252-5299
- `diff_dataset_versions()`: client.py:4972-5000
- `read_dataset_openai_finetuning()`: client.py:5041-5073
- `create_example()`: client.py:6241-6320
- `create_examples()`: client.py:6007-6082
- `list_examples()`: client.py:6384-6460
- `create_run()`: client.py:2039-2150
- `read_run()`: client.py:3583-3620
- `list_runs()`: client.py:3678-3800
- `_load_child_runs()`: client.py:3541-3581
- `read_thread()`: client.py:3622-3676
- `create_feedback()`: client.py:7193-7220
- `list_feedback()`: client.py:7518-7559
- `create_feedback_config()`: client.py:7996-8053
- `list_feedback_configs()`: client.py:8055-8100
- `create_feedback_formula()`: client.py:7880-7933
- `list_feedback_formulas()`: client.py:7821-7859
- `evaluate()`: client.py:9213-9234
- `_get_paginated_list()`: client.py:1679-1709
- `_hide_run_inputs()`: client.py:2349-2366
- `_hide_run_outputs()`: client.py:2358-2366
- `_hide_run_metadata()`: client.py:2368-2373
- `create_anonymizer()`: anonymizer.py:175-201

### CLI Citations

- CLI binary: `/Users/Jason/.local/bin/langsmith`
- `dataset --help`: Dataset commands
- `trace --help`: Trace commands
- `run --help`: Run commands
- `experiment --help`: Experiment commands
- `project --help`: Project commands
- `evaluator --help`: Evaluator commands
- `example --help`: Example commands
- `thread --help`: Thread commands
- `sandbox --help`: Sandbox commands

---

## Appendix A: Schema Definitions

### Dataset Schema
**File**: `.venv/lib/python3.11/site-packages/langsmith/schemas.py`

**Fields**: id, name, description, data_type, created_at, modified_at, example_count, session_count, inputs_schema, outputs_schema, transformations, metadata

### Example Schema
**Fields**: id, dataset_id, inputs, outputs, metadata, created_at, modified_at, source_run_id, attachments, split

### Run Schema
**Fields**: id, trace_id, session_id, parent_run_id, run_type, inputs, outputs, error, metadata, tags, start_time, end_time, extra, reference_example_id

### Feedback Schema
**Fields**: id, run_id, key, score, value, correction, comment, source_info, feedback_source_type, created_at, modified_at

---

## Appendix B: Filter DSL Examples

### Run Filter Examples
```python
# Filter by metadata
client.list_runs(project_name="my-project", metadata={"revision_id": "abc123"})

# Filter by error status
client.list_runs(project_name="my-project", error=False)

# Filter by run type
client.list_runs(project_name="my-project", run_type="llm")

# Filter by reference example
client.list_runs(project_name="my-project", reference_example_id=example_id)

# Structured filter string
client.list_runs(project_name="my-project", filter='eq(name, "my_run")')
```

### Example Filter Examples
```python
# Filter by split
client.list_examples(dataset_name="my-dataset", splits=["train", "test"])

# Filter by metadata
client.list_examples(dataset_name="my-dataset", metadata={"difficulty": "hard"})

# Structured filter
client.list_examples(dataset_name="my-dataset", filter='contains(inputs.question, "test")')
```

---

## Appendix C: Export Format Samples

### Dataset Export (JSON)
```json
[
  {
    "id": "uuid",
    "dataset_id": "uuid",
    "inputs": {"question": "What is LangSmith?"},
    "outputs": {"answer": "LangSmith is..."},
    "metadata": {"difficulty": "easy"},
    "split": "train"
  }
]
```

### Trace Export (JSONL per trace)
```jsonl
{"id": "uuid", "trace_id": "uuid", "run_type": "chain", "inputs": {...}, "outputs": {...}}
{"id": "uuid", "trace_id": "uuid", "run_type": "llm", "inputs": {...}, "outputs": {...}}
```

### Run Export (JSONL)
```jsonl
{"id": "uuid", "trace_id": "uuid", "run_type": "llm", "inputs": {...}, "outputs": {...}}
{"id": "uuid", "trace_id": "uuid", "run_type": "tool", "inputs": {...}, "outputs": {...}}
```
