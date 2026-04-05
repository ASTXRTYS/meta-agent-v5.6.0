---
artifact: research-decomposition
project_id: meta-agent-research-agent
title: "Research Agent — PRD Decomposition & Research Agenda"
version: "1.0.0"
status: in_progress
stage: RESEARCH
authors:
  - research-agent
lineage:
  - /.agents/pm/projects/meta-agent/artifacts/intake/research-agent-prd.md
  - /.agents/pm/projects/meta-agent/evals/eval-suite-prd.json
---

# Research Decomposition

## 1. PRD–Eval Bidirectional Map

### 1.1 PRD Functional Requirements → Eval Coverage

| FR ID | FR Name | PRD Lines | Primary Evals | Eval-Implied Constraints |
|-------|---------|-----------|---------------|--------------------------|
| FR-A | PRD & Eval Suite Consumption | 106–111 | RB-001, RB-002, RS-001, RS-002 | Must read FULL PRD (not truncated); must factor eval criteria into agenda |
| FR-B | Research Decomposition | 112–121 | RB-003, RQ-001 | Must include exact PRD line citations; must have progress tracker; persist as MD file |
| FR-C | Skills Utilization | 122–128 | RB-007, RQ-007, RQ-008, RQ-009 | Must read skills in FULL (not first 100 lines); skills must observably influence research direction |
| FR-D | Sub-Agent Delegation | 129–135 | RB-008, RB-009, RB-010, RQ-010 | Must execute in PARALLEL; must reason about topology; task briefs must include baseline knowledge |
| FR-E | SME Consultation | 136–140 | RQ-006 | Must consult ALL 6 handles; must contextualize with technical findings |
| FR-F | Anthropic Model Research | 141–148 | RB-006 | Must cover capability matrix, pricing, rate limits, tool_as_code, langchain-anthropic; must NOT research latency/multimodal unless PRD requires |
| FR-G | Citation & Source Tracking | 149–155 | RB-005, RINFRA-004, RQ-004 | Every cited URL MUST appear in trace as web_fetch; citations re-fetched for accuracy; no hallucinated sources |
| FR-H | Gap & Contradiction Remediation | 156–165 | RQ-013 | Must diagnose root causes; must prioritize by downstream impact; must persist remediation log |
| FR-I | HITL Research Clusters | 166–173 | RB-011, RQ-012 | Must fire BEFORE deep-dive; must include estimated effort; must tie to PRD requirements |
| FR-J | Research Bundle Output | 174–180 | RINFRA-001, RINFRA-002, RINFRA-003, RQ-005, RQ-011 | Must have 17-section schema; must be organized by TOPIC not source; YAML frontmatter required |
| FR-K | Spec-Writer Feedback Loop | 181–185 | RI-001 | Must accept targeted requests and update bundle |

### 1.2 Eval-Implied Quality Bars Not Explicit in PRD

| Eval ID | Implied Constraint | Source |
|---------|-------------------|--------|
| RQ-003 | Research must go beyond READMEs — source code, architecture docs, issues/PRs required for depth score ≥ 4 | Likert anchors |
| RQ-004 | Citations will be RE-FETCHED and content accuracy verified — paraphrases must be faithful | Likert anchors |
| RQ-010 | Topology reasoning must be "sophisticated metacognitive" — must evaluate multiple options, consider compute cost, domain dependencies | Likert anchors |
| RQ-011 | Synthesis must produce "emergent insights no single sub-agent could have produced" for top score | Likert anchors |
| RR-001 | Agent must reflect at EVERY decision point, not just major ones | Likert anchors |
| RR-002 | Must triangulate findings across sources — convergence increases confidence, divergence flagged | Likert anchors |
| RR-003 | Must dynamically adapt — abandon dead ends, revise assumptions, flag corrections | Likert anchors |
| RI-002 | Must cover FRs A–G explicitly (eval text says A–G, though PRD defines A–K) | Binary check |
| RI-003 | Bundle must address how to implement evaluable behaviors from the eval suite | Binary check |

### 1.3 Tensions and Ambiguities

1. **RI-002 scope mismatch**: Eval says "every functional requirement (A–G)" but PRD defines A–K. FRs H–K may not be checked by RI-002 but are still PRD requirements. Research must cover all A–K.
2. **"Native Opus 4.6 web_search_20260209 tool"** (PRD line 56): This is a specific tool version constraint. Need to verify this tool identifier and understand how it maps to Deep Agents SDK server-side tool configuration.
3. **Sub-agent upper bound** (PRD Unresolved Q1, line 229): No upper limit defined. Research should surface real-world patterns for optimal sub-agent counts.
4. **Token/time budget** (PRD Unresolved Q2, line 230): Currently unconstrained. Research should surface SummarizationMiddleware patterns and context window management.
5. **Feedback loop trigger mechanism** (PRD Unresolved Q3, line 231): Direct message vs. orchestrator-mediated — needs research into Deep Agents inter-agent communication patterns.
6. **Bundle versioning** (PRD Unresolved Q4, line 232): Whether to version bundle on follow-up — needs research into artifact versioning patterns.

---

## 2. Research Domains

### Domain 1: Deep Agents SDK — Core Architecture & Agent Creation

**Description**: How `create_deep_agent()` works, harness architecture, middleware stacks, configuration options, and how the research agent will be instantiated as a Deep Agent.

**PRD References**: Lines 21 (meta-agent system), 24 (Deep Agents SDK), 54 (must operate within meta-agent system), 275–295 (agent configuration)

**Mapped Eval IDs**: RS-003 (config in state), RQ-005 (bundle utility depends on understanding agent architecture)

**Relevant Skills**:
- `deep-agents-core` — create_deep_agent(), harness, SKILL.md format, config
- `framework-selection` — which framework layer is right

**Relevant SME Handles**: @hwchase17, @BraceSproul, @masondrxy

**Research Questions**:
1. What is the current API for `create_deep_agent()` and what parameters does it accept?
2. What is the harness architecture and how does it wrap the underlying LangGraph?
3. How does the middleware stack compose (ToolErrorMiddleware, SummarizationToolMiddleware, SkillsMiddleware)?
4. How is a Deep Agent configured for server-side tools like web_search and web_fetch?
5. What is the SKILL.md format and how does SkillsMiddleware use it?
6. How does `effort: max` affect agent behavior?

---

### Domain 2: LangGraph Runtime, State Management & Deployment

**Description**: StateGraph construction, state schemas, persistence, checkpointing, and LangGraph dev server deployment — the runtime foundation the research agent runs on.

**PRD References**: Lines 54 (LangGraph), 62 (launchable on LangGraph dev server), 84 (persists decomposition)

**Mapped Eval IDs**: RS-001, RS-002, RS-003, RS-004 (state presence checks), RB-003 (decomposition persistence)

**Relevant Skills**:
- `langgraph-fundamentals` — StateGraph, nodes, edges, Command, Send
- `langgraph-persistence` — checkpointers, thread_id, Store, time travel
- `langgraph-human-in-the-loop` — interrupt(), Command(resume=)

**Relevant SME Handles**: @hwchase17, @RLanceMartin

**Research Questions**:
1. What state schema is appropriate for a research agent (input: PRD path, eval path, config; output: bundle path)?
2. How does LangGraph persistence work for long-running research sessions?
3. What are the dev server deployment requirements and constraints?
4. How does state flow between the research agent and its sub-agents?
5. How does the checkpointer interact with sub-agent spawning?

---

### Domain 3: Skills System & SkillsMiddleware

**Description**: How the pre-loaded skills system works within Deep Agents — progressive disclosure, trigger mechanisms, skill file format, and how SkillsMiddleware integrates skills into the agent's reasoning.

**PRD References**: Lines 55 (skills directories), 66–68 (skills-first research posture), 122–128 (FR-C Skills Utilization), 268–271 (skills paths config)

**Mapped Eval IDs**: RB-007 (uses skills directory), RQ-007 (trigger relevance/timing), RQ-008 (reflection/internalization), RQ-009 (skill-to-research influence)

**Relevant Skills**:
- `deep-agents-core` — covers SkillsMiddleware
- All 25+ skills listed in system prompt — need to understand the ecosystem

**Relevant SME Handles**: @hwchase17, @BraceSproul

**Research Questions**:
1. How does SkillsMiddleware discover and inject skills into agent context?
2. What is the progressive disclosure pattern — how does an agent decide when to read a skill?
3. How are skill priorities resolved when multiple skills are relevant?
4. What is the relationship between the SKILL.md format and the middleware's trigger logic?
5. How does reading a skill consume context window, and what strategies exist for managing this?

---

### Domain 4: Sub-Agent Orchestration & Parallel Delegation

**Description**: How the `task` tool works for spawning sub-agents, parallel execution patterns, result collection, and topology reasoning strategies.

**PRD References**: Lines 59 (must use sub-agents), 69–71 (intentional deployment), 129–135 (FR-D Sub-Agent Delegation)

**Mapped Eval IDs**: RB-008 (spawns sub-agents), RB-009 (parallel execution), RB-010 (findings aggregated), RQ-010 (delegation quality)

**Relevant Skills**:
- `deep-agents-orchestration` — SubAgentMiddleware, TodoList, HITL interrupts
- `deep-agents-core` — harness architecture for sub-agents

**Relevant SME Handles**: @hwchase17, @Vtrivedy10, @masondrxy

**Research Questions**:
1. What is the `task` tool's underlying API and how does SubAgentMiddleware implement it?
2. How are parallel sub-agents scheduled — concurrent launch or queued?
3. How do sub-agents share output (file system, state, or return values)?
4. What are the practical limits on concurrent sub-agents (context, memory, API rate limits)?
5. What delegation topologies have been used in production Deep Agents?
6. How does the main agent aggregate and verify sub-agent outputs?

---

### Domain 5: Human-in-the-Loop Patterns & Approval Gates

**Description**: interrupt(), Command(resume=), approval workflows — how to implement the HITL research cluster approval gate and any other approval points.

**PRD References**: Lines 40 (HITL gates), 95–97 (HITL cluster approval), 166–173 (FR-I HITL Research Clusters)

**Mapped Eval IDs**: RB-011 (HITL gate fires before deep-dive), RQ-012 (HITL cluster quality)

**Relevant Skills**:
- `langgraph-human-in-the-loop` — interrupt(), Command(resume=), 4-tier error handling
- `langchain-middleware` — HumanInTheLoopMiddleware
- `deep-agents-orchestration` — HITL interrupts in Deep Agents

**Relevant SME Handles**: @hwchase17, @RLanceMartin

**Research Questions**:
1. How does `interrupt()` work in LangGraph vs. Deep Agents' HITL patterns?
2. How does the `request_approval` tool relate to the underlying interrupt mechanism?
3. What data can be presented to the user during a HITL interrupt?
4. How does the agent resume after approval — full state restored or partial?
5. Can HITL interrupts be nested (e.g., approve cluster, then approve individual targets)?

---

### Domain 6: Web Research Tools & Citation Infrastructure

**Description**: How web_search and web_fetch tools work as server-side tools, the "native Opus 4.6 web_search_20260209" tool version, and patterns for systematic citation tracking.

**PRD References**: Lines 56 (native tool version), 149–155 (FR-G Citation & Source Tracking)

**Mapped Eval IDs**: RB-004 (uses web tools), RB-005 (no hallucinated sources), RINFRA-004 (citation quality), RQ-004 (citation accuracy)

**Relevant Skills**:
- `claude-api` — may cover tool use and server-side tools

**Relevant SME Handles**: None directly relevant

**Research Questions**:
1. What is "web_search_20260209" — is this a specific Anthropic native tool version?
2. How do server-side tools differ from agent-defined tools in Deep Agents?
3. How does the agent configure server-side tools (web_search, web_fetch) in create_deep_agent()?
4. What strategies exist for tracking all fetched URLs to prevent citation hallucination?
5. How to implement a citation index that maps every finding to its web_fetch trace?

---

### Domain 7: Anthropic Model Capabilities & langchain-anthropic Integration

**Description**: Current frontier model (Claude) capabilities, pricing, rate limits, tool_as_code, and the langchain-anthropic integration package.

**PRD References**: Lines 36 (model capabilities research), 141–148 (FR-F Anthropic Model Research)

**Mapped Eval IDs**: RB-006 (researches Anthropic model capabilities)

**Relevant Skills**:
- `claude-api` — Claude API, Anthropic SDK, Agent SDK

**Relevant SME Handles**: None (Anthropic-specific, not LangChain SMEs)

**Research Questions**:
1. What is the current frontier model and its full capability matrix (context window, max output tokens, modalities, tool use, extended thinking)?
2. What are current pricing tiers and rate limits?
3. What is tool_as_code / programmatic tool calling and how does it work?
4. What native tools does Claude support (web_search, code_execution, etc.)?
5. What is the langchain-anthropic package and how does it integrate with LangGraph?
6. What are the differences between Anthropic SDK direct use vs. langchain-anthropic?

---

### Domain 8: LangSmith Evaluation & Tracing Patterns

**Description**: How LangSmith evaluation pipelines work, trace patterns that support behavioral evals, and how the research agent's implementation should be designed for evaluability.

**PRD References**: Lines 108–109 (factor eval criteria into agenda), 60 (Likert thresholds >= 4.0)

**Mapped Eval IDs**: RI-003 (covers eval implications), all RESEARCH-BEHAVIORAL evals (trace inspection)

**Relevant Skills**:
- `langsmith-evaluator` — evaluators, run functions, evaluate()
- `langsmith-dataset` — dataset types, management
- `langsmith-trace` — tracing, querying traces
- `langsmith-evaluator-architect` — evaluator design

**Relevant SME Handles**: @hwchase17, @RLanceMartin

**Research Questions**:
1. How does LangSmith trace inspection work for behavioral evals (RB-* series)?
2. What trace patterns make tool calls visible and verifiable?
3. How does the `trace_cross_reference_and_refetch` evaluation method work (RB-005)?
4. How to structure a run function for research agent evaluation?
5. What dataset format should the research agent's eval suite use?
6. How does `llm_as_judge_with_refetch` work (RQ-004)?

---

### Domain 9: SME Consultation — Twitter/X Search Patterns

**Description**: How to effectively search Twitter/X for SME content, contextualize it with technical findings, and identify consensus/disagreements across 6 configured handles.

**PRD References**: Lines 37 (SME perspectives), 75–78 (configurable SME tracking), 136–140 (FR-E SME Consultation), 237–263 (handle configuration)

**Mapped Eval IDs**: RQ-006 (SME consultation quality)

**Relevant Skills**: None directly

**Relevant SME Handles**: All 6 — @hwchase17, @Vtrivedy10, @sydneyrunkle, @masondrxy, @BraceSproul, @RLanceMartin

**Research Questions**:
1. How to search X/Twitter for recent relevant posts by specific handles?
2. What content formats do these SMEs typically use (tweets, threads, blog cross-posts)?
3. How to distinguish relevant technical content from casual posts?
4. What topics has each SME recently discussed that relate to research agent domains?
5. How to identify consensus vs. disagreement across SME perspectives?

---

### Domain 10: Research Bundle Schema, Synthesis & Output Patterns

**Description**: The 17-section research bundle schema, YAML frontmatter requirements, topic-based organization strategy, and synthesis patterns that produce emergent cross-cutting insights.

**PRD References**: Lines 98–100 (synthesis workflow), 174–180 (FR-J Research Bundle Output), 209–214 (required outputs)

**Mapped Eval IDs**: RINFRA-001 (file exists), RINFRA-002 (frontmatter valid), RINFRA-003 (schema completeness), RQ-005 (utility), RQ-011 (synthesis quality)

**Relevant Skills**: None directly (output format concern, informed by downstream spec-writer needs)

**Relevant SME Handles**: None

**Research Questions**:
1. What does the spec-writer agent need from a research bundle to make architectural decisions?
2. How should 17 sections be populated to maximize utility?
3. What patterns exist for topic-based synthesis vs. source-based organization?
4. How to produce emergent insights from cross-cutting analysis?
5. What YAML frontmatter fields are required and what values should they take?
6. How to build a PRD Coverage Matrix that is usable by the verification agent?

---

## 3. Phased Execution Plan

### Phase Priority: Architectural Impact (High → Low)

| Phase | Domains | Rationale | Estimated Effort |
|-------|---------|-----------|-----------------|
| **P1: Foundation** | D1 (Deep Agents Core), D2 (LangGraph Runtime) | These determine the runtime foundation — every other domain depends on understanding how agents are built and deployed | HIGH |
| **P2: Agent Internals** | D3 (Skills System), D4 (Sub-Agent Orchestration), D5 (HITL Patterns) | These are core behavioral capabilities the agent must implement — skills, delegation, and approval gates | HIGH |
| **P3: Research Infrastructure** | D6 (Web Research Tools), D7 (Anthropic Model), D8 (LangSmith Eval) | These support the research process itself — tools, model capabilities, and evaluability | MEDIUM |
| **P4: Integration & Output** | D9 (SME Consultation), D10 (Bundle Schema) | These are integration and output concerns — how to gather SME input and structure the final deliverable | MEDIUM |

### Skills Consultation Priority Order

Based on the phased execution plan, skills should be read in this order:
1. `framework-selection` — determines framework choice before anything else
2. `deep-agents-core` — core agent creation and architecture
3. `deep-agents-orchestration` — sub-agents and HITL
4. `deep-agents-memory` — state and persistence
5. `langgraph-fundamentals` — underlying runtime
6. `langgraph-persistence` — checkpointing and state
7. `langgraph-human-in-the-loop` — HITL patterns
8. `langchain-middleware` — middleware patterns
9. `langchain-fundamentals` — base framework
10. `claude-api` — model capabilities and tool use
11. `langsmith-evaluator` — evaluation pipelines
12. `langsmith-trace` — tracing patterns
13. `langsmith-dataset` — dataset management
14. `langsmith-evaluator-architect` — evaluator design
15. `langchain-dependencies` — package versions

---

## 4. Progress Tracker

| Domain | Status | Skills Consulted | Web Research | Gaps Identified | Deep-Dive Done |
|--------|--------|-----------------|--------------|-----------------|----------------|
| D1: Deep Agents Core | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D2: LangGraph Runtime | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D3: Skills System | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D4: Sub-Agent Orchestration | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D5: HITL Patterns | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D6: Web Research Tools | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D7: Anthropic Model | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D8: LangSmith Eval | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D9: SME Consultation | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |
| D10: Bundle Schema | NOT_STARTED | [ ] | [ ] | [ ] | [ ] |

---

## 5. Gap & Contradiction Remediation Log

_To be populated after Phase 5 (Gap & Contradiction Remediation)._

| ID | Type | Description | Severity | Root Cause | Remediation Action | Status | Resolution |
|----|------|-------------|----------|------------|-------------------|--------|------------|
| — | — | — | — | — | — | — | — |

---

## 6. Cross-Cutting Concerns

These concerns span multiple domains and must be tracked across the research process:

1. **Context window management**: Affects D1, D3, D4, D6 — skills consumption + sub-agent delegation + web research all consume context. SummarizationMiddleware is the mitigation, but need to understand its limits.
2. **State schema design**: Affects D1, D2, D4 — how state flows from main agent to sub-agents and back. Needs consistent design across delegation topology.
3. **Trace evaluability**: Affects D6, D8, and all behavioral evals — every tool call must be traceable for the eval suite to function. Trace patterns must be designed with evals in mind.
4. **Citation integrity**: Affects D6, D7, D9 — every web_fetch must be tracked, every finding must be cited, and citations must survive synthesis into the bundle. This is a cross-cutting data-flow concern.
5. **Server-side vs. agent-defined tools**: Affects D1, D6 — web_search and web_fetch are listed as server_side_tools in the config. Need to understand how this differs from regular tool definitions.
