# Research Decomposition — Meta-Agent Research Agent

## Project
Research Agent — Deep Ecosystem Researcher for the Meta-Agent System

## Project ID: meta-agent-research-agent
## PRD: `/workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md`
## Eval Suite: `/workspace/projects/meta-agent/evals/eval-suite-prd.json`
## Decomposition Date: 2025-07-17

---

## Research Domains

### Domain 1: Deep Agents SDK Architecture & Agent Runtime
**Description:** How Deep Agents SDK structures agent lifecycles, tool registration, state management, and sub-agent spawning. This is the foundational runtime the research agent must operate within.

**PRD References:**
- Line 21: "operates within the meta-agent system (Deep Agents SDK, LangGraph)"
- Line 54: "must operate within the meta-agent system architecture (Deep Agents SDK, LangGraph)"
- Lines 274-296: Agent configuration block (type: deep_agent, effort: max, recursion_limit: 100)
- Lines 283-288: Middleware stack (ToolErrorMiddleware, SummarizationToolMiddleware, SkillsMiddleware)
- Line 59: "must use sub-agents for parallel research execution"

**Eval IDs:** RB-008, RB-009, RB-010, RQ-010, RS-003

**Skills to Consult:**
- `/skills/langchain/config/skills/deep-agents-core/`
- `/skills/langchain/config/skills/deep-agents-memory/`
- `/skills/langchain/config/skills/deep-agents-orchestration/`
- `/skills/langchain/config/skills/framework-selection/`

**SME Handles:** @hwchase17, @BraceSproul, @RLanceMartin

**Research Questions:**
1. What is the Deep Agents SDK agent lifecycle (init → tool execution → state persistence → termination)?
2. How does the `task` tool work for sub-agent spawning — is it LangGraph-native or SDK-specific?
3. What state is shared between parent and child agents?
4. How does `recursion_limit: 100` interact with sub-agent depth?
5. What is the `effort` parameter and how does it affect agent behavior?
6. How do server-side tools (web_search, web_fetch) differ from regular tools?

**Status:** `NOT_STARTED`

---

### Domain 2: LangGraph State Management & Persistence
**Description:** How LangGraph manages state graphs, checkpointing, interrupts/HITL, and message persistence. Critical for understanding how the research agent's state flows through the pipeline.

**PRD References:**
- Line 54: "meta-agent system architecture (Deep Agents SDK, LangGraph)"
- Line 63: "must be launchable on the LangGraph dev server"
- Lines 96-98: HITL research cluster approval workflow
- Line 60: "must present HITL research clusters for user approval"

**Eval IDs:** RB-011, RQ-012, RS-001, RS-002, RS-004

**Skills to Consult:**
- `/skills/langchain/config/skills/langgraph-fundamentals/`
- `/skills/langchain/config/skills/langgraph-persistence/`
- `/skills/langchain/config/skills/langgraph-human-in-the-loop/`

**SME Handles:** @hwchase17, @Vtrivedy10, @RLanceMartin

**Research Questions:**
1. How does LangGraph implement HITL interrupts — `interrupt()` function, breakpoints, or custom gates?
2. What state graph patterns support multi-phase research pipelines?
3. How does checkpointing work for long-running research processes?
4. How does the LangGraph dev server expose agent endpoints?
5. What is the relationship between LangGraph state and Deep Agents SDK state?

**Status:** `NOT_STARTED`

---

### Domain 3: Middleware Architecture
**Description:** The three middleware components listed in the PRD config: ToolErrorMiddleware, SummarizationToolMiddleware, and SkillsMiddleware.

**PRD References:**
- Lines 283-288: Middleware configuration
- Line 227: "SummarizationMiddleware auto-compacts" (context window management)
- Lines 55-56: Skills directories usage
- Lines 124-129: Skills utilization requirements (FR-C)

**Eval IDs:** RQ-007, RQ-008, RQ-009, RB-007

**Skills to Consult:**
- `/skills/langchain/config/skills/langchain-middleware/`
- `/skills/langchain/config/skills/deep-agents-core/`

**SME Handles:** @hwchase17, @BraceSproul

**Research Questions:**
1. How does ToolErrorMiddleware intercept and handle tool errors?
2. How does SummarizationToolMiddleware manage context window pressure?
3. How does SkillsMiddleware inject skills into the agent's context?
4. What is the middleware execution order and how do they compose?
5. Are these middleware components from Deep Agents SDK or LangGraph core?

**Status:** `NOT_STARTED`

---

### Domain 4: Web Research Tools (web_search, web_fetch)
**Description:** The native Opus 4.6 web research tools that the research agent must use for all external research.

**PRD References:**
- Line 56: "must use native Opus 4.6 web_fetch and web_search tools"
- Lines 289-296: Tools and server_side_tools configuration
- Lines 150-155: Citation and source tracking requirements (FR-G)

**Eval IDs:** RB-004, RB-005, RQ-004, RINFRA-004

**Skills to Consult:**
- (No specific skill — platform-native tools)

**Research Questions:**
1. What are the web_search and web_fetch tool APIs — parameters, return formats, rate limits?
2. How do server-side tools differ from client-side tools in Deep Agents?
3. Best patterns for citation tracking — correlating fetched URLs with findings?
4. What content types can web_fetch handle?
5. How to handle web_fetch failures gracefully?

**Status:** `NOT_STARTED`

---

### Domain 5: Anthropic Model Capabilities (Claude Opus 4)
**Description:** Full capability matrix for the current frontier model, including context window, output limits, tool use, extended thinking, pricing, and rate limits.

**PRD References:**
- Lines 143-148: Anthropic model research requirements (FR-F)
- Line 36: "Research Anthropic model capabilities including full capability matrices"
- Line 56: "native Opus 4.6 web_fetch and web_search tools"

**Eval IDs:** RB-006, RQ-002, RQ-003

**Skills to Consult:**
- `/skills/anthropic/spec/agent-skills-spec.md`
- `/skills/anthropic/skills/claude-api/`

**Research Questions:**
1. What is Claude Opus 4's context window size and max output tokens?
2. What modalities are supported (text, vision, tool use)?
3. How does extended thinking work — beta headers, budget tokens?
4. Current pricing tiers and rate limits?
5. What is tool_as_code / programmatic tool calling?
6. What is the langchain-anthropic integration package's current API?

**Status:** `NOT_STARTED`

---

### Domain 6: Skills System Architecture
**Description:** How the skills system works — directory structure, SKILL.md format, progressive disclosure pattern, and how SkillsMiddleware loads them.

**PRD References:**
- Lines 55-56: Skills directories constraint
- Lines 67-69: Skills-first research posture (stakeholder intent)
- Lines 87-89: Skills consultation workflow
- Lines 124-129: Skills utilization requirements (FR-C)
- Lines 267-272: Skills paths configuration

**Eval IDs:** RB-007, RQ-007, RQ-008, RQ-009

**Skills to Consult:**
- `/skills/anthropic/template/SKILL.md`
- `/skills/anthropic/spec/agent-skills-spec.md`

**Research Questions:**
1. What is the canonical SKILL.md format and structure?
2. How does SkillsMiddleware discover and load skills?
3. What does "progressive disclosure" mean in practice?
4. How should the research agent prioritize skill reading order?
5. Difference between LangChain skills and Anthropic skills?

**Status:** `NOT_STARTED`

---

### Domain 7: Sub-Agent Delegation Patterns
**Description:** Patterns for parallel sub-agent deployment — topology reasoning, task brief construction, output aggregation.

**PRD References:**
- Lines 70-72: Intentional sub-agent deployment (stakeholder intent)
- Lines 91-93: Sub-agent delegation workflow
- Lines 131-135: Sub-agent delegation requirements (FR-D)
- Line 59: "must use sub-agents for parallel research execution"

**Eval IDs:** RB-008, RB-009, RB-010, RQ-010

**Skills to Consult:**
- `/skills/langchain/config/skills/deep-agents-orchestration/`
- `/skills/langchain/config/skills/deep-agents-core/`

**SME Handles:** @hwchase17, @masondrxy

**Research Questions:**
1. What patterns exist for reasoning about delegation topology?
2. How does the `task` tool manage sub-agent lifecycle?
3. Optimal way to pass baseline knowledge to sub-agents?
4. How do sub-agents write findings to a shared directory?
5. Failure modes — sub-agent timeout, partial results?
6. How to aggregate and cross-reference sub-agent outputs?

**Status:** `NOT_STARTED`

---

### Domain 8: HITL (Human-in-the-Loop) Patterns
**Description:** Patterns for implementing HITL gates in LangGraph agents — interrupt mechanisms, approval workflows, state resumption.

**PRD References:**
- Lines 96-98: HITL research cluster approval workflow
- Line 60: "must present HITL research clusters for user approval"
- Lines 167-173: HITL research cluster requirements (FR-I)

**Eval IDs:** RB-011, RQ-012

**Skills to Consult:**
- `/skills/langchain/config/skills/langgraph-human-in-the-loop/`

**SME Handles:** @hwchase17, @Vtrivedy10

**Research Questions:**
1. How does LangGraph's `interrupt()` function work in practice?
2. State persistence across HITL interrupts?
3. Patterns for structured approval requests?
4. How does `request_approval_tool` relate to LangGraph interrupts?
5. Handling partial approval (some clusters, not all)?

**Status:** `NOT_STARTED`

---

### Domain 9: Citation & Source Tracking Patterns
**Description:** How to implement reliable citation tracking — correlating web_fetch calls with findings, maintaining a citation index, preventing hallucinated sources.

**PRD References:**
- Lines 150-155: Citation and source tracking requirements (FR-G)
- Line 38: "mandatory citations that traces every finding to its source"
- Line 57: "cite every finding with source type and URL/reference"

**Eval IDs:** RINFRA-004, RB-005, RQ-004

**Research Questions:**
1. Patterns for maintaining a citation registry during research?
2. How to correlate web_fetch trace entries with cited URLs?
3. Appropriate source type taxonomy?
4. How to prevent citation drift?

**Status:** `NOT_STARTED`

---

### Domain 10: Research Bundle Schema & Synthesis Patterns
**Description:** The 17-section research bundle schema, YAML frontmatter requirements, and synthesis patterns for organizing findings by topic.

**PRD References:**
- Lines 99-101: Research bundle synthesis workflow
- Lines 175-181: Research bundle output requirements (FR-J)
- Lines 210-215: Required outputs listing

**Eval IDs:** RINFRA-001, RINFRA-002, RINFRA-003, RQ-005, RQ-011

**Research Questions:**
1. Best practices for research synthesis — topic-based organization?
2. How should the 17 sections be structured for spec-writer utility?
3. Required YAML frontmatter fields and expected values?
4. How should confidence assessments be calibrated?
5. What makes a PRD Coverage Matrix useful for verification?

**Status:** `NOT_STARTED`

---

### Domain 11: Gap & Contradiction Remediation
**Description:** Systematic approaches to identifying, diagnosing, and resolving gaps and contradictions across research findings.

**PRD References:**
- Lines 73-75: Gap and contradiction remediation (stakeholder intent)
- Lines 94-95: Gap remediation workflow
- Lines 157-165: Gap remediation requirements (FR-H)

**Eval IDs:** RQ-013

**Research Questions:**
1. Frameworks for systematic gap analysis?
2. Prioritizing gaps by downstream impact?
3. What makes a good resolution statement?
4. Handling genuinely unresolvable contradictions?

**Status:** `NOT_STARTED`

---

### Domain 12: LangSmith Evaluation & Tracing
**Description:** LangSmith tracing, evaluation, and dataset management — relevant because the eval suite references trace inspection and the agent must produce traceable outputs.

**PRD References:**
- Lines 109-111: Eval suite consumption requirements (FR-A)
- Line 61: "All Likert eval thresholds are >= 4.0"
- Lines 219-227: Risks table references eval cross-referencing

**Eval IDs:** RB-001, RB-002, RI-003

**Skills to Consult:**
- `/skills/langsmith/config/skills/langsmith-trace/`
- `/skills/langsmith/config/skills/langsmith-evaluator/`
- `/skills/langsmith/config/skills/langsmith-evaluator-architect/`
- `/skills/langsmith/config/skills/langsmith-dataset/`

**SME Handles:** @hwchase17, @RLanceMartin

**Research Questions:**
1. How does LangSmith trace agent tool calls for eval inspection?
2. How does trace_inspection eval method work?
3. How does llm_as_judge work in LangSmith?
4. What makes traces evaluable — required metadata?
5. How does trace_cross_reference_and_refetch work?

**Status:** `NOT_STARTED`

---

### Domain 13: langchain-anthropic Integration Package
**Description:** The Python package that integrates Anthropic models with LangChain — ChatAnthropic, tool binding, extended thinking support.

**PRD References:**
- Line 147: "must research the langchain-anthropic integration package"
- Line 62: "Python is the implementation language"

**Eval IDs:** RB-006, RQ-002

**Skills to Consult:**
- `/skills/langchain/config/skills/langchain-fundamentals/`
- `/skills/langchain/config/skills/langchain-dependencies/`

**SME Handles:** @hwchase17, @BraceSproul

**Research Questions:**
1. Current version of langchain-anthropic?
2. How does ChatAnthropic bind tools?
3. Extended thinking / beta header support?
4. Known limitations or gotchas?

**Status:** `NOT_STARTED`

---

## Phased Execution Plan

### Phase A — Foundation (Highest Architectural Impact)
1. Domain 1: Deep Agents SDK Architecture
2. Domain 2: LangGraph State Management & Persistence
3. Domain 3: Middleware Architecture
4. Domain 6: Skills System Architecture

**Rationale:** These domains define the runtime environment. All other domains depend on this foundation.

### Phase B — Core Capabilities
5. Domain 4: Web Research Tools
6. Domain 5: Anthropic Model Capabilities
7. Domain 7: Sub-Agent Delegation Patterns
8. Domain 8: HITL Patterns

**Rationale:** Primary capabilities the agent must use. Depend on Phase A understanding.

### Phase C — Quality & Integration
9. Domain 9: Citation & Source Tracking
10. Domain 10: Research Bundle Schema
11. Domain 11: Gap & Contradiction Remediation
12. Domain 12: LangSmith Evaluation & Tracing
13. Domain 13: langchain-anthropic Integration

**Rationale:** Output quality and downstream integration. Build on Phase B capabilities.

---

## Progress Tracker

| Domain | Phase | Status | Last Updated |
|--------|-------|--------|-------------|
| 1. Deep Agents SDK | A | NOT_STARTED | — |
| 2. LangGraph State | A | NOT_STARTED | — |
| 3. Middleware | A | NOT_STARTED | — |
| 4. Web Research Tools | B | NOT_STARTED | — |
| 5. Anthropic Models | B | NOT_STARTED | — |
| 6. Skills System | A | NOT_STARTED | — |
| 7. Sub-Agent Delegation | B | NOT_STARTED | — |
| 8. HITL Patterns | B | NOT_STARTED | — |
| 9. Citation Tracking | C | NOT_STARTED | — |
| 10. Bundle Schema | C | NOT_STARTED | — |
| 11. Gap Remediation | C | NOT_STARTED | — |
| 12. LangSmith Eval | C | NOT_STARTED | — |
| 13. langchain-anthropic | C | NOT_STARTED | — |

---

## Gap & Contradiction Remediation Log

*(To be populated after sub-agent findings are collected — Phase 5)*
## Created: 2025-07-17

---

## Research Domains

### Domain 1: Deep Agents SDK Architecture & Agent Lifecycle
**Description:** How the Deep Agents SDK works — agent types, lifecycle, spawning sub-agents, recursion limits, effort levels, and the `task` tool delegation model.  
**PRD References:** Lines 54 (meta-agent architecture constraint), 59 (sub-agents for parallel execution), 63 (Python), 64 (LangGraph dev server), 71-72 (delegation topology), 131-135 (sub-agent delegation FRs), 278-279 (agent config: deep_agent type, effort: max, recursion_limit: 100)  
**Eval IDs:** RB-008 (spawns sub-agents), RB-009 (parallel execution), RB-010 (findings aggregated), RQ-010 (delegation quality)  
**Skills:** `/skills/langchain/config/skills/deep-agents-core/`, `/skills/langchain/config/skills/deep-agents-orchestration/`, `/skills/langchain/config/skills/deep-agents-memory/`  
**SME Handles:** @hwchase17, @BraceSproul, @RLanceMartin  
**Key Questions:**
1. What is the Deep Agents SDK agent type system and how does `deep_agent` differ from other types?
2. How does the `task` tool work for sub-agent spawning — what are the exact parameters, lifecycle, and return semantics?
3. What does `effort: max` do? How does `recursion_limit: 100` affect agent behavior?
4. How do sub-agents communicate results back to the parent agent?
5. What are the best practices for parallel sub-agent delegation topology?

### Domain 2: LangGraph Fundamentals, State Management & HITL
**Description:** LangGraph's graph-based agent orchestration, state channels, checkpointing, persistence, and human-in-the-loop interrupt patterns.  
**PRD References:** Lines 54 (LangGraph constraint), 60-61 (HITL approval), 64 (LangGraph dev server), 96-98 (HITL workflow), 167-174 (HITL FRs)  
**Eval IDs:** RB-011 (HITL gate fires), RQ-012 (HITL cluster quality)  
**Skills:** `/skills/langchain/config/skills/langgraph-fundamentals/`, `/skills/langchain/config/skills/langgraph-human-in-the-loop/`, `/skills/langchain/config/skills/langgraph-persistence/`  
**SME Handles:** @hwchase17, @Vtrivedy10  
**Key Questions:**
1. How does LangGraph implement HITL interrupts — what are the primitives (`interrupt`, `Command`)?
2. How does checkpointing work for resuming after HITL approval?
3. What state channels are needed for research agent state (PRD, evals, config, bundle)?
4. How does the LangGraph dev server work for launching agents?
5. What persistence backends are available and recommended?

### Domain 3: Middleware System (Tool Error, Summarization, Skills)
**Description:** The middleware stack configured for the research agent: ToolErrorMiddleware, SummarizationToolMiddleware, SkillsMiddleware.  
**PRD References:** Lines 281-284 (middleware config), 55-56 (skills directories), 68-69 (skills-first posture), 124-129 (skills utilization FRs), 227 (context window risk/SummarizationMiddleware)  
**Eval IDs:** RB-007 (uses skills directory), RQ-007 (skill trigger relevance), RQ-008 (skill reflection quality), RQ-009 (skill-to-research influence)  
**Skills:** `/skills/langchain/config/skills/langchain-middleware/`  
**SME Handles:** @hwchase17, @BraceSproul  
**Key Questions:**
1. How does SummarizationToolMiddleware work — when does it compact, what triggers it?
2. How does SkillsMiddleware inject skill content into agent context?
3. How does ToolErrorMiddleware handle failures and retries?
4. How do middlewares compose in the Deep Agents stack?

### Domain 4: Anthropic Model Capabilities & langchain-anthropic Integration
**Description:** Claude model capabilities (context window, max tokens, tool use, extended thinking), pricing, rate limits, `tool_as_code`, and the `langchain-anthropic` package.  
**PRD References:** Lines 36-37 (model capabilities research), 56 (native Opus 4.6 tools), 143-148 (Anthropic model research FRs)  
**Eval IDs:** RB-006 (researches Anthropic model capabilities), RINFRA-003 (model capability matrix section)  
**Skills:** `/skills/anthropic/spec/agent-skills-spec.md`, `/skills/anthropic/skills/claude-api/`  
**SME Handles:** @hwchase17  
**Key Questions:**
1. What is the current frontier model (Claude Opus 4.6)? Full capability matrix.
2. What are the pricing tiers and rate limits?
3. How does `tool_as_code` / programmatic tool calling work?
4. What is `web_search` and `web_fetch` as native/server-side tools?
5. How does `langchain-anthropic` integrate with the ChatAnthropic class?
6. What is extended thinking and how does it affect token usage?

### Domain 5: Web Research Tools (web_search, web_fetch)
**Description:** The native Opus 4.6 web_search and web_fetch tools — how they work, their parameters, limitations, and how they integrate as server-side tools.  
**PRD References:** Lines 56 (native Opus 4.6 tools), 150-155 (citation/source tracking FRs), 293-296 (server_side_tools config)  
**Eval IDs:** RB-004 (uses web_search/web_fetch), RB-005 (no hallucinated sources), RQ-004 (citation accuracy), RINFRA-004 (citation quality)  
**Skills:** `/skills/anthropic/skills/claude-api/`  
**SME Handles:** @hwchase17, @BraceSproul  
**Key Questions:**
1. How do web_search and web_fetch work as server-side tools in LangGraph?
2. What are the parameters, rate limits, and response formats?
3. How do you ensure citation traceability (trace every web_fetch call)?
4. What is the difference between agent-native tools and server-side tools?

### Domain 6: Research Bundle Schema & Artifact Structure
**Description:** The required output artifact schema — 17 sections, YAML frontmatter, lineage tracing, and how the bundle integrates with the spec-writer downstream.  
**PRD References:** Lines 99-101 (bundle synthesis workflow), 175-181 (bundle output FRs), 210-215 (required outputs)  
**Eval IDs:** RINFRA-001 (bundle exists), RINFRA-002 (valid frontmatter), RINFRA-003 (schema completeness), RQ-005 (spec-writer utility), RQ-011 (synthesis quality), RI-002 (covers all FRs), RI-003 (covers eval implications)  
**Skills:** None directly (artifact structure is PRD-defined)  
**Key Questions:**
1. What exactly are the 17 required sections and what content goes in each?
2. How should YAML frontmatter be structured for lineage tracing?
3. What makes a bundle "usable by the spec-writer without additional research"?

### Domain 7: SME Consultation via Twitter/X
**Description:** How to systematically search and contextualize SME perspectives from configured Twitter/X handles.  
**PRD References:** Lines 37-38 (SME perspectives), 76-78 (configurable SME tracking), 138-142 (SME consultation FRs), 238-264 (Twitter handle config)  
**Eval IDs:** RQ-006 (SME consultation quality)  
**Skills:** None directly  
**SME Handles:** @hwchase17, @Vtrivedy10, @sydneyrunkle, @masondrxy, @BraceSproul, @RLanceMartin  
**Key Questions:**
1. How to effectively search Twitter/X for relevant technical content from specific handles?
2. How to contextualize SME posts by tying them to documentation findings?

### Domain 8: Gap/Contradiction Remediation & Quality Assurance
**Description:** The systematic process for identifying gaps/contradictions in sub-agent findings, root cause analysis, and remediation.  
**PRD References:** Lines 73-75 (gap/contradiction remediation intent), 93-95 (remediation workflow), 157-165 (remediation FRs)  
**Eval IDs:** RQ-013 (remediation quality)  
**Skills:** None directly  
**Key Questions:**
1. What patterns exist for systematic gap analysis across multiple research outputs?
2. How should severity be assessed for downstream impact on spec-writer decisions?

### Domain 9: LangSmith Evaluation & Tracing
**Description:** LangSmith capabilities for tracing agent runs, creating datasets, and building evaluators — relevant because the research agent's outputs will be evaluated.  
**PRD References:** Lines 61 (Likert eval thresholds >= 4.0), 109-111 (eval suite consumption)  
**Eval IDs:** All eval IDs implicitly  
**Skills:** `/skills/langsmith/config/skills/langsmith-trace/`, `/skills/langsmith/config/skills/langsmith-dataset/`, `/skills/langsmith/config/skills/langsmith-evaluator/`, `/skills/langsmith/config/skills/langsmith-evaluator-architect/`  
**SME Handles:** @hwchase17, @RLanceMartin  
**Key Questions:**
1. How does LangSmith trace inspection work for binary eval methods?
2. How does llm_as_judge evaluation work for Likert scoring?
3. What trace data is needed for `trace_cross_reference_and_refetch` (RB-005)?

### Domain 10: Spec-Writer Feedback Loop & Integration
**Description:** How the research agent integrates with the spec-writer downstream — the feedback loop for additional research requests.  
**PRD References:** Lines 41 (feedback loop goal), 102-104 (feedback loop workflow), 182-186 (feedback loop FRs)  
**Eval IDs:** RI-001 (spec-writer sufficiency gate)  
**Skills:** None directly  
**Key Questions:**
1. How should the feedback loop be triggered (direct message vs orchestrator-mediated)?
2. How should the bundle be versioned on follow-up research?

---

## Phased Execution Plan (prioritized by architectural impact)

### Phase A: Core Architecture (Domains 1, 2, 3) — HIGHEST IMPACT
These domains define how the agent is built, how it delegates work, and how it interacts with users. Every other domain depends on understanding the Deep Agents SDK, LangGraph, and middleware stack.

### Phase B: Research Tooling & Model (Domains 4, 5) — HIGH IMPACT
The agent's primary tools (web_search, web_fetch) and the model it runs on (Anthropic Claude) are critical for understanding what's possible and what constraints exist.

### Phase C: Output Quality & Integration (Domains 6, 8, 9, 10) — MEDIUM IMPACT
Bundle schema, quality assurance, evaluation integration, and spec-writer handoff.

### Phase D: SME Consultation (Domain 7) — LOWER IMPACT (but required)
SME consultation is a required research activity but has less architectural impact.

---

## Progress Tracker

| Domain | Status | Notes |
|--------|--------|-------|
| 1. Deep Agents SDK | NOT_STARTED | |
| 2. LangGraph & HITL | NOT_STARTED | |
| 3. Middleware System | NOT_STARTED | |
| 4. Anthropic Model | NOT_STARTED | |
| 5. Web Research Tools | NOT_STARTED | |
| 6. Bundle Schema | NOT_STARTED | |
| 7. SME Consultation | NOT_STARTED | |
| 8. Gap/Contradiction | NOT_STARTED | |
| 9. LangSmith Eval | NOT_STARTED | |
| 10. Spec-Writer Integration | NOT_STARTED | |

---

## Gap and Contradiction Remediation Log

*(To be populated after sub-agent findings are collected)*
- **Eval Suite Source:** `/workspace/projects/meta-agent/evals/eval-suite-prd.json`
- **Created:** 2025-07-17
- **Last Updated:** 2025-07-17

---

## Research Domains

### Domain 1: Deep Agents SDK Architecture & Agent Construction
**Description:** How to build a research agent using the Deep Agents SDK — `create_deep_agent()`, agent lifecycle, tool registration, middleware stack, recursion limits, and system prompt composition.

**PRD References:**
- Lines 54: "must operate within the meta-agent system architecture (Deep Agents SDK, LangGraph)"
- Lines 63: "Python is the implementation language"
- Lines 274-296: Agent configuration (type: deep_agent, effort: max, recursion_limit: 100, middleware list, tools list, server_side_tools)

**Eval IDs:** RS-001, RS-002, RS-003, RS-004 (state context); RINFRA-001 (artifact path)

**Skills to Consult:**
- `/skills/langchain/config/skills/deep-agents-core/`
- `/skills/langchain/config/skills/deep-agents-memory/`
- `/skills/langchain/config/skills/deep-agents-orchestration/`
- `/skills/langchain/config/skills/langchain-middleware/`
- `/skills/langchain/config/skills/framework-selection/`

**SME Handles:** @hwchase17, @BraceSproul, @masondrxy

**Research Questions:**
1. What is the current `create_deep_agent()` API surface? Constructor params, return type, how to attach tools and middleware?
2. How does the agent state model work — what fields can input/output state carry? How to pass prd_path, eval_suite_path, twitter_handles, config?
3. How do server-side tools (web_search, web_fetch) differ from regular tools in registration?
4. What is the correct middleware stack for ToolErrorMiddleware, SummarizationToolMiddleware, SkillsMiddleware?
5. How does recursion_limit interact with sub-agent spawning via the task tool?
6. How to launch a Deep Agent on the LangGraph dev server?

---

### Domain 2: LangGraph Fundamentals & Sub-Agent Patterns
**Description:** LangGraph graph construction, state management, sub-agent spawning via `task` tool, parallel execution patterns, and how the research agent fits into the meta-agent multi-agent graph.

**PRD References:**
- Lines 54: "Deep Agents SDK, LangGraph"
- Lines 59: "must use sub-agents for parallel research execution"
- Lines 69-73: Intentional sub-agent deployment (topology reasoning)
- Lines 90-92: Sub-Agent Delegation workflow
- Lines 131-135: FR D (Sub-Agent Delegation)

**Eval IDs:** RB-008, RB-009, RB-010, RQ-010

**Skills to Consult:**
- `/skills/langchain/config/skills/langgraph-fundamentals/`
- `/skills/langchain/config/skills/langgraph-human-in-the-loop/`
- `/skills/langchain/config/skills/langgraph-persistence/`
- `/skills/langchain/config/skills/deep-agents-orchestration/`

**SME Handles:** @hwchase17, @Vtrivedy10, @RLanceMartin

**Research Questions:**
1. How does the `task` tool work in Deep Agents? How are sub-agents spawned, scoped, and collected?
2. Can multiple `task` calls execute in parallel? What determines parallel vs sequential execution?
3. How does sub-agent output get returned to the parent agent? Files vs return values?
4. What are the practical limits of sub-agent depth/count?
5. How does LangGraph state flow between parent and child agents?

---

### Domain 3: Anthropic Model Capabilities (Claude Opus 4.6)
**Description:** Full capability matrix for the frontier model — context window, output tokens, tool use, extended thinking, native tools (web_search, web_fetch), pricing, rate limits, programmatic tool calling.

**PRD References:**
- Lines 56: "must use native Opus 4.6 web_fetch and web_search tools"
- Lines 143-148: FR F (Anthropic Model Research) — capability matrix, pricing, rate limits, tool_as_code, langchain-anthropic
- Lines 36: "model capabilities including full capability matrices, pricing, and rate limits"

**Eval IDs:** RB-006, RB-004 (web tool usage)

**Skills to Consult:**
- `/skills/anthropic/spec/agent-skills-spec.md`
- `/skills/anthropic/skills/claude-api/`

**SME Handles:** (none specified — Anthropic SMEs not in config)

**Research Questions:**
1. What is the current Claude Opus 4.6 context window and max output tokens?
2. What are the native tool capabilities (web_search, web_fetch)? How do they work?
3. What is the extended thinking API? budget_tokens vs streaming_thinking?
4. What is the pricing per input/output token for Opus 4.6?
5. What are the rate limits (requests/min, tokens/min)?
6. What is tool_as_code / programmatic tool calling? Is it available?
7. What is the langchain-anthropic integration package version and capabilities?

---

### Domain 4: Skills System Architecture
**Description:** How the skills middleware works, how skills are loaded and accessed, the progressive disclosure pattern, and how the research agent should consume skill content.

**PRD References:**
- Lines 55: "must use the skills directories at `/skills/langchain/`, `/skills/anthropic/`, `/skills/langsmith/`"
- Lines 66-68: Skills-First Research Posture (read and internalize BEFORE web research)
- Lines 87-89: Skills Consultation workflow
- Lines 123-129: FR C (Skills Utilization)
- Lines 267-272: Skills paths configuration

**Eval IDs:** RB-007, RQ-007, RQ-008, RQ-009

**Skills to Consult:**
- `/skills/anthropic/template/SKILL.md` (skill template/structure)
- `/skills/anthropic/spec/agent-skills-spec.md` (skills specification)
- All 11 LangChain skills, 4 LangSmith skills (to understand their structure)

**SME Handles:** @sydneyrunkle (Pydantic/LangChain)

**Research Questions:**
1. What is the SkillsMiddleware and how does it auto-load skills?
2. What is the progressive disclosure pattern for skills?
3. How should an agent read skill files — what is the expected structure?
4. How does the SKILL.md template work?
5. What is the agent-skills-spec.md and what guidance does it provide?

---

### Domain 5: HITL (Human-in-the-Loop) Patterns
**Description:** How to implement HITL gates in the research agent — requesting approval, presenting structured clusters, handling user responses (approve all, approve some, redirect).

**PRD References:**
- Lines 60: "must present HITL research clusters for user approval before deep-dive verification"
- Lines 96-98: HITL Research Cluster Approval workflow
- Lines 167-173: FR I (HITL Research Clusters)

**Eval IDs:** RB-011, RQ-012

**Skills to Consult:**
- `/skills/langchain/config/skills/langgraph-human-in-the-loop/`

**SME Handles:** @hwchase17, @Vtrivedy10

**Research Questions:**
1. How does the `request_approval_tool` work in Deep Agents?
2. How does LangGraph handle HITL interrupts? What are the state mechanics?
3. How should the agent present structured cluster data for user approval?
4. How does the agent resume after approval? What state is preserved?

---

### Domain 6: Web Research Tooling (web_search, web_fetch)
**Description:** How web_search and web_fetch work as native tools — capabilities, limitations, citation requirements, rate limits, and best practices for research agents.

**PRD References:**
- Lines 56: "native Opus 4.6 web_fetch and web_search tools"
- Lines 150-155: FR G (Citation and Source Tracking) — every cited URL must appear in trace as web_fetch call
- Lines 35: "multi-pass web research across all domains"

**Eval IDs:** RB-004, RB-005, RQ-004, RINFRA-004

**Skills to Consult:**
- (no specific skills — these are native Anthropic tools)

**SME Handles:** (none specifically)

**Research Questions:**
1. What are the parameters and return formats for web_search and web_fetch?
2. Are there rate limits or token costs specific to these tools?
3. How do these tools interact with the citation requirement (every cited URL = web_fetch call)?
4. Best practices for multi-pass research — when to search vs fetch?

---

### Domain 7: Research Bundle Schema & Synthesis Patterns
**Description:** The 17-section research bundle schema, YAML frontmatter requirements, topic-based organization, and how to produce a bundle usable by the spec-writer.

**PRD References:**
- Lines 99-100: Research Bundle Synthesis workflow
- Lines 175-180: FR J (Research Bundle Output) — 17 sections, YAML frontmatter, topic-based organization
- Lines 210-214: Required outputs list

**Eval IDs:** RINFRA-001, RINFRA-002, RINFRA-003, RQ-005, RQ-011, RI-002, RI-003

**Skills to Consult:**
- (structural — reference Full-Spec.md Section 5.3 schema)

**SME Handles:** (none specifically)

**Research Questions:**
1. What YAML frontmatter fields are required?
2. What are the exact 17 H2 sections required?
3. How should the PRD Coverage Matrix be structured for verification-agent consumption?
4. What does "organized by topic, not by source" mean in practice?
5. How should confidence assessments be calibrated?

---

### Domain 8: LangSmith Observability & Eval Infrastructure
**Description:** How LangSmith tracing, experiments, datasets, and evaluators work — needed because the research agent must produce traceable outputs that can be evaluated by the 38-eval suite.

**PRD References:**
- Lines 155: "all cited URLs must appear in the trace as web_fetch calls"
- Eval suite: All 38 evals reference trace_inspection, llm_as_judge, state_inspection, content_inspection methods

**Eval IDs:** All evals (the agent must produce evaluable traces)

**Skills to Consult:**
- `/skills/langsmith/config/skills/langsmith-trace/`
- `/skills/langsmith/config/skills/langsmith-evaluator/`
- `/skills/langsmith/config/skills/langsmith-evaluator-architect/`
- `/skills/langsmith/config/skills/langsmith-dataset/`

**SME Handles:** @hwchase17, @RLanceMartin

**Research Questions:**
1. How does LangSmith tracing work for Deep Agents? What trace structure is produced?
2. How do evaluators inspect traces for tool call verification?
3. How does llm_as_judge evaluation work in LangSmith?
4. What is the LangSmith experiment/dataset model for running eval suites?

---

### Domain 9: Gap/Contradiction Remediation & Research Quality
**Description:** Patterns for identifying research gaps and contradictions, performing root cause analysis, executing targeted remediation, and documenting resolution.

**PRD References:**
- Lines 73-76: Gap and Contradiction Remediation (stakeholder design intent)
- Lines 93-95: Gap and Contradiction Remediation workflow
- Lines 157-165: FR H (Gap and Contradiction Remediation)

**Eval IDs:** RQ-013

**Skills to Consult:**
- (process/methodology — not skill-specific)

**SME Handles:** (none)

**Research Questions:**
1. What are best practices for systematic gap identification in multi-source research?
2. How should contradictions between official docs and SME perspectives be resolved?
3. What severity framework should be used for prioritizing remediation?

---

### Domain 10: Per-Agent Memory (AGENTS.md)
**Description:** The per-agent memory system — each agent has its own `.agents/{agent-name}/AGENTS.md` file for persistent memory across sessions.

**PRD References:**
- Lines 215: Required output: `.agents/research-agent/AGENTS.md`
- Full-Spec C5: Per-agent AGENTS.md memory

**Eval IDs:** (implicit — agent must update its memory file)

**Skills to Consult:**
- `/skills/langchain/config/skills/deep-agents-memory/`

**SME Handles:** (none)

**Research Questions:**
1. What is the AGENTS.md schema/structure?
2. How should the research agent update its memory file?
3. What information should be persisted for future sessions?

---

## Phased Execution Plan

### Phase A (Highest Architectural Impact) — PRIORITY 1
- **Domain 1:** Deep Agents SDK Architecture
- **Domain 2:** LangGraph & Sub-Agent Patterns
- **Domain 3:** Anthropic Model Capabilities

**Rationale:** These three domains determine the fundamental architecture — how the agent is built, how it spawns sub-agents, and what model capabilities it can leverage. Every other domain depends on these.

### Phase B (Core Behavioral Patterns) — PRIORITY 2
- **Domain 4:** Skills System Architecture
- **Domain 5:** HITL Patterns
- **Domain 6:** Web Research Tooling

**Rationale:** These define the primary behavioral patterns the agent must implement — skills consumption, HITL gates, and web research mechanics.

### Phase C (Output & Integration) — PRIORITY 3
- **Domain 7:** Research Bundle Schema
- **Domain 8:** LangSmith Observability
- **Domain 9:** Gap/Contradiction Remediation
- **Domain 10:** Per-Agent Memory

**Rationale:** These define output formats, evaluation infrastructure, quality processes, and persistence — important but dependent on the architectural foundation from Phase A.

---

## Progress Tracker

| Domain | Status | Notes |
|--------|--------|-------|
| 1. Deep Agents SDK | NOT_STARTED | |
| 2. LangGraph & Sub-Agents | NOT_STARTED | |
| 3. Anthropic Model Capabilities | NOT_STARTED | |
| 4. Skills System | NOT_STARTED | |
| 5. HITL Patterns | NOT_STARTED | |
| 6. Web Research Tooling | NOT_STARTED | |
| 7. Research Bundle Schema | NOT_STARTED | |
| 8. LangSmith Observability | NOT_STARTED | |
| 9. Gap/Contradiction Remediation | NOT_STARTED | |
| 10. Per-Agent Memory | NOT_STARTED | |

---

## Gap and Contradiction Remediation Log

*(To be populated after Phase 5)*
