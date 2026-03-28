"""Polly rubric anchors for PM evaluation dimensions.

Spec References: Sections 15.3.1-15.3.5, 22.23

These are EXTERNAL evaluator definitions — they evaluate orchestrator
traces post-hoc via LLM-as-judge. They are NOT embedded in the
orchestrator's system prompt.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Dimension 1: Requirement Elicitation Quality (Likert 1-5)
# Section 15.3.1
# ---------------------------------------------------------------------------

REQUIREMENT_ELICITATION_QUALITY: dict[int, str] = {
    1: "Asked no clarifying questions; assumed requirements or hallucinated details",
    2: "Asked generic questions not tailored to the PRD context",
    3: "Asked relevant questions but missed obvious ambiguities or edge cases",
    4: "Asked targeted questions that surfaced most ambiguities; minor gaps",
    5: "Systematically identified all ambiguities, dependencies, and unstated assumptions; questions were prioritized by impact",
}

# ---------------------------------------------------------------------------
# Dimension 2: Stakeholder Alignment / Consensus Building (Likert 1-5)
# Section 15.3.2
# ---------------------------------------------------------------------------

STAKEHOLDER_ALIGNMENT: dict[int, str] = {
    1: "Proceeded without confirming understanding; stakeholder left confused or misaligned",
    2: "Summarized requirements but didn't seek explicit confirmation",
    3: "Sought confirmation but accepted vague 'yes' without probing; partial alignment",
    4: "Confirmed understanding with specific restatements; minor misalignments remain",
    5: "Explicitly confirmed each requirement, resolved all conflicts, and stakeholder expressed clear confidence in shared understanding",
}

# ---------------------------------------------------------------------------
# Dimension 3: Spec Decomposition Quality (Likert 1-5)
# Section 15.3.3
# ---------------------------------------------------------------------------

SPEC_DECOMPOSITION_QUALITY: dict[int, str] = {
    1: "No decomposition; passed raw PRD or vague instructions downstream",
    2: "Decomposed into tasks but with missing context, unclear scope, or overlapping responsibilities",
    3: "Reasonable decomposition; some tasks lack acceptance criteria or have implicit dependencies",
    4: "Clear task breakdown with explicit acceptance criteria; minor gaps in edge case handling",
    5: "Each task has: clear scope, acceptance criteria, dependencies, and enough context for the downstream agent to execute autonomously without back-and-forth",
}

# ---------------------------------------------------------------------------
# Dimension 4: Synthetic Eval Generation Quality (Likert 1-5)
# Section 15.3.4
# ---------------------------------------------------------------------------

SYNTHETIC_EVAL_GENERATION_QUALITY: dict[int, str] = {
    1: "No evals generated, or evals are trivial/unrelated to requirements",
    2: "Evals exist but only cover happy path; no edge cases or failure modes",
    3: "Covers main functionality; edge cases mentioned but not rigorously defined",
    4: "Good coverage of happy path + key edge cases; evals are executable and measurable",
    5: "Comprehensive eval suite: happy path, edge cases, failure modes, regression tests for known risks; each eval has clear pass/fail criteria and maps to a specific requirement",
}

# ---------------------------------------------------------------------------
# Dimension 5: Iteration Efficiency (Likert 1-5)
# Section 15.3.5
# ---------------------------------------------------------------------------

ITERATION_EFFICIENCY: dict[int, str] = {
    1: "Endless loop; never converged or stakeholder abandoned",
    2: "Converged but took 3x+ more turns than necessary due to poor questions or misunderstandings",
    3: "Converged with some unnecessary back-and-forth; could have batched questions better",
    4: "Efficient iteration; minor redundancy",
    5: "Optimal path to convergence; every turn added value, no wasted exchanges",
}

# ---------------------------------------------------------------------------
# All dimensions as a collection
# ---------------------------------------------------------------------------

PM_DIMENSIONS: dict[str, dict[str, Any]] = {
    "requirement_elicitation_quality": {
        "name": "Requirement Elicitation Quality",
        "scoring": "likert_1_5",
        "threshold": 3.5,
        "anchors": REQUIREMENT_ELICITATION_QUALITY,
    },
    "stakeholder_alignment": {
        "name": "Stakeholder Alignment / Consensus Building",
        "scoring": "likert_1_5",
        "threshold": 3.5,
        "anchors": STAKEHOLDER_ALIGNMENT,
    },
    "spec_decomposition_quality": {
        "name": "Spec Decomposition Quality",
        "scoring": "likert_1_5",
        "threshold": 3.5,
        "anchors": SPEC_DECOMPOSITION_QUALITY,
    },
    "synthetic_eval_generation_quality": {
        "name": "Synthetic Eval Generation Quality",
        "scoring": "likert_1_5",
        "threshold": 3.5,
        "anchors": SYNTHETIC_EVAL_GENERATION_QUALITY,
    },
    "iteration_efficiency": {
        "name": "Iteration Efficiency",
        "scoring": "likert_1_5",
        "threshold": 3.5,
        "anchors": ITERATION_EFFICIENCY,
    },
}
