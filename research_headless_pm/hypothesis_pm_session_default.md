# Hypothesis: PM Session As The Default Headless Entry State

| Field | Value |
|---|---|
| Status | Hypothesis for architecture validation |
| Date | 2026-04-19 |
| Scope | Meta Harness headless PM entrypoint, project/thread identity, cross-project context routing |
| Related Open Question | `meta_harness/AD.md` OQ-1: Entry Point Architecture vs Headless-First Vision |
| Primary Runtime Assumption | LangGraph / LangSmith Agent Server provides the headless runtime boundary |

## 1. Hypothesis
*in order to satisfy goig headless as stated in /vision.md*

Meta Harness should should introduce `pm_session` as the default runtime state whenever a user communicates with the Project Manager outside an already-selected project execution thread.

In this model, the user is always talking to the same Project Manager from a product perspective. Internally, the PM can operate in two modes:

1. **PM session mode**: a projectless or cross-project conversation thread used for stakeholder intake, project discovery, cross-project questions, and pre-seed scoping.
2. **Project mode**: a canonical project execution thread used by the Project Coordination Graph to run the full project lifecycle with the PM and specialist Deep Agents.

The PM is not split into a "helper PM" and a "real PM." `pm_session` is the Project Manager running outside a specific project. The same PM factory, prompt identity, memory policy, and tool philosophy should apply across both modes.

The main architectural change is to stop treating `thread_id` as identical to `project_id` in all contexts. Instead:

```txt
thread_id          = LangGraph checkpoint / conversation identity
project_id         = Meta Harness durable domain identity
project_thread_id  = canonical LangGraph thread for one executable project
pm_session_thread  = LangGraph thread for non-project PM conversation
```

## 2. Why This Matters

The original architecture assumes a user enters the application through a single Project Coordination Graph, with `thread_id = project_id`. That works when the user is already inside a project, but it does not naturally support headless usage.

Headless users will often start with projectless or cross-project messages:

- "I want to scope a new project."
- "How are evals going for Project Beta?"
- "What was the architecture decision for Alpha?"
- "Compare the status of Alpha, Beta, and Charlie."
- "Start a project from this Slack thread once everyone aligns."

Forcing every such interaction into a project thread creates premature project identity and makes cross-project PM communication awkward. Conversely, forcing the PM to always begin in projectless mode without a durable thread loses conversation continuity.

`pm_session` resolves this by giving the PM a durable, stateful conversation thread that is not yet a project.

## 3. Core Product Invariant

The user experience should be:

```txt
The user always experiences one Project Manager.
The system internally distinguishes PM session threads from project execution threads.
```

This matters more than the backend topology. A stakeholder in Slack, email, Discord, the web app, or the TUI should not need to understand whether they are in `pm_session` or `project` mode. They should experience a PM that can:

- discuss work generally,
- remember relevant company/project context,
- create a project when enough information exists,
- enter an existing project when the user references it,
- switch project focus when the conversation changes,
- execute the full Meta Harness project lifecycle from a headless channel.

## 4. Runtime Model

### 4.1 Thread Kinds

Meta Harness should classify LangGraph threads with explicit metadata:

```json
{
  "thread_kind": "pm_session | project | utility",
  "org_id": "acme",
  "user_id": "optional-user-id",
  "source": "slack | discord | email | web | tui | api",
  "external_thread_key": "optional external channel/thread id",
  "active_project_id": "optional current project focus",
  "active_project_thread_id": "optional current project execution thread"
}
```

For canonical project execution threads:

```json
{
  "thread_kind": "project",
  "org_id": "acme",
  "project_id": "beta",
  "project_thread_id": "project_beta",
  "parent_pm_thread_id": "pm_session_abc123",
  "source": "slack | discord | email | web | tui | api"
}
```

### 4.2 Default Routing Rule

Whenever a user communicates with the PM:

```txt
if message is explicitly bound to an existing project_thread_id:
    route to the project graph/thread
else:
    create or select a pm_session thread
```

This applies to both headless channels and first-party UIs.

Examples:

- Slack mention in a new Slack thread -> `pm_session`
- Web app "Ask PM" outside a selected project -> `pm_session`
- TUI global PM chat outside selected project -> `pm_session`
- Slack thread already attached to Project Beta -> may route to Beta or to `pm_session` with `active_project_id=beta`, depending on product policy
- Direct project dashboard message inside Beta -> project thread

## 5. PM Capabilities In Session Mode

The PM in session mode should receive tools that let it bridge from general conversation to project execution without custom runtime infrastructure.

Recommended tool surface:

| Tool | Purpose |
|---|---|
| `create_project_thread` | Create a canonical project execution thread from seed context and register it |
| `continue_project_thread` | Submit a run to an existing project thread |
| `search_project_registry` | Find projects by name, alias, summary, status, stakeholders, or metadata |
| `resolve_project_reference` | Map user language such as "Beta" or "the support QA agent" to a project ID/thread |
| `read_project_memory` | Read project summary, decisions, status, eval state, artifact index |
| `search_past_threads` | Search LangGraph thread metadata/history for relevant prior conversations |
| `read_thread_history` | Inspect a specific LangGraph thread's historical state/messages when needed |
| `summarize_context_to_project_memory` | Persist synthesized context from PM session into the target project memory |

These are product-domain tools over LangGraph SDK and Store primitives. They should not become a separate orchestration framework.

## 6. Project Creation Flow

When a user says, "I want to start a project. I'm ready to start scoping," the PM should begin in `pm_session`, gather high-signal pre-seed information, and call `create_project_thread` when enough context exists.

The flow:

```txt
1. User sends message in Slack/web/TUI/email.
2. Adapter creates or selects pm_session thread.
3. PM gathers seed context:
   - product goal
   - stakeholders
   - target users
   - rough success criteria
   - constraints
   - existing docs or references
4. PM calls create_project_thread.
5. Tool creates a canonical project_thread_id.
6. Tool writes project registry entry and project memory seed.
7. Tool invokes or schedules the Project Coordination Graph on the project thread.
8. PM tells the user the project has been created and remains available in the same channel.
```

The seed package should include:

```json
{
  "project_id": "support_qa_agent",
  "project_thread_id": "project_support_qa_agent",
  "source_pm_session_thread_id": "pm_session_abc123",
  "seed_context": {
    "stakeholder_goal": "...",
    "known_constraints": ["..."],
    "initial_success_criteria": ["..."],
    "referenced_artifacts": ["..."],
    "open_questions": ["..."]
  }
}
```

## 7. Cross-Project Question Flow

### 7.1 Project Beta Evals Example

User:

> How are the evals going for Project Beta?

Expected flow:

```txt
1. Channel adapter resolves the external conversation to a pm_session thread.
2. PM calls resolve_project_reference("Project Beta").
3. PM receives project_id and project_thread_id.
4. PM calls read_project_memory for Beta eval/status artifacts.
5. If memory is stale, PM calls continue_project_thread with a status request.
6. PM answers in the original user channel.
```

### 7.2 Switching To Project Alpha

User:

> What was the chosen architecture for Project Alpha?

Expected flow:

```txt
1. PM remains in the same pm_session thread.
2. PM resolves "Project Alpha" through the project registry.
3. PM reads Alpha project memory and relevant thread history.
4. PM answers from Alpha context or resumes Alpha's project thread if needed.
5. PM may update active_project_id to Alpha in the pm_session metadata.
```

The PM session should not be mutated into Alpha's project thread. The PM session is the control surface; Alpha's project thread remains canonical for Alpha execution.

## 8. Memory Model

The hypothesis uses the SDK-supported split between thread-scoped checkpoint state and cross-thread Store memory.

| Layer | Purpose | Scope |
|---|---|---|
| LangGraph checkpoint | Short-term resumable execution state | One `thread_id` |
| LangGraph Store | Cross-thread registry, summaries, indexes, active focus | Organization / user / project namespaces |
| Deep Agents `CompositeBackend` + `StoreBackend` | Filesystem-style persistent memory exposed to agents | Project and PM memory paths |
| Project artifacts | Durable project files and deliverables | Project filesystem / sandbox / local disk |

Recommended Store namespaces:

```txt
(org_id, "pm")
(org_id, "pm", user_id)
(org_id, "projects")
(org_id, "project", project_id)
(org_id, "thread_index")
(org_id, "external_threads", source)
```

Recommended project memory files:

```txt
/memories/project/AGENTS.md
/memories/project/summary.md
/memories/project/current_status.md
/memories/project/decisions.md
/memories/project/eval_status.md
/memories/project/artifact_index.json
```

Vector search may be added later, but it is not required for the base architecture. The base implementation should start with Store-backed registry entries, compact markdown summaries, and explicit project memory files.

## 9. Busy Thread Handling

Headless channels can deliver messages while a project thread is already running. Starting a duplicate run against the same project thread would create race conditions and confusing product behavior.

Use the Open SWE pattern:

```txt
1. Adapter checks whether the target LangGraph thread is busy.
2. If idle, adapter creates a run.
3. If busy, adapter appends the new message to a Store-backed queue keyed by thread_id.
4. A before_model middleware checks the queue before each model call.
5. Middleware injects queued messages into the active run and clears the queue.
```

This is especially important for Slack threads with multiple stakeholders. People should be able to add clarifications while the PM or project graph is working; the system should absorb those messages into the active execution rather than fork duplicate project runs.

## 10. Relationship To The Project Coordination Graph

This hypothesis does not remove the Project Coordination Graph. It scopes it more precisely.

The Project Coordination Graph remains the executable project lifecycle boundary:

```txt
Project thread
  -> Project Coordination Graph
      -> PM Deep Agent
      -> Harness Engineer Deep Agent
      -> Researcher Deep Agent
      -> Architect Deep Agent
      -> Planner Deep Agent
      -> Developer Deep Agent
      -> Evaluator Deep Agent
```

The PM session exists before, above, or beside project execution:

```txt
PM session thread
  -> PM Deep Agent
      -> create_project_thread
      -> continue_project_thread
      -> search_project_registry
      -> read_project_memory
      -> search_past_threads
```

This allows Meta Harness to support both:

1. projectless conversation with the PM, and
2. full project execution through the existing PCG topology.

## 11. Deployment Shape

The clean deployment shape is two graph IDs:

```json
{
  "graphs": {
    "pm_intake": "meta_harness.agents.project_manager:make_pm_intake_graph",
    "project": "meta_harness.graph:make_graph"
  }
}
```

`pm_intake` should not be understood as a second PM product identity. It is the PM in session mode.

Both graph IDs can share:

- PM prompt fragments,
- PM tools where appropriate,
- PM long-term memory namespace,
- model profile,
- auth policy,
- tracing metadata conventions.

The graph IDs differ because their state contracts differ. A projectless PM session should not carry the full Project Coordination Graph state schema, and the PCG should not become a catch-all chat router.

## 12. Compatibility Impact

The main breaking change is semantic rather than mechanical:

```txt
Before:
project_id doubles as thread_id everywhere.

After:
project_id is the durable domain identity.
project_thread_id is the canonical execution thread for that project.
pm_session thread_id is a non-project PM conversation.
```

Expected update points:

- `meta_harness/AD.md` language around `thread_id = "{project_id}"`.
- `meta_harness/schemas/state.py` docstrings that describe `project_id` as root thread identifier.
- Project registry and context schemas.
- Thread metadata conventions.
- UI thread/project selectors.
- Headless channel adapters.

`HandoffRecord` does not need `project_thread_id` by default if it remains purely project-scoped. Cross-thread audit can be handled through metadata fields such as `origin_thread_id` or `parent_pm_thread_id` only where needed.

## 13. Alternatives Considered

### Alternative A: Keep `thread_id = project_id` Everywhere

Rejected as a general headless model.

This works for project execution but fails for projectless PM conversations and cross-project questions. It forces premature project creation and makes "talk to the PM outside a project" awkward.

### Alternative B: Collapse PM Session And Project Execution Into One Giant Graph

Rejected for state clarity.

This would make the PCG responsible for global PM conversation, project routing, and full project execution. It risks turning the PCG into a second agent brain and weakening the clean state boundary already established in the architecture.

### Alternative C: Separate Helper PM For Intake

Rejected as product framing.

There may be a separate `pm_intake` graph ID, but product identity should remain one PM. The user should not experience an intake assistant and then a different project PM. The implementation should reuse the same PM identity and memory.

### Alternative D: Merge Multiple Checkpoint Threads

Rejected because it is not supported as a native LangGraph primitive.

The supported approach is tool-mediated context assembly: search thread metadata, read thread history, search/read Store-backed memory, then write synthesized context into the target session or project memory.

## 14. Source Support

The hypothesis is supported by previous research in this folder:

- `research_headless_pm/report.md`: Agent Server as runtime boundary, `thread_id` as checkpoint identity, Store as cross-thread memory, two graph IDs.
- `research_headless_pm/findings_official_docs.md`: official documentation support for assistants, threads, runs, Store, auth, thread search/history, and the absence of native checkpoint-thread merge.
- `research_headless_pm/findings_sdk_source.md`: local SDK source confirmation for `create_deep_agent(... checkpointer, store, backend, name, subagents)`, StoreBackend, CompositeBackend, LangGraph `thread_id`, `checkpoint_ns`, and runtime execution info.
- `research_headless_pm/findings_open_swe.md`: Open SWE source confirmation for deterministic external-thread mapping, thread metadata, `runs.create`, Store-backed queueing, and `before_model` queue drain.

External source anchors:

- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangSmith Agent Server: https://docs.langchain.com/langsmith/agent-server
- LangGraph / LangSmith threads: https://docs.langchain.com/langsmith/use-threads
- Deep Agents memory: https://docs.langchain.com/oss/python/deepagents/memory
- Open SWE reference: https://github.com/langchain-ai/open-swe

## 15. Falsifiable Validation Plan

This hypothesis should be validated through concrete scenarios.

### Scenario 1: New Project From Slack

Input:

> We want to scope a support QA agent. Can you help us start?

Expected:

- Slack thread maps to `pm_session`.
- PM gathers seed context.
- PM calls `create_project_thread`.
- Registry contains new project.
- Project thread starts PCG scoping.
- User can continue in Slack.

### Scenario 2: Cross-Project Status

Input:

> How are Alpha, Beta, and Charlie going?

Expected:

- PM remains in `pm_session`.
- PM resolves all three projects.
- PM reads project memory/status summaries.
- PM answers without merging checkpoint states.

### Scenario 3: Project Focus Switch

Input sequence:

```txt
User: How are evals going for Beta?
User: What architecture did we choose for Alpha?
```

Expected:

- PM resolves Beta, answers Beta.
- PM then resolves Alpha, answers Alpha.
- Same PM session thread remains active.
- Project threads remain separate.

### Scenario 4: Busy Project Thread Follow-Up

Input:

> One more constraint: we need SOC2-safe logging.

Expected:

- If target project thread is busy, message is queued in Store.
- `before_model` middleware injects the follow-up into the active run.
- No duplicate project run starts.

### Scenario 5: UI Outside Existing Project

Input:

User opens web app global PM chat and asks:

> Can you remind me which project owns the eval harness migration?

Expected:

- Web app creates/selects `pm_session`.
- PM searches project registry.
- PM answers from registry/project memory.
- No project thread is created unless needed.

## 16. Decision Criteria

Promote this hypothesis to an architectural decision if validation shows:

- Stakeholders can start a full project from a headless conversation.
- The PM can answer cross-project questions without confusing project state.
- The PM can switch project focus inside one user conversation.
- The full PCG lifecycle still executes in canonical project threads.
- LangSmith traces and LangGraph thread metadata remain understandable.
- No custom runtime is introduced beyond thin channel adapters and PM tools over Agent Server SDK / Store.
- The product experience remains "one PM" across session and project modes.

Reject or revise the hypothesis if:

- `pm_session` creates confusing state transitions for users.
- PM tools over thread/store primitives become a brittle custom orchestration layer.
- PCG execution cannot be reliably started/resumed from PM session tools.
- Cross-project registry/search is too weak without a heavier memory/indexing layer.
- Observability becomes worse than the current `project_id = thread_id` model.

## 17. Current Recommendation

Adopt `pm_session` as the default state for headless PM communication and any first-party UI communication outside a selected project.

Keep the Project Coordination Graph as the canonical project execution boundary.

Give the PM SDK-backed tools to create, resolve, continue, and inspect project threads.

Use LangGraph Store and Deep Agents `StoreBackend` for cross-thread/project memory.

Do not attempt to merge checkpoint threads. Use explicit context assembly and project memory summarization instead.
