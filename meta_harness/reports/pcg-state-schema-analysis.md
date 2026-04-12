# PCG State Schema Analysis Report

> **Date:** 2026-04-12  
> **Status:** Research report — not yet an AD amendment  
> **Purpose:** Provide high-signal analysis of the current `ProjectCoordinationState` schema, identify unresolved semantics, trace SDK-verified message flow, and propose a revised schema with clear key semantics.

---

## 1. Executive Summary

The current PCG state schema in `AD.md:186-201` lists seven keys with types and a "Set by" column, but the **semantic purpose** of each key — *why* it exists, *what* flows through it, and *what* a maintainer should understand at a glance — is under-specified. The most consequential gap is `messages`: the AD says it is the "shared key with child agent input schemas" but does not explain what actually accumulates there, whether handoff tools write to it, or how it differs from `handoff_log`.

This report traces the full SDK-verified data flow, analyzes each key's current state of resolution, and proposes a revised schema where every key's purpose is immediately obvious to a maintainer.

**Key finding:** The current schema conflates two different concerns — the `messages` key serves as both a LangGraph-mandated parent-child conduit AND an ambiguous coordination trail. These concerns should be cleanly separated.

---

## 2. SDK-Verified Parent-to-Child State Propagation

### 2.1 How LangGraph Maps Parent State to Child Input

When a compiled graph is added as a node via `add_node`, the node's `input_schema` determines which parent state keys flow into the child:

**Source:** `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1308-1309`
```python
input_schema = node.input_schema if node else self.builder.state_schema
input_channels = list(self.builder.schemas[input_schema])
```

If `input_schema` is not explicitly set, it defaults to the full parent state schema (`self.state_schema` at line 775). Only the keys present in `input_schema` are read from parent state and passed into the node.

**Implication:** The AD's invariant that "messages is the only key shared with child agent input schemas" is **not enforced by LangGraph** — it requires the implementation to explicitly set `input_schema=_InputAgentState` on the `add_node` call for each mounted child graph. Without this, the child would receive ALL PCG state keys.

### 2.2 The `_InputAgentState` Contract

**Source:** `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361`
```python
class _InputAgentState(TypedDict):
    """Input state schema for the agent."""
    messages: Required[Annotated[list[AnyMessage | dict[str, Any]], add_messages]]
```

The Deep Agent input schema defines exactly one key: `messages`. This is the **only** channel LangGraph will use to pass data from the PCG into a mounted child graph.

**Source:** `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:364-368`
```python
class _OutputAgentState(TypedDict, Generic[ResponseT]):
    """Output state schema for the agent."""
    messages: Required[Annotated[list[AnyMessage], add_messages]]
    structured_response: NotRequired[ResponseT]
```

The output schema also has `messages` as its primary key. When a child agent finishes normally (not via `Command.PARENT`), its final `messages` output flows back to the parent state's `messages` key via the `add_messages` reducer.

### 2.3 How `Command.PARENT` Updates Flow Back to Parent State

When a child agent's handoff tool returns `Command(graph=Command.PARENT, update={...}, goto="process_handoff")`, the update dict is applied to the **parent** state channels using the parent's reducers.

**Source:** `.venv/lib/python3.11/site-packages/langgraph/pregel/_retry.py:127-140`
```python
except ParentCommand as exc:
    ns: str = config[CONF][CONFIG_KEY_CHECKPOINT_NS]
    cmd = exc.args[0]
    if cmd.graph in (ns, recast_checkpoint_ns(ns), task.name):
        # this command is for the current graph, handle it
        for w in task.writers:
            w.invoke(cmd, config)
        break
    elif cmd.graph == Command.PARENT:
        # this command is for the parent graph, assign it to the parent.
        exc.args = (replace(cmd, graph=_checkpoint_ns_for_parent_command(ns)),)
    # bubble up
    raise
```

When the `ParentCommand` bubbles up to the parent graph level, `cmd.graph` matches the parent's namespace, and the command's `update` dict is written through the parent node's writers. Each key in `update` is applied to the corresponding parent state channel using its reducer.

**Critical implication:** The handoff tool's `Command.PARENT` update dict can write to **any** key in the parent state schema. It is not limited to `messages`. The update dict maps directly to parent state channels:

```python
Command(
    graph=Command.PARENT,
    goto="process_handoff",
    update={
        "handoff_log": [HandoffRecord(...)],   # → appended via add_messages reducer
        "current_agent": "researcher",          # → overwritten (no reducer)
        "pending_handoff": HandoffRecord(...),  # → overwritten (no reducer)
        "current_phase": "research",            # → overwritten (no reducer)
    }
)
```

Each key in the update dict goes to its own channel. `handoff_log` gets appended (because it has `add_messages` reducer), while `current_agent` gets overwritten (no reducer). The `messages` key is only written to if the update dict explicitly includes it.

### 2.4 How `add_messages` Works

**Source:** `.venv/lib/python3.11/site-packages/langgraph/graph/message.py:60-244`

The `add_messages` reducer merges two message lists:
- **Append:** New messages with unique IDs are appended to the existing list
- **Upsert:** Messages with existing IDs overwrite the previous version
- **Remove:** `RemoveMessage` objects remove messages by ID
- **Clear:** `RemoveMessage(id=REMOVE_ALL_MESSAGES)` clears all prior messages

For our use case, all writes produce new messages with unique IDs, so the reducer effectively just **appends**. The upsert and remove semantics are not exercised.

### 2.5 Checkpoint Namespace Isolation

**Source:** `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:593-602`

Each mounted child graph runs under its own checkpoint namespace:

```python
checkpoint_ns = f"{parent_ns}{NS_SEP}{name}" if parent_ns else name
```

Where `name` is the node name (e.g., `"project_manager"`, `"researcher"`). This means each child agent has its own independent checkpoint state under the same project `thread_id`. When a child agent is re-invoked, it **resumes from its own checkpoint** with its full conversation history intact.

---

## 3. End-to-End Message Flow Trace

### 3.1 User Sends First Message

```
User types message in CLI
  → graph.invoke({"messages": [HumanMessage("I want to build...")]}, 
                  config={"configurable": {"thread_id": "proj-123"}})
  → START → receive_user_input
     - Writes HumanMessage to PCG state.messages (via add_messages reducer)
     - Sets project_id = "proj-123"
  → receive_user_input → run_agent (edge)
     - run_agent reads ONLY messages from PCG state (input_schema=_InputAgentState)
     - run_agent invokes PM child graph with input: {"messages": [HumanMessage("I want to build...")]}
     - PM runs in its own checkpoint namespace: "project_manager"
     - PM's full conversation accumulates in PM's OWN messages list (not PCG's)
```

**What's in PCG `messages` at this point:** `[HumanMessage("I want to build...")]`

### 3.2 PM Calls Handoff Tool

```
PM calls deliver_prd_to_harness_engineer(reason="deliver", brief="...", artifact_paths=[...])
  → Middleware hook fires (phase gate check)
  → Gate passes → Command.PARENT emitted:
     Command(graph=Command.PARENT, goto="process_handoff", update={
         "handoff_log": [HandoffRecord(source="pm", target="harness_engineer", ...)],
         "current_agent": "harness_engineer",
         "current_phase": "research",
         "pending_handoff": HandoffRecord(...)
     })
  → ParentCommand bubbles up to PCG level
  → Update dict applied to PCG state channels:
     - handoff_log: [HandoffRecord(...)] appended via add_messages
     - current_agent: "harness_engineer" (overwritten)
     - current_phase: "research" (overwritten)
     - pending_handoff: HandoffRecord(...) (overwritten)
  → Command.PARENT goto="process_handoff" routes to process_handoff node
```

**What's in PCG `messages` at this point:** Still just `[HumanMessage("I want to build...")]`  
**The handoff tool did NOT write to `messages`.** The substantive content (brief, artifacts) went into `handoff_log`.

### 3.3 PCG Invokes Harness Engineer

```
process_handoff
  - Records handoff in handoff_log (already done by Command.PARENT update)
  - Sets pending_handoff = the current HandoffRecord
  - Ensures harness_engineer checkpoint namespace is initialized
  - Prepares invocation payload
→ process_handoff → run_agent (edge)
  - run_agent reads current_agent = "harness_engineer" from PCG state
  - run_agent reads pending_handoff from PCG state
  - run_agent constructs child input: {"messages": [HumanMessage(content=handoff_brief)]}
    where handoff_brief is constructed from pending_handoff.brief + pending_handoff.artifact_paths
  - run_agent invokes HE child graph with this input
  - HE runs in its own checkpoint namespace: "harness_engineer"
  - HE's full conversation accumulates in HE's OWN messages list
```

**What's in PCG `messages` at this point:** Still just `[HumanMessage("I want to build...")]`  
The HE never sees the PCG's `messages` list. It sees only the handoff brief that `run_agent` constructs for it.

### 3.4 HE Returns to PM

```
HE calls return_eval_suite_to_pm(reason="return", brief="...", artifact_paths=[...])
  → Command.PARENT emitted:
     Command(graph=Command.PARENT, goto="process_handoff", update={
         "handoff_log": [HandoffRecord(source="harness_engineer", target="pm", ...)],
         "current_agent": "project_manager",
         "pending_handoff": HandoffRecord(...)
     })
  → process_handoff → run_agent
  - run_agent constructs child input for PM: {"messages": [HumanMessage(content=return_brief)]}
  - PM RESUMES from its own checkpoint with its full history
  - The return_brief is appended to PM's messages as a new HumanMessage
```

**What's in PCG `messages` at this point:** Still just `[HumanMessage("I want to build...")]`  
PM's own messages list now contains: original user message + PM's AI responses + the return brief as a new HumanMessage.

### 3.5 User Sends Follow-Up Message

```
User types another message in CLI
  → graph.invoke({"messages": [HumanMessage("Actually, let me add...")]}, 
                  config={"configurable": {"thread_id": "proj-123"}})
  → START → receive_user_input
     - Appends new HumanMessage to PCG state.messages
  → receive_user_input → run_agent (edge)
     - run_agent reads messages from PCG state
     - PCG messages now contains: [HumanMessage("I want to build..."), HumanMessage("Actually, let me add...")]
     - run_agent invokes PM with these messages
     - PM RESUMES from its own checkpoint
     - The new HumanMessage is appended to PM's existing conversation
```

**What's in PCG `messages` at this point:** `[HumanMessage("I want to build..."), HumanMessage("Actually, let me add...")]`

---

## 4. Analysis of Current State Keys

### 4.1 `messages` — The Ambiguous Conduit

**Current AD description (AD.md:188):**
> Shared key with child agent input schemas; `receive_user_input` writes the initial user message, `run_agent` receives child output here

**Problems:**
1. **"receives child output here" is misleading.** When a child agent calls a handoff tool and emits `Command.PARENT`, the update dict does NOT automatically write to `messages`. The handoff tool's update dict writes to `handoff_log`, `current_agent`, `pending_handoff`, and `current_phase` — not `messages`. The only way child output reaches `messages` is if the child finishes normally (no `Command.PARENT`) and its `_OutputAgentState.messages` flows back through the node's output writers.

2. **What actually accumulates here is unclear.** Based on the trace above, PCG `messages` accumulates only user input messages. Handoff content goes to `handoff_log`. Child agent conversation history stays in the child's own checkpoint namespace. So PCG `messages` is effectively a **user input log**, not a coordination trail or conversation history.

3. **The `add_messages` reducer is mandatory but trivial.** Without it, each new user message would overwrite the previous one (last-write-wins for keys without reducers). The reducer ensures append semantics. But the reducer's full power (upsert, remove) is never exercised.

4. **The "shared key" framing is a LangGraph implementation detail, not a semantic purpose.** A maintainer reading "shared key with child agent input schemas" doesn't understand what `messages` *does* — they learn how it's wired. The purpose should be stated first.

**Resolved semantics:**
- `messages` accumulates **stakeholder input messages only** — every `HumanMessage` the user sends through the CLI
- It is the **conduit** by which `run_agent` passes user input to the PM child graph
- It does NOT accumulate child agent output, handoff briefs, or coordination messages
- The `add_messages` reducer is required to prevent overwrite; its behavior is trivial (append-only)

**Unresolved question:** Should `run_agent` pass the **entire** PCG `messages` list to the child, or just the **latest** user message? If the PM is resuming from its own checkpoint (which already has the full conversation), passing the entire PCG `messages` list would duplicate messages the PM has already seen. This needs an explicit decision.

### 4.2 `project_id` — Clean and Clear

**Current AD description (AD.md:189):**
> Root thread identifier; doubles as project namespace for all child checkpoint namespaces

**Assessment:** High-signal. Purpose is clear. The "doubles as" phrasing communicates the dual role. No changes needed.

### 4.3 `current_phase` — Clean but One Ambiguity

**Current AD description (AD.md:190):**
> Current project phase; middleware reads this for gate dispatch

**Assessment:** Purpose is clear. One ambiguity: the AD says `process_handoff` sets this, but not all handoffs advance the phase. A `return_eval_suite_to_pm` handoff doesn't change the phase. The key should clarify that it's only updated on phase-transition handoffs, not every handoff.

### 4.4 `current_agent` — Clean and Clear

**Current AD description (AD.md:191):**
> Which role graph is currently active; `run_agent` reads this to select the correct mounted child

**Assessment:** High-signal. Purpose and consumer are both stated. No changes needed.

### 4.5 `handoff_log` — Purpose Unclear

**Current AD description (AD.md:192):**
> Append-only log of all handoff records; capped at N records (older summarized)

**Problems:**
1. **Why does this exist?** The AD doesn't state the purpose. Is it for observability? For PCG resumption after crash? For middleware dispatch? The purpose determines whether it should even be in state vs. the Store.

2. **The cap strategy is described but the need for the cap is not justified.** The AD says "unbounded handoff log growth is a persistence concern, not a context-flooding concern" (AD.md:322). But if the purpose is observability, an unbounded log in state is fine (checkpoints handle it). If the purpose is for `run_agent` or middleware to query, then a cap with summarization makes sense. The purpose needs to be stated first.

3. **`add_messages` reducer on `HandoffRecord` objects.** The AD says `handoff_log` uses `add_messages` (AD.md:198). This works because `HandoffRecord` implements the message protocol (has an `id` field). But a maintainer might be confused about why a list of handoff records uses a message reducer. The rationale should be explicit: `add_messages` provides append-without-overwrite semantics, which is exactly what an append-only log needs.

**Resolved semantics:**
- `handoff_log` is the **durable coordination audit trail** — who handed what to whom, when, why, and with which artifacts
- It exists for **observability and crash recovery**: the PCG can reconstruct the full handoff history from this log
- It is NOT read by child agents (they never see it)
- It is NOT used for middleware dispatch (middleware reads the handoff tool call arguments, not the log)
- The `add_messages` reducer is used for its append-only semantics, not because these are messages

### 4.6 `handoff_summary` — Potentially Redundant

**Current AD description (AD.md:193):**
> Prose summary of handoff records that fell off the cap; empty until cap is exceeded

**Problems:**
1. **Only exists as a cap mitigation.** If `handoff_log` moves to the Store in v2 (AD.md:325), this key disappears entirely. Defining a key whose existence depends on a v1 cap strategy feels premature.

2. **"Prose summary" is vague.** Who writes it? The `process_handoff` node? An LLM call? If it's an LLM-generated summary, that introduces non-determinism into a supposedly deterministic coordination layer.

3. **Low signal for maintainers.** A key that's empty most of the time and only appears when a cap is exceeded is hard to reason about.

**Recommendation:** Consider removing this from the v1 schema and handling cap overflow in the implementation spec. The AD should mandate the cap requirement but not enshrine the mitigation strategy as a state key.

### 4.7 `pending_handoff` — Ephemeral in Persistent State

**Current AD description (AD.md:194):**
> The handoff record currently being processed; cleared after `run_agent` completes

**Problems:**
1. **Ephemeral data in persistent state.** This key is set by `process_handoff`, consumed by `run_agent`, and then cleared. It never survives across handoff cycles. Putting ephemeral data in the persistent state schema means it gets checkpointed unnecessarily.

2. **Could be a local variable.** If `run_agent` is a function node (not a subgraph node), it could read `pending_handoff` from the state dict passed into it. But since `process_handoff` and `run_agent` are separate nodes connected by an edge, the only way to pass data between them is through state. So `pending_handoff` in state is actually **required** by the two-node topology.

3. **Is it redundant with `handoff_log[-1]`?** The most recent handoff record in `handoff_log` is the same record as `pending_handoff`. However, `pending_handoff` serves a different purpose: it's the **active** handoff being processed, while `handoff_log[-1]` is the last recorded handoff. After `run_agent` completes and clears `pending_handoff`, the log still has the record. So they're not truly redundant — `pending_handoff` is a cursor, not a copy.

**Assessment:** Required by the two-node topology, but the semantics should be clearer. It's a **cursor** pointing to the handoff currently being executed, not a copy of the data.

---

## 5. The `messages` Key Decision Matrix

The central unresolved question: **what is `messages` for?** There are three viable positions:

### Position A: User Input Log Only

`messages` accumulates only stakeholder `HumanMessage` objects. Handoff tools do NOT write to it. Child agent output does NOT flow back into it.

| Pro | Con |
|---|---|
| Cleanest separation of concerns | If the PCG ever needs to present a readable message trail (e.g., for Studio inspection), it won't have one |
| No ambiguity about what accumulates | The "run_agent receives child output here" claim in the current AD would be incorrect |
| Minimal growth — one message per user input | |

### Position B: User Input + Coordination Trail

`messages` accumulates stakeholder input AND a lightweight coordination message for each handoff cycle (e.g., a `HumanMessage` containing the handoff brief when a child returns).

| Pro | Con |
|---|---|
| PCG has a readable message trail for Studio inspection | `messages` becomes a second representation of handoff data that's already in `handoff_log` |
| "run_agent receives child output here" becomes accurate | Redundancy between `messages` and `handoff_log` |
| | Risk of `messages` growing faster than needed |

### Position C: User Input + Child Output (Full Duplex)

`messages` accumulates everything — user input, child agent output messages, handoff briefs. This is the "default LangGraph behavior" if you don't explicitly control what the child returns.

| Pro | Con |
|---|---|
| Matches the default LangGraph parent-child pattern | Context flooding — the PCG's `messages` would contain fragments of every agent's conversation |
| Simple to implement | Violates the AD's principle of "no specialist messages in shared graph state" (AD.md:170) |

**Recommendation: Position A.** It aligns with the AD's existing principles (no specialist messages in shared state, PCG carries only deterministic coordination data). The "shared key with child input schemas" framing should be reframed: `messages` is the **stakeholder input channel**, and it happens to be the only key shared with `_InputAgentState` by LangGraph's key-name-matching convention.

---

## 6. The `run_agent` Input Construction Decision

A critical implementation decision that the AD should address: **what does `run_agent` pass into the child's `messages` input?**

### Option 1: Pass the Full PCG `messages` List

`run_agent` passes the entire accumulated PCG `messages` list to the child graph.

**Problem:** When the PM is re-invoked after a specialist returns, the PM already has its full conversation in its own checkpoint. Passing the full PCG `messages` list (which only contains user inputs) would **duplicate** messages the PM has already processed. The `add_messages` reducer would upsert-by-ID, but the PM would still see redundant HumanMessages.

### Option 2: Pass Only the Latest User Message

`run_agent` passes only the most recent `HumanMessage` from PCG `messages` that the child hasn't seen yet.

**Problem:** Requires tracking which messages the child has already seen. Adds complexity.

### Option 3: Construct a Single Handoff Brief Message

`run_agent` constructs a **new** `HumanMessage` containing the handoff brief (from `pending_handoff.brief` + `pending_handoff.artifact_paths`) and passes that as the child's input. For the first PM invocation, the handoff brief IS the user's original message.

**This is the cleanest option.** It aligns with:
- The AD's statement that "the receiving agent gets a concise brief plus artifact paths, not a dump of the caller's full conversation" (AD.md:251-253)
- The SubAgentMiddleware pattern, which constructs a single `HumanMessage(content=description)` for subagent invocation (`.reference/libs/deepagents/deepagents/middleware/subagents.py:360`)
- The checkpoint-resume model: when a child is re-invoked, it resumes from its own checkpoint with its full history, and the new HumanMessage is appended to that history

**Recommendation: Option 3.** `run_agent` always constructs a single `HumanMessage` as the child's input. For the first PM invocation, this is the user's message. For subsequent invocations, this is a handoff brief constructed from `pending_handoff`.

---

## 7. Proposed Revised State Schema

### 7.1 Schema Table

| Key | Type | Purpose | Written by | Reducer |
|---|---|---|---|---|
| `messages` | `Annotated[list[AnyMessage], add_messages]` | **Stakeholder input channel.** Accumulates every `HumanMessage` the user sends. Also the only key shared with `_InputAgentState`, so it's the conduit by which `run_agent` passes input to child graphs. | `receive_user_input` | `add_messages` (append-only) |
| `project_id` | `str` | **Project thread identity.** Root `thread_id` for the project; all child checkpoint namespaces derive from this. | `receive_user_input` | None (overwrite) |
| `current_phase` | `Literal["scoping", "research", "architecture", "planning", "development", "acceptance"]` | **Active project phase.** Middleware reads this for gate dispatch. Only updated on phase-transition handoffs. | `process_handoff` | None (overwrite) |
| `current_agent` | `Literal["project_manager", "harness_engineer", "researcher", "architect", "planner", "developer", "evaluator"]` | **Active role selector.** `run_agent` reads this to select which mounted child graph to invoke. | `process_handoff` | None (overwrite) |
| `handoff_log` | `Annotated[list[HandoffRecord], add_messages]` | **Coordination audit trail.** Append-only record of every handoff — who, to whom, why, when, with which artifacts. Used for observability and crash recovery; never read by child agents. | `process_handoff` | `add_messages` (append-only) |
| `pending_handoff` | `HandoffRecord \| None` | **Active handoff cursor.** The handoff record currently being processed by `run_agent`. Set by `process_handoff`, consumed by `run_agent`, cleared on completion. | `process_handoff` (set), `run_agent` (clear) | None (overwrite) |

### 7.2 Removed Keys

| Key | Why removed |
|---|---|
| `handoff_summary` | Cap mitigation strategy, not a state concern. The AD should mandate the cap requirement; the mitigation mechanism (summarize, Store migration, etc.) belongs in the implementation spec. |

### 7.3 Key Invariants

1. **`messages` is the stakeholder input channel.** It accumulates only user `HumanMessage` objects. Handoff tools do NOT write to it. Child agent output does NOT flow back into it. The `add_messages` reducer is required to prevent overwrite when multiple user messages arrive across invocations.

2. **`messages` is the only key visible to child agents.** LangGraph maps parent state to child input by shared key name. The Deep Agent input schema (`_InputAgentState`) defines only `messages`. The implementation MUST set `input_schema=_InputAgentState` on each `add_node` call for mounted child graphs to prevent other PCG keys from leaking into child input.

3. **`run_agent` constructs the child's input, not the PCG.** The `run_agent` node constructs a single `HumanMessage` containing the handoff brief (from `pending_handoff`) and passes it as the child's `messages` input. The child never sees the raw PCG `messages` list.

4. **`handoff_log` uses `add_messages` for append-only semantics.** `HandoffRecord` objects implement the message protocol (have an `id` field) so `add_messages` provides append-without-overwrite. This is a reuse of the reducer for its semantics, not because handoff records are messages.

5. **`pending_handoff` is an execution cursor, not a data store.** It points to the handoff currently being processed. It is set by `process_handoff`, consumed by `run_agent`, and cleared on completion. It is required by the two-node topology (data must flow through state between nodes).

6. **`handoff_log` must be capped.** Unbounded growth bloats checkpoint storage. The cap threshold N is a runtime constant. The mitigation mechanism for records that exceed the cap is delegated to the implementation spec (options: summarize into a string field, migrate to LangGraph Store, or discard with a count marker).

7. **Child agents own their own conversation history.** Each mounted Deep Agent accumulates messages in its own checkpoint namespace. The PCG's `messages` key is not a conversation history — it's an input channel. Child agent message compaction is handled by `SummarizationMiddleware` within each agent, not by the PCG.

---

## 8. Handoff Tool `Command.PARENT` Update Contract

The AD should specify what keys the handoff tool's `Command.PARENT` update dict includes. Based on the analysis:

```python
Command(
    graph=Command.PARENT,
    goto="process_handoff",
    update={
        "handoff_log": [HandoffRecord(
            project_id=...,
            source_agent=...,
            target_agent=...,
            reason=...,
            brief=...,
            artifact_paths=...,
        )],
        "current_agent": <target_agent>,
        "current_phase": <new_phase_if_transition>,  # only on phase transitions
        "pending_handoff": HandoffRecord(...),        # same record as handoff_log entry
    }
)
```

**Key observation:** The update dict does NOT include `messages`. The handoff brief and artifact paths are captured in `handoff_log`, not in `messages`. This is Position A from Section 5.

**PCG-filled fields** (`handoff_id`, `langsmith_run_id`, `status`, `created_at`) are added by `process_handoff`, not by the calling agent. The calling agent populates: `project_id`, `source_agent`, `target_agent`, `reason`, `brief`, `artifact_paths`.

---

## 9. Open Questions for Jason

1. **Should `run_agent` pass the full PCG `messages` list or a single constructed `HumanMessage`?** I recommend the single constructed message (Option 3 from Section 6), but this needs your call.

2. **Should `handoff_summary` be removed from the schema?** I recommend removing it and delegating cap mitigation to the implementation spec. The AD should mandate the cap requirement without enshrining the mitigation as a state key.

3. **Should the handoff tool write anything to `messages`?** I recommend no (Position A from Section 5). The handoff brief is fully captured in `handoff_log`. Adding it to `messages` creates redundancy.

4. **Should the AD specify the `Command.PARENT` update contract?** I recommend yes — the set of keys in the update dict is an architectural decision (what gets communicated), not an implementation detail (how it's serialized).

5. **Should the AD mandate `input_schema=_InputAgentState` on `add_node`?** I recommend yes — without this explicit setting, LangGraph defaults to passing the full parent state schema, which would leak PCG-private keys into child agents.

---

## 10. Source Citations

| Finding | Source |
|---|---|
| `_InputAgentState` defines only `messages` | `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:358-361` |
| `_OutputAgentState` defines `messages` + `structured_response` | `.venv/lib/python3.11/site-packages/langchain/agents/middleware/types.py:364-368` |
| `add_node` defaults to `self.state_schema` when `input_schema` not set | `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:775` |
| Node `input_schema` determines which parent state keys flow into child | `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1308-1309` |
| `Command.PARENT` update dict applied to parent state channels via writers | `.venv/lib/python3.11/site-packages/langgraph/pregel/_retry.py:127-140` |
| `Command.PARENT` causes `_get_updates` to return `None` (no normal output) | `.venv/lib/python3.11/site-packages/langgraph/graph/state.py:1256-1257` |
| `add_messages` reducer: append, upsert-by-ID, remove, clear | `.venv/lib/python3.11/site-packages/langgraph/graph/message.py:60-244` |
| Checkpoint namespace constructed from parent namespace + node name | `.venv/lib/python3.11/site-packages/langgraph/pregel/_algo.py:593-602` |
| `SubAgentMiddleware` constructs single `HumanMessage` for subagent input | `.reference/libs/deepagents/deepagents/middleware/subagents.py:359-361` |
| `SubAgentMiddleware` extracts only final message from subagent output | `.reference/libs/deepagents/deepagents/middleware/subagents.py:345-348` |
| `_EXCLUDED_STATE_KEYS` prevents `messages` from leaking to/from subagents | `.reference/libs/deepagents/deepagents/middleware/subagents.py:125-137` |
| `create_deep_agent` delegates to `create_agent` with middleware stack | `.reference/libs/deepagents/deepagents/graph.py:602-623` |
| `_resolve_schemas` merges middleware state schemas, respects `OmitFromInput`/`OmitFromOutput` | `.venv/lib/python3.11/site-packages/langchain/agents/factory.py:402-444` |
| `ToolNode` handles `Command` returns from tools | `.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:857-899` |
| `Command` type: `graph`, `update`, `resume`, `goto` fields | `.venv/lib/python3.11/site-packages/langgraph/types.py:652-702` |
| AD current state schema | `meta_harness/AD.md:186-201` |
| AD PCG state growth section | `meta_harness/AD.md:318-327` |
| AD handoff protocol | `meta_harness/AD.md:229-277` |
| AD handoff record data contract | `meta_harness/AD.md:947-977` |
| AD PCG topology | `meta_harness/AD.md:205-227` |
| v0.5 `MetaAgentStateSchema` (bloated single-agent state) | `meta_agent_v.0.5/middleware/meta_state.py:38-85` |
