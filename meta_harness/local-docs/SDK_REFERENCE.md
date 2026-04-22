# Canonical SDK References

Grouped by SDK. Each subsection states its **root** directory once; rows carry
only the path relative to that root. Cross-root references are collected at the
bottom with full paths.

## Deep Agents SDK

Root: `.reference/libs/deepagents/deepagents/`

Use for `create_deep_agent()`, middleware, backends, harness architecture.

| Topic | Path |
|---|---|
| `create_deep_agent()` parameter passing (`checkpointer`, `store`, `name`) | `graph.py:217-236`, `602-623` |
| Declarative `task` subagent (ephemeral, stateless) | `middleware/subagents.py:152-162`, `355-376` |
| `CompiledSubAgent` runnable (no stable `thread_id` config) | `middleware/subagents.py:488-493` |
| `AsyncSubAgent` remote thread creation | `middleware/async_subagents.py:280-318`, `500-548` |
| `CompositeBackend` pattern (used by CLI + deploy templates) | `backends/composite.py:119-158` |

## Deep Agents CLI

Root: `.reference/libs/cli/deepagents_cli/`

Production Deep Agent reference implementation — coding-agent assembly, sandbox
routing, LangGraph server wiring, deploy templates, TUI ergonomics.

| Topic | Path |
|---|---|
| `langgraph.json` scaffolding | `server.py:85-119`, `server_manager.py:92-115` |
| Server graph factory (`graph = make_graph`) | `server_graph.py:1-10`, `93-196` |
| Sandbox backend creation | `server_graph.py:117-170`, `integrations/sandbox_factory.py:1-134` |
| Sandbox integration package layout | `integrations/__init__.py`, `integrations/sandbox_provider.py:1-49` |
| `create_cli_agent()` backend selection | `agent.py:1104-1218` (pair with Deep Agents `backends/composite.py:119-158`) |
| Deploy template graph factory | `deploy/bundler.py:192-201`, `deploy/templates.py:430-469` |
| Deploy template `CompositeBackend` pattern | `deploy/templates.py:199-207`, `405-424` |
| LangSmith thread URL resolution | `config.py:1600-1745`, `app.py:2545-2579` |

## LangGraph runtime

Root: `.venv/lib/python3.11/site-packages/langgraph/`

Use for `StateGraph`, subgraphs, checkpoint namespaces, `Command.PARENT`,
persistence, streaming, interrupts.

| Topic | Path |
|---|---|
| Checkpoint memory keyed by `thread_id` | `graph/state.py:1038-1074` |
| `Command.PARENT` parent bubbling | `types.py:652-702`, `graph/state.py:1540-1550` |
| Mounted subgraph persistence (child `checkpoint_ns`) | `pregel/main.py:2416`, `2613-2615`, `_internal/_config.py:34-45` |
| `ToolNode` tool-returned `Command` | `prebuilt/tool_node.py:857-899` |

## LangGraph API server

Root: `.venv/lib/python3.11/site-packages/langgraph_api/`

Use for Agent Server behavior — threads, runs, Store, auth, persistence,
queueing boundary.

| Topic | Path |
|---|---|
| Callable graph exports | `graph.py:330-379`, `730-765` |

## LangGraph SDK client

Root: `.venv/lib/python3.11/site-packages/langgraph_sdk/`

Use for explicit thread/run submission, assistant management, headless client
patterns.

| Topic | Path |
|---|---|
| Explicit thread/run submission | `_async/threads.py:98-143`, `_async/runs.py:435-462`, `552-585` |
| Assistants / graph IDs | `_async/assistants.py:320-350` |

## LangChain agent foundation

Root: `.venv/lib/python3.11/site-packages/langchain/`

Use for `create_agent()`, `AgentMiddleware`, built-in middleware, tool handling,
model abstraction, structured output.

| Topic | Path |
|---|---|
| `AgentMiddleware` base class (`wrap_model_call`, `before_agent`, state schema) | `agents/middleware/types.py` |
| `create_agent()` tool wiring | `agents/factory.py:920-939` |

## LangChain Anthropic integration

Root: `.venv/lib/python3.11/site-packages/langchain_anthropic/`

Use for `ChatAnthropic` and Claude-specific patterns. No line-range references
yet — read the package root when `ChatAnthropic` behavior is in question.

## Anthropic SDK

Root: `.venv/lib/python3.11/site-packages/anthropic/`

| Topic | Path |
|---|---|
| Server-side tool descriptor types (`web_search`, `web_fetch`, `code_execution`, `tool_search_*`) | `types/tool_union_param.py` |

## LangSmith

Root: `.venv/lib/python3.11/site-packages/langsmith/`

Use for tracing, datasets, run management, experiments, feedback, presigned
feedback tokens, programmatic LangSmith workflows. No line-range references yet
— read the package root when `Client`, `evaluate()`, or feedback behavior is in
question.

## Agent evals

Root: `.venv/lib/python3.11/site-packages/agentevals/`

Use for `EvaluatorResult`, LLM-as-judge, trajectory scoring, `GraphTrajectory`.

| Topic | Path |
|---|---|
| LLM-as-judge trajectory evaluator | `trajectory/llm.py` |
| Tool-call matching (strict, unordered, subset, superset) | `trajectory/match.py` |
| LangGraph thread trajectory evals | `graph_trajectory/` |
| `GraphTrajectory`, `EvaluatorResult` shapes | `types.py` |

## Cross-cutting references

Rows that span multiple roots. Full paths carried intentionally.

| Topic | Paths |
|---|---|
| `ToolNode` tool-returned `Command` + `create_agent()` wiring + Deep Agents graph assembly | `.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py:857-899`, `.venv/lib/python3.11/site-packages/langchain/agents/factory.py:920-939`, `.reference/libs/deepagents/deepagents/graph.py:602-623` |
