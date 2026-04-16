# Deep Agents Frontend SDK — Sandbox Pattern

> Source: https://docs.langchain.com/oss/python/deepagents/frontend/sandbox

## Architecture (3 Layers)

1. **Deep agent with sandbox backend** — agent gets filesystem tools (`read_file`, `write_file`, `edit_file`, `execute`) automatically from the sandbox
2. **Custom API server** — FastAPI app exposed via `langgraph.json`'s `http.app` field, providing file browsing endpoints
3. **IDE frontend** — Three-panel layout (file tree, code/diff viewer, chat) that syncs files in real time

## Sandbox Scoping Strategies

| Scope | Description | Use Case |
|---|---|---|
| **Thread-scoped** (recommended) | Each LangGraph thread gets its own sandbox, ID stored in thread metadata | Production apps — isolation per conversation |
| **Agent-scoped** | All threads under same assistant share one sandbox | Persistent project environments |
| **User-scoped** | Each user gets their own sandbox across all threads | Multi-tenant apps |
| **Session-scoped** | Frontend generates session ID, no persistence across browser sessions | Demos / prototyping |

## Backend Setup

### Sandbox Provider
```python
from deepagents import create_deep_agent
from deepagents.sandbox import LangSmithSandbox  # or DaytonaSandbox, etc.

sandbox = LangSmithSandbox.create()
agent = create_deep_agent(model="anthropic:claude-sonnet-4-5", backend=sandbox)
```

### Per-Thread Sandbox Resolution (Recommended)
```python
from deepagents import create_deep_agent
from deepagents.sandbox import LangSmithSandbox
from langgraph.config import get_config

sandbox = LangSmithSandbox(
    resolve=lambda: get_or_create_sandbox_for_thread(
        get_config()["configurable"]["thread_id"]
    ),
)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-5", backend=sandbox)
```

### Custom File Browsing API (FastAPI)
```python
# src/api/server.py
from fastapi import FastAPI, Query, Path
app = FastAPI()

@app.get("/api/sandbox/{thread_id}/tree")
async def list_tree(thread_id: str = Path(...), path: str = Query("/app")):
    sandbox = await get_or_create_sandbox_for_thread(thread_id)
    result = await sandbox.aexecute(f"find {path} -printf '%y\\t%s\\t%p\\n' 2>/dev/null | sort")
    # Parse and return entries...

@app.get("/api/sandbox/{thread_id}/file")
async def read_file(thread_id: str = Path(...), path: str = Query(...)):
    sandbox = await get_or_create_sandbox_for_thread(thread_id)
    results = await sandbox.adownload_files([path])
    return {"path": path, "content": results[0].content.decode()}
```

### langgraph.json Configuration
```json
{
  "graphs": { "coding_agent": "./src/agents/my_agent.py:agent" },
  "env": ".env",
  "http": { "app": "./src/api/server.py:app" }
}
```

## Frontend Patterns

### Thread Creation & Persistence
- Create LangGraph thread on page load
- Persist `threadId` in `sessionStorage` for page reload reconnection
- Use `stream.switchThread(null)` + clear stored ID for "new thread"

### Real-Time File Sync
- Watch `stream.messages` for `ToolMessage` instances from file-mutating tools
- On `write_file` / `edit_file` completion → refresh that specific file
- On `execute` completion → refresh everything (shell can modify any file)
- Snapshot file contents before each agent run to detect changes

### Three-Panel IDE Layout

| Panel | Width | Purpose |
|---|---|---|
| File tree | Fixed (208px) | Browse sandbox files, change indicators |
| Code / Diff | Flexible | View file content or unified diff |
| Chat | Fixed (320px) | Interact with the agent |

### Diff Libraries by Framework

| Framework | Library | Component |
|---|---|---|
| React | `@pierre/diffs` | `<FileDiff>` with `parseDiffFromFile` |
| Vue | `@git-diff-view/vue` | `<DiffView>` with `generateDiffFile` |
| Svelte | `@git-diff-view/svelte` | `<DiffView>` with `generateDiffFile` |
| Angular | `ngx-diff` | `<ngx-unified-diff>` with `[before]` and `[after]` |

## Key Insights

1. **`LangSmithSandbox` is a first-class sandbox provider** — implements `SandboxBackendProtocol`, gives agent all filesystem + execute tools automatically
2. **`resolve=` lambda pattern** enables per-thread sandbox resolution at runtime via `get_config()`
3. **Custom FastAPI routes served alongside LangGraph API** via `http.app` in `langgraph.json`
4. **Real-time file sync** is achieved by watching tool messages in the stream, not polling
5. **Seed the sandbox** with `uploadFiles` before agent runs — starting from empty is disorienting
6. **Default to diff view** for changed files — that's what users care about
7. **Filter `node_modules`** from file tree

## Best Practices
- Use thread-scoped sandboxes for production
- Share `getOrCreateSandboxForThread` between agent backend and API server
- Persist `threadId` in `sessionStorage`
- Sync files on every relevant tool call, not just when run finishes
- Show compact tool results for read-only operations
