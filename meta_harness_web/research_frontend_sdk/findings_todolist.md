# Deep Agents Frontend SDK — Todo List Pattern

> Source: https://docs.langchain.com/oss/python/deepagents/frontend/todo-list

## Core Concept

The todo list pattern reads a `todos` array directly from the agent's state via `stream.values`, rendering each item with its current status as the agent works through its plan. It's a **progress dashboard built on the same `useStream` hook** used for chat.

## How It Works

1. User submits a request
2. Agent creates a plan and populates `todos` in its state
3. Agent executes each todo — transitions through `pending → in_progress → completed`
4. `stream.values.todos` updates in real time
5. UI re-renders the todo list with current statuses

## Data Model

### Todo Interface
```typescript
interface TodoItem {
  title: string;
  status: "pending" | "in_progress" | "completed";
  description?: string;
}

interface AgentState {
  messages: BaseMessage[];
  todos: TodoItem[];
}
```

## useStream Setup

```tsx
const stream = useStream<AgentState>({
  apiUrl: AGENT_URL,
  assistantId: "deep_agent_todo_list",
});

const todos = stream.values?.todos ?? [];
```

No special configuration needed — just point `useStream` at your agent and read `todos` from `stream.values`.

## Calculating Progress

```typescript
const completed = todos.filter((t) => t.status === "completed").length;
const inProgress = todos.filter((t) => t.status === "in_progress").length;
const pending = todos.filter((t) => t.status === "pending").length;
const percentage = todos.length
  ? Math.round((completed / todos.length) * 100)
  : 0;
```

Values update reactively as the agent modifies its state.

## UI Components

### TodoList — main container with progress bar and item list
### ProgressBar — visual bar showing `{percentage}%` completion
### TodoItem — individual item with status icon, color coding, strikethrough for completed

Status styling:
| Status | Icon | Background | Text |
|---|---|---|---|
| `pending` | ○ | `bg-gray-50` | `text-gray-600` |
| `in_progress` | ◉ (animate-pulse) | `bg-amber-50` | `text-amber-800` |
| `completed` | ✓ | `bg-green-50` | `text-green-800 line-through` |

## Layout: Combining with Chat

```tsx
function TodoAgentLayout() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_todo_list",
  });
  const todos = stream.values?.todos ?? [];

  return (
    <div className="flex h-screen flex-col">
      {todos.length > 0 && (
        <div className="border-b bg-gray-50 p-4">
          <TodoList todos={todos} />
        </div>
      )}
      <main className="flex-1 overflow-y-auto p-6">
        {stream.messages.map((msg) => <Message key={msg.id} message={msg} />)}
      </main>
      <ChatInput onSubmit={(text) =>
        stream.submit({ messages: [{ type: "human", content: text }] })
      } isLoading={stream.isLoading} />
    </div>
  );
}
```

## Custom State Beyond Todos

`stream.values` can expose **any custom state** your agent defines:

```typescript
const document = stream.values?.document;       // Generated artifacts
const sources = stream.values?.sources ?? [];    // Resource lists
const confidence = stream.values?.confidence_score; // Metrics
const decisions = stream.values?.decisions;      // Decision logs
```

## Key Insights

1. **`stream.values` is the universal custom state accessor** — any key in the agent's state schema is accessible reactively on the frontend
2. **No special configuration** — `useStream` exposes custom state values automatically
3. **TypeScript type safety** — define an interface matching your agent's state schema and pass as type parameter to `useStream`
4. **Reactive updates** — no manual polling or refresh logic needed; `stream.values` updates automatically
5. **Composable with chat** — todo list works alongside regular message rendering
6. **Animatable** — CSS `transition-all duration-300` on status changes for smooth UX

## Best Practices
- Show todo list prominently — it's the primary progress indicator for plan-based agents
- Animate status transitions with CSS transitions
- Only highlight one `in_progress` item at a time
- Collapse or dim completed items as list grows
- Show progress percentage for at-a-glance understanding
- Handle empty/loading states (show "Agent is creating a plan..." spinner)

## Use Cases
- Project planning, research workflows, data processing pipelines
- Onboarding flows, report generation, any structured multi-step plan
