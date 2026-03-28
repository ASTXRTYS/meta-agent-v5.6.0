"""PM/Orchestrator Agent — Live Validation Harness.

Runs real traces against the orchestrator agent with actual LLM calls.
Validates INTAKE conversation, tool usage, state mutations, HITL interrupts,
dynamic prompt recomposition, and stage transitions.

Results are logged to LangSmith project: meta-agent-pm-validation
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

# Environment setup
# API keys must be set via environment variables or .env file
# os.environ.setdefault("ANTHROPIC_API_KEY", "...")
# os.environ.setdefault("LANGSMITH_API_KEY", "...")
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "meta-agent-pm-validation")
os.environ.setdefault("META_AGENT_MODEL", "anthropic:claude-sonnet-4-5-20250514")

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command

from meta_agent.graph import create_graph
from meta_agent.state import WorkflowStage


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.details = ""
        self.error = ""
        self.duration = 0.0
        self.state_snapshot = {}

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name} ({self.duration:.1f}s) — {self.details or self.error}"


def extract_ai_text(state):
    """Get the last AI message text from state."""
    msgs = state.get("messages", [])
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            return str(m.content) if m.content else ""
        if isinstance(m, dict) and m.get("role") == "assistant":
            return m.get("content", "")
    return ""


def extract_tool_calls(state):
    """Get tool calls from the last AI message."""
    msgs = state.get("messages", [])
    for m in reversed(msgs):
        if isinstance(m, AIMessage) and m.tool_calls:
            return m.tool_calls
    return []


def count_messages_by_type(state):
    """Count messages by type."""
    counts = {"human": 0, "ai": 0, "tool": 0, "system": 0, "other": 0}
    for m in state.get("messages", []):
        if isinstance(m, HumanMessage):
            counts["human"] += 1
        elif isinstance(m, AIMessage):
            counts["ai"] += 1
        elif isinstance(m, ToolMessage):
            counts["tool"] += 1
        elif isinstance(m, dict):
            role = m.get("role", "other")
            counts[role] = counts.get(role, 0) + 1
        else:
            counts["other"] += 1
    return counts


# ---------------------------------------------------------------------------
# Test 1: Basic INTAKE — Can the agent respond to a product idea?
# ---------------------------------------------------------------------------

def test_intake_conversation(graph, config):
    """Send a product idea and verify the agent enters PM mode."""
    result = TestResult("INTAKE: Basic PM Conversation")
    start = time.time()

    try:
        state = graph.invoke(
            {"messages": [HumanMessage(content=(
                "I want to build a CLI tool that helps developers manage their "
                ".env files across multiple projects. It should support encryption, "
                "syncing between team members, and have a simple 'env push' / 'env pull' "
                "workflow similar to git."
            ))]},
            config=config,
            # Use recursion_limit to prevent runaway
        )

        result.duration = time.time() - start
        result.state_snapshot = {
            "current_stage": state.get("current_stage"),
            "message_counts": count_messages_by_type(state),
            "decision_log_count": len(state.get("decision_log", [])),
            "assumption_log_count": len(state.get("assumption_log", [])),
        }

        ai_text = extract_ai_text(state)

        # Checks
        checks = []

        # 1. Agent responded with text
        if ai_text and len(ai_text) > 50:
            checks.append("agent_responded")
        else:
            result.error = f"Agent response too short or empty: {len(ai_text)} chars"
            result.passed = False
            return result

        # 2. Agent is in INTAKE stage
        if state.get("current_stage") == "INTAKE":
            checks.append("correct_stage")

        # 3. Agent asks clarifying questions (PM behavior)
        question_indicators = ["?", "could you", "what", "how", "which", "would you",
                               "clarify", "tell me", "can you", "requirements",
                               "do you", "are there"]
        ai_lower = ai_text.lower()
        if any(q in ai_lower for q in question_indicators):
            checks.append("asks_clarifying_questions")

        # 4. Todos channel exists
        if "todos" in state:
            checks.append("todos_channel_present")

        result.passed = len(checks) >= 3
        result.details = f"Checks passed: {checks}. AI response: {len(ai_text)} chars"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 2: Multi-turn INTAKE — Does the agent maintain context?
# ---------------------------------------------------------------------------

def test_multi_turn_intake(graph, config):
    """Multiple turns of conversation, verify context is maintained."""
    result = TestResult("INTAKE: Multi-Turn Context Maintenance")
    start = time.time()

    try:
        # Turn 1: Initial idea
        state1 = graph.invoke(
            {"messages": [HumanMessage(content=(
                "I want to build a Slack bot that monitors our CI/CD pipeline "
                "and posts summaries to relevant channels when builds fail."
            ))]},
            config=config,
        )

        # Turn 2: Answer a clarifying question
        state2 = graph.invoke(
            {"messages": [HumanMessage(content=(
                "We use GitHub Actions for CI/CD, and we want notifications in "
                "#engineering and #devops channels. The bot should tag the PR author "
                "when a build fails."
            ))]},
            config=config,
        )

        result.duration = time.time() - start

        ai_text1 = extract_ai_text(state1)
        ai_text2 = extract_ai_text(state2)

        # Multi-turn state should accumulate messages
        msg_counts = count_messages_by_type(state2)
        result.state_snapshot = {
            "current_stage": state2.get("current_stage"),
            "message_counts": msg_counts,
            "total_messages": sum(msg_counts.values()),
        }

        checks = []

        # 1. Both turns produced responses
        if len(ai_text1) > 20 and len(ai_text2) > 20:
            checks.append("both_turns_responded")

        # 2. Message accumulation (should have at least 2 human + 2 AI)
        if msg_counts["human"] >= 2 and msg_counts["ai"] >= 2:
            checks.append("messages_accumulated")

        # 3. Second response references context from first (GitHub Actions, Slack, etc.)
        context_refs = ["github", "slack", "ci", "cd", "pipeline", "channel", "bot", "build"]
        if any(ref in ai_text2.lower() for ref in context_refs):
            checks.append("context_maintained")

        # 4. Stage is still INTAKE
        if state2.get("current_stage") == "INTAKE":
            checks.append("stage_stable")

        result.passed = len(checks) >= 3
        result.details = f"Checks: {checks}. Turn1: {len(ai_text1)}c, Turn2: {len(ai_text2)}c, Messages: {msg_counts}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 3: Tool Usage — Does the agent use record_decision and write_file?
# ---------------------------------------------------------------------------

def test_tool_usage(graph, config):
    """Provide enough info that the agent should use tools (record decisions, write PRD)."""
    result = TestResult("INTAKE: Tool Usage (record_decision, write_file)")
    start = time.time()

    try:
        # Give a comprehensive enough description that the agent should start recording decisions
        state = graph.invoke(
            {"messages": [HumanMessage(content=(
                "Build a simple TODO CLI app in Python. Requirements: "
                "1) Add/remove/list tasks stored in a local JSON file. "
                "2) Each task has a title, status (pending/done), and created_at timestamp. "
                "3) CLI uses argparse with subcommands: add, remove, list, done. "
                "4) No external dependencies beyond the Python standard library. "
                "That's the full scope — please start drafting the PRD."
            ))]},
            config=config,
        )

        result.duration = time.time() - start

        # Check what tools were actually used
        tool_messages = [m for m in state.get("messages", []) if isinstance(m, ToolMessage)]
        tool_names_used = set()
        for tm in tool_messages:
            if hasattr(tm, 'name') and tm.name:
                tool_names_used.add(tm.name)
            # Also check content for tool action
            try:
                content = json.loads(tm.content)
                if "action" in content:
                    tool_names_used.add(content["action"])
            except (json.JSONDecodeError, TypeError):
                pass

        result.state_snapshot = {
            "current_stage": state.get("current_stage"),
            "tools_used": list(tool_names_used),
            "tool_message_count": len(tool_messages),
            "decision_log": len(state.get("decision_log", [])),
            "artifacts_written": state.get("artifacts_written", []),
            "todos": state.get("todos", []),
        }

        ai_text = extract_ai_text(state)
        checks = []

        # 1. Agent used at least one tool
        if tool_names_used:
            checks.append(f"tools_used:{list(tool_names_used)}")

        # 2. Agent used write_file or talked about writing the PRD
        if "write_file" in tool_names_used or "prd" in ai_text.lower():
            checks.append("prd_related_activity")

        # 3. Decision log has entries
        if state.get("decision_log"):
            checks.append("decisions_recorded")

        # 4. Agent responded substantively
        if len(ai_text) > 100:
            checks.append("substantive_response")

        # 5. Todos were written
        if state.get("todos"):
            checks.append("todos_created")

        result.passed = len(checks) >= 2
        result.details = f"Checks: {checks}. Tools: {tool_names_used}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 4: Dynamic Prompt Recomposition
# ---------------------------------------------------------------------------

def test_dynamic_prompt(graph, config):
    """Verify that prompts change based on stage."""
    result = TestResult("Prompt: Stage-Aware Recomposition")
    start = time.time()

    try:
        from meta_agent.prompts.orchestrator import construct_orchestrator_prompt

        intake_prompt = construct_orchestrator_prompt("INTAKE", ".", "test")
        prd_review_prompt = construct_orchestrator_prompt("PRD_REVIEW", ".", "test")
        research_prompt = construct_orchestrator_prompt("RESEARCH", ".", "test")
        execution_prompt = construct_orchestrator_prompt("EXECUTION", ".", "test")

        result.duration = time.time() - start

        checks = []

        # 1. All prompts are non-empty
        if all(len(p) > 100 for p in [intake_prompt, prd_review_prompt, research_prompt, execution_prompt]):
            checks.append("all_prompts_non_empty")

        # 2. Prompts differ between stages
        if intake_prompt != prd_review_prompt != research_prompt:
            checks.append("prompts_differ_by_stage")

        # 3. INTAKE has scoring strategy section
        if "scoring" in intake_prompt.lower() or "binary" in intake_prompt.lower():
            checks.append("intake_has_scoring_strategy")

        # 4. INTAKE has eval approval protocol
        if "eval" in intake_prompt.lower():
            checks.append("intake_has_eval_content")

        # 5. RESEARCH has delegation section
        if "delegat" in research_prompt.lower() or "subagent" in research_prompt.lower():
            checks.append("research_has_delegation")

        # 6. PRD_REVIEW has eval approval
        if "eval" in prd_review_prompt.lower() and "approv" in prd_review_prompt.lower():
            checks.append("prd_review_has_eval_approval")

        result.state_snapshot = {
            "intake_length": len(intake_prompt),
            "prd_review_length": len(prd_review_prompt),
            "research_length": len(research_prompt),
            "execution_length": len(execution_prompt),
        }

        result.passed = len(checks) >= 4
        result.details = f"Checks: {checks}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 5: State Mutation Verification
# ---------------------------------------------------------------------------

def test_state_mutations(graph, config):
    """Verify that state mutations work correctly via Command pattern."""
    result = TestResult("State: Mutation via Command Pattern")
    start = time.time()

    try:
        from meta_agent.tools import (
            transition_stage_tool,
            record_decision_tool,
            record_assumption_tool,
            toggle_participation_tool,
        )
        from meta_agent.state import DecisionEntry, AssumptionEntry

        checks = []

        # 1. Test record_decision_tool returns Command
        decision_cmd = record_decision_tool.invoke({
            "decision": "Use argparse for CLI",
            "rationale": "Standard library, no deps",
            "alternatives": "click, typer",
            "tool_call_id": "test-001",
        })
        if hasattr(decision_cmd, 'update') and "decision_log" in decision_cmd.update:
            checks.append("record_decision_returns_command")
            entries = decision_cmd.update["decision_log"]
            if len(entries) == 1 and hasattr(entries[0], 'decision'):
                checks.append("decision_entry_valid")

        # 2. Test record_assumption_tool returns Command
        assumption_cmd = record_assumption_tool.invoke({
            "assumption": "Users have Python 3.11+",
            "context": "PRD specifies Python only",
            "tool_call_id": "test-002",
        })
        if hasattr(assumption_cmd, 'update') and "assumption_log" in assumption_cmd.update:
            checks.append("record_assumption_returns_command")

        # 3. Test toggle_participation returns Command
        toggle_cmd = toggle_participation_tool.invoke({
            "enabled": True,
            "tool_call_id": "test-003",
        })
        if hasattr(toggle_cmd, 'update') and toggle_cmd.update.get("active_participation_mode") is True:
            checks.append("toggle_participation_works")

        # 4. Test transition_stage_tool with valid stage
        transition_cmd = transition_stage_tool.invoke({
            "target_stage": "PRD_REVIEW",
            "reason": "PRD drafted",
            "tool_call_id": "test-004",
        })
        if hasattr(transition_cmd, 'update') and transition_cmd.update.get("current_stage") == "PRD_REVIEW":
            checks.append("transition_stage_works")

        # 5. Test transition_stage_tool with invalid stage
        invalid_cmd = transition_stage_tool.invoke({
            "target_stage": "INVALID_STAGE",
            "reason": "test",
            "tool_call_id": "test-005",
        })
        if hasattr(invalid_cmd, 'update'):
            msgs = invalid_cmd.update.get("messages", [])
            if msgs and "error" in str(msgs[0].content):
                checks.append("invalid_transition_returns_error")

        result.duration = time.time() - start
        result.passed = len(checks) >= 4
        result.details = f"Checks: {checks}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 6: HITL Interrupt Flow
# ---------------------------------------------------------------------------

def test_hitl_interrupt(graph, config):
    """Verify that request_approval triggers a real interrupt that pauses execution."""
    result = TestResult("HITL: Interrupt and Resume Flow")
    start = time.time()

    try:
        # Ask the agent to approve something — this should trigger the interrupt
        # We'll use a direct tool invocation approach to test the interrupt mechanism
        from meta_agent.tools import request_approval_tool
        from langgraph.types import interrupt

        # Create a temp file to approve
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test PRD\n\nThis is a test artifact.")
            temp_path = f.name

        try:
            # The request_approval_tool calls interrupt() which should raise
            # an interrupt exception — this is expected behavior
            try:
                approval_result = request_approval_tool.invoke({
                    "artifact_path": temp_path,
                    "summary": "Test PRD for validation",
                    "tool_call_id": "test-hitl-001",
                })
                # If we get here without error, the interrupt was handled
                result.details = "request_approval_tool completed (interrupt may have been caught)"
                checks = ["tool_callable"]
            except Exception as e:
                if "interrupt" in str(type(e).__name__).lower() or "interrupt" in str(e).lower():
                    checks = ["interrupt_raised_correctly"]
                    result.details = f"Interrupt raised as expected: {type(e).__name__}"
                else:
                    checks = []
                    result.error = f"Unexpected error: {type(e).__name__}: {e}"
        finally:
            os.unlink(temp_path)

        # Also verify the graph itself handles interrupts by checking
        # the compiled graph has the HITL middleware node
        has_hitl_node = "HumanInTheLoopMiddleware.after_model" in graph.nodes
        if has_hitl_node:
            checks.append("hitl_middleware_in_graph")

        # Check interrupt_on config
        from meta_agent.tools.registry import HITL_GATED_TOOLS
        if len(HITL_GATED_TOOLS) > 0:
            checks.append("hitl_tools_configured")

        result.duration = time.time() - start
        result.passed = len(checks) >= 2
        if not result.details:
            result.details = f"Checks: {checks}"
        else:
            result.details += f" | Checks: {checks}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Test 7: Full PRD Drafting Flow (the big one)
# ---------------------------------------------------------------------------

def test_full_prd_flow(graph, config):
    """End-to-end: provide a complete product idea, verify PRD gets drafted."""
    result = TestResult("E2E: Full PRD Drafting Flow")
    start = time.time()

    try:
        # Provide a very complete product description to encourage PRD writing
        state = graph.invoke(
            {"messages": [HumanMessage(content=(
                "I need you to draft a PRD for the following product:\n\n"
                "Product: EnvGuard — a CLI tool for managing .env files\n\n"
                "Summary: A command-line tool that helps development teams "
                "securely manage environment variables across projects.\n\n"
                "Core features:\n"
                "1. `envguard init` — Initialize a project, creating .envguard/ directory\n"
                "2. `envguard set KEY=VALUE` — Set an env var (encrypted at rest)\n"
                "3. `envguard get KEY` — Retrieve a value\n"
                "4. `envguard push` — Push encrypted env to shared storage\n"
                "5. `envguard pull` — Pull latest env from shared storage\n"
                "6. `envguard diff` — Show differences between local and remote\n\n"
                "Constraints:\n"
                "- Python 3.11+, no external dependencies beyond cryptography and click\n"
                "- Encryption: AES-256-GCM via the cryptography library\n"
                "- Storage: Local filesystem + optional S3 backend\n"
                "- Must work on macOS, Linux, Windows\n\n"
                "Target users: Small development teams (2-10 people)\n\n"
                "Please go ahead and draft the full PRD now. Write it to the "
                "workspace using write_file."
            ))]},
            config=config,
        )

        result.duration = time.time() - start

        ai_text = extract_ai_text(state)
        tool_messages = [m for m in state.get("messages", [])
                        if isinstance(m, ToolMessage)]
        tool_names = set()
        for tm in tool_messages:
            if hasattr(tm, 'name') and tm.name:
                tool_names.add(tm.name)
            try:
                c = json.loads(tm.content) if isinstance(tm.content, str) else {}
                if "action" in c:
                    tool_names.add(c["action"])
            except:
                pass

        result.state_snapshot = {
            "current_stage": state.get("current_stage"),
            "tools_used": list(tool_names),
            "tool_messages": len(tool_messages),
            "decision_log": len(state.get("decision_log", [])),
            "artifacts_written": state.get("artifacts_written", []),
            "todos": [t.get("content", str(t)) if isinstance(t, dict) else str(t)
                     for t in (state.get("todos") or [])],
            "ai_response_length": len(ai_text),
            "message_counts": count_messages_by_type(state),
        }

        checks = []

        # 1. Agent responded
        if len(ai_text) > 50:
            checks.append("agent_responded")

        # 2. Agent used write_file to create a PRD
        if "write_file" in tool_names:
            checks.append("used_write_file")

        # 3. Agent used record_decision or other PM tools
        pm_tools = {"record_decision_tool", "record_assumption_tool",
                    "record_decision", "record_assumption",
                    "write_todos", "transition_stage_tool", "transition_stage",
                    "propose_evals_tool", "propose_evals"}
        used_pm_tools = tool_names & pm_tools
        if used_pm_tools:
            checks.append(f"pm_tools_used:{list(used_pm_tools)}")

        # 4. PRD content appears in response or was written to file
        prd_indicators = ["product summary", "goals", "requirements",
                         "constraints", "acceptance criteria", "non-goals",
                         "functional requirement", "user workflow"]
        if any(ind in ai_text.lower() for ind in prd_indicators):
            checks.append("prd_content_in_response")

        # 5. Check if PRD was written via write_file
        for tm in tool_messages:
            try:
                c = json.loads(tm.content) if isinstance(tm.content, str) else {}
                if c.get("name") == "write_file" or "write_file" in str(tm.name or ""):
                    if "prd" in str(c).lower() or "artifact" in str(c).lower():
                        checks.append("prd_file_written")
            except:
                pass

        # 6. Todos were created
        if state.get("todos"):
            checks.append("todos_created")

        result.passed = len(checks) >= 3
        result.details = f"Checks: {checks}"

    except Exception as e:
        result.duration = time.time() - start
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all validation tests and produce a report."""
    print("=" * 70)
    print("META-AGENT PM/ORCHESTRATOR — LIVE VALIDATION")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Model: {os.environ.get('META_AGENT_MODEL')}")
    print(f"LangSmith Project: {os.environ.get('LANGSMITH_PROJECT')}")
    print("=" * 70)

    # Create the graph once
    print("\n[SETUP] Creating orchestrator graph...")
    graph = create_graph(
        project_dir="./workspace/projects/pm-validation",
        project_id="pm-validation",
    )
    print(f"[SETUP] Graph created: {type(graph).__name__}")
    print(f"[SETUP] Nodes: {list(graph.nodes.keys())}")

    # Ensure workspace directory exists
    os.makedirs("./workspace/projects/pm-validation/artifacts/intake", exist_ok=True)

    results = []

    # --- Non-LLM tests first (fast) ---
    print("\n" + "-" * 50)
    print("PHASE 1: Unit-Level Validation (no LLM calls)")
    print("-" * 50)

    # Test 4: Dynamic prompts
    print("\n[TEST] Dynamic Prompt Recomposition...")
    r = test_dynamic_prompt(graph, {})
    results.append(r)
    print(f"  {r}")

    # Test 5: State mutations
    print("\n[TEST] State Mutations via Command Pattern...")
    r = test_state_mutations(graph, {})
    results.append(r)
    print(f"  {r}")

    # Test 6: HITL interrupt mechanism
    print("\n[TEST] HITL Interrupt Flow...")
    r = test_hitl_interrupt(graph, {"configurable": {"thread_id": "hitl-test-001"}})
    results.append(r)
    print(f"  {r}")

    # --- LLM tests (real API calls) ---
    print("\n" + "-" * 50)
    print("PHASE 2: Live Agent Traces (real LLM calls)")
    print("-" * 50)

    # Test 1: Basic INTAKE
    print("\n[TEST] Basic INTAKE Conversation...")
    config1 = {"configurable": {"thread_id": "pm-val-intake-001"}}
    r = test_intake_conversation(graph, config1)
    results.append(r)
    print(f"  {r}")

    # Test 2: Multi-turn
    print("\n[TEST] Multi-Turn Context Maintenance...")
    config2 = {"configurable": {"thread_id": "pm-val-multiturn-001"}}
    r = test_multi_turn_intake(graph, config2)
    results.append(r)
    print(f"  {r}")

    # Test 3: Tool usage
    print("\n[TEST] Tool Usage (record_decision, write_file)...")
    config3 = {"configurable": {"thread_id": "pm-val-tools-001"}}
    r = test_tool_usage(graph, config3)
    results.append(r)
    print(f"  {r}")

    # Test 7: Full PRD flow (the big one)
    print("\n[TEST] Full PRD Drafting Flow (E2E)...")
    config7 = {"configurable": {"thread_id": "pm-val-prd-e2e-001"}}
    r = test_full_prd_flow(graph, config7)
    results.append(r)
    print(f"  {r}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for i, r in enumerate(results, 1):
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {i}. [{status}] {r.name} ({r.duration:.1f}s)")
        if r.state_snapshot:
            for k, v in r.state_snapshot.items():
                print(f"       {k}: {v}")
        if r.error:
            print(f"       ERROR: {r.error[:200]}")

    print(f"\n  TOTAL: {passed}/{total} passed")
    print(f"  Traces logged to LangSmith project: {os.environ.get('LANGSMITH_PROJECT')}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    results = run_all_tests()
    # Write results to a JSON file for later analysis
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": os.environ.get("META_AGENT_MODEL"),
        "results": [
            {
                "name": r.name,
                "passed": r.passed,
                "details": r.details,
                "error": r.error,
                "duration": r.duration,
                "state_snapshot": r.state_snapshot,
            }
            for r in results
        ],
        "summary": {
            "passed": sum(1 for r in results if r.passed),
            "total": len(results),
        }
    }
    with open("pm_validation_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults written to pm_validation_results.json")
