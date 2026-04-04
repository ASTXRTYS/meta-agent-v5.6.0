"""Shared LLM-as-Judge infrastructure for research agent evals.

Phase 3 runtime policy:
- Anthropic SDK is the canonical judge runtime (`anthropic.AsyncAnthropic`)
- Adaptive thinking is always enabled for Anthropic judges
- Judge calls are traced as explicit LangSmith child spans
- Judge prompt construction is trace-context aware
"""

from __future__ import annotations

import inspect
import json
import os
from typing import Any, Annotated, Mapping, TypedDict

import anthropic
from langsmith import traceable
from langsmith.wrappers import wrap_anthropic

from meta_agent.evals.research.common import make_result
from meta_agent.evals.research.judge_trace_context import build_trace_context_pack

JUDGE_DEFAULT_MODEL = "claude-opus-4-6"
JUDGE_MAX_TOKENS = 2048


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


CATEGORY_POLICY: dict[str, dict[str, Any]] = {
    "RESEARCH-QUALITY": {
        "template": "Focus on quality/completeness of artifacts and corroborating trace evidence.",
        "evidence_strategy": "bundle_plus_key_trace",
        "require_full_trace_fetch": False,
        "tools_allowed": False,
        "streaming": True,
    },
    "RESEARCH-REASONING": {
        "template": "Prioritize decision quality and intermediate reasoning evidence from the run trajectory.",
        "evidence_strategy": "reasoning_rich_trace",
        "require_full_trace_fetch": True,
        "tools_allowed": False,
        "streaming": True,
    },
    "RESEARCH-BEHAVIORAL": {
        "template": "Treat trace-level behavioral evidence as primary; bundle text is supporting context only.",
        "evidence_strategy": "trace_first_behavioral",
        "require_full_trace_fetch": True,
        "tools_allowed": False,
        "streaming": True,
    },
    "RESEARCH-INTEGRATION": {
        "template": "Evaluate integrated system readiness across bundle + decomposition + handoff artifacts + trace linkage.",
        "evidence_strategy": "integration_composite",
        "require_full_trace_fetch": True,
        "tools_allowed": False,
        "streaming": True,
    },
}


LIKERT_TEMPLATE = """\
You are evaluating: {eval_name} ({eval_id})

CATEGORY POLICY:
- Category: {category}
- Category frame: {category_template}
- Evidence strategy: {evidence_strategy}

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

SPECIFIC EVAL GUIDANCE:
{specific_instructions}

TRACE-AWARE EVIDENCE PACK:
{evidence_pack}

{reference_section}

Respond with EXACTLY this JSON structure:
{{"score": <integer 1-5>, "reasoning": "<2-4 sentences with specific rubric references>", "evidence": ["<quote or observation 1>", "<...>"], "confidence": "<HIGH|MEDIUM|LOW>", "flags": ["<any concerns, or empty array>"]}}"""


BINARY_TRACE_TEMPLATE = """\
You are evaluating: {eval_name} ({eval_id})

CATEGORY POLICY:
- Category: {category}
- Category frame: {category_template}
- Evidence strategy: {evidence_strategy}

PASS CRITERIA: {pass_criteria}

You must determine whether this criterion is MET or NOT MET based on the \
trace evidence below.

EVALUATION RULES:
1. The criterion is either fully met or not met. There is no partial credit.
2. If the trace evidence is ambiguous or incomplete, score as NOT MET (fail).
3. Quote specific trace entries that support your determination.

TRACE-AWARE EVIDENCE PACK:
{evidence_pack}

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


def _run_get(run: Any, key: str, default: Any = None) -> Any:
    if run is None:
        return default
    if isinstance(run, Mapping):
        return run.get(key, default)
    return getattr(run, key, default)


def _get_outputs(run: Any) -> dict:
    outputs = _run_get(run, "outputs", {}) or {}
    return outputs if isinstance(outputs, dict) else {}


def short_comment(eval_id: str, reasoning: str, *, fallback: str = "") -> str:
    reasoning = (reasoning or fallback or "").strip()
    if not reasoning:
        reasoning = "no judge reasoning returned"
    return f"{eval_id}: {reasoning}"


def infer_eval_category(eval_id: str) -> str:
    if eval_id.startswith("RR-"):
        return "RESEARCH-REASONING"
    if eval_id.startswith("RB-"):
        return "RESEARCH-BEHAVIORAL"
    if eval_id.startswith("RI-"):
        return "RESEARCH-INTEGRATION"
    return "RESEARCH-QUALITY"


def _policy_for_category(category: str) -> dict[str, Any]:
    return CATEGORY_POLICY.get(category, CATEGORY_POLICY["RESEARCH-QUALITY"])


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
    return {
        "score": -1,
        "reasoning": f"Failed to parse judge response: {text[:200]}",
        "evidence": [],
        "confidence": "LOW",
        "flags": ["parse_error"],
    }


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _judge_model(default_model: str | None) -> str:
    override_model = os.getenv("RESEARCH_EVAL_JUDGE_MODEL", "").strip()
    if override_model:
        return override_model
    return default_model or JUDGE_DEFAULT_MODEL


def _judge_streaming_enabled() -> bool:
    return _bool_env("RESEARCH_EVAL_JUDGE_STREAMING", True)


def _judge_debug_thinking_enabled() -> bool:
    return _bool_env("RESEARCH_EVAL_JUDGE_DEBUG_THINKING", False)


def _thinking_config() -> dict[str, Any]:
    thinking = {"type": "adaptive"}
    if _bool_env("RESEARCH_EVAL_JUDGE_OMIT_THINKING_DISPLAY", False):
        thinking["display"] = "omitted"
    return thinking


def _judge_client() -> anthropic.AsyncAnthropic | None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    return wrap_anthropic(anthropic.AsyncAnthropic())


def _build_anthropic_call_kwargs(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    return {
        "model": model,
        "max_tokens": JUDGE_MAX_TOKENS,
        "thinking": _thinking_config(),
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }


def _extract_block_texts(message: Any) -> tuple[str, str]:
    text_parts: list[str] = []
    thinking_parts: list[str] = []
    content_blocks = getattr(message, "content", None) or []
    for block in content_blocks:
        block_type = getattr(block, "type", None)
        if block_type is None and isinstance(block, Mapping):
            block_type = block.get("type")
        if block_type == "text":
            text_value = getattr(block, "text", None)
            if text_value is None and isinstance(block, Mapping):
                text_value = block.get("text", "")
            if text_value:
                text_parts.append(str(text_value))
        elif block_type == "thinking":
            thinking_value = getattr(block, "thinking", None)
            if thinking_value is None and isinstance(block, Mapping):
                thinking_value = block.get("thinking", "")
            if thinking_value:
                thinking_parts.append(str(thinking_value))
    return "".join(text_parts), "".join(thinking_parts)


def _extract_usage(message: Any) -> dict[str, Any]:
    usage = getattr(message, "usage", None)
    if usage is None:
        return {}
    fields = (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "server_tool_use",
    )
    data: dict[str, Any] = {}
    for field in fields:
        value = getattr(usage, field, None)
        if value is not None:
            data[field] = value
    return data


def _trace_metadata(
    *,
    eval_id: str,
    category: str,
    scoring: str,
    evaluation_method: str,
    model: str,
    streaming_used: bool,
    trace_context_source: str,
) -> dict[str, Any]:
    return {
        "eval_id": eval_id,
        "category": category,
        "scoring": scoring,
        "evaluation_method": evaluation_method,
        "judge_model": model,
        "thinking_type": "adaptive",
        "streaming_used": streaming_used,
        "tools_enabled": False,
        "trace_context_source": trace_context_source,
    }


def _compact_json(value: Any, *, max_chars: int) -> str:
    try:
        rendered = json.dumps(value, indent=2, default=str)
    except Exception:
        rendered = str(value)
    if len(rendered) <= max_chars:
        return rendered
    return f"{rendered[:max_chars]}...<truncated>"


def _render_likert_evidence_pack(
    *,
    category: str,
    policy: dict[str, Any],
    trace_pack: dict[str, Any],
    agent_output: str,
) -> str:
    judge_view = trace_pack.get("judge_view", {})
    distilled = trace_pack.get("judge_view_json", "")
    raw_payload = trace_pack.get("raw_trace_payload_json", "")
    source = trace_pack.get("trace_context_source", "run_only")

    if category == "RESEARCH-REASONING":
        return (
            f"1) Primary evaluator payload:\n---\n{agent_output[:22000]}\n---\n\n"
            f"2) Distilled trace view ({source}):\n---\n{distilled[:18000]}\n---\n\n"
            f"3) Raw trace payload excerpt:\n---\n{raw_payload[:22000]}\n---"
        )
    if category == "RESEARCH-BEHAVIORAL":
        return (
            f"1) Trace-first distilled view ({source}):\n---\n{distilled[:22000]}\n---\n\n"
            f"2) Raw trace payload excerpt:\n---\n{raw_payload[:22000]}\n---\n\n"
            f"3) Supplemental evaluator payload:\n---\n{agent_output[:12000]}\n---"
        )
    if category == "RESEARCH-INTEGRATION":
        return (
            f"1) Integration payload (bundle/decomposition/handoff context):\n---\n{agent_output[:22000]}\n---\n\n"
            f"2) Trace linkage ({source}):\n---\n{distilled[:22000]}\n---\n\n"
            f"3) Child run summaries:\n---\n{_compact_json(judge_view.get('child_run_summaries', []), max_chars=10000)}\n---"
        )
    return (
        f"1) Primary evaluator payload:\n---\n{agent_output[:26000]}\n---\n\n"
        f"2) Key trace evidence ({source}):\n---\n{distilled[:18000]}\n---\n\n"
        f"3) Raw trace payload excerpt:\n---\n{raw_payload[:12000]}\n---\n\n"
        f"(Strategy: {policy.get('evidence_strategy', '')})"
    )


def _render_binary_evidence_pack(
    *,
    category: str,
    policy: dict[str, Any],
    trace_pack: dict[str, Any],
    trace_data: str,
    additional_context: str,
) -> str:
    distilled = trace_pack.get("judge_view_json", "")
    raw_payload = trace_pack.get("raw_trace_payload_json", "")
    source = trace_pack.get("trace_context_source", "run_only")

    if category == "RESEARCH-BEHAVIORAL":
        return (
            f"1) Distilled trace view ({source}):\n---\n{distilled[:22000]}\n---\n\n"
            f"2) Raw trace payload excerpt:\n---\n{raw_payload[:22000]}\n---\n\n"
            f"3) Evaluator trace payload:\n---\n{trace_data[:18000]}\n---\n\n"
            f"4) Additional context:\n---\n{additional_context[:12000]}\n---"
        )
    return (
        f"1) Evaluator trace payload:\n---\n{trace_data[:18000]}\n---\n\n"
        f"2) Distilled trace view ({source}):\n---\n{distilled[:18000]}\n---\n\n"
        f"3) Raw trace payload excerpt:\n---\n{raw_payload[:18000]}\n---\n\n"
        f"4) Additional context:\n---\n{additional_context[:12000]}\n---\n\n"
        f"(Strategy: {policy.get('evidence_strategy', '')})"
    )


@traceable(name="judge_context_assembly", run_type="chain")
def _assemble_trace_context(
    *,
    run: Any,
    eval_id: str,
    category: str,
    require_full_fetch: bool,
) -> dict[str, Any]:
    return build_trace_context_pack(
        run,
        eval_id=eval_id,
        require_full_trace_fetch=require_full_fetch,
    )


@traceable(name="judge_claude_call", run_type="llm")
async def _invoke_anthropic_judge(
    *,
    eval_id: str,
    category: str,
    scoring: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    streaming: bool,
    trace_context_source: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    client = _judge_client()
    if client is None:
        return (
            {
                "score": -1,
                "reasoning": "Judge invocation failed: ANTHROPIC_API_KEY is not set",
                "evidence": [],
                "confidence": "LOW",
                "flags": ["missing_judge_backend"],
            },
            {
                "provider": "anthropic",
                "model": model,
                "errors": ["ANTHROPIC_API_KEY is not set"],
                "thinking_type": "adaptive",
                "streaming_used": False,
                "tools_enabled": False,
                "trace_context_source": trace_context_source,
            },
        )

    kwargs = _build_anthropic_call_kwargs(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    stream_text: list[str] = []
    stream_thinking: list[str] = []
    final_message: Any = None
    streaming_used = bool(streaming)

    try:
        if streaming:
            async with client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    event_type = getattr(event, "type", "")
                    if event_type != "content_block_delta":
                        continue
                    delta = getattr(event, "delta", None)
                    delta_type = getattr(delta, "type", "")
                    if delta_type == "text_delta":
                        text_value = getattr(delta, "text", "")
                        if text_value:
                            stream_text.append(str(text_value))
                    elif delta_type == "thinking_delta":
                        thinking_value = getattr(delta, "thinking", "")
                        if thinking_value:
                            stream_thinking.append(str(thinking_value))
                final_message = stream.get_final_message()
                if inspect.isawaitable(final_message):
                    final_message = await final_message
        else:
            final_message = await client.messages.create(**kwargs)
    except Exception as exc:
        return (
            {
                "score": -1,
                "reasoning": f"Judge invocation failed: {exc}",
                "evidence": [],
                "confidence": "LOW",
                "flags": ["judge_error"],
            },
            {
                "provider": "anthropic",
                "model": model,
                "evaluation_method": "anthropic_messages_stream" if streaming_used else "anthropic_messages_create",
                "thinking_type": "adaptive",
                "streaming_used": streaming_used,
                "tools_enabled": False,
                "trace_context_source": trace_context_source,
                "errors": [str(exc)],
                "token_usage": {},
                "stop_reason": None,
                "category": category,
                "scoring": scoring,
            },
        )

    text_from_blocks, thinking_from_blocks = _extract_block_texts(final_message)
    parsed_text = text_from_blocks or "".join(stream_text)
    parsed_thinking = thinking_from_blocks or "".join(stream_thinking)

    if _judge_debug_thinking_enabled() and parsed_thinking:
        print(f"[judge-thinking][{eval_id}] {parsed_thinking[:2000]}")

    grade = _parse_judge_response(parsed_text)
    usage = _extract_usage(final_message)
    stop_reason = getattr(final_message, "stop_reason", None)
    backend = {
        "provider": "anthropic",
        "model": model,
        "evaluation_method": "anthropic_messages_stream" if streaming_used else "anthropic_messages_create",
        "thinking_type": "adaptive",
        "streaming_used": streaming_used,
        "tools_enabled": False,
        "trace_context_source": trace_context_source,
        "token_usage": usage,
        "stop_reason": stop_reason,
        "category": category,
        "scoring": scoring,
    }
    return grade, backend


@traceable(name="judge_response_parse", run_type="chain")
def _normalize_score(*, scoring: str, grade: dict[str, Any]) -> int:
    raw_score = grade.get("score", -1)
    if isinstance(raw_score, str):
        raw_score = int(raw_score) if raw_score.isdigit() else -1
    if not isinstance(raw_score, int):
        return -1
    if scoring == "binary_pass_fail":
        return min(raw_score, 1) if raw_score >= 0 else raw_score
    if scoring == "likert_1_5":
        if raw_score < 1:
            return -1
        return max(1, min(raw_score, 5))
    return raw_score


@traceable(name="research_likert_judge", run_type="chain")
async def run_likert_judge(
    *,
    eval_id: str,
    eval_name: str,
    anchors: dict[int | str, str],
    specific_instructions: str,
    agent_output: str,
    reference_excerpt: str = "",
    model: str | None = JUDGE_DEFAULT_MODEL,
    run: Any | None = None,
) -> dict:
    """Run a Likert-scale Anthropic judge and return LangSmith-compatible result."""
    category = infer_eval_category(eval_id)
    policy = _policy_for_category(category)
    model_name = _judge_model(model)
    streaming = bool(policy.get("streaming", True)) and _judge_streaming_enabled()

    trace_pack = _assemble_trace_context(
        run=run,
        eval_id=eval_id,
        category=category,
        require_full_fetch=bool(policy.get("require_full_trace_fetch", False)),
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="likert_1_5",
                evaluation_method="judge_context_assembly",
                model=model_name,
                streaming_used=streaming,
                trace_context_source="unknown",
            )
        },
    )

    ref_section = ""
    if reference_excerpt:
        ref_section = (
            "CALIBRATION REFERENCE (Score 5 example):\n---\n"
            f"{reference_excerpt}\n---\nUse this reference to calibrate your scoring."
        )

    evidence_pack = _render_likert_evidence_pack(
        category=category,
        policy=policy,
        trace_pack=trace_pack,
        agent_output=agent_output,
    )
    prompt = LIKERT_TEMPLATE.format(
        eval_id=eval_id,
        eval_name=eval_name,
        category=category,
        category_template=policy.get("template", ""),
        evidence_strategy=policy.get("evidence_strategy", ""),
        anchor_1=anchors.get(1, anchors.get("1", "")),
        anchor_2=anchors.get(2, anchors.get("2", "")),
        anchor_3=anchors.get(3, anchors.get("3", "")),
        anchor_4=anchors.get(4, anchors.get("4", "")),
        anchor_5=anchors.get(5, anchors.get("5", "")),
        specific_instructions=specific_instructions,
        evidence_pack=evidence_pack,
        reference_section=ref_section,
    )

    grade, backend = await _invoke_anthropic_judge(
        eval_id=eval_id,
        category=category,
        scoring="likert_1_5",
        model=model_name,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_prompt=prompt,
        streaming=streaming,
        trace_context_source=trace_pack.get("trace_context_source", "run_only"),
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="likert_1_5",
                evaluation_method="anthropic_messages_stream" if streaming else "anthropic_messages_create",
                model=model_name,
                streaming_used=streaming,
                trace_context_source=trace_pack.get("trace_context_source", "run_only"),
            )
        },
    )

    score = _normalize_score(
        scoring="likert_1_5",
        grade=grade,
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="likert_1_5",
                evaluation_method="judge_response_parse",
                model=model_name,
                streaming_used=streaming,
                trace_context_source=trace_pack.get("trace_context_source", "run_only"),
            )
        },
    )
    judge_trace = _trace_metadata(
        eval_id=eval_id,
        category=category,
        scoring="likert_1_5",
        evaluation_method=backend.get("evaluation_method", ""),
        model=model_name,
        streaming_used=backend.get("streaming_used", False),
        trace_context_source=trace_pack.get("trace_context_source", "run_only"),
    )
    judge_trace["tools_enabled"] = bool(policy.get("tools_allowed", False))
    judge_trace["token_usage"] = backend.get("token_usage", {})
    judge_trace["stop_reason"] = backend.get("stop_reason")

    return make_result(
        score,
        short_comment(eval_id, grade.get("reasoning", "")),
        reasoning=grade.get("reasoning", ""),
        evidence=grade.get("evidence", []),
        confidence=str(grade.get("confidence", "LOW")),
        flags=[str(flag) for flag in grade.get("flags", [])],
        details={
            "judge_raw": grade,
            "judge_backend": backend,
            "judge_trace": judge_trace,
            "trace_context_source": trace_pack.get("trace_context_source", "run_only"),
            "trace_context_pack": {
                "run_id": trace_pack.get("run_id", ""),
                "trace_id": trace_pack.get("trace_id", ""),
                "fetch_error": trace_pack.get("fetch_error", ""),
            },
        },
    )


@traceable(name="research_binary_judge", run_type="chain")
async def run_binary_judge(
    *,
    eval_id: str,
    eval_name: str,
    pass_criteria: str,
    trace_data: str,
    additional_context: str = "",
    model: str | None = JUDGE_DEFAULT_MODEL,
    run: Any | None = None,
) -> dict:
    """Run a binary Anthropic judge and return LangSmith-compatible result."""
    category = infer_eval_category(eval_id)
    policy = _policy_for_category(category)
    model_name = _judge_model(model)
    streaming = bool(policy.get("streaming", True)) and _judge_streaming_enabled()

    trace_pack = _assemble_trace_context(
        run=run,
        eval_id=eval_id,
        category=category,
        require_full_fetch=bool(policy.get("require_full_trace_fetch", False)),
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="binary_pass_fail",
                evaluation_method="judge_context_assembly",
                model=model_name,
                streaming_used=streaming,
                trace_context_source="unknown",
            )
        },
    )

    evidence_pack = _render_binary_evidence_pack(
        category=category,
        policy=policy,
        trace_pack=trace_pack,
        trace_data=trace_data,
        additional_context=additional_context,
    )
    prompt = BINARY_TRACE_TEMPLATE.format(
        eval_id=eval_id,
        eval_name=eval_name,
        category=category,
        category_template=policy.get("template", ""),
        evidence_strategy=policy.get("evidence_strategy", ""),
        pass_criteria=pass_criteria,
        evidence_pack=evidence_pack,
    )

    grade, backend = await _invoke_anthropic_judge(
        eval_id=eval_id,
        category=category,
        scoring="binary_pass_fail",
        model=model_name,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_prompt=prompt,
        streaming=streaming,
        trace_context_source=trace_pack.get("trace_context_source", "run_only"),
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="binary_pass_fail",
                evaluation_method="anthropic_messages_stream" if streaming else "anthropic_messages_create",
                model=model_name,
                streaming_used=streaming,
                trace_context_source=trace_pack.get("trace_context_source", "run_only"),
            )
        },
    )

    score = _normalize_score(
        scoring="binary_pass_fail",
        grade=grade,
        langsmith_extra={
            "metadata": _trace_metadata(
                eval_id=eval_id,
                category=category,
                scoring="binary_pass_fail",
                evaluation_method="judge_response_parse",
                model=model_name,
                streaming_used=streaming,
                trace_context_source=trace_pack.get("trace_context_source", "run_only"),
            )
        },
    )
    judge_trace = _trace_metadata(
        eval_id=eval_id,
        category=category,
        scoring="binary_pass_fail",
        evaluation_method=backend.get("evaluation_method", ""),
        model=model_name,
        streaming_used=backend.get("streaming_used", False),
        trace_context_source=trace_pack.get("trace_context_source", "run_only"),
    )
    judge_trace["tools_enabled"] = bool(policy.get("tools_allowed", False))
    judge_trace["token_usage"] = backend.get("token_usage", {})
    judge_trace["stop_reason"] = backend.get("stop_reason")

    return make_result(
        score,
        short_comment(eval_id, grade.get("reasoning", "")),
        reasoning=grade.get("reasoning", ""),
        evidence=grade.get("evidence", []),
        confidence=str(grade.get("confidence", "LOW")),
        flags=[str(flag) for flag in grade.get("flags", [])],
        details={
            "judge_raw": grade,
            "judge_backend": backend,
            "judge_trace": judge_trace,
            "trace_context_source": trace_pack.get("trace_context_source", "run_only"),
            "trace_context_pack": {
                "run_id": trace_pack.get("run_id", ""),
                "trace_id": trace_pack.get("trace_id", ""),
                "fetch_error": trace_pack.get("fetch_error", ""),
            },
        },
    )
