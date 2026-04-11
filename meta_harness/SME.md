I used the relevant Deep Agents and LangGraph skills, then checked the local canonical SDK source and PyPI. My decision: **do not model PM, Harness Engineer, Researcher, Architect, Planner, Developer, and Evaluator as PM-owned `SubAgent` dicts or stock `CompiledSubAgent`s.** Make each one a first-class `create_deep_agent()` graph with its own `name`, checkpointer, project-scoped thread identity, memory, tools, and summarization stack. Then add a thin coordination layer for handoffs and loops.

**Recommended Topology**
Use this abstraction split:

- **Deep Agents**: the runtime for each cognitive role.
- **LangGraph / LangGraph SDK**: the control plane for durable routing, thread identity, background execution, loop gates, and run status.
- **LangChain**: underlying model/tool primitives only.

Each role should have a canonical thread per project, for example:

`thread_id = f"{project_id}:{agent_name}"`

So the PM is not the parent container of the others. It is one peer Deep Agent and the default human-facing entry point. The specialists are peer Deep Agent graphs that can be invoked by PM or by other specialists through explicit handoff tools.

**Why**
The SDK’s `task` tool is explicitly for ephemeral subagents, and the built-in path calls `subagent.invoke(subagent_state)` without forwarding a config or `thread_id`; see [subagents.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/subagents.py):152 and [subagents.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/subagents.py):375. `CompiledSubAgent` is used as-is, but the stock `task` invocation still does not supply the stable thread config needed for checkpoint resumption; see [subagents.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/subagents.py):489.

LangGraph persistence is keyed by runtime config; the compile docs say the same `thread_id` is what accumulates state across invocations, and runtime raises if a checkpointer has no configurable checkpoint keys; see [state.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/graph/state.py):1055 and [main.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph/pregel/main.py):2421.

**How Agents Communicate**
Do not rely on free-form peer-to-peer magic. Give agents explicit coordination tools such as:

- `handoff_to_harness_engineer(project_id, bundle_ref, summary)`
- `request_research(project_id, question, needed_by)`
- `request_architect_revision(project_id, critique_ref)`
- `request_eval(project_id, artifact_ref, criteria_ref)`
- `ask_pm(project_id, question_bundle)`

Those tools should resolve the target agent, ensure the target project-role thread exists, then invoke that agent with the stable `thread_id`. Handoffs should pass a concise brief plus artifact references, not dump the whole PM context.

For remote/background work, stock `AsyncSubAgent` is close but not sufficient if project-scoped remote thread IDs are a hard requirement. Its `start_async_task` creates a new remote thread with `client.threads.create()` and then runs on that generated ID; updates reuse the same task thread, but new starts make new threads. See [async_subagents.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/async_subagents.py):291 and [async_subagents.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.reference/libs/deepagents/deepagents/middleware/async_subagents.py):523. The lower-level SDK does support explicit `thread_id` and `if_exists="do_nothing"` on thread creation, and explicit `thread_id` on runs; see [threads.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph_sdk/_async/threads.py):98 and [runs.py](/Users/Jason/2026/v4/meta-agent-v5.6.0/.venv/lib/python3.11/site-packages/langgraph_sdk/_async/runs.py):438. So build a small project-aware async handoff wrapper or custom middleware rather than using stock `AsyncSubAgent` as the final production abstraction.

**How Loops Work**
For LLM-directed loops, let the agents call narrowly-scoped peer tools. Example: Architect can call Researcher repeatedly, each time resuming Researcher’s `project_id:researcher` thread. Harness Engineer can call PM only when it needs stakeholder clarification. Developer can call Evaluator and Harness Engineer at phase boundaries.

For deterministic phase gates, use a thin LangGraph coordinator. It should own routing state, allowed transitions, run IDs, and pass/fail gates, not the specialist cognition. The specialists remain Deep Agents.

**PM → Harness Engineer**
The PM should finish PRD scoping, write or register a handoff bundle, then call a dedicated handoff tool targeting `project_id:harness-engineer`. The Harness Engineer resumes its own project thread, reads the bundle, and owns rubrics, datasets, calibration, and eval harness strategy. If it has questions, it uses `ask_pm` or `ask_user`-style HITL rather than pulling the PM into every technical loop.

One caveat: “full reasoning trajectories” should mean observable trajectory: decisions, assumptions, tool calls, todos, artifacts, summaries, traces, and rationale notes. Do not design around persisting hidden model chain-of-thought.

Source note: PyPI shows `deepagents` latest as `0.5.2` released April 10, 2026, matching the `.reference` SDK source I used; your current venv reports `deepagents 0.4.12`, so implementation should use or upgrade to the canonical reference behavior before coding against these APIs. [PyPI source](https://pypi.org/project/deepagents/)