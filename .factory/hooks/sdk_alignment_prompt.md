---
name: "SDK Alignment & Skill Review Before Spec Work"
description: "This workspace enforces SDK alignment as a mandatory prerequisite before any technical engagement. Whether you are scoping requirements, authoring design documents, implementing features, debugging issues, refactoring code, or collaborating with the user on approach, you must first internalize the relevant skill files and canonical SDK references. This ensures architectural consistency, prevents the introduction of ad-hoc patterns that conflict with established conventions, and maintains the integrity of the codebase's design philosophy."
version: "1"
---

Before writing a single line of code or spec, you must first understand what the user is actually trying to accomplish and which SDK conventions apply to *this specific request*.

**Step 1: Parse intent before touching any files**
Articulate in 2-3 sentences: What is the user trying to build, fix, or decide? What are the implicit constraints? What would "success" look like for this specific request? Do not proceed until you can answer this.

**Step 2: Select relevant skills based on intent (not habit)**
Based on your intent analysis, determine which skill files are actually relevant:
- Does this involve any abstraction related to Langchain? -> `.agents/skills/langchain/config/AGENTS.md`
- Does this involve writing any LangGraph code, such as state graph, state schemas, nodes, edges, commands, send, invoke, streaming, and error handling? -> `.agents/skills/langchain/config/skills/langgraph-fundamentals/SKILL.md`
- Does this involve the Claude API or Anthropic SDK? -> `.agents/skills/anthropic/skills/claude-api/SKILL.md`
- Does this involve or mention deep agents or create_deep_agent? -> `.agents/skills/deepagents`
- **Important:** Do NOT read skills that don't apply to this specific request. Targeted research beats breadth.

**Step 3: Study with interleaved thinking**
As you read each skill file, pause after every major section and explicitly connect it back to the user's request:
- "The user wants to build X; this skill says we should do Y; does Y apply here?"
- "The user mentioned Z; the SDK recommends W; is W compatible with Z?"
- If a section doesn't apply, skip it and say why.
- If you're confused, re-read before proceeding.

**Step 4: Articulate your SDK alignment checkpoint**
Before writing any spec or code, state explicitly:
1. Which skills you studied and why they apply to THIS request
2. Which SDK conventions will govern your approach
3. Why your planned imports/architecture align with those conventions

**Step 5: Escalate to canonical SDK sources when confidence is below 95%**
You have **zero excuse** for guessing or implementing custom logic that drifts from the SDK. The following canonical references exist **locally** in this workspace—no external lookups required:

| If you need clarity on... | Consult this canonical source |
|---------------------------|------------------------------|
| Deep Agents SDK (`create_deep_agent()`, middleware, backends, harness architecture) | `.reference/libs/deepagents/deepagents/` or `.venv/lib/python3.11/site-packages/deepagents/` |
| Production Deep Agent patterns (state-of-the-art coding assistant implementation) | `.reference/libs/cli/deepagents_cli/` |
| LangGraph (StateGraph, state schemas, nodes, edges, Command, Send, invoke, streaming, error handling, persistence) | `.venv/lib/python3.11/site-packages/langgraph/` |
| LangGraph API server internals | `.venv/lib/python3.11/site-packages/langgraph_api/` |
| LangGraph SDK client patterns | `.venv/lib/python3.11/site-packages/langgraph_sdk/` |
| LangSmith (tracing, evaluations, datasets, run management) | `.venv/lib/python3.11/site-packages/langsmith/` |
| Agent evaluation harnesses (`agentevals` SDK for scoring and rubrics) | `.venv/lib/python3.11/site-packages/agentevals/` |
| LangChain Anthropic integration (ChatAnthropic, Claude-specific patterns) | `.venv/lib/python3.11/site-packages/langchain_anthropic/` |
| LangChain OpenAI integration | `.venv/lib/python3.11/site-packages/langchain_openai/` |
| Core LangChain patterns | `.venv/lib/python3.11/site-packages/langchain/` |

**Mandatory escalation rule:** If you are below **95% confident** about any of the following after reading skills, you MUST consult the relevant canonical SDK reference above before proceeding, EX:
- Import syntax or available exports
- Middleware behavior or configuration options
- Correct harness initialization patterns
- API parameter names or types
- Whether the SDK already solves the problem you're about to hand-roll

**Elegance checkpoint:** Even if you are technically confident, consult the canonical reference if you want to ensure your approach is elegant, idiomatic, and won't need revisiting. Production-grade code follows SDK patterns precisely—not approximately.

**Stop if:** You find yourself thinking "I'll just read all the skills to be safe" — this means you're not parsing intent. Go back to Step 1.

**Hard stop if:** You find yourself writing custom logic to solve a problem the SDK already handles. The canonical references above contain the correct pattern. Use them.
