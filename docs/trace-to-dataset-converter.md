# Trace to Dataset Converter

Convert LangSmith traces into rich evaluation datasets for baseline testing and improvement tracking.

## Overview

The trace-to-dataset converter extracts comprehensive data from LangSmith traces and transforms it into multiple evaluation-ready dataset formats:

- **final_response** - Complete input→output pairs for end-to-end testing
- **trajectory** - Tool call sequences for execution path validation  
- **single_step** - Individual component evaluations
- **eval_metadata** - Evaluation context and performance metrics

## Usage

### Convert Trace by ID

```bash
python scripts/trace_to_datasets.py <trace-id>
```

### Convert from Exported Trace File

```bash
python scripts/trace_to_datasets.py --trace-file exports/traces/trace_<id>_<timestamp>.json
```

### Upload to LangSmith

```bash
python scripts/trace_to_datasets.py <trace-id> --upload
```

### Generate Specific Formats

```bash
python scripts/trace_to_datasets.py <trace-id> --formats final_response trajectory
```

### Custom Dataset Naming

```bash
python scripts/trace_to_datasets.py <trace-id> --prefix my-baseline-dataset
```

## Examples

### Basic Conversion
```bash
# Convert trace and save locally
python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1

# Convert and upload to LangSmith
python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1 --upload

# Convert specific formats only
python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1 --formats final_response trajectory --upload
```

### From Exported File
```bash
# First export the trace
python scripts/export_trace.py 019d404a-8275-7cb3-81a7-4bc166c13cb1

# Then convert to datasets
python scripts/trace_to_datasets.py --trace-file exports/traces/trace_019d404a-8275-7cb3-81a7-4bc166c13cb1_20260330_200208.json --upload
```

## Output Files

Datasets are saved to `exports/datasets/` by default:

- `baseline-research-final_response-YYYYMMDD_HHMMSS.json`
- `baseline-research-trajectory-YYYYMMDD_HHMMSS.json`
- `baseline-research-single_step-YYYYMMDD_HHMMSS.json`
- `baseline-research-eval_metadata-YYYYMMDD_HHMMSS.json`

## Dataset Formats

### final_response
Complete input→output pairs for end-to-end testing:
```json
{
  "inputs": {
    "query": "main query string",
    "full_input": {...}
  },
  "outputs": {
    "response": "main response string", 
    "full_output": {...}
  },
  "metadata": {
    "dataset_type": "final_response",
    "trace_id": "...",
    "phase_name": "RESEARCH",
    "has_errors": false
  }
}
```

### trajectory
Tool call sequences for execution validation:
```json
{
  "inputs": {
    "query": "main query string",
    "full_input": {...}
  },
  "outputs": {
    "expected_trajectory": ["tool1", "tool2", "tool3"],
    "detailed_trajectory": [...],
    "tool_count": 3,
    "has_errors": false
  },
  "metadata": {
    "dataset_type": "trajectory",
    "unique_tools": 2,
    "error_count": 0
  }
}
```

### single_step
Individual component evaluations:
```json
{
  "inputs": {
    "messages": [...],
    "node_name": "tool_name",
    "run_inputs": {...}
  },
  "outputs": {
    "content": "output content",
    "run_outputs": {...}
  },
  "metadata": {
    "dataset_type": "single_step",
    "run_id": "...",
    "run_type": "tool",
    "duration_seconds": 1.23,
    "has_error": false
  }
}
```

### eval_metadata
Evaluation context and performance metrics:
```json
{
  "inputs": {
    "trace_id": "...",
    "scenario_type": "live_trace",
    "phase_name": "RESEARCH"
  },
  "outputs": {
    "evaluation_metadata": {...},
    "performance_metrics": {...},
    "conversation_summary": {...},
    "tool_usage_summary": {...}
  },
  "metadata": {
    "dataset_type": "eval_metadata",
    "commit_hash": "...",
    "agent_version": "0.1.0"
  }
}
```

## Implementation Notes

- Uses the existing `export_trace.py` for trace data extraction
- Leverages LangSmith SDK for dataset upload
- Preserves full conversation context and tool call sequences
- Extracts evaluation metadata from trace headers
- Handles research agent Phase 3 workflow specifics

## Integration with Evaluation System

The generated datasets work seamlessly with the existing evaluation infrastructure:

```python
from langsmith import evaluate

# Use final_response dataset for end-to-end testing
evaluate(
    my_agent_function,
    data="baseline-research-final_response-20260330",
    evaluators=[my_evaluators]
)

# Use trajectory dataset for execution validation
evaluate(
    my_agent_function, 
    data="baseline-research-trajectory-20260330",
    evaluators=[trajectory_evaluators]
)
```

## Recent Success

Successfully converted research agent trace `019d404a-8275-7cb3-81a7-4bc166c13cb1` into:
- `baseline-research-final_response-20260330` (1 example)
- `baseline-research-trajectory-20260330` (1 example)

Both datasets are now available in LangSmith for baseline testing and improvement tracking.
