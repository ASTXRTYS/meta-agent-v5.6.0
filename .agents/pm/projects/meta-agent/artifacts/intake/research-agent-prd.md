---
artifact: prd
project_id: meta-agent-research-agent
title: "Research Agent — Deep Ecosystem Researcher for the Meta-Agent System"
version: "1.0.0"
status: draft
stage: INTAKE
authors:
  - Jason (stakeholder)
  - orchestrator-agent (PM)
lineage:
  - /datasets/golden-path/prd-input.md
---

# Product Requirements Document

## Product
Research Agent — Deep Ecosystem Researcher for the Meta-Agent System

## Document Purpose
Define the product requirements for the research agent that operates within the meta-agent system (Phase 3). This agent sits between the PM/orchestrator agent and the spec-writer agent in the agent hierarchy. It receives an approved PRD and eval suite, performs state-of-the-art deep ecosystem research, deeply reflects and studies its own skills wich guide the previousley mentioned research process, and produces a research bundle that the spec-writer can use to generate a complete technical specification.

## Product Summary
The research agent is a specialized deep researcher that extends the PM agent's capabilities into the LangChain, LangGraph, Deep Agents, LangSmith, and Anthropic ecosystems. Given an approved PRD and its accompanying eval suite, the research agent decomposes the PRD into research domains, consults pre-loaded skills as baseline domain guidance, delegates parallel web research to sub-agents, gathers perspectives from specified subject matter experts, conducts deep-dive verification of critical findings, and synthesizes everything into a structured research bundle with full citations. The research bundle is the canonical input to the spec-writer agent.

## Problem Statement
The spec-writer agent cannot produce a high-quality, zero-ambiguity technical specification without deep ecosystem research. The PM agent gathers requirements and produces the PRD, but it does not have the depth of knowledge about LangChain internals, LangGraph patterns, Deep Agents SDK architecture, Anthropic model capabilities, or real-world production patterns needed to inform architectural decisions. Without a dedicated research phase, the spec-writer either makes uninformed architectural choices or the specification contains material ambiguity.

## Product Vision
Create a state-of-the-art deep research agent that produces research bundles so thorough that a spec-writer can make every architectural decision with HIGH confidence, backed by verified evidence from official documentation, SDK source code, real-world usage patterns, and subject matter expert perspectives.

## Goals
- Receive an approved PRD and eval suite from the upstream PM agent and fully decompose them into a structured research agenda.
- Consult pre-loaded LangChain, LangSmith, and Anthropic skills as baseline domain guidance before conducting web research.
- Perform deep, multi-pass web research across all domains identified in the PRD decomposition with zero blind spots.
- Research Anthropic model capabilities including full capability matrices, pricing, and rate limits for the current frontier model.
- Gather and contextualize perspectives from specified subject matter experts via their public Twitter/X posts and blog content.
- Produce a research bundle with mandatory citations that traces every finding to its source (docs, API reference, tweet, source code, etc.).
- Delegate research to sub-agents for parallel execution, with intentional reasoning about delegation topology.
- Present HITL research clusters for user approval before deep-dive verification passes.
- Support a feedback loop where the downstream spec-writer can request additional targeted research if the bundle is insufficient.

## Non-Goals
- The research agent does not make architectural decisions. It reports capabilities, options, and tradeoffs for the spec-writer to decide.
- The research agent does not write the technical specification.
- The research agent does not modify the PRD or eval suite it receives.
- The research agent does not conduct research outside the LangChain ecosystem and Anthropic model ecosystem unless the PRD explicitly requires it.
- The research agent does not interact directly with the end user for requirements gathering — that is the PM agent's responsibility.

## Target User
The primary consumer of the research agent's output is the spec-writer agent. The secondary consumer is the PM/orchestrator agent, which coordinates the handoff and may review the research bundle. The human user has visibility into the research process via HITL gates and can approve or redirect research clusters.

## Constraints
- The research agent must operate within the meta-agent system architecture (Deep Agents SDK, LangGraph).
- The research agent must use the skills directories at `/skills/langchain/`, `/skills/anthropic/`, and `/skills/langsmith/` as baseline domain guidance when available.
- The research agent must use native Opus 4.6 web_search_20260209 tool version for web research.
- The research agent must cite every finding with source type and URL/reference.
- The research agent must persist its PRD decomposition as a file (not just in-memory) for debuggability.
- The research agent must use sub-agents for parallel research execution — it cannot do all research as a single sequential agent.
- All Likert eval thresholds are >= 4.0 — the agent must achieve "Good" quality or above on every quality dimension.
- Python is the implementation language.
- The agent must be launchable on the LangGraph dev server.

## Stakeholder Design Intent

### Skills-First Research Posture
The agent should read and deeply internalize pre-loaded skills BEFORE conducting web research. Skills provide baseline domain guidance that should inform what the agent researches on the web. The agent should identify gaps in skill content and target web research to fill those specific gaps. Skills are not just reference material — they are foundational knowledge that structures the entire research agenda.

### Intentional Sub-Agent Deployment
When the agent delegates research to sub-agents, it must reason explicitly about the delegation topology: how many sub-agents, why each one exists, what each uniquely contributes, and why alternative topologies were rejected. Each sub-agent should have a clear reason for being. Mechanical fixed splits (one per domain) are insufficient — the agent should consider workload volume, domain dependencies, compute efficiency, and breadth vs. depth requirements.

### Gap and Contradiction Remediation
After collecting sub-agent findings, the agent must systematically identify gaps and contradictions across findings, diagnose root causes, plan targeted remediation, and execute verification research. Contradictions between sources should be explained (e.g., "both are correct in different contexts"), not just picked arbitrarily. Unresolvable gaps should be explicitly flagged with recommended approaches for the spec-writer.

### Configurable SME Tracking
The agent receives a list of Twitter/X handles for subject matter experts. It should systematically search each handle for relevant content, contextualize SME perspectives within the broader research (tying tweets to docs findings), and identify consensus or disagreements among SMEs. The handles are provided as configuration — the agent does not discover SMEs on its own.

### Debuggable Research Process
Every stage of the research process should produce observable artifacts: the decomposition file, sub-agent findings in a shared directory, the gap remediation log, the HITL cluster document, and the final research bundle. This ensures the human user can inspect, debug, and understand the agent's research decisions at any point.

## Core User Workflows

### 1. PRD Reception and Decomposition
The research agent receives an approved PRD and eval suite. It reads both documents in full (not just the first N lines), decomposes the PRD into discrete research domains, maps each domain to specific PRD line references and eval IDs, identifies which skills are relevant to each domain, and persists the decomposition as a structured Markdown file with a progress tracker.

### 2. Skills Consultation
The agent reads pre-loaded skills deeply (full files, not just first 100 lines), reflects on what it learned, internalizes skill content as baseline knowledge, identifies what gaps remain that require web research, and uses skill insights to shape its research agenda. The agent should read skills in priority order based on the decomposition phasing.

### 3. Sub-Agent Delegation
The agent reasons about delegation topology, articulates why each sub-agent exists and what it uniquely contributes, deploys sub-agents in parallel for web research, collects their findings from a shared output directory, and reviews all results systematically.

### 4. Gap and Contradiction Remediation
After collecting sub-agent findings, the agent catalogs gaps and contradictions with severity ratings, performs root cause analysis, creates a remediation plan, and executes targeted verification. Resolved items are documented. Unresolved items are flagged for the HITL deep-dive or deferred to the spec-writer with explicit reasoning.

### 5. HITL Research Cluster Approval
Before conducting deep-dive verification (source code review, issue/PR examination, real-world repo analysis), the agent groups research targets into themed clusters, explains what it wants to investigate and why, ties each target to specific PRD requirements, and requests user approval. The user can approve all, approve some, or redirect.

### 6. Research Bundle Synthesis
The agent synthesizes all findings (skills baseline, sub-agent web research, SME perspectives, deep-dive verification) into a structured research bundle organized by topic (not by source). The bundle includes ecosystem options with tradeoffs, rejected alternatives with rationale, model capability matrices, SME perspectives tied to technical findings, risks and caveats, confidence assessments per domain, research methodology documentation, and unresolved questions for the spec-writer.

### 7. Spec-Writer Feedback Loop
If the spec-writer determines the research bundle is insufficient for a particular area, it can request additional targeted research. The research agent receives the request, understands what's missing, and conducts focused follow-up research to fill the gap.

## Functional Requirements

### A. PRD and Eval Suite Consumption
- The agent must read the full PRD artifact (all lines, not truncated).
- The agent must read the full eval suite artifact.
- The agent must factor both the PRD requirements and eval criteria into its research agenda.
- The agent must not modify the PRD or eval suite.

### B. Research Decomposition
- The agent must decompose the PRD into discrete research domains.
- Each domain must cite specific PRD line numbers or sections.
- Each domain must map to relevant eval IDs.
- Each domain must identify which skills to consult.
- Each domain must identify which SME handles may be relevant.
- The decomposition must include a phased execution plan prioritized by architectural impact.
- The decomposition must include a progress tracker.
- The decomposition must be persisted as a Markdown file at `artifacts/research/research-decomposition.md`.

### C. Skills Utilization
- The agent must read pre-loaded skills from `/skills/langchain/`, `/skills/anthropic/`, and `/skills/langsmith/` directories.
- The agent must read skill files in full (not truncated to first 100 lines).
- The agent must reflect on skill content and internalize it as baseline knowledge.
- The agent must identify research gaps that skills do not cover and target web research to fill those gaps.
- The agent must trigger skills at contextually appropriate times based on the current research domain.

### D. Sub-Agent Delegation
- The agent must delegate web research to sub-agents for parallel execution.
- The agent must reason explicitly about delegation topology: number of sub-agents, grouping rationale, unique contribution of each, alternatives considered.
- Sub-agent task descriptions must include baseline knowledge from skills, specific research questions tied to PRD requirements, and expected output format.
- Sub-agents must write findings to a shared output directory.
- The main agent must read all sub-agent outputs thoroughly after completion.

### E. SME Consultation
- The agent must consult all Twitter/X handles provided in configuration.
- The agent must search each handle for content relevant to the research domains.
- The agent must contextualize SME perspectives by tying them to findings from docs and skills.
- The agent must identify consensus and disagreements among SMEs.

### F. Anthropic Model Research
- The agent must research the current frontier model's full capability matrix: context window, max output tokens, supported modalities, tool use capabilities, extended thinking, native tools.
- The agent must research pricing and rate limits.
- The agent must research tool_as_code / programmatic tool calling capabilities.
- The agent must research the langchain-anthropic integration package.
- The agent must NOT research latency benchmarks or multimodal support unless the PRD requires it.

### G. Citation and Source Tracking
- Every finding in the research bundle must have a citation.
- Citations must include source type (official docs, API reference, tweet, blog post, source code, skill file).
- Citations must include a URL or file path reference.
- Citations must be specific (link to the exact page, not a landing page).
- The agent must not cite URLs it did not actually fetch — all cited URLs must appear in the trace as web_fetch calls.

### H. Gap and Contradiction Remediation
- After collecting sub-agent findings, the agent must systematically identify gaps and contradictions.
- The agent must diagnose root causes for each gap or contradiction.
- The agent must create a remediation plan with specific actions.
- The agent must prioritize remediation by downstream impact on the spec-writer's decisions.
- The agent must execute verification research against primary sources.
- Resolved items must have explicit resolution statements with evidence.
- Unresolved items must be flagged with recommended approaches.
- The remediation log must be persisted in the decomposition file.

### I. HITL Research Clusters
- Before deep-dive verification, the agent must group research targets into themed clusters.
- Each cluster must explain what will be investigated and why.
- Each target must specify what the agent expects to learn.
- Each cluster must tie back to specific PRD requirements.
- Each cluster must include an estimated effort level.
- The agent must request user approval before proceeding with deep-dive research.

### J. Research Bundle Output
- The agent must produce a research bundle at `artifacts/research/research-bundle.md`.
- The bundle must include YAML frontmatter with lineage tracing to all input artifacts.
- The bundle must be organized by topic, not by source or sub-agent.
- The bundle must include: ecosystem options with tradeoffs, rejected alternatives with rationale, model capability matrix, SME perspectives, risks and caveats, confidence assessment per domain, research methodology, and unresolved questions.
- The bundle must be usable by the spec-writer without additional research for all major architectural decisions.

### K. Spec-Writer Feedback Loop
- The agent must accept targeted research requests from the spec-writer.
- The agent must execute focused follow-up research on the requested topic.
- The agent must update the research bundle with additional findings.

## Acceptance Criteria

### Decomposition
- Given an approved PRD and eval suite, the agent produces a decomposition file with domain-level research questions, PRD line citations, eval ID mappings, skills mappings, and a phased execution plan.

### Skills
- Given available skill directories, the agent reads skill files in full, reflects on content, and uses skill findings to guide subsequent web research.

### Sub-Agents
- Given a decomposition with multiple domains, the agent deploys sub-agents in parallel with intentional topology reasoning and collects all findings.

### Citations
- Given a completed research bundle, every finding has a citation with source type and URL, and every cited URL appears in the trace as a web_fetch call.

### HITL
- Given the need for deep-dive verification, the agent presents a HITL research cluster with grouped targets, rationale, and estimated effort before proceeding.

### Bundle Quality
- Given the complete research pipeline, the research bundle covers all PRD functional requirement areas with sufficient depth for the spec-writer to make informed architectural decisions.

### Feedback Loop
- Given a spec-writer request for additional research, the agent conducts targeted follow-up and updates the bundle.

## Required Outputs
- `artifacts/research/research-decomposition.md` — PRD decomposition with research agenda
- `artifacts/research/sub-findings/*.md` — Individual sub-agent research outputs
- `artifacts/research/research-clusters.md` — HITL cluster document
- `artifacts/research/research-bundle.md` — Final synthesized research bundle
- `.agents/research-agent/AGENTS.md` — Agent memory updated with research summary

## Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Agent hallucinates sources not actually fetched | HIGH | RB-005 eval cross-references cited URLs against trace; RQ-004 re-fetches for content accuracy |
| Agent reads PRD partially and misses requirements | HIGH | RB-001 verifies full read; RQ-001 checks decomposition covers all FRs |
| Skills are skipped entirely | HIGH | RB-007 binary check; RQ-007/008/009 evaluate full skills lifecycle |
| Sub-agent findings contradict each other | MEDIUM | RQ-013 evaluates gap/contradiction remediation quality |
| Research is surface-level (READMEs only) | HIGH | RQ-003 anchors penalize surface research; deep-dive HITL adds verification layer |
| Agent doesn't consider eval implications | MEDIUM | RB-002 checks eval suite read; RI-003 checks bundle addresses eval needs |
| Context window exhaustion during long research | MEDIUM | SummarizationMiddleware auto-compacts; sub-agent delegation distributes context load |

## Unresolved Questions
1. What is the maximum number of sub-agents the research agent should deploy? (The agent reasons dynamically, but should there be an upper bound?)
2. Should the research agent have a token budget or time budget for research? (Currently unconstrained.)
3. How should the feedback loop from the spec-writer be triggered? (Direct message, or orchestrator-mediated?)
4. Should the research agent version its research bundle if the spec-writer requests follow-up? (v1.0.0 → v1.1.0?)

## Configuration

### Twitter/X SME Handles
```yaml
twitter_handles:
  - handle: "@hwchase17"
    name: "Harrison Chase"
    role: "LangChain CEO"
    url: "https://x.com/hwchase17"
  - handle: "@Vtrivedy10"
    name: "Varun Trivedy"
    role: "LangChain"
    url: "https://x.com/Vtrivedy10"
  - handle: "@sydneyrunkle"
    name: "Sydney Runkle"
    role: "Pydantic / LangChain"
    url: "https://x.com/sydneyrunkle"
  - handle: "@masondrxy"
    name: "Mason Drexler"
    role: "LangChain"
    url: "https://x.com/masondrxy"
  - handle: "@BraceSproul"
    name: "Brace Sproul"
    role: "LangChain"
    url: "https://x.com/BraceSproul"
  - handle: "@RLanceMartin"
    name: "Lance Martin"
    role: "LangChain Developer Relations"
    url: "https://x.com/RLanceMartin"
```

### Skills Paths
```yaml
skills_paths:
  - "/skills/langchain/"   # 11 skills: framework-selection, deep-agents-*, langgraph-*, langchain-*
  - "/skills/anthropic/"   # Agent Skills spec + examples
  - "/skills/langsmith/"   # 3 skills: trace, dataset, evaluator
```

### Agent Configuration
```yaml
agent:
  type: deep_agent
  effort: max
  recursion_limit: 100
  middleware:
    - ToolErrorMiddleware
    - SummarizationToolMiddleware
    - SkillsMiddleware
  tools:
    - write_file
    - read_file
    - ls
    - edit_file
    - glob
    - grep
    - web_search
    - web_fetch
  server_side_tools:
    - web_search
    - web_fetch
```
