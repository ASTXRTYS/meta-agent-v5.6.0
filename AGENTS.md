# Repository Guidelines

This document is the contributor and maintainer guide for `meta-agent-v5.6.0`. It is intentionally implementation-specific: use it as the default operating manual when you add features, debug behavior, tune prompts, or extend the Deep Agents harness.

## Project Structure & Module Organization

### Top-level layout

The repository is organized around one Python package (`meta_agent/`) plus policy and validation assets:

- `meta_agent/`: runtime code (graph assembly, subagent runtimes, tools, middleware, prompts, state, eval harness glue).
- `tests/`: canonical contract/integration/eval/drift suites. `tests/unit/` is legacy quarantine.
- `docs/`: architecture references and test-catalog traceability docs.
- `datasets/`: golden/bronze fixtures used by eval and calibration flows.
- `scripts/testing/`: inventory + traceability generators for catalog drift control.
- `.agents/`: memory, skills, project workspaces, and protocol files.
- Root configs: `pyproject.toml`, `Makefile`, `langgraph.json`, `.env.example`.

### Runtime package map (`meta_agent/`)

Use these boundaries when making changes:

- `graph.py`: orchestrator graph composition via `create_deep_agent()`.
- `server.py`: LangGraph dev-server entrypoint (`meta_agent.server:get_agent`), runtime dependency checks, `.env` load.
- `backend.py`: backend contract (`CompositeBackend`, bare filesystem backend, checkpointer/store factories).
- `state.py`: canonical state schema (`MetaAgentState`) and stage transition model.
- `configuration.py` + `model_config.py`: env-backed configuration and per-agent model resolution/policy.
- `tools/`: all custom tools and registry wiring.
- `middleware/`: custom middleware implementations and state extensions.
- `subagents/`: each runtime factory (`research-agent`, `spec-writer`, `plan-writer`, `code-agent`, `verification-agent`, `evaluation-agent`, `document-renderer`), plus centralized provisioning.
- `prompts/`: source-of-truth prompt markdown and composition loaders.
- `stages/`: formalized stage interface and stage gate logic.
- `evals/`: eval runners, rubrics, research eval infrastructure.

### Project workspace hierarchy (runtime artifacts)

The runtime scaffolds project work under:

```text
.agents/pm/projects/<project_id>/
├── meta.yaml
├── artifacts/
│   ├── intake/
│   ├── research/
│   ├── spec/
│   ├── planning/
│   └── audit/
├── evals/
├── logs/
└── .agents/
    ├── pm/AGENTS.md
    ├── research-agent/AGENTS.md
    ├── spec-writer/AGENTS.md
    ├── plan-writer/AGENTS.md
    ├── code-agent/AGENTS.md
    ├── verification-agent/AGENTS.md
    └── evaluation-agent/AGENTS.md
```

If you change scaffolding in `meta_agent/project.py`, update drift tests and this guide in the same PR.

## Build, Test, and Development Commands

Use a local virtualenv and run everything from repo root.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Core commands

- `make dev`: installs editable package with dev extras.
- `make install`: installs editable package without dev extras.
- `make lint`: compile-checks key runtime modules.
- `make test`: canonical suite (excludes `tests/unit/`).
- `make test-all`: all tests including legacy quarantine.
- `make test-contracts`: contract tests only.
- `make test-integration`: integration tests only.
- `make test-drift`: convention/regression drift tests.
- `make test-evals`: eval tests (`-m eval`, requires `ANTHROPIC_API_KEY`).
- `make evals`, `make evals-p0`, `make evals-p1`, `make evals-p2`: run eval pipelines by phase.
- `make test-catalogs`: focused drift checks for runtime and SDK catalog parity.
- `python scripts/testing/generate_traceability.py`: regenerate `docs/testing/TEST_TRACEABILITY.{md,json}` after catalog updates.

### Running the app locally

- Launch with plain `langgraph dev` from repo root.
- Do not use extra launch flags for normal local runs (for this codebase, avoid passing options such as `--no-browser` unless you are explicitly validating CLI behavior).
- `langgraph.json` points to `meta_agent.server:get_agent`; changing entrypoint paths requires matching updates in docs/tests.

## Coding Style & Naming Conventions

### Python and typing

- Target runtime: Python 3.11+.
- Indentation: 4 spaces.
- Prefer explicit type hints on public functions and runtime contracts.
- Keep dataclasses/TypedDicts authoritative for structured payloads.

Naming patterns:

- Modules/functions/files: `snake_case`
- Classes/dataclasses: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

### Architecture conventions (important)

- Prefer SDK-native patterns over custom reimplementation.
- Centralize cross-agent behavior:
  - Middleware assembly in `meta_agent/subagents/provisioner.py`.
  - Tool registration in `meta_agent/tools/registry.py`.
  - Model defaults in `meta_agent/model_config.py`.
- State-mutating tools must return `Command(update={...})` (not ad hoc dict mutations) in `@tool` wrappers.
- Keep prompt source in markdown (`meta_agent/prompts/*.md`) and composition logic in slim loader modules.

### Filesystem and backend conventions

Do not change these routes casually; drift tests enforce them:

- default route: `FilesystemBackend(root_dir=<repo_root>, virtual_mode=True)`
- `/memories/` -> `StoreBackend`
- `/large_tool_results/` -> `StateBackend`
- `/conversation_history/` -> `StateBackend`
- memory/skills loaders use a separate bare filesystem backend (`virtual_mode=False`) for absolute-path reads.

## Testing Guidelines

### Test suite structure

- `tests/contracts/`: invariants and interface contracts (fast, no model calls).
- `tests/integration/`: runtime wiring, middleware composition, scaffolding behavior.
- `tests/evals/`: behavioral eval tests (live API dependent).
- `tests/drift/`: anti-regression convention guards (catalogs, provisioning, backend routes, stubs, hygiene).
- `tests/unit/`: legacy quarantine. Do not add new tests here.

### Markers and placement

Every new test file must:

1. Live in `contracts`, `integration`, `evals`, or `drift`.
2. Use the correct pytest marker.
3. Include `COVERS:` ids aligned to catalog components.
4. Include `REPLACES:` when replacing old legacy tests.

### Catalog-driven coverage workflow (mandatory)

When you add/rename/remove a tool, middleware, subagent, state field, or SDK touchpoint:

1. Update `docs/testing/runtime_components.yaml` and/or `docs/testing/sdk_touchpoints.yaml`.
2. If stubs are introduced or retired, update `docs/testing/intentional_stubs.yaml`.
3. Regenerate traceability:

```bash
python scripts/testing/generate_traceability.py
```

4. Run:

```bash
make test-contracts
make test-integration
make test-drift
```

If drift tests fail, assume convention mismatch first, not test fragility.

## Commit & Pull Request Guidelines

### Commit style used in this repository

History is mostly Conventional Commit style. Follow that pattern:

- `feat(scope): ...`
- `fix(scope): ...`
- `refactor(scope): ...`
- `docs: ...`
- `test: ...`
- `chore: ...`

Use precise scopes (`config`, `subagents`, `middleware`, `tools`, `tests`, etc.). Avoid non-descriptive one-word messages.

### PR expectations

Each PR should include:

1. Problem statement and why the change is needed.
2. Approach summary with affected modules.
3. Validation commands run and outcomes.
4. Any catalog updates and regenerated traceability artifacts.
5. If behavior changed at stage or runtime-contract level, reference affected spec/docs sections.

Keep PRs focused. If you change runtime conventions (backend routes, provisioning, memory loading, tool names), include corresponding drift/integration updates in the same PR.

## Security & Configuration Tips

### Environment configuration

Start from `.env.example`:

- Required for most workflows:
  - `ANTHROPIC_API_KEY`
  - `LANGSMITH_API_KEY`
- Common defaults:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_PROJECT=meta-agent`
  - `META_AGENT_MODEL=anthropic:claude-opus-4-6`
  - `META_AGENT_MAX_REFLECTION_PASSES=3`
  - `LANGCHAIN_CALLBACKS_BACKGROUND=false` (important for trace flush reliability in experiment runs)

`META_AGENT_MODEL_PROVIDER` and `META_AGENT_MODEL_NAME` are deprecated in favor of `META_AGENT_MODEL=provider:model`.

### Runtime dependency guard

`meta_agent/server.py` enforces minimum runtime versions (for `deepagents`, `langgraph-cli`, and `langchain-anthropic`) at startup. If startup fails, reinstall from repo root with:

```bash
pip install -e ".[dev]"
```

### Command/file safety behavior

- `execute_command` is HITL-gated and validated by `meta_agent/safety.py`.
- Path traversal and unsafe path patterns are blocked by safety checks.
- Never commit `.env` or secret-bearing artifacts.

### Persistence expectations

Current default store/checkpointer are in-memory (`MemorySaver`, `InMemoryStore`), suitable for local development and tests. If you need durable cross-restart persistence, plan a production store/checkpointer migration (e.g., Postgres-backed saver/store) and update docs/tests accordingly.

## Agent-Specific Instructions (Deep Agents / LangGraph SDK Conventions)

This section is the operational checklist for feature work in the harness.

### 1) Adding a new API feature or tool

When introducing a tool or tool behavior:

1. Implement raw logic in `meta_agent/tools/__init__.py`.
2. Add/update the `@tool` wrapper there.
3. If state mutates, return `Command(update={...})`.
4. Register in `TOOL_FUNCTIONS` and `TOOL_REGISTRY` (`meta_agent/tools/registry.py`).
5. If sensitive, add to `HITL_GATED_TOOLS` and verify `interrupt_on` behavior.
6. Add/adjust contract and integration tests.
7. Update testing catalogs and regenerate traceability.

Do not hand-roll alternate tool registration paths outside the central registry.

### 2) Adding a new sub-agent

Sub-agent additions require synchronized updates across registries:

1. Add runtime factory under `meta_agent/subagents/`.
2. Register lazy factory in `meta_agent/subagents/configs.py` (`AGENT_REGISTRY`).
3. Add provisioning profile in `meta_agent/subagents/provisioner.py` (`PROFILE_REGISTRY`).
4. Add model entry in `meta_agent/model_config.py` (`AGENT_MODEL_REGISTRY`).
5. Add tool mapping in `meta_agent/tools/registry.py` (`TOOL_REGISTRY`).
6. If project-local memory is required, include agent in `PROJECT_AGENTS` (`meta_agent/project.py`).
7. Add/update drift + integration tests that enforce provisioning and scaffolding parity.

Runtimes must call `build_provisioning_plan(...)`; manual middleware assembly is intentionally blocked by drift tests.

### 3) Adding or modifying middleware

- Put custom middleware in `meta_agent/middleware/`.
- Integrate via provisioning profiles (subagents) or orchestrator explicit stack (`graph.py`) in correct order.
- Preserve critical order constraints:
  - `DynamicSystemPromptMiddleware` must stay first in orchestrator explicit middleware.
  - `ToolErrorMiddleware` should stay active across orchestrator and subagents.
- If middleware adds state, use schema extension patterns (`state_schema`, reducers) instead of ad hoc side channels.
- Update `docs/architecture/middleware_catalog.md` and relevant drift tests.

### 4) Prompt addition, expansion, or debugging

Prompt conventions in this repo:

- Keep source prompt text in markdown files under `meta_agent/prompts/`.
- Keep Python loaders thin (`construct_*_prompt`) and cache markdown reads with `lru_cache`.
- For PM orchestration, stage-aware composition flows through `construct_pm_prompt()` + `DynamicSystemPromptMiddleware`.
- When expanding prompts, update both:
  - markdown source(s)
  - composition logic (if section wiring changes)

Debugging prompt behavior:

1. Reproduce with `langgraph dev` and inspect traces in LangSmith.
2. Confirm the right stage is set in state (`current_stage`).
3. Check system-message duplication behavior (middleware strips stale system messages by design).

### 5) Debugging agent runtime behavior

Use this order:

1. `langgraph dev` (plain command from repo root).
2. Reproduce through Studio/API with minimal input.
3. Inspect traces with LangSmith tools/CLI.
4. Validate stage gates and artifact provenance in state/logs.
5. Run focused test subsets (`contracts`/`integration`/`drift`) before broad suite.

For code-agent loops, inspect normalized status blocks (`complete`, `in_progress`, `blocked`, `parse_error`) and treat `parse_error` as schema-contract breakage first.

### 6) Memory model and artifact hierarchy (onboarding-critical)

Memory loading is tiered and explicit:

- Global per-agent memory: `.agents/<agent>/AGENTS.md`
- Project-local per-agent memory: `.agents/pm/projects/<project_id>/.agents/<agent>/AGENTS.md`
- Resolution order from `get_memory_sources(...)`: project-local first, global second.
- Exception: `document-renderer` uses repo-level memory profile by design.

Skills are loaded from three canonical roots:

- `.agents/skills/langchain/config/skills`
- `.agents/skills/langsmith/config/skills`
- `.agents/skills/anthropic/skills`

Do not point `SkillsMiddleware` at top-level clone roots; it must point at directories containing skill subdirectories (each with `SKILL.md`).

### 7) LangGraph dev-server usage conventions

- Launch from repo root with:

```bash
langgraph dev
```

- Use standard defaults during normal development; avoid extra launch flags (including no-browser style flags) unless explicitly debugging CLI runtime behavior.
- Keep `langgraph.json` aligned with `meta_agent.server:get_agent`.
- If dev server startup fails, check:
  - dependency guard output from `server.py`
  - `.env` loading and required keys
  - editable install status (`pip install -e ".[dev]"`)

---

If you are unsure where a change belongs, prefer these anchors:

- Runtime composition contract: `meta_agent/graph.py`
- Provisioning contract: `meta_agent/subagents/provisioner.py`
- Tool contract: `meta_agent/tools/registry.py`
- State contract: `meta_agent/state.py`
- Catalog contract: `docs/testing/*.yaml`

That pattern keeps this codebase predictable and keeps drift tests green.
