"""Integration test: verify real deepagents SDK graph works with Anthropic API.

This test creates a real graph via create_deep_agent(), sends a simple message,
and verifies a response is returned.
"""
from __future__ import annotations

import os
import sys
import traceback

# Load .env
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
except ImportError:
    pass

from meta_agent.graph import create_graph
from meta_agent.state import create_initial_state


def main():
    results = {"steps": [], "success": False, "error": None}

    # Step 1: Create graph
    try:
        graph = create_graph(project_id="integration-test")
        results["steps"].append({"step": "create_graph", "status": "ok", "type": type(graph).__name__})
        print(f"[OK] Graph created: {type(graph).__name__}")
    except Exception as e:
        results["steps"].append({"step": "create_graph", "status": "error", "error": str(e)})
        results["error"] = str(e)
        print(f"[FAIL] Graph creation failed: {e}")
        _write_results(results)
        return

    # Step 2: Verify graph has key methods
    has_invoke = hasattr(graph, "invoke")
    has_get_state = hasattr(graph, "get_state")
    has_update_state = hasattr(graph, "update_state")
    results["steps"].append({
        "step": "verify_graph_api",
        "status": "ok",
        "has_invoke": has_invoke,
        "has_get_state": has_get_state,
        "has_update_state": has_update_state,
    })
    print(f"[OK] Graph API: invoke={has_invoke}, get_state={has_get_state}, update_state={has_update_state}")

    # Step 3: Send a test message via invoke
    try:
        initial_state = create_initial_state("integration-test")
        initial_state["messages"] = [
            {"role": "user", "content": "Say 'hello integration test' in exactly those words and nothing else."}
        ]
        config = {"configurable": {"thread_id": "integration-test-001"}}
        response = graph.invoke(initial_state, config=config)

        # Extract response info
        messages = response.get("messages", [])
        last_msg = messages[-1] if messages else None
        last_content = ""
        if last_msg:
            if isinstance(last_msg, dict):
                last_content = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                last_content = last_msg.content

        results["steps"].append({
            "step": "invoke",
            "status": "ok",
            "message_count": len(messages),
            "last_message_preview": last_content[:200] if last_content else "(empty)",
        })
        results["success"] = True
        print(f"[OK] Invoke returned {len(messages)} messages")
        print(f"[OK] Last message: {last_content[:200]}")

    except Exception as e:
        tb = traceback.format_exc()
        results["steps"].append({"step": "invoke", "status": "error", "error": str(e), "traceback": tb})
        results["error"] = str(e)
        print(f"[FAIL] Invoke failed: {e}")
        print(tb)

    _write_results(results)


def _write_results(results):
    """Write results to tests/results/integration_remediation_test.md."""
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "integration_remediation_test.md")

    lines = ["# Remediation Integration Test Results\n"]
    lines.append(f"**Overall**: {'PASS' if results['success'] else 'FAIL'}\n")

    if results.get("error"):
        lines.append(f"**Error**: {results['error']}\n")

    lines.append("\n## Steps\n")
    for step in results["steps"]:
        status = step["status"].upper()
        name = step["step"]
        lines.append(f"### {name}: {status}\n")
        for k, v in step.items():
            if k not in ("step", "status"):
                lines.append(f"- **{k}**: {v}\n")
        lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
