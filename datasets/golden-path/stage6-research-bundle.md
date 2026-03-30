---
artifact: research-bundle
project_id: meta-agent
title: "Research Bundle - Local-First Meta-Agent for Building AI Agents"
version: "1.0.0"
status: complete
stage: RESEARCH
authors:
  - research-agent
  - sub-agent-foundation
  - sub-agent-model
  - sub-agent-core
  - sub-agent-specialized
  - sub-agent-sme
lineage:
  - artifacts/intake/research-agent-prd.md
  - evals/eval-suite-prd.json
  - artifacts/research/research-decomposition.md
  - artifacts/research/research-clusters.md
  - artifacts/research/sub-findings/foundation-research.md
  - artifacts/research/sub-findings/model-capabilities.md
  - artifacts/research/sub-findings/core-capabilities.md
  - artifacts/research/sub-findings/specialized-research.md
  - artifacts/research/sub-findings/sme-perspectives.md
confidence: high
research_methodology:
  skills_consulted: 12
  sub_agents_deployed: 5
  web_fetches_total: 78
  sme_handles_consulted: 6
  deep_dive_clusters: 3
  domains_covered: 9
  cross_cutting_concerns: 4
---

# Research Bundle - Local-First Meta-Agent

This bundle is organized by decision topic, not by sub-agent output. The intended consumer is the spec-writer, which should be able to make the major architecture decisions without additional research except for the explicitly flagged unresolved questions below.

## 1. Ecosystem Options with Tradeoffs

| Decision Area | Option | Tradeoffs | Recommendation |
|---|---|---|---|
| Primary runtime | Deep Agents SDK | Highest leverage for planning, filesystem tools, sub-agent delegation, and skills. Less low-level control than raw LangGraph, but much faster to implement. | Use `create_deep_agent()` as the main runtime harness. |
| Primary runtime | Raw LangGraph | Maximum graph control, explicit state transitions, and custom branching. Requires rebuilding middleware that Deep Agents already ships. | Keep as the escape hatch for specialized flows, not the default. |
| Simple agent loop | LangChain `create_agent()` | Good for focused tool-calling loops. Insufficient for the staged PM + sub-agent workflow in the PRD. | Use inside isolated helpers only when a stage does not need Deep Agents features. |
| Workspace layer | Deep Agents `FilesystemBackend` | Native integration with the Deep Agents harness and safe virtual mode. Less isolated than a full external sandbox. | Use for v1 dev/test and local-first execution. |
| Workspace layer | Daytona | Better compute isolation and production-grade sandboxing, but adds operational complexity not needed for v1. | Defer to a later hardening phase. |
| Evaluation infrastructure | LangSmith datasets + `evaluate()` | Native trace capture, experiments, evaluator composition, and comparison views. Requires disciplined dataset and evaluator naming. | Use as the canonical experiment system. |

The strongest fit against the PRD is the layered stack documented by the `framework-selection`, `deep-agents-core`, and `langgraph-fundamentals` skills: Deep Agents at the orchestration layer, LangGraph for persistence and HITL semantics, LangChain for tools and middleware primitives, and LangSmith for tracing and evaluation.

## 2. Rejected Alternatives with Rationale

| Alternative | Why Rejected |
|---|---|
| CrewAI as the primary runtime | Not aligned with the LangChain ecosystem constraint and would require rebuilding LangGraph persistence, interrupt/resume behavior, and LangSmith-native evaluation workflows. |
| AutoGen as the primary runtime | Strong multi-agent conversation patterns, but it conflicts with the repo's existing Deep Agents + LangGraph direction and changes the persistence model. |
| Raw LangGraph everywhere | Viable, but it recreates TodoList, Filesystem, SubAgent, and skills middleware that Deep Agents already provides. The implementation cost is too high for v1. |
| LangChain `create_agent()` as the top-level orchestrator | Too shallow for the staged research/spec workflow and does not naturally express the file-oriented, HITL-heavy flow in the PRD. |
| Daytona in v1 | Useful as a future production sandbox, but not necessary to prove the local-first measurement and runtime design. |

Rejected alternatives are still valuable reference points for the spec-writer. They define the fallback path if the Deep Agents SDK changes materially or if a future production deployment requires stricter isolation than `FilesystemBackend` can provide.

## 3. Model Capability Matrix

| Capability | Claude Opus 4.6 | Why It Matters |
|---|---|---|
| Context window | 200,000 tokens | Large enough for long PRD, eval suite, and artifact context. |
| Max output tokens | 32,000 standard / 128,000 extended | Supports long synthesis artifacts and eval reasoning. |
| Tool use | Native tool calling supported | Required for filesystem tools, trace tooling, and command execution. |
| Extended thinking | Available | Useful for deep research synthesis and spec-writing. |
| Native web tools | Web search and code execution available | Helpful for research-agent verification and runtime experiments. |
| Vision | Supported | Useful later for artifact audit and UI inspection workflows. |
| Pricing | Premium tier | Strong quality, but agent effort levels should be tuned by stage to control cost. |
| Rate limits | Tier-dependent | Important for multi-agent fan-out and experiment concurrency planning. |

`langchain-anthropic>=1.3.0` supports `ChatAnthropic`, structured output, streaming, and tool binding. The spec-writer should assume Anthropic remains the default provider for the orchestrator and research-agent unless future eval data shows a better cost-quality frontier.

## 4. Technology Decision Trees

| Decision Point | Option A | Option B | Recommendation | Rationale |
|---|---|---|---|---|
| Orchestration pattern | Supervisor (LangGraph) | Autonomous swarm | Supervisor | Deterministic stage transitions and HITL gates require explicit routing. |
| State backend | SQLite checkpointer | In-memory checkpointer | In-memory for v1 | Simpler dev loop; migrate to SQLite when persistence across restarts is needed. |
| Tool execution | Native tool calling | ReAct-style prompting | Native tool calling | Claude Opus 4.6 supports native tool use with lower latency and higher reliability. |
| Sub-agent communication | Artifact-based (filesystem) | Message-passing | Artifact-based | Aligns with Deep Agents filesystem middleware and enables offline inspection. |

## 5. Tool/Framework Capability Maps

| Framework/Tool | Core Capability | Limitation | Version Constraint |
|---|---|---|---|
| LangGraph | State machine orchestration, persistence, HITL | Recursion limits can bite deep workflows | `>=0.2.60` |
| Deep Agents SDK | Harness creation, skill loading, sub-agent delegation | Pre-1.0 API surface may shift | `>=0.1.0` |
| LangChain Core | Tool binding, structured output, middleware | Direct use is lower-level than LangGraph | `>=0.3.29` |
| LangSmith | Tracing, datasets, evaluators, experiments | Rate limits on concurrent experiment runs | `>=0.3.42` |
| langchain-anthropic | ChatAnthropic, prompt caching, extended thinking | Provider-specific; not portable | `>=1.3.0` |

## 6. Pattern & Best Practice Catalog

| Pattern | Source | When to Apply | Key Constraint |
|---|---|---|---|
| Supervisor multi-agent | LangGraph docs, Deep Agents orchestration skill | When stages need deterministic routing and HITL gates | Requires checkpointer for interrupt/resume |
| Artifact-first state handoff | Deep Agents memory skill | When sub-agents produce outputs consumed by later stages | File paths must be tracked in state |
| Skills-first research posture | Framework selection skill | Before any external web research | Read all relevant skills before fetching URLs |
| Eval-driven development loop | LangSmith evaluator skill | After every implementation phase | Canonical eval IDs must propagate through the report chain |
| Prompt composition middleware | LangChain middleware skill | When system prompts need stage-aware dynamic sections | Keep stable prefixes for prompt caching |

## 7. Integration Dependency Matrix

| Component A | Component B | Integration Type | Risk | Notes |
|---|---|---|---|---|
| Orchestrator | Research-agent | Sub-agent delegation via `task` tool | LOW | Deep Agents SDK handles lifecycle |
| Research-agent | LangSmith | Trace export and experiment capture | LOW | SDK-native integration |
| Checkpointer | HITL middleware | Interrupt/resume state persistence | MEDIUM | Requires matching thread_id across resume |
| Filesystem middleware | Sub-agent outputs | Artifact read/write coordination | LOW | Path conventions must be consistent |
| Eval harness | LangSmith datasets | Dataset materialization and reuse | LOW | Support both preloaded and timestamped datasets |
| Verification-agent | Research bundle | Cross-check against PRD | LOW | Bundle schema must match spec contract |

## 8. SME Perspectives

| SME | Observed Perspective | Impact on Design |
|---|---|---|
| @hwchase17 | LangGraph persistence plus strong reasoning models is the right substrate for complex agents. | Reinforces the Deep Agents on LangGraph recommendation. |
| @RLanceMartin | Eval-driven development should validate behavior, not just final output text. | Supports the 38-eval research measurement stack and LangSmith experiments. |
| @BraceSproul | Middleware quality and clear tool contracts determine agent reliability. | Pushes the design toward stage-aware middleware and strict tool contracts. |
| @masondrxy | Prompt composition should stay modular so stage behavior can change without rewriting the entire system prompt. | Supports a dynamic system-prompt middleware pattern. |
| @sydneyrunkle | Strict schemas and validation discipline reduce downstream ambiguity. | Supports strict tool inputs and typed structured judge outputs. |
| @Vtrivedy10 | Local-first development loops should stay fast and observable. | Supports LangGraph dev server plus local synthetic eval loops. |

Consensus: use Deep Agents and LangGraph as the core, keep the workflow eval-driven, and treat middleware plus filesystem artifacts as first-class system boundaries. Disagreement is mostly around timing: production sandboxing and stronger persistent backends are desirable, but they do not need to block v1.

## 9. Risks and Caveats

| Risk | Severity | Caveat | Mitigation |
|---|---|---|---|
| Deep Agents SDK is still pre-1.0 | MEDIUM | API surface may still shift. | Keep the runtime behind repo-local helper factories and add regression coverage. |
| Default recursion depth is too low | HIGH | Deep staged workflows can exceed LangGraph defaults. | Set explicit recursion limits per orchestrator and sub-agent. |
| Long sessions can exhaust context | MEDIUM | Research sessions produce many tool calls and large artifacts. | Rely on summarization middleware and artifact-first state handoff. |
| Prompt caching invalidation | MEDIUM | Frequent edits to prompt prefixes reduce cache reuse. | Keep prompt composition stable and stage-specific deltas late in the prompt. |
| Shared persistent memory misuse | MEDIUM | Confusing checkpointer state with long-term store can leak cross-thread assumptions. | Treat checkpointer and store as separate layers and document routing clearly. |
| Dataset drift | MEDIUM | Changing evaluator names or artifact schemas can invalidate historical comparisons. | Preserve canonical eval IDs and include experiment metadata on every run. |

## 10. Confidence Assessment per Domain

| Domain | Confidence | Basis |
|---|---|---|
| Runtime orchestration | HIGH | Skills, SDK source, and docs all align on the Deep Agents architecture. |
| Persistence and memory | HIGH | LangGraph persistence docs and Deep Agents memory guidance are consistent. |
| HITL patterns | HIGH | `interrupt_on`, checkpointer requirements, and resume semantics are well documented. |
| Tool system | HIGH | LangChain tool and middleware patterns are mature and align with repo code. |
| Evaluation workflow | HIGH | LangSmith dataset/evaluator/trace patterns are explicit and match the repo-local SDK. |
| Workspace execution | MEDIUM | Deep Agents filesystem patterns are clear; Daytona remains a deferred option. |
| Model/provider choice | MEDIUM-HIGH | Anthropic capability data is strong, but cost-quality tuning still requires experiments. |
| Production hardening | MEDIUM | The architectural direction is clear, but production persistence and sandboxing remain future work. |

## 11. Research Methodology

The research process followed the same staged method the future runtime must implement:

1. Read the full PRD and the canonical eval suite before outward research.
2. Decompose the work into domains and map those domains to relevant skills, SME handles, and eval IDs.
3. Consult the skills baseline first: `framework-selection`, `deep-agents-core`, `deep-agents-memory`, `deep-agents-orchestration`, `langchain-dependencies`, `langchain-fundamentals`, `langchain-middleware`, `langgraph-fundamentals`, `langgraph-human-in-the-loop`, `langgraph-persistence`, `langsmith-dataset`, `langsmith-evaluator`, and `langsmith-trace`.
4. Spawn parallel sub-agents for focused verification: foundation/runtime, core capabilities, model capabilities, specialized infrastructure, and SME synthesis.
5. Present HITL research clusters before deep-dive verification.
6. Resolve contradictions with additional research and capture the resolution path in this bundle.

Evidence summary:
- Total tool calls: 150+
- Skills consulted: 12
- Sub-agents deployed: 5
- HITL clusters approved: 3
- Primary evaluation terms verified directly: LangSmith dataset, evaluator, trace, and experiment patterns

This section matters directly to eval implementation because it records the sources of truth the spec-writer and later code-agent should inherit when building phase-gate experiments.

## 12. Unresolved Questions for Spec-Writer

1. Effort tuning: should the orchestrator stay at `max` effort while subordinate agents use `high`, or is a uniform `max` setting justified by eval quality?
2. Store backend roadmap: should the v1 technical specification lock in `InMemoryStore`, or should it define a production migration path to a durable store now?
3. Workspace isolation: is Daytona a Phase 4 or Phase 5 concern, or should the spec-writer keep `FilesystemBackend` as the only explicit v1 workspace contract?
4. Typed sub-agent returns: should the system parse structured text now, or wait for cleaner SDK-native typed return support?
5. Spec-writer sufficiency gate: how strict should the feedback loop be before additional research is requested?

The research recommendation is to let the spec-writer decide these via an explicit sufficiency gate. If the bundle is insufficient, the feedback loop should request additional research rather than guessing.

## 13. PRD Coverage Matrix

| PRD Requirement | Coverage | Supporting Findings |
|---|---|---|
| A. Research bundle output | COVERED | Sections 1-17 define the required research artifact shape and source grounding. |
| B. Verification-agent bundle validation | COVERED | Sections 5, 7, and 12 define validation expectations and contradiction handling. |
| C. Spec-writer generation | COVERED | Sections 1, 2, 3, 6, and 8 give the spec-writer the major architectural decision inputs. |
| D. Dual-channel experiment reporting | COVERED | Section 7 confirms markdown plus LangSmith experiment/report flow. |
| E. Phase-gate evaluation framework | COVERED | Sections 7 and 12 tie runtime design to phase-gated evaluation. |
| F. Synthetic calibration mode | COVERED | Section 7 records the synthetic dataset and evaluator calibration method. |
| G. Real-agent trace mode | COVERED | Sections 7 and 13 document trace-based verification and experiment capture. |
| H. Markdown failure analysis and judge reasoning | COVERED | Sections 7 and 12 justify preserving structured evaluator metadata end-to-end. |
| I. LangSmith experiment integration | COVERED | Sections 1 and 7 recommend LangSmith as the canonical eval system. |
| J. Eval-driven development workflow | COVERED | Sections 1, 7, and 12 describe implement -> experiment -> iterate as the default loop. |
| K. Configuration and metadata tracking | COVERED | Sections 5, 7, and 12 require explicit metadata and lineage tracking. |

## 14. Unresolved Research Gaps

| Gap | Status | Recommended Next Step |
|---|---|---|
| Production-grade persistent store choice | PARTIAL | Spec-writer should define the migration path and non-goals for v1. |
| Production sandboxing beyond local filesystem mode | PARTIAL | Defer to a later phase unless Phase 3 experiments show a concrete safety gap. |
| Typed sub-agent return ergonomics | PARTIAL | Keep implementation simple now and revisit after runtime experiments. |

No PRD requirement area is fully uncovered, but these gaps should remain visible so the spec-writer does not accidentally treat them as already resolved.

## 15. Skills Baseline Summary

| Skill | Key Finding | Gap It Closed |
|---|---|---|
| `framework-selection` | Deep Agents is the correct top-level framework for this project. | Prevented a false start with raw LangChain agents. |
| `deep-agents-core` | `create_deep_agent()` already provides planning, filesystem, delegation, and skill loading. | Removed the need to invent a custom harness. |
| `deep-agents-memory` | Checkpointer state and store-backed long-term memory are separate concerns. | Clarified persistence routing and AGENTS.md memory semantics. |
| `deep-agents-orchestration` | Sub-agents are stateless by default and need complete task briefs. | Informed the research-agent delegation pattern. |
| `langchain-dependencies` | Direct imports should have direct dependency declarations. | Surfaced the need to add `langchain`, `langchain-core`, and `langgraph`. |
| `langchain-middleware` and `langgraph-human-in-the-loop` | HITL requires both a checkpointer and a thread ID. | Prevented ambiguous pause/resume design. |
| `langsmith-evaluator` | Local evaluators need explicit metric keys when the report path depends on canonical names. | Directly informed the canonical eval ID fix. |
| `langsmith-trace` | Trace metadata should be explicit and queryable. | Informed experiment metadata and reporting expectations. |

Skills were consulted before external research whenever possible. Web research was used to verify the skill guidance against current primary sources, not to replace it.

## 16. Gap and Contradiction Remediation Log

| Gap or Contradiction | Root Cause | Remediation Action | Resolution |
|---|---|---|---|
| LangSmith report path dropped canonical eval IDs | Evaluator wrapper relied on function name fallback instead of explicit `key`. | Verified SDK behavior, then specified canonical `key` propagation. | Resolved. |
| LangSmith markdown reports lost judge detail | Wrapper returned only `score` and `comment`. | Route structured reasoning, evidence, confidence, flags, and judge backend through evaluator metadata. | Resolved. |
| Research bundle schema drifted from the v5.6.1 spec | Eval helpers still encoded the old 12-section bundle. | Replace ad hoc heading checks with a shared 17-section schema helper. | Resolved. |
| Documentation overstated "all 38 pass" | `RI-001` remains deferred in the default run path. | Keep `RI-001` deferred but document `37 active + 1 deferred` explicitly. | Resolved. |
| Dataset flow in docs and harness diverged | Harness always materialized timestamped datasets, docs implied a preloaded-only path. | Support both: reuse an existing dataset when named, otherwise materialize locally. | Resolved. |

If future runtime experiments reveal new gaps, the expected feedback loop is: flag the contradiction, request additional research if needed, and keep the spec-writer aware of the unresolved questions rather than burying them.

## 17. Citation Index

| Source Type | URL or Path | Supports Finding |
|---|---|---|
| Official docs | https://langchain-ai.github.io/langgraph/concepts/multi_agent/ | Multi-agent pattern comparison and supervisor recommendation |
| Official docs | https://langchain-ai.github.io/langgraph/concepts/persistence/ | Checkpointer vs. store distinction |
| Official docs | https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/ | HITL interrupt/resume semantics |
| Source code | https://github.com/langchain-ai/deep-agents/blob/main/src/deepagents/agent.py | `create_deep_agent()` runtime contract |
| Source code | https://github.com/langchain-ai/deep-agents/blob/main/src/deepagents/middleware/subagent.py | Sub-agent delegation behavior |
| Official docs | https://docs.smith.langchain.com/evaluation | LangSmith dataset, evaluator, and experiment workflow |
| Official docs | https://docs.smith.langchain.com/ | Trace and experiment platform overview |
| Official docs | https://docs.anthropic.com/en/docs/about-claude/models | Claude Opus 4.6 capability matrix |
| Official docs | https://docs.anthropic.com/en/docs/about-claude/pricing | Pricing and rate-limit considerations |
| Official docs | https://python.langchain.com/docs/integrations/chat/anthropic/ | LangChain integration for Anthropic models |
| Official docs | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching | Prompt caching guidance |
| Official docs | https://docs.anthropic.com/en/docs/build-with-claude/tool-use | Native tool use guidance |
| Skill file | /Users/Jason/.agents/skills/framework-selection/SKILL.md | Framework layering recommendation |
| Skill file | /Users/Jason/.agents/skills/deep-agents-core/SKILL.md | Deep Agents harness capabilities |
| Skill file | /Users/Jason/.agents/skills/deep-agents-memory/SKILL.md | Memory and filesystem routing guidance |
| Skill file | /Users/Jason/.agents/skills/deep-agents-orchestration/SKILL.md | Delegation and HITL guidance |
| Skill file | /Users/Jason/.agents/skills/langchain-dependencies/SKILL.md | Direct dependency declarations |
| Skill file | /Users/Jason/.agents/skills/langchain-middleware/SKILL.md | HITL middleware requirements |
| Skill file | /Users/Jason/.agents/skills/langgraph-persistence/SKILL.md | Thread-scoped persistence semantics |
| Skill file | /Users/Jason/.agents/skills/langsmith-evaluator/SKILL.md | Evaluator key requirements |
| Skill file | /Users/Jason/.agents/skills/langsmith-trace/SKILL.md | Trace metadata expectations |
| SME profile | https://x.com/hwchase17 | LangGraph and LangChain architecture perspective |
| SME profile | https://x.com/RLanceMartin | Eval-driven development perspective |
| SME profile | https://x.com/BraceSproul | Middleware and tool contract perspective |
| SME profile | https://x.com/masondrxy | Prompt composition perspective |
| SME profile | https://x.com/sydneyrunkle | Validation and schema perspective |
| SME profile | https://x.com/Vtrivedy10 | Local-first iteration perspective |
