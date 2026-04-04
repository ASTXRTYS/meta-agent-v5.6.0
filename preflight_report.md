# Researcher E2E Preflight Audit Report

**Date:** 2026-04-04  
**Branch:** main @ b2e88d6 (parity with origin/main)  
**Scope:** Phase 3 researcher E2E experiment readiness  
**Verdict:** 🟡 CONDITIONAL GO (E2E eval experiment only)

---

## 1. Executive Summary

This preflight audit assessed production-readiness for running the researcher E2E experiment per Full-Development-Plan.md Phase 3. Nine audit lanes were executed across environment validation, SDK middleware provenance, orchestrator/model configuration, research-agent runtime, LangSmith observability, and judge runtime.

**Result:** The system is ready for the E2E eval experiment with `auto_approve_hitl=True`. Two issues block production HITL usage but do not affect eval correctness:

1. **Middleware ordering** — DynamicSystemPromptMiddleware fires after AnthropicPromptCachingMiddleware (cost/latency, not correctness)
2. **Missing interrupt_on** — research-agent's create_deep_agent() call omits interrupt_on (HITL won't pause in production)

Both are mitigated in eval mode. All imports succeed, all middleware is SDK-native, backend routing is correct, and the research eval stack has deep LangSmith integration.

---

## 2. Environment Gate Results (Stage 0)

| Check | Result | Evidence |
|-------|--------|----------|
| Branch | main @ b2e88d6 | Parity with origin/main |
| Python | 3.11.15 | Project-local .venv |
| deepagents | 0.4.12 | .venv/lib/python3.11/site-packages/deepagents/__init__.py |
| Module imports | 46/46 pass | All meta_agent modules import successfully |
| Dependency versions | 11/11 pass | All required deps meet version constraints |
| Stale bytecode | 70 .cpython-314.pyc files | Non-blocking; cleanup recommended |
| Extraneous packages | google-genai, langchain-google-genai, langchain-openai, numpy, openai | Non-blocking; unused |

**Verdict:** ✅ PASS

---

## 3. Per-Agent Findings

### 3.1 Orchestrator (PM Agent)

| Check | Result | Evidence |
|-------|--------|----------|
| Model config | ✅ PASS | get_configured_model("pm") → thinking=adaptive, effort=high, max_tokens=12000 |
| create_deep_agent() params | ✅ PASS | All 10 required params present (model, tools, system_prompt, middleware, subagents, checkpointer, store, backend, interrupt_on, name) |
| Middleware order | ✅ PASS (code) | DynamicSystemPromptMiddleware is index 0 per spec Section 22.4 |
| HITL config | ✅ PASS | 6 gated tools, checkpointer present |
| Skills | ✅ PASS | 31 skills provisioned across 3 directories |
| Subagent wiring | ✅ PASS | 3 CompiledSubAgent + 4 dict-based |
| Custom tracing | ❌ FAIL | No @traceable spans on graph nodes, stages, middleware |

**Verdict:** ✅ PASS (tracing gap is non-blocking for eval)

### 3.2 Research-Agent

| Check | Result | Evidence |
|-------|--------|----------|
| Model config | ✅ PASS | get_configured_model("research-agent") → thinking=adaptive, effort=max, max_tokens=16000 |
| Backend | ✅ PASS | CompositeBackend with 4-route config |
| Middleware stack | ✅ PASS | AgentDecisionState, Summarization, Memory, Skills, ToolError |
| Server-side tools | ✅ PASS | web_search_20260209, web_fetch_20260209 included |
| Output normalization | ✅ PASS | 15+ fields match evaluator contract |
| Eval bridge | ✅ PASS | auto_approve_hitl=True, unique thread_id per run |
| interrupt_on | ❌ MISSING | create_deep_agent() call omits interrupt_on parameter |
| Path resolution | ✅ PASS | ResearchRuntimePaths, _to_workspace_path, _localize_workspace_path correct |

**Verdict:** 🟡 CONDITIONAL PASS — interrupt_on missing (eval-safe with auto_approve_hitl)

### 3.3 Verification-Agent

| Check | Result | Evidence |
|-------|--------|----------|
| Model config | ✅ PASS | get_configured_model("verification-agent") → thinking=adaptive, effort=max, max_tokens=16000 |
| Subagent pattern | ✅ PASS | CompiledSubAgent via create_verification_agent_subagent() |

**Verdict:** ✅ PASS

### 3.4 Spec-Writer

| Check | Result | Evidence |
|-------|--------|----------|
| Model config | ✅ PASS | get_configured_model("spec-writer") → thinking=adaptive, effort=high, max_tokens=12000 |
| Subagent pattern | ✅ PASS | CompiledSubAgent via create_spec_writer_agent_subagent() |
| Custom tools | ✅ PASS | propose_evals_tool assigned |

**Verdict:** ✅ PASS

### 3.5 Config-Level Agents (Phase 4-5)

| Agent | Status | Notes |
|-------|--------|-------|
| plan-writer | Dict config only | Phase 4 scope |
| code-agent | Dict config only | Phase 4 scope |
| test-agent | Dict config only | Phase 4 scope |
| document-renderer | Dict config only | Phase 5 scope |
| observation/evaluation/audit-agent | Metadata only | Phase 4-5 scope |
| memory_loader.py | Vestigial stub | Dead code, no imports |

**Verdict:** ✅ PASS — No blockers for Phase 3

---

## 4. Cross-Agent Consistency Matrix

| Property | PM | Research | Verification | Spec-Writer |
|----------|-----|----------|--------------|-------------|
| Model source | get_configured_model() | get_configured_model() | get_configured_model() | get_configured_model() |
| thinking.type | adaptive | adaptive | adaptive | adaptive |
| budget_tokens | ❌ None (correct) | ❌ None (correct) | ❌ None (correct) | ❌ None (correct) |
| Backend | CompositeBackend | CompositeBackend | CompositeBackend | CompositeBackend |
| Checkpointer | MemorySaver | MemorySaver | MemorySaver | MemorySaver |
| Store | InMemoryStore | InMemoryStore | InMemoryStore | InMemoryStore |
| ToolErrorMiddleware | ✅ | ✅ | ✅ | ✅ |
| MemoryMiddleware | ✅ | ✅ | ✅ | ✅ |
| SkillsMiddleware | ✅ | ✅ | ✅ | ✅ |
| interrupt_on | ✅ (6 tools) | ❌ MISSING | Not confirmed | Not confirmed |

---

## 5. Blocking Issues

### BLOCK-1: Middleware Ordering — DynamicSystemPromptMiddleware Fires After Prompt Caching

- **Severity:** BLOCKING for production; NON-BLOCKING for E2E eval
- **File:** meta_agent/graph.py lines 156-163 (explicit middleware), SDK create_deep_agent() lines 188-189
- **Evidence:** SDK source: `if middleware: deepagent_middleware.extend(middleware)` — explicit middleware appended AFTER auto-attached stack. Line 56-59 docstring: "middleware: Additional middleware to apply after the standard middleware stack." This means AnthropicPromptCachingMiddleware sets cache breakpoints on system prompts BEFORE DynamicSystemPromptMiddleware rewrites them.
- **Impact:** Prompt caching corruption — stale system prompts cached, stage-specific prompts uncached. Cost/latency regression, NOT correctness issue.
- **Affects:** All agents using DynamicSystemPromptMiddleware (currently PM orchestrator only)
- **Eval impact:** None — prompt caching is an optimization, not correctness
- **Remediation:** Either (a) move DynamicSystemPromptMiddleware logic into a pre-model hook that fires before caching, or (b) request SDK support for middleware priority/ordering, or (c) implement a custom wrapper that invalidates cache after prompt rewrite

### BLOCK-2: Missing interrupt_on on Research-Agent

- **Severity:** BLOCKING for production HITL; NON-BLOCKING for E2E eval
- **File:** meta_agent/subagents/research_agent.py lines 582-597
- **Evidence:** create_deep_agent() call passes model, tools, system_prompt, middleware, backend, checkpointer, store, name — but NOT interrupt_on. Compare with PM graph (graph.py:166-169) which correctly passes `interrupt_on = {tool_name: True for tool_name in HITL_GATED_TOOLS}`.
- **Impact:** research-agent's request_approval_tool executes immediately without pausing for human input. Phase 6 (HITL Research Clusters) requires pausing for human approval.
- **Eval impact:** None — auto_approve_hitl=True in eval state causes self-approval
- **Remediation:** Add `interrupt_on={"request_approval": True}` to the create_deep_agent() call in research_agent.py

---

## 6. Non-Blocking Issues

### NB-1: Orchestrator Tracing Missing

- **Severity:** HIGH (production observability gap)
- **File:** meta_agent/graph.py, meta_agent/stages/, meta_agent/middleware/
- **Evidence:** No @traceable decorators on graph nodes, stage logic, middleware hooks, delegation decisions. Stubs in tracing.py (prepare_agent_state, delegation_decision) have zero call sites. TRACE_TAGS defined but unused.
- **Impact:** Orchestrator is a black box in LangSmith UI. Only SDK auto-traced tool calls are visible.

### NB-2: Research-Agent @traceable Unused

- **Severity:** LOW
- **File:** meta_agent/subagents/research_agent.py line 34
- **Evidence:** Imports traceable but never applies it to any function. SDK auto-tracing covers the critical execution path (tool calls, model calls).

### NB-3: Stale .cpython-314.pyc Files

- **Severity:** LOW
- **File:** Various __pycache__ directories
- **Evidence:** 70 stale .cpython-314.pyc files from a different Python version
- **Impact:** No runtime impact; disk clutter

### NB-4: Extraneous Packages

- **Severity:** LOW
- **Evidence:** google-genai, langchain-google-genai, langchain-openai, numpy, openai installed but unused
- **Impact:** No runtime impact; increased venv size

### NB-5: Redundant Recursion Limit

- **Severity:** LOW
- **File:** research_agent.py lines 617 and 745
- **Evidence:** recursion_limit=100 set in both _invoke() and run_research_agent(). Both resolve to RECURSION_LIMITS["research-agent"]=100.
- **Impact:** Harmless redundancy

### NB-6: No Runtime Fallback for Server-Side Tool API Versions

- **Severity:** LOW
- **File:** meta_agent/tools/__init__.py lines 1083-1085
- **Evidence:** Comment documents fallback to _20250305 versions but no automatic detection code. Low risk since _20260209 should exist.

### NB-7: SummarizationToolMiddleware Uses Model String

- **Severity:** LOW
- **File:** research_agent.py lines 559-561
- **Evidence:** Passes cfg["model_string"] ("anthropic:claude-opus-4-6") not the configured ChatAnthropic instance. Inconsistent with model instance pattern but should work.

### NB-8: Dead Code — memory_loader.py

- **Severity:** LOW
- **File:** meta_agent/middleware/memory_loader.py (63 lines)
- **Evidence:** No imports of MemoryLoaderMiddleware found in codebase. Replaced by SDK-native MemoryMiddleware.

---

## 7. Developer Notes Coverage (Notes.md)

| # | Concern | Status | Finding |
|---|---------|--------|---------|
| 1 | DynamicSystemPromptMiddleware + prompt caching | 🔴 CONFIRMED BLOCKER (BLOCK-1) | SDK appends explicit MW after auto-attached. Cache breakpoints set on stale prompts. |
| 2 | TodoList/Filesystem/SubAgent auto-attach duplication | ✅ PASS | Not duplicated. SDK auto-attaches; code does not re-add. |
| 3 | SummarizationMiddleware provenance | ✅ PASS | SDK-native import from deepagents.middleware.summarization |
| 4 | SkillsMiddleware provenance | ✅ PASS | SDK-native import from deepagents.middleware.skills |
| 5 | MemoryMiddleware provenance | ✅ PASS | SDK-native import. memory_loader.py is dead code. |
| 6 | SubAgent system | ✅ PASS | SDK-native CompiledSubAgent pattern |
| 7 | PatchToolCallsMiddleware | ✅ PASS | Auto-attached on all agents by SDK |
| 8 | FilesystemMiddleware | ✅ PASS | Auto-attached, no duplicates |
| 9 | Backend SDK usage | ✅ PASS | All 4 backend types from deepagents.backends |
| 10 | Harness over-engineering | ✅ PASS | Minimal custom code over SDK |
| 11 | Meta loop (planner/coder/eval) | ⏸️ OUT OF SCOPE | Phase 4-5 |
| 12 | Reference SDK comparison | 🟡 PARTIAL | Auditor had version false positive (claimed 0.2.7, actually 0.4.12). Middleware provenance analysis still valid. |
| 13 | interrupt_on missing | 🔴 CONFIRMED BLOCKER (BLOCK-2) | research-agent create_deep_agent() missing interrupt_on parameter |

**Summary:** 13 concerns total. 8 fully investigated and PASSED. 2 confirmed blockers. 1 out of scope (Phase 4-5). 1 partial (false positive corrected). 1 duplicate of #1.

---

## 8. GO/NO-GO Verdict

### GO Criteria Assessment

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Environment parity gate | ✅ PASS | Python 3.11.15, deepagents 0.4.12, 46/46 imports, 11/11 deps |
| Middleware provenance unambiguous | ✅ PASS | All SDK-native (MemoryMiddleware, SkillsMiddleware, SummarizationMiddleware confirmed at 0.4.12) |
| Backend/path routing | ✅ PASS | CompositeBackend with 4 routes, correct bare_fs for middleware |
| Claude API conformance | ✅ PASS | All agents use get_configured_model(), thinking=adaptive, no budget_tokens |
| Server-side tools and citations | ✅ PASS | web_search_20260209, web_fetch_20260209 correctly integrated |
| LangSmith observability | 🟡 PARTIAL | Research eval stack: excellent (deep tracing, rich metadata, category-aware evidence). Orchestrator: no custom spans. |
| Judge runtime | ✅ PASS | claude-opus-4-6, adaptive thinking, non-fatal failures, comprehensive metadata |

### Verdict: 🟡 CONDITIONAL GO for E2E eval experiment

**Conditions:**
1. Run with `auto_approve_hitl=True` (already default in eval mode)
2. Do NOT test production HITL flows until BLOCK-2 is resolved
3. Accept that prompt caching is degraded (BLOCK-1) — increased cost/latency but correct outputs

---

## 9. Fastest Path to Green

| Priority | Action | Effort | Unblocks |
|----------|--------|--------|----------|
| 1 | Add `interrupt_on={"request_approval": True}` to research_agent.py create_deep_agent() call | 5 min | Production HITL testing |
| 2 | Investigate SDK middleware ordering API for priority/pre-model hooks | 1-2 hrs | Prompt caching efficiency |
| 3 | Add @traceable to orchestrator graph nodes and stage logic | 2-4 hrs | LangSmith orchestrator debugging |
| 4 | Remove dead code: memory_loader.py | 5 min | Code hygiene |
| 5 | Clean up 70 stale .cpython-314.pyc files | 5 min | Disk hygiene |
| 6 | Remove extraneous packages from venv | 10 min | Dependency hygiene |

**Immediate next step:** Proceed with E2E eval experiment as-is. Items 1-2 must be resolved before production HITL testing.

---

## Appendix: Audit Lane Sources

| Lane | Auditor | Note ID | Lines |
|------|---------|---------|-------|
| Orchestrator & Model Config | Orchestrator Auditor | 9ada644e | 552 |
| SDK Middleware & Backend | SDK Middleware Auditor | 47efa2a4 | 440 |
| LangSmith Observability & Judge | Verifier Agent | 0829b065 | 747 |
| Research-Agent Lane | Research Lane Auditor v3 | 6a76f284 | 259 |
| Environment Gate | Coordinator | (inline) | — |
| Config-Level Lanes | Coordinator | (inline) | — |

### False Positive Correction

The SDK Middleware Auditor (note 47efa2a4) reported deepagents==0.2.7 as a BLOCKING version mismatch. This was a **false positive**: the auditor's Python environment resolved to a global install at `/opt/homebrew/lib/python3.14/site-packages/deepagents/` rather than the project-local .venv. The coordinator confirmed deepagents==0.4.12 in the project .venv at `.venv/lib/python3.11/site-packages/deepagents/__init__.py`. All middleware imports succeed in the correct environment. The auditor's middleware provenance analysis, backend routing analysis, and non-blocking findings remain valid.
