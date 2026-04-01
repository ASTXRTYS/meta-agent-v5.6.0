# PM Agent Memory

This file stores persistent memory for the PM agent across sessions.**Last updated: 2026-04-01** — synchronized with codebase after major refactors.

## Critical Self-Awareness

**I am the PM agent of the meta-agent system.** The codebase at the repo root is MY OWN source code — the very harness and agentic architecture that I operate within. When I work on this project, I am working on my own infrastructure.

### My Own Architecture

- **My home directory:** `.agents/pm/` (renamed from `.agents/orchestrator/` in the `7d67d36` refactor)
- **My project artifacts:** `.agents/pm/projects/meta-agent/` (PRD, eval suite, synthetic data, reports)
- **My graph:** `meta_agent/graph.py` → `create_graph()` calls `create_deep_agent()` from Deep Agents SDK; graph name is `"meta-agent-pm"`
- **My server:** `meta_agent/server.py` → `get_agent()` factory for `langgraph.json`
- **My state:** `meta_agent/state.py` → `MetaAgentState` TypedDict, `WorkflowStage` enum (10 stages: INTAKE → PRD_REVIEW → RESEARCH → SPEC_GENERATION → SPEC_REVIEW → PLANNING → PLAN_REVIEW → EXECUTION → EVALUATION → AUDIT)
- **My prompts:** `meta_agent/prompts/` → 12 prompt modules: `pm.py` (composer), `sections.py` (13 base sections), `research_agent.py`, `spec_writer.py`, `verification_agent.py`, `plan_writer.py`, `code_agent.py`, `eval_mindset.py`, `eval_engineering.py`, `eval_approval_protocol.py`, `scoring_strategy.py`, plus `Research_Agent_System_Prompt.md`
- **My tools:** `meta_agent/tools/` → 16 custom @tool functions: `transition_stage`, `record_decision`, `record_assumption`, `request_approval`, `request_eval_approval`, `toggle_participation`, `execute_command`, `langgraph_dev_server`, `langsmith_cli`, `glob`, `grep`, `langsmith_trace_list`, `langsmith_trace_get`, `langsmith_dataset_create`, `langsmith_eval_run`, `propose_evals`, `create_eval_dataset`
- **My middleware:** `meta_agent/middleware/` plus SDK middleware → DynamicSystemPrompt, MetaAgentState, Memory, Skills, SummarizationTool, ToolError (6 explicit, plus SDK auto-attached: TodoList, Filesystem, SubAgent, Summarization, PromptCaching, PatchToolCalls)
- **My subagents:** `meta_agent/subagents/configs.py` → 7 subagents wired via `build_pm_subagents()`: research-agent, spec-writer, plan-writer, code-agent, verification-agent, test-agent, document-renderer. Plus `eval-agent` reserved for future.
- **My evals:** `meta_agent/evals/` → orchestrator evals (phases 0-2) plus dedicated research-eval package under `meta_agent/evals/research/`
- **My skills:** Loaded via `SkillsMiddleware` from 3 dirs: `skills/langchain/config/skills` (11), `skills/langsmith/config/skills` (3), `skills/anthropic/skills` (17). Also cloned into `.agents/skills/` for centralized agent access.

### Current Project Status (as of 2026-04-01)

- **Phases 0, 1, 2:** ✅ COMPLETE on the real Deep Agents SDK (`deepagents==0.4.12`). 471 unit tests pass.
- **Phase 3:** 🔄 ~80% COMPLETE. All three runtime agents (research-agent, verification-agent, spec-writer) are IMPLEMENTED as standalone Deep Agent modules (`meta_agent/subagents/research_agent.py`, `verification_agent_runtime.py`, `spec_writer_agent.py`) and wired into `build_pm_subagents()`. Phase 3 gate evals (7 Layer 1) and eval run function bridge are complete.
- **Phase 3 BLOCKERS:** Development FROZEN pending API funding. A live experiment was run (see "Phase 3 Experimental Findings" below) but exposed critical behavioral issues that require fixes before the research-agent can function as designed.
- **Research eval stack:** IMPLEMENTED and calibrated. 38 canonical evals (37 active + RI-001 deferred), 5 synthetic calibration scenarios, LangSmith experiment harness, markdown report generation, and UI judge profiles under `meta_agent/evals/research/`. Historical frozen calibration baseline: `185/185` pass-fail, `182/185` exact. Must rerun calibration before trusting — measurement contract was repaired after that baseline.
- **Phase 4:** ⏸️ NOT STARTED — Planning + Execution (plan-writer, code-agent with 3 nested sub-agents)
- **Phase 5:** ⏸️ NOT STARTED — End-to-end evaluation + audit UX

### Spec and Plan Documents (In-Repo)

- **Technical Specification:** `Full-Spec.md` (v5.6.1) — in repo root
- **Development Plan:** `Full-Development-Plan.md` — in repo root (has progress tracking)
- **Deviation Record:** `DEVIATION_RECORD.md` — in repo root (22 sections of implementation deviations)

### Existing Datasets

- `meta-agent-phase-0-scaffolding` (15 examples, ID: `835a9b10-371f-413c-99f9-bdc19e2c4c25`)
- `meta-agent-phase-1-orchestrator` (18 examples, ID: `70f34716-7d60-4042-a565-c086b063809d`)
- `meta-agent-phase-2-intake-prd` (11 scenarios, ID: `b7c0535f-c17f-48bd-8663-e2dda2bd8f07`)
- Phase 2 synthetic data: `datasets/phase-2-synthetic-data.yaml`
- Research eval seed artifacts: `.agents/pm/projects/meta-agent/` with runtime expansion into 5 calibration scenarios via `meta_agent.evals.research.synthetic_trace_adapter`
- Research eval suite: `.agents/pm/projects/meta-agent/evals/eval-suite-prd.json`
- Research synthetic dataset: `.agents/pm/projects/meta-agent/datasets/synthetic-research-agent.json`

### Phase 3 Experimental Findings (2026-03-30)

A live experiment was run but cut off before the research phase completed. Critical behavioral issues were discovered:

- **Trace ID:** `019d404a-8275-7cb3-81a7-4bc166c13cb1` (LangSmith)
- **PRD used:** `.agents/pm/projects/meta-agent/artifacts/intake/research-agent-prd.md`
- **Skills misuse:** Research-agent did 78 brute-force `read_file` calls through `/skills/` instead of using SkillsMiddleware's pre-loaded skills
- **No web research:** 0 `web_search` calls, 0 `web_fetch` calls — agent stuck in filesystem exploration
- **Minimal delegation:** Only 2 `task` calls vs expected intentional multi-agent topology
- **Middleware broken:** DynamicSystemPromptMiddleware not firing correctly for stage-aware prompts
- **PRD decomposition failed:** Agent couldn't translate PRD into actionable research agenda
- **Root cause analysis:** See `DEVIATION_RECORD.md` Section 21 for detailed analysis of why the measurement stack rewarded incorrect behaviors

These issues must be fixed before Phase 3 can complete. The architectural foundation exists but behavioral fixes are required.

## Research Agent: Design Decisions & Artifacts (Phase 3) — RESOLVED

All design decisions below were resolved during the PRD → Evals → Synthetic Data cycle. The eval stack is built and calibrated. The runtime agents are implemented. The remaining work is behavioral fixes exposed by the live experiment (see "Phase 3 Experimental Findings" above).

### User (Jason) Requirements for Research Agent

1. **Hierarchy:** Research agent sits below PM (me), above spec-writer
2. **Specialization:** LangChain, LangGraph, Deep Agents ecosystem — EVERYTHING related
3. **Skills:** Use LangChain-maintained skills (cloned into `/skills/` and `.agents/skills/`)
4. **Sources:** LangChain docs website, API reference, tweets/blogs from LangChain employees
5. **Twitter handles:** Jason will provide specific handles for individuals to track
6. **Anthropic model research:** Full capability matrices including pricing, rate limits (NOT latency benchmarks, NOT multimodal — we use Opus 4.6 frontier)
7. **Web access:** Uses native Opus 4.6 web_fetch / web_search tools (registered as server-side tools in subagent config)
8. **Output:** Research bundle with fixed-but-flexible 17-section schema (v5.6.1), ALWAYS with citations
9. **Depth:** SOTA deep researcher — full breadth (zero blind spots), deep dives on promising options
10. **PRD decomposition:** MUST read PRD + evals, decompose into research brief, then systematically research each topic
11. **Spec-writer feedback loop:** Spec-writer can request more targeted research if insufficient
12. **Broken signals:** Hallucination, no citations, surface-level research, didn't decompose PRD, didn't satisfy all PRD topics

### Key Decisions (All Locked)

- Web fetching via web_fetch/web_search tools — not pre-indexed
- Twitter individuals provided as config, not discovered by agent
- Agent reports capabilities for spec-writer to decide (not agent making arch decisions)
- Fixed-but-flexible research bundle schema with mandatory citations
- Agent must consider evals when doing research (not just PRD)
- ALL Likert thresholds at >= 4.0 — SOTA bar
- Sub-agent delegation is MANDATORY with intentional topology reasoning
- HITL gate for research clusters before deep-diving
- ALL Likert evals have full 1-5 anchored rubrics (no bare scales)
- Eval suite format: JSON (not YAML) — `eval-suite-prd.json` for LangSmith
- Synthetic datasets: JSON — LangSmith-compatible with `inputs`/`outputs`/`metadata`
- Three required INTAKE exit artifacts: PRD (.md), eval suite (.json), synthetic dataset (.json)
- Total research evals: 38 (20 binary + 18 Likert)

### Synthetic Data — All 6 Stages COMPLETE

- Stage 1 (PRD + eval suite input): APPROVED
- Stage 2 (decomposition file): APPROVED — 9 domains, PRD line citations
- Stage 3 (skill interactions): APPROVED — 12 skills, 3 corrections
- Stage 4 (sub-agent delegation): REVISED — intentional topology reasoning
- Stage 5 (HITL cluster): APPROVED — 3 clusters, 16 targets
- Stage 6 (research bundle): COMPLETED — 13 sections, full citations

### Workflow

- Standard for each agent: PRD → Evals → Synthetic Data → Implementation
- **NEXT AFTER RESEARCH AGENT BEHAVIORAL FIXES:** Backtrack and overhaul PM eval suite (Jason's directive)

## Directory Convention Reminder

The `.agents/` directory follows this convention (per `7d67d36` refactor):

```
.agents/
├── pm/                    # MY home directory (was "orchestrator")
│   ├── AGENTS.md          # THIS FILE — my persistent memory
│   └── projects/
│       └── meta-agent/    # Current project artifacts
│           ├── artifacts/intake/research-agent-prd.md
│           ├── artifacts/research/research-decomposition.md
│           ├── datasets/synthetic-research-agent.json
│           ├── evals/eval-suite-prd.json
│           └── evals/reports/  # Eval run reports
├── research-agent/AGENTS.md
├── spec-writer/AGENTS.md
├── verification-agent/AGENTS.md
├── plan-writer/AGENTS.md
├── code-agent/AGENTS.md
├── test-agent/AGENTS.md
├── document-renderer/AGENTS.md
└── skills/                # Cloned skill repos for all agents
    ├── langchain/
    ├── langsmith/
    └── anthropic/
```