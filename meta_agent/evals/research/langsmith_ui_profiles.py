"""LangSmith UI evaluator profiles for canonical research-agent judge evaluators."""

from __future__ import annotations

import json

from meta_agent.evals.research.common import format_fr_checklist
from meta_agent.evals.research.rubrics import SPECIFIC_INSTRUCTIONS, get_anchors, get_eval_meta


_SYSTEM_PREAMBLE = """\
You are an expert evaluation judge for AI agent systems. You assess the quality of an AI research agent's outputs and behaviors against one specific rubric.

CRITICAL EVALUATION PRINCIPLES:
1. Score ONLY from the provided materials.
2. Do NOT default to middle scores when uncertain; score conservatively.
3. A score of 4 means production-worthy with only minor gaps. A score of 3 is below the bar.
4. Quote or cite specific evidence for every conclusion.
5. Consider missing evidence as a negative signal.
6. Do NOT hallucinate content that is not present in the example.

Analyze carefully. Provide your reasoning first, then your score."""


def _build_likert_prompt(eval_id: str, eval_name: str) -> str:
    anchors = get_anchors(eval_id)
    instructions = SPECIFIC_INSTRUCTIONS.get(eval_id, "")
    meta = get_eval_meta(eval_id)
    description = meta.get("description", eval_name)

    rubric_rows = "\n".join(
        f"| {key} | {value} |"
        for key, value in sorted(anchors.items(), key=lambda item: int(item[0]) if str(item[0]).isdigit() else 0)
    )

    anchor_3 = anchors.get(3, anchors.get("3", ""))
    anchor_4 = anchors.get(4, anchors.get("4", ""))

    return f"""{_SYSTEM_PREAMBLE}

You are evaluating: **{eval_name}** ({eval_id})

**Description:** {description}

## Rubric

| Score | Definition |
|-------|-----------|
{rubric_rows}

## Critical Boundary — Score 3 vs Score 4

A score of **3** means: {anchor_3}

A score of **4** means: {anchor_4}

The passing threshold is >= 4.0. You MUST articulate the concrete evidence that elevates the work from 3 to 4. If that evidence is missing, the score is 3 or below.

## Specific Evaluation Guidance

{instructions}

## Evaluation Task

Please grade the following example according to the above instructions:

<example>
<input>
{{{{input}}}}
</input>

<output>
{{{{output}}}}
</output>

<reference_outputs>
{{{{reference}}}}
</reference_outputs>
</example>

Provide your reasoning first, then your score. Be strict and consistent."""


def _build_binary_prompt(eval_id: str, eval_name: str, pass_criteria: str) -> str:
    return f"""{_SYSTEM_PREAMBLE}

You are evaluating: **{eval_name}** ({eval_id})

## Pass Criteria

{pass_criteria}

## Evaluation Rules

1. The criterion is either fully met or not met.
2. If the evidence is ambiguous or incomplete, score as NOT MET.
3. Quote the specific evidence that supports your determination.

## Evaluation Task

Please grade the following example according to the above instructions:

<example>
<input>
{{{{input}}}}
</input>

<output>
{{{{output}}}}
</output>

<reference_outputs>
{{{{reference}}}}
</reference_outputs>
</example>

Provide your reasoning first, then your pass/fail determination."""


def _likert_feedback_config(eval_id: str, eval_name: str) -> dict:
    return {
        "title": "extract",
        "description": f"Likert 1-5 score for {eval_name} ({eval_id})",
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "description": "Score from 1 to 5 per rubric anchors",
                "minimum": 1,
                "maximum": 5,
            },
            "comment": {
                "type": "string",
                "description": "Short reasoning summary",
            },
            "confidence": {
                "type": "string",
                "description": "HIGH, MEDIUM, or LOW confidence in the judgment",
            },
            "flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional evaluation concerns such as missing evidence",
            },
        },
        "required": ["score", "comment"],
        "strict": True,
    }


def _binary_feedback_config(eval_id: str, eval_name: str) -> dict:
    return {
        "title": "extract",
        "description": f"Binary pass/fail for {eval_name} ({eval_id})",
        "type": "object",
        "properties": {
            "passed": {
                "type": "boolean",
                "description": "True if the pass criteria are fully met, false otherwise",
            },
            "comment": {
                "type": "string",
                "description": "Short reasoning summary",
            },
            "confidence": {
                "type": "string",
                "description": "HIGH, MEDIUM, or LOW confidence in the judgment",
            },
            "flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional evaluation concerns such as missing evidence",
            },
        },
        "required": ["passed", "comment"],
        "strict": True,
    }


_LIKERT_EVALS = [
    "RINFRA-003",
    "RINFRA-004",
    "RQ-001",
    "RQ-002",
    "RQ-003",
    "RQ-004",
    "RQ-005",
    "RQ-006",
    "RQ-007",
    "RQ-008",
    "RQ-009",
    "RQ-010",
    "RQ-011",
    "RQ-012",
    "RQ-013",
    "RR-001",
    "RR-002",
    "RR-003",
]

_BINARY_JUDGE_EVALS = {
    "RB-005": {
        "name": "Citation integrity and content verification",
        "pass_criteria": "Assume URL prechecks already ran. Pass only if the cited claims remain faithful to the fetched sources and no unsupported citation-backed claim is present.",
    },
    "RB-009": {
        "name": "Sub-agents execute in parallel",
        "pass_criteria": "Pass only if the trace clearly shows true parallel sub-agent execution, not just multiple task calls.",
    },
    "RB-010": {
        "name": "Main agent aggregates sub-agent findings after completion",
        "pass_criteria": "Pass only if the main agent reads sub-agent findings after those sub-agents complete and uses them in synthesis.",
    },
    "RB-011": {
        "name": "HITL gate fires before deep-dive research",
        "pass_criteria": "Pass only if an HITL approval or interrupt happens before the deep-dive verification stage begins.",
    },
    "RI-002": {
        "name": "Research covers all PRD functional requirements",
        "pass_criteria": "Pass only if the full research record (bundle, decomposition, HITL artifacts, and trace evidence when provided) substantively addresses every PRD functional requirement area in the following checklist:\n\n"
        + format_fr_checklist(),
    },
    "RI-003": {
        "name": "Research covers eval implications",
        "pass_criteria": "Pass only if the research record addresses tooling, dataset, evaluator, experiment, and trace implications needed to implement the eval suite.",
    },
}


EVALUATOR_PROFILES: list[dict] = []

for eval_id in _LIKERT_EVALS:
    meta = get_eval_meta(eval_id)
    title = meta.get("title", eval_id)
    EVALUATOR_PROFILES.append(
        {
            "eval_id": eval_id,
            "name": f"Research Agent: {title}",
            "type": "likert",
            "recommended_model": "claude-sonnet-4-20250514",
            "recommended_sampling_rate": 1.0,
            "sampling_justification": "Calibration and judge development require full coverage.",
            "prompt": _build_likert_prompt(eval_id, title),
            "feedback_config": _likert_feedback_config(eval_id, title),
        }
    )

for eval_id, info in _BINARY_JUDGE_EVALS.items():
    EVALUATOR_PROFILES.append(
        {
            "eval_id": eval_id,
            "name": f"Research Agent: {info['name']}",
            "type": "binary",
            "recommended_model": "claude-sonnet-4-20250514",
            "recommended_sampling_rate": 1.0,
            "sampling_justification": "These are release-gating hybrid/binary checks during evaluator hardening.",
            "prompt": _build_binary_prompt(eval_id, info["name"], info["pass_criteria"]),
            "feedback_config": _binary_feedback_config(eval_id, info["name"]),
        }
    )


def print_profiles(*, format: str = "ui") -> None:
    for index, profile in enumerate(EVALUATOR_PROFILES, 1):
        print(f"\n{'#' * 70}")
        print(f"### Evaluator Profile {index}/{len(EVALUATOR_PROFILES)}: `{profile['name']}`")
        print(f"{'#' * 70}")
        print(f"\n**Eval ID:** {profile['eval_id']}")
        print(f"**Type:** {profile['type']}")
        print(f"**Recommended Model:** `{profile['recommended_model']}`")
        print(
            f"**Recommended Sampling Rate:** {profile['recommended_sampling_rate'] * 100:.0f}% — {profile['sampling_justification']}"
        )
        print("\n**Prompt** (paste into LangSmith prompt editor):\n")
        print("```text")
        print(profile["prompt"])
        print("```")
        print("\n**Feedback Configuration JSON** (paste into Feedback Configuration):\n")
        print("```json")
        print(json.dumps(profile["feedback_config"], indent=2))
        print("```")
