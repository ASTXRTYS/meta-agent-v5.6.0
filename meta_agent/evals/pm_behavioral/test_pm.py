"""PM behavioral evals: PM-001 through PM-008.

Spec References: Sections 2.3.2, 15.11

These evals verify the orchestrator's PM behavior during INTAKE:
- PM-001: Asks clarifying questions before writing PRD
- PM-002: Does not delegate PRD writing
- PM-003: Proposes evals with scoring strategy rationale
- PM-004: Pushes back when user says skip evals
- PM-005: Confirms approval explicitly before stage transition
- PM-006: No premature PRD writing
- PM-007: Evals proposed during INTAKE
- PM-008: Requirement elicitation quality (Likert)
"""

from __future__ import annotations

from typing import Any


def eval_pm_001_asks_clarifying_questions(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-001: Orchestrator asks clarifying questions before writing PRD.

    Given a vague initial user message, the orchestrator should ask
    clarifying questions — NOT immediately write a PRD.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    Input: Trace from INTAKE with initial user message "Build me an agent"
    """
    first_response = trace.get("orchestrator_messages", [{}])[0].get("content", "")
    has_question = "?" in first_response
    has_prd = "write_file" in str(trace.get("tool_calls", [])[:3])
    return {
        "pass": has_question and not has_prd,
        "reason": (
            "Correctly asked questions before writing" if has_question and not has_prd
            else "Failed: " + ("No questions asked" if not has_question else "PRD written prematurely")
        ),
    }


def eval_pm_002_does_not_delegate_prd(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-002: Orchestrator does NOT delegate PRD writing to a subagent.

    The orchestrator must write the PRD itself. It must NOT spawn or
    delegate to a subagent for PRD authoring.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    tool_calls = trace.get("tool_calls", [])
    for tc in tool_calls:
        if tc.get("name") == "task":
            desc = tc.get("args", {}).get("description", "").lower()
            if "prd" in desc and ("write" in desc or "create" in desc or "draft" in desc):
                return {"pass": False, "reason": f"Delegated PRD writing: {desc}"}
    return {"pass": True, "reason": "PRD authored directly by orchestrator"}


def eval_pm_003_proposes_evals_with_rationale(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-003: Orchestrator proposes evals with scoring strategy rationale.

    When proposing evals, the orchestrator must explain WHY it chose
    each scoring strategy (binary vs. Likert) using <pm_reasoning> blocks.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    messages = trace.get("orchestrator_messages", [])
    found_eval_proposal = False
    found_reasoning = False
    for msg in messages:
        content = msg.get("content", "")
        if "EVAL-" in content or ("eval" in content.lower() and ("binary" in content.lower() or "likert" in content.lower())):
            found_eval_proposal = True
        if "<pm_reasoning>" in content:
            found_reasoning = True
    return {
        "pass": found_eval_proposal and found_reasoning,
        "reason": (
            "Evals proposed with reasoning" if found_eval_proposal and found_reasoning
            else "Missing: " + ("eval proposal" if not found_eval_proposal else "<pm_reasoning> block")
        ),
    }


def eval_pm_004_pushes_back_on_no_evals(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-004: Orchestrator pushes back when user says "skip evals."

    When the user tries to skip evals, the orchestrator must push back
    and explain why evals are necessary.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    Input: Trace where user says "Let's skip the evals and just build it"
    """
    messages = trace.get("orchestrator_messages", [])
    user_said_skip = any(
        "skip" in m.get("content", "").lower() and "eval" in m.get("content", "").lower()
        for m in trace.get("user_messages", [])
    )
    if not user_said_skip:
        return {"pass": True, "reason": "User did not attempt to skip evals (not applicable)"}

    # Check orchestrator pushed back
    for msg in messages:
        content = msg.get("content", "").lower()
        if ("without evals" in content or "no way to verify" in content or
            "success looks like" in content or "define done" in content or
            "what would make you say" in content):
            return {"pass": True, "reason": "Orchestrator pushed back on skipping evals"}
    return {"pass": False, "reason": "Orchestrator did not push back when user tried to skip evals"}


def eval_pm_005_confirms_before_transition(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-005: Orchestrator confirms approval explicitly before stage transition.

    When the user says "looks good" or "yes," the orchestrator should
    probe with a specific restatement before transitioning.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    tool_calls = trace.get("tool_calls", [])
    messages = trace.get("orchestrator_messages", [])

    # Find the transition_stage call
    transition_idx = None
    for i, tc in enumerate(tool_calls):
        if tc.get("name") == "transition_stage":
            transition_idx = i
            break

    if transition_idx is None:
        return {"pass": True, "reason": "No stage transition occurred (not applicable)"}

    # Check that a confirmation message preceded the transition
    pre_transition_messages = messages[:transition_idx] if transition_idx < len(messages) else messages
    has_confirmation = any(
        "just to confirm" in m.get("content", "").lower() or
        "to confirm" in m.get("content", "").lower() or
        "you're approving" in m.get("content", "").lower()
        for m in pre_transition_messages[-3:]  # Check last 3 messages before transition
    )
    return {
        "pass": has_confirmation,
        "reason": "Explicit confirmation before transition" if has_confirmation else "Transitioned without explicit confirmation",
    }


def eval_pm_006_no_premature_prd(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-006: Orchestrator does not write PRD after a single user message.

    The orchestrator must gather information through multiple exchanges
    before writing the PRD. A PRD written after one user message is
    almost always wrong.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    tool_calls = trace.get("tool_calls", [])
    user_messages = trace.get("user_messages", [])

    # Find when PRD was written
    prd_write_idx = None
    user_msg_count_at_write = 0
    for i, tc in enumerate(tool_calls):
        if tc.get("name") == "write_file" and "prd" in tc.get("args", {}).get("path", "").lower():
            prd_write_idx = i
            # Count user messages before this tool call
            user_msg_count_at_write = sum(
                1 for m in user_messages
                if m.get("timestamp", 0) < tc.get("timestamp", float("inf"))
            )
            break

    if prd_write_idx is None:
        return {"pass": True, "reason": "No PRD written yet (not applicable)"}

    # Must have at least 2 user messages (initial + at least one Q&A round)
    return {
        "pass": user_msg_count_at_write >= 2,
        "reason": (
            f"PRD written after {user_msg_count_at_write} user messages (OK)"
            if user_msg_count_at_write >= 2
            else f"PRD written prematurely after only {user_msg_count_at_write} user message(s)"
        ),
    }


def eval_pm_007_evals_proposed_during_intake(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-007: Eval suite proposed during INTAKE, not after.

    The orchestrator must propose the eval suite during INTAKE stage,
    before transitioning to PRD_REVIEW.

    Priority: P1 (every PR)
    Scoring: Binary pass/fail
    """
    tool_calls = trace.get("tool_calls", [])

    # Find when eval suite was created/proposed
    eval_proposed_stage = None
    for tc in tool_calls:
        if tc.get("name") in ["propose_evals", "write_file"]:
            path = tc.get("args", {}).get("path", "")
            if "eval-suite" in path or tc.get("name") == "propose_evals":
                eval_proposed_stage = tc.get("stage", "UNKNOWN")
                break

    return {
        "pass": eval_proposed_stage == "INTAKE",
        "reason": (
            "Evals proposed during INTAKE" if eval_proposed_stage == "INTAKE"
            else f"Evals proposed during {eval_proposed_stage or 'never'} (expected INTAKE)"
        ),
    }


def eval_pm_008_elicitation_quality(trace: dict[str, Any]) -> dict[str, Any]:
    """PM-008: Requirement elicitation quality (Likert 1-5).

    Evaluates whether the orchestrator asks targeted clarifying questions
    that surface ambiguities, dependencies, and unstated assumptions.

    Priority: P1 (every PR)
    Scoring: Likert 1-5 with anchored definitions
    Threshold: >= 3.5

    Note: This is the only Likert eval in the orchestrator suite. It uses
    LLM-as-judge with the Polly rubric anchors from Section 15.3.1.
    """
    judge_prompt = """You are evaluating an AI PM agent's requirement elicitation quality.
    Review the conversation transcript and score using this rubric:

    1 = Asked no clarifying questions; assumed requirements or hallucinated details
    2 = Asked generic questions not tailored to the PRD context
    3 = Asked relevant questions but missed obvious ambiguities or edge cases
    4 = Asked targeted questions that surfaced most ambiguities; minor gaps
    5 = Systematically identified all ambiguities, dependencies, and unstated
        assumptions; questions were prioritized by impact

    List each clarifying question asked.
    Identify gaps the agent missed.
    Provide your score (1-5) with justification.

    Output: SCORE: [1-5], REASONING: [explanation]"""

    return {
        "type": "likert",
        "judge_prompt": judge_prompt,
        "input": trace.get("conversation_transcript", ""),
        "threshold": 3.5,
        "anchors": {
            1: "Asked no clarifying questions; assumed requirements or hallucinated details",
            2: "Asked generic questions not tailored to the PRD context",
            3: "Asked relevant questions but missed obvious ambiguities or edge cases",
            4: "Asked targeted questions that surfaced most ambiguities; minor gaps",
            5: "Systematically identified all ambiguities, dependencies, and assumptions",
        },
    }
