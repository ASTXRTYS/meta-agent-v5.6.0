# Agent Skills Allocation

> **Status:** Merged into canonical docs on 2026-04-22 as Q17.  
> **Canonical decision:** [`AD.md` §4 → Per-Agent Skill Allocation (Q17)](./AD.md) and [`DECISIONS.md` → Q17](./DECISIONS.md#q17-per-agent-skill-allocation).  
> This file is retained as companion design-team commentary only. The per-agent allocation table, skill path table, prompt-vs-skill boundary, and rendering-subagent delegation are authoritative in AD/DECISIONS, not here. Do not edit allocations here without updating AD and DECISIONS in the same change.
>
> Companion to `AD.md` §4 Agent Primitives. This document originally specified which skills each agent receives via `skills=[]` on `create_deep_agent()`. The design-team open questions at the bottom remain active and are not closed by Q17.

## Allocation Table

| Agent | Skill | Source | Purpose |
|---|---|---|---|
| **PM** | `doc-coauthoring` | `.agents/skills/anthropic/skills/doc-coauthoring` | Structured document co-authoring workflow (PRDs, eval criteria, stakeholder comms) |
| ~~**PM**~~ | ~~`docx`~~ | ~~`.agents/skills/anthropic/skills/docx`~~ | **Delegated to rendering subagent (not a PM skill)** — per Q17, PM stakeholder-deliverable rendering is owned by a narrowly-scoped rendering subagent outside the seven peer roles. Do not add to PM `skills=[]`. |
| **PM** | `internal-comms` | `.agents/skills/anthropic/skills/internal-comms` | Standardized communication with team and stakeholder (status reports, leadership updates, FAQs, incident reports) |
| ~~**PM**~~ | ~~`pdf`~~ | ~~`.agents/skills/anthropic/skills/pdf`~~ | **Delegated to rendering subagent (not a PM skill)** — per Q17, PM stakeholder-deliverable rendering is owned by a narrowly-scoped rendering subagent outside the seven peer roles. Do not add to PM `skills=[]`. |
| ~~**PM**~~ | ~~`pptx`~~ | ~~`.agents/skills/anthropic/skills/pptx`~~ | **Delegated to rendering subagent (not a PM skill)** — per Q17, PM stakeholder-deliverable rendering is owned by a narrowly-scoped rendering subagent outside the seven peer roles. Do not add to PM `skills=[]`. |
| **PM** | `prompt-architect` | **Custom — to be created** | Prompt engineering and system prompt design for downstream agents |
| **Architect** | `langchain` | `.agents/skills/langchain` | LangChain/LangGraph/Deep Agents SDK reference for design decisions |
| **Architect** | `langsmith` | `.agents/skills/langsmith` | LangSmith tracing and observability patterns for design |
| **Architect** | `web-artifacts-builder` | `.agents/skills/anthropic/skills/web-artifacts-builder` | Multi-component web artifact design patterns |
| **Architect** | `theme-factory` | `.agents/skills/anthropic/skills/theme-factory` | Theming and styling for TUI and artifact design |
| **Architect** | `frontend-design` | `.agents/skills/anthropic/skills/frontend-design` | Frontend interface design for TUI extension |
| **Architect** | `doc-coauthoring` | `.agents/skills/anthropic/skills/doc-coauthoring` | Structured spec document authoring (requirements, design, task docs) |
| **Architect** | `claude-api` | `.agents/skills/anthropic/skills/claude-api` | Anthropic API patterns and Claude-specific model behavior |
| **Architect** | `openai-docs` | `skills/openai-docs` | OpenAI API patterns and GPT-specific model behavior |
| **Planner** | `doc-coauthoring` | `.agents/skills/anthropic/skills/doc-coauthoring` | Structured task document authoring |
| **Developer** | `langsmith` | `.agents/skills/langsmith` | LangSmith tracing integration during development |
| **Developer** | `langchain` | `.agents/skills/langchain` | LangChain/LangGraph SDK patterns for implementation |
| **Developer** | `remember` | `.agents/skills/remember` | Persistent note-taking across development sessions |
| **Evaluator** | `langsmith-evaluator-feedback` | `skills/langsmith/config/skills/langsmith-evaluator-feedback` | Evaluator feedback standard for harness iteration |
| **Evaluator** | `remember` | `.agents/skills/remember` | Persistent note-taking across evaluation sessions |
| **Evaluator** | `playwright` | `skills/playwright` | Browser automation for UI/UX testing |
| **Evaluator** | `webapp-testing` | `skills/webapp-testing` | Local web application interaction and testing |
| **Harness Engineer** | `langsmith-evaluator-feedback` | `skills/langsmith/config/skills/langsmith-evaluator-feedback` | Evaluator feedback standard for harness iteration |
| **Harness Engineer** | `remember` | `.agents/skills/remember` | Persistent note-taking across evaluation experiments |
| **Harness Engineer** | `langsmith` | `.agents/skills/langsmith` | Full LangSmith knowledge — datasets, experiments, tracing, evaluation pipelines |
| **Researcher** | *(none allocated — see open question below)* | | |

## Agent-by-Agent Rationale

### Project Manager (PM)

The PM is the document hub. It assembles PRDs, evaluation criteria, stakeholder packages, and approval documents. The rendering skills (`docx`, `pdf`, `pptx`) enable it to produce the document packages that approval gates require. `internal-comms` establishes a standard for how the PM communicates with both the stakeholder and the team — status reports, decision memos, kickoffs, incident reports. `doc-coauthoring` provides the structured co-authoring workflow for all of the above. `prompt-architect` is a custom skill (to be created) that gives the PM prompt engineering capabilities — the PM needs to be able to craft and refine system prompts for downstream agents as part of the scoping phase.

### Architect

The architect needs the broadest skill set. It must design across the full LangChain ecosystem (`langchain`), understand observability patterns (`langsmith`), design the TUI extension (`frontend-design`, `theme-factory`, `web-artifacts-builder`), author spec documents (`doc-coauthoring`), and understand model behavior from both Anthropic (`claude-api`) and OpenAI (`openai-docs`) to make informed model-specific design decisions.

**Model behavior awareness (baked into system prompt, not a skill):** The architect's system prompt must encode awareness that its primary model knowledge covers:
- Opus 4.6
- ChatGPT 5.4
- GPT 5.4 Pro

If a build is requested for a model outside this set, the architect must request the Researcher to investigate that model's behavior, prompting guidance, and provider documentation before designing for it. This is a behavioral invariant (Q12) — it belongs in the system prompt, not as a skill.

### Planner

The planner receives the architect's design and produces a phased task document. `doc-coauthoring` is sufficient — the planner's output is structured documentation, not code or evaluation.

### Developer

The developer needs SDK reference (`langchain`) for implementation, tracing integration (`langsmith`) for observability during development, and persistent memory (`remember`) for cross-session learning about SDK patterns and prior implementations.

### Evaluator

The evaluator validates code, SDK compliance, and UI/UX. `langsmith-evaluator-feedback` provides the feedback standard for communicating evaluation results back to the optimizer. `playwright` and `webapp-testing` enable the evaluator to spin up frontends, record interactions, and verify UI behavior — critical for TUI acceptance testing. `remember` preserves evaluation learnings across sessions.

### Harness Engineer

The harness engineer owns evaluation science. It needs full LangSmith knowledge (`langsmith`) — datasets, experiments, tracing, evaluation pipelines, run management. `langsmith-evaluator-feedback` provides the feedback standard for communicating harness evaluation results. `remember` preserves experiment results and calibration data across sessions.

**Agentevals SDK knowledge (baked into system prompt, not a skill):** The harness engineer must have full working knowledge of the `agentevals` SDK — `EvaluatorResult`, LLM-as-judge, trajectory scoring, `GraphTrajectory`, tool-call matching. This is deep domain expertise that should be encoded in the system prompt as a behavioral invariant, not delegated to a skill that loads on demand. The harness engineer should *always* have this knowledge active, not progressively disclosed.

The experience the app is supposed to drive is that users can actually see data sets, experiments, etc., all being uploaded to Langsmith directly from their LLM application that is running in the TUI.

### Researcher

No skills allocated yet. The researcher's primary capability is web research and documentation retrieval. The existing `web-research` skill at `.agents/skills/web-research` is a candidate, but the design team should evaluate whether the researcher needs it or whether its research capabilities are better served by tool assignments (e.g., web search tools, documentation fetchers) rather than skills.

## Open Questions for Design Team

1. **Is the researcher's skill allocation sufficient?** Should `web-research` be added? Should the researcher get `remember` for cross-session learning about SDKs and APIs?

2. **Does the developer need more skills?** The developer is a coding agent — should it get `frontend-design` or `web-artifacts-builder` for TUI implementation? Should it get `doc-coauthoring` for code documentation?

3. **Should the planner get `langchain`?** The planner creates development plans that reference specific SDK patterns. Having `langchain` available might improve plan accuracy.

4. **Should the harness engineer get `langchain`?** The harness engineer designs eval harnesses that test LangChain/LangGraph applications. SDK reference could improve harness design.

5. **Custom `prompt-architect` skill — what scope?** The PM needs prompt engineering capabilities. Should this be a skill (progressive disclosure, loaded on demand) or a behavioral invariant baked into the PM's system prompt? If the PM is always crafting prompts as part of scoping, it should be in the prompt, not a skill.

6. **Skill vs. system prompt boundary.** The general principle: if the knowledge must be *always active* (the agent needs it on every call), it belongs in the system prompt as a behavioral invariant. If the knowledge is *on-demand* (the agent invokes it when needed), it belongs as a skill. The design team must evaluate each agent's skill list against this principle — some items above might be better as prompt invariants, and some prompt invariants might be better as skills.

7. **Agentevals SDK for harness engineer — skill or prompt?** The harness engineer needs full `agentevals` knowledge always active. This argues for system prompt inclusion, not progressive disclosure via skill. But `agentevals` is a large API surface. The design team should decide: bake the core patterns into the prompt and create an `agentevals` skill for deep reference on demand?

## Skill Path Reference

All paths are relative to the project root (`/Users/Jason/2026/v4/meta-agent-v5.6.0/`).

| Skill | Path |
|---|---|
| `doc-coauthoring` | `.agents/skills/anthropic/skills/doc-coauthoring/` |
| `docx` | `.agents/skills/anthropic/skills/docx/` |
| `internal-comms` | `.agents/skills/anthropic/skills/internal-comms/` |
| `pdf` | `.agents/skills/anthropic/skills/pdf/` |
| `pptx` | `.agents/skills/anthropic/skills/pptx/` |
| `prompt-architect` | **To be created** — proposed location: `.agents/skills/anthropic/skills/prompt-architect/` |
| `langchain` | `.agents/skills/langchain/` |
| `langsmith` | `.agents/skills/langsmith/` |
| `claude-api` | `.agents/skills/anthropic/skills/claude-api/` |
| `openai-docs` | `skills/openai-docs/` |
| `web-artifacts-builder` | `.agents/skills/anthropic/skills/web-artifacts-builder/` |
| `theme-factory` | `.agents/skills/anthropic/skills/theme-factory/` |
| `frontend-design` | `.agents/skills/anthropic/skills/frontend-design/` |
| `remember` | `.agents/skills/remember/` |
| `langsmith-evaluator-feedback` | `skills/langsmith/config/skills/langsmith-evaluator-feedback/` |
| `playwright` | `skills/playwright/` |
| `webapp-testing` | `skills/webapp-testing/` |
| `web-research` | `.agents/skills/web-research/` |
| `agentevals` | **To be created** — proposed location: `.agents/skills/agentevals/` or baked into HE system prompt |
