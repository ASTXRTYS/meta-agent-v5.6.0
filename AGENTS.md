# AGENTS.md — Meta-Agent v5.6.0

## Local Development Setup

Follow these steps exactly to get the dev server running with the Studio UI.

### 1. Install Dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Prefer a project-local virtualenv so `langgraph dev` uses this repo's dependency baseline,not a globally installed CLI/runtime from your shell PATH.

This installs the `meta-agent` package plus all required dependencies:

- `deepagents>=0.4.3` — the Deep Agents SDK (provides `create_deep_agent()`)
- `langgraph-cli[inmem]>=0.4.12` — the `langgraph` CLI with in-memory runtime
- `langchain-anthropic>=1.3.0` — Anthropic model provider
- `python-dotenv>=1.0.0` — loads `.env` file automatically
- `langsmith` — tracing and evaluation
- `pydantic>=2.0`, `langgraph-sdk>=0.1.0`, `langchain-community>=0.4.0,<0.5.0`

### 2. Create the `.env` File

Copy `.env.example` and fill in your real API keys:

```bash
cp .env.example .env
```

Then edit `.env` with your actual keys:

```
LANGSMITH_API_KEY=lsv2_pt_your_real_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=meta-agent
ANTHROPIC_API_KEY=sk-ant-api03-your_real_key_here
META_AGENT_MODEL=anthropic:claude-opus-4-6
META_AGENT_MODEL_PROVIDER=anthropic
META_AGENT_MODEL_NAME=claude-opus-4-6
META_AGENT_MAX_REFLECTION_PASSES=3
```

**Both keys are required:**

- `ANTHROPIC_API_KEY` — the agent calls Claude via the Anthropic API. Without this, `graph.invoke()` will fail.
- `LANGSMITH_API_KEY` — tracing and eval runs go to LangSmith. Without this, `LANGSMITH_TRACING=true` will cause connection errors at runtime.

The `.env` file is loaded automatically by `meta_agent/server.py` on import via `python-dotenv`. It is also referenced directly in `langgraph.json` via the `"env": ".env"` field, so the `langgraph dev` CLI loads it too.

**Do NOT commit **`.env`** to git.** It is in `.gitignore`.

### 3. Launch the Dev Server

```bash
langgraph dev
```

If you are not activating the venv in your shell, run:

```bash
./.venv/bin/langgraph dev
```

For normal local development, run this command exactly as shown so Studio opens automatically.Do not add `--no-browser` unless you explicitly need headless mode.

This will:

1. Read `langgraph.json` at the project root
2. Install the local package (from `"dependencies": ["."]`)
3. Load environment variables from `.env` (from `"env": ".env"`)
4. Import the graph via `meta_agent.server:get_agent`
5. Start the API server at `http://127.0.0.1:2024`
6. Open LangGraph Studio in your default browser

You should see output like:

```
Welcome to LangGraph
- API: http://127.0.0.1:2024
- Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- API Docs: http://127.0.0.1:2024/docs
```

Use `langgraph dev --no-browser` only for headless runs (CI, remote terminals, or when explicitly requested).

To use a different port: `langgraph dev --port 8123`.

### 4. Interact with the Agent

Once the dev server is running, the Studio UI lets you:

- Send messages to the orchestrator (the PM agent)
- See the graph topology and state flow
- Inspect tool calls, HITL interrupts, and stage transitions
- View LangSmith traces in real-time

The orchestrator starts in the INTAKE stage. Send it a product idea and it will ask clarifying questions before drafting a PRD — this is the intended PM behavior per the spec.

### 5. Run Tests

```bash
make test          # Run all 471 unit tests
make evals-p0      # Run Phase 0 evals (INFRA-001 through INFRA-004)
make evals-p1      # Run Phase 1 evals (INFRA-005–008, STAGE-001–002)
make evals-p2      # Run Phase 2 evals (PM-001–008, STAGE-003, GUARD-001–004)
make evals         # Run all evals
```

### Troubleshooting

| Problem | Fix |
| --- | --- |
| No dependencies found in config | Your langgraph.json is missing "dependencies": ["."]. See the file in repo root. |
| ANTHROPIC_API_KEY not set | Your .env file is missing or doesn't have the Anthropic key. Copy from .env.example. |
| ModuleNotFoundError: deepagents | Run pip install -e . — the package isn't installed. |
| langgraph: command not found | Run pip install "langgraph-cli[inmem]>=0.4.12" |
| unexpected keyword argument 'system_message' / 'system_prompt' | Your runtime packages are outdated or mixed. Recreate/activate .venv, run pip install -e ".[dev]", and relaunch from that env. |
| Connection refused on Studio | The dev server isn't running. Run langgraph dev first. |
| Port already in use | Another process is on 2024. Use langgraph dev --port 8123 or kill the existing process. |

## API and SDK Investigation Protocol

When investigating, auditing, or implementing features from any external API or SDK, agents MUST follow this protocol to prevent misidentification of features and ensure correct integration.

### The Problem This Solves

During a preflight audit, subagents confidently misidentified Claude API features:

- "Programmatic Tool Calling" (Claude writing code to call tools in a sandbox) was confused with `tool_choice` (forcing a specific tool via API parameter)
- "Dynamic Filtering" (Claude filtering web search results via code execution) was confused with middleware-level tool list filtering

Both misidentifications occurred because agents relied on skill files and general knowledge instead of consulting authoritative documentation. The skill files gave enough context to be confidently wrong.

### Mandatory Verification Steps

**Step 1: Identify the authoritative source.** Before investigating any API feature, determine the canonical documentation URL. For this project:

| SDK/API | Authoritative Source |
| --- | --- |
| Claude API (Anthropic) | https://platform.claude.com/docs/ |
| Deep Agents SDK | .reference/libs/deepagents/ (local source) + skill files |
| LangChain | https://python.langchain.com/docs/ |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| LangSmith | https://docs.smith.langchain.com/ |

**Step 2: Fetch and read the authoritative docs.** Use web_fetch or web_search to retrieve the actual documentation page for the specific feature. Do NOT rely solely on skill files — skill files are baseline context, not exhaustive references.

**Step 3: Map terminology precisely.** API features often have specific, non-obvious meanings. Before claiming understanding:

- Quote the official definition from the docs
- Identify any prerequisites (e.g., "requires code_execution tool to be enabled")
- Distinguish between features with similar names (e.g., tool_choice vs programmatic tool calling)

**Step 4: Verify integration path via Python introspection.** For any SDK integration, run actual Python code to inspect:

- Available parameters: `inspect.signature()`, `model_fields`, etc.
- Supported values: docstrings, type annotations
- Version compatibility: `importlib.metadata.version()`

**Step 5: Cross-reference integration layers.** When a feature spans multiple layers (e.g., Claude API → LangChain → Deep Agents SDK), verify at each layer:

- Does the layer expose the feature?
- Does it pass through transparently?
- Does it transform or restrict the feature?

### Anti-patterns

1. **Assuming skill files are exhaustive.** Skill files provide baseline knowledge, not comprehensive API coverage. Always verify against authoritative docs for specific features.
2. **Mapping familiar terms to API features without verification.** "Tool calling" in general AI context ≠ "Programmatic Tool Calling" in Claude API. Always use the API's own definitions.
3. **Claiming a feature is "not available" without checking.** A feature might be auto-enabled (like dynamic filtering in web_search_20260209), available via model_kwargs, or accessible through a different parameter name.
4. **Testing only that existing tests pass.** When implementing a new feature, write tests that specifically validate the feature's behavior. "Tests pass" means "nothing broke," not "the feature works."

### SDK Reference Locations

For quick reference, the authoritative local sources for each SDK:

| SDK | Local Reference | Key Files |
| --- | --- | --- |
| Deep Agents | .reference/libs/deepagents/deepagents/ | middleware/, backends/, init.py |
| LangChain Anthropic | .venv/lib/python3.11/site-packages/langchain_anthropic/ | chat_models.py |
| LangGraph | .venv/lib/python3.11/site-packages/langgraph/ | graph/, prebuilt/ |
| LangSmith | .venv/lib/python3.11/site-packages/langsmith/ | client.py, wrappers.py |

### Claude API Feature Quick Reference

Features confirmed available and integrated in this project:

| Feature | API Mechanism | Integration Point | Status |
| --- | --- | --- | --- |
| Adaptive Thinking | thinking: {type: "adaptive"} | ChatAnthropic constructor | ✅ Active |
| Effort Levels | effort: "max"/"high"/"medium"/"low" | ChatAnthropic constructor | ✅ Active |
| Streaming | streaming: True on ChatAnthropic | model.py get_configured_model() | ✅ Active |
| Web Search | web_search_20260209 server-side tool | SERVER_SIDE_TOOLS dict | ✅ Active |
| Web Fetch | web_fetch_20260209 server-side tool | SERVER_SIDE_TOOLS dict | ✅ Active |
| Dynamic Filtering | Built into _20260209 web tools (automatic) | No config needed | ✅ Active |
| Code Execution | code_execution_20260120 server-side tool | SERVER_SIDE_TOOLS dict | ✅ Active |
| Programmatic Tool Calling | allowed_callers on tool definitions | BaseTool.extras | ✅ Active |
| Citations (web search) | Automatic with web_search | extract_api_citations() | ✅ Active |
| tool_choice | tool_choice on bind_tools() | DynamicToolConfigMiddleware | ✅ Active |
| Tool Filtering | ModelRequest.tools modification | DynamicToolConfigMiddleware | ✅ Active |
| Prompt Caching | AnthropicPromptCachingMiddleware (auto) | SDK auto-attached | ⚠️ Ordering issue |

### LangSmith Tracing Convention — Maximum Visibility

LangSmith tracing is **binary** (on/off). There are no tiers or debug levels. When `LANGSMITH_TRACING=true`, ALL data is captured by default:
- Full input/output payloads (not truncated)
- Token usage per step
- Tool call details and timing
- Thinking/reasoning blocks from Claude
- Middleware execution spans
- Subagent delegation with parent-child hierarchy

**Required .env settings for maximum visibility:**
```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-key>
LANGSMITH_PROJECT=meta-agent
LANGCHAIN_CALLBACKS_BACKGROUND=false
```

**Variables that MUST NOT be set (they reduce visibility):**
| Variable | Effect if Set |
|----------|--------------|
| LANGSMITH_HIDE_INPUTS | Hides all inputs from traces |
| LANGSMITH_HIDE_OUTPUTS | Hides all outputs from traces |
| LANGSMITH_HIDE_METADATA | Hides run metadata |
| LANGSMITH_TRACING_SAMPLING_RATE | Reduces percentage of traces logged |

**Convention:** Any new .env file must include the four required settings above. Never set the HIDE_* variables in development or experiment environments.

## Project Status

**Current Progress:** See Section 1.5 "Project Status Summary" in `Full-Development-Plan.md` for detailed phase-by-phase progress tracking.

Phases 0, 1, and 2 are complete and running on the real Deep Agents SDK (`deepagents==0.4.12`). The orchestrator produces a real `CompiledStateGraph` via `create_deep_agent()` and successfully invokes model providers through the configured runtime.

**Phase 3 is IN PROGRESS (~80% complete).** All three runtime agents are implemented as standalone Deep Agents (research-agent, verification-agent, spec-writer) and wired into the orchestrator. Phase 3 gate evals (7 Layer 1 evals) and the eval run function bridge are complete. 471 unit tests pass. Remaining work: end-to-end live experiment run, stage wiring validation, and HITL checkpoint verification.

The research-agent evaluation stack exists under `meta_agent/evals/research/`. That package implements 38 canonical research eval definitions, with 37 active in the default run path and `RI-001` intentionally deferred, plus 5 synthetic calibration scenarios, structured judge outputs, LangSmith SDK experiment execution, and UI-ready judge profiles. The measurement contract in that package is now aligned to the v5.6.1 17-section research-bundle schema. A historical frozen synthetic calibration baseline reached `185/185` pass/fail agreement and `182/185` exact agreement before this contract repair; rerun the calibration flow before treating that baseline as current. No current real-agent performance baseline exists yet because end-to-end live validation of the implemented research-agent runtime is still pending.

**Note to agents:** As you work on this project, update the progress tracking in `Full-Development-Plan.md` to reflect completed work. See the "Progress Tracking" section below for instructions.

## How It Works

`langgraph.json` points to `meta_agent.server:get_agent`. That function calls `create_graph()` in `meta_agent/graph.py`, which calls `create_deep_agent()` from the real Deep Agents SDK. The SDK auto-attaches TodoListMiddleware, FilesystemMiddleware, SubAgentMiddleware, SummarizationMiddleware, and prompt caching. We pass in our custom middleware, tools, backend, checkpointer, and HITL config.

### What `create_deep_agent()` Provides Automatically

These are **auto-attached** by the SDK — we do NOT instantiate them:

| Middleware | What It Does |
| --- | --- |
| TodoListMiddleware | Provides write_todos tool for task planning |
| FilesystemMiddleware | Provides ls, read_file, write_file, edit_file tools via configured backend |
| SubAgentMiddleware | Provides task tool for delegation to subagents |
| SummarizationMiddleware | Auto-compacts context when token usage is high |
| Prompt caching + tool patching | Anthropic cache breakpoints, tool call normalization |

### What We Configure Explicitly

| Parameter | Value | Spec Reference |
| --- | --- | --- |
| model | "claude-opus-4-6" (from env) | Section 10.5 |
| system_prompt | construct_pm_prompt() output | Section 7.3 |
| tools | Custom tools from meta_agent/tools/ (registered as @tool) | Sections 8.1–8.14 |
| middleware | [DynamicSystemPromptMiddleware, MetaAgentStateMiddleware, SummarizationToolMiddleware, MemoryMiddleware, ToolErrorMiddleware] | Sections 22.4, 22.12 |
| backend | FilesystemBackend(root_dir=<repo_root>, virtual_mode=True) | Section 4.2 |
| checkpointer | MemorySaver() (InMemorySaver) | Section 4.3 |
| store | InMemoryStore() | Section 4.2 |
| interrupt_on | {tool_name: True for tool_name in HITL_GATED_TOOLS} | Section 9.2 |
| skills | skills/langchain/config/skills, skills/langsmith/config/skills, skills/anthropic/skills | Sections 11, 22.4 |
| name | "meta-agent-orchestrator" | — |

### Custom Middleware

| Middleware | File | Hook Type | Purpose |
| --- | --- | --- | --- |
| DynamicSystemPromptMiddleware | middleware/dynamic_system_prompt.py | @wrap_model_call / @before_model | Reads current_stage from state, builds stage-aware prompt, strips stale system messages from history in before_model, then applies request-level system prompt in wrap hooks. MUST be first in middleware list. |
| MetaAgentStateMiddleware | middleware/meta_state.py | AgentMiddleware | Extends the graph state schema and keeps orchestrator state shape aligned with the spec. |
| SummarizationToolMiddleware | graph.py (SDK middleware instance) | SDK middleware | Exposes compact_conversation for agent-controlled compaction on top of the auto-attached summarization layer. |
| MemoryMiddleware | graph.py (SDK middleware instance) | SDK middleware | Loads the orchestrator's tiered AGENTS.md files with per-agent isolation. |
| ToolErrorMiddleware | middleware/tool_error_handler.py | @wrap_tool_call | Wraps tool calls in try/except, returns structured error JSON |

### Subagent Memory Architecture

All subagents follow a strict memory convention to ensure instruction reliability and SDK alignment:

1.  **Tiered Resolution**: Agents load instructions from the root `.agents/`, their per-agent `.agents/{name}/`, and the project-local `.agents/` directory using the `get_memory_sources` helper.
2.  **Middleware Injection**: Memory is always loaded via `MemoryMiddleware` during `create_deep_agent()` initialization. This ensures instructions are treated as persistent system context rather than volatile history.
3.  **Zero Manual I/O**: Agent factories must never use manual filesystem checks for `AGENTS.md`. The `MemoryMiddleware` is the sole authority for loading instructions, handling optional project files gracefully.
4.  **Persona Graduation**: To define a new subagent identity, simply create a directory under `/.agents/` with an `AGENTS.md`. The system will automatically resolve it for any agent initialized with that name.

## Architecture

```
meta_agent/
├── graph.py            # create_deep_agent() — real SDK, real graph
├── server.py           # get_agent() factory for langgraph.json
├── state.py            # MetaAgentState TypedDict, WorkflowStage enum
├── configuration.py    # MetaAgentConfig from env vars
├── model.py            # Per-agent effort levels, adaptive thinking
├── backend.py          # Checkpointer and store creation helpers
├── project.py          # Multi-project init, directory trees
├── tracing.py          # @traceable stubs, trace spans
├── errors.py           # Four-tier error handling
├── safety.py           # Recursion limits, token budgets, path validation
├── middleware/          # Custom middleware (real AgentMiddleware subclasses)
├── prompts/            # 16 prompt sections, stage-aware composition
├── tools/              # 14+ custom @tool functions, tool registry
├── stages/             # IntakeStage, PrdReviewStage logic
├── subagents/          # 8 subagent configs
└── evals/              # Orchestrator evals, research eval package, runners
    └── research/       # 38 research-agent evaluators, dataset builder, LangSmith harness
```

## Remaining Work (Phases 3-5)

- **Phase 3:** Research + Spec end-to-end validation and behavioral hardening for the implemented runtime agents (research-agent, verification-agent, spec-writer as real SubAgents). The evaluation stack for this phase already exists; remaining work is live experiment execution, stage wiring validation, and HITL verification.
- **Phase 4:** Planning + Execution (plan-writer, code-agent with 3 nested sub-agents)
- **Phase 5:** End-to-end evaluation + audit UX. LangSmith experiment plumbing exists, but the orchestrator still does not provide a user-friendly end-to-end eval/testing workflow.

## Phase 3 Experimental Findings and Known Issues

### Experiment Context

- **Trace ID**: 019d404a-8275-7cb3-81a7-4bc166c13cb1 (LangSmith)
- **Date**: 2026-03-30
- **PRD**: .agents/pm/projects/meta-agent/artifacts/intake/research-agent-prd.md
- **Status**: Experiment cut off before research phase began

### Issues Discovered

#### Skills Usage Behavior

The research-agent demonstrated incorrect skills consultation:

- **Expected**: Use SkillsMiddleware to internalize pre-loaded skills before web research
- **Actual**: Brute-force directory traversal through `/skills/` with 78 read_file calls
- **Problem**: Measurement stack was rewarding filesystem access rather than middleware-driven skill usage

#### Research Approach

- **Expected**: Web research using web_search and web_fetch tools
- **Actual**: 0 web_search calls, 0 web_fetch calls
- **Problem**: Agent stuck in filesystem exploration mode instead of conducting research

#### Delegation Patterns

- **Expected**: Intentional sub-agent topology with parallel research
- **Actual**: Only 2 task calls, minimal delegation
- **Problem**: Poor reasoning about delegation topology and workload distribution

#### Middleware Integration

- **Expected**: DynamicSystemPromptMiddleware firing correctly
- **Actual**: Middleware not operating as intended
- **Problem**: Stage-aware prompts and system message handling broken

#### PRD Decomposition

- **Expected**: Structured decomposition into research domains
- **Actual**: Failed to properly decompose PRD requirements
- **Problem**: Agent couldn't translate PRD into actionable research agenda

### Current Frozen State

Development is frozen until API funding is available. The architectural foundation exists (all three Phase 3 agents implemented as Deep Agents), but behavioral fixes are required before the research-agent can perform as designed.

### Detailed Analysis Reference

See DEVIATION_RECORD.md Section 21 for comprehensive analysis of:

- Why the measurement stack rewarded incorrect behaviors
- Skills-first research posture implementation gaps
- Middleware evidence vs filesystem access patterns
- Evaluation contract misalignment

This section contains high-signal feedback about the root causes of these issues.

## Progress Tracking

**For Agents Working on This Project:**

The `Full-Development-Plan.md` includes progress tracking that shows what's complete, in progress, and not started. As you complete work, you **must** update this document to reflect the current state.

### How to Update Progress

1. **Phase Headers:** Update status badges as phases are completed

- `⏸️ NOT STARTED` → `🔄 IN PROGRESS` → `✅ COMPLETE`

1. **Task Checklists:** Mark tasks as complete using `[x]` instead of `[ ]`

- Found in each phase's "Phase Complete Checklist" section

1. **Project Status Summary:** Update completion percentages and current focus

- Located in Section 1.5 of the development plan

1. **Phase-Specific Progress:** Update progress sections for the current phase

- Example: Phase 3 has separate "Foundations" vs "Runtime Implementation" sections

### When to Update

- **After completing any implementation task** (e.g., implementing a tool, middleware, or stage)
- **When evals pass** - Update the relevant eval checklist items
- **When starting a new phase** - Change the header from `⏸️ NOT STARTED` to `🔄 IN PROGRESS`
- **Before committing work** - Ensure progress tracking reflects your changes

### Progress Tracking Legend

- ✅ **COMPLETE** - All evals passing, phase fully functional
- 🔄 **IN PROGRESS** - Implementation underway, partial completion
- ⏸️ **NOT STARTED** - Blocked by prerequisite phases
- [x]
- Task completed
- [ ]
- Task incomplete
- ⏳ - In progress

**Important:** The development plan is the single source of truth for project status. Keeping it accurate ensures any agent can quickly understand what's done and what remains.

## Test Suite Structure

The test suite has two layers: the canonical new suite and a quarantined legacy suite.

### Directory Layout

| Directory | Purpose | Marker | Mock Policy |
| --- | --- | --- | --- |
| tests/contracts/ | Fast invariant tests — no I/O, no model calls | pytest.mark.contract | No unittest.mock allowed |
| tests/integration/ | App composition tests — may use tmp_path, mocks | pytest.mark.integration | Mocks permitted |
| tests/evals/ | Live behavioral tests — real API calls | pytest.mark.eval | Auto-skipped without ANTHROPIC_API_KEY |
| tests/drift/ | Regression/drift guards | pytest.mark.drift | No mocks |
| tests/unit/ | LEGACY QUARANTINE — do not add new tests here | pytest.mark.legacy | Frozen at ceiling of 410 tests |
| tests/_support/ | Shared helpers (fake models, builders, assertions) | N/A — not test files | N/A |

### Makefile Targets

| Target | What It Runs |
| --- | --- |
| make test | New suite only (excludes tests/unit/) — this is the default |
| make test-all | Everything including legacy |
| make test-contracts | Contract tests only |
| make test-integration | Integration tests only |
| make test-evals | Eval tests only (skipped without API key) |
| make test-drift | Drift tests only |
| make test-legacy | Legacy quarantine only |

### When Writing New Tests

1. **Choose the right directory** based on the table above
2. **Add the correct marker** as `pytestmark = pytest.mark.<marker>` at the top of the file
3. **Add **`REPLACES:`** comments** if your test replaces legacy coverage:`# REPLACES: tests/unit/test_backend.py::TestCreateCompositeBackend`
4. **Add **`COVERS:`** declarations** mapping to catalog component IDs:`# COVERS: backend.composite_routing, backend.filesystem_virtual`
5. **Never add tests to **`tests/unit/` — the legacy ratchet (ceiling=410) will fail CI

### Legacy Test Ratchet

The legacy suite is frozen at a ceiling of 410 tests. This number must only decrease as legacy tests are replaced by new canonical tests. The drift test `test_legacy_ratchet.py` enforces this. If you replace a legacy test, delete the legacy version and update the `REPLACES:` comment in the new test.

## Test Catalog Maintenance

Three YAML catalogs in `docs/testing/` track the components that need test coverage. **You must update these catalogs when changing the application.**

### Catalogs

| File | What It Tracks | When to Update |
| --- | --- | --- |
| docs/testing/runtime_components.yaml | Tools, middleware, subagents, state fields, guardrails (82 components) | Adding/removing/renaming a tool, middleware, subagent, state field, or guardrail |
| docs/testing/sdk_touchpoints.yaml | SDK symbols imported and how they're used (17 touchpoints) | Adding a new SDK import or changing usage pattern |
| docs/testing/intentional_stubs.yaml | Phase-deferred stubs with justification (14 stubs) | Adding a new stub, retiring a stub, or a stub becoming real |

### After Any Catalog Change

Regenerate the traceability matrix:

```bash
python scripts/testing/generate_traceability.py
```

This updates `docs/testing/TEST_TRACEABILITY.md` and `docs/testing/TEST_TRACEABILITY.json`.

### Drift Enforcement

Drift tests automatically catch catalog staleness:

- **Catalog parity** — fails if `runtime_components.yaml` doesn't match what's in `meta_agent/`
- **SDK touchpoints** — fails if new SDK imports aren't cataloged
- **Stub allowlist** — fails if new stubs (both `NotImplementedError` and soft stubs like `return {"status": "pending"}`) aren't in the allowlist
- **Collection hygiene** — fails if test files are missing markers or `REPLACES:` comments

If a drift test fails after your change, update the relevant catalog and regenerate traceability.

### Inventory Scripts

| Script | Purpose |
| --- | --- |
| scripts/testing/extract_runtime_inventory.py | Scans meta_agent/ for runtime components via AST |
| scripts/testing/extract_sdk_touchpoints.py | Scans imports for SDK symbol usage |
| scripts/testing/generate_traceability.py | Builds the coverage traceability matrix from catalogs + COVERS declarations |

## Spec and Plan Documents

- **Technical Specification (source of truth):** `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Spec.md` (v5.6.1)
- **Development Plan:** `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Development-Plan.md` (updated 2026-03-29)
- **Implementation Deviation Record:** `/Users/Jason/2026/v4/meta-agent-v5.6.0/DEVIATION_RECORD.md`

## LangSmith Datasets (Pre-loaded)

- `meta-agent-phase-0-scaffolding` (15 examples, ID: `835a9b10-371f-413c-99f9-bdc19e2c4c25`)
- `meta-agent-phase-1-orchestrator` (18 examples, ID: `70f34716-7d60-4042-a565-c086b063809d`)
- `meta-agent-phase-2-intake-prd` (11 scenarios, ID: `b7c0535f-c17f-48bd-8663-e2dda2bd8f07`)

## Research Eval Calibration

- Seed artifacts live under `.agents/pm/projects/meta-agent/` and are expanded into a 5-scenario calibration dataset by `meta_agent.evals.research.synthetic_trace_adapter`.
- Build the raw LangSmith-ready dataset with `python -m meta_agent.evals.research.dataset_builder --datasets-dir datasets --output /tmp/research-agent-eval-calibration.json`.
- Run the synthetic calibration experiment with `python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets`.
- The default LangSmith experiment path materializes a timestamped dataset from the local canonical examples. Pass `--dataset-name <existing-dataset>` to reuse an already-uploaded LangSmith dataset instead.
- The registry contains 38 defined evals, reported as 37 active + 1 deferred unless `--include-deferred` is used.
- The frozen calibration baseline validates evaluator behavior only. It does not measure live runtime performance because end-to-end experiments against the implemented research-agent runtime are still pending.

## Experiment Reporting (New)

The research eval package now supports dual-channel reporting:

- **Local Markdown Reports:** Detailed human-readable reports with failure analysis, judge reasoning, evidence summaries, confidence, flags, and experiment metadata. Generated automatically with `--report-dir` flag.
- **LangSmith UI:** Full traceability, filtering, and deep-dive analysis capabilities.

### Report Generation Commands

```bash
# Runner with markdown reports
python -m meta_agent.evals.research.runner --mode trace --report-dir reports

# LangSmith experiment with markdown reports
python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets --report-dir reports

# LangSmith experiment reusing an existing dataset
python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets --dataset-name research-agent-eval-calibration --report-dir reports
```

Reports are persisted under `.agents/pm/projects/meta-agent/evals/reports/` and include:

- Executive summary with pass/fail counts
- Registry coverage totals (`defined`, `active`, `deferred`)
- Detailed failure blocks with judge reasoning, evidence, confidence, and flags
- Passing evaluations summary table
- Experiment metadata and configuration, including scenario labeling for multi-scenario LangSmith calibration runs

## Middleware Catalog

This section catalogs all middleware used across the meta-agent system, organized by agent and source (SDK vs Custom).

### Summary Table

| Middleware | Source | Purpose | Used By | Status |
| --- | --- | --- | --- | --- |
| **SDK Middleware (Explicitly Imported)** |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading | PM, all subagents | ✅ Active |
| SkillsMiddleware | SDK | On-demand SKILL.md loading | PM, all subagents | ✅ Active |
| SummarizationToolMiddleware | SDK | Automatic compaction + compact_conversation tool | PM, research, evaluation, code, plan-writer | ✅ Active |
| CompiledSubAgent, SubAgent | SDK | Subagent delegation support | PM, all subagents | ✅ Active |
| **SDK Middleware (Auto-Attached by create_deep_agent)** |
| TodoListMiddleware | SDK | Provides write_todos tool for task planning | All agents | ✅ Active |
| FilesystemMiddleware | SDK | Provides ls, read_file, write_file, edit_file tools | All agents | ✅ Active |
| SubAgentMiddleware | SDK | Provides task tool for delegation to subagents | All agents | ✅ Active |
| AnthropicPromptCachingMiddleware | SDK | Anthropic cache breakpoints, prompt caching | All agents | ✅ Active |
| PatchToolCallsMiddleware | SDK | Tool call normalization, patches dangling tool calls | All agents | ✅ Active |
| HumanInTheLoopMiddleware | SDK | HITL interrupt handling via interrupt_on parameter | PM (gated tools) | ✅ Active |
| **Custom Middleware** |
| MetaAgentStateMiddleware | Custom | Extends graph state with custom fields (current_stage, decision_log, etc.) | PM only | ✅ Active |
| DynamicSystemPromptMiddleware | Custom | Stage-aware prompt recomposition based on current_stage | PM only | ✅ Active |
| AskUserMiddleware | Custom | Structured user questioning via ask_user tool (ported from CLI) | PM only | ✅ Active |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except, returns structured error JSON | PM, all subagents | ✅ Active |
| AgentDecisionStateMiddleware | Custom | General-purpose decision/assumption state fields (decision_log, assumption_log, approval_history) | Research, verification | ✅ Active |
| DynamicToolConfigMiddleware | Custom | Stage-aware tool choice and filtering | PM, research, evaluation, code, plan-writer | ⚠️ DEAD CODE |
| CompletionGuardMiddleware | Custom | Prevents premature session termination via after_model hook | Code-agent | ⚠️ NAIVE - CONSIDER REMOVAL |

### PM Orchestrator Middleware Stack

The PM orchestrator (meta_agent/graph.py) uses the following middleware stack:

#### Explicit Middleware (Lines 159-168)

| Order | Middleware | Source | Purpose |
| --- | --- | --- | --- |
| 0 | DynamicSystemPromptMiddleware | Custom | Reads current_stage from state, builds stage-aware prompt, strips stale system messages from history. MUST be first in middleware list. |
| 1 | MetaAgentStateMiddleware | Custom | Extends the graph state schema with meta-agent fields (current_stage, decision_log, assumption_log, approval_history, project paths, participation mode). |
| 2 | AskUserMiddleware | Custom | Provides ask_user tool for structured user questioning (free-form text + multiple-choice). Uses LangGraph interrupt() to pause execution. |
| 3 | MemoryMiddleware | SDK | Loads the orchestrator's tiered AGENTS.md files with per-agent isolation. |
| 4 | SkillsMiddleware | SDK | On-demand SKILL.md loading from skills directories (langchain, langsmith, anthropic). |
| 5 | SummarizationToolMiddleware | SDK | Exposes compact_conversation tool for agent-controlled compaction on top of auto-attached summarization layer. |
| 6 | ToolErrorMiddleware | Custom | Wraps tool calls in try/except, converts exceptions to ToolMessage with structured error JSON so LLM can self-correct. |
| 7 | DynamicToolConfigMiddleware | Custom | ⚠️ DEAD CODE - Stage-aware tool choice and filtering. Initialized with empty config, passes through without modification. |

#### Auto-Attached Middleware (Added by SDK)

| Middleware | Source | Purpose |
| --- | --- | --- |
| TodoListMiddleware | SDK | Provides write_todos tool for task planning |
| FilesystemMiddleware | SDK | Provides ls, read_file, write_file, edit_file, glob, grep tools via configured backend |
| SubAgentMiddleware | SDK | Provides task tool for delegation to subagents |
| AnthropicPromptCachingMiddleware | SDK | Anthropic cache breakpoints, prompt caching |
| PatchToolCallsMiddleware | SDK | Tool call normalization, patches dangling tool calls in message history |
| HumanInTheLoopMiddleware | SDK | HITL interrupt handling via interrupt_on parameter (configured for HITL_GATED_TOOLS) |

### Subagent Middleware Stacks

Each subagent has its own middleware configuration. Note: The SUBAGENT_MIDDLEWARE dict in configs.py is dead metadata; actual middleware is configured inline in each subagent's factory file.

#### Research Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| AgentDecisionStateMiddleware | Custom | Provides decision_log, assumption_log, approval_history state fields for decision tracking tools. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |
| SummarizationToolMiddleware | SDK | Agent-controlled compact_conversation tool. |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| SkillsMiddleware | SDK | On-demand SKILL.md loading. |
| DynamicToolConfigMiddleware | Custom | ⚠️ DEAD CODE - Empty config, no-op. |

#### Verification Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| AgentDecisionStateMiddleware | Custom | Provides decision_log, assumption_log, approval_history state fields. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

#### Spec Writer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

#### Plan Writer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |
| DynamicToolConfigMiddleware | Custom | ⚠️ DEAD CODE - Empty config, no-op. |

#### Code Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |
| CompletionGuardMiddleware | Custom | ⚠️ NAIVE - Prevents premature session termination via after_model hook. Has technical issues (logic duplication, type assumptions, no SDK precedent, no test coverage). Better solved via system prompt instructions. |
| DynamicToolConfigMiddleware | Custom | ⚠️ DEAD CODE - Empty config, no-op. |

#### Evaluation Agent

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |
| DynamicToolConfigMiddleware | Custom | ⚠️ DEAD CODE - Empty config, no-op. |

#### Document Renderer

| Middleware | Source | Purpose |
| --- | --- | --- |
| MemoryMiddleware | SDK | Per-agent AGENTS.md loading. |
| ToolErrorMiddleware | Custom | Wraps tool calls in try/except for error handling. |

### Custom Middleware Deep Dive

#### MetaAgentStateMiddleware

**Purpose**: Extends graph state with custom fields specific to the PM orchestrator (current_stage, decision_log, assumption_log, approval_history, project paths, participation mode).

**Why Custom**: The SDK provides TodoListMiddleware for todo lists, but doesn't provide a mechanism for custom state schema extension. This middleware uses the SDK's state_schema merging pattern (same as TodoListMiddleware) to add meta-agent-specific fields directly into the graph state. Tools return Command(update={...}) to update these fields.

**Status**: ✅ Active - Necessary for PM orchestrator state management.

#### DynamicSystemPromptMiddleware

**Purpose**: Recomposes the system prompt based on current_stage. Uses wrap_model_call to set the stage-appropriate system prompt on ModelRequest while before_model sanitizes message history to avoid duplicate system messages.

**Why Custom**: The SDK doesn't provide stage-aware prompt recomposition. This is specific to the meta-agent's multi-stage workflow (INTAKE → RESEARCH → DRAFTING → etc.). MUST be first in the explicit middleware list to ensure cache breakpoints are set on the current (not stale) system prompt.

**Status**: ✅ Active - Necessary for multi-stage PM workflow.

#### AskUserMiddleware

**Purpose**: Provides an ask_user tool that lets agents pose structured questions with free-form text input and multiple-choice options (always includes an implicit "Other" option). Uses LangGraph interrupt() to pause execution and wait for user input, then parses the response into a formatted ToolMessage.

**Why Custom**: Ported from deepagents_cli (deepagents_cli/ask_user.py). The CLI has this middleware for interactive questioning, but it's not part of the SDK. We ported it to maintain the same pattern for structured user questioning in the meta-agent.

**Status**: ✅ Active - Necessary for structured user questioning in PM orchestrator.

#### ToolErrorMiddleware

**Purpose**: Wraps tool calls in try/except to catch exceptions. Converts unhandled exceptions into ToolMessage with status="error" and a structured JSON payload so the LLM can see the failure and self-correct rather than crashing the agent run.

**Why Custom**: The SDK provides PatchToolCallsMiddleware for patching dangling tool calls in message history, but does NOT provide general tool error handling middleware that wraps tool calls in try/except. This fills that gap.

**Status**: ✅ Active - Necessary for robust error handling across all agents.

#### AgentDecisionStateMiddleware

**Purpose**: Provides decision_log, assumption_log, and approval_history state fields to ANY agent that needs structured decision tracking. This is the lightweight, reusable counterpart to MetaAgentStateMiddleware (which carries the full PM orchestrator state). Each agent instance gets its own isolated copy of these fields — no collision with the PM agent's state.

**Why Custom**: The SDK doesn't provide a general-purpose decision tracking middleware. This is intentionally lightweight — it only declares state fields. No hooks are needed. Uses the same state_schema merging pattern as TodoListMiddleware.

**Status**: ✅ Active - Necessary for decision tracking in research and verification agents.

#### DynamicToolConfigMiddleware

**Purpose**: Stage-aware tool choice and filtering. Uses wrap_model_call to dynamically set tool_choice and filter available tools based on current workflow stage and agent state.

**Why Custom**: Originally added as a bridge for server-side tools, but this was a naive implementation. Server-side tools are configured at the model level, not via middleware. The SDK doesn't provide this pattern because it's not the right approach.

**Status**: ⚠️ DEAD CODE - Initialized with tool_config={} in all agents (PM, research, evaluation, code, plan-writer). With an empty config, the middleware passes through all requests without modification. It exists as a placeholder for future stage-aware tool policies that have not yet been authored. Consider removing.

**TODO**: Remove this middleware and all references if stage-aware tool filtering is not needed. See file for complete removal guide.

#### CompletionGuardMiddleware

**Purpose**: Prevents premature session termination by checking if the model response suggests premature completion and injecting nudge/confirmation messages. Uses @after_model hook to check last AI message: if no tool calls AND no text content → inject nudge; if text but no tool calls → inject confirmation.

**Why Custom**: The SDK doesn't use @after_model hooks at all. This is a custom pattern not aligned with upstream conventions. The problem (preventing premature completion) is better solved through system prompt instructions or task state tracking, not middleware that blindly injects messages based on surface-level checks.

**Status**: ⚠️ NAIVE - CONSIDER REMOVAL. Multiple technical issues:
- Logic duplication (has_tool_calls/has_text computed but never used; real logic lives in check_response)
- Hard to read (response dict built on one massive line)
- Type assumptions (assumes content is strip()-able string, but AIMessage content can be blocks/multimodal shapes)
- No SDK/CLI precedent (neither SDK nor deepagents_cli use @after_model hooks)
- No test coverage

**TODO**: Remove this middleware. The problem is better solved through system prompt instructions or task state tracking. See file for complete removal guide.

### SDK Middleware Reference

#### MemoryMiddleware

**Source**: deepagents.middleware.memory

**Purpose**: Loads agent memory from AGENTS.md files. Supports multiple sources that are combined together. Injects memory content into the system prompt via append_to_system_message.

**Why SDK**: This is a core SDK middleware for per-agent instruction loading. We use it for all agents to load their AGENTS.md files with tiered resolution (root → agent-specific → project-local).

#### SkillsMiddleware

**Source**: deepagents.middleware.skills

**Purpose**: Loads skills from backend sources and injects them into the system prompt using progressive disclosure (metadata first, full content on demand).

**Why SDK**: This is a core SDK middleware for dynamic skill loading. We use it for all agents to load SKILL.md files from the skills directories (langchain, langsmith, anthropic).

#### SummarizationToolMiddleware

**Source**: deepagents.middleware.summarization (via create_summarization_tool_middleware)

**Purpose**: Provides a compact_conversation tool for manual compaction. Composes with SummarizationMiddleware to reuse its summarization engine (model, backend, trigger thresholds) to let the agent compact its own context window.

**Why SDK**: This is an SDK middleware that builds on the auto-attached SummarizationMiddleware. We use it in agents that need agent-controlled compaction (PM, research, evaluation, code, plan-writer).

#### FilesystemMiddleware

**Source**: deepagents.middleware.filesystem (auto-attached)

**Purpose**: Provides filesystem and optional execution tools to an agent (ls, read_file, write_file, edit_file, glob, grep, execute). Can evict large tool results to filesystem storage.

**Why SDK**: This is auto-attached by create_deep_agent(). We configure it with a CompositeBackend for the PM orchestrator and bare FilesystemBackend for subagents.

#### SubAgentMiddleware

**Source**: deepagents.middleware.subagents (auto-attached)

**Purpose**: Provides a task tool for delegation to subagents. Manages the subagent lifecycle and message routing.

**Why SDK**: This is auto-attached by create_deep_agent(). We configure it with our subagent definitions (research-agent, spec-writer, etc.).

#### TodoListMiddleware

**Source**: SDK (auto-attached, not exported in __init__.py)

**Purpose**: Provides a write_todos tool for task planning.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed.

#### AnthropicPromptCachingMiddleware

**Source**: SDK (auto-attached)

**Purpose**: Anthropic cache breakpoints, prompt caching.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed.

#### PatchToolCallsMiddleware

**Source**: deepagents.middleware.patch_tool_calls (auto-attached)

**Purpose**: Patches dangling tool calls in the messages history. When an AIMessage has tool_calls but no corresponding ToolMessage (e.g., cancelled), it adds a ToolMessage saying the call was cancelled.

**Why SDK**: This is auto-attached by create_deep_agent(). No explicit configuration needed. Note: This is NOT a tool error handler — it's for fixing incomplete message history.