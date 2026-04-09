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

***Checking .reference/libs/deepagents/deepagents (canonical SDK reference) and .reference/libs/cli/deepagents_cli (prodution deepagent coding assistant) tends to suffice as examples of Conventions i.e how middleware, sdk, imports, langchain conventions for when using the sdk.

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
| tool_choice | tool_choice on bind_tools() | Not yet implemented | ⏸️ Planned |
| Tool Filtering | ModelRequest.tools modification | Not yet implemented | ⏸️ Planned |
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
| backend | create_composite_backend(repo_root): default FilesystemBackend(root_dir=<repo_root>, virtual_mode=True) + routes (/memories/, /large_tool_results/, /conversation_history/) | Section 4.2 |
| checkpointer | MemorySaver() (InMemorySaver) | Section 4.3 |
| store | InMemoryStore() | Section 4.2 |
| interrupt_on | {tool_name: True for tool_name in HITL_GATED_TOOLS} | Section 9.2 |
| skills | skills/langchain/config/skills, skills/langsmith/config/skills, skills/anthropic/skills | Sections 11, 22.4 |
| name | "meta-agent-orchestrator" | — |

### Custom Middleware

| Middleware | File | Hook Type | Purpose |
| --- | --- | --- | --- |
| ArtifactProtocolMiddleware | middleware/artifact_protocol.py | SDK middleware | Enforces structural validation (Pydantic/Regex/JSON) for artifacts defined in `.agents/protocols/artifacts.yaml` by injecting a `validate_artifact` tool. |
| AskUserMiddleware | middleware/ask_user_middleware.py | SDK middleware | Provides the `ask_user` tool, converting classification approaches to structured LLM-driven HITL checkpoints. |
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

### Filesystem Backend Convention (Track A)

The filesystem contract is centralized in `meta_agent/backend.py` and must remain deterministic:

- **Default route:** `FilesystemBackend(root_dir=<repo_root>, virtual_mode=True)` for normal workspace files.
- **Persistent store route:** `/memories/ -> StoreBackend` for cross-thread memory.
- **Ephemeral offload routes:** `/large_tool_results/ -> StateBackend` and `/conversation_history/ -> StateBackend`.
- **Memory/skills source loading:** `create_bare_filesystem_backend(virtual_mode=False)` for `MemoryMiddleware` and `SkillsMiddleware` absolute source reads.
- **Project workspace contract:** project artifacts and per-agent AGENTS.md files live under `/.agents/pm/projects/{project_id}/...` (on disk: `<repo_root>/.agents/pm/projects/{project_id}/...`).

**Required change protocol for maintainers:**
1. Update `meta_agent/backend.py` and/or `meta_agent/project.py` first.
2. Run `tests/drift/test_filesystem_backend_convention.py`.
3. Run `tests/integration/test_memory_and_skills.py`.
4. If memory/scaffolding semantics changed, also run `tests/drift/test_subagent_provisioning_convention.py`.
5. Update this AGENTS.md and `README.md` if any path or routing behavior changed.

### Subagent Provisioning Convention (Track B)

All runtime subagents now use a centralized, profile-driven provisioning system:

- **Single source of truth:** `meta_agent/subagents/provisioner.py` (`PROFILE_REGISTRY` + `build_provisioning_plan()`).
- **Runtime factories MUST call the provisioner:** runtime files for `research-agent`, `spec-writer`, `plan-writer`, `code-agent`, `verification-agent`, `evaluation-agent`, and `document-renderer` must assemble middleware via `build_provisioning_plan(...)`.
- **Runtime factories MUST NOT manually instantiate per-agent middleware stacks** (`MemoryMiddleware`, `SkillsMiddleware`, `create_summarization_tool_middleware`, `AskUserMiddleware`, `ArtifactProtocolMiddleware`, `AgentDecisionStateMiddleware`, `ToolErrorMiddleware`) outside the provisioner.
- **Document-renderer special-case is intentional:** it uses `MemoryMiddleware + ToolErrorMiddleware` via profile middleware and passes Anthropic skills via `create_deep_agent(skills=...)` from `ProvisioningPlan.deep_agent_skills`.
- **Project scaffolding alignment rule:** `PROJECT_AGENTS` must remain aligned with provisioner profiles using `use_project_memory=True` plus `"pm"`.

**Required change protocol for maintainers:**
1. Update `PROFILE_REGISTRY` first.
2. Run `tests/integration/test_subagent_provisioner_parity.py`.
3. Run `tests/drift/test_subagent_provisioning_convention.py`.
4. Run `tests/drift/test_filesystem_backend_convention.py` if memory/scaffolding coupling changed.
5. Update this AGENTS.md, `README.md`, and `docs/architecture/middleware_catalog.md` if behavior changes.

**Enforced by tests:**
- `tests/drift/test_filesystem_backend_convention.py`
- `tests/integration/test_subagent_provisioner_parity.py`
- `tests/drift/test_subagent_provisioning_convention.py`
- `tests/integration/test_memory_and_skills.py` (scaffolding + memory-load coverage)

### Enabled User Stories (Provisioning + Filesystem + Artifact Organization)

1. As a runtime user, I can rely on a deterministic filesystem structure so stage transitions do not fail due to path drift.
2. As a maintainer, I can add or adjust a subagent middleware stack in one profile location and avoid cross-file drift.
3. As a reviewer, I can verify middleware ordering and stable config parity through deterministic parity tests before merge.
4. As a developer adding a new project-scoped agent, I get automatic guardrails that fail fast if scaffolding and runtime memory provisioning diverge.
5. As an architect, I can preserve intentional per-agent differences (including document-renderer special behavior) without a one-size-fits-all stack.
6. As an operations owner, I can rely on drift tests to prevent silent regressions from manual runtime edits.
7. As a project owner, I can trust project-local agent memory (`/.agents/pm/projects/{project_id}/.agents/{agent}/AGENTS.md`) to override repo defaults predictably.
8. As a document pipeline owner, I can keep document-renderer behavior intentionally isolated from project memory while still using shared provisioning logic.

### Interrupt Communication Convention

When pausing an agent workflow via LangGraph's `interrupt()`, the emitted payload **MUST NOT** be a raw primitive dictionary.

Instead, a strictly-typed schema must be defined in `meta_agent/schemas/` and instantiated by the emitting tool before passing it to `interrupt()`. This guarantees that UI clients traversing the backend API can import and rely on static object shapes (e.g. `AskUserRequest`, `ExecuteCommandRequest`, `ApprovalRequest`) to render interactive components like modals, radio buttons, or code blocks natively without pulling in execution modules or heavy `langchain` overhead.

## Formalized Stage Interface (FSI) Convention

To ensure consistent telemetry, state synchronization, and governance across all workflow transitions, all workflow stages MUST adhere to the **Formalized Stage Interface (FSI)**.

### 1. Mandatory Inheritance
All stage handler classes must inherit from `meta_agent.stages.base.BaseStage`. Direct implementation of gate logic without the base class is prohibited.

### 2. Implementation Hooks
Stage logic must be implemented in the protected `_check_impl` hooks, never by overriding the public gate methods.
- Implement entry logic in: `_check_entry_impl(self, state: dict[str, Any]) -> ConditionResult`
- Implement exit logic in: `_check_exit_impl(self, state: dict[str, Any]) -> ConditionResult`

### 3. Template Method Pipeline
The `BaseStage` provides public template methods (`check_entry_conditions` and `check_exit_conditions`) that automatically execute the following pipeline:
1. **Normalization**: Ensures `state` is a dictionary.
2. **Synchronization**: Calls `sync_from_state` to hydrate persistent counters (e.g., feedback cycles).
3. **Execution**: Invokes the agent's `_check_impl` hook.
4. **Telemetry**: Emits a LangSmith span with rich metadata via `_emit_span`.
5. **Post-processing**: Normalizes the `ConditionResult` to ensure `met` and `unmet` parity.

### 4. State Synchronization
Permanent workflow counters (like `revision_count` via the `stage_metadata` dictionary) must be hydrated in the `sync_from_state` method. This ensures that in-memory counters remain accurate across graph resumes from checkpoints.

### 5. Telemetry & The `_span_carrier`
The base class provides a `_span_carrier` helper. This is a no-op method used specifically to capture telemetry metadata. Do not remove or shadow this method in subclasses.

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

*See `docs/project/phase_3_evaluation_report.md` for historical observations and bug analysis.*

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

## Testing & Evaluation

*See `docs/testing/testing_guidelines.md` for complete test directories, legacy ratchets, LangSmith catalogs, and eval instructions.*

## Spec and Plan Documents

- **Technical Specification (source of truth):** `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Spec.md` (v5.6.1)
- **Development Plan:** `/Users/Jason/2026/v4/meta-agent-v5.6.0/Full-Development-Plan.md` (updated 2026-03-29)
- **Implementation Deviation Record:** `/Users/Jason/2026/v4/meta-agent-v5.6.0/DEVIATION_RECORD.md`

## Middleware Catalog

*See `docs/architecture/middleware_catalog.md` for the full catalog of SDK and custom middleware per agent.*
