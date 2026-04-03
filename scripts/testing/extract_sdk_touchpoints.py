#!/usr/bin/env python3
"""Extract SDK touchpoints from meta_agent/ source code using the ast module.

Scans all Python files under meta_agent/ for import statements matching:
- deepagents.*
- langgraph.*
- langchain.*
- langchain_core.*

Outputs discovered touchpoints as JSON for comparison against sdk_touchpoints.yaml.

Usage:
    python scripts/testing/extract_sdk_touchpoints.py
    python scripts/testing/extract_sdk_touchpoints.py --output touchpoints.json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
META_AGENT = REPO_ROOT / "meta_agent"

# SDK module prefixes to track
SDK_PREFIXES = ("deepagents", "langgraph", "langchain", "langchain_core")


def extract_imports_from_file(filepath: Path) -> list[dict]:
    """Parse a Python file and extract SDK import statements."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (OSError, SyntaxError):
        return []

    imports: list[dict] = []
    rel_path = str(filepath.relative_to(REPO_ROOT))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(SDK_PREFIXES):
                    imports.append({
                        "module": alias.name,
                        "symbol": alias.asname or alias.name.split(".")[-1],
                        "import_type": "import",
                        "file": rel_path,
                        "line": node.lineno,
                    })

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not module.startswith(SDK_PREFIXES):
                continue
            for alias in node.names:
                imports.append({
                    "module": module,
                    "symbol": alias.name,
                    "alias": alias.asname,
                    "import_type": "from_import",
                    "file": rel_path,
                    "line": node.lineno,
                })

    return imports


def scan_meta_agent() -> list[dict]:
    """Scan all Python files under meta_agent/ for SDK imports."""
    all_imports: list[dict] = []

    if not META_AGENT.is_dir():
        print(f"Warning: {META_AGENT} not found", file=sys.stderr)
        return all_imports

    for py_file in sorted(META_AGENT.rglob("*.py")):
        all_imports.extend(extract_imports_from_file(py_file))

    return all_imports


def deduplicate_touchpoints(imports: list[dict]) -> list[dict]:
    """Group imports by (module, symbol) and list all files using each."""
    grouped: dict[tuple[str, str], dict] = {}

    for imp in imports:
        key = (imp["module"], imp["symbol"])
        if key not in grouped:
            grouped[key] = {
                "module": imp["module"],
                "symbol": imp["symbol"],
                "local_usages": [],
            }
        filepath = imp["file"]
        if filepath not in grouped[key]["local_usages"]:
            grouped[key]["local_usages"].append(filepath)

    return sorted(
        grouped.values(),
        key=lambda x: (x["module"], x["symbol"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    raw_imports = scan_meta_agent()
    touchpoints = deduplicate_touchpoints(raw_imports)

    result = {
        "version": 1,
        "touchpoints": touchpoints,
        "raw_import_count": len(raw_imports),
        "unique_touchpoint_count": len(touchpoints),
    }

    output = json.dumps(result, indent=2) + "\n"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(
            f"SDK touchpoints written to {args.output} "
            f"({len(touchpoints)} unique from {len(raw_imports)} imports)",
            file=sys.stderr,
        )
    else:
        print(output)


if __name__ == "__main__":
    main()
