# LangSmith Deployment

> Source: https://docs.langchain.com/langsmith/deployment

## Overview

LangSmith Deployment is a **workflow orchestration runtime purpose-built for agent workloads**. It provides managed infrastructure for agents to run reliably in production at scale, supporting the full lifecycle from local development to deployment. It is **framework-agnostic** — deploy agents built with LangGraph or other frameworks.

## Core Capabilities

### Studio
- Connects to any Agent Server (local or deployed)
- Interactive environment for developing and debugging agents
- Visualize execution graphs
- Inspect state at any checkpoint
- Step through runs
- Modify state mid-execution
- Branch to explore alternative paths

### Agent Composition
- **RemoteGraph** — any agent can call other deployed agents using the same interface as local
- Research agent delegates to search agent on a different deployment
- Routing agent dispatches to specialized sub-agents
- Agents don't need to know if they're calling local or remote
- **Native MCP and A2A support** — deployed agents can expose and consume tool interfaces and agent-to-agent protocols

### Deployment Options

| Option | Description |
|---|---|
| **Cloud** | Fully managed. Push from git repo or use `langgraph deploy` |
| **Hybrid** | Runs in your cloud, managed by LangSmith control plane |
| **Self-hosted** | Fully self-managed in your own infrastructure |

Same runtime, same APIs across all options.

## Server Customization

| Feature | Description |
|---|---|
| Custom auth | Authentication and multi-tenant access control |
| Server customization | Custom routes, middleware, lifespan hooks, encryption |
| CI/CD pipelines | Deployment automation |
| TTL configuration | State and thread management lifecycle |
| Semantic search | Built-in search capabilities |

## Key Insights

1. **Framework-agnostic runtime** — not locked to LangGraph, though LangGraph is first-class
2. **RemoteGraph for agent composition** — deployed agents can call each other transparently (local/remote agnostic)
3. **MCP + A2A native** — agents can expose/consume tool interfaces and agent-to-agent protocols
4. **Three deployment tiers** — Cloud (fully managed), Hybrid (your cloud, their control plane), Self-hosted (fully yours)
5. **Studio for debugging** — state inspection, checkpoint browsing, mid-execution modification, branching
6. **Custom routes via `http.app`** — same mechanism used by the sandbox pattern for file browsing APIs
7. **TTL configuration** — manage thread and state lifecycle for production cleanup

## Relevance to Meta Harness Frontend

- The `useStream` hook connects to a LangSmith Deployment Agent Server
- Custom API routes (sandbox file browsing, etc.) are served alongside the agent API via `http.app`
- RemoteGraph enables the multi-agent architecture where PM, Researcher, Architect, etc. can be separate deployments
- Studio provides development-time debugging for the agent workflows before building custom frontend
- A2A protocol could enable inter-agent communication in the distributed agent topology
