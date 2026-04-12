# DeepWiki Q&A with Code Context for Repository: langchain-ai/langgraph
## Q1
in langgraph, is there a way for subgraphs to decide at whim to communicate with another subgraph?
### Answer
The user is asking about subgraph communication in LangGraph - specifically whether subgraphs can communicate with each other directly/at will. Let me search for relevant information about subgraphs and their communication patterns in LangGraph.

Now I have a comprehensive understanding of how subgraph communication works in LangGraph. Let me summarize the key findings:

1. **Direct peer-to-peer communication between sibling subgraphs is not supported** - subgraphs can't directly call each other at the same level.

2. **The main communication mechanisms are:**
   - **Via shared parent state**: Subgraphs communicate indirectly through the parent graph's shared state channels.
   - **`Command.PARENT`**: A subgraph node can return `Command(graph=Command.PARENT, goto="some_node", update={...})` to jump to a node in the *immediate parent* graph and update parent state. This is the closest thing to "at-whim" communication, but it goes UP to the parent, not sideways to a sibling.
   - **Direct `.invoke()` calls**: A node function (which could be inside a subgraph) can directly call another compiled subgraph's `.invoke()` method. This is the most flexible approach - a node inside subgraph A can call subgraph B's `.invoke()` directly.
   - **`Send` API**: For fan-out patterns, a conditional edge can return `Send` objects to dispatch to multiple subgraph nodes in parallel.

3. **There's no native "sideways" communication** - subgraphs in LangGraph are hierarchical. Communication flows up (via `Command.PARENT`) or down (via state projection), not laterally between siblings.

The closest to "at whim" communication between subgraphs would be:
1. A node inside one subgraph directly calling another subgraph's `.invoke()` - this works but is sequential and the calling subgraph must have a reference to the other.
2. Using `Command.PARENT` to bubble up to the parent and then route to another subgraph node.


There is no native "sideways" peer-to-peer communication between sibling subgraphs in LangGraph. The execution model is strictly hierarchical (parent → child). However, there are a few patterns that approximate what you're describing:

---

## 1. Direct `.invoke()` call from a node (most flexible)

A node function *inside* one subgraph can hold a reference to another compiled subgraph and call it directly:

```python
def node_in_subgraph_a(state):
    # subgraph_b is captured from outer scope
    result = subgraph_b.invoke({"some_key": state["value"]})
    return {"output": result["result"]}
```

This is demonstrated in `test_multiple_subgraphs` — a parent node sequentially calls two independent subgraphs: langgraph:6697-6700 

The calling subgraph must hold a Python reference to the other. There's no "discovery" mechanism — it's just a direct function call.

---

## 2. `Command(graph=Command.PARENT, ...)` — bubble up and reroute

A node inside a subgraph can return a `Command` with `graph=Command.PARENT` to escape to the **immediate parent** graph, update parent state, and redirect execution to a different node (which could be another subgraph node): langgraph:652-678 

```python
def node_in_subgraph_a(state):
    return Command(
        graph=Command.PARENT,
        goto="subgraph_b_node",       # a node in the parent graph
        update={"shared_key": "val"},
    )
```

Internally this raises a `ParentCommand` exception that the parent's Pregel loop catches and processes: langgraph:1548-1551 

A real test showing this pattern — a child node jumps to a parent node, bypassing the rest of its own subgraph: langgraph:8266-8299 

`Command.PARENT` only targets the **closest** parent, not an arbitrary ancestor. For deeply nested graphs, each level must propagate it upward. langgraph:8304-8377 

---

## 3. Shared parent state (indirect)

The standard pattern: both subgraphs share keys with the parent state. Subgraph A writes to a shared key, the parent routes to subgraph B, which reads it. No direct link between A and B — the parent mediates everything.

---

## Summary

| Pattern | Direction | "At whim"? |
|---|---|---|
| Direct `.invoke()` in a node | Peer (via Python ref) | Yes, but sequential and requires a captured reference |
| `Command(graph=Command.PARENT, goto=...)` | Up to parent, then rerouted | Yes, but only targets the immediate parent graph |
| Shared parent state + edges | Via parent mediation | No — requires pre-wired edges |

The closest to "at whim" is the direct `.invoke()` approach — a node in any subgraph can call any other compiled graph it has a reference to, at any point during its execution. `Command.PARENT` is the other option if you want to redirect the parent's control flow dynamically.
### Citations
**File:** libs/langgraph/tests/test_pregel.py (L6697-6700)
```python
    def parent_node(state):
        result = sub_graph_1.invoke({"sub_counter": state["parent_counter"]})
        other_result = sub_graph_2.invoke({"other_sub_counter": result["sub_counter"]})
        return {"parent_counter": other_result["other_sub_counter"]}
```
**File:** libs/langgraph/tests/test_pregel.py (L8266-8299)
```python
    def node_a_child(state):
        return {"dialog_state": ["a_child_state"]}

    def node_b_child(state):
        return Command(
            graph=Command.PARENT,
            goto="node_b_parent",
            update={"dialog_state": ["b_child_state"]},
        )

    sub_builder = StateGraph(State)
    sub_builder.add_node(node_a_child)
    sub_builder.add_node(node_b_child)
    sub_builder.add_edge(START, "node_a_child")
    sub_builder.add_edge("node_a_child", "node_b_child")
    sub_graph = sub_builder.compile(checkpointer=subgraph_persist)
    if with_timeout in ("inner", "both"):
        sub_graph.step_timeout = 1

    def node_b_parent(state):
        return {"dialog_state": ["node_b_parent"]}

    main_builder = StateGraph(State)
    main_builder.add_node(node_b_parent)
    main_builder.add_edge(START, "subgraph_node")
    main_builder.add_node("subgraph_node", sub_graph, destinations=("node_b_parent",))
    main_graph = main_builder.compile(sync_checkpointer, name="parent")
    if with_timeout in ("outer", "both"):
        main_graph.step_timeout = 1

    config = {"configurable": {"thread_id": 1}}

    assert main_graph.invoke(input={"dialog_state": ["init_state"]}, config=config) == {
        "dialog_state": ["init_state", "b_child_state", "node_b_parent"]
```
**File:** libs/langgraph/tests/test_pregel.py (L8304-8377)
```python
def test_parent_command_goto_deeply_nested(
    sync_checkpointer: BaseCheckpointSaver,
    subgraph_persist: bool,
) -> None:
    """Test Command.PARENT in a 3-level nested subgraph.

    Command.PARENT should jump to sub_child_3 in the immediate parent (sub_graph).

    Note: With operator.add, subgraph state (including its input) is merged with
    parent state, causing the input to appear multiple times. This is expected.
    """

    class State(TypedDict):
        dialog_state: Annotated[list[str], operator.add]

    # Level 3: Deepest subgraph that issues Command.PARENT
    def sub_sub_child_node(state):
        # Jump to immediate parent (sub_graph)
        return Command(
            graph=Command.PARENT,
            goto="sub_child_3",
            update={"dialog_state": ["sub_sub_child"]},
        )

    sub_sub_builder = StateGraph(State)
    sub_sub_builder.add_node("sub_sub_child", sub_sub_child_node)
    sub_sub_builder.add_edge(START, "sub_sub_child")
    sub_sub_graph = sub_sub_builder.compile(
        name="sub_sub_graph", checkpointer=subgraph_persist
    )

    # Level 2: Middle subgraph containing Level 3
    def sub_child_1(state):
        return {"dialog_state": ["sub_child_1"]}

    def sub_child_3(state):
        return {"dialog_state": ["sub_child_3"]}

    sub_builder = StateGraph(State)
    sub_builder.add_node("sub_child_1", sub_child_1)
    sub_builder.add_node("sub_child_2", sub_sub_graph, destinations=("sub_child_3",))
    sub_builder.add_node("sub_child_3", sub_child_3)
    sub_builder.add_edge(START, "sub_child_1")
    sub_builder.add_edge("sub_child_1", "sub_child_2")
    sub_graph = sub_builder.compile(name="sub_graph", checkpointer=subgraph_persist)

    # Level 1: Main graph containing Level 2
    def child_1(state):
        return {"dialog_state": ["child_1"]}

    builder = StateGraph(State)
    builder.add_node("child_1", child_1)
    builder.add_node("child_2", sub_graph)
    builder.add_edge(START, "child_1")
    builder.add_edge("child_1", "child_2")
    graph = builder.compile(name="main_graph", checkpointer=sync_checkpointer)

    config = {"configurable": {"thread_id": 1}}

    result = graph.invoke(input={"dialog_state": ["init"]}, config=config)

    # Command.PARENT from sub_sub_child jumps to sub_child_3 in immediate parent
    # State duplication occurs due to operator.add merging behavior
    assert result == {
        "dialog_state": [
            "init",
            "child_1",
            "init",
            "child_1",
            "sub_child_1",
            "sub_sub_child",
            "sub_child_3",
        ]
    }
```
**File:** libs/langgraph/langgraph/types.py (L652-678)
```python
@dataclass(**_DC_KWARGS)
class Command(Generic[N], ToolOutputMixin):
    """One or more commands to update the graph's state and send messages to nodes.

    Args:
        graph: Graph to send the command to. Supported values are:

            - `None`: the current graph
            - `Command.PARENT`: closest parent graph
        update: Update to apply to the graph's state.
        resume: Value to resume execution with. To be used together with [`interrupt()`][langgraph.types.interrupt].
            Can be one of the following:

            - Mapping of interrupt ids to resume values
            - A single value with which to resume the next interrupt
        goto: Can be one of the following:

            - Name of the node to navigate to next (any node that belongs to the specified `graph`)
            - Sequence of node names to navigate to next
            - `Send` object (to execute a node with the input provided)
            - Sequence of `Send` objects
    """

    graph: str | None = None
    update: Any | None = None
    resume: dict[str, Any] | Any | None = None
    goto: Send | Sequence[Send | N] | N = ()
```
**File:** libs/langgraph/langgraph/graph/state.py (L1548-1551)
```python
    for command in commands:
        if command.graph == Command.PARENT:
            raise ParentCommand(command)

```
## Q2
well. My unique situation is that I have multiple subgraphs that are all compiled as deep agents. Because they are all compiled as deep agents, they are all their own unique compiled graph. I am orchestrating roughly five deep agents, and I need them to be able to communicate with each other as peers (peer-to-peer). How do I facilitate this?
### Answer
The user has multiple compiled subgraphs (deep agents) that they want to communicate peer-to-peer. Based on the previous conversation, I know the options. Let me think about what patterns would work best for this use case.

The user has ~5 compiled graphs (agents) and wants them to communicate as peers. Let me search for relevant patterns in LangGraph for multi-agent communication, particularly:
1. The `Send` API for fan-out
2. Multi-agent patterns
3. Any supervisor/orchestrator patterns

Let me search for multi-agent orchestration patterns in LangGraph.

Now I have a comprehensive picture. The user has 5 deep agents (each a compiled graph) and wants them to communicate peer-to-peer. Let me synthesize the best architectural patterns for this use case.

The key patterns I've found:

1. **Supervisor/orchestrator pattern** - A parent graph that routes between agents using `Command(goto=...)`. Each agent is a node in the parent graph, and they can hand off to each other via `Command.PARENT` + the parent routes to the next agent.

2. **Direct `.invoke()` calls** - Any agent can call any other agent directly if it has a Python reference to it.

3. **Agents as tools** - Each agent can be wrapped as a tool that another agent can call via its tool-calling mechanism.

The most natural "peer-to-peer" pattern in LangGraph for compiled agents is:

**Option A: Supervisor/orchestrator parent graph**
- Create a parent `StateGraph` with each of the 5 agents as nodes
- Use `Command(graph=Command.PARENT, goto="agent_X", update={...})` from within any agent to hand off to another agent
- The parent graph mediates all routing

**Option B: Agents as tools (supervisor with tools)**
- One agent acts as a supervisor/orchestrator
- The other agents are wrapped as tools that the supervisor can call
- The supervisor's LLM decides which agent to call

**Option C: Direct `.invoke()` calls**
- Each agent holds references to the others
- Any agent can call any other directly during its execution
- This is truly peer-to-peer but sequential

The most idiomatic LangGraph approach for "peer-to-peer" multi-agent communication is the **supervisor pattern** where:
1. All 5 agents are nodes in a parent graph
2. Each agent can return `Command(graph=Command.PARENT, goto="agent_N", update={...})` to hand off to any other agent
3. The parent graph needs `destinations=("agent_1", "agent_2", ...)` declared when adding each subgraph node

This is the closest to true peer-to-peer because any agent can dynamically decide to hand off to any other agent at any time.

Let me explain this clearly.


For 5 independent compiled agents that need to communicate as peers, the canonical LangGraph approach is the **supervisor/orchestrator parent graph** pattern, where each agent is a node and any agent can hand off to any other via `Command(graph=Command.PARENT, goto=...)`.

---

## The recommended pattern: shared parent + `Command.PARENT` handoffs

Each agent node can dynamically route to any sibling by bubbling up to the parent and redirecting:

```python
# Inside agent_A's final node:
def agent_a_exit(state):
    # Decide at runtime to hand off to agent_C
    return Command(
        graph=Command.PARENT,
        goto="agent_c",          # name of the node in the parent graph
        update={"messages": [...], "handoff_data": "..."},
    )
```

The parent graph wires all 5 agents together and declares the possible destinations for each:

```python
parent = StateGraph(SharedState)
parent.add_node("agent_a", agent_a_graph, destinations=("agent_b", "agent_c", "agent_d", "agent_e"))
parent.add_node("agent_b", agent_b_graph, destinations=("agent_a", "agent_c", "agent_d", "agent_e"))
# ... same for c, d, e
parent.add_edge(START, "agent_a")
orchestrator = parent.compile(checkpointer=checkpointer)
```

The `destinations` parameter is required when a subgraph node uses `Command.PARENT` to jump to sibling nodes — it tells the parent graph which nodes are reachable from that subgraph. langgraph:8288-8292 

The `Command.PARENT` mechanism raises a `ParentCommand` exception that the parent's Pregel loop catches and uses to redirect execution: langgraph:1548-1551 

---

## What this looks like end-to-end

```
orchestrator (parent graph)
├── agent_a  ──┐
├── agent_b  ──┤  any of these can Command.PARENT → goto any other
├── agent_c  ──┤
├── agent_d  ──┤
└── agent_e  ──┘
```

Any agent, at any point in its internal execution, can return:

```python
Command(
    graph=Command.PARENT,
    goto="agent_d",
    update={"messages": [...], "context": "..."},
)
```

This is truly "at whim" — the decision is made dynamically inside the agent's logic, not by pre-wired edges. langgraph:652-678 

---

## Key constraints to be aware of

1. **Shared state schema**: All 5 agents and the parent must share (or project to/from) a common state schema. The `update` dict in `Command` writes to the **parent's** state keys.

2. **`destinations` must be declared**: When you `add_node("agent_a", agent_a_graph, destinations=(...))`, you must list every sibling node that `agent_a` might `goto`. This is a compile-time declaration even though the routing is dynamic at runtime. langgraph:8288-8292 

3. **Only jumps to the immediate parent**: `Command.PARENT` targets the closest parent graph, not an arbitrary ancestor. Since your agents are all one level deep in the orchestrator, this is exactly what you want.

4. **No cycles without a termination condition**: If agents can freely hand off to each other, you need a way to reach `END` — either an agent returns normally (no `Command.PARENT`) or you route to an `END` node.

---

## Alternative: agents as tools (if you want LLM-driven routing)

If you want an LLM to decide which agent to call, wrap each agent as a tool:

```python
def call_agent_b(query: str) -> str:
    """Delegate to Agent B for X tasks."""
    result = agent_b_graph.invoke({"messages": [("user", query)]})
    return result["messages"][-1].content
```

Then give `agent_a` a `ToolNode` containing `[call_agent_b, call_agent_c, ...]`. This is the "supervisor with tools" pattern referenced in the codebase. langgraph:1093-1101 langgraph:1127-1135 

The tradeoff: the tool approach is sequential (one agent calls another and waits), while the `Command.PARENT` approach transfers control entirely (the calling agent stops, the target agent takes over).
### Citations
**File:** libs/langgraph/tests/test_pregel.py (L8288-8292)
```python
    main_builder = StateGraph(State)
    main_builder.add_node(node_b_parent)
    main_builder.add_edge(START, "subgraph_node")
    main_builder.add_node("subgraph_node", sub_graph, destinations=("node_b_parent",))
    main_graph = main_builder.compile(sync_checkpointer, name="parent")
```
**File:** libs/langgraph/langgraph/graph/state.py (L1548-1551)
```python
    for command in commands:
        if command.graph == Command.PARENT:
            raise ParentCommand(command)

```
**File:** libs/langgraph/langgraph/types.py (L652-678)
```python
@dataclass(**_DC_KWARGS)
class Command(Generic[N], ToolOutputMixin):
    """One or more commands to update the graph's state and send messages to nodes.

    Args:
        graph: Graph to send the command to. Supported values are:

            - `None`: the current graph
            - `Command.PARENT`: closest parent graph
        update: Update to apply to the graph's state.
        resume: Value to resume execution with. To be used together with [`interrupt()`][langgraph.types.interrupt].
            Can be one of the following:

            - Mapping of interrupt ids to resume values
            - A single value with which to resume the next interrupt
        goto: Can be one of the following:

            - Name of the node to navigate to next (any node that belongs to the specified `graph`)
            - Sequence of node names to navigate to next
            - `Send` object (to execute a node with the input provided)
            - Sequence of `Send` objects
    """

    graph: str | None = None
    update: Any | None = None
    resume: dict[str, Any] | Any | None = None
    goto: Send | Sequence[Send | N] | N = ()
```
**File:** libs/prebuilt/langgraph/prebuilt/tool_node.py (L1093-1101)
```python
        # GraphInterrupt is a special exception that will always be raised.
        # It can be triggered in the following scenarios,
        # Where GraphInterrupt(GraphBubbleUp) is raised from an `interrupt` invocation
        # most commonly:
        # (1) a GraphInterrupt is raised inside a tool
        # (2) a GraphInterrupt is raised inside a graph node for a graph called as a tool
        # (3) a GraphInterrupt is raised when a subgraph is interrupted inside a graph
        #     called as a tool
        # (2 and 3 can happen in a "supervisor w/ tools" multi-agent architecture)
```
**File:** libs/prebuilt/tests/test_react_agent.py (L1127-1135)
```python
    # Add subgraphs as tools

    def addition(a: int, b: int):
        """Add two numbers"""
        return add_subgraph.invoke({"a": a, "b": b})["result"]

    def multiplication(a: int, b: int):
        """Multiply two numbers"""
        return multiply_subgraph.invoke({"a": a, "b": b})["result"]
```
## Q3
So, does this parent have to be, can this parent be, the graph itself essentially, the orchestration layer, or do I have to compile the parent as its own agent?
### Answer
The user is asking whether the parent/orchestrator graph needs to be compiled as its own agent (with LLM, tools, etc.) or if it can just be a plain StateGraph that acts purely as a routing/orchestration layer. This is a conceptual question about LangGraph's architecture.

The answer is: the parent does NOT need to be an agent itself. It can be a plain `StateGraph` that just wires the subgraphs together and handles routing. It's just a compiled graph that acts as a coordinator/router, not necessarily an LLM-backed agent.

Let me verify this by looking at how the parent graph is constructed in the test examples and any multi-agent examples.

The user is asking a simple conceptual question: does the parent/orchestrator graph need to be compiled as its own agent (with LLM, tools, etc.), or can it just be a plain StateGraph that acts as a routing layer?

The answer is clear from what I already know and the search results:

The parent does NOT need to be an agent. It can be a plain `StateGraph` that just wires the subgraphs together. The `StateGraph.compile()` method doesn't require any LLM or agent-specific components - it just needs nodes and edges. The parent is just a compiled graph that acts as a coordinator/router.

The examples in the codebase show parent graphs that are plain `StateGraph` instances with no LLM involved - they just have nodes and edges that route between subgraphs.

I have enough information to answer this directly without more searches.


The parent does **not** need to be an agent. It can be a plain `StateGraph` with no LLM, no tools, and no agent logic — just nodes and edges that wire your five agents together.

`StateGraph.compile()` has no requirement for an LLM or any agent-specific component: langgraph:1038-1048 

The parent is just a compiled graph that acts as a router/coordinator. For example, a minimal pure-routing parent looks like:

```python
orchestrator = StateGraph(SharedState)
orchestrator.add_node("agent_a", agent_a_graph, destinations=("agent_b", "agent_c", "agent_d", "agent_e"))
orchestrator.add_node("agent_b", agent_b_graph, destinations=("agent_a", "agent_c", "agent_d", "agent_e"))
orchestrator.add_node("agent_c", agent_c_graph, destinations=("agent_a", "agent_b", "agent_d", "agent_e"))
orchestrator.add_node("agent_d", agent_d_graph, destinations=("agent_a", "agent_b", "agent_c", "agent_e"))
orchestrator.add_node("agent_e", agent_e_graph, destinations=("agent_a", "agent_b", "agent_c", "agent_d"))
orchestrator.add_edge(START, "agent_a")  # or whichever starts first
compiled = orchestrator.compile(checkpointer=checkpointer)
```

The parent graph here has zero intelligence of its own — it's purely structural. All routing decisions are made *inside* the agents themselves via `Command(graph=Command.PARENT, goto="agent_x", ...)`. The parent just provides the namespace in which those `goto` targets are resolved.

The test examples confirm this pattern — parent graphs are plain `StateGraph` instances with simple nodes and edges, no LLM involved: langgraph:6702-6707 

That said, you *can* also make the parent an LLM-backed supervisor agent if you want a central brain deciding which agent runs next — but that's optional and a separate architectural choice. For true peer-to-peer (agents deciding for themselves who to hand off to), a dumb routing parent is the right call.
### Citations
**File:** libs/langgraph/langgraph/graph/state.py (L1038-1048)
```python
    def compile(
        self,
        checkpointer: Checkpointer = None,
        *,
        cache: BaseCache | None = None,
        store: BaseStore | None = None,
        interrupt_before: All | list[str] | None = None,
        interrupt_after: All | list[str] | None = None,
        debug: bool = False,
        name: str | None = None,
    ) -> CompiledStateGraph[StateT, ContextT, InputT, OutputT]:
```
**File:** libs/langgraph/tests/test_pregel.py (L6702-6707)
```python
    parent_graph = (
        StateGraph(ParentState)
        .add_node(parent_node)
        .add_edge(START, "parent_node")
        .compile(checkpointer=sync_checkpointer)
    )
```