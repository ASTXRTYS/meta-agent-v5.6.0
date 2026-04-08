#!/usr/bin/env python3
"""Extract runtime component inventory from meta_agent/ source code.

Scans the source to discover:
- Tools: LANGCHAIN_TOOLS list members
- Middleware: AgentMiddleware subclasses
- Subagents: SUBAGENT_CONFIGS keys
- Backend routes: CompositeBackend route definitions
- State fields: MetaAgentState TypedDict annotations
- Guardrails: safety module constants and functions

Outputs JSON to stdout for comparison against runtime_components.yaml.

Usage:
    python scripts/testing/extract_runtime_inventory.py
    python scripts/testing/extract_runtime_inventory.py --output inventory.json
"""

from __future__ import annotations

import ast
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
META_AGENT = REPO_ROOT / "meta_agent"


def extract_langchain_tools(source: str) -> list[str]:
    """Extract tool names from LANGCHAIN_TOOLS = [...] list."""
    match = re.search(
        r'LANGCHAIN_TOOLS\s*=\s*\[([^\]]+)\]',
        source, re.DOTALL,
    )
    if not match:
        return []
    raw = match.group(1)
    # Extract identifiers (variable names in the list)
    return [name.strip() for name in raw.split(",") if name.strip()]


def extract_subagent_configs(source: str) -> list[str]:
    """Extract subagent names from AGENT_REGISTRY dict keys."""
    registry_match = re.search(r'AGENT_REGISTRY.*?(?:=)\s*\{([^}]+)\}', source, re.DOTALL)
    if not registry_match:
        return []
    return re.findall(r'"([^"]+)"\s*:', registry_match.group(1))


def extract_state_fields(source: str) -> list[str]:
    """Extract field names from MetaAgentState TypedDict."""
    # Find the class body
    match = re.search(
        r'class MetaAgentState\(TypedDict\):.*?(?=\nclass |\ndef |\Z)',
        source, re.DOTALL,
    )
    if not match:
        return []
    body = match.group(0)
    # Match field annotations: field_name: Type
    fields = re.findall(r'^\s+(\w+)\s*:', body, re.MULTILINE)
    return fields


def extract_middleware_classes() -> list[dict]:
    """Scan middleware directory for AgentMiddleware subclasses."""
    middleware_dir = META_AGENT / "middleware"
    results = []
    if not middleware_dir.is_dir():
        return results

    for py_file in sorted(middleware_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = ""
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    if base_name in ("AgentMiddleware", "AgentState"):
                        results.append({
                            "class": node.name,
                            "file": str(py_file.relative_to(REPO_ROOT)),
                            "base": base_name,
                        })
    return results


def extract_backend_routes(source: str) -> list[str]:
    """Extract route prefixes from CompositeBackend routes={...}."""
    return re.findall(r'"(/[^"]+/)":', source)


def extract_guardrails() -> list[dict]:
    """Extract guardrail constants and functions from safety.py."""
    safety_path = META_AGENT / "safety.py"
    if not safety_path.is_file():
        return []
    source = safety_path.read_text(encoding="utf-8")
    results = []

    # Dict constants
    for name in ["RECURSION_LIMITS", "TOKEN_BUDGET_LIMITS",
                 "FILESYSTEM_RESTRICTIONS", "COMMAND_EXECUTION_GUARDRAILS"]:
        if re.search(rf'^{name}\s*[:=]', source, re.MULTILINE):
            results.append({"type": "constant", "name": name})

    # Functions
    for match in re.finditer(r'^def\s+(\w+)\(', source, re.MULTILINE):
        fname = match.group(1)
        if fname.startswith("validate_") or fname.startswith("get_"):
            results.append({"type": "function", "name": fname})

    # HITL gated tools from registry
    registry_path = META_AGENT / "tools" / "registry.py"
    if registry_path.is_file():
        reg_source = registry_path.read_text(encoding="utf-8")
        match = re.search(
            r'HITL_GATED_TOOLS[^{]*\{([^}]+)\}', reg_source, re.DOTALL
        )
        if match:
            tools = re.findall(r'"([^"]+)"', match.group(1))
            results.append({
                "type": "constant",
                "name": "HITL_GATED_TOOLS",
                "values": tools,
            })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    tools_init = (META_AGENT / "tools" / "__init__.py").read_text("utf-8")
    configs_src = (META_AGENT / "subagents" / "configs.py").read_text("utf-8")
    state_src = (META_AGENT / "state.py").read_text("utf-8")
    backend_src = (META_AGENT / "backend.py").read_text("utf-8")

    inventory = {
        "version": 1,
        "tools": extract_langchain_tools(tools_init),
        "middleware": extract_middleware_classes(),
        "subagents": extract_subagent_configs(configs_src),
        "state_fields": extract_state_fields(state_src),
        "backend_routes": extract_backend_routes(backend_src),
        "guardrails": extract_guardrails(),
    }

    output = json.dumps(inventory, indent=2) + "\n"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Inventory written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
