# LangChain Frontend SDK — Overview (createAgent)

> Source: https://docs.langchain.com/oss/python/langchain/frontend/overview

## Architecture

Every pattern follows the same architecture: a `createAgent` backend streams state to a frontend via the **`useStream` hook**.

- **Backend**: `createAgent` produces a compiled LangGraph graph that exposes a streaming API
- **Frontend**: `useStream` hook connects to that API and provides reactive state — messages, tool calls, interrupts, history, and more

## useStream — Multi-Framework Support

```tsx
import { useStream } from "@langchain/react";    // React
import { useStream } from "@langchain/vue";       // Vue
import { useStream } from "@langchain/svelte";    // Svelte
import { useStream } from "@langchain/angular";   // Angular
```

`useStream` is **UI-agnostic** — use it with any component library or generative UI framework.

## Reactive State Provided by useStream

| State | Description |
|---|---|
| `messages` | Agent message stream |
| Tool calls | Active tool call information |
| Interrupts | HITL interrupt state |
| History | Conversation history |
| Custom values | Any custom state keys from agent state schema |

## Pattern Categories

1. **Render messages and output** — display agent responses, markdown, streaming text
2. **Display agent actions** — tool calls, function invocations, agent reasoning
3. **Manage conversations** — thread management, history, branching
4. **Advanced streaming** — subgraph streaming, filtering, real-time updates

## Key Insights

1. **`useStream` is the universal frontend hook** — same hook works for both `createAgent` and `createDeepAgent` backends
2. **Framework-agnostic**: React, Vue, Svelte, Angular all supported with identical API
3. **Reactive state model**: messages, tool calls, interrupts, history all provided as reactive state
4. **HITL (Human-in-the-Loop) interrupts** are a first-class concept in the streaming API
5. **All LangChain frontend patterns work with Deep Agents** — Deep Agents are built on the same LangGraph runtime
6. **Generative UI compatible** — `useStream` can power any component library or generative UI framework

## Relationship to Deep Agents

The Deep Agents frontend patterns are a **superset** of the LangChain frontend patterns:
- All `createAgent` patterns (messages, tool calls, HITL, history) work identically with `createDeepAgent`
- Deep Agents add: `stream.subagents`, `stream.values.todos`, `filterSubagentMessages`, `getSubagentsByMessage`
- Same `useStream` hook, same API, additional capabilities for multi-agent workflows
