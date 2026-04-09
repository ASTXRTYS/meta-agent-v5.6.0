# Long Horizon Meta Harness

![Harness Diagram](Harness-Diagram.png)

## Overview

The Long Horizon Meta Harness is a multi-agent system that takes a product idea from initial concept through to a fully built, tested, and evaluated AI application. It orchestrates a pipeline of specialized agents — from requirements gathering through research, architecture, planning, implementation, and evaluation — with a built-in optimizer-evaluator feedback loop that enforces scientific rigor throughout development.

The system is built on the Deep Agents SDK and coordinated through LangGraph. Each agent in the pipeline produces artifacts that flow downstream, with evaluation gates ensuring quality at every stage transition.

## Guiding Principle

**"PM Scopes Criteria, Harness Engineer Owns the Science"**

- The **PM** is a business-oriented project manager with exceptional organizational skills. It translates stakeholder vision into clear requirements and evaluation criteria — defining WHAT success looks like.
- The **Harness Engineer** is the PM's brightest technical coworker — the scientific authority on evaluation. It owns HOW to evaluate: scoring rubrics, LLM judge assembly, calibration methodology, and harness topology.
- The PM defines WHAT to evaluate (aligned with stakeholder vision).
- The Harness Engineer owns HOW to evaluate (scoring, judges, calibration, harness topology).

When the PM finishes shaping evaluation criteria and business-logic datasets with the stakeholder, it recognizes: *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."* This self-awareness — knowing where its expertise ends and the Harness Engineer's begins — is a core design constraint.

## Diagram Legend

- **Black arrows**: Show the flow of artifacts through the application.
- **Red text**: Names the artifacts passed along the black arrows.
- **Thin Golden arrows**: Show where two agents may loop with one another to refine their work. For example, the Researcher and Architect looping when the Architect determines further research is needed to uncover new possibilities, potential tools, or APIs that could inform the full architecture.

---

## Agent Roster

### Project Manager (PM)

- **Role**: Business-oriented orchestrator and requirements owner
- **Responsibilities**: Requirements elicitation, PRD authoring, evaluation criteria scoping, stakeholder alignment, pipeline coordination, organizing where evaluation artifacts are stored
- **Skills**: `prompt-architect`, `langsmith-dataset`
- **Hands off to**: Research Agent, Architect, Harness Engineer
- **Key behavior**: After shaping eval criteria and business-logic datasets with the stakeholder, recognizes "now it's time to bring in the expert" and invokes the Harness Engineer with a structured handoff containing: (1) full product vision and stakeholder requirements, (2) proposed evaluation criteria, (3) business-logic synthetic datasets, and (4) where evaluation artifacts should be organized

### Research Agent

- **Role**: Deep ecosystem researcher
- **Responsibilities**: Multi-pass web research, evidence synthesis, SDK/API discovery, decision-space mapping
- **Skills**: `web_search`, `web_fetch` (server-side tools)
- **Hands off to**: Architect (research bundle)
- **Key behavior**: May loop with the Architect when further research is needed to uncover tools, APIs, or architectural possibilities that inform the technical specification

### Architect (formerly Spec Writer)

- **Role**: System architect and technical specification author
- **Responsibilities**: Translates PRD + research bundle into implementation-ready technical specifications with architecture decisions, prompt designs, and component definitions
- **Skills**: Filesystem tools
- **Hands off to**: Plan Writer (technical specification)
- **Key behavior**: May loop with Research Agent for additional discovery. Introduces new components (tools, middleware, prompts) that did not exist at PRD time — triggering Harness Engineer Stage 2 intervention to create evaluation coverage for those components

### Plan Writer

- **Role**: Implementation strategist
- **Responsibilities**: Transforms spec + eval suites into phased implementation plans with clear break points where development stops and experiments run
- **Skills**: Filesystem tools, Document Renderer sub-agent
- **Hands off to**: Code Agent (development plan) AND Harness Engineer (for Stage 3 intervention)
- **Key behavior**: Plan marks eval/experiment break points but does NOT include evaluation criteria — only the stopping points. The plan says *when* to evaluate, never *what* or *how*.

### Code Agent (The Optimizer)

- **Role**: Hill-climbing implementation engineer
- **Two tracks**:
  1. **Harness Engineering**: Building Deep Agent applications with correct SDK conventions
  2. **Frontend/UI**: Building chatbots, TUIs, web UIs, desktop apps
- **Skills**: `deep-agents-core`, `deep-agents-orchestration`, `deep-agents-memory`, `langsmith-trace`
- **Tools**: `execute_command` (HITL-gated), `langgraph_dev_server`, `langsmith_cli`
- **Key behavior**: Works phase-by-phase against the development plan. Receives EBDR-1 feedback from the Harness Engineer and iterates. **Completely blind to evaluation artifacts** — only sees EBDR-1 feedback packets and can inspect its own traces in LangSmith.

### Harness Engineer (Evaluation Agent)

- **Role**: Scientific iterator, LLM judge authority, phase-gate enforcer
- **Responsibilities**: Builds, calibrates, and operates the full evaluation harness across three intervention stages and the development loop (detailed below)
- **Skills**:
  - `langsmith-evaluator-feedback` (EBDR-1) — translates eval results into optimizer-safe feedback without leaking scoring logic
  - `langsmith-evaluator` — building evaluators, run functions, execution wiring
  - `langsmith-dataset` — creating and managing evaluation datasets
  - `langsmith-trace` — querying traces for analysis
  - `prompt-architect` — for writing judge prompts (judge assembly IS prompt engineering)
  - **TODO: `llm-judge-assembly`** — procedural knowledge for building judges: model selection, prompt writing, scoring schemas, judge strategy (how many judges, which evals need dedicated judges, when a single eval within a category warrants its own judge)
  - **TODO: `llm-judge-calibration`** — procedural knowledge for validating judges: calibration datasets, agreement metrics, drift detection, prompt iteration until reliable
- **Key behavior**: Has FULL knowledge of all evaluation artifacts. Creates a parallel eval plan alongside the development plan. Produces EBDR-1 feedback that gives the optimizer directional signal without exposing scoring logic, rubrics, or judge configurations.

### Verification Agent

- **Role**: Artifact quality gate
- **Responsibilities**: Cross-checks artifacts against specs, PRDs, and standards before they flow downstream
- **Skills**: Filesystem tools (read-only)

### Document Renderer

- **Role**: Format conversion utility
- **Responsibilities**: Converts Markdown artifacts to DOCX/PDF
- **Available to**: PM, Research Agent, Plan Writer

---

## Memory & Instruction Architecture (AGENTS.md)

The system uses a tiered memory architecture powered by `MemoryMiddleware` to ensure agents stay aligned with their identity and project goals without manual filesystem overhead.

### The Tier System
Instructions are automatically resolved across three levels of `AGENTS.md` files:

1.  **Level 1: Global/Library** (`/.agents/AGENTS.md`) - Core system instructions and shared SDK patterns.
2.  **Level 2: Agent-Specific** (`/.agents/{agent_name}/AGENTS.md`) - Specialized identity and behavioral protocols for that specific sub-agent.
3.  **Level 3: Project-Specific** (`{project_dir}/.agents/AGENTS.md`) - Context unique to the current active project.

### Configuration Convention
- **Middleware Loading**: All instructions are injected via `MemoryMiddleware`. This prevents instruction loss during context compaction (summarization).
- **No Manual Checks**: Runtimes never perform manual `os.path` checks. `MemoryMiddleware` handles missing files gracefully, allowing for a mix of defaults and overrides.
- **Directory Personas**: New sub-agent personas are created by adding a directory under `/.agents/` with its own `AGENTS.md`.

## Filesystem Backend Convention (Current)

The runtime filesystem contract is centralized in `meta_agent/backend.py` and must remain stable:

- **Default route**: `FilesystemBackend(root_dir=<repo_root>, virtual_mode=True)` for normal workspace files.
- **Persistent memory namespace**: `/memories/` routes to `StoreBackend` (cross-thread persistence).
- **Ephemeral large output namespace**: `/large_tool_results/` routes to `StateBackend` (thread-local temporary files).
- **Ephemeral history namespace**: `/conversation_history/` routes to `StateBackend` (thread-local compaction/history offloading).
- **Memory/skills file loading**: `MemoryMiddleware` and `SkillsMiddleware` use a separate bare filesystem backend (`virtual_mode=False`) for absolute-path source reads.

### Expected Project Workspace Layout

For project `project_id=<id>`, files are expected under:

- On disk: `<repo_root>/.agents/pm/projects/<id>/...`
- Agent-facing workspace path shape: `/.agents/pm/projects/<id>/...`

```text
/.agents/pm/projects/<id>/
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

### Enabled User Stories (Filesystem + Memory + Artifact Organization)

1. As a runtime user, I can trust a deterministic workspace layout so every stage knows exactly where to read and write artifacts.
2. As a subagent maintainer, I can change middleware/file-loading behavior once in the provisioner and avoid runtime-by-runtime drift.
3. As a project owner, I can rely on consistent project memory precedence (project-local first, repo fallback second) across all project-scoped agents.
4. As a release owner, I can preserve document-renderer isolation (repo-level memory only) without leaking project-scoped memory into render jobs.
5. As a contributor adding a new project-scoped agent, I get immediate failures if scaffolding, memory provisioning, and runtime registration diverge.
6. As a quality gate reviewer, I can require parity/drift test evidence before approving backend, memory, or artifact-path convention changes.

### Convention Guardrails (Anti-Regression)

- `tests/drift/test_filesystem_backend_convention.py` enforces backend route mapping and required workspace scaffolding.
- `tests/drift/test_subagent_provisioning_convention.py` enforces centralized middleware provisioning and project-agent alignment.
- `tests/integration/test_subagent_provisioner_parity.py` enforces legacy-equivalent middleware order/config plus document-renderer special behavior.
- `tests/integration/test_memory_and_skills.py` enforces scaffolding + memory-load behavior and skills directory assumptions.

---

## Information Isolation Protocol

This is architecturally critical. The optimizer-evaluator feedback loop only works if information asymmetry is maintained. The optimizer must remain blind to evaluation artifacts to prevent reward hacking and overfitting.

| Artifact | PM | Harness Engineer | Optimizer | Architect | Plan Writer |
|---|---|---|---|---|---|
| PRD + requirements | ✅ | ✅ | ✅ | ✅ | ✅ |
| Evaluation criteria | ✅ | ✅ | ❌ | ❌ | ❌ |
| Scoring rubrics | ❌ | ✅ | ❌ | ❌ | ❌ |
| LLM judge configs | ❌ | ✅ | ❌ | ❌ | ❌ |
| Synthetic eval datasets | ✅ (proposes) | ✅ (owns) | ❌ | ❌ | ❌ |
| Development plan | ✅ | ✅ | ✅ | ✅ | ✅ |
| Eval break points in plan | ✅ | ✅ | ✅ (sees breaks, not criteria) | ✅ | ✅ |
| EBDR-1 feedback packets | ❌ | ✅ (produces) | ✅ (consumes) | ❌ | ❌ |
| Raw traces (LangSmith) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Unit tests | ✅ | ✅ | ✅ | ✅ | ✅ |

The PM decides where evaluation artifacts are stored. The Harness Engineer has full knowledge of those locations. The optimizer must be **completely blind** to all evaluation artifacts — eval suites, scoring rubrics, synthetic datasets, and LLM judge configs cannot be visible to it. Unit tests are fine for the optimizer to see; it is evals, experiments, and the evaluation harness that must be hidden.

---

## Harness Engineer Intervention Points

### Stage 1: Product Requirement Documents

At Stage 1, the Harness Engineer refines the PM's evaluation criteria into a complete evaluation harness before the PRD can be finalized.

**Key responsibilities:**
- Refine and validate the PM's proposed evaluation criteria
- Determine evaluation types: binary, binary score, Likert score, evaluation categories
- Define judge strategy: how many judges, which evals need dedicated judges, separation of concerns across eval categories
- For each judge: select the model, write the prompt, configure the scoring schema
- Create the full synthetic dataset (building on the PM's initial golden path and failure mode examples)
- Calibrate each judge against synthetic data before development begins
- **Gate**: The PRD cannot be finalized until the eval harness is complete and all judges are calibrated

### Stage 2: Full Specification Artifact

At Stage 2, the Harness Engineer creates evaluation coverage for new components introduced by the Architect that did not exist when the PRD was written.

**Key responsibilities:**
- Create evaluation suites for new components including (but not limited to):
  - System prompts
  - Tools
  - Programmatic behaviors (middleware, etc.)
- Ensure the optimizer can effectively hill-climb against these new components during development
- **Gate**: The specification cannot flow to the Plan Writer until evaluation coverage exists for all architect-introduced components

### Stage 3: Development Plan and Roadmap

At Stage 3, the Harness Engineer dictates where evaluation gates belong in the development plan and creates its own parallel eval plan.

**Key responsibilities:**
- Dictate where evaluation harnesses and experiments should be placed in the development plan
- Set phase-gate criteria that must be met before progressing
- Create the parallel eval plan: which evals run after which development phases, which harnesses to invoke
- The development plan marks the break points; the eval plan (visible only to PM and Harness Engineer) specifies what runs at each break

---

## The Pipeline: Closing the PRD

1. PM gathers stakeholder requirements → proposes evaluation criteria + initial synthetic examples
2. PM determines: *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."*
3. PM invokes Harness Engineer with structured handoff (vision + criteria + examples)
4. Harness Engineer determines: eval types, categories, judge strategy, harness topology
5. For each judge: model selection, prompt, scoring schema
6. Harness Engineer creates full synthetic dataset (building on PM's initial examples)
7. Harness Engineer calibrates each judge against synthetic data
8. Harness Engineer returns finalized evaluation harness to PM
9. PM organizes and stores eval artifacts in an isolated location — only PM and Harness Engineer know where
10. PM reviews and approves → PRD is complete
11. PRD flows to Architect → Plan Writer (plan marks eval break points but NOT eval criteria)
12. Harness Engineer creates its own parallel eval plan: which evals run after which development phases
13. During development: Optimizer works against plan, Harness Engineer runs evals at gates, produces EBDR-1 feedback
14. Optimizer is BLIND to eval artifacts — only receives EBDR-1 feedback packets + can inspect its own traces

---

## The Development Loop (Meta-Harness)

### Pre-Phase Contract

Before beginning any phase, the Optimizer and Harness Engineer may negotiate:
- What "done" looks like for this phase
- What must be achieved before entering the phase
- Agreement on completion criteria

The full development plan and roadmap are available to both the Optimizer and the Harness Engineer at all times.

### The Optimization Cycle

1. Optimizer implements the current phase
2. Harness Engineer runs evaluation harness at the phase gate
3. Harness Engineer produces EBDR-1 feedback packet (directional signal, no scoring logic leaked)
4. Optimizer inspects routed traces in LangSmith, performs its own causal reasoning
5. Optimizer iterates on the implementation
6. Loop continues until phase gate criteria are met
7. Advance to next phase

The loop continues iterating for each phase throughout the full development plan until the application is fully built and both the Optimizer and Harness Engineer agree completion is achieved.

### Two Testing Paradigms

1. **Scientific (LLM Harness)**: Eval-driven development with judge calibration, metric vectors, and EBDR-1 feedback. Used for behavioral validation of AI components — system prompts, tool usage, agent delegation patterns, output quality.
2. **Practical (Frontend/UI)**: Playwright-based QA — navigate, click, screenshot, record proof, report to user. Used for frontend functionality, UI correctness, and user-facing flows. Follows Anthropic's "Harness Design for Long-Running Apps" pattern.

---

## Skills Inventory

### Existing Skills

| Skill | Used By | What It Enables |
|---|---|---|
| `langsmith-evaluator-feedback` (EBDR-1) | Harness Engineer | Translates eval results into optimizer-safe feedback without leaking scoring logic |
| `langsmith-dataset` | Harness Engineer | Create, upload, and manage evaluation datasets via LangSmith CLI |
| `langsmith-evaluator` | Harness Engineer | Build evaluators, run functions, execution wiring |
| `langsmith-trace` | Harness Engineer, Code Agent | Query and analyze LangSmith traces |
| `prompt-architect` | PM, Harness Engineer | System prompt design methodology (also used for judge prompt writing) |
| `deep-agents-core` | Code Agent | Deep Agent SDK patterns, `create_deep_agent()` API |
| `deep-agents-orchestration` | Code Agent | SubAgent delegation, task planning, HITL patterns |
| `deep-agents-memory` | Code Agent | Backend configuration, memory middleware, persistence |
| `remember` | All agents (future) | Reflect on tasks, persist procedural knowledge, graduate to skills |

### TODO — Skills That Need To Be Created

| Skill | For | What It Will Enable | Research Status |
|---|---|---|---|
| `llm-judge-assembly` | Harness Engineer | Model selection, judge prompt writing, scoring schema config, judge strategy (how many judges, when a single eval warrants its own judge) | ❌ Needs targeted research — papers, SME input |
| `llm-judge-calibration` | Harness Engineer | Calibration datasets, agreement metrics, drift detection, prompt iteration until reliable | ❌ Needs targeted research |

**Key insight — Judge Assembly ≈ Prompt Engineering + Strategy**: Assembling a judge is fundamentally prompt engineering — writing the prompt that tells the judge what criteria to evaluate and how to score. But it is also strategy: given 5 eval categories, does each need its own judge? Within a category, does a particularly complex criterion warrant a dedicated judge? What model is best suited for each role? The Harness Engineer must make these judgment calls for the entire eval suite.

**Key insight — Judge Calibration ≈ Prompt Iteration + Validation**: Calibrating a judge is largely iterating on the judge prompt against synthetic datasets until scoring is reliable. But it also involves measuring inter-rater agreement, detecting scoring drift, and validating that the judge actually measures what it claims to.

### Open Research Questions

1. **Harness topology**: When to use single vs multiple evaluation harnesses. At what point does the Harness Engineer make this determination, and what procedural knowledge does it need?
2. **Judge strategy**: How to determine judge count — judge-per-eval vs judge-per-category, and when individual evals within a category warrant dedicated judges
3. **Calibration methodology**: Beyond prompt iteration — agreement metrics, drift detection, validation that judges measure what they claim
4. **Assembly best practices**: Model selection criteria, prompt patterns for different judge types

These questions require the same research approach used for the EBDR-1 skill: targeted paper review, SME input, and synthesis through a reasoning model.

---

## Final Delivery

Once development is complete:
1. A final demo is produced showing all user stories and expectations from the PRD are met
2. The full application and demo are presented to the PM
3. The PM confirms project completion
4. Stakeholders (humans) are brought back into play
