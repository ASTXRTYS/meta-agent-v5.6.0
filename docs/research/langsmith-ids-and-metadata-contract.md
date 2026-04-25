# LangSmith IDs and Metadata Contract

**Purpose**: Define the identifiers and metadata fields that Meta Harness must persist to interact with LangSmith effectively.

**Audited Version**: LangSmith SDK 0.7.25

**Scope**: Datasets, Examples, Experiments/Sessions, Runs/Traces, Feedback

---

## 1. Identifier Types

### UUID Identifiers

LangSmith uses UUID v4 identifiers for all entities. These are stable, globally unique, and should be persisted for all references.

**Format**: Standard UUID string (e.g., "c9ace0d8-a82c-4b6c-13d2-83401d68e9ab")

**Generation**:
- SDK generates UUIDs automatically if not provided
- Examples support deterministic IDs via `example_id` parameter
- All other entities use server-generated UUIDs

### Name Identifiers

Human-readable identifiers used for resolution. Names are unique per workspace but may change over time.

**Resolution Pattern**: SDK methods accept either `name` or `id` parameters (XOR constraint enforced via `@ls_utils.xor_args` decorator)

**Stability**: Names are more stable than IDs for human reference but IDs are required for programmatic access.

---

## 2. Dataset Identifiers and Metadata

### Required Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `dataset.id` | UUID | Primary identifier | ✅ Yes |
| `dataset.name` | string | Human-readable resolution | ✅ Yes |

### Optional Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `dataset.share_token` | string | Public sharing token | ⚠️ If sharing enabled |

### Metadata Schema

**Field**: `dataset.metadata` (dict[str, Any])

**Supported Operations**:
- Filter via `list_datasets(metadata=...)`
- Free-form key-value pairs

**Common Meta Harness Fields** (recommended):
- `project_id`: Meta Harness project reference
- `created_by`: Agent or user who created dataset
- `purpose`: Evaluation, testing, training, etc.
- `domain`: Application domain (e.g., "chatbot", "code-assistant")

**Searchability**: Metadata is searchable via exact match on `list_datasets()`.

---

## 3. Example Identifiers and Metadata

### Required Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `example.id` | UUID | Primary identifier | ✅ Yes |
| `example.dataset_id` | UUID | Foreign key to dataset | ✅ Yes |

### Optional Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `example.source_run_id` | UUID | Link to originating run | ⚠️ If created from run |

### Metadata Schema

**Field**: `example.metadata` (dict[str, Any])

**Supported Operations**:
- Filter via `list_examples(metadata=...)`
- Filter via structured `filter` parameter
- Free-form key-value pairs

**Common Meta Harness Fields** (recommended):
- `difficulty`: easy, medium, hard
- `category`: Behavior category being tested
- `source`: production_trace, synthetic, curated
- `hidden`: Boolean flag for hidden examples

**Split Field**:
- `example.split` (str | list[str]): Dataset partition (e.g., "train", "test", "validation")
- Filterable via `list_examples(splits=...)`
- **Persistence Required**: ✅ Yes (for dataset partitioning)

**Deterministic IDs**:
- Supported via `create_example(example_id=...)` parameter
- **Use Case**: When importing examples from external systems with stable IDs
- **Persistence Required**: ⚠️ Only if using deterministic IDs

---

## 4. Run/Trace Identifiers and Metadata

### Required Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `run.id` | UUID | Primary identifier | ✅ Yes |
| `run.trace_id` | UUID | Root run ID (trace grouping) | ✅ Yes |
| `run.session_id` | UUID | Project/session ID | ✅ Yes |

### Optional Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `run.parent_run_id` | UUID | Parent run in tree | ⚠️ For tree reconstruction |
| `run.reference_example_id` | UUID | Link to dataset example | ⚠️ For evaluation linkage |

### Thread Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `thread_id` | string | Multi-turn conversation ID | ⚠️ For chat applications |

### Metadata Schema

**Field**: `run.extra.metadata` (dict[str, Any])

**Supported Operations**:
- Filter via `list_runs(metadata=...)`
- Filter via structured `filter` parameter (e.g., `eq(metadata.revision_id, "abc123")`)
- Free-form key-value pairs

**Common Meta Harness Fields** (recommended):
- `revision_id`: Code revision or deployment ID
- `agent_role`: Which agent generated the run
- `environment`: sandbox, local, production
- `test_id`: Link to test case or evaluation ID

**Tags**:
- `run.tags` (list[str]): Alternative to metadata for categorical labeling
- Filterable via `list_runs()` and CLI `--tags` flag
- **Persistence Required**: ⚠️ If using tags

**Runtime Metadata** (auto-populated):
- `run.extra.runtime`: SDK version, platform, Python version, etc.
- Can be omitted via `omit_traced_runtime_info=True` in Client init
- **Persistence Required**: ❌ No (can be omitted)

---

## 5. Feedback Identifiers and Metadata

### Required Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `feedback.id` | UUID | Primary identifier | ✅ Yes |
| `feedback.run_id` | UUID | Link to run | ✅ Yes |

### Optional Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `feedback.trace_id` | UUID | Link to trace (root run) | ⚠️ For trace-level feedback |
| `feedback.project_id` | UUID | Link to project | ⚠️ For project-level feedback |

### Feedback Key

**Field**: `feedback.key` (string)

**Purpose**: Metric name (e.g., "correctness", "helpfulness", "latency")

**Persistence Required**: ✅ Yes (for metric grouping)

**Normalization**:
- SDK truncates float scores to 4 decimal places via `_format_feedback_score()`
- No automatic normalization for other value types

### Metadata Schema

**Field**: `feedback.source_info` (dict[str, Any])

**Purpose**: Source metadata for feedback (e.g., evaluator name, model version)

**Common Meta Harness Fields** (recommended):
- `evaluator_name`: Which evaluator generated the feedback
- `evaluator_version`: Version of evaluator logic
- `evaluation_type": online, offline, manual

**Extra Field**:
- `feedback.extra` (dict[str, Any]): Additional metadata
- **Persistence Required**: ⚠️ If using extra metadata

---

## 6. Experiment/Session Identifiers and Metadata

### Required Identifiers

| Field | Type | Purpose | Persistence Required |
|-------|------|---------|----------------------|
| `experiment.id` | UUID | Primary identifier | ✅ Yes |
| `experiment.dataset_id` | UUID | Link to dataset | ✅ Yes |
| `experiment.project_id` | UUID | Link to project/session | ✅ Yes |

### Metadata Schema

**Field**: `experiment.metadata` (dict[str, Any])

**Purpose**: Experiment-level metadata

**Supported Operations**: Set via `evaluate(metadata=...)`

**Common Meta Harness Fields** (recommended):
- `agent_version`: Agent configuration version
- `harness_config`: Harness parameters used
- `evaluation_purpose`: regression, optimization, exploration

---

## 7. Resolution Patterns

### Name-to-ID Resolution

**Supported for**: Datasets, Projects (Sessions)

**SDK Methods**:
- `read_dataset(dataset_name=...)` → returns dataset with ID
- `list_runs(project_name=...)` → returns runs with session_id

**Pattern**:
```python
# Resolve dataset name to ID
dataset = client.read_dataset(dataset_name="my-dataset")
dataset_id = dataset.id

# Resolve project name to session_id
runs = list(client.list_runs(project_name="my-project", limit=1))
session_id = runs[0].session_id if runs else None
```

**CLI Support**:
- `dataset get NAME` → returns dataset with ID
- `project list --name-contains SUBSTRING` → lists projects

### ID-to-Name Lookup

**Not directly supported**: Must fetch entity by ID and read name field

**Pattern**:
```python
dataset = client.read_dataset(dataset_id=dataset_id)
dataset_name = dataset.name
```

---

## 8. Identifier Persistence Strategy

### Primary Storage

**Project Data Plane** (see `docs/specs/project-data-plane.md`):
- Store all LangSmith identifiers in Project Data Plane schemas
- Use foreign key relationships for entity linkage
- Maintain referential integrity

### Recommended Schema

```python
# Dataset reference
{
    "langsmith_dataset_id": UUID,
    "langsmith_dataset_name": str,
    "metadata": dict[str, Any],
    "created_at": datetime,
    "last_synced_at": datetime
}

# Example reference
{
    "langsmith_example_id": UUID,
    "langsmith_dataset_id": UUID,
    "split": str | list[str],
    "metadata": dict[str, Any],
    "created_at": datetime
}

# Run/Trace reference
{
    "langsmith_run_id": UUID,
    "langsmith_trace_id": UUID,
    "langsmith_session_id": UUID,
    "langsmith_project_id": UUID,
    "parent_run_id": UUID | None,
    "reference_example_id": UUID | None,
    "thread_id": str | None,
    "metadata": dict[str, Any],
    "created_at": datetime
}

# Feedback reference
{
    "langsmith_feedback_id": UUID,
    "langsmith_run_id": UUID,
    "langsmith_trace_id": UUID | None,
    "langsmith_project_id": UUID | None,
    "feedback_key": str,
    "score": float | int | bool | None,
    "value": Any | None,
    "source_info": dict[str, Any],
    "created_at": datetime
}

# Experiment reference
{
    "langsmith_experiment_id": UUID,
    "langsmith_dataset_id": UUID,
    "langsmith_project_id": UUID,
    "metadata": dict[str, Any],
    "created_at": datetime
}
```

### Indexing Recommendations

**Primary Keys**:
- All `langsmith_*_id` fields should be indexed

**Foreign Keys**:
- `langsmith_dataset_id` in example references
- `langsmith_session_id` / `langsmith_project_id` in run references
- `langsmith_run_id` in feedback references
- `langsmith_dataset_id` in experiment references

**Search Indices**:
- `langsmith_dataset_name` for name-based lookup
- `langsmith_trace_id` for trace grouping
- `feedback_key` for metric grouping
- Common metadata fields (e.g., `revision_id`, `agent_role`)

---

## 9. Metadata Field Conventions

### Reserved Keys

LangSmith reserves some keys for internal use. Avoid using these in custom metadata:

**Reserved in `extra`**:
- `runtime`: Auto-populated runtime information
- `langsmith`: LangSmith internal metadata

### Meta Harness Conventions

**Prefix convention**: Use `mh_` prefix for Meta Harness-specific metadata to avoid collisions

**Standard Fields**:
- `mh_project_id`: Meta Harness project reference
- `mh_agent_role`: Agent role that created the entity
- `mh_revision_id`: Code revision identifier
- `mh_environment`: Execution environment
- `mh_purpose`: Purpose classification

**Example**:
```python
{
    "mh_project_id": "proj-123",
    "mh_agent_role": "developer",
    "mh_revision_id": "abc123",
    "mh_environment": "sandbox",
    "mh_purpose": "regression_test",
    "custom_field": "value"
}
```

---

## 10. Identifier Lifecycle

### Creation

**Server-generated**: Most identifiers are generated by LangSmith server on entity creation
- Dataset ID: Generated by `create_dataset()`
- Example ID: Generated by `create_example()` unless `example_id` provided
- Run ID: Generated by `create_run()`
- Feedback ID: Generated by `create_feedback()`
- Experiment ID: Generated by `evaluate()`

**Client-generated**: Only supported for examples via `example_id` parameter

### Immutability

**UUID identifiers**: Immutable once created
**Names**: Can change but should be treated as stable for resolution
**Metadata**: Can be updated via SDK methods (e.g., `update_example()`, `update_feedback()`)

### Deletion

**Cascade behavior**: Deleting a parent entity does NOT automatically delete child entities
- Deleting a dataset does NOT delete its examples
- Deleting a run does NOT delete its feedback
- Deleting a project does NOT delete its runs

**Manual cleanup required**: Must explicitly delete child entities if needed

---

## 11. Privacy-Sensitive Identifiers

### Share Tokens

**Entities with share tokens**:
- Datasets: `dataset.share_token`
- Runs: `run.share_token` (via `read_run_shared_link()`)

**Privacy Risk**: Medium (public access via share URL)

**Persistence Decision**: ⚠️ Only persist if sharing is explicitly enabled

### Hidden Example References

**Risk**: Hidden examples may appear in traces if referenced by `reference_example_id`

**Mitigation**:
- Use `hide_inputs`/`hide_outputs` at Client level
- Post-process exported traces to redact hidden example data
- Do NOT persist hidden example content in local mirror

---

## 12. Identifier Resolution in Meta Harness

### Lookup Cache

**Recommendation**: Maintain a lookup cache mapping names to IDs for frequently accessed entities

**Cache Invalidation**: Refresh cache when:
- New datasets/experiments are created
- Entity names are changed
- Cache age exceeds TTL (e.g., 1 hour)

### Fallback Pattern

```python
def resolve_dataset_id(client, identifier: str) -> UUID:
    """Resolve dataset identifier (name or ID) to UUID."""
    try:
        # Try parsing as UUID
        return UUID(identifier)
    except ValueError:
        # Treat as name
        dataset = client.read_dataset(dataset_name=identifier)
        return dataset.id
```

---

## 13. Bulk Operations and Identifiers

### Batch Operations

**Supported**:
- `create_examples()`: Batch create with optional deterministic IDs
- `list_runs()`: Batch fetch with `run_ids` filter
- `list_feedback()`: Batch fetch with `run_ids` filter

**Identifier Handling**:
- Batch operations return arrays of entities with their IDs
- Persist returned IDs for future reference

### Pagination and Identifiers

**SDK**: Automatic pagination via iterators
**CLI**: Explicit `--limit` parameter

**Identifier Collection**:
- Collect all IDs from paginated results
- Persist for subsequent operations (e.g., feedback creation, export)

---

## 14. Export and Identifiers

### Export Format Identifiers

**Dataset export (JSON)**: Includes `id` and `dataset_id` fields
**Trace export (JSONL)**: Includes `id`, `trace_id`, `session_id`, `parent_run_id` fields
**Run export (JSONL)**: Includes `id`, `trace_id`, `session_id` fields

**Preservation**: All identifiers are preserved in exports

### Mirror Reconstruction

**Requirement**: When reconstructing local mirror from exports, preserve identifier relationships

**Pattern**:
```python
# Reconstruct trace tree from exported JSONL
runs_by_id = {run["id"]: run for run in exported_runs}
for run in exported_runs:
    if run["parent_run_id"]:
        parent = runs_by_id[run["parent_run_id"]]
        parent.setdefault("child_runs", []).append(run)
```

---

## 15. Source Citations

All identifier and metadata field definitions verified against LangSmith SDK source:

**Key Files**:
- `client.py`: SDK client methods and parameters
- `schemas.py`: Pydantic schema definitions
- `anonymizer.py`: Privacy utilities

**Method Citations**:
- `create_dataset()`: client.py:4828-4899
- `create_example()`: client.py:6241-6320
- `create_run()`: client.py:2039-2150
- `create_feedback()`: client.py:7193-7220
- `evaluate()`: client.py:9213-9234
- `list_datasets()`: client.py:5075-5126
- `list_examples()`: client.py:6384-6460
- `list_runs()`: client.py:3678-3800
- `list_feedback()`: client.py:7518-7559
