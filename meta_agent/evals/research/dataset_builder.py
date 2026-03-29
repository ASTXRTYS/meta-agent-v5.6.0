"""Build LangSmith-compatible dataset JSON from synthetic data.

Transforms golden/bronze YAML files + calibration JSON into a single
dataset file that can be uploaded to LangSmith via CLI or SDK.

Usage:
    python -m meta_agent.evals.research.dataset_builder \
        --datasets-dir datasets \
        --output /tmp/research-agent-eval-calibration.json

    # Then upload:
    # langsmith dataset upload /tmp/research-agent-eval-calibration.json \
    #     --name "research-agent-eval-calibration"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from meta_agent.evals.research.synthetic_trace_adapter import (
    load_calibration_dataset,
)


def build_dataset(datasets_dir: str) -> list[dict]:
    """Build the full dataset from available synthetic data."""
    try:
        examples = load_calibration_dataset(datasets_dir)
    except Exception as e:
        print(f"  Warning: calibration dataset failed: {e}", file=sys.stderr)
        return []

    for example in examples:
        scenario = example["metadata"].get("scenario_type", "unknown")
        tool_calls = example["outputs"].get("trace_summary", {}).get("total_tool_calls", 0)
        print(f"  {scenario} loaded: {tool_calls} tool calls")

    return examples


def write_dataset(examples: list[dict], output_path: str) -> None:
    """Write dataset to JSON file in LangSmith upload format."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(examples, f, indent=2, default=str)
    print(f"  Written {len(examples)} examples to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LangSmith dataset from synthetic data")
    parser.add_argument("--datasets-dir", default="datasets", help="Path to datasets directory")
    parser.add_argument("--output", default="/tmp/research-agent-eval-calibration.json")
    args = parser.parse_args()

    print("Building research agent eval calibration dataset...")
    examples = build_dataset(args.datasets_dir)

    if not examples:
        print("No examples built. Check dataset paths.", file=sys.stderr)
        sys.exit(1)

    write_dataset(examples, args.output)
    print(f"\nDone. Upload with:")
    print(f'  langsmith dataset upload {args.output} --name "research-agent-eval-calibration"')


if __name__ == "__main__":
    main()
