# Deep Agents Frontend SDK — Subagent Streaming

> Source: https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming

## Core Concept

When a coordinator agent spawns specialist subagents, set `filterSubagentMessages: true` in `useStream` to cleanly split coordinator messages from subagent output. Use `getSubagentsByMessage` to attach each subagent's progress card to the coordinator message that triggered it.

## Why Filter Subagent Messages

Without filtering: every token from every subagent appears interleaved in the coordinator's message stream — unreadable.

With `filterSubagentMessages: true`:
- `stream.messages` contains **only** the coordinator's messages
- Each subagent's content is accessible through `stream.subagents` and `stream.getSubagentsByMessage`
- UI stays clean: coordinator reasoning is separate from specialist work

## useStream Setup

```tsx
const stream = useStream<AgentState>({
  apiUrl: AGENT_URL,
  assistantId: "deep_agent",
  filterSubagentMessages: true,  // ALWAYS set this
});
```

## Submitting with Subgraph Streaming

```tsx
stream.submit(
  { messages: [{ type: "human", content: text }] },
  { streamSubgraphs: true }  // Enable subgraph streaming
);
```

> Set a high recursion limit (start with 100) — deep agent workflows with nested subgraphs need higher limits than the default 25.

## SubagentStreamInterface

```typescript
interface SubagentStreamInterface {
  id: string;
  status: "pending" | "running" | "complete" | "error";
  messages: BaseMessage[];
  result: string | undefined;
  toolCall: {
    id: string;
    name: string;
    args: {
      description: string;
      subagent_type: string;
      [key: string]: unknown;
    };
  };
  startedAt: number | undefined;
  completedAt: number | undefined;
}
```

| Property | Description |
|---|---|
| `id` | Unique identifier for this subagent instance |
| `status` | Lifecycle: `pending → running → complete` or `error` |
| `messages` | Subagent's own message stream, updated in real time |
| `result` | Final output text, available only when `status === "complete"` |
| `toolCall` | The tool call that spawned this subagent |
| `toolCall.args.description` | Task description coordinator assigned |
| `toolCall.args.subagent_type` | Specialist type (e.g., "researcher", "analyst") |
| `startedAt` / `completedAt` | Timestamps for elapsed time calculation |

## Key APIs

### Linking Subagents to Messages
```tsx
const turnSubagents = stream.getSubagentsByMessage(msg.id);
// Returns SubagentStreamInterface[] — empty if message didn't spawn subagents
```

### Accessing All Subagents
```tsx
const allSubagents = [...stream.subagents.values()];
const running = allSubagents.filter((s) => s.status === "running");
const completed = allSubagents.filter((s) => s.status === "complete");
const errors = allSubagents.filter((s) => s.status === "error");
```

## UI Components

### SubagentCard
- Shows specialist name (`toolCall.args.subagent_type`), task description, streaming content or final result, timing
- Collapsible with expand/collapse toggle
- Status icon + badge (pending/running/complete/error)
- Animated cursor for running state

### SubagentProgress
- Progress bar + counter: `{completed}/{total} complete`
- Percentage-based width bar

### MessageWithSubagents
- Renders coordinator message content
- If message spawned subagents → renders SubagentProgress + SubagentCard list below it
- Indented with left border for visual hierarchy

### SynthesisIndicator
- Shows when all subagents complete but coordinator is still loading (synthesizing results)
- "Synthesizing results from N subagents..."

## Layout Pattern

```tsx
{stream.messages.map((msg) => {
  const turnSubagents = stream.getSubagentsByMessage(msg.id);
  return (
    <MessageWithSubagents
      key={msg.id}
      message={msg}
      subagents={turnSubagents}
    />
  );
})}
```

## Key Insights

1. **`filterSubagentMessages: true`** is essential — always set it. Without it, coordinator and subagent tokens interleave into unreadable output.

2. **`streamSubgraphs: true`** must be passed in `submit()` options to enable subagraph streaming.

3. **`stream.getSubagentsByMessage(msg.id)`** is the key linking API — maps coordinator messages to the subagents they spawned.

4. **`stream.subagents`** is a Map of all subagent instances — useful for global dashboards.

5. **`SubagentStreamInterface`** provides rich metadata: task description, specialist type, real-time messages, timing, status lifecycle.

6. **Synthesis phase detection**: when all subagents are complete but `stream.isLoading` is still true, the coordinator is synthesizing.

7. **Error isolation**: one subagent failing doesn't crash the UI — show error in that card while others continue.

## Best Practices
- Always set `filterSubagentMessages: true`
- Show task descriptions prominently (`toolCall.args.description`)
- Use collapsible cards — auto-collapse completed cards when 5+ subagents
- Display timing data for performance visibility
- Set recursion limit to 100+ for deep agent workflows
- Handle errors per-subagent, not globally

## Use Cases
- Deep research with coordinator dispatching researchers
- Multi-expert analysis (legal, financial, technical specialists)
- Complex task decomposition with specialist workers
- Code review pipelines (security, style, performance, docs agents)
