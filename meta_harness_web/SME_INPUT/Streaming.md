---
SME#1
---

**The LangGraph `ns` (namespace) propagation and the

 Deep Agents `SubAgentMiddleware`'s internal tracking are complementary mechanisms and do not overwrite each other.** They work together to provide a comprehensive view of your nested agent architecture in the frontend.

Here's how they interact:

1.  **LangGraph `ns` Propagation:** When you mount your 7 Deep Agent child graphs via `add_node` in your PCG and enable `streamSubgraphs: true`, LangGraph ensures that the `ns` field in the streamed parts accurately reflects the hierarchical path of the currently executing subgraph. This gives you the context of *which* of your 7 child graphs is currently active.

2.  **Deep Agents `SubAgentMiddleware`:** When one of these mounted child Deep Agents *itself* spawns a subagent using its internal `task` tool, the `SubAgentMiddleware` within that child Deep Agent injects specific `toolCall` metadata (including `subagent_type`) into the stream. This metadata identifies the event as a Deep Agent subagent invocation.

The Deep Agents frontend SDK's UI abstractions (`filterSubagentMessages`, `stream.subagents`, `SubagentStreamInterface`, `getSubagentsByMessage`) are designed to interpret both these pieces of information. They will use the `ns` field to understand the parent context (i.e., which of your 7 mounted child graphs is executing) and then, within that context, use the `toolCall` metadata to identify and track the subagents spawned *by that child graph*.

Therefore, you will retain the benefits of:

*   **Automatic coordinator/subagent message separation:** The `toolCall` metadata for subagents spawned by your child graphs will still be processed.
*   **Per-subagent status tracking with `SubagentStreamInterface`:** This interface will utilize the `toolCall` events to track the internal subagents of your mounted Deep Agents.
*   **The `getSubagentsByMessage` linking API:** This will continue to function based on the presence of the `toolCall` metadata.
*   **Built-in `SubagentCard` / `SubagentProgress` component patterns:** These components can correctly display the activity of subagents spawned within your child Deep Agents.

The two abstractions operate at different levels of information within the stream, allowing them to coexist and provide detailed observability for your complex, nested Deep Agent setup.

**Relevant docs:**
- [Subagent streaming (Python)](https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming)
- [Subagent streaming (JavaScript)](https://docs.langchain.com/oss/javascript/deepagents/frontend/subagent-streaming)
- [Subgraphs (Python)](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
---
SME #2
---
**Yes — you can stream a DeepAgent that’s compiled as a subgraph, but you must handle streaming propagation, run/thread mapping, client disconnects/resumable streams, async vs sync execution, and deployment-worker behavior carefully.**

Streaming works by emitting chunks from graph execution (LLM tokens, tool events, subgraph events) via the `client.runs.stream` API (or equivalent JS client). When your DeepAgent is a compiled subgraph inside a parent graph, the runtime will surface subgraph outputs up the parent run, but you must wire the stream consumption and lifecycle (cancellation, resumability, concurrency) correctly so the front end receives timely, correct events.

## How it works (high level)
Subgraphs are executed as part of a parent run; any streaming tokens/events produced inside the subgraph can be forwarded to the parent run stream so the front end can observe them in near real-time. The platform exposes streaming via the Runs streaming endpoint (used by `client.runs.stream`) which yields chunks for token-level updates, tool calls, subagent/subgraph events, and final outputs.

```python
# Python (async) example: stream a run (works for runs that invoke subgraphs)
async for chunk in client.runs.stream(
    thread_id=thread_id,
    assistant_id="my-parent-agent",
    input={"messages": [{"role": "human", "content": "Start subgraph run"}]},
    on_disconnect="cancel",          # cancel run if client disconnects
):
    # handle partial tokens, subgraph events, final outputs
    print(chunk)
```

## Key nuances to know
- Streaming propagation: subgraph nodes can emit intermediate tokens/events which the runtime will surface to the parent run stream — you don’t need a separate stream for each compiled subgraph in most cases, but you must detect and handle subgraph-specific chunk types in your client UI (e.g., markers for "subgraph started", "subgraph output", "subgraph finished").

- Run/thread mapping: each top-level run has a `thread_id`/`run_id`. Subgraph executions are nested inside that run; if you need to map UI components to a specific DeepAgent node, inspect run chunk metadata (the runtime includes node/subgraph identifiers in chunks).

- Cancellation and disconnects: use `on_disconnect="cancel"` when calling `client.runs.stream` (or pass the equivalent option in JS) so background workers cancel runs for disconnected clients. Without this, runs may continue and produce stale work.

- Resumable streams and partial results: enable/respect resumable stream settings for handling timeouts or temporary disconnects. Environment variables like `RESUMABLE_STREAM_TTL_SECONDS` (configurable) control how long a stream can be resumed. If you want clients to reconnect and pick up partial output, configure the resumable stream TTLs appropriately.

- Async vs sync LLM calls inside subgraphs: prefer `ainvoke` (native async) for parallel LLM calls inside a node; `invoke` is sequential and slows long-running subgraphs. If running in a deployment with sync code, set `BG_JOB_ISOLATED_LOOPS=true` to avoid blocking the API, but `ainvoke` still gives better parallelism.

- Worker and infra constraints: streaming depends on healthy background workers. Common failure modes:
  - Redis or Postgres exhaustion can stall workers while the API layer remains healthy (leading to a “zombie” service that accepts requests but produces no stream chunks).
  - Tune Postgres pool sizes and Redis resources, and monitor workers.
  - Use run cancellation strategies (`multitask_strategy="interrupt"`) to avoid queue buildup of stale runs.

- Thread TTL and cleanup: runs/threads are stored durably by default. If you expect many transient runs from streaming subgraphs, configure TTL or cleanup strategies so run data doesn’t accumulate indefinitely.

- Subagent / subgraph-specific streaming patterns: for DeepAgents that spawn subagents (coordinator → subagent), see the platform’s subagent-streaming guide — it covers the coordinator forwarding subagent streams to the root client and special event types you should handle in the UI.

## Front-end considerations
- Use SSE or WebSockets to forward stream chunks from the backend to the browser. The backend should consume `client.runs.stream` and translate chunks into WebSocket/SSE messages including node/subgraph identifiers so the UI can attribute tokens to the correct DeepAgent node.
- Implement UI handling for partial tokens, tool output, and subgraph lifecycle events (start/finish/error).
- Support reconnect/resume: when a user refreshes or reconnects, reopen a stream against the same `thread_id` and rely on resumable stream settings to continue from last state (if configured on the server).

## Deployment and reliability tips
- Set `on_disconnect="cancel"` to avoid leaving zombie runs; increase `RESUMABLE_STREAM_TTL_SECONDS` if you want longer resume windows (defaults may be short).
- Use `BG_JOB_ISOLATED_LOOPS=true` in container env for safer sync code execution; prefer async `ainvoke` for multi-LLM parallelism inside a node.
- Monitor Redis and Postgres metrics; reduce Postgres pool defaults (e.g., for Azure) if you see connection pressure.
- If facing a stuck/zombie deployment, follow the documented checklist: upgrade LangGraph, adjust DB/Redis settings, enable cancellation on disconnect, and as last resort clear Redis after pausing traffic.

## Example: backend bridging stream to WebSocket (pseudo-Python)
```python
# async backend handler pseudocode
async def websocket_run_handler(ws, thread_id, assistant_id):
    # open run stream (resumable + cancel on disconnect)
    try:
        async for chunk in client.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input={},                    # if continuing an existing thread, input may be empty
            on_disconnect="cancel",
        ):
            # normalize chunk (include node/subgraph id, token text, event type)
            await ws.send_json(chunk)      # forward to browser over WebSocket
    except ClientDisconnectedError:
        # client disconnected, run will be cancelled on the server side
        pass
```

**Relevant docs:**

- [Streaming (Python, LangGraph)](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Streaming (JavaScript, LangGraph)](https://docs.langchain.com/oss/javascript/langgraph/streaming)
- [Subagent streaming (DeepAgents frontend)](https://docs.langchain.com/oss/javascript/deepagents/frontend/subagent-streaming)
- [Subgraphs (Python LangGraph)](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [Subagents (JavaScript DeepAgents)](https://docs.langchain.com/oss/javascript/deepagents/subagents)
- [Why is my LangSmith deployment entering a "zombie state"? (support article)](https://support.langchain.com/articles/7079938307-why-is-my-langgraph-deployment-entering-a-zombie-state-where-it-accepts-requests-but-stops-responding)
- [Sync vs Async in LangSmith Deployment: BG_JOB_ISOLATED_LOOPS + invoke vs ainvoke (support article)](https://support.langchain.com/articles/7101951234-sync-vs-async-in-langsmith-deployment-bg-job-isolated-loops-invoke-vs-ainvoke)

---
SME #3
---
**LangGraph supports streaming through subgraphs (your DeepAgents as nodes), with the parent graph's `.stream()` method yielding events from both parent and subgraph execution in a unified stream.**

DeepAgents appear to be built on LangGraph, so they inherit its streaming system. When you compile a DeepAgent graph as a subgraph and add it as a node in a parent graph, calling `.stream()` on the parent yields hierarchical events: parent node updates, then nested subgraph node updates (DeepAgent internals), then back to parent.

This enables two layers of streaming:
- **Parent layer**: Controls overall flow, yields `updates` for entry/exit of subgraph nodes.
- **Subgraph layer**: Streams DeepAgent's internal tokens/steps as nested events.

Key nuances:
- Use `stream_mode=["updates", "values", "tokens"]` on parent `.stream()` to control granularity.
- Subgraph inputs/outputs must match schemas exactly for seamless integration.
- Events are tagged with node names; filter frontend by prefix (e.g., `deepagent_node__internal_node`) to separate layers.
- Persistence/checkpointers shared; use `configurable={"thread_id": ...}` for state across layers.
- For frontend, parse SSE or async iterator, display hierarchically (parent summary + DeepAgent details).
- If deployed to LangSmith Deployment, use LangGraph SDK `client.runs.stream()` with `on_disconnect="cancel"` for robust streaming.

```python
# Define DeepAgent as subgraph
deepagent_subgraph = deepagent_graph.compile(checkpointer=...)

# Parent graph with DeepAgent as node
parent_builder = StateGraph(ParentState)
parent_builder.add_node("deepagent", deepagent_subgraph)  # Subgraph as node
parent_graph = parent_builder.compile()

# Stream parent - gets events from both layers
async for event in parent_graph.astream(
    input, 
    stream_mode=["updates", "tokens"],  # Parent + subgraph tokens
    configurable={"thread_id": "abc"}
):
    # event: {'node_1': ..., 'deepagent__llm': {'messages': [AIMessageChunk(...)]}, ...}
    print(event)
```

In frontend, use SSE transport or React hooks like `useStream` (from DeepAgents docs), filtering subagent events.

**Relevant docs:**
- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [Streaming API](https://docs.langchain.com/langsmith/streaming)
