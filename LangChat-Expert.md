**Mostly — your approach is on the right track, but there are three concrete fixes needed for correctness and to match the deepagents expectations.**

You construct the right pieces (dynamic prompt, meta-state, summarization tool middleware, memory, checkpointer/store) and you use the SDK `FilesystemBackend` for workspace paths — that matches the docs. The issues to address are: (1) the `SummarizationMiddleware` instance must be added to the middleware chain (the `SummarizationToolMiddleware` depends on it), (2) your `StoreBackend` currently ignores the wrapped `InMemoryStore` and uses an internal `_kv`, and (3) the agent expects an SDK-compatible composite backend (or the actual SDK backend object) for correct routing of `/memories/` vs ephemeral state.

```python

# 1) Add the SummarizationMiddleware instance before the SummarizationToolMiddleware:

summarization_mw = SummarizationMiddleware(model=cfg.model_name, backend=backend)

summarization_tool_mw = SummarizationToolMiddleware(summarization_mw)

explicit_middleware = [

    dynamic_prompt_mw,     # 0. Dynamic system prompt (MUST be first)

    meta_state_mw,         # 1. Extends state schema

    summarization_mw,      # <-- required: SummarizationMiddleware must be present

    summarization_tool_mw, # 8. Agent-controlled compact_conversation

    memory_mw,             # 9. Per-agent [AGENTS.md](http://AGENTS.md) loading

    tool_error_mw,         # 10. ToolError (catches tool exceptions)

]

```

## StoreBackend fix

`StoreBackend` should delegate to the provided `InMemoryStore` instead of keeping a separate `_kv` dict. Use the store API (method names below are illustrative — adjust if your `InMemoryStore` uses different names):

```python

class StoreBackend:

    def **init**(self, store: InMemoryStore | None = None) -> None:

        [self.store](http://self.store) = store or InMemoryStore()

    def get(self, key: str) -> Any:

        # use the real store API instead of a private dict

        return [self.store](http://self.store).get(key)    # adjust to actual API if different

    def put(self, key: str, value: Any) -> None:

        [self.store](http://self.store).put(key, value)    # adjust to actual API if different

    def delete(self, key: str) -> None:

        [self.store](http://self.store).delete(key)        # adjust to actual API if different

```

If `InMemoryStore` is not a simple key/value object (e.g., uses `set`, `get_item`, or namespaced methods), call the correct methods — the important part is not to shadow the passed `InMemoryStore` with an independent dict.

## Backend routing / SDK compatibility

The deepagents FilesystemMiddleware expects either the SDK `CompositeBackend` or an object that matches the SDK backend interface. Options:

- Preferred: build/pass the SDK `CompositeBackend` that maps `/memories/` to a store backend and default to state backend. This ensures filesystem tools persist files under `/memories/`.

```python

# conceptual example — adjust constructors to SDK API

from deepagents.backends import CompositeBackend, StateBackend as SdkStateBackend, StoreBackend as SdkStoreBackend, FilesystemBackend as SdkFilesystemBackend

sdk_fs = SdkFilesystemBackend(root_dir=str(repo_root), virtual_mode=True)

# create SDK store backend bound to your InMemoryStore (pseudocode; adapt to SDK)

sdk_store = SdkStoreBackend(store=create_store())

composite = CompositeBackend(default=SdkStateBackend(), routes={"/memories/": sdk_store})

graph = create_deep_agent(

    model=cfg.model_name,

    tools=LANGCHAIN_TOOLS,

    system_prompt=system_prompt,

    middleware=explicit_middleware,

    subagents=subagents,

    checkpointer=checkpointer,

    store=create_store(),

    backend=composite,    # pass SDK-compatible composite backend

    interrupt_on=interrupt_on,

    skills=skills_dirs,

    name="meta-agent-orchestrator",

)

```

- If you keep your wrapper `CompositeBackend`, expose and pass the underlying SDK backend instance (for example via a `.sdk_backend` property) or implement exactly the same interface the SDK expects. Otherwise the FilesystemMiddleware/MemoryMiddleware may not route or persist correctly.

## Other suggestions

- Thread-safety: your `StateBackend` uses a plain dict. If multiple threads may access it, use a lock or thread-local storage.
- Naming: avoid naming your wrapper `CompositeBackend` if you also use the SDK's `CompositeBackend` to reduce confusion.
- Checkpointer/store: returning `MemorySaver()` and `InMemoryStore()` for development is fine; for production move to durable backends (Postgres, disk, etc.).

Relevant docs:

- [Deep Agents Middleware](%5Bhttps://docs.langchain.com/oss/python/deepagents/middleware%5D(https://docs.langchain.com/oss/python/deepagents/middleware))
- [Deep Agents Middleware — Short-term vs. long-term filesystem](%5Bhttps://docs.langchain.com/oss/python/deepagents/middleware#short-term-vs-long-term-filesystem%5D(https://docs.langchain.com/oss/python/deepagents/middleware#short-term-vs-long-term-filesystem))
- [Deep Agents Backends](%5Bhttps://docs.langchain.com/oss/python/deepagents/backends%5D(https://docs.langchain.com/oss/python/deepagents/backends))