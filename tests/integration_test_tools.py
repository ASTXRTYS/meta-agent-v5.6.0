"""Integration test: verify @tool wrappers mutate state via Command pattern.

Creates a real graph, asks the agent to record a decision, and verifies
that decision_log gets updated in state.
"""
from __future__ import annotations

import os
import sys
import json
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

from meta_agent.graph import create_graph
from meta_agent.state import create_initial_state


def main():
    results = {"steps": [], "success": False, "error": None}

    # Create graph
    try:
        graph = create_graph(project_id="tool-test")
        results["steps"].append({"step": "create_graph", "status": "ok"})
        print("[OK] Graph created")
    except Exception as e:
        results["steps"].append({"step": "create_graph", "status": "error", "error": str(e)})
        print(f"[FAIL] {e}")
        _write(results)
        return

    # Test: Ask the agent to record a decision — verify it uses Command to update state
    config = {"configurable": {"thread_id": "tool-test-001"}}
    try:
        initial_state = create_initial_state("tool-test")
        initial_state["messages"] = [
            {"role": "user", "content": (
                "Please record a decision: 'Use PostgreSQL for the database' "
                "with rationale 'Better JSON support and full-text search'. "
                "Use the record_decision_tool to do this."
            )}
        ]
        response = graph.invoke(initial_state, config=config)

        # Check if decision_log was updated in state
        state = graph.get_state(config)
        decision_log = state.values.get("decision_log", [])

        results["steps"].append({
            "step": "record_decision_via_command",
            "status": "ok" if len(decision_log) > 0 else "no_decisions",
            "decision_count": len(decision_log),
            "decision_log_preview": str(decision_log[:2])[:500],
            "message_count": len(response.get("messages", [])),
        })

        if len(decision_log) > 0:
            print(f"[OK] Decision log updated: {len(decision_log)} entries")
            results["success"] = True
        else:
            print("[WARN] Decision log empty — agent may not have used the tool")

        # Check current_stage
        current_stage = state.values.get("current_stage", "unknown")
        results["steps"].append({
            "step": "verify_state",
            "status": "ok",
            "current_stage": current_stage,
        })
        print(f"[OK] Current stage: {current_stage}")

    except Exception as e:
        tb = traceback.format_exc()
        results["steps"].append({"step": "invoke", "status": "error", "error": str(e), "traceback": tb})
        results["error"] = str(e)
        print(f"[FAIL] {e}")
        print(tb)

    _write(results)


def _write(results):
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "tool_integration_test_results.md")
    lines = [
        "# Tool Integration Test Results\n",
        f"**Overall**: {'PASS' if results['success'] else 'FAIL'}\n",
    ]
    if results.get("error"):
        lines.append(f"**Error**: {results['error']}\n")
    lines.append("\n## Steps\n")
    for step in results["steps"]:
        lines.append(f"### {step['step']}: {step['status'].upper()}\n")
        for k, v in step.items():
            if k not in ("step", "status"):
                lines.append(f"- **{k}**: {v}\n")
        lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"\nResults written to {path}")


if __name__ == "__main__":
    main()
