# Deep Agents Frontend SDK — Overview

> Source: https://docs.langchain.com/oss/python/deepagents/frontend/overview

## Architecture

Deep Agents use a **coordinator-worker architecture**. The main agent plans tasks and delegates to specialized subagents, each running in isolation. On the frontend, `useStream` surfaces both the coordinator's messages and each subagent's streaming state.

## Backend Setup

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.4",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Research assistant",
        }
    ],
)
```

## Frontend Connection

```tsx
import { useStream } from "@langchain/react";

function App() {
  const stream = useStream<typeof agent>({
    apiUrl: "http://localhost:2024",
    assistantId: "agent",
  });

  // Deep agent state beyond messages
  const todos = stream.values?.todos;
  const subagents = stream.subagents;
}
```

## Key Capabilities

| Capability | Access Pattern |
|---|---|
| Coordinator messages | `stream.messages` |
| Subagent streaming state | `stream.subagents` |
| Todo list / plan progress | `stream.values?.todos` |
| Custom agent state values | `stream.values?.{key}` |
| Subagent message filtering | `filterSubagentMessages: true` option |

## Key Insights

1. **Same `useStream` hook as `createAgent`**: Deep agent patterns use the same `useStream` hook from `@langchain/react` (also available for Vue, Svelte, Angular). No separate SDK needed.

2. **Additional `useStream` features for deep agents**:
   - `stream.subagents` — access subagent streaming state
   - `stream.values.todos` — access todo list / plan progress from agent state
   - `filterSubagentMessages` — cleanly separate coordinator vs subagent message streams

3. **Full LangChain frontend pattern compatibility**: All standard LangChain frontend patterns (markdown messages, tool calling, human-in-the-loop) work with deep agents since they're built on the same LangGraph runtime.

4. **Patterns documented**:
   - Subagent streaming cards
   - Todo list / plan progress
   - Sandbox / IDE experience
   - All standard LangChain patterns (HITL, tool calls, generative UI, etc.)
