# Meta Harness Agent Conventions

This directory is the v1 workspace for Meta Harness. Treat the existing
`meta_agent/` application as the v0.5 reference implementation: keep the parts
that are valuable, but do not inherit its naming, registry, or plumbing shape by
default.

## Highest-Level Decisions

- Meta Harness will adopt the Deep Agents harness from langchain as its primary
  agent runtime/framework.
- Deep Agents is an excellent default harness layer for open-ended, multi-step
  agent work which can be perfectly tuned for a task by carefully crafted system
  prompts, task-specific tools, skills, and an opinionated file system for
  memory.
- From day one, we need to ship our LLM application to allow our agents to have their own virtual machine and their own virtual file system. With that being said, we need to also ship the capability to use our LLM application as a local-first system where the file system for memory and artifact persistence can be stored on the user's disk if the user so desires. There must be dual modality, local-first, and also the ability for the agent to spin up its own virtual machine and entirely run inside of a sandbox.
- For the deep agents abstraction, Langchain ships the majority of all needed logic to develop an agent harness or an LLM application. We must always leverage what the deep agents SDK provides and embrace middleware as an extension of the deep agent's harness abilities.
- A rewrite is allowed to be incremental. New v1 code should be clean enough
  that old v0.5 code can be ported over one behavior at a time.
- We will ship with our main agent, which is going to be the direct interface that most users will interact with. Other agents will be part of this LLM application, and it is to be decided whether they should be sub-agents or have the same or be their own standalone agent. The researcher, who is in charge of researching, should itself be fully stateful and capable of managing its own set of sub-agents, so the researcher must be its own deep agent as well. We will ship with an architect who, as I mentioned for the researcher, must be stateful, have its own memory, and be its own create deep agent that has access to all the benefits of the deep agent harness. The same applies for all of the agents that I will mention here:
- The planner, our planner agent
- our developer agent who serves as our coding agent, essentially our generator
- our harness engineer agent
- and our evaluator agent  All of these agents together serve as an LLM application for developing, observing, and shipping other LLM applications. The decision that I am wrestling with is: should we have the project manager as its own agent and all these other agents serve as sub-agents, or should each agent serve as its own deep agent separately without needing to be a sub-agent? In my articulation, I realize I must clarify that, when I say, "should these agents be sub-agents of the PM in a world where they do end up being the sub-agents of the PM," they must also be deep agents, even if they are sub-agents. The only thing that I am attempting to articulate is: should they be compiled as sub-agents, or should they be their own deep agent? This is the decision matrix that I am wrestling with.
  
    ## HIGH-LEVEL REQUIREMENTS (NOT YET RESOLVED)
### **"PM Scopes Criteria, Harness Engineer Owns the Science"**

---

### **Core Agent Roles**

#### **Project Manager (PM)**
- **Responsibility**: Business-oriented project manager with exceptional organizational skills
- **Function**: Translates stakeholder vision into clear requirements and evaluation criteria — defining **WHAT** success looks like
- **Key Capability**: Context building and project scope dissemination

#### **Harness Engineer**
- **Responsibility**: PM's brightest technical coworker — the scientific authority on evaluation
- **Function**: Owns **HOW** to evaluate: scoring rubrics, LLM judge assembly, calibration methodology,runs experiments, designs eval harnesses, serves as full agent harness engineer and harness topology

---

### **Critical Design Constraint: PM Self-Awareness**
When the PM finishes shaping evaluation criteria and business-logic datasets with stakeholders, it must recognize:

> *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."*

This self-awareness — knowing where its expertise ends and the Harness Engineer's begins — is a core design constraint.

---

### **Communication Architecture**

#### **PM Context Broadcasting Mechanism**
The PM should be able to send a "burst of information" to all relevant agents (researcher, architect, harness engineer) when project scope is clear.

**Implementation Option**: Shared `@AGENTS.md` file per project that serves as:
- A communication board accessible to all agents
- PM's mechanism for publishing high-signal project information
- Context engineering foundation in the agent memory filesystem

---

### **Workflow Handoffs & Loops**

#### **Phase 1: PM → Harness Engineer Handoff**
1. **PM recognizes completion** of stakeholder discussions and PRD finalization
2. **PM communicates** to Harness Engineer:
   - Final PRD
   - Evaluation criteria
   - Rough draft datasets from stakeholder
3. **Harness Engineer responsibilities**:
   - Finalize datasets and evaluation criteria
   - Create scoring rubrics
   - Generate held-out datasets for LLM judge calibration and final phase experiments against target harness and target application
   - Create evaluation criteria and datasets for researcher consumption

#### **Feedback Loop Capability**
- Harness Engineer may have questions for PM → PM asks high-signal questions to stakeholder
- Harness Engineer can use `ask_user` middleware tool for targeted stakeholder questions
- Loop must be optional but available
- Deep Agent's CLI shows an example of this `ask_user` middleware and tool.

#### **Phase 2: Researcher ↔ Architect Collaboration**
- **Architect's role**: NOT to research, but to design based on research bundle and PRD
- **Researcher's role**: Identify SDKs, APIs, abstractions to satisfy PRD requirements (langchain abstraction biased due to the robustness and elegance of the full Langchain ecosystem (i.e., Langchain, Langgraph, and Deep Agents).

**Research Focus Areas**:
- LangChain ecosystem (LangGraph, Deep Agents)
- Model capabilities (Anthropic, OpenAI documentation)
- LLM application APIs (Fire, Crawl, LlamaIndex, etc.)
- Subject Matter Expert identification (curated SMEs provided in system prompt)

**Architect-Researcher Loop**:
- Architect identifies knowledge gaps ("I need more info on X SDK/API, I need to know more about this model's capabilities and the correct way to use these model-specific APIs.")
- Requests targeted research from Researcher
- Waits for Researcher completion before proceeding with final design

**Architect's Design Deliverables**:
- Full application design and specification
- Complete tool schemas
- System prompts and tool messages
- Zero-ambiguity architecture documentation
- Has full rein on designing his own designs. Is fully versed in an elegant approach to creating LLM applications. Is ambitious and confident enough to create novel designs that don't currently exist and has a full inventory of existing repos so that it can see how other production agents handle semantically similar situations that the architect may be facing when building his own target harness or application.
- Context for downstream planner agent

#### **Phase 3: Architect → Planner Handoff**
1. **Architect completes** full design specification (may be multiple documents):
   - Requirements document
   - Design document  
   - Task list with phases
2. **Harness Engineer re-engagement** before planner receives work:
   - May have questions for the architect when creating eval harness, evaluation logic, data sets, etc.
   - Evaluates new tools/system prompts introduced by architect
   - Creates evaluation criteria for target harness components
   - Designs evaluation harness for development phase
   - Manages dataset strategy (public vs held-out)
   - Establishes LangSmith upload strategy for visibility

**Data Management Principle**: All agent artifacts and memory must exist in the filesystem (virtual or disk-based)

#### **Phase 4: Planner → Developer Handoff**
- **Planner receives**: Full design, spec, public eval criteria, public datasets
- **Planner creates**: End-to-end development plan with structured phases
- **Note**: Held-out datasets remain exclusively with Harness Engineer for final testing

#### **Phase 5: Development & Evaluation Loop**
- **Developer role**: Execute plan using spec as reference, orchestrate subagents, maintain context isolation
- **Developer as optimizer**: Pause between phases for evaluation and experimentation
- **Evaluation triggers**: Phase completion, major milestones

**Dual Evaluation System**:
1. **Harness Engineer**: Runs technical evaluations on target harness
2. **Evaluator Agent**: 
   - Validates code alignment with design spec and plan
   - Ensures naming conventions and SDK compliance
   - Tests UX/UI components (spins up frontend, records interactions)
   - Hard fails/passes development phases

#### **Final Delivery**
- Both Harness Engineer and Evaluator Agent run final acceptance tests
- Create comprehensive screen recordings of application interaction
- Bundle all deliverables including final artifacts and documentation

## Naming Rules
- New function names must match their canonical SDK/API equivalent. Communicate the aligned SDK name to Jason and justify any net-new function — what it does and why it belongs.
- Before defining a constant, check if an existing one covers the same contract — if so, import it. If semantically distinct, name it to make the distinction clear and communicate it to Jason in your reply or commit.
- New classes must be documented in the commit message with what they represent and why they were added. Surface non-trivial abstractions to Jason before merging.
- Renaming a function, class, or constant requires a deprecation alias or a note to Jason — silent renames break callers.
- New module and file names must be approved by Jason before merging.

## Canonical SDK References

Before implementing, planning, or writing specs for anything touching these SDKs, read the local source first. Do not rely on training data or general knowledge.

| Topic | Local canonical source |
|---|---|
| Deep Agents SDK (`create_deep_agent()`, middleware, backends, harness architecture) | `.reference/libs/deepagents/deepagents/` |
| Production Deep Agent patterns (CLI reference implementation) | `.reference/libs/cli/deepagents_cli/` |
| `AgentMiddleware` base class (`wrap_model_call`, `before_agent`, state schema) | `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py` |
| LangGraph (StateGraph, nodes, edges, Command, Send, persistence, streaming) | `.venv/lib/python3.11/site-packages/langgraph/` |
| LangGraph API server internals | `.venv/lib/python3.11/site-packages/langgraph_api/` |
| LangGraph SDK client patterns | `.venv/lib/python3.11/site-packages/langgraph_sdk/` |
| LangSmith (tracing, datasets, run management, experiments) | `.venv/lib/python3.11/site-packages/langsmith/` |
| Agent evals (`EvaluatorResult`, LLM-as-judge, trajectory scoring, `GraphTrajectory`) | `.venv/lib/python3.11/site-packages/agentevals/` — `trajectory/llm.py` for LLM-as-judge; `trajectory/match.py` for tool-call matching; `graph_trajectory/` for LangGraph thread trajectory evals; `types.py` for `GraphTrajectory` and `EvaluatorResult` |
| LangChain Anthropic integration (`ChatAnthropic`, Claude-specific patterns) | `.venv/lib/python3.11/site-packages/langchain_anthropic/` |
| Core LangChain patterns | `.venv/lib/python3.11/site-packages/langchain/` |

## Harness-First Architecture  
  
This section is a philosophical and technical guide for maintainers and contributors  
to this codebase. It describes the design principles that govern how this application  
is built using the DeepAgents SDK, and why those principles produce more maintainable,  
composable, and correct LLM applications than the alternatives.  
  
---  
  
### The Core Thesis  
  
The central insight of the DeepAgents SDK is that an LLM application is not a  
collection of prompts and API calls — it is a **harness**: a structured runtime  
that intercepts, transforms, and routes every interaction between the model and  
the world. The harness is the architecture.  
  
`create_deep_agent()` is not a convenience wrapper. It is the graph. It assembles  
a `CompiledStateGraph` whose middleware stack defines the agent's entire behavioral  
surface: what tools it sees, what context is injected into every LLM call, how  
state is managed across turns, and how sub-agents are spawned and isolated. You do  
not build *around* `create_deep_agent()` — you build *into* it by configuring its  
parameters and extending its middleware stack.  
  
The practical consequence of this thesis is that **the shape of your Python code  
should mirror the shape of your agent's cognitive architecture**, not the shape of  
your API calls. A researcher agent and a coder agent are not two instances of the  
same class with different prompts. They are two distinct harnesses with different  
backends, different memory sources, different skills, and different tools — each  
assembled by its own factory function, each living in its own file.  
  
---  
  
### The Middleware Intercept Model  
  
The most important architectural distinction in the DeepAgents SDK is between  
**middleware** and **plain tools**.  
  
A plain tool is invoked *by* the LLM. It is reactive. The LLM decides to call it,  
it runs, and it returns a result. It cannot modify the system prompt, cannot filter  
the tool list, cannot track state across turns, and cannot intercept the model  
request before it is sent.  
  
Middleware is invoked *before* the LLM. It is proactive. It wraps every model call  
via `wrap_model_call()`, giving it the ability to:  
  
- **Inject system-prompt context** on every call (e.g., `MemoryMiddleware` injects  
  loaded memory files; `SkillsMiddleware` injects available skill metadata)  
- **Filter tools dynamically** at call-time based on runtime conditions (e.g.,  
  `FilesystemMiddleware` removes the `execute` tool when the resolved backend does  
  not implement `SandboxBackendProtocol`)  
- **Transform messages** before they reach the model (e.g., `SummarizationMiddleware`  
  truncates old tool arguments and replaces history with summaries when the context  
  window fills)  
- **Maintain cross-turn state** via a typed `state_schema` TypedDict that persists  
  across agent turns  
  
The rule of thumb: **use middleware when the behavior must happen before the LLM  
call; use a plain tool when the behavior is triggered by the LLM's decision.**  
  
The `create_deep_agent()` function assembles a fixed base middleware stack  
automatically — `TodoListMiddleware`, `FilesystemMiddleware`, `SubAgentMiddleware`,  
`SummarizationMiddleware`, `PatchToolCallsMiddleware`, and  
`AnthropicPromptCachingMiddleware` are always present. `SkillsMiddleware` is added  
when `skills=` is passed; `MemoryMiddleware` is added when `memory=` is passed.  
Your custom middleware, passed via `middleware=[]`, is inserted after the base stack  
but before `AnthropicPromptCachingMiddleware` and `MemoryMiddleware`. This ordering  
is intentional: memory and caching are always last so that memory updates do not  
invalidate the Anthropic prompt cache prefix.  
  
The implication for this codebase: **do not add custom middleware to a sub-agent  
unless you need pre-LLM-call interception.** If you only need a specialized tool,  
put it in `tools=[]`. Custom middleware is for cross-cutting concerns that must  
apply to every model call the agent makes.  
  
---  
  
### The Backend Abstraction  
  
The `BackendProtocol` is the agent's interface to the world. It defines a uniform  
API for file operations (`read`, `write`, `edit`, `ls`, `glob`, `grep`,  
`upload_files`, `download_files`) and optionally shell execution (`execute` via  
`SandboxBackendProtocol`). The agent never knows what is behind the backend — it  
could be the local filesystem, LangGraph state, a persistent store, or a remote  
sandbox.  
  
The four backend implementations represent four distinct persistence semantics:  
  
| Backend | Persistence | Scope | Disk |  
|---|---|---|---|  
| `StateBackend` | Thread-scoped | In-process LangGraph state | No |  
| `StoreBackend` | Cross-thread | LangGraph `BaseStore` (namespaced) | Optional |  
| `FilesystemBackend` | Durable | OS filesystem | Yes |  
| `DaytonaSandbox` | Session-scoped | Remote sandbox + execution | Remote |  
  
The `CompositeBackend` is the routing layer. It matches file paths against prefixes  
(longest-first) and delegates to the corresponding backend. This is the mechanism  
that gives each agent a **virtual filesystem** with different persistence semantics  
at different paths:
/ → FilesystemBackend(root_dir=/Agents/architect/) [working files]
/memories/ → FilesystemBackend(root_dir=/Agents/architect/memories/) [on-demand memory]
/skills/ → FilesystemBackend(root_dir=/Agents/architect/skills/) [skills]
/shared/ → FilesystemBackend(root_dir=/Agents/) [shared team context]

  
The key design principle: **path semantics encode persistence semantics.** A file  
at `/memories/` is persistent and agent-scoped. A file at `/shared/` is persistent  
and team-scoped. A file at `/tmp/` is ephemeral. The agent does not need to know  
this — it just reads and writes paths. The `CompositeBackend` handles the routing.  
  
For virtual (no-disk) mode, replace `FilesystemBackend` with `StoreBackend` backed  
by `InMemoryStore` for persistent paths, and `StateBackend` for ephemeral working  
files. The agent code is identical — only the backend factory changes.  
  
---  
  
### Memory as Filesystem, Not State  
  
The DeepAgents memory model is file-based, not state-based. This is a deliberate  
design choice with significant implications.  
  
`MemoryMiddleware` loads configured source files (e.g., `/AGENT.md`,  
`/shared/AGENTS.md`) at the start of each thread, stores their contents in a  
private state field (`memory_contents`), and injects them into the system prompt  
on every LLM call. The load happens once per thread — subsequent calls within the  
same thread skip the load because `memory_contents` is already in state.  
  
The agent writes back to memory files using the standard `edit_file` tool. The  
`MEMORY_SYSTEM_PROMPT` injected by `MemoryMiddleware` explicitly instructs the  
agent to update its memory files when it learns something new, before responding  
to the user. This creates a **memory loop**: load → act → write → load (next  
thread).  
  
The practical consequence: **cross-task learning for `CompiledSubAgent` instances  
happens through files, not through LangGraph checkpointers.** A `CompiledSubAgent`  
is invoked via the `task` tool without a `thread_id` in the config, so its  
LangGraph state does not persist across invocations. But its memory files do. The  
architect sub-agent that writes an Architecture Decision Record to `/memories/`  
will find that ADR in its system prompt the next time it is invoked, because  
`MemoryMiddleware` loads it from disk.  
  
This means the filesystem IS the long-term memory. Design your agent's memory  
structure as carefully as you design its code structure. The `/AGENT.md` file is  
the agent's core identity and working context — always loaded, always injected.  
The `/memories/` directory is the agent's episodic memory — loaded on demand via  
`read_file`. The `/skills/` directory is the agent's procedural memory — loaded  
as metadata by `SkillsMiddleware` and expanded on demand.  
  
---  
  
### Skills as Progressive Disclosure  
  
Skills are on-demand workflows, not always-loaded context. `SkillsMiddleware`  
scans the configured skill directories for subdirectories containing `SKILL.md`  
files, parses their YAML frontmatter, and injects only the skill *metadata* (name  
and description) into the system prompt. The full skill instructions are loaded  
only when the agent decides to use a skill.  
  
The skill directory structure is:  
  
/skills/
└── web-research/
├── SKILL.md ← Required: YAML frontmatter + instructions
└── helper.py ← Optional: supporting scripts

  
This progressive disclosure pattern keeps the system prompt lean. An agent with  
twenty skills does not have twenty full skill documents injected on every call —  
it has twenty one-line descriptions, and loads the full instructions only when  
relevant. This is the correct pattern for capability-rich agents that must operate  
within context window constraints.  
  
---  
  
### System Prompts as External Artifacts  
  
System prompts are configuration, not code. They belong in `.md` files, not in  
Python strings. This is not merely a style preference — it has concrete  
maintainability consequences:  
  
1. **Diff clarity**: Changes to agent behavior are visible as markdown diffs, not  
   Python string diffs. Reviewers can evaluate prompt changes without reading code.  
2. **Separation of concerns**: The agent factory (`agent.py`) describes *how* the  
   agent is assembled. The system prompt (`system_prompt.md`) describes *what* the  
   agent does. These are different concerns and should live in different files.  
3. **Tooling**: Markdown files can be linted, spell-checked, and reviewed with  
   documentation tooling. Python strings cannot.  
4. **Composability**: A system prompt loaded from a file can be templated,  
   versioned, and swapped without touching the factory code.  
  
The pattern is:  
  
```python  
SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.md").read_text()  
The create_deep_agent() function accepts system_prompt as a plain string and
concatenates it with BASE_AGENT_PROMPT — the base behavioral contract that every
DeepAgent inherits. Your system prompt is prepended; the base prompt follows. You
are specializing the agent, not replacing its foundation.

The Sub-Agent Taxonomy
There are three sub-agent patterns in the DeepAgents SDK, and choosing the wrong
one is the most common architectural mistake. The choice is determined by two
questions: does the sub-agent need cross-task persistence? and does it need
to run asynchronously (non-blocking)?

SubAgent (declarative dict spec): Ephemeral, synchronous, in-process. The
base middleware stack (TodoListMiddleware, FilesystemMiddleware,
SummarizationMiddleware, PatchToolCallsMiddleware) is automatically prepended
by create_deep_agent(). Use for simple, fast, stateless delegation tasks. The
sub-agent shares the parent's backend unless you override it via middleware=.

CompiledSubAgent (pre-built Runnable): Ephemeral, synchronous or async
(via ainvoke), in-process. The runnable is used as-is — no base middleware is
prepended. The runnable field accepts any Runnable, including the result of
create_deep_agent(). This is the pattern for sub-agents that need their own
full DeepAgent harness: their own backend, their own memory sources, their own
skills, their own tools. Cross-task persistence is achieved through the filesystem
(memory files), not through a LangGraph checkpointer, because the task tool
invokes the runnable without a thread_id.

AsyncSubAgent (remote deployment spec): Stateful per-task, non-blocking,
out-of-process. Each start_async_task call creates a new thread on the remote
server and stores the thread_id in the parent's async_tasks state.
update_async_task sends a follow-up message to the same thread, giving the
sub-agent full conversation history for that task. This is the only pattern that
gives you both async execution and cross-turn sub-agent state. The trade-off is
that each sub-agent must be deployed as a separate service.

The decision tree:

Does the sub-agent need to run for a long time (minutes+)?  
  → Yes: AsyncSubAgent (deploy as remote service)  
  → No: Does it need its own full DeepAgent harness (own backend, memory, skills)?  
      → Yes: CompiledSubAgent (create_deep_agent() as runnable)  
      → No: SubAgent (declarative dict spec)  
The Orchestrator/Worker Pattern
The project manager agent is an orchestrator. Sub-agents are workers. This
distinction is not just semantic — it has concrete implications for how each is
configured.


What "Taste" Looks Like
Good DeepAgents code has the following properties:

One factory per agent. Each agent is assembled in exactly one place. There
is no agent configuration spread across multiple files or assembled conditionally
at runtime.
System prompts in .md files. No multi-line Python strings for prompts.
Backends in factory functions. The backend is constructed in the factory,
not passed in from outside. The factory knows what storage semantics the agent
needs.
Middleware only when necessary. Custom middleware is added only when the
behavior requires pre-LLM-call interception. Specialized tools go in tools=[].
Memory through files, not state. Cross-task learning is encoded in
/AGENT.md and /memories/. The agent writes to these files; MemoryMiddleware
loads them on the next invocation.
Path semantics encode persistence semantics. /memories/ is persistent.
/tmp/ is ephemeral. /shared/ is team-scoped. The CompositeBackend routes
accordingly.
The orchestrator synthesizes; workers execute. The PM agent does not do
deep work. It delegates, monitors, and synthesizes. Sub-agents do the deep work
and return structured results.
No graph.py unless you need deterministic routing. create_deep_agent()
is the graph. A custom StateGraph is only warranted when you need conditional
edges, fan-out/fan-in, or non-LLM-driven state transitions that cannot be
expressed through the middleware stack and tool-calling loop.
  
---  
  
**Source citations for the claims above:**  
  
The middleware intercept model and the distinction between middleware and plain tools: [1](#8-0) (`.reference/libs/deepagents/deepagents/middleware/__init__.py:1–48`; `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:380–490`)   
  
The base middleware stack assembled by `create_deep_agent()` and its ordering: [2](#8-1) (`.reference/libs/deepagents/deepagents/graph.py:291–322`)   
  
The `BASE_AGENT_PROMPT` that every agent inherits and how `system_prompt` is prepended to it: [3](#8-2) [4](#8-3) (`.reference/libs/deepagents/deepagents/graph.py:38–67` for the prompt definition; `.reference/libs/deepagents/deepagents/graph.py:324–331` for the prepend logic)   
  
The CLI's pattern of loading system prompts from `.md` files: [5](#8-4) (`.reference/libs/cli/deepagents_cli/agent.py:507` loads `system_prompt.md` via `Path(__file__).parent / "system_prompt.md").read_text()`; `.reference/libs/cli/deepagents_cli/agent.py:1122–1129` shows it as the default)   
  
`MemoryMiddleware` loading once per thread and the memory loop: [6](#8-5) [7](#8-6) (`.reference/libs/deepagents/deepagents/middleware/memory.py:238–270` — `before_agent` skips load if `"memory_contents" in state`; `.reference/libs/deepagents/deepagents/middleware/memory.py:322–337` — `wrap_model_call` injects on every LLM call)   
  
`CompiledSubAgent` used as-is with no base middleware prepended: [8](#8-7) (`.reference/libs/deepagents/deepagents/middleware/subagents.py:478–481` — `if "runnable" in spec` branch takes the compiled runnable directly, skipping `create_agent()`)   
  
The `task` tool invocation contract (no `thread_id`, no config): [9](#8-8) (`.reference/libs/deepagents/deepagents/middleware/subagents.py:352–365` — `subagent.invoke(subagent_state)` with no config arg)   
  
State isolation via `_EXCLUDED_STATE_KEYS`: [10](#8-9) (`.reference/libs/deepagents/deepagents/middleware/subagents.py:123–126` — definition; `.reference/libs/deepagents/deepagents/middleware/subagents.py:348` — applied when building subagent state)   
  
`CompositeBackend` path-prefix routing: [11](#8-10) [12](#8-11) (`.reference/libs/deepagents/deepagents/backends/composite.py:119–158` — class docstring and longest-first sort; `.reference/libs/deepagents/deepagents/backends/composite.py:87–116` — `_route_for_path` prefix-matching logic)   
  
`StateBackend` (ephemeral, thread-scoped) and `StoreBackend` (persistent, cross-thread): [13](#8-12) [14](#8-13) (`.reference/libs/deepagents/deepagents/backends/state.py:38–48`; `.reference/libs/deepagents/deepagents/backends/store.py:102–109`)   
  
`FilesystemBackend` with `virtual_mode=True` for path-anchored on-disk storage: [15](#8-14) (`.reference/libs/deepagents/deepagents/backends/filesystem.py:39–138` — class docstring and `virtual_mode` param docs)   
  
`DaytonaSandbox` as the remote sandbox backend: [16](#8-15) (`.reference/libs/deepagents/deepagents/middleware/summarization.py:1154–1163` — canonical usage example importing `from langchain_daytona import DaytonaSandbox`)   
  
Skills progressive disclosure via `SkillsMiddleware`: [17](#8-16) (`.reference/libs/deepagents/deepagents/middleware/skills.py:602–630` — class docstring; `.reference/libs/deepagents/deepagents/middleware/skills.py:763–797` — `abefore_agent` loads metadata once; `.reference/libs/deepagents/deepagents/middleware/skills.py:799–831` — `wrap_model_call` injects on every call) 

## Agent Identity

- Agent identity belongs in one catalog.
- The catalog should answer:
  - What is the agent called?
  - What work is it responsible for?
  - Which prompt or instruction source does it use?
  - Which model policy does it use?
  - Which tools does it own?
  - Which middleware profile does it use?
  - Which child subagents can it call?
  - Does it need project-local memory?
- Do not scatter agent identity across project scaffolding, model policy,
  middleware policy, tool policy, and subagent construction files.
- **Project policy: set `name=` on every agent and sub-agent.** In the SDK, `name` is optional, but when set it propagates to `lc_agent_name` metadata used in traces and streamed chunk metadata. Omitting names degrades multi-agent debugging. (`.reference/libs/deepagents/deepagents/graph.py:100`; `.reference/libs/deepagents/deepagents/graph.py:344–354`)

## Model And Provider Policy

- Model policy owns model/provider request configuration only.
- Valid model policy concerns include model spec, provider, effort, max tokens,
  thinking, streaming, beta headers, Anthropic server-side tools, OpenAI response
  API settings, and provider-specific request parameters.
- Model policy must not own project scaffolding, middleware construction, prompt
  selection, or agent lifecycle.
- If an agent declares Anthropic server-side tools, the runtime factory must pass
  those provider tool definitions into the effective tool set for that agent.
- A model policy that resolves data but is not consumed by the runtime is a bug.

## Memory And Workspace Policy

- Project scaffolding only creates project workspace files and directories.
- Runtime memory loading belongs to the harness assembly layer or middleware
  profile layer.
- Repo-root memory and project-local memory must be named separately.
- Do not imply that a scaffolded `AGENTS.md` file is active runtime memory unless
  the runtime actually loads it.
- `AGENTS.md` files contain active maintainer and agent instructions. Historical
  reasoning belongs in future decision docs.
- **Ensure every `StoreBackend` has a store source.** Satisfy this either by passing `store=` to `create_deep_agent()` (runtime-managed store) or by constructing `StoreBackend(store=...)`. If neither is provided, `StoreBackend` raises at runtime when resolving store access. (`.reference/libs/deepagents/deepagents/graph.py:188–190`; `.reference/libs/deepagents/deepagents/backends/store.py:125–127`; `.reference/libs/deepagents/deepagents/backends/store.py:170–176`)
- **Use POSIX-style virtual paths for backend-facing config.** `skills=` sources are explicitly documented as POSIX; keep `memory=` sources and `CompositeBackend` route prefixes in the same forward-slash form (for example, `/memories/`, `/skills/`) for cross-platform consistency. Avoid backslashes. (`.reference/libs/deepagents/deepagents/graph.py:173–179`; `.reference/libs/deepagents/deepagents/middleware/skills.py:67–70`; `.reference/libs/deepagents/deepagents/backends/composite.py:148–149`)
- **`BackendFactory` enables runtime-scoped backends.** `BackendFactory = Callable[[ToolRuntime], BackendProtocol]` — a callable that receives `ToolRuntime` at call-time and returns a backend. Use this when you need per-user or per-session namespace routing (e.g. deriving a namespace from config). Static backend instances are not sufficient for that pattern. (`.reference/libs/deepagents/deepagents/backends/protocol.py:810–811`)

## Tools And Middleware

- App-owned tools belong in a tool catalog with explicit per-agent ownership.
- SDK-provided tools should be documented as SDK-provided, not re-registered as
  if the application owns them.
- Middleware profiles should be named for the runtime behavior they create.
- Middleware order is a contract. If order matters, document why at the profile
  declaration site.
- Human approval gates must be declared close to the tools they protect or in a
  clearly named HITL policy module.
- **`GENERAL_PURPOSE_SUBAGENT` is always auto-inserted.** `create_deep_agent()` inserts a `general-purpose` subagent at position 0 of the inline subagent list unless you supply a `SubAgent` with `name="general-purpose"` yourself — that named override is the only way to customize it. Do not be surprised by the extra entry in the task tool description. (`.reference/libs/deepagents/deepagents/graph.py:285–289`)
- **`interrupt_on` inheritance rules.** The top-level `interrupt_on` passed to `create_deep_agent()` always applies to the main agent. For subagents: declarative `SubAgent` specs inherit it by default; a per-spec `interrupt_on` overrides the inherited config. `CompiledSubAgent` runnables do **not** inherit — configure HITL inside the compiled runnable. `AsyncSubAgent` specs do **not** inherit — configure approval on the remote deployment. (`.reference/libs/deepagents/deepagents/graph.py:194–211`)
- **For ACP-served agents, never use raw LangGraph `interrupt()` for HITL.** ACP rejects free-form `interrupt()` payloads with a protocol error. Use `interrupt_on=` on `create_deep_agent()` or `HumanInTheLoopMiddleware` so interrupts follow ACP-compatible `action_requests/review_configs` shape. (`.reference/libs/acp/deepagents_acp/server.py:662–679`)
- **`execute` requires `SandboxBackendProtocol`.** The `execute` tool is always registered but only works when the backend implements `SandboxBackendProtocol`. `StateBackend`, `FilesystemBackend`, and `StoreBackend` do not — calling `execute` returns an error. Only `LocalShellBackend`, `DaytonaSandbox`, and equivalent sandbox backends enable it. (`.reference/libs/deepagents/deepagents/graph.py:113–115`)
- **Always declare `tools=[]` explicitly on specialized sub-agents.** If `tools` is omitted from a `SubAgent` spec, the sub-agent inherits the parent's full tool list. This is intentional for the `general-purpose` subagent but will give specialized sub-agents unintended capabilities. (`.reference/libs/deepagents/deepagents/middleware/subagents.py:64–65`)

## Observability Contract

- Preserve decision rationale as a first-class behavior.
- Preserve enough trajectory data to debug why an agent chose a path, which tools
  it used, what assumptions it made, and where it handed work to another agent.
- Decision rationale must be structured enough for tests, traces, or artifacts to
  inspect it. Do not bury it only in prose logs.
- Agent runs should make it possible to answer:
  - What did the agent believe the task was?
  - What plan or todo trajectory did it create?
  - What decision points changed the trajectory?
  - What tool calls or subagent calls mattered?
  - What artifacts were read or written?
  - What assumptions or unresolved risks remain?
- **Canonical streaming contract.** Any code consuming the agent stream must use this pattern:
  ```python
  async for chunk in agent.astream(
      input,
      stream_mode=["messages", "updates"],
      subgraphs=True,
      config=config,
      durability="exit",
  ):
      namespace, stream_mode, data = chunk  # 3-tuple always
      is_main_agent = not namespace         # subagents have non-empty namespace
  ```
  Each chunk is a 3-tuple `(namespace, stream_mode, data)`. Main agent chunks have an empty namespace; subagent chunks have a non-empty namespace. (`.reference/libs/cli/deepagents_cli/non_interactive.py:591–598`; `.reference/libs/cli/deepagents_cli/textual_adapter.py:516–536`)

## Documentation Policy

- 

### AD Governance (`AD.md`)

- `AGENTS.md` is the normative convention contract; `AD.md` is the architecture
  decision baseline and rationale record.
- `AD.md` must capture context, options considered, selected decision, tradeoffs,
  risks, and rollout intent for major architecture changes.
- Implementation-level execution detail belongs in dedicated spec docs; `AD.md`
  should summarize and link, not duplicate full implementation plans.
- Any PR that changes architecture, runtime policy, or agent behavior must update
  at least one of: `AGENTS.md`, `AD.md`, or the relevant spec doc.
- `AD.md` status changes (`Proposed`, `Accepted`, `Superseded`, `Deprecated`)
  must be reflected in the header and changelog in the same edit.
- `Accepted` decisions should not retain unresolved placeholders (for example:
  `TBD`, `<...>`) without an explicit owner and target date.
- High-signal technical assertions in `AD.md` should include local source
  citations (repo path + lines) when feasible.
- If `AD.md` and `AGENTS.md` conflict, treat `AGENTS.md` as authoritative for
  active implementation and update `AD.md` to match.

## Review Standard

- New code should be rejected if it adds a second source of truth without a clear
  reason.
- New files should be rejected if their names do not describe their ownership.
- New agent runtime code should be rejected if it bypasses the SDK harness without
  explaining why.
- New observability behavior should be rejected if it makes trajectory debugging
  worse.
- Refactors should be small enough that v0.5 behavior can be compared against v1
  behavior during migration.
