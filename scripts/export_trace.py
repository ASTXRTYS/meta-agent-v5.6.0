#!/usr/bin/env python3
"""Export a LangSmith trace with full hierarchy and metadata.

Following best practices from langsmith-trace skill:
- Always specify project explicitly
- Use traces (not runs) for complete hierarchy
- Include full metadata for performance/cost analysis
- Handle errors gracefully

Usage:
    python scripts/export_trace.py <trace-id> [output-dir]
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langsmith import Client


def _load_env() -> None:
    """Load environment variables from repo root .env file."""
    repo_root = Path(__file__).parent.parent
    load_dotenv(repo_root / ".env")


def _ensure_output_dir(output_dir: Path) -> Path:
    """Ensure output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _get_trace_summary(trace: dict[str, Any]) -> dict[str, Any]:
    """Extract summary statistics from trace."""
    # Handle both single run and runs with children
    runs = []
    
    # Add root run
    if trace:
        runs.append(trace)
    
    # Add child runs if they exist
    if "child_runs" in trace and trace["child_runs"]:
        runs.extend(trace["child_runs"])
    
    # Count run types
    run_types: dict[str, int] = {}
    total_tokens = 0
    total_latency = 0.0
    error_count = 0
    
    for run in runs:
        run_type = run.get("run_type", "unknown")
        run_types[run_type] = run_types.get(run_type, 0) + 1
        
        # Token usage
        usage = run.get("usage", {})
        total_tokens += usage.get("total_tokens", 0)
        
        # Latency
        latency = run.get("latency", 0.0)
        if isinstance(latency, (int, float)):
            total_latency += latency
        
        # Errors
        if run.get("error"):
            error_count += 1
    
    return {
        "total_runs": len(runs),
        "run_types": run_types,
        "total_tokens": total_tokens,
        "total_latency_seconds": total_latency,
        "error_count": error_count,
        "has_errors": error_count > 0,
    }


def export_trace(trace_id: str, output_dir: str | None = None) -> None:
    """Export a single trace with full hierarchy to JSON."""
    
    # Load environment
    _load_env()
    
    # Get configuration
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT", "meta-agent")
    
    if not api_key:
        print("❌ Error: LANGSMITH_API_KEY not found in environment")
        sys.exit(1)
    
    # Set default output directory
    if not output_dir:
        output_dir = "exports/traces"
    
    output_path = Path(output_dir)
    output_path = _ensure_output_dir(output_path)
    
    print(f"🔍 Connecting to LangSmith project: {project}")
    print(f"📥 Exporting trace: {trace_id}")
    
    # Initialize client
    client = Client(api_key=api_key)
    
    try:
        # Get the trace with full hierarchy (load all child runs)
        trace = client.read_run(trace_id, load_child_runs=True)
        
        if not trace:
            print(f"❌ Error: Trace {trace_id} not found")
            sys.exit(1)
        
        # Convert to dict for JSON serialization
        trace_dict = trace.model_dump() if hasattr(trace, 'model_dump') else (trace.dict() if hasattr(trace, 'dict') else trace)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{trace_id}_{timestamp}.json"
        output_file = output_path / filename
        
        # Prepare export data with full context
        export_data = {
            "export_metadata": {
                "trace_id": trace_id,
                "project": project,
                "exported_at": datetime.now().isoformat(),
                "exported_by": "meta-agent/scripts/export_trace.py",
            },
            "trace_summary": _get_trace_summary(trace_dict),
            "trace": trace_dict,  # Full trace with hierarchy
        }
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        # Print summary
        summary = export_data["trace_summary"]
        print(f"✅ Trace exported successfully to: {output_file.absolute()}")
        print(f"📊 Trace Summary:")
        print(f"   - Total runs: {summary['total_runs']}")
        print(f"   - Total tokens: {summary['total_tokens']:,}")
        print(f"   - Total latency: {summary['total_latency_seconds']:.2f}s")
        print(f"   - Errors: {summary['error_count']}")
        print(f"   - Run types:")
        for run_type, count in summary["run_types"].items():
            print(f"     • {run_type}: {count}")
        
        # Show root run info if available
        if "child_runs" in trace_dict and trace_dict["child_runs"]:
            root_run = trace_dict
            print(f"🎯 Root run: {root_run.get('name', 'unnamed')}")
            print(f"   Started: {root_run.get('start_time', 'unknown')}")
        elif trace_dict:
            root_run = trace_dict
            print(f"🎯 Root run: {root_run.get('name', 'unnamed')}")
            print(f"   Started: {root_run.get('start_time', 'unknown')}")
            
    except Exception as e:
        print(f"❌ Error exporting trace: {e}")
        sys.exit(1)


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/export_trace.py <trace-id> [output-dir]")
        print("\nExamples:")
        print("  python scripts/export_trace.py 019d404a-8275-7cb3-81a7-4bc166c13cb1")
        print("  python scripts/export_trace.py 019d404a-8275-7cb3-81a7-4bc166c13cb1 /tmp/exports")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_trace(trace_id, output_dir)


if __name__ == "__main__":
    main()
