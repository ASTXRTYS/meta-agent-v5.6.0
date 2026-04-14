# LangSmith Agent Server API Reference

> Source: https://docs.langchain.com/langsmith/server-api-ref

## Overview

The Agent Server API reference is available within each deployment at the `/docs` endpoint (e.g., `http://localhost:8124/docs`).

## API Endpoint Groups

| Group | Purpose |
|---|---|
| **Assistants** | Configured instances of a graph |
| **Threads** | Accumulated outputs of a group of runs |
| **Thread Runs** | Invocations of a graph/assistant on a thread |
| **Stateless Runs** | Invocations with no state persistence |
| **Crons** | Periodic runs on a schedule |
| **Store** | Persistent key-value store for long-term memory |
| **A2A** | Agent-to-Agent Protocol endpoints |
| **MCP** | Model Context Protocol endpoints |
| **System** | Health checks and server info |

## Authentication

For LangSmith deployments, pass the `X-Api-Key` header with a valid LangSmith API key:

```bash
curl --request POST \
  --url http://localhost:8124/assistants/search \
  --header 'Content-Type: application/json' \
  --header 'X-Api-Key: LANGSMITH_API_KEY' \
  --data '{"metadata": {}, "limit": 10, "offset": 0}'
```

## Key Insights

1. **Self-documenting API** — each deployment serves its own API docs at `/docs`
2. **Thread-based state model** — Threads accumulate run outputs; Thread Runs invoke graphs on threads
3. **Persistent Store API** — key-value store for long-term memory, accessible via API
4. **A2A and MCP protocols** — first-class support for Agent-to-Agent and Model Context Protocol
5. **Stateless Runs** — available for invocations that don't need state persistence
6. **Cron support** — periodic scheduled runs built into the server

## Relevance to Frontend SDK

The `useStream` hook communicates with these API endpoints under the hood:
- **Threads API** — creating/managing conversation threads
- **Thread Runs API** — submitting messages and streaming responses
- **Assistants API** — selecting which agent graph to use (`assistantId` in `useStream`)
- **Store API** — backend for `StoreBackend` persistence
