# Deviation Record

## Context

- Date: 2026-03-23
- Project: `meta-agent-v5.6.0`
- Spec source of truth: `/Users/Jason/2026/v4/meta-agent-v5.6.0/technical-specification-v5.6.0-final.md`
- Trigger: runtime failures observed in LangGraph Studio and `/runs/wait` path

## Deviation 1: Dynamic prompt middleware execution model

- File: `meta_agent/middleware/dynamic_system_prompt.py`
- Spec sections: `22.4`, `22.14`

### Spec baseline

Spec text describes `DynamicSystemPromptMiddleware` as primarily a `before_model` hook that recomposes and injects/replaces the system message in `messages` each call.

### Implemented behavior

- `before_model` now sanitizes state history by stripping existing system messages.
- `wrap_model_call` / `awrap_model_call` apply the stage-aware prompt at request level.
- Request override is version-compatible across runtime shapes:
  - `system_message` (newer LangChain)
  - `system_prompt` (older LangChain)
  - fallback to `messages` replacement if needed

### Why

This was required to fix two real runtime failures:

1. `TypeError: ModelRequest.__init__() got an unexpected keyword argument 'system_message'` (older runtime shape)
2. `ValueError: Received multiple non-consecutive system messages` (duplicate system prompt injection path)

### Evidence

- Failure reproduced through Studio and direct API `runs/wait`.
- After change, `runs/wait` returns successful agent responses.
- Targeted tests pass (`tests/unit/test_dynamic_prompt.py`).

### Reversibility

Reversible by moving all prompt injection back into `before_model` once runtime compatibility and provider semantics are strictly pinned and validated.

---

## Deviation 2: Runtime dependency fail-fast guard

- File: `meta_agent/server.py`
- Spec section: `22.6` (server factory)

### Spec baseline

Spec describes dynamic graph factory behavior but does not require runtime package validation.

### Implemented behavior

- Added `REQUIRED_RUNTIME_VERSIONS` and `_validate_runtime_dependencies()`.
- `get_agent()` now fails fast on incompatible/missing runtime versions.

### Why

Prevent silent runtime drift (global CLI/runtime mismatch) from causing opaque middleware/model failures at execution time.

### Reversibility

Can be removed, but not recommended. This guard enforces architecture assumptions explicitly.

---

## Deviation 3: Filesystem backend root path

- File: `meta_agent/graph.py`
- Related spec/docs area: graph backend configuration in Section `22.4` ecosystem docs

### Implemented behavior

- Backend root uses absolute repo root path resolved from module location.

### Why

Avoided runtime blocking issues tied to cwd resolution in dev runtime.

### Reversibility

Can revert to `root_dir="."` after validating runtime blocking behavior across local/dev server modes.

---

## Impact Assessment

- Functional intent is preserved: stage-aware dynamic prompt recomposition remains active and ordered first.
- Reliability improved: startup now detects incompatible runtimes early.
- Architectural risk reduced: fewer runtime-shape assumptions in hot execution path.

---

## Phase 1 Assessment Remediation (2026-03-29)

### Context

A Phase 1 assessment identified 6 gaps against the development plan. Root cause analysis classified them as:
- **Category A (execution failures):** 2 items — spec and plan were clear, coding agent missed them
- **Category B (spec/plan gaps):** 4 items — plan told the agent WHAT to build but not HOW to wire it into the SDK

All 6 have been remediated across 4 commits. 433 unit tests pass after each.

---

## Deviation 4: SummarizationToolMiddleware wired (Category A)

- File: `meta_agent/graph.py`
- Spec sections: `8.11`, `22.4`
- Plan section: `1.2.1`
- Commit: `a462886`

### Gap

Plan 1.2.1 provides exact instantiation code. Spec 22.4 lists it as explicit middleware. Neither was followed — the middleware was never imported, instantiated, or added.

### Fix

Instantiated `SummarizationMiddleware(model, backend)` and passed to `SummarizationToolMiddleware()`. Added to explicit middleware list. Enables `compact_conversation` tool on orchestrator.

### Root cause: Pure execution failure.

---

## Deviation 5: MemoryMiddleware wired (Category A)

- File: `meta_agent/graph.py`
- Spec sections: `13.4.6`, `22.4`
- Plan section: `1.2.2`
- Commit: `a462886`

### Gap

Plan lists MemoryMiddleware as one of "5 explicit" middleware. The custom `MemoryLoaderMiddleware` stub was imported but never used. The SDK's `MemoryMiddleware` was not imported at all.

### Fix

Replaced stub import with SDK `MemoryMiddleware`. Instantiated with backend and orchestrator AGENTS.md source paths (project-specific + global). Enforces per-agent isolation.

### Root cause: Pure execution failure.

---

## Deviation 6: SkillsMiddleware paths corrected (Category B1)

- File: `meta_agent/graph.py`
- Spec sections: `11`, `11.5`, `22.4`
- Plan sections: `0.2.1`, `1.2.2`
- Commit: `95f2cd5`

### Gap

Spec says "cloned into skills/ directory" but does not document the internal layouts of the three upstream repos. Plan says "clone repos" and "add SkillsMiddleware" but never specifies the `skills=[]` parameter values. The three repos have different nesting:
- `langchain-skills`: `config/skills/*/SKILL.md`
- `langsmith-skills`: `config/skills/*/SKILL.md`
- `anthropic/skills`: `skills/*/SKILL.md`

Pointing to the top-level `skills/` found 0 skills because SkillsMiddleware scans one level deep.

### Fix

Replaced single `skills/` path with three repo-specific paths pointing to the directories that contain the actual skill subdirectories. All 31 skills now loadable.

### Root cause: Spec gap (no repo layout documentation) + Plan gap (no `skills=[]` parameter values).

### Spec/Plan update needed

The plan Section 1.2.2 should include a note:
> After cloning, resolve the actual skill roots for each repo. The `skills=[]` parameter must point to the directory containing skill subdirectories (each with SKILL.md), not the top-level clone directory.

---

## Deviation 7: Subagent definitions wired into SDK (Category B2)

- Files: `meta_agent/subagents/configs.py`, `meta_agent/graph.py`
- Spec sections: `6`, `22.3`, `22.4`
- Plan section: `1.2.2`
- Commit: `b13d2ac`

### Gap

Plan says "Implement configs.py per Section 22.3" and lists SubAgentMiddleware as "auto-attached." But SubAgentMiddleware auto-attachment only adds the middleware — it does not populate it with agent definitions. The plan never specifies the `subagents=[]` parameter on `create_deep_agent()`.

### Fix

Added `build_orchestrator_subagents()` to `configs.py` which:
- Converts metadata configs into SDK `SubAgent` TypedDicts (name, description, system_prompt, tools, middleware, skills)
- Resolves middleware string names to actual instances
- Composes system prompts via each agent's prompt builder
- Passes custom (non-filesystem) tools only
- Assigns skill directories per agent

`graph.py` now passes `subagents=` to `create_deep_agent()`.

### Root cause: Plan gap (no wiring step specified).

### Spec/Plan update needed

Plan Section 1.2.2 should include:
> Pass the built subagent list as `subagents=` to `create_deep_agent()`. SubAgentMiddleware is auto-attached but requires the `subagents` parameter to know what agents are available for delegation.

---

## Deviation 8: Tracing stubs integrated at graph creation (Category B3)

- File: `meta_agent/graph.py`
- Spec sections: `18.5.1`, `18.5.3`
- Plan sections: `0.2.6` (stubs), `1.2.2` (integration)
- Commit: `64c3bd3`

### Gap

Plan Phase 0 says "create stubs" (done). Plan Phase 1 says "full implementation with orchestrator graph" but provides no call sites, no code snippets, no file targets.

### Fix

- `prepare_agent_state` spans now fire at graph creation for the orchestrator (logs state keys, artifact paths, skill dirs, tools) and each subagent (logs skills and custom tools).
- `delegation_decision` spans remain stubs — runtime delegation tracing requires intercepting the `task` tool during actual delegation, which is a Phase 3 concern.

### Root cause: Plan gap (Phase 1 "full implementation" with no integration instructions).

### Spec/Plan update needed

Plan Section 1.2.2 should include:
> Call `prepare_agent_state()` in `create_graph()` after subagent definitions are built, logging the provisioning of each agent. Runtime `delegation_decision` spans should be emitted via a `wrap_tool_call` middleware intercepting `task` calls, implemented in Phase 3 when delegation is exercised.

---

## Deferred: Transition validation (Category B4)

- File: `meta_agent/tools/__init__.py`
- Spec section: `8.1`
- Plan section: `1.2.5`

### Gap

The `@tool` version of `transition_stage` cannot access graph state to validate transitions. The spec defines the tool as if it has state access; the SDK's `@tool` pattern does not provide it. Deferred pending architectural decision on `InjectedState` vs middleware interception.

### Root cause: Spec gap (tool contract assumes state access) + Plan gap (no mechanism specified).

---

## Deviation 9: Eval Engineering prompt section added (Polly Enhancement)

- Files: `meta_agent/prompts/eval_engineering.py` (new), `meta_agent/prompts/sections.py`, `meta_agent/prompts/orchestrator.py`, `meta_agent/prompts/__init__.py`
- Spec sections: `7.3`, `22.14`, `22.15`
- Plan sections: `0.2.9`, `2.2.2`
- Source: Polly assessment (LangSmith trace `019d2a1c-bdf9-7a01-b683-8278e3345d6d`)

### Gap

The orchestrator had no dedicated guidance on eval engineering methodology. The agent improvised eval formats, scoring strategies, and dataset structures through conversation rather than from prompt instructions. This meant:
- Agent wrote YAML when LangSmith needs JSON
- Likert anchors were improvised inconsistently
- No synthetic data curation protocol existed
- No LangSmith dataset schema guidance was present

### Fix

Three changes to the prompt system:

1. **New `EVAL_ENGINEERING_SECTION`** (always-on for orchestrator) — eval taxonomy (5 categories), scoring strategies with mandatory Likert anchor SOP, LangSmith-compatible JSON dataset format, synthetic data curation protocol, eval suite artifact schema, and dataset writing format.

2. **Enhanced `STAGE_CONTEXTS["INTAKE"]`** — 5-phase protocol (Requirements Elicitation, PRD Drafting, Eval Definition, Synthetic Data Curation, Approval), 3 exit artifacts (PRD + eval suite JSON + synthetic dataset), hard rules (JSON not YAML, mandatory Likert anchors, no eval skipping).

3. **Expanded `ROLE_SECTION`** — eval engineering elevated to named core PM skill with LangSmith format awareness and curation methodology.

### Root cause: Prompt gap — spec and plan defined eval tools and eval-mindset sections but did not include structured methodology guidance for the agent to follow when writing evals and curating datasets.

### Spec/Plan updates applied

- Plan Section 0.2.9: `[v5.6-R]` note documenting new `eval_engineering.py` section
- Plan Section 2.2.2: `[v5.6-R]` note documenting enhanced INTAKE context with 3-artifact exit conditions
- Spec Section 22.15: `[v5.6-R]` note documenting the fourth eval-specific section file
- Spec Section 22.16: `[v5.6-R]` note documenting always-on loading and enhanced INTAKE protocol

---

## Follow-up

- Keep this record synced with spec updates.
- If spec is revised to this implementation, mark these deviations as absorbed and close this record.
- Category B4 (transition validation) requires an architectural decision before implementation.

---

## Deviation 10: Research eval package hardened and calibrated ahead of runtime implementation

- Files: `meta_agent/evals/research/*`, `workspace/projects/meta-agent/datasets/synthetic-research-agent.json`
- Spec sections: `3.3`, `5.10`, `15.2`, `15.14`
- Plan sections: `3.1` through `3.3`
- Date: `2026-03-29`

### Gap

The repo had a research-agent PRD, a 38-eval suite, and seed synthetic data, but it did not have a production-ready evaluation package that could be executed end-to-end in LangSmith. The seed dataset was summary-level and JSON/YAML references drifted. The runtime research-agent itself also remains unimplemented, so the repo needed a way to prove evaluator readiness independently of agent readiness.

### Implemented behavior

- Added a dedicated research evaluation package under `meta_agent/evals/research/`.
- Restored the canonical external 38-eval contract.
- Added deterministic, hybrid, and LLM-as-judge evaluators with structured outputs.
- Added a LangSmith SDK experiment harness and dataset builder.
- Froze a 5-scenario synthetic calibration baseline: `golden_path`, `silver_path`, `bronze_path`, `citation_hallucination_failure`, and `hitl_subagent_failure`.
- Standardized the canonical Tier 1 research eval artifact path to `eval-suite-prd.json`.

### Why

This separates two concerns that were previously blurred:

1. **Evaluator readiness** — can the measurement stack score known-good and known-bad traces consistently?
2. **Agent readiness** — can the actual research-agent runtime perform well?

The repository needed (1) before Phase 3 runtime implementation could begin in a trustworthy way.

### Evidence

- LangSmith frozen synthetic calibration run: `research-eval-calibration-openai-frozen-1774813660-98b28e62`
- Threshold agreement: `185/185`
- Exact agreement: `182/185`

### Impact

- The evaluation stack is ready for Phase 3 runtime integration.
- No real-agent performance claims are made yet, because the research-agent runtime has not been built.
- Documentation must clearly distinguish seed artifacts from the runtime-generated calibration dataset and must stop implying that LLM-as-judge work is still entirely deferred in external offline evaluation.
