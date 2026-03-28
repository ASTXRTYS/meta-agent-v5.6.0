# AGENTS.md — Meta-Agent v5.6.0

## Local Development Setup

Follow these steps exactly to get the dev server running with the Studio UI.

### 1. Install Dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Prefer a project-local virtualenv so `langgraph dev` uses this repo's dependency baseline,
not a globally installed CLI/runtime from your shell PATH.

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

**Do NOT commit `.env` to git.** It is in `.gitignore`.

### 3. Launch the Dev Server

```bash
langgraph dev
```

If you are not activating the venv in your shell, run:

```bash
./.venv/bin/langgraph dev
```

For normal local development, run this command exactly as shown so Studio opens automatically.
Do not add `--no-browser` unless you explicitly need headless mode.

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
make test          # Run all 410 unit tests
make evals-p0      # Run Phase 0 evals (INFRA-001 through INFRA-004)
make evals-p1      # Run Phase 1 evals (INFRA-005–008, STAGE-001–002)
make evals-p2      # Run Phase 2 evals (PM-001–008, STAGE-003, GUARD-001–004)
make evals         # Run all evals
```

### Troubleshooting

| Problem | Fix |
|---|---|
| `No dependencies found in config` | Your `langgraph.json` is missing `"dependencies": ["."]`. See the file in repo root. |
| `ANTHROPIC_API_KEY not set` | Your `.env` file is missing or doesn't have the Anthropic key. Copy from `.env.example`. |
| `ModuleNotFoundError: deepagents` | Run `pip install -e .` — the package isn't installed. |
| `langgraph: command not found` | Run `pip install "langgraph-cli[inmem]>=0.4.12"` |
| `unexpected keyword argument 'system_message'` / `'system_prompt'` | Your runtime packages are outdated or mixed. Recreate/activate `.venv`, run `pip install -e ".[dev]"`, and relaunch from that env. |
| `Connection refused` on Studio | The dev server isn't running. Run `langgraph dev` first. |
| Port already in use | Another process is on 2024. Use `langgraph dev --port 8123` or kill the existing process. |

---

## Project Status

Phases 0, 1, and 2 are complete and running on the **real Deep Agents SDK** (`deepagents==0.4.12`). 410 unit tests pass. 23 eval functions implemented across 4 categories. The orchestrator produces a real `CompiledStateGraph` via `create_deep_agent()` and successfully invokes the Anthropic API.

## How It Works

`langgraph.json` points to `meta_agent.server:get_agent`. That function calls `create_graph()` in `meta_agent/graph.py`, which calls `create_deep_agent()` from the real Deep Agents SDK. The SDK auto-attaches TodoListMiddleware, FilesystemMiddleware, SubAgentMiddleware, SummarizationMiddleware, and prompt caching. We pass in our custom middleware, tools, backend, checkpointer, and HITL config.

### What `create_deep_agent()` Provides Automatically

These are **auto-attached** by the SDK — we do NOT instantiate them:

| Middleware | What It Does |
|---|---|
| `TodoListMiddleware` | Provides `write_todos` tool for task planning |
| `FilesystemMiddleware` | Provides `ls`, `read_file`, `write_file`, `edit_file` tools via configured `backend` |
| `SubAgentMiddleware` | Provides `task` tool for delegation to subagents |
| `SummarizationMiddleware` | Auto-compacts context when token usage is high |
| Prompt caching + tool patching | Anthropic cache breakpoints, tool call normalization |

### What We Configure Explicitly

| Parameter | Value | Spec Reference |
|---|---|---|
| `model` | `"claude-opus-4-6"` (from env) | Section 10.5 |
| `system_prompt` | `construct_orchestrator_prompt()` output | Section 7.3 |
| `tools` | Custom tools from `meta_agent/tools/` (registered as `@tool`) | Sections 8.1–8.14 |
| `middleware` | `[DynamicSystemPromptMiddleware, MetaAgentStateMiddleware, ToolErrorMiddleware]` | Sections 22.4, 22.12 |
| `backend` | `FilesystemBackend(root_dir=<repo_root>, virtual_mode=True)` | Section 4.2 |
| `checkpointer` | `MemorySaver()` (InMemorySaver) | Section 4.3 |
| `store` | `InMemoryStore()` | Section 4.2 |
| `interrupt_on` | `{tool_name: True for tool_name in HITL_GATED_TOOLS}` | Section 9.2 |
| `name` | `"meta-agent-orchestrator"` | — |

### Custom Middleware

| Middleware | File | Hook Type | Purpose |
|---|---|---|---|
| `DynamicSystemPromptMiddleware` | `middleware/dynamic_system_prompt.py` | `@wrap_model_call` / `@before_model` | Reads `current_stage` from state, builds stage-aware prompt, strips stale system messages from history in `before_model`, then applies request-level system prompt in wrap hooks. **MUST be first in middleware list.** |
| `ToolErrorMiddleware` | `middleware/tool_error_handler.py` | `@wrap_tool_call` | Wraps tool calls in try/except, returns structured error JSON |
| `CompletionGuardMiddleware` | `middleware/completion_guard.py` | `@after_model` | Injects nudge when model returns no tool calls |
| `MemoryLoaderMiddleware` | `middleware/memory_loader.py` | `@before_model` | Loads per-agent AGENTS.md with isolation |

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
└── evals/              # 23 eval functions, CLI runner
```

## Remaining Work (Phases 3-5)

- **Phase 3:** Research + Spec (research-agent, verification-agent, spec-writer as real SubAgents)
- **Phase 4:** Planning + Execution (plan-writer, code-agent with 3 nested sub-agents)
- **Phase 5:** Evaluation + Audit (full LangSmith integration, CLI)

## Spec and Plan Documents

- **Technical Specification (source of truth):** `/Users/Jason/2026/V3/technical-specification-v5.6.0-final (3).md`
- **Implementation Deviation Record:** `DEVIATION_RECORD.md`

## LangSmith Datasets (Pre-loaded)

- `meta-agent-phase-0-scaffolding` (15 examples, ID: `835a9b10-371f-413c-99f9-bdc19e2c4c25`)
- `meta-agent-phase-1-orchestrator` (18 examples, ID: `70f34716-7d60-4042-a565-c086b063809d`)
- `meta-agent-phase-2-intake-prd` (11 scenarios, ID: `b7c0535f-c17f-48bd-8663-e2dda2bd8f07`)
