#!/usr/bin/env python3
"""Convert LangSmith trace to rich evaluation datasets.

This script extracts comprehensive data from a LangSmith trace and converts it
into multiple evaluation dataset formats for baseline testing and improvement tracking.

Usage:
    python scripts/trace_to_datasets.py <trace-id> [options]
    python scripts/trace_to_datasets.py --trace-file <path> [options]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from meta_agent.evals.dataset_converter import TraceToDatasetConverter


def _load_env() -> None:
    """Load environment variables from repo root .env file."""
    repo_root = Path(__file__).parent.parent
    load_dotenv(repo_root / ".env")


def _validate_trace_id(client: Client, trace_id: str) -> bool:
    """Validate that trace ID exists in LangSmith.
    
    Args:
        client: LangSmith client.
        trace_id: Trace ID to validate.
        
    Returns:
        True if trace exists, False otherwise.
    """
    try:
        client.read_run(trace_id, load_child_runs=False)
        return True
    except Exception:
        return False


def _validate_trace_file(trace_file: Path) -> bool:
    """Validate that trace file exists and is valid JSON.
    
    Args:
        trace_file: Path to trace file.
        
    Returns:
        True if file is valid, False otherwise.
    """
    if not trace_file.exists():
        print(f"❌ Trace file not found: {trace_file}")
        return False
    
    try:
        import json
        with open(trace_file, 'r') as f:
            data = json.load(f)
        
        # Check for expected structure
        if "trace" not in data and "export_metadata" not in data:
            print("❌ Invalid trace file format - missing trace data")
            return False
        
        return True
    except json.JSONDecodeError:
        print("❌ Invalid JSON in trace file")
        return False
    except Exception as e:
        print(f"❌ Error reading trace file: {e}")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert LangSmith trace to evaluation datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert trace by ID
  python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1
  
  # Convert from exported trace file
  python scripts/trace_to_datasets.py --trace-file exports/traces/trace_019d404a-8275-7cb3-81a7-4bc166c13cb1_20260330_200208.json
  
  # Custom dataset naming
  python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1 --prefix my-research-baseline
  
  # Only generate specific formats
  python scripts/trace_to_datasets.py 019d404a-8275-7cb3-81a7-4bc166c13cb1 --formats final_response trajectory
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "trace_id",
        nargs="?",
        help="LangSmith trace ID to convert"
    )
    input_group.add_argument(
        "--trace-file",
        type=Path,
        help="Path to exported trace JSON file"
    )
    
    # Output options
    parser.add_argument(
        "--prefix",
        default="baseline-research",
        help="Dataset name prefix (default: baseline-research)"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["final_response", "trajectory", "single_step", "eval_metadata"],
        default=["final_response", "trajectory", "single_step", "eval_metadata"],
        help="Dataset formats to generate (default: all formats)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Local output directory for datasets (default: exports/datasets)"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload datasets to LangSmith"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Additional description for uploaded datasets"
    )
    
    args = parser.parse_args()
    
    # Load environment
    _load_env()
    
    # Check API key
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("❌ Error: LANGSMITH_API_KEY not found in environment")
        sys.exit(1)
    
    # Initialize converter
    client = Client()
    converter = TraceToDatasetConverter(client)
    
    # Load trace data
    print("🔍 Loading trace data...")
    
    if args.trace_file:
        # Load from file
        if not _validate_trace_file(args.trace_file):
            sys.exit(1)
        
        trace_data = converter.load_trace_from_file(args.trace_file)
        trace_id = trace_data.get("export_metadata", {}).get("trace_id", "unknown")
        print(f"📥 Loaded trace from file: {args.trace_file}")
    else:
        # Load from LangSmith
        trace_id = args.trace_id
        if not _validate_trace_id(client, trace_id):
            print(f"❌ Error: Trace {trace_id} not found")
            sys.exit(1)
        
        trace_data = converter.load_trace_from_langsmith(trace_id)
        print(f"📥 Loaded trace from LangSmith: {trace_id}")
    
    # Set default output directory
    if not args.output_dir:
        args.output_dir = Path("exports/datasets")
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to datasets
    print("🔄 Converting trace to datasets...")
    datasets = converter.convert_to_datasets(trace_data, args.prefix)
    
    # Filter formats if specified
    if args.formats != ["final_response", "trajectory", "single_step", "eval_metadata"]:
        datasets = {fmt: data for fmt, data in datasets.items() if fmt in args.formats}
    
    # Save datasets locally
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = []
    
    for format_name, examples in datasets.items():
        filename = f"{args.prefix}-{format_name}-{timestamp}.json"
        output_file = args.output_dir / filename
        
        import json
        with open(output_file, 'w') as f:
            json.dump(examples, f, indent=2, default=str)
        
        saved_files.append(output_file)
        print(f"💾 Saved {format_name} dataset: {output_file}")
        print(f"   Examples: {len(examples)}")
    
    # Upload to LangSmith if requested
    uploaded_names = {}
    if args.upload:
        print("📤 Uploading datasets to LangSmith...")
        
        try:
            uploaded_names = converter.upload_datasets_to_langsmith(
                datasets, args.prefix, args.description
            )
            
            for format_name, dataset_name in uploaded_names.items():
                print(f"✅ Uploaded {format_name}: {dataset_name}")
        except Exception as e:
            print(f"❌ Error uploading to LangSmith: {e}")
    
    # Print summary
    print("\n📊 Conversion Summary:")
    print(f"   Trace ID: {trace_id}")
    print(f"   Formats generated: {list(datasets.keys())}")
    print(f"   Total examples: {sum(len(examples) for examples in datasets.values())}")
    print(f"   Local files: {len(saved_files)}")
    print(f"   Uploaded datasets: {len(uploaded_names)}")
    
    if uploaded_names:
        print("\n🔗 Dataset Links:")
        project = os.getenv("LANGSMITH_PROJECT", "unknown")
        for format_name, dataset_name in uploaded_names.items():
            print(f"   {format_name}: https://smith.langchain.com/datasets/{dataset_name}?project={project}")


if __name__ == "__main__":
    main()
