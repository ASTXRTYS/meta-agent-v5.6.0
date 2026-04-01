# Deviation Record

## Context

- Date: 2026-03-23
- Project: `meta-agent-v5.6.0`
- Spec source of truth: `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Spec.md`
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

## Deviation 3: Filesystem backend root path

- File: `meta_agent/graph.py`
- Related spec/docs area: graph backend configuration in Section `22.4` ecosystem docs

### Implemented behavior

- Backend root uses absolute repo root path resolved from module location.

### Why

Avoided runtime blocking issues tied to cwd resolution in dev runtime.

### Reversibility

Can revert to `root_dir="."` after validating runtime blocking behavior across local/dev server modes.

## Impact Assessment

- Functional intent is preserved: stage-aware dynamic prompt recomposition remains active and ordered first.
- Reliability improved: startup now detects incompatible runtimes early.
- Architectural risk reduced: fewer runtime-shape assumptions in hot execution path.

## Phase 1 Assessment Remediation (2026-03-29)

### Context

A Phase 1 assessment identified 6 gaps against the development plan. Root cause analysis classified them as:

- **Category A (execution failures):** 2 items — spec and plan were clear, coding agent missed them
- **Category B (spec/plan gaps):** 4 items — plan told the agent WHAT to build but not HOW to wire it into the SDK

All 6 have been remediated across 4 commits. 433 unit tests pass after each.

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

> After cloning, resolve the actual skill roots for each repo. The skills=[] parameter must point to the directory containing skill subdirectories (each with SKILL.md), not the top-level clone directory.

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

> Pass the built subagent list as subagents= to create_deep_agent(). SubAgentMiddleware is auto-attached but requires the subagents parameter to know what agents are available for delegation.

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

> Call prepare_agent_state() in create_graph() after subagent definitions are built, logging the provisioning of each agent. Runtime delegation_decision spans should be emitted via a wrap_tool_call middleware intercepting task calls, implemented in Phase 3 when delegation is exercised.

## Deferred: Transition validation (Category B4)

- File: `meta_agent/tools/__init__.py`
- Spec section: `8.1`
- Plan section: `1.2.5`

### Gap

The `@tool` version of `transition_stage` cannot access graph state to validate transitions. The spec defines the tool as if it has state access; the SDK's `@tool` pattern does not provide it. Deferred pending architectural decision on `InjectedState` vs middleware interception.

### Root cause: Spec gap (tool contract assumes state access) + Plan gap (no mechanism specified).

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

1. **New **`EVAL_ENGINEERING_SECTION` (always-on for orchestrator) — eval taxonomy (5 categories), scoring strategies with mandatory Likert anchor SOP, LangSmith-compatible JSON dataset format, synthetic data curation protocol, eval suite artifact schema, and dataset writing format.
2. **Enhanced **`STAGE_CONTEXTS["INTAKE"]` — 5-phase protocol (Requirements Elicitation, PRD Drafting, Eval Definition, Synthetic Data Curation, Approval), 3 exit artifacts (PRD + eval suite JSON + synthetic dataset), hard rules (JSON not YAML, mandatory Likert anchors, no eval skipping).
3. **Expanded **`ROLE_SECTION` — eval engineering elevated to named core PM skill with LangSmith format awareness and curation methodology.

### Root cause: Prompt gap — spec and plan defined eval tools and eval-mindset sections but did not include structured methodology guidance for the agent to follow when writing evals and curating datasets.

### Spec/Plan updates applied

- Plan Section 0.2.9: `[v5.6-R]` note documenting new `eval_engineering.py` section
- Plan Section 2.2.2: `[v5.6-R]` note documenting enhanced INTAKE context with 3-artifact exit conditions
- Spec Section 22.15: `[v5.6-R]` note documenting the fourth eval-specific section file
- Spec Section 22.16: `[v5.6-R]` note documenting always-on loading and enhanced INTAKE protocol

## Follow-up

- Keep this record synced with spec updates.
- If spec is revised to this implementation, mark these deviations as absorbed and close this record.
- Category B4 (transition validation) requires an architectural decision before implementation.

## Phase 3 Alignment Remediation (2026-03-30)

### Context

A Phase 3 assessment identified 6 additional gaps against the specification, development plan, and research-agent PRD. These were discovered during preparation for Phase 3 runtime implementation. Root cause analysis classified them as:

- **Category A (execution failures):** 1 item — spec was clear, implementation missed it
- **Category B (test/metadata gaps):** 4 items — tests and metadata were scaffolded before validators and state schema were finalized
- **Category C (incremental debt):** 1 item — early implementation not updated when rich validators were added

All 6 are being remediated in a coordinated 5-stream effort.

## Deviation 11: request_eval_approval tool registry inconsistency

- Files: `meta_agent/tools/__init__.py`, `meta_agent/tools/registry.py`
- Spec sections: `8.18` (get_eval_results), `9.2` (interrupt configuration — lists `request_eval_approval` as always-HITL-gated)
- Plan sections: Full-Development-Plan.md Phase 3 (eval approval gates for PRD_REVIEW and SPEC_REVIEW)

### Gap

Spec Section 9.2 requires `request_eval_approval` as a dedicated HITL-gated tool separate from `request_approval`. The tool function was implemented (`request_eval_approval_tool` in `__init__.py`) and registered in `HITL_GATED_TOOLS`, `TOOL_REGISTRY`, and `TOOL_FUNCTIONS`. However, `TOOL_FUNCTIONS` maps `"request_eval_approval"` to the `@tool`-decorated `StructuredTool` object rather than the raw function, while all other entries map to raw functions. This causes `test_functions_are_callable` to fail because `callable()` returns `False` on a `StructuredTool` instance (which is callable at the SDK level but not at the Python `callable()` level in the test's assertion model).

Additionally, the PRD_REVIEW and SPEC_REVIEW stages have HARD GATES requiring explicit eval suite approval. The eval approval flow was conflated with artifact approval during initial implementation — a separate tool was needed to distinguish eval suite approval (with its 7 user response branches per the EVAL_APPROVAL_PROTOCOL) from artifact approval.

### Fix

Unify the `TOOL_FUNCTIONS` registry so `"request_eval_approval"` maps to the raw function (matching the pattern of all other entries). Ensure the `@tool`-decorated version is used only in `LANGCHAIN_TOOLS` for the SDK tool list. Stream 2 is handling this fix.

### Root cause: Category A — execution failure. The spec was clear (Section 9.2 lists the tool explicitly); the registry entry used the wrong function form.

### Reversibility

Fully reversible. Change the `TOOL_FUNCTIONS` mapping from the StructuredTool to the raw function.

## Deviation 12: Dual validation path in transition_stage

- Files: `meta_agent/tools/__init__.py` (raw `transition_stage()` + `@tool transition_stage_tool`), `meta_agent/stages/research.py`, `meta_agent/stages/spec_generation.py`, `meta_agent/stages/spec_review.py`
- Spec sections: `8.1` (transition_stage validates transitions with exit/entry conditions), `3.3` (RESEARCH stage exit conditions)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.1 (stage validation)

### Gap

Spec Section 8.1 describes `transition_stage` as validating transitions using exit conditions and entry conditions. Two implementations exist:

1. **Raw function** (`transition_stage()`) — uses a simplified `_check_exit_conditions()` that only checks field-presence (e.g., "does `current_research_path` exist in state?").
2. **Stage validators** (`ResearchStage`, `SpecGenerationStage`, `SpecReviewStage`) — implement rich semantic validation (e.g., ResearchStage checks 8 exit conditions including decomposition, clusters, bundle, agents_md, sub-findings, research path, verification pass, cluster+bundle approval).

The raw function was written in Phase 1 before the rich validators existed. When the validators were added in Phase 3, the raw function was not updated to delegate to them. This means transition validation depends on which call path is used.

### Fix

Unify by having the raw `transition_stage()` delegate to the stage validators for exit condition checking. The simplified field-presence check becomes a fallback for stages without a dedicated validator. Stream 2 is handling this fix.

### Root cause: Category C — incremental debt. Early implementation was not updated when rich validators were added.

### Reversibility

Fully reversible. The raw function can be restored to field-presence-only by removing the validator delegation.

## Deviation 13: Research-agent prompt missing runtime protocol addendum

- Files: `meta_agent/prompts/research_agent.py`
- Spec sections: `6.1.2` (10-phase research protocol)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.2 (research-agent prompt)
- PRD: `workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md`

### Gap

Spec Section 6.1.2 defines the canonical 10-phase research protocol (PRD & Eval Suite Consumption, Skills Ingestion, Decomposition & Agenda, Skills-First Research, Gap-Targeted Web Research, Sub-Agent Topology Reasoning, Cluster Assembly & HITL Checkpoint, Deep-Dive Verification, Bundle Assembly, AGENTS.md Update). The research-agent system prompt (`research_agent.py`, sourced from `Research_Agent_System_Prompt.md`) covers the protocol narratively across 271 lines but lacks a structured "Canonical 10-Phase Runtime Protocol" reference section that tests expect.

Tests check for a structured protocol addendum; the prompt was authored before the test contract was finalized, so the two diverged.

### Fix

Add a structured protocol reference section to the research-agent prompt that enumerates the 10 phases with their phase numbers, names, and key outputs. This preserves the existing narrative prompt content while satisfying the test contract. Stream 1 is handling this fix.

### Root cause: Category B — test/metadata gap. Prompt and test were authored independently; the structured section was never added to the prompt.

### Reversibility

Fully reversible. The addendum is appended to the existing prompt; removing it restores the original 271-line version.

## Deviation 14: SUBAGENT_CONFIGS metadata originally missing SkillsMiddleware

- Files: `meta_agent/subagents/configs.py`
- Spec sections: `6.1` (research-agent requires SkillsMiddleware), `22.4` (middleware stacks)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.1 (subagent configuration)

### Gap

Spec Section 6.1 requires the research-agent to have `SkillsMiddleware` in its middleware stack. The `SUBAGENT_MIDDLEWARE["research-agent"]` metadata dictionary originally did not include `"SkillsMiddleware"`. At runtime, the SDK auto-attaches `SkillsMiddleware` when `skills=` is passed to `create_deep_agent()` or subagent definitions, so the actual research-agent behavior was correct — it received skills. However, the metadata contract (used for documentation, testing, and subagent introspection via `get_subagent_middleware()`) was incomplete.

As of the current codebase, `"SkillsMiddleware"` has been added to `SUBAGENT_MIDDLEWARE["research-agent"]`, resolving the metadata gap.

### Fix

Added `"SkillsMiddleware"` to the `SUBAGENT_MIDDLEWARE["research-agent"]` list. Stream 1 handled this fix.

### Root cause: Category B — test/metadata gap. Developer assumed SDK auto-attachment was sufficient and did not update the metadata contract.

### Reversibility

Fully reversible. Remove the entry from the list; runtime behavior is unaffected (SDK still auto-attaches).

## Deviation 15: Test fixtures incomplete for Phase 3 stage validators

- Files: `tests/unit/test_phase3_runtime.py`
- Spec sections: `3.3` (RESEARCH exit conditions), `3.4` (SPEC_GENERATION exit conditions), `3.5` (SPEC_REVIEW exit conditions)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.4 (Phase 3 stage validation tests)

### Gap

The stage validators enforce rich exit conditions per the spec:

1. **ResearchStage** (`meta_agent/stages/research.py`) requires 8 exit conditions: decomposition artifact, cluster artifacts, bundle artifact, agents_md update, sub-findings, current_research_path, verification pass, and cluster+bundle approval flags.
2. **SpecGenerationStage** (`meta_agent/stages/spec_generation.py`) requires Tier 2 eval metadata and a spec artifact path.
3. **SpecReviewStage** (`meta_agent/stages/spec_review.py`) requires separate spec approval and eval approval gates.

The test fixtures were scaffolded before the validators were fully specified:

- `test_research_stage_exit_conditions` only created decomposition and bundle files, missing 5 of the 8 required conditions.
- `test_spec_generation_stage_exit_conditions` had incorrect Tier 2 eval metadata format and was missing the Tier 1 eval suite path.

The validators themselves work correctly; the tests do not satisfy their conditions.

### Fix

Update test fixtures to provide all required exit condition artifacts and metadata. Stream 2 is handling this fix.

### Root cause: Category B — test/metadata gap. Tests were scaffolded before validators were fully specified.

### Reversibility

Fully reversible. Test fixture changes do not affect production code.

## Deviation 16: State schema Phase 3 fields not reflected in test expectations

- Files: `meta_agent/state.py`, `tests/unit/test_state.py`, `tests/unit/test_tools.py`
- Spec sections: `4.1` (MetaAgentState schema), `3.3`-`3.5` (Phase 3 stage definitions reference these fields)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.1 (state schema extension)

### Gap

Three Phase 3 fields were added to `state.py` and `create_initial_state()`:

- `verification_results: dict` — verification verdicts by artifact type
- `spec_generation_feedback_cycles: int` — orchestrator-mediated research/spec retries
- `pending_research_gap_request: Optional[str]` — targeted research request from spec-writer

Two tests broke because they expected the old field set:

1. `test_returns_dict_with_all_keys` — expected key set did not include the 3 new fields.
2. `test_before_agent_preserves_existing` — expected `before_agent()` to return `None` (no updates needed) when given a state with only pre-Phase-3 fields. But the middleware now detects missing Phase 3 fields and returns defaults for them, so the return is no longer `None`.

### Fix

Update the test expected key set to include the 3 new fields. Update the `test_before_agent_preserves_existing` fixture to include Phase 3 field defaults so the middleware detects no missing fields. Stream 2 is handling this fix.

### Root cause: Category B — test/metadata gap. State schema was extended without updating all dependent tests.

### Reversibility

Fully reversible. Test changes do not affect production code.

## Deviation 17: Research bundle 13-section list in prompt did not match spec Section 5.3

- Files: `meta_agent/prompts/Research_Agent_System_Prompt.md`
- Spec sections: `5.3` (lines 530–544 — the canonical 13 required sections)
- Plan sections: Full-Development-Plan.md Phase 3, Section 3.2.1
- PRD: `workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md` (FR J)
- Date: `2026-03-30`

### Gap

Spec Section 5.3 defines exactly 13 required research bundle sections:

1. Ecosystem Options with Tradeoffs
2. Rejected Alternatives with Rationale
3. Model Capability Matrix
4. SME Perspectives
5. Risks and Caveats
6. Confidence Assessment per Domain
7. Research Methodology
8. Unresolved Questions for Spec-Writer
9. PRD Coverage Matrix
10. Unresolved Research Gaps
11. Skills Baseline Summary
12. Gap and Contradiction Remediation Log
13. Citation Index

The Stream 1 agent wrote 4 non-canonical sections into the prompt instead: "Technology Decision Trees", "Tool/Framework Capability Maps", "Pattern & Best Practice Catalog", "Integration Dependency Matrix". These replaced 4 canonical sections: "SME Perspectives", "Risks and Caveats", "Confidence Assessment per Domain", "Research Methodology". Additionally, "Unresolved Questions for Spec-Writer" and "PRD Coverage Matrix" were omitted.

This conflicted with the ResearchStage validator (`stages/research.py`), which checks for `## PRD Coverage Matrix` in bundle content — the prompt would not have told the agent to write it.

### Fix

Replaced the prompt's 13-section list with the exact canonical list from spec Section 5.3. All section names now match verbatim.

### Root cause: Category A — execution failure. The Stream 1 implementation agent did not read the spec section and instead generated section names from its training data.

### Resolution

Initially corrected by restoring the canonical 13-section list verbatim. Subsequently superseded by Deviation 19 (controlled, approved): the 4 agent-generated sections were judged useful and added to the spec alongside the 13 originals, expanding to 17 total.

### Reversibility

Fully reversible. The fix is a text replacement in the markdown prompt file.

## Deviation 18: Phase A/B/C eval slices incomplete vs development plan Section 3.2.8

- Files: `meta_agent/evals/research/runner.py`
- Spec sections: n/a (eval slicing is in the development plan)
- Plan sections: Full-Development-Plan.md Section 3.2.8 (Incremental Experiment Checkpoints)
- Date: `2026-03-30`

### Gap

Development plan Section 3.2.8 defines 4 checkpoints with specific eval IDs:

- **Checkpoint 1 (Phase A):** 9 evals — RS-001, RS-002, RS-003, RS-004, RINFRA-001, RINFRA-002, RB-001, RB-002, RB-003
- **Checkpoint 2 (Phase B):** 9 evals — RB-004, RB-007, RB-008, RB-009, RB-010, RQ-007, RQ-008, RQ-009, RQ-010
- **Checkpoint 3 (Phase C):** 9 evals — RB-005, RB-006, RB-011, RQ-006, RQ-012, RQ-013, RR-001, RR-002, RR-003
- **Checkpoint 4 (Phase all):** Full 37-eval suite

The Stream 3 agent defined only partial slices:

- Phase A: 5 evals (missing RS-003, RS-004, RINFRA-001, RINFRA-002)
- Phase B: 4 evals (missing RB-004, RQ-007, RQ-008, RQ-009, RQ-010)
- Phase C: dynamic fallback (not explicit)

Additionally, PHASE_GATES in the runner defined gate requirements that didn't match the slices — the gate for Phase A required 6 evals, but the slice only ran 5.

### Fix

Updated `EVAL_PHASE_SLICES` to include all eval IDs per plan Section 3.2.8. Phase C is now explicit (not dynamic). All three slices contain exactly 9 eval IDs each.

### Root cause: Category A — execution failure. The Stream 3 implementation agent used the plan prompt's summary (which listed only a subset) rather than reading the plan document directly.

### Reversibility

Fully reversible. The fix is a data structure update in runner.py.

## Deviation 19: Research bundle expanded from 13 to 17 required sections (Controlled Deviation — Approved)

- Files modified:
  - `meta_agent/prompts/Research_Agent_System_Prompt.md` (prompt section list)
  - `Full-Spec.md` Section 5.3 (canonical schema)
  - `Full-Development-Plan.md` (4 count references)
  - `meta_agent/evals/research/common.py` (`RESEARCH_BUNDLE_REQUIRED_SECTIONS`)
  - `meta_agent/evals/research/rubrics.py` (RINFRA-003 section count)
  - `meta_agent/prompts/verification_agent.py` (section count reference)
  - `meta_agent/prompts/sections.py` (section count reference)
  - `datasets/golden-path/stage6-research-bundle.md` (fixture data)
  - `tests/unit/test_research_eval_hardening.py` (assertions)
- Spec sections: `5.3` (research bundle schema)
- Plan sections: Full-Development-Plan.md Phase 3
- PRD: `workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md` (FR J)
- Date: `2026-03-30`
- Approval: Human-approved controlled deviation

### What the spec said (before this change)

Spec Section 5.3 defined 13 required research bundle sections.

### What we changed

Expanded to 17 required sections. All 13 original sections are preserved in their original relative order (renumbered 8–17). Four new sections are inserted after "Model Capability Matrix" (#3) as a practical-reference block (#4–#7):

1. **Technology Decision Trees** — Decision frameworks organized by PRD requirement area, with PRD requirements as decision criteria, branch conditions based on research findings, and recommended paths with evidence references.
2. **Tool/Framework Capability Maps** — For each library, framework, or tool relevant to the PRD: what it does, when to use it, known limitations, and version-specific considerations.
3. **Pattern & Best Practice Catalog** — Real-world usage patterns, production patterns, performance considerations, and implementation guidance drawn from source code analysis, documentation, and community practice.
4. **Integration Dependency Matrix** — How different components interact, version constraints, compatibility requirements, and transitive dependency considerations.

### Why

During the Stream 1 remediation, the implementing agent independently generated 4 sections that were not in the spec but were judged to be directly actionable for the downstream spec-writer agent. A subsequent audit identified the mismatch, and a human-led review determined that:

- The 4 new sections provide practical reference material the spec-writer would otherwise lack (decision trees, capability maps, patterns, dependency analysis).
- The 4 spec sections they initially replaced (Confidence Assessment, Research Methodology, Unresolved Questions for Spec-Writer, PRD Coverage Matrix) are structurally critical to the pipeline — particularly "PRD Coverage Matrix" (which the ResearchStage validator checks for) and "Unresolved Questions for Spec-Writer" (the handoff contract to the spec-writer).
- The best outcome is to keep all 13 canonical sections AND add the 4 new ones, expanding to 17.

### Spec and plan updated

- `Full-Spec.md` Section 5.3: count changed from 13 to 17, 4 new entries added with descriptions, existing entries renumbered.
- `Full-Spec.md` changelog line 111: updated to reflect 17 sections.
- `Full-Development-Plan.md`: 4 references to "13 sections" updated to "17".
- All evaluators, validators, prompts, and fixtures updated to expect 17 sections.

### Files NOT changed (verified compatible)

- `meta_agent/stages/research.py` — `_contains_required_bundle_sections()` checks 3 specific headings (PRD Coverage Matrix, Unresolved Research Gaps, Citation Index), all still present. No count-based check. Compatible as-is.
- `meta_agent/evals/research/evaluators.py` — Uses dynamic `REQUIRED_SECTIONS` list from common.py. Compatible as-is.
- `meta_agent/evals/research/deterministic.py` — No hardcoded section count. Compatible as-is.

### Reversibility

Fully reversible. Remove the 4 new entries, renumber 8–17 back to 4–13, and update all count references back to 13.

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