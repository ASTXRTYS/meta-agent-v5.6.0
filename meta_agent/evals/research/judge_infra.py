"""Shared LLM-as-Judge infrastructure for research agent evals.

Provides the Likert and Binary judge templates, structured output schemas,
retry logic, and the system prompt shared by all judge evaluators.
"""

from __future__ import annotations

import json
import os
from typing import Any, TypedDict, Annotated

from meta_agent.evals.research.common import make_result

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluation judge for AI agent systems. Your task is to \
assess the quality of an AI research agent's outputs and behaviors against \
a specific rubric.

CRITICAL EVALUATION PRINCIPLES:
1. Score ONLY based on evidence present in the provided materials. Never \
infer quality from absence of information — absence is a signal of lower quality.
2. Do NOT default to middle scores (3) when uncertain. If evidence is \
ambiguous, explain why and score conservatively (lower).
3. Do NOT be generous. A score of 4 means "good with minor gaps" — not \
"good enough." A score of 5 is reserved for genuinely exceptional performance \
with zero observable gaps.
4. Quote specific evidence for every claim in your reasoning. If you cannot \
quote evidence, you cannot make the claim.
5. The threshold for passing is >= 4.0. A score of 3 means "below the bar." \
Be especially rigorous about distinguishing 3 from 4 — this is the pass/fail boundary.
6. Do NOT hallucinate content that is not in the provided materials. If the \
research bundle does not mention something, the agent did not do it.
7. Consider both what IS present and what is MISSING. Gaps are as important as content.

Respond ONLY with valid JSON matching the specified output format. No other text."""


LIKERT_TEMPLATE = """\
You are evaluating: {eval_name} ({eval_id})

RUBRIC:
| Score | Definition |
|-------|-----------|
| 1 | {anchor_1} |
| 2 | {anchor_2} |
| 3 | {anchor_3} |
| 4 | {anchor_4} |
| 5 | {anchor_5} |

CRITICAL BOUNDARY — Score 3 vs Score 4:
A score of 3 means: {anchor_3}
A score of 4 means: {anchor_4}
The passing threshold is >= 4.0. You must articulate specific evidence that \
elevates the work from "3" to "4". If you cannot identify concrete evidence \
of the qualities described in the score-4 anchor, the score is 3 or below.

{specific_instructions}

AGENT OUTPUT TO EVALUATE:
---
{agent_output}
---

{reference_section}

Respond with EXACTLY this JSON structure:
{{"score": <integer 1-5>, "reasoning": "<2-4 sentences with specific rubric references>", "evidence": ["<quote or observation 1>", "<...>"], "confidence": "<HIGH|MEDIUM|LOW>", "flags": ["<any concerns, or empty array>"]}}"""


BINARY_TRACE_TEMPLATE = """\
You are evaluating: {eval_name} ({eval_id})

PASS CRITERIA: {pass_criteria}

You must determine whether this criterion is MET or NOT MET based on the \
trace evidence below.

EVALUATION RULES:
1. The criterion is either fully met or not met. There is no partial credit.
2. If the trace evidence is ambiguous or incomplete, score as NOT MET (fail).
3. Quote specific trace entries that support your determination.

TRACE DATA:
---
{trace_data}
---

{additional_context}

Respond with EXACTLY this JSON structure:
{{"score": <0 for fail, 1 for pass>, "reasoning": "<2-3 sentences with specific trace references>", "evidence": ["<specific trace entry 1>", "<...>"], "confidence": "<HIGH|MEDIUM|LOW>", "flags": ["<any concerns, or empty array>"]}}"""


class LikertGrade(TypedDict):
    score: Annotated[int, "Integer 1-5"]
    reasoning: Annotated[str, "Explanation with rubric references"]
    evidence: Annotated[list[str], "Specific quotes or observations"]
    confidence: Annotated[str, "HIGH, MEDIUM, or LOW"]
    flags: Annotated[list[str], "Concerns about this evaluation"]


class BinaryGrade(TypedDict):
    score: Annotated[int, "0 for fail, 1 for pass"]
    reasoning: Annotated[str, "Explanation with trace references"]
    evidence: Annotated[list[str], "Specific trace entries"]
    confidence: Annotated[str, "HIGH, MEDIUM, or LOW"]
    flags: Annotated[list[str], "Concerns about this evaluation"]


def _get_outputs(run: Any) -> dict:
    return run.outputs if hasattr(run, "outputs") else run.get("outputs", {}) or {}


def short_comment(eval_id: str, reasoning: str, *, fallback: str = "") -> str:
    reasoning = (reasoning or fallback or "").strip()
    if not reasoning:
        reasoning = "no judge reasoning returned"
    return f"{eval_id}: {reasoning}"


def _parse_judge_response(text: str) -> dict:
    """Parse JSON from judge response, handling common formatting issues."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"score": -1, "reasoning": f"Failed to parse judge response: {text[:200]}",
            "evidence": [], "confidence": "LOW", "flags": ["parse_error"]}


def _judge_backends(default_model: str | None = None) -> list[tuple[str, str]]:
    override_provider = os.getenv("RESEARCH_EVAL_JUDGE_PROVIDER", "").strip().lower()
    override_model = os.getenv("RESEARCH_EVAL_JUDGE_MODEL", "").strip()

    if override_provider:
        if override_provider == "openai":
            model = override_model or os.getenv("RESEARCH_EVAL_OPENAI_MODEL", "gpt-4o-mini")
        elif override_provider == "anthropic":
            model = override_model or default_model or "claude-opus-4-6"
        else:
            model = override_model or default_model or ""
        return [(override_provider, model)]

    backends: list[tuple[str, str]] = []
    if os.getenv("ANTHROPIC_API_KEY"):
        backends.append(("anthropic", default_model or "claude-opus-4-6"))
    if os.getenv("OPENAI_API_KEY"):
        backends.append(("openai", os.getenv("RESEARCH_EVAL_OPENAI_MODEL", "gpt-4o-mini")))
    return backends


async def _invoke_judge(
    *,
    messages: list[dict[str, str]],
    default_model: str | None,
    temperature: float,
) -> tuple[dict, dict[str, Any] | None]:
    errors: list[str] = []
    for provider, model_name in _judge_backends(default_model):
        try:
            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic

                llm = ChatAnthropic(model=model_name, temperature=temperature, max_tokens=1024)
            elif provider == "openai":
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(model=model_name, temperature=temperature, max_tokens=1024)
            else:
                errors.append(f"unsupported provider: {provider}")
                continue

            resp = await llm.ainvoke(messages)
            content = resp.content if isinstance(resp.content, str) else json.dumps(resp.content)
            return _parse_judge_response(content), {"provider": provider, "model": model_name}
        except Exception as exc:
            errors.append(f"{provider}:{model_name}: {exc}")

    return {
        "score": -1,
        "reasoning": "Judge invocation failed",
        "evidence": [],
        "confidence": "LOW",
        "flags": ["judge_error"],
    }, {"errors": errors}


async def run_likert_judge(
    *,
    eval_id: str,
    eval_name: str,
    anchors: dict[int | str, str],
    specific_instructions: str,
    agent_output: str,
    reference_excerpt: str = "",
    model: str | None = "claude-opus-4-6",
    temperature: float = 0.0,
) -> dict:
    """Run a Likert-scale LLM judge and return LangSmith-compatible result."""
    if not _judge_backends(model):
        return make_result(
            -1,
            f"{eval_id}: no configured judge backend",
            confidence="LOW",
            flags=["missing_judge_backend"],
        )

    ref_section = ""
    if reference_excerpt:
        ref_section = f"CALIBRATION REFERENCE (Score 5 example):\n---\n{reference_excerpt}\n---\nUse this reference to calibrate your scoring."

    prompt = LIKERT_TEMPLATE.format(
        eval_id=eval_id,
        eval_name=eval_name,
        anchor_1=anchors.get(1, anchors.get("1", "")),
        anchor_2=anchors.get(2, anchors.get("2", "")),
        anchor_3=anchors.get(3, anchors.get("3", "")),
        anchor_4=anchors.get(4, anchors.get("4", "")),
        anchor_5=anchors.get(5, anchors.get("5", "")),
        specific_instructions=specific_instructions,
        agent_output=agent_output[:30000],
        reference_section=ref_section,
    )

    try:
        grade, backend = await _invoke_judge(
            messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            ],
            default_model=model,
            temperature=temperature,
        )
        score = grade.get("score", -1)
        if isinstance(score, str):
            score = int(score) if score.isdigit() else -1
        return make_result(
            score,
            short_comment(eval_id, grade.get("reasoning", "")),
            reasoning=grade.get("reasoning", ""),
            evidence=grade.get("evidence", []),
            confidence=str(grade.get("confidence", "LOW")),
            flags=[str(flag) for flag in grade.get("flags", [])],
            details={"judge_raw": grade, "judge_backend": backend},
        )
    except Exception as e:
        return make_result(
            -1,
            f"{eval_id}: judge error: {e}",
            confidence="LOW",
            flags=["judge_error"],
        )


async def run_binary_judge(
    *,
    eval_id: str,
    eval_name: str,
    pass_criteria: str,
    trace_data: str,
    additional_context: str = "",
    model: str | None = "claude-opus-4-6",
    temperature: float = 0.0,
) -> dict:
    """Run a binary LLM judge and return LangSmith-compatible result."""
    if not _judge_backends(model):
        return make_result(
            -1,
            f"{eval_id}: no configured judge backend",
            confidence="LOW",
            flags=["missing_judge_backend"],
        )

    prompt = BINARY_TRACE_TEMPLATE.format(
        eval_id=eval_id,
        eval_name=eval_name,
        pass_criteria=pass_criteria,
        trace_data=trace_data[:20000],
        additional_context=additional_context,
    )

    try:
        grade, backend = await _invoke_judge(
            messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            ],
            default_model=model,
            temperature=temperature,
        )
        score = grade.get("score", -1)
        if isinstance(score, str):
            score = int(score) if score.isdigit() else -1
        bounded_score = min(score, 1) if score >= 0 else score
        return make_result(
            bounded_score,
            short_comment(eval_id, grade.get("reasoning", "")),
            reasoning=grade.get("reasoning", ""),
            evidence=grade.get("evidence", []),
            confidence=str(grade.get("confidence", "LOW")),
            flags=[str(flag) for flag in grade.get("flags", [])],
            details={"judge_raw": grade, "judge_backend": backend},
        )
    except Exception as e:
        return make_result(
            -1,
            f"{eval_id}: judge error: {e}",
            confidence="LOW",
            flags=["judge_error"],
        )
