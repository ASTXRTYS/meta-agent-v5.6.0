# Canonical Technical Specification

Current-State Specification for the Long Horizon Meta Harness

Version: 2026-04-11 current-state draft

Prepared for: Jason M.

Status: Canonical replacement candidate for `Full-Spec.md`

---

## 1. Executive Summary

This document describes the application as it exists in the current repository, not as the original phase plan intended it to exist. `Full-Spec.md` remains useful as historical design context, especially for the vision of a local-first meta-agent that turns product intent into PRDs, research bundles, technical specifications, plans, implementation work, evaluations, and audits. The runtime, however, has evolved into a registry-driven Deep Agents application with a narrower implemented surface and several architecture conventions that are now more important than the original phase narrative.

The application is a Python 3.11+ local-first multi-agent harness built on:

- Deep Agents for the primary `create_deep_agent(...)` runtime, filesystem tooling, task delegation, skills, memory, and middleware composition.
- LangGraph for graph serving, checkpointing, store integration, interrupts, and the `langgraph dev` runtime.
- LangChain for model initialization, tools, middleware types, and chat model abstractions.
- LangSmith for tracing, traceable spans, and intended evaluation workflows.
- Anthropic and OpenAI model providers through a centralized model control plane, with Anthropic as the default runtime provider.

The canonical runtime entry point is `meta_agent.server:get_agent`, referenced by `langgraph.json`. That factory validates minimum runtime dependency versions, loads `.env`, enables LangChain debug logging, constructs `MetaAgentConfig`, and delegates to `meta_agent.graph.create_graph(...)`. The main graph is a Deep Agent named `meta-agent-pm`. The PM/orchestrator is not a custom LangGraph supervisor; it is a Deep Agents graph configured with explicit middleware, custom tools, a composite backend, a LangGraph checkpointer/store pair, and seven orchestrator-level subagents.

The implementation no longer cleanly matches the old claim that "Phase 4 was not started." The repository currently includes runtime modules for plan-writer, code-agent, evaluation-agent, and document-renderer, plus a centralized subagent provisioner and model control plane. At the same time, the repository has also been purged in ways that make several plan-era claims false: `tests/`, `docs/`, `datasets/`, `scripts/`, and `meta_agent/evals/` are absent from the current working tree, while the Makefile and older docs still reference them. The current spec must therefore distinguish implemented runtime code from stale plans, deleted test/eval infrastructure, and historical claims preserved in old documents or deleted files.

---

## 2. Evidence Snapshot

This specification was derived from the current working tree and these primary source files:

- Runtime entry: `langgraph.json`, `meta_agent/server.py`, `meta_agent/graph.py`
- Configuration and model policy: `pyproject.toml`, `.env.example`, `meta_agent/configuration.py`, `meta_agent/model_config.py`, `meta_agent/anthropic_api.py`, `meta_agent/openai_api.py`
- Backend and persistence: `meta_agent/backend.py`, `meta_agent/config/memory.py`
- State and stages: `meta_agent/state.py`, `meta_agent/stages/base.py`, `meta_agent/stages/intake.py`, `meta_agent/stages/prd_review.py`, `meta_agent/stages/research.py`, `meta_agent/stages/spec_generation.py`, `meta_agent/stages/spec_review.py`
- Subagents: `meta_agent/subagents/configs.py`, `meta_agent/subagents/provisioner.py`, `meta_agent/subagents/research_agent.py`, `meta_agent/subagents/spec_writer_agent.py`, `meta_agent/subagents/plan_writer_runtime.py`, `meta_agent/subagents/code_agent_runtime.py`, `meta_agent/subagents/evaluation_agent_runtime.py`, `meta_agent/subagents/verification_agent_runtime.py`, `meta_agent/subagents/document_renderer.py`
- Tools: `meta_agent/tools/__init__.py`, `meta_agent/tools/registry.py`, `meta_agent/tools/eval_tools.py`
- Middleware: `meta_agent/middleware/dynamic_system_prompt.py`, `meta_agent/middleware/meta_state.py`, `meta_agent/middleware/ask_user.py`, `meta_agent/middleware/artifact_protocol.py`, `meta_agent/middleware/agent_decision_state.py`, `meta_agent/middleware/tool_error_handler.py`
- Prompt sources: `meta_agent/prompts/*.py`, `meta_agent/prompts/*.md`
- Artifact protocols: `.agents/protocols/artifacts.yaml`
- Project memory and artifacts: `.agents/pm/projects/meta-agent/**`
- Historical comparison: `Full-Spec.md`, `Full-Development-Plan.md`, `Readme.md`, and the deleted `DEVIATION_RECORD.md` as recovered from git history

The current git worktree is dirty before this spec was created: `AGENTS.md`, `DEVIATION_RECORD.md`, `R1.md`, `R2.md`, and `VIV.md` are deleted, and `main` is ahead of `origin/main` by three commits. Those pre-existing changes are treated as user-owned state.

---

## 3. Alignment and Deviation From `Full-Spec.md`

### 3.1 Still Aligned

The current application still follows these core ideas from `Full-Spec.md`:

- The PM/orchestrator is the central agent and is responsible for stakeholder-facing requirements flow.
- Deep Agents is the chosen abstraction over raw LangGraph for the core agent harness.
- LangGraph is the serving and persistence substrate through `langgraph dev` and `langgraph.json`.
- The runtime is local-first and repository-rooted.
- Artifacts are intended to live under `.agents/pm/projects/<project_id>/...`.
- The workflow state machine still names ten stages: `INTAKE`, `PRD_REVIEW`, `RESEARCH`, `SPEC_GENERATION`, `SPEC_REVIEW`, `PLANNING`, `PLAN_REVIEW`, `EXECUTION`, `EVALUATION`, and `AUDIT`.
- Per-agent `AGENTS.md` memory is still a first-class convention.
- PM, research, spec writer, plan writer, code, verification, evaluation, and rendering roles still exist as architectural concepts.
- Eval-first behavior is still part of the prompt/tool contract, especially through PRD and architecture eval suite artifacts.
- HITL remains central through `interrupt(...)`, `AskUserMiddleware`, and HITL-gated tools.
- The corrected SDK-native CompositeBackend architecture has been absorbed into the runtime.

### 3.2 Major Deviations

The current codebase deviates from the old spec in the following important ways:

- The runtime is now registry-driven. Four registries must stay aligned: `PROJECT_AGENTS`, `PROFILE_REGISTRY`, `AGENT_MODEL_REGISTRY`, and `TOOL_REGISTRY`.
- The old plan's `tests/`, `docs/`, `datasets/`, `scripts/`, and `meta_agent/evals/` surfaces are not present in the working tree, even though `Makefile`, `meta_agent/AGENTS.md`, `Full-Development-Plan.md`, and old deleted docs still reference them.
- `DEVIATION_RECORD.md` is deleted from the working tree. Its git-history content remains useful as historical context but is no longer a live tracked worktree document.
- The current orchestrator builds seven subagents, not the old mix of eight orchestrator-level agents plus nested code-agent subagents described in `Full-Spec.md`. The configured subagents are `research-agent`, `spec-writer`, `plan-writer`, `code-agent`, `verification-agent`, `evaluation-agent`, and `document-renderer`.
- `test-agent` remains in some memory scaffolds and old docs, but it is not registered in `meta_agent/subagents/configs.py`.
- `evaluation-agent` is no longer merely reserved; it has a runtime module and is registered as a subagent.
- Plan-writer, code-agent, and evaluation-agent runtime modules exist, so Phase 4+ is at least partially implemented, despite older status text saying Phase 4 was not started.
- Formalized Stage Interface work is implemented for the first five stages via `BaseStage`, but there are no concrete `PLANNING`, `PLAN_REVIEW`, `EXECUTION`, `EVALUATION`, or `AUDIT` stage classes in `meta_agent/stages/`.
- Tool support is partial relative to the old five-eval-tool plan. `propose_evals` and `create_eval_dataset` exist; `run_eval_suite`, `get_eval_results`, and `compare_eval_runs` remain stubs that raise `NotImplementedError`.
- Artifact validation is now protocol-driven through `.agents/protocols/artifacts.yaml` and `ArtifactProtocolMiddleware`, with provenance checks in stage exit conditions.
- Model configuration has evolved into a typed control plane that supports both Anthropic and OpenAI provider policies, server-side Anthropic tool inventory, effort profiles, streaming defaults, and provider-specific validation.

---

## 4. Runtime Architecture

### 4.1 Entry Point

`langgraph.json` registers one graph:

```json
{
  "dependencies": ["."],
  "graphs": {
    "meta_agent": "meta_agent.server:get_agent"
  },
  "env": ".env"
}
```

`meta_agent.server.get_agent()` is the LangGraph dev-server factory. It:

- Loads `.env` if `python-dotenv` is available.
- Enables global LangChain debug output via `set_debug(True)`.
- Validates minimum package versions for `deepagents`, `langgraph-cli`, and `langchain-anthropic`.
- Builds `MetaAgentConfig.from_env()`.
- Calls `create_graph(config=config)`.

The graph returned by `create_graph(...)` is a compiled Deep Agents/LangGraph runnable created by `create_deep_agent(...)`.

### 4.2 Main PM Graph

`meta_agent.graph.create_graph(...)` constructs the PM/orchestrator graph with:

- Name: `meta-agent-pm`
- Model: resolved through `resolve_agent_model("orchestrator", model_spec=cfg.model_spec)`
- Tools: `LANGCHAIN_TOOLS`
- System prompt: `construct_pm_prompt(stage="INTAKE", project_dir=..., project_id=...)`
- Explicit middleware:
  1. `DynamicSystemPromptMiddleware`
  2. `MetaAgentStateMiddleware`
  3. `AskUserMiddleware`
  4. SDK `MemoryMiddleware`
  5. SDK `SkillsMiddleware`
  6. `ArtifactProtocolMiddleware`
  7. SDK summarization tool middleware from `create_summarization_tool_middleware(...)`
  8. `ToolErrorMiddleware`
- SDK-provided/default middleware behavior from `create_deep_agent(...)` for planning, filesystem, subagents, summarization, prompt caching, patch tool calls, and HITL via `interrupt_on`.
- Subagents from `build_pm_subagents(...)`.
- `MemorySaver` checkpointer and `InMemoryStore`.
- SDK-native CompositeBackend from `create_composite_backend(...)`.
- HITL gates for all names in `HITL_GATED_TOOLS`.

This graph is the canonical application runtime. Future architecture changes should preserve this single construction boundary unless there is a deliberate decision to replace Deep Agents as the harness.

### 4.3 Backend Contract

`meta_agent/backend.py` is the canonical persistence and filesystem contract.

The main agent backend is a factory returning SDK `CompositeBackend` with:

- Default route: `FilesystemBackend(root_dir=<repo_root>, virtual_mode=True)`
- `/memories/`: `StoreBackend(rt)` for cross-session store-backed memory files
- `/large_tool_results/`: `StateBackend(rt)` for thread-local large output offloading
- `/conversation_history/`: `StateBackend(rt)` for summarization/history offloading

`create_bare_filesystem_backend(...)` returns a non-virtual `FilesystemBackend` for middleware that must read absolute paths from disk, specifically `MemoryMiddleware`, `SkillsMiddleware`, and `ArtifactProtocolMiddleware`.

Current persistence is development-grade:

- Checkpointer: `MemorySaver`
- Store: `InMemoryStore`
- Production migration target: durable checkpointer and store, likely Postgres-backed for checkpointing and a durable LangGraph store for memory.

### 4.4 Runtime Dependency Policy

`pyproject.toml` requires:

- `deepagents>=0.4.3`
- `langchain>=1.0,<2.0`
- `langchain-core>=1.0,<2.0`
- `langgraph>=1.0,<2.0`
- `langgraph-sdk>=0.1.0`
- `langgraph-cli[inmem]>=0.4.12`
- `pydantic>=2.0`
- `langsmith`
- `langchain-community>=0.4.0,<0.5.0`
- `python-dotenv>=1.0.0`
- `langchain-anthropic>=1.3.0`
- `langchain-openai>=1.0,<2.0`

The server enforces selected minimum runtime versions at startup. This is a deliberate guardrail against SDK drift.

---

## 5. State Model

`meta_agent/state.py` defines `WorkflowStage`, transition validation, structured logs, and `MetaAgentState`.

### 5.1 Workflow Stages

The state enum contains:

- `INTAKE`
- `PRD_REVIEW`
- `RESEARCH`
- `SPEC_GENERATION`
- `SPEC_REVIEW`
- `PLANNING`
- `PLAN_REVIEW`
- `EXECUTION`
- `EVALUATION`
- `AUDIT`

`VALID_TRANSITIONS` includes the linear and rollback transitions through `EVALUATION`, while `AUDIT` is a lateral transition target from any stage and can return to any stage.

### 5.2 MetaAgentState

The current state schema includes:

- Conversation: `messages`
- Stage and project: `current_stage`, `project_id`
- Current artifact pointers: `current_prd_path`, `current_spec_path`, `current_plan_path`, `current_research_path`
- Collaboration flag: `active_participation_mode`
- Append-only logs: `decision_log`, `assumption_log`, `approval_history`, `artifacts_written`
- Execution tracking: `execution_plan_tasks`, `current_task_id`, `completed_task_ids`, `execution_summary`, `test_summary`, `progress_log`
- Eval tracking: `eval_suites`, `eval_results`, `current_eval_phase`
- Verification tracking: `verification_results`
- Stage-local metadata: `stage_metadata`

Reducers are used where accumulation matters:

- `operator.add` for lists such as messages, logs, completed task IDs, and progress.
- `operator.or_` for `stage_metadata`, allowing shallow merge of per-stage namespaces.

### 5.3 StageContext

`StageContext` provides a per-stage namespace:

```python
class StageContext(TypedDict):
    revision_count: int
    extra: dict
```

`BaseStage.sync_from_state(...)` hydrates `revision_count` from `state["stage_metadata"][STAGE_NAME]` and retains a temporary backward-compatibility fallback for the legacy `spec_generation_feedback_cycles` field.

---

## 6. Stage Interface

### 6.1 Formalized Stage Interface

The first five concrete stages inherit from `BaseStage`:

- `IntakeStage`
- `PrdReviewStage`
- `ResearchStage`
- `SpecGenerationStage`
- `SpecReviewStage`

`BaseStage` enforces:

- A concrete `STAGE_NAME` class attribute.
- A non-empty `project_dir`.
- Public `check_entry_conditions(...)` and `check_exit_conditions(...)` template methods.
- Subclass hooks `_check_entry_impl(...)` and `_check_exit_impl(...)`.
- Shared path resolution via `resolve_path(...)`.
- Shared revision tracking.
- Structured `ConditionResult` return shape.
- Best-effort LangSmith span emission when `LANGSMITH_TRACING=true`.
- Artifact provenance checks through `_artifact_is_proven(...)`.

This is a major implementation evolution beyond the original freeform phase description. New stages should inherit from `BaseStage` and use the same condition-check contract.

### 6.2 Implemented Stages

`INTAKE`:

- Entry is always allowed.
- Exit requires PRD and Tier 1 eval suite files plus explicit approvals recorded in `approval_history`.
- Current PRD path: `artifacts/intake/prd.md`.
- Current eval path: `evals/eval-suite-prd.json`.

`PRD_REVIEW`:

- Entry requires PRD and eval suite.
- Exit requires proven PRD and eval suite artifacts, artifact protocol validation when protocols are loaded, and separate approval of PRD and eval suite.

`RESEARCH`:

- Entry requires PRD and Tier 1 eval suite.
- For the `meta-agent` project, it prefers the research-agent PRD fixture at `artifacts/intake/research-agent-prd.md`.
- Exit requires proven decomposition, approved clusters, approved research bundle, research-agent memory file, at least one sub-finding markdown file, matching `current_research_path`, passing verification result for `research_bundle`, and required bundle sections.

`SPEC_GENERATION`:

- Entry requires PRD, research bundle, and Tier 1 eval suite.
- Exit requires proven technical spec and Tier 2 architecture eval suite, `current_spec_path`, passing verification for `technical_specification`, eval suite paths recorded in `state.eval_suites`, feedback loop below limit, and Tier 2 metadata with `artifact=eval-suite-architecture`, `tier=2`, and `created_by=spec-writer`.

`SPEC_REVIEW`:

- Entry requires technical spec and Tier 2 eval suite.
- Exit requires proven technical spec and architecture eval suite, plus separate approvals for the spec and architecture eval suite.

### 6.3 Declared But Not Implemented As Stage Classes

The workflow enum and prompts still describe:

- `PLANNING`
- `PLAN_REVIEW`
- `EXECUTION`
- `EVALUATION`
- `AUDIT`

But there are no corresponding `BaseStage` subclasses in `meta_agent/stages/`. Runtime subagents exist for plan writing, code, and evaluation; stage-gate classes for those later phases remain a gap.

---

## 7. Project and Memory Layout

### 7.1 Project Scaffolding

`meta_agent/project.py` owns project layout and identifies the registries that must remain synchronized.

For a project with `project_id=<id>`, current `init_project(...)` creates:

```text
<base_dir>/projects/<id>/
|-- meta.yaml
|-- artifacts/
|   |-- intake/
|   |-- research/
|   |-- spec/
|   |-- planning/
|   `-- audit/
|-- evals/
|-- logs/
`-- .agents/
    |-- pm/AGENTS.md
    |-- research-agent/AGENTS.md
    |-- spec-writer/AGENTS.md
    |-- plan-writer/AGENTS.md
    |-- code-agent/AGENTS.md
    |-- verification-agent/AGENTS.md
    `-- evaluation-agent/AGENTS.md
```

`document-renderer` is intentionally excluded from project-local memory because it uses repo-level memory only.

### 7.2 Memory Sources

`get_memory_sources(agent_name, project_dir, repo_root)` returns:

1. Project-specific memory: `{project_dir}/.agents/{agent_name}/AGENTS.md`
2. Global fallback memory: `{repo_root}/.agents/{agent_name}/AGENTS.md`

Those sources are loaded by SDK `MemoryMiddleware` with a bare filesystem backend.

### 7.3 Current Workspace Reality

The repository contains `.agents/pm/projects/meta-agent/` with:

- `meta.yaml`
- Project-local agent memory files
- `artifacts/intake/research-agent-prd.md`
- Research scratch/decomposition files
- `datasets/synthetic-research-agent.json`
- `evals/eval-suite-prd.json`
- Research eval report documents and markdown reports

The current tree also contains a global `.agents/research-agent/` directory, but no global `.agents/research-agent/AGENTS.md` was found during inspection. Some old docs still describe a global research-agent memory file as if present.

---

## 8. Registries

### 8.1 Agent Registry

`meta_agent/subagents/configs.py` defines `AGENT_REGISTRY`:

- `research-agent`
- `spec-writer`
- `plan-writer`
- `code-agent`
- `verification-agent`
- `evaluation-agent`
- `document-renderer`

`build_pm_subagents(...)` iterates this registry dynamically and returns SDK-compatible `SubAgent | CompiledSubAgent` entries for `create_deep_agent(subagents=...)`.

### 8.2 Provisioning Registry

`meta_agent/subagents/provisioner.py` defines `PROFILE_REGISTRY`. It controls each subagent's explicit middleware stack and whether the agent uses project memory, `SkillsMiddleware`, or the `create_deep_agent(skills=...)` argument.

The profile tokens are:

- `decision_state`
- `ask_user`
- `artifact_protocol`
- `summarization_tool`
- `memory`
- `skills`
- `tool_error`

Current profile highlights:

- `research-agent` and `plan-writer` use decision state, ask-user, artifact protocols, summarization tool, memory, skills, and tool error handling.
- `verification-agent` uses decision state, ask-user, artifact protocols, memory, skills, and tool error handling.
- `spec-writer` uses ask-user, artifact protocols, skills, memory, and tool error handling.
- `code-agent` and `evaluation-agent` use decision state, summarization tool, memory, skills, and tool error handling.
- `document-renderer` uses only memory and tool error middleware, no project memory, and Anthropic-only skill sources through the `skills` argument.

### 8.3 Tool Registry

`meta_agent/tools/registry.py` maps agent names to visible tools. It distinguishes SDK-provided filesystem tools from custom tools registered via `tools=[]`.

HITL-gated tool names are:

- `execute_command`
- `transition_stage`
- `request_eval_approval`
- `langsmith_dataset_create`
- `langsmith_eval_run`
- `create_eval_dataset`

### 8.4 Model Registry

`meta_agent/model_config.py` defines `AGENT_MODEL_REGISTRY`:

- `orchestrator`: effort `high`
- `research-agent`: effort `high`, Anthropic server-side `web_search_latest` and `web_fetch_latest`
- `spec-writer`: effort `high`
- `plan-writer`: effort `high`
- `code-agent`: effort `high`
- `verification-agent`: effort `high`
- `evaluation-agent`: effort `high`
- `document-renderer`: effort `low`

Default `META_AGENT_MODEL` is `anthropic:claude-opus-4-6`. Supported providers are `anthropic` and `openai`. Anthropic gets adaptive thinking by default through the feature inventory; OpenAI uses Responses API mode by default.

---

## 9. Subagent Catalog

### 9.1 Research Agent

Runtime file: `meta_agent/subagents/research_agent.py`

Responsibilities:

- Consume PRD and eval suite context.
- Build or normalize research decomposition.
- Track skill interactions, API citations, delegation context, and gap remediation context.
- Produce or normalize research artifacts including decomposition, clusters, bundle, sub-findings, and memory updates.
- Use web search/fetch server tools via model policy when Anthropic supports them.

Graph construction:

- Uses `create_deep_agent(...)`.
- Uses tools selected for research-agent from the registry.
- Uses `construct_research_agent_prompt(...)`.
- Uses provisioning profile `research-agent`.
- HITL gate: `request_approval`.
- Returns `CompiledSubAgent(name="research-agent", ...)`.

### 9.2 Spec Writer

Runtime file: `meta_agent/subagents/spec_writer_agent.py`

Responsibilities:

- Convert PRD, eval suite, and research bundle into a technical specification.
- Generate Tier 2 architecture eval coverage.
- Normalize outputs and update spec-writer memory.

Graph construction:

- Uses `create_deep_agent(...)`.
- Uses selected custom tools for spec-writer.
- Uses `construct_spec_writer_prompt(...)`.
- Uses provisioning profile `spec-writer`.
- Returns `CompiledSubAgent(name="spec-writer", ...)`.

### 9.3 Plan Writer

Runtime file: `meta_agent/subagents/plan_writer_runtime.py`

Responsibilities:

- Produce implementation plans from upstream artifacts.
- Use filesystem tools through Deep Agents middleware.
- Normalize plan output.

Graph construction:

- Uses `create_deep_agent(...)`.
- Passes `tools=[]`; filesystem tools are expected from middleware.
- Uses `construct_plan_writer_prompt(...)`.
- Uses provisioning profile `plan-writer`.
- Returns `CompiledSubAgent(name="plan-writer", ...)`.

### 9.4 Code Agent

Runtime file: `meta_agent/subagents/code_agent_runtime.py`

Responsibilities:

- Implement code changes according to plan/spec context.
- Use command execution and LangGraph/LangSmith helper tools under HITL.
- Normalize code-agent outputs.

Graph construction:

- Uses `create_deep_agent(...)`.
- Uses selected custom tools.
- Uses `construct_code_agent_prompt(...)`.
- Uses provisioning profile `code-agent`.
- HITL gate: `execute_command`.
- Returns `CompiledSubAgent(name="code-agent", ...)`.

The older spec described three nested code-agent subagents. The current runtime file does not expose a nested subagent registry in the inspected code; treat nested code-agent subagents as historical/future design unless reintroduced.

### 9.5 Verification Agent

Runtime files: `meta_agent/subagents/verification_agent_runtime.py`, `meta_agent/subagents/verification_agent.py`

Responsibilities:

- Read artifacts and verify them against upstream contracts.
- Normalize verdicts.
- Parse verification verdict text.

Graph construction:

- Uses `create_deep_agent(...)`.
- Passes `tools=[]`; read-oriented filesystem tools are expected from middleware.
- Uses `construct_verification_agent_prompt(...)`.
- Uses provisioning profile `verification-agent`.
- Returns `CompiledSubAgent(name="verification-agent", ...)`.

### 9.6 Evaluation Agent

Runtime file: `meta_agent/subagents/evaluation_agent_runtime.py`

Responsibilities:

- Work with LangSmith trace/dataset/eval tools.
- Propose evals and create eval datasets.
- Normalize evaluation-agent outputs.

Graph construction:

- Uses `create_deep_agent(...)`.
- Uses selected custom tools.
- Uses `construct_evaluation_agent_prompt(...)`.
- Uses provisioning profile `evaluation-agent`.
- Returns `CompiledSubAgent(name="evaluation-agent", ...)`.

This is an implemented runtime surface, not only a reserved future concept.

### 9.7 Document Renderer

Runtime file: `meta_agent/subagents/document_renderer.py`

Responsibilities:

- Convert or render documents according to `Document_Renderer_System_Prompt.md`.
- Operate with repo-level memory only.

Graph construction:

- Uses `create_deep_agent(...)`.
- Passes `tools=[]`; filesystem tools are auto-attached.
- Uses provisioning profile `document-renderer`.
- Returns `CompiledSubAgent(name="document-renderer", ...)`.

---

## 10. Tool Catalog

### 10.1 PM and Shared Runtime Tools

`meta_agent/tools/__init__.py` defines raw functions and `@tool` wrappers for:

- `transition_stage`
- `record_decision`
- `record_assumption`
- `request_approval`
- `request_eval_approval`
- `toggle_participation`
- `execute_command`
- `langgraph_dev_server`
- `langsmith_cli`
- `glob`
- `grep`
- `langsmith_trace_list`
- `langsmith_trace_get`
- `langsmith_dataset_create`
- `langsmith_eval_run`
- `propose_evals`
- `create_eval_dataset`

`LANGCHAIN_TOOLS` is the list passed to the PM `create_deep_agent(...)`.

### 10.2 Eval Tools

`meta_agent/tools/eval_tools.py` implements:

- `propose_evals(...)`: builds Tier 1 or Tier 2 eval-suite JSON content from requirement records.
- `validate_eval_suite(...)`: validates eval suite file shape.
- `create_eval_dataset(...)`: converts an eval suite into LangSmith-compatible dataset examples.

It stubs:

- `run_eval_suite(...)`
- `get_eval_results(...)`
- `compare_eval_runs(...)`

Those three raise `NotImplementedError` and should not be documented as operational in the current product.

### 10.3 Command Execution

`execute_command_tool(...)` triggers a LangGraph `interrupt(...)` with command, working directory, and timeout before running the shell command. This matches the design principle that shell execution is high-stakes and requires approval.

### 10.4 LangGraph and LangSmith Helpers

`langgraph_dev_server` validates the presence of `langgraph.json` and operates on the local dev server lifecycle. `langsmith_cli` and the LangSmith trace/dataset/eval helpers are present as custom tools. Some helpers are scaffolding-level and should be validated before being treated as production workflows.

---

## 11. Prompt Architecture

Prompt content is split between Python loaders/composers and Markdown source files.

PM prompt composition:

- Source files: `PM_System_Prompt.md`, `PM_Scoring_Strategy.md`, `PM_Eval_Approval_Protocol.md`, `PM_Delegation.md`
- Composer: `construct_pm_prompt(stage, project_dir, project_id, agents_md_content="")`
- Always includes base PM prompt, workspace section, memory section, and stage context.
- Adds eval approval protocol in `INTAKE`, `PRD_REVIEW`, and `SPEC_REVIEW`.
- Adds scoring strategy in `INTAKE` and `SPEC_REVIEW`.
- Adds delegation protocol in `RESEARCH`, `SPEC_GENERATION`, `PLANNING`, and `EXECUTION`.
- Appends runtime-injected memory last when available.

Subagent prompts follow the same pattern:

- `construct_research_agent_prompt(...)`
- `construct_spec_writer_prompt(...)`
- `construct_plan_writer_prompt(...)`
- `construct_code_agent_prompt(...)`
- `construct_verification_agent_prompt(...)`
- `construct_evaluation_agent_prompt(...)`

`DynamicSystemPromptMiddleware` is the runtime mechanism that recomposes the PM prompt based on `current_stage`. This is more robust than relying on a static startup prompt.

---

## 12. Artifact Protocols and Validation

`.agents/protocols/artifacts.yaml` defines structural protocols for:

- `prd`
- `technical-specification`
- `eval-suite`

`ArtifactProtocolMiddleware`:

- Loads the YAML protocols into private graph state as `artifact_protocols`.
- Provides a `validate_artifact` tool.
- Uses the same backend abstraction as Deep Agents filesystem tools.
- Validates content through `meta_agent.utils.artifact_validator`.

Stage validators combine artifact protocol validation with provenance checks. A file existing on disk is not enough for later-stage exit; it must also be recorded in `artifacts_written`, and some stages require explicit approval in `approval_history`.

---

## 13. Model and Provider Policy

`MetaAgentConfig` reads:

- `META_AGENT_MODEL`, default `anthropic:claude-opus-4-6`
- `LANGSMITH_TRACING`, default true
- `LANGSMITH_PROJECT`, default `meta-agent`
- `META_AGENT_MAX_REFLECTION_PASSES`, default `3`

Deprecated:

- `META_AGENT_MODEL_PROVIDER`
- `META_AGENT_MODEL_NAME`

The model resolver:

- Accepts provider-prefixed model specs: `provider:model_name`.
- Supports `anthropic` and `openai`.
- Maps internal effort values: `max`, `high`, `medium`, `low`.
- Defaults streaming and stream usage to true.
- Sets Anthropic adaptive thinking through the native feature registry unless overridden.
- Maps OpenAI reasoning effort appropriately depending on Responses API mode.
- Validates provider-specific fields rather than silently accepting incompatible request policy.
- Resolves server-side Anthropic tool policies for agents that request feature keys.

Anthropic native feature keys include:

- `adaptive_thinking`
- `web_search_latest`
- `web_fetch_latest`
- `code_execution_latest`
- `tool_search_latest`

The research-agent currently requests web search and web fetch.

---

## 14. Safety and Error Handling

### 14.1 Safety

`meta_agent/safety.py` defines:

- Recursion limits per agent, currently 1000 for each listed agent.
- Token budget warning thresholds, with research-agent at 1,000,000 and spec/verification at 200,000.
- Filesystem path validation helpers for path traversal, absolute path, and symlink checks.
- Command execution policy requiring HITL and a default 300 second timeout.
- Eval dataset immutability policy during `EXECUTION`, with HITL override.

Not every safety helper is necessarily wired into every runtime path. The canonical runtime safety surface is currently a mix of Deep Agents backend virtual mode, HITL-gated tools, and these helper policies.

### 14.2 Error Handling

`ToolErrorMiddleware` is the operational tool-error boundary. It converts tool exceptions into structured error messages that the LLM can reason about.

`meta_agent/errors.py` is explicitly marked as dead code in its module docstring. It remains a reference for the four-tier strategy but should not be treated as the live error-handling implementation.

---

## 15. Observability

`meta_agent/tracing.py` provides:

- `TRACE_TAGS`
- A best-effort `traceable(...)` wrapper around LangSmith's `traceable`
- `prepare_agent_state(...)`
- `delegation_decision(...)`

`create_graph(...)` calls `prepare_agent_state(...)` for the PM and each built subagent at graph creation time. `delegation_decision(...)` exists as a trace stub but is not shown as a runtime task-tool interception mechanism in the inspected code.

`BaseStage` emits condition-check spans when `LANGSMITH_TRACING` is true. It treats telemetry as non-critical and catches exceptions.

---

## 16. Evaluation Strategy

The implemented current-state evaluation surface is not the same as the old evaluation architecture.

Implemented in current tree:

- Eval suite JSON generator: `propose_evals`
- Eval suite file validation: `validate_eval_suite`
- Dataset conversion: `create_eval_dataset`
- Project-level research eval artifacts under `.agents/pm/projects/meta-agent/evals/`
- Research eval reports as `.docx` and `.md` artifacts

Absent from current tree:

- `meta_agent/evals/`
- `tests/evals/`
- Dataset fixtures under a root `datasets/` directory
- Eval runner module referenced by `Makefile`
- The three later eval tools: `run_eval_suite`, `get_eval_results`, `compare_eval_runs`

Therefore, the canonical claim should be:

The application contains eval-first prompts, eval-suite authoring helpers, and stored research eval artifacts, but the in-repo executable evaluation harness referenced by the old plan is not present in the current working tree. Reintroducing executable evals should start by deciding whether to restore the deleted `meta_agent/evals` package, migrate eval execution into `evaluation-agent`, or both.

---

## 17. Testing and Verification

The current `Makefile` references a rich pytest layout:

- `tests/contracts/`
- `tests/integration/`
- `tests/evals/`
- `tests/drift/`
- `tests/unit/`

Those directories are absent in the current working tree. `make test`, `make test-contracts`, `make test-integration`, `make test-evals`, `make test-drift`, `make test-all`, `make test-collect`, `make test-legacy`, and `make test-catalogs` therefore reference missing paths unless tests are restored.

The only practical verification target currently guaranteed by the inspected tree is `make lint`, which compiles selected runtime modules:

- `meta_agent/state.py`
- `meta_agent/configuration.py`
- `meta_agent/anthropic_api.py`
- `meta_agent/openai_api.py`
- `meta_agent/model_config.py`

The `.kiro/specs/formalized-stage-interface/` docs claim BaseStage migration tests were completed, but the corresponding `tests/` tree is not present now. Treat those Kiro docs as a completed design record whose test artifacts have been removed or are otherwise unavailable in the current worktree.

---

## 18. Local Development Workflow

Canonical setup:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
langgraph dev
```

The runtime expects `.env` with:

- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT=meta-agent`
- `ANTHROPIC_API_KEY`
- `META_AGENT_MODEL=anthropic:claude-opus-4-6`
- `META_AGENT_MAX_REFLECTION_PASSES=3`
- `LANGCHAIN_CALLBACKS_BACKGROUND=false`

`LANGCHAIN_CALLBACKS_BACKGROUND=false` is documented as required for complete experiment traces before process exit.

---

## 19. Current Implementation Gaps

The following gaps should be treated as current product/architecture gaps, not speculative nice-to-haves:

1. Later stage classes are missing. `PLANNING`, `PLAN_REVIEW`, `EXECUTION`, `EVALUATION`, and `AUDIT` exist in the enum and prompts but not as `BaseStage` subclasses.
2. Test and eval packages are missing from the working tree despite Makefile and docs references.
3. `meta_agent/evals` is absent, so old claims about in-repo eval runner modules are stale.
4. `run_eval_suite`, `get_eval_results`, and `compare_eval_runs` are stubs.
5. `test-agent` is referenced in older docs and some project memory scaffolds but not registered as an orchestrator subagent.
6. `DEVIATION_RECORD.md` is deleted from the working tree; if deviation tracking remains desired, this spec or a new architecture decision record should replace it.
7. Runtime observability has graph-creation provisioning spans and stage condition spans, but no confirmed task-tool interception for delegation decisions.
8. Safety helpers are not uniformly proven to be enforced across all runtime execution paths.
9. The project has both old status claims and current runtime modules for Phase 4+ roles. The new canonical status should be module-by-module rather than phase-only.
10. Some docs contain mojibake character sequences, indicating encoding drift in historical plan content.

---

## 20. Canonical Architecture Decisions

### ADR-001: Deep Agents Remains the Harness Boundary

Decision: Keep `create_deep_agent(...)` as the core runtime abstraction for the PM graph and subagent runtimes.

Rationale: The current implementation is built around Deep Agents middleware, backends, skills, memory, subagents, and tool conventions. Replacing it with raw LangGraph would duplicate SDK capabilities and invalidate existing provisioning logic.

### ADR-002: Registry Synchronization Is a First-Class Contract

Decision: Any agent addition/removal must update:

- `PROJECT_AGENTS`
- `PROFILE_REGISTRY`
- `AGENT_MODEL_REGISTRY`
- `TOOL_REGISTRY`
- `AGENT_REGISTRY`
- Runtime factory in `meta_agent/subagents/`

Rationale: Current behavior is distributed by design. Drift between registries is more likely than failure inside a single module.

### ADR-003: Bare Filesystem Backend Is Required for Memory, Skills, and Protocols

Decision: Continue to use non-virtual filesystem backend for middleware that loads absolute paths.

Rationale: Virtual-mode backends are correct for agent-facing workspace I/O but wrong for absolute skill and memory source loading.

### ADR-004: Current State Beats Phase Narrative

Decision: Future docs should report implementation by module and runtime surface, not only by phase number.

Rationale: Plan-writer, code-agent, and evaluation-agent runtime files exist even though older docs frame Phase 4/5 as not started. Phase-only status now hides reality.

### ADR-005: Tests and Evals Must Be Reconciled Before Claims of Passing Gates

Decision: No future spec should claim "471 unit tests pass" or similar unless the test tree and command are present and rerun in the current worktree.

Rationale: The current working tree lacks the referenced tests.

---

## 21. File Reference Map

Runtime:

- `meta_agent/server.py`: LangGraph graph factory and dependency validation
- `meta_agent/graph.py`: PM graph construction
- `meta_agent/backend.py`: SDK backend factories
- `meta_agent/configuration.py`: environment-backed configuration
- `meta_agent/model_config.py`: model/provider control plane

State and stages:

- `meta_agent/state.py`: workflow enum, transitions, state schema, structured logs
- `meta_agent/stages/base.py`: formalized stage interface
- `meta_agent/stages/intake.py`: INTAKE validator/helpers
- `meta_agent/stages/prd_review.py`: PRD_REVIEW validator/helpers
- `meta_agent/stages/research.py`: RESEARCH validator
- `meta_agent/stages/spec_generation.py`: SPEC_GENERATION validator
- `meta_agent/stages/spec_review.py`: SPEC_REVIEW validator

Subagents:

- `meta_agent/subagents/configs.py`: subagent registry and lazy factories
- `meta_agent/subagents/provisioner.py`: middleware provisioning profiles
- `meta_agent/subagents/research_agent.py`: research runtime
- `meta_agent/subagents/spec_writer_agent.py`: spec-writer runtime
- `meta_agent/subagents/plan_writer_runtime.py`: plan-writer runtime
- `meta_agent/subagents/code_agent_runtime.py`: code-agent runtime
- `meta_agent/subagents/evaluation_agent_runtime.py`: evaluation-agent runtime
- `meta_agent/subagents/verification_agent_runtime.py`: verification-agent runtime
- `meta_agent/subagents/document_renderer.py`: document-renderer runtime

Tools and middleware:

- `meta_agent/tools/__init__.py`: raw and `@tool` implementations
- `meta_agent/tools/registry.py`: tool registry and HITL gates
- `meta_agent/tools/eval_tools.py`: eval authoring/dataset helpers and stubs
- `meta_agent/middleware/dynamic_system_prompt.py`: stage-aware prompt recomposition
- `meta_agent/middleware/meta_state.py`: MetaAgent state middleware
- `meta_agent/middleware/ask_user.py`: structured user-question interrupt tool
- `meta_agent/middleware/artifact_protocol.py`: artifact protocol loader and validator tool
- `meta_agent/middleware/agent_decision_state.py`: subagent decision state schema/middleware
- `meta_agent/middleware/tool_error_handler.py`: tool error middleware

Prompts and artifacts:

- `meta_agent/prompts/pm.py`: PM prompt composer
- `meta_agent/prompts/sections.py`: stage/workspace/memory prompt sections
- `meta_agent/prompts/*.md`: Markdown prompt sources
- `.agents/protocols/artifacts.yaml`: artifact validation protocols
- `.agents/pm/projects/meta-agent/`: current project artifacts, eval reports, and memory

Historical docs:

- `Full-Spec.md`: historical full spec
- `Full-Development-Plan.md`: historical/current mixed development plan
- `Readme.md`: high-level product narrative
- `.kiro/specs/formalized-stage-interface/`: BaseStage feature design record

---

## 22. Recommended Next Documentation Actions

1. Treat this document as the replacement baseline for architecture discussion.
2. Decide whether to restore or permanently retire `DEVIATION_RECORD.md`.
3. Update or replace `Full-Development-Plan.md` so it stops claiming absent test/eval packages as current.
4. Add a small architecture status table that tracks runtime surfaces by module: PM graph, first-five stages, later stages, each subagent, eval tools, tests, and eval harness.
5. If executable tests are still intended, restore `tests/` and `meta_agent/evals/` or delete Makefile targets that point to them.
6. Add canonical stage specs for `PLANNING`, `PLAN_REVIEW`, `EXECUTION`, `EVALUATION`, and `AUDIT` before implementing more phase-gate behavior.
7. Add parity checks for the five registries so future agent additions cannot silently drift.
# Canonical Technical Specification

## Local-First Meta-Agent for Building AI Agents

**Version:** 1.0.0 — As-Built  
**Date:** April 2026  
**Prepared for:** Jason M.  
**Status:** Authoritative — reflects the system as it exists today

---

> **About this document.** `Full-Spec.md` was the original design blueprint (v5.6.0-R / v5.6.1). Implementation diverged significantly during Phases 3 and 4. This document is the canonical reference for the system *as built*. It supersedes `Full-Spec.md` as the source of truth for architecture, state, middleware, tooling, and subagent topology. Where the original spec was aspirational, this document is descriptive.

---

## Table of Contents

1. Executive Summary
2. Architecture Overview
3. Layered Stack
4. Middleware Architecture
5. State Model
6. Persistence and Backend Design
7. Workflow Stages and State Machine
8. Stage Validators (Formalized Stage Interface)
9. Subagent Topology
10. Subagent Provisioning
11. Tool Inventory
12. Prompt Architecture
13. Model Control Plane
14. Artifact System
15. Eval Infrastructure
16. HITL (Human-in-the-Loop) Design
17. Observability and Tracing
18. Safety and Guardrails
19. Project Isolation
20. Configuration and Environment
21. Server and Graph Entry Point
22. Implementation File Reference
23. Known Gaps and Deferred Work
