---
artifact: research-decomposition
project_id: meta-agent
title: "PRD Research Decomposition — Meta-Agent"
version: "1.0.0"
status: in_progress
stage: RESEARCH
authors:
  - research-agent
lineage:
  - artifacts/intake/prd.md
  - evals/eval-suite-prd.yaml
---

# PRD Research Decomposition

## Purpose
This file is the research agent's structured decomposition of the approved PRD into discrete research topics. Each topic maps to specific PRD lines and eval requirements. This file serves as:
1. The research agenda — what must be investigated
2. A progress tracker — checked off as research completes
3. A traceability artifact — every topic cites its PRD origin

## Methodology
- Read full PRD (285 lines) and eval suite (13 evals)
- Identified 9 primary research domains from functional requirements A–G plus cross-cutting concerns
- Decomposed each domain into specific research questions
- Prioritized by architectural impact (domains that constrain other decisions come first)
- Identified cross-cutting concerns that span multiple domains

---

## Domain 1: Agent Orchestration Architecture
**Priority:** CRITICAL — this decision constrains all other domains
**PRD Source:** Stakeholder Design Intent > Sub-Agent Delegation (lines 48–50), Non-Goals (line 78: "does not prescribe a final graph topology"), Core Product Principle (lines 85–95), Constraints (line 237: "built in the LangChain ecosystem")
**Eval Relevance:** EVAL-013 (architecture decisions must be evidence-backed)

### Research Questions
- [ ] What orchestration patterns does LangGraph support? (graph topologies, state machines, agent-supervisor, hierarchical)
- [ ] What is the Deep Agents SDK and how does it relate to LangGraph? (create_deep_agent, middleware system, auto-attached capabilities)
- [ ] How do LangGraph's StateGraph and MessageGraph compare for multi-stage workflows?
- [ ] What is the current recommended pattern for multi-agent orchestration in LangGraph? (supervisor vs. swarm vs. hierarchical)
- [ ] How does LangGraph handle sub-agent spawning and parallel execution?
- [ ] What are the tradeoffs between single-graph and multi-graph architectures?
- [ ] What does @hwchase17 recommend for complex multi-stage agent systems?
- [ ] What does @RLanceMartin say about production agent patterns?

### Skills to Consult
- `/skills/langchain/` — LangGraph orchestration patterns, graph design
- `/skills/langsmith/` — observability implications of different architectures

---

## Domain 2: State Management & Persistence
**Priority:** CRITICAL — determines how artifacts flow between stages
**PRD Source:** Artifact Continuity and State Requirements (lines 194–204), Artifact-Driven Communication (lines 34–37), Required Outputs (lines 184–193)
**Eval Relevance:** EVAL-012 (artifact lineage preserved across stages)

### Research Questions
- [ ] How does LangGraph manage state? (TypedDict, Pydantic models, checkpointing)
- [ ] What checkpointing backends does LangGraph support? (MemorySaver, SqliteSaver, PostgresSaver)
- [ ] How can state be persisted across sessions for long-running workflows?
- [ ] How should artifacts (PRD, research bundle, spec, plan) be stored? (filesystem vs. state vs. both)
- [ ] What is the LangGraph `Store` abstraction and when should it be used vs. checkpointer?
- [ ] How does state flow between parent graphs and sub-agents?
- [ ] What patterns exist for artifact lineage tracking in LangGraph-based systems?
- [ ] How do Deep Agents handle state — does the SDK provide state management middleware?

### Skills to Consult
- `/skills/langchain/` — state management patterns, persistence options
- `/skills/langsmith/` — how state relates to trace structure

---

## Domain 3: Human-in-the-Loop (HITL) Patterns
**Priority:** HIGH — required for all approval gates
**PRD Source:** FR-G Human-in-the-Loop Collaboration (lines 175–181), Configurable User Participation (lines 42–44), Stakeholder Design Intent (lines 28–32)
**Eval Relevance:** EVAL-011 (review checkpoints fire at all required gates), EVAL-002 (PRD supports iterative revision)

### Research Questions
- [ ] What HITL patterns does LangGraph support? (interrupt_before, interrupt_after, dynamic breakpoints)
- [ ] How does `interrupt` work in LangGraph's event loop? (pause/resume semantics)
- [ ] How should approval history be captured and persisted?
- [ ] What is the pattern for configurable HITL — toggling between autonomous and collaborative modes?
- [ ] How does LangGraph Studio visualize HITL interrupts?
- [ ] What does the Deep Agents SDK provide for HITL? (interrupt_on config)
- [ ] What are best practices for HITL in multi-agent systems where sub-agents also need approval?

### Skills to Consult
- `/skills/langchain/` — interrupt patterns, approval flows
- `/skills/langsmith/` — how HITL events appear in traces

---

## Domain 4: Tool System & Contracts
**Priority:** HIGH — tools are the agent's primary interface to workspace and external services
**PRD Source:** Technical-Spec Content Requirements (lines 211–212: "tool descriptions and tool message structures", "tool interfaces and data contracts"), FR-E Local Implementation (lines 166–171)
**Eval Relevance:** EVAL-009 (system operates against local workspace files)

### Research Questions
- [ ] What tool patterns does LangChain support? (@tool decorator, StructuredTool, BaseTool)
- [ ] How does the Deep Agents SDK handle tool registration and middleware? (FilesystemMiddleware, ToolErrorMiddleware)
- [ ] What is the current best practice for filesystem tools in LangGraph agents?
- [ ] How should tool errors be handled and surfaced to the agent?
- [ ] What tools does Anthropic's Claude Opus 4.6 natively support? (web_fetch, web_search, code execution)
- [ ] How does tool_as_code (programmatic tool calling) work in Opus 4.6?
- [ ] What tool patterns does @BraceSproul recommend for complex agents?
- [ ] How should tool contracts be documented for inter-agent communication?

### Skills to Consult
- `/skills/langchain/` — tool design patterns, middleware
- `/skills/anthropic/` — Opus 4.6 native tool capabilities

---

## Domain 5: Prompt Engineering & Context Management
**Priority:** HIGH — prompt strategy determines agent quality
**PRD Source:** Technical-Spec Content Requirements (lines 208–210: "prompt strategy", "system prompts"), Deep Research Posture (lines 39–41), Quality Requirements (lines 232–236)
**Eval Relevance:** EVAL-006 (spec must be exhaustive including prompts), EVAL-013 (evidence-backed decisions)

### Research Questions
- [ ] What prompt strategies work best for multi-stage agent systems? (dynamic system prompts, stage-aware prompts)
- [ ] How does context management work in long-running LangGraph agents? (summarization, context window management)
- [ ] What does the Deep Agents SDK provide for prompt management? (SummarizationMiddleware, prompt caching)
- [ ] How should system prompts be composed for agents that need to behave differently across workflow stages?
- [ ] What is Anthropic's guidance on prompt engineering for Claude Opus 4.6?
- [ ] How does prompt caching work with Anthropic models? (cache breakpoints, cost implications)
- [ ] What patterns does @masondrxy share about agent prompt design?
- [ ] How should inter-agent prompts differ from user-facing prompts?

### Skills to Consult
- `/skills/langchain/` — prompt composition, context engineering
- `/skills/anthropic/` — Claude-specific prompt patterns, caching

---

## Domain 6: Evaluation & Observability
**Priority:** HIGH — the system must create eval workflows for agents it builds
**PRD Source:** FR-F Evaluation and Audit (lines 172–178), Evaluation Design and Execution workflow (lines 131–134), Research and Source-of-Truth Requirements (lines 223–228)
**Eval Relevance:** EVAL-010 (LangSmith-aligned evaluation workflows), EVAL-005 (research extracts constraints not just summaries)

### Research Questions
- [ ] What evaluation patterns does LangSmith support? (datasets, evaluators, experiments, online eval)
- [ ] How does LangSmith trace inspection work? (run trees, token tracking, feedback)
- [ ] What evaluator types are available? (LLM-as-judge, heuristic, custom Python)
- [ ] How should synthetic datasets be structured for agent evaluation?
- [ ] What is the current best practice for eval-driven development in the LangChain ecosystem?
- [ ] How does @RLanceMartin approach evaluation design for agents?
- [ ] What audit patterns exist for inspecting pre-existing LangChain agents?
- [ ] How do traces relate to evaluation — can evals be triggered from trace data?

### Skills to Consult
- `/skills/langsmith/` — evaluation workflows, dataset creation, trace inspection
- `/skills/langchain/` — how agent outputs map to evaluable assertions

---

## Domain 7: Virtual Workspace & Execution Environment
**Priority:** MEDIUM — needed for execution stage but doesn't block earlier stages
**PRD Source:** Stakeholder Design Intent > Virtual Workspace Access (lines 52–54), FR-E Local Implementation (lines 166–171), Local-First Development Requirements (lines 229–234)
**Eval Relevance:** EVAL-009 (system operates against local workspace files)

### Research Questions
- [ ] What is the Deep Agents CLI filesystem middleware? (capabilities, sandboxing, virtual mode)
- [ ] What is Daytona and how does it compare to other sandbox options?
- [ ] What is OpenSWE and what does it provide for agent execution?
- [ ] How does the LangGraph dev server work? (langgraph.json, hot reload, Studio integration)
- [ ] What is the recommended local development workflow for LangGraph agents?
- [ ] How should file operations be sandboxed for safety? (path validation, workspace scoping)
- [ ] What does @Vtrivedy10 share about agent development workflows?

### Skills to Consult
- `/skills/langchain/` — dev server setup, filesystem patterns

---

## Domain 8: Model Capabilities (Anthropic Claude Opus 4.6)
**Priority:** MEDIUM — informs tool and prompt decisions but doesn't drive architecture
**PRD Source:** Constraints (line 237: "LangChain ecosystem"), Quality Requirements (lines 232–236: "state of the art"), Non-Goals (line 80: "does not lock to single model provider")
**Eval Relevance:** EVAL-013 (evidence-backed decisions)

### Research Questions
- [ ] What are Claude Opus 4.6's capabilities? (context window, tool use, coding, reasoning)
- [ ] What are the pricing and rate limits for Opus 4.6?
- [ ] What native tools does Opus 4.6 provide? (web search, code execution, file handling)
- [ ] How does tool_as_code / programmatic tool calling work?
- [ ] What is Anthropic's extended thinking / reasoning mode?
- [ ] How does langchain-anthropic integrate with LangGraph? (ChatAnthropic, tool binding)
- [ ] What are the known limitations or caveats of Opus 4.6 for agentic use cases?
- [ ] What does Anthropic's official documentation say about building agents with Claude?

### Skills to Consult
- `/skills/anthropic/` — model capabilities, API reference, agent patterns

---

## Domain 9: Safety, Guardrails & Error Handling
**Priority:** MEDIUM — cross-cutting concern that affects all stages
**PRD Source:** Technical-Spec Content Requirements (lines 219–221: "error handling", "safety and guardrail approach"), Risks (lines 260–266), FR-G (lines 179–181: "review checkpoints before local file writes")
**Eval Relevance:** EVAL-011 (review checkpoints enforced)

### Research Questions
- [ ] What safety patterns exist for LangGraph agents? (recursion limits, token budgets, path validation)
- [ ] How should error handling work in multi-agent systems? (tool errors, sub-agent failures, cascading failures)
- [ ] What guardrails does the Deep Agents SDK provide? (safety middleware, recursion limits)?
- [ ] How should file operations be restricted to prevent workspace escape?
- [ ] What patterns exist for graceful degradation when a sub-agent fails?
- [ ] How does @sydneyrunkle approach validation and safety in Python agent systems? (Pydantic patterns)

### Skills to Consult
- `/skills/langchain/` — error handling, safety middleware
- `/skills/anthropic/` — model-level safety, content filtering

---

## Cross-Cutting Concerns (Span Multiple Domains)

### CC-1: Artifact Schema Design
**Spans:** Domain 2 (state), Domain 4 (tools), Domain 6 (evaluation)
**PRD Source:** Required Outputs (lines 184–193), Artifact Continuity (lines 194–204)
**Question:** What schema should artifacts follow? How should frontmatter be structured? How do artifacts relate to state and traces?

### CC-2: Multi-Agent Communication Patterns
**Spans:** Domain 1 (orchestration), Domain 2 (state), Domain 4 (tools)
**PRD Source:** Artifact-Driven Communication (lines 34–37), Sub-Agent Delegation (lines 48–50)
**Question:** How should agents communicate — shared state, message passing, or artifact handoff? What does LangGraph recommend?

### CC-3: Research-to-Specification Pipeline
**Spans:** Domain 1 (orchestration), Domain 5 (prompts), Domain 6 (evaluation)
**PRD Source:** Core User Workflow 2 (lines 115–119), FR-B Research Workflow (lines 149–156), FR-C Technical Specification (lines 157–165)
**Question:** How should research findings flow into specification decisions? What verification step ensures the spec satisfies the PRD?

### CC-4: Quality as a Measurable Objective
**Spans:** Domain 6 (evaluation), Domain 8 (model capabilities)
**PRD Source:** Quality Requirements (lines 232–236), Assumptions (line 253: "state of the art is a measurable quality objective")
**Question:** How do we measure "state of the art" empirically? What eval benchmarks exist for agent systems?

---

## Research Execution Plan

### Phase 1: Foundation (Domains 1, 2, 8)
These must be researched first because orchestration architecture, state management, and model capabilities constrain all downstream decisions.

### Phase 2: Core Capabilities (Domains 3, 4, 5)
HITL, tools, and prompts can be researched in parallel once the architecture foundation is understood.

### Phase 3: Specialized Concerns (Domains 6, 7, 9)
Evaluation, workspace, and safety can be researched once the core architecture is clear.

### Phase 4: Cross-Cutting Synthesis
Resolve cross-cutting concerns by synthesizing findings across domains.

---

## Progress Tracker

| Domain | Status | Sub-agent Assigned | Key Findings |
|--------|--------|--------------------|--------------|
| 1. Orchestration Architecture | ⬜ Not started | — | — |
| 2. State & Persistence | ⬜ Not started | — | — |
| 3. HITL Patterns | ⬜ Not started | — | — |
| 4. Tool System | ⬜ Not started | — | — |
| 5. Prompt Engineering | ⬜ Not started | — | — |
| 6. Evaluation & Observability | ⬜ Not started | — | — |
| 7. Virtual Workspace | ⬜ Not started | — | — |
| 8. Model Capabilities | ⬜ Not started | — | — |
| 9. Safety & Guardrails | ⬜ Not started | — | — |
| CC-1. Artifact Schemas | ⬜ Not started | — | — |
| CC-2. Multi-Agent Comms | ⬜ Not started | — | — |
| CC-3. Research→Spec Pipeline | ⬜ Not started | — | — |
| CC-4. Quality Measurement | ⬜ Not started | — | — |
