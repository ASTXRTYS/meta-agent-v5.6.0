"""Rubric anchors and per-eval specific instructions loaded from eval-suite-prd.json.

Anchors are loaded at import time from the canonical eval suite JSON.
Specific instructions are the detailed judge guidance blocks that get injected
into the LLM judge prompt template — these are the only hand-authored data here.
"""

from __future__ import annotations

from typing import Any

from meta_agent.evals.research.common import (
    RESEARCH_BUNDLE_FRONTMATTER_FIELDS,
    RESEARCH_BUNDLE_REQUIRED_SECTIONS,
    format_fr_checklist,
    load_eval_suite,
)

# ---------------------------------------------------------------------------
# Load anchors from the canonical eval suite JSON
# ---------------------------------------------------------------------------
_EVAL_SUITE: dict[str, Any] = load_eval_suite()
_ANCHORS_BY_ID: dict[str, dict] = {}
for _ev in _EVAL_SUITE.get("evals", []):
    if "anchors" in _ev:
        _ANCHORS_BY_ID[_ev["id"]] = {
            int(k) if str(k).isdigit() else k: v
            for k, v in _ev["anchors"].items()
        }


def get_anchors(eval_id: str) -> dict:
    """Get Likert anchors for an eval from the JSON suite."""
    return _ANCHORS_BY_ID.get(eval_id, {})


def get_eval_meta(eval_id: str) -> dict:
    """Get full eval metadata from the JSON suite."""
    for ev in _EVAL_SUITE.get("evals", []):
        if ev["id"] == eval_id:
            return ev
    return {}


# ---------------------------------------------------------------------------
# Per-eval specific instructions (hand-authored judge guidance)
# These are NOT in the JSON — they are the detailed evaluation prompts
# that tell the LLM judge exactly what to look for.
# ---------------------------------------------------------------------------
SPECIFIC_INSTRUCTIONS: dict[str, str] = {

    "RINFRA-003": (
        "WHAT TO EVALUATE: The structural completeness and content quality of the research bundle.\n\n"
        f"REQUIRED YAML FRONTMATTER FIELDS: {', '.join(RESEARCH_BUNDLE_FRONTMATTER_FIELDS)}.\n\n"
        f"REQUIRED SECTIONS (13): {', '.join(RESEARCH_BUNDLE_REQUIRED_SECTIONS)}.\n\n"
        "LOOK FOR:\n"
        "- Are all 13 required sections present as distinct H2 headings?\n"
        "- Is the YAML frontmatter complete and aligned to the research-bundle contract?\n"
        "- Does each section have substantive content (not just a title or one-liner)?\n"
        "- Are sections internally structured with sub-headings, tables, or lists?\n\n"
        "RED FLAGS (score <= 2): Missing frontmatter fields; missing more than 3 required sections; flat structure with no sub-headings.\n\n"
        "SCORE-4 MINIMUM: All 13 sections present with multi-paragraph content; frontmatter complete; at least 8 sections have sub-structure."
    ),

    "RINFRA-004": (
        "WHAT TO EVALUATE: The structural and presentational quality of citations.\n\n"
        "LOOK FOR:\n"
        "- Do findings include URLs or specific references?\n"
        "- Are source types distinguished (docs vs tweet vs API ref vs source code)?\n"
        "- Do citations point to specific pages, not just homepages?\n"
        "- Are citations contextualized (not just appended)?\n\n"
        "RED FLAGS (score <= 2): Findings with no citations; generic 'from docs' references.\n\n"
        "SCORE-4 MINIMUM: 80%+ of findings have specific URLs; source types clearly labeled."
    ),

    "RQ-001": (
        "WHAT TO EVALUATE: The agent's PRD decomposition file.\n\n"
        "LOOK FOR:\n"
        "- Does the file identify distinct research domains? Count them.\n"
        "- Does each domain cite specific PRD line numbers or section references?\n"
        "- Are research questions specific and actionable (not generic)?\n"
        "- Is there a priority ordering with rationale?\n"
        "- Does the decomposition account for cross-cutting concerns?\n"
        "- Is there a progress-tracking mechanism?\n\n"
        "RED FLAGS (score <= 2): No decomposition file; vague domains; no PRD line references.\n\n"
        "SCORE-4 MINIMUM: At least 7 distinct domains; 80%+ of PRD FRs mapped; PRD line citations present."
    ),

    "RQ-002": (
        "WHAT TO EVALUATE: Breadth of ecosystem options discovered.\n\n"
        "LOOK FOR:\n"
        "- Coverage across all PRD functional requirement areas\n"
        "- Multiple options per domain (not just one obvious choice)\n"
        "- Non-obvious alternatives (niche libraries, community forks)\n"
        "- Coverage of adjacent concerns (safety, observability, deployment)\n\n"
        "RED FLAGS (score <= 2): Only 2-3 broad topics; entire FR areas unaddressed.\n\n"
        "SCORE-4 MINIMUM: Every PRD functional requirement area has research; at least 2 options per major decision.\n\n"
        f"CURRENT PRD FR CHECKLIST:\n{format_fr_checklist()}"
    ),

    "RQ-003": (
        "WHAT TO EVALUATE: Depth of research approach.\n\n"
        "LOOK FOR in the trace and bundle:\n"
        "- Did agent read API references (not just tutorials)?\n"
        "- Did agent examine source code?\n"
        "- Did agent find trade-offs and limitations?\n"
        "- Did agent identify undocumented behaviors or real-world patterns?\n\n"
        "RED FLAGS (score <= 2): Only tutorials and landing pages fetched.\n\n"
        "SCORE-4 MINIMUM: API references examined; source code or architecture docs read; trade-offs identified."
    ),

    "RQ-004": (
        "WHAT TO EVALUATE: Whether cited content accurately represents sources.\n\n"
        "LOOK FOR:\n"
        "- Do URLs appear real and specific?\n"
        "- Are claims attributed to the correct sources?\n"
        "- Are paraphrases faithful to the likely source content?\n"
        "- Are caveats and nuances preserved?\n\n"
        "NOTE: You cannot re-fetch URLs. Assess plausibility given the cited source type.\n\n"
        "RED FLAGS (score <= 2): Claims with no citation; attributions to wrong sources.\n\n"
        "SCORE-4 MINIMUM: Specific URLs cited; claims plausible given source type; source types identified.\n\n"
        "IMPORTANT: When citation verification evidence is unavailable, score conservatively and flag missing verification."
    ),

    "RQ-005": (
        "WHAT TO EVALUATE: Whether a spec-writer could make ALL architectural decisions from this bundle alone.\n\n"
        "EVALUATE AS IF YOU ARE THE SPEC-WRITER:\n"
        "- Can I choose an orchestration framework? Are tradeoffs clear?\n"
        "- Can I design the state model? Are persistence options compared?\n"
        "- Can I specify the tool system?\n"
        "- Can I design HITL flows?\n"
        "- Can I write system prompts? Are model capabilities known?\n"
        "- Can I design the eval strategy?\n"
        "- Do I know what to avoid? Are rejected alternatives documented?\n\n"
        "RED FLAGS (score <= 2): Reads like documentation summaries; no comparative analysis.\n\n"
        "SCORE-4 MINIMUM: Every PRD functional requirement area has researched options with tradeoffs; 80%+ decisions can be made confidently."
    ),

    "RQ-006": (
        "WHAT TO EVALUATE: Quality of SME perspective gathering.\n\n"
        "SPECIFIED SMEs: @hwchase17, @Vtrivedy10, @sydneyrunkle, @masondrxy, @BraceSproul, @RLanceMartin\n\n"
        "LOOK FOR:\n"
        "- How many of the 6 handles were consulted?\n"
        "- Were specific relevant tweets/posts found (not just profile pages)?\n"
        "- Are SME insights connected to technical findings?\n\n"
        "RED FLAGS (score <= 2): Only profile pages fetched; 4+ handles ignored.\n\n"
        "SCORE-4 MINIMUM: 4+ handles consulted; relevant content found; perspectives connected to research."
    ),

    "RQ-007": (
        "WHAT TO EVALUATE: Whether the agent triggered the right skills at the right time.\n\n"
        "AVAILABLE SKILLS (14): framework-selection, deep-agents-core, deep-agents-memory, "
        "deep-agents-orchestration, langchain-fundamentals, langchain-middleware, langchain-rag, "
        "langgraph-fundamentals, langgraph-persistence, langgraph-human-in-the-loop, "
        "langchain-dependencies, langsmith-trace, langsmith-dataset, langsmith-evaluator\n\n"
        "LOOK FOR:\n"
        "- Were skills triggered BEFORE web research on the same topic?\n"
        "- Did the skill choice match the current research domain?\n"
        "- Were trigger decisions explained?\n\n"
        "SCORE-4 MINIMUM: Skills triggered for 80%+ of applicable research questions; timing is logical."
    ),

    "RQ-008": (
        "WHAT TO EVALUATE: Whether agent reflected on and internalized skill content.\n\n"
        "LOOK FOR in skill interaction records:\n"
        "- Is there a 'reflection' or 'internalization' for each skill read?\n"
        "- Does reflection connect skill content to specific PRD requirements?\n"
        "- Does internalization distinguish 'now known' vs 'still need to research'?\n\n"
        "SCORE-4 MINIMUM: Reflection present for 80%+ of skills; explicit PRD connections."
    ),

    "RQ-009": (
        "WHAT TO EVALUATE: Whether skill findings influenced research direction.\n\n"
        "LOOK FOR:\n"
        "- Did agent change research plan after reading a skill?\n"
        "- Did skill findings cause agent to drop or prioritize certain topics?\n"
        "- Is there temporal evidence: skill read -> research direction change?\n\n"
        "SCORE-4 MINIMUM: Observable direction change after skill reading for 3+ skills."
    ),

    "RQ-010": (
        "WHAT TO EVALUATE: Quality of sub-agent task delegation.\n\n"
        "LOOK FOR in trace:\n"
        "- How many sub-agents were spawned?\n"
        "- Is there topology reasoning (why this grouping)?\n"
        "- Are task briefs specific (research questions, not just domain names)?\n"
        "- Were alternative topologies considered?\n\n"
        "SCORE-4 MINIMUM: 3+ sub-agents with reasoned grouping; specific task briefs; rationale documented."
    ),

    "RQ-011": (
        "WHAT TO EVALUATE: How well sub-agent findings were synthesized.\n\n"
        "LOOK FOR:\n"
        "- Is the bundle organized around PRD requirements (not around sub-agents)?\n"
        "- Are cross-cutting patterns identified?\n"
        "- Are contradictions resolved with reasoning?\n"
        "- Does the synthesis produce emergent insights?\n\n"
        "SCORE-4 MINIMUM: Findings reorganized by topic; cross-cutting patterns identified; contradictions resolved."
    ),

    "RQ-012": (
        "WHAT TO EVALUATE: Quality of the HITL research cluster presentation.\n\n"
        "LOOK FOR:\n"
        "- Are research targets grouped into themed clusters?\n"
        "- Does each target explain what will be investigated and why?\n"
        "- Is there a connection to PRD requirements?\n"
        "- Can the user understand the research strategy from this presentation?\n\n"
        "SCORE-4 MINIMUM: Targets grouped by theme; each has expected insight; PRD relevance stated."
    ),

    "RQ-013": (
        "WHAT TO EVALUATE: Gap and contradiction identification and remediation.\n\n"
        "LOOK FOR:\n"
        "- Are gaps explicitly identified in the bundle?\n"
        "- Is there root cause analysis for contradictions?\n"
        "- Was additional research done to resolve gaps?\n"
        "- Are unresolvable gaps flagged with recommended approaches?\n\n"
        "SCORE-4 MINIMUM: Gaps identified with root causes; verification attempted; evidence provided."
    ),

    "RR-001": (
        "WHAT TO EVALUATE: Reflection quality at decision points.\n\n"
        "DECISION POINTS TO CHECK (minimum):\n"
        "- After reading the PRD\n"
        "- After reading each skill\n"
        "- After each sub-agent returns findings\n"
        "- Before writing the research bundle\n"
        "- When encountering contradictory information\n\n"
        "LOOK FOR: Does agent articulate WHAT it learned, WHY it chose the next action, what is known vs unknown?\n\n"
        "SCORE-4 MINIMUM: Reflection at each major decision point with learning and rationale."
    ),

    "RR-002": (
        "WHAT TO EVALUATE: Whether the agent builds connections across different sources.\n\n"
        "LOOK FOR:\n"
        "- Are docs cross-referenced with API references?\n"
        "- Are SME opinions validated against official docs?\n"
        "- Are skill findings connected to web research findings?\n"
        "- Are contradictions between sources identified and analyzed?\n\n"
        "SCORE-4 MINIMUM: Systematic cross-referencing between source types; convergence/divergence noted."
    ),

    "RR-003": (
        "WHAT TO EVALUATE: Whether the agent adjusts research direction based on discoveries.\n\n"
        "LOOK FOR:\n"
        "- Did agent abandon dead-end research paths?\n"
        "- Did agent revisit assumptions after new findings?\n"
        "- Did agent reprioritize based on what it learned?\n"
        "- How quickly did course corrections happen?\n\n"
        "SCORE-4 MINIMUM: Observed course correction within 2 tool calls of recognizing a dead end."
    ),
}


# ---------------------------------------------------------------------------
# Unified lookup: combines JSON anchors with hand-authored instructions
# ---------------------------------------------------------------------------
RESEARCH_EVAL_RUBRICS: dict[str, dict] = {}

for _eval_id, _instructions in SPECIFIC_INSTRUCTIONS.items():
    RESEARCH_EVAL_RUBRICS[_eval_id] = {
        "anchors": get_anchors(_eval_id),
        "specific_instructions": _instructions,
    }

# Also populate entries for evals that have anchors in JSON but no
# special instructions (they'll use the JSON description as fallback)
for _ev in _EVAL_SUITE.get("evals", []):
    if _ev["id"] not in RESEARCH_EVAL_RUBRICS and "anchors" in _ev:
        RESEARCH_EVAL_RUBRICS[_ev["id"]] = {
            "anchors": _ANCHORS_BY_ID.get(_ev["id"], {}),
            "specific_instructions": f"Evaluate: {_ev.get('description', _ev.get('title', ''))}",
        }
