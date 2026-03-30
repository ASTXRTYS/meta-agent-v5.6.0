# Orchestrator Agent Memory

This file stores persistent memory for the orchestrator/PM agent across sessions.

---

## Critical Self-Awareness (2025-07-17)

**I am the PM/orchestrator agent of the meta-agent system.** The codebase at `/` is MY OWN source code — the very harness and agentic architecture that I operate within. When I work on this project, I am working on my own infrastructure.

### My Own Architecture
- **My graph:** `meta_agent/graph.py` → uses `create_deep_agent()` from Deep Agents SDK
- **My server:** `meta_agent/server.py` → `get_agent()` factory for `langgraph.json`
- **My state:** `meta_agent/state.py` → `MetaAgentState` TypedDict, `WorkflowStage` enum
- **My prompts:** `meta_agent/prompts/` → 16 prompt sections, stage-aware composition
- **My tools:** `meta_agent/tools/` → 14+ custom @tool functions
- **My middleware:** `meta_agent/middleware/` plus configured SDK middleware → DynamicSystemPrompt, MetaAgentState, SummarizationTool, Memory, ToolError
- **My subagents:** `meta_agent/subagents/configs.py` → 8 subagent configurations
- **My evals:** `meta_agent/evals/` → orchestrator evals plus a dedicated research-eval package under `meta_agent/evals/research/`
- **My spec (source of truth):** `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Spec.md`

### Current Project Status
- **Phases 0, 1, 2:** COMPLETE on the real Deep Agents SDK (`deepagents==0.4.12`).
- **Research eval stack:** IMPLEMENTED and calibrated ahead of the runtime agent. Canonical 38 evals, 5 synthetic scenarios, LangSmith experiment harness, and UI judge profiles now live under `meta_agent/evals/research/`.
- **Frozen calibration baseline:** `185/185` pass-fail agreement and `182/185` exact agreement on the synthetic calibration set.
- **Phase 3 runtime status:** Research-agent runtime is NOT built yet. The next runtime work remains research-agent, verification-agent, and spec-writer implementation.
- **Phase 4:** Planning + Execution (plan-writer, code-agent)
- **Phase 5:** End-to-end evaluation + audit UX still needs a more user-friendly orchestrator workflow

### Existing Datasets
- `meta-agent-phase-0-scaffolding` (15 examples, ID: `835a9b10-371f-413c-99f9-bdc19e2c4c25`)
- `meta-agent-phase-1-orchestrator` (18 examples, ID: `70f34716-7d60-4042-a565-c086b063809d`)
- `meta-agent-phase-2-intake-prd` (11 scenarios, ID: `b7c0535f-c17f-48bd-8663-e2dda2bd8f07`)
- Phase 2 synthetic data file: `/datasets/phase-2-synthetic-data.yaml`
- Research eval seed artifacts: `/workspace/projects/meta-agent/` with runtime expansion into 5 calibration scenarios via `meta_agent.evals.research.synthetic_trace_adapter`

---

## Current Work: Research Agent PRD, Evals & Synthetic Datasets (Phase 3)

### User (Jason) Requirements for Research Agent
1. **Hierarchy:** Research agent sits below PM/orchestrator (me), above spec-writer
2. **Specialization:** LangChain, LangGraph, Deep Agents ecosystem — EVERYTHING related
3. **Skills:** Use LangChain-maintained skills (cloned from github repos into `/skills/`)
4. **Sources:** LangChain docs website, API reference, tweets/blogs from LangChain employees
5. **Twitter handles:** Jason will provide specific handles for individuals to track
6. **Anthropic model research:** Full capability matrices including pricing, rate limits (NOT latency benchmarks, NOT multimodal — we use Opus 4.6 frontier)
7. **Web access:** Uses native Opus 4.6 web_fetch / tool_as_code capabilities
8. **Output:** Research bundle with fixed-but-flexible schema, ALWAYS with citations (source: docs, tweet, API ref, etc.)
9. **Depth:** SOTA deep researcher — full breadth (zero blind spots), deep dives on promising options
10. **PRD decomposition:** MUST read PRD + evals, decompose into research brief, then systematically research each topic
11. **Spec-writer feedback loop:** Spec-writer can request more targeted research if insufficient
12. **Broken signals:** Hallucination, no citations, surface-level research, didn't decompose PRD, didn't satisfy all PRD topics

### Key Decisions Made
- Web fetching via native Opus 4.6 tools (web_fetch, web_search) — not pre-indexed
- Twitter individuals provided as config, not discovered by agent
- Agent reports capabilities for spec-writer to decide (not agent making arch decisions)
- Fixed-but-flexible research bundle schema with mandatory citations
- Agent must consider evals when doing research (not just PRD)

### Workflow Established
- Jason and I will work hand-in-hand on eval design and synthetic dataset curation
- This is the standard workflow for each agent we build: PRD → Evals → Synthetic Data → Implementation

### Upcoming Work Queue
- **NEXT AFTER RESEARCH AGENT:** Backtrack and overhaul PM/orchestrator eval suite (Jason's directive)
- Spec file should be in workspace — search for it if not found in current session

### Eval Design Decisions (Round 2 — User Feedback)
- **Two new categories added:** RESEARCH-STATE (what's in agent state, binary debug evals) and RESEARCH-REASONING (LLM-as-judge on agent thought quality)
- **RINFRA-003/004:** Upgraded from Binary → Likert 1-5 (quality gradient matters)
- **RB-005 (hallucination):** Now includes content re-fetching, not just URL cross-reference
- **RQ-001 (PRD decomposition):** Agent MUST persist decomposition to a file with PRD line citations
- **New evals:** Dedicated Twitter/SME consultation eval (Likert), dedicated Skills usage eval
- **SOP:** ALL Likert evals must have fully described anchors for every score level — no bare 1-5 scales ever

### Eval Design Decisions (Round 3 — User Feedback)
- **ALL Likert thresholds elevated to >= 4.0** — no eval passes at 3.5; SOTA agent requires SOTA bar
- **Skills lifecycle evals (RQ-007/008/009):** Approved. RQ-008 strengthened to penalize shallow reading
- **HITL gate for research clusters:** Agent must present grouped research targets + rationale before deep-diving; user approves; primarily for debuggability
- **Sub-agent delegation is MANDATORY:** Research agent orchestrates sub-agents for parallel research; cannot do everything as a single agent
  - New evals needed: delegation quality, parallel execution, findings aggregation, synthesis
  - Architecture: main agent decomposes PRD → delegates to sub-agents → sub-agents return raw findings → main agent synthesizes into research bundle
- **Anchors locked in:** RINFRA-003, RINFRA-004, RQ-001, RQ-002, RQ-003, RQ-004, RQ-007, RQ-008, RQ-009
- **Anchors still needed:** RQ-005, RQ-006, RR-001, RR-002, RR-003, plus new sub-agent/HITL evals

### Eval Design Decisions (Round 4 — User Feedback)
- **RQ-010 revised:** Sub-agent delegation must show INTENTIONAL topology reasoning — agent articulates why each sub-agent exists, what it uniquely contributes, why N was chosen over N-1 or N+1
- **RQ-013 added:** Gap/contradiction remediation quality — identify → root cause → plan → execute → resolve
- **ALL Likert anchors now defined:** 18 total Likert evals with full 1-5 anchored rubrics
- **Synthetic data strategy:** GOLDEN-PATH (score 5) + BRONZE-PATH (score 2) only — two calibration poles sufficient for initial LLM-as-judge validation. Additional scenarios deferred.
- **Total evals: 38** (20 binary + 18 Likert)

### GOLDEN-PATH Synthetic Data — Stages Completed
- Stage 1 (PRD + eval suite input): APPROVED — uses actual meta-agent PRD
- Stage 2 (decomposition file): APPROVED — 9 domains, PRD line citations, phased execution
- Stage 3 (skill interactions): APPROVED — 12 skills, 3 corrections applied re: create_deep_agent, sub-agent isolation, return types
- Stage 4 (sub-agent delegation): REVISED — intentional topology reasoning (5 options evaluated) + gap/contradiction remediation cycle (5 items identified, 2 resolved analytically, 3 deferred to deep-dive)
- Stage 5 (HITL cluster): APPROVED — 3 themed clusters, 16 targets, risk assessment
- Stage 6 (research bundle): COMPLETED — 13 sections, all domains, full citations, SME perspectives, risks, unresolved questions

### FORMAT CORRECTION (System Prompt Update)
- **Eval suite MUST be JSON** (not YAML) — `eval-suite-prd.json` for direct LangSmith upload
- **Synthetic datasets MUST be JSON** — LangSmith-compatible schema with `inputs`/`outputs`/`metadata`
- **Three required INTAKE exit artifacts:** PRD (.md), eval suite (.json), synthetic dataset (.json)
- YAML working files in /datasets/golden-path/ and /datasets/bronze-path/ are drafts — must be transformed to JSON final deliverables
- Phase 2 used YAML (`/datasets/phase-2-synthetic-data.yaml`) but going forward all datasets are JSON
