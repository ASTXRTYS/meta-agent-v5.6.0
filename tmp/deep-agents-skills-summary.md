# Deep Agents SDK — Comprehensive Skills Summary

**Sources read in full:**
- `/skills/langchain/config/AGENTS.md` (34 lines)
- `/skills/langchain/config/skills/deep-agents-core/SKILL.md` (423 lines)
- `/skills/langchain/config/skills/deep-agents-orchestration/SKILL.md` (471 lines)
- `/skills/langchain/config/skills/deep-agents-memory/SKILL.md` (301 lines)

---

## 1. KEY FINDINGS BY DIRECTORY

### 1A. `AGENTS.md` — Project Overview

- Acts as the **global entry point** for the skill system. Lists all available skills across three tiers: LangChain, LangGraph, and Deep Agents.
- Establishes a **critical rule**: "ALWAYS invoke the relevant skill first — skills have the correct imports, patterns, and scripts that prevent common mistakes."
- Deep Agents skills are the highest tier, built on top of LangChain and LangGraph primitives.
- Required env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.

---

### 1B. `deep-agents-core/SKILL.md` — Harness Architecture & Configuration

#### What It Teaches
The core entry point for the entire SDK. Deep Agents is an **opinionated agent framework** built on LangChain/LangGraph that provides built-in middleware. You **configure, not implement**.

#### Core Function: `create_deep_agent()`
The single factory function. Accepts:
| Parameter | Purpose |
|-----------|---------|
| `name` | Agent identifier |
| `model` | LLM model string (e.g., `"claude-sonnet-4-5-20250929"`) |
| `tools` | List of custom `@tool`-decorated functions |
| `system_prompt` | Custom instructions |
| `subagents` | List of subagent config dicts |
| `backend` | Storage backend (StateBackend, FilesystemBackend, StoreBackend, CompositeBackend) |
| `interrupt_on` | Dict mapping tool names to boolean/config for HITL |
| `skills` | List of directory paths containing SKILL.md files |
| `checkpointer` | Required for HITL interrupts (e.g., `MemorySaver()`) |
| `store` | Required for StoreBackend persistence (e.g., `InMemoryStore()`) |

#### Six Built-in Middleware (Always Present)
1. **TodoListMiddleware** — `write_todos` tool for task planning
2. **FilesystemMiddleware** — `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
3. **SubAgentMiddleware** — `task` tool for spawning sub-agents
4. **HumanInTheLoopMiddleware** — Approval workflows
5. **SkillsMiddleware** — On-demand skill loading from directories
6. **MemoryMiddleware** — Persistent storage via Store

#### SKILL.md Format (Progressive Disclosure)
- Directory structure: `skills/<name>/SKILL.md` (+ optional supporting files)
- YAML frontmatter is **required**: `name` + `description`
- Descriptions must be specific (not vague) to help agents decide when to load
- Skills vs AGENTS.md: Skills are on-demand/task-specific; AGENTS.md is always loaded at startup

#### Immutable Constraints
- Core middleware **cannot be removed** (TodoList, Filesystem, SubAgent always present)
- Tool names are fixed: `write_todos`, `task`, `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
- SKILL.md frontmatter format is fixed

#### Common Pitfalls (Fix Patterns)
- Interrupts require a checkpointer
- StoreBackend requires a Store instance
- Consistent `thread_id` required for conversation continuity
- SKILL.md must have YAML frontmatter
- Skills require a proper backend (FilesystemBackend for local, StoreBackend for serverless)
- Skills are NOT inherited by custom subagents — must be passed explicitly
- Default "general-purpose" subagent DOES inherit skills

---

### 1C. `deep-agents-orchestration/SKILL.md` — SubAgents, TodoList, and HITL

#### What It Teaches
Three orchestration capabilities, all automatically included in `create_deep_agent()`.

#### SubAgent System (Task Delegation)

**Mechanism**: Main agent has `task` tool → creates **fresh** subagent → subagent executes autonomously → returns final report.

**Default subagent**: A "general-purpose" subagent is always available with the same tools/config as the main agent.

**Custom subagent config dict**:
```python
{
    "name": "researcher",
    "description": "...",
    "system_prompt": "...",
    "tools": [...],
    "interrupt_on": {...},  # Optional HITL per-subagent
    "skills": [...]         # Optional, NOT inherited from parent
}
```

**Critical: Subagents are STATELESS**
- Each `task()` call creates a fresh agent with no memory of prior calls
- Must provide complete instructions in a single call
- WRONG: `task(agent='x', instruction='Find data')` then `task(agent='x', instruction='What did you find?')`
- RIGHT: `task(agent='x', instruction='Find data on AI, save to /research/, return summary')`

**Custom subagents don't inherit skills** — must provide explicitly. The default general-purpose subagent DOES inherit.

#### TodoList System (Task Planning)

- `write_todos(todos: list[dict])` — each item has `content` (str) and `status` ("pending" | "in_progress" | "completed")
- Included by default via TodoListMiddleware
- Best for: complex multi-step tasks, long-running operations
- Skip for: simple single-action tasks, < 3 steps
- Todos are accessible from final state: `result.get("todos", [])`
- Requires `thread_id` for persistence across invocations

#### Human-in-the-Loop (HITL) System

**Configuration**: `interrupt_on` dict maps tool names to:
- `True` — all approval decisions allowed
- `{"allowed_decisions": ["approve", "reject"]}` — restrict decision types
- `False` — no interrupts for that tool

**Approval Workflow (3-step)**:
1. Agent proposes tool call → execution pauses (invoke returns)
2. Check state: `state = agent.get_state(config); if state.next: ...`
3. Resume with decision: `agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)`

**Three Decision Types**:
1. `{"type": "approve"}` — proceed as proposed
2. `{"type": "reject", "message": "Run tests first"}` — reject with feedback
3. `{"type": "edit", "edited_action": {"name": "tool_name", "args": {...}}}` — modify args then execute

**Critical Requirements**:
- Checkpointer is **mandatory** for any HITL
- Consistent `thread_id` required for resumption
- Interrupts happen **between** `invoke()` calls, not mid-execution

#### Immutable Constraints
- Tool names (`task`, `write_todos`) cannot be changed
- HITL protocol structure (approve/edit/reject) is fixed
- Checkpointer requirement cannot be bypassed
- Subagents cannot be made stateful — they are always ephemeral

---

### 1D. `deep-agents-memory/SKILL.md` — Storage Backends & Persistence

#### What It Teaches
Four pluggable backends for file operations and memory:

#### Backend Types

| Backend | Scope | Persistence | Use Case |
|---------|-------|-------------|----------|
| **StateBackend** | Thread-scoped | Lost when thread ends | Default; temp working files |
| **StoreBackend** | Cross-thread | Persists across threads/sessions | Long-term memory |
| **FilesystemBackend** | Real disk | Actual filesystem | Local dev / CLI tools |
| **CompositeBackend** | Routing | Mixed | Hybrid ephemeral + persistent |

#### StateBackend (Default)
- Files exist only within a single thread
- No setup required — it's the default
- Thread-2 CANNOT read files written by Thread-1

#### StoreBackend (Cross-Session)
- Requires a `Store` instance (`InMemoryStore()` for dev, `PostgresStore(...)` for prod)
- Files persist across threads
- Used for long-term memory, user preferences, learned patterns

#### FilesystemBackend (Local Dev)
- Direct disk read/write access
- `virtual_mode=True` restricts path access (prevents `../` and `~/` escapes)
- **SECURITY WARNING**: Never use in web servers — use StateBackend or sandbox

#### CompositeBackend (Hybrid Routing)
- Routes file paths to different backends based on **longest prefix match**
- Example: `/draft.txt` → StateBackend (ephemeral), `/memories/prefs.txt` → StoreBackend (persistent)
- Configuration:
  ```python
  CompositeBackend(
      default=StateBackend(rt),
      routes={"/memories/": StoreBackend(rt)}
  )
  ```
- Longest prefix wins: `/mem/temp/file.txt` matches `/mem/temp/` over `/mem/`

#### Direct Store Access in Custom Tools
- Custom tools can access the store via `ToolRuntime`:
  ```python
  @tool
  def my_tool(key: str, runtime: ToolRuntime) -> str:
      store = runtime.store
      result = store.get(("namespace",), key)
  ```
- Store API: `store.get(namespace_tuple, key)`, `store.put(namespace_tuple, key, value_dict)`

#### Cross-Session Memory Pattern
- Use CompositeBackend with StoreBackend route for `/memories/`
- Thread-1 writes to `/memories/style.txt` → Thread-2 reads it successfully

#### Immutable Constraints
- Tool names (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`) are fixed
- Cannot access files outside `virtual_mode` restrictions
- Cannot do cross-thread file access without proper backend setup

#### Common Pitfalls
- StoreBackend without Store instance = error
- StateBackend files don't persist across threads
- Path must match CompositeBackend route prefix for persistence
- Use PostgresStore for production (InMemoryStore is lost on restart)
- FilesystemBackend needs `virtual_mode=True` for security

---

## 2. GAPS — What Questions Remain Unanswered

### 2.1 Agent Types & Lifecycle
- **No agent type taxonomy** — The skills mention a "general-purpose" default subagent but never enumerate distinct agent types (research agent, code agent, PM agent, etc.)
- **No lifecycle documentation** — No information about agent startup sequence, middleware initialization order, or shutdown/cleanup
- **No recursion limits** — Despite the prompt asking about this, the skills contain ZERO mention of recursion depth limits, max sub-agent nesting, or effort levels
- **No effort levels** — No concept of "effort levels" appears anywhere in these skills

### 2.2 The `task` Tool
- **Exact signature unknown** — The skills show `task(agent="name", instruction="...")` in comments but never define the formal tool schema/parameters
- **Return format unclear** — "Returns final report" but no schema for what that report contains
- **Error handling** — What happens if a subagent fails? No error/retry patterns documented
- **Concurrency** — Can multiple `task()` calls run in parallel? Not addressed

### 2.3 Subagent Configuration
- **Model override** — Can subagents use a different model than the parent? Not shown
- **Backend inheritance** — Do subagents inherit the parent's backend? Not addressed
- **Store sharing** — Do subagents share the parent's Store instance? Not explicit
- **Nesting** — Can subagents spawn their own subagents? Not addressed

### 2.4 Streaming & Observability
- **No streaming documentation** — No mention of `astream`, `astream_events`, or token streaming
- **No tracing/LangSmith integration** — No observability patterns documented
- **No logging** — No middleware for logging or debugging

### 2.5 Production Deployment
- **PostgresStore mentioned but not shown** — Only `InMemoryStore` examples
- **No async patterns** — All examples use synchronous `invoke()`, no `ainvoke()`
- **No error handling patterns** — No try/catch, no retry logic, no timeout configuration
- **No rate limiting** — No discussion of API rate limits or token budgets
- **No deployment patterns** — No web server integration, no queue-based processing

### 2.6 State Management
- **State schema** — What does the full agent state look like beyond `messages` and `todos`?
- **Custom state** — Can you add custom state fields?
- **State size limits** — Any limits on state/context window management?

### 2.7 Skills System Internals
- **Skill loading trigger** — How exactly does an agent decide to load a skill? Keyword matching? LLM decision?
- **Skill unloading** — Are skills ever unloaded from context?
- **Skill conflicts** — What if two skills give contradictory advice?

---

## 3. ACTIONABLE BASELINE — What We Know For Certain

### 3.1 Architecture Certainties
1. `create_deep_agent()` is the single entry point for creating any Deep Agent
2. Six middleware are always present and cannot be removed
3. Three built-in tool categories: planning (`write_todos`), filesystem (`ls`/`read_file`/`write_file`/`edit_file`/`glob`/`grep`), delegation (`task`)
4. The framework is built on LangChain/LangGraph — it's an opinionated layer on top

### 3.2 Sub-Agent Certainties
5. Subagents are **always stateless** — each `task()` call is a fresh execution
6. A "general-purpose" default subagent always exists with the parent's tools/config
7. Custom subagents must explicitly receive skills — no inheritance
8. The general-purpose subagent DOES inherit skills
9. Subagent config is a dict: `name`, `description`, `system_prompt`, `tools`, optional `interrupt_on` and `skills`

### 3.3 Memory Certainties
10. Default backend is StateBackend — ephemeral, thread-scoped
11. StoreBackend enables cross-thread persistence — requires Store instance
12. CompositeBackend routes paths to backends via longest-prefix matching
13. FilesystemBackend gives real disk access — `virtual_mode=True` for security
14. InMemoryStore for dev, PostgresStore for production
15. Custom tools can access Store directly via `ToolRuntime.store`

### 3.4 HITL Certainties
16. HITL requires a checkpointer (e.g., `MemorySaver()`)
17. Three decision types: approve, reject (with message), edit (with modified args)
18. Interrupts occur between `invoke()` calls
19. Consistent `thread_id` required for resumption
20. HITL can be configured per-tool and per-subagent

### 3.5 Configuration Certainties
21. `thread_id` in config is required for conversation continuity
22. Skills use YAML frontmatter with `name` + `description`
23. Skills directory structure: `skills/<name>/SKILL.md`
24. Both Python and TypeScript APIs available with equivalent features

### 3.6 What CANNOT Be Changed
25. Core middleware (TodoList, Filesystem, SubAgent) — always present
26. Built-in tool names — fixed
27. SKILL.md frontmatter format — fixed
28. HITL protocol structure — fixed
29. Subagent statelessness — they cannot be made persistent
