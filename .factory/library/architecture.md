# Meta Harness v1 Architecture

## Overview

Meta Harness is a multi-agent LLM application for developing, observing, and shipping other LLM applications. It uses the Deep Agents SDK from LangChain as its primary harness.

## Runtime Topology

A thin LangGraph Project Coordination Graph (PCG) orchestrates 7 peer Deep Agent child graphs:

```
User/TUI → PCG (2 nodes) → 7 mounted Deep Agent child graphs
```

**PCG nodes:** `process_handoff` (records handoff, routes) → `run_agent` (invokes target child graph)

**Child graphs (each a `create_deep_agent()` harness):**
- PM (project-manager) — stakeholder interface, pipeline hub
- Harness Engineer (harness-engineer) — evaluation science
- Researcher (researcher) — SDK/API research
- Architect (architect) — system design
- Planner (planner) — implementation planning
- Developer (developer) — code implementation
- Evaluator (evaluator) — spec/plan compliance

## Communication Model

All agent-to-agent communication uses explicit handoff tools that return `Command(graph=Command.PARENT, goto="process_handoff", update={...})`. The PCG records the handoff and invokes the target. No direct peer invocation.

**23 handoff tools** across 6 categories: Pipeline Delivery (5), Pipeline Return (5), Acceptance (2), Stage Review (2), Phase Review (4), Consultation (5).

**Common tool params:** `brief` (str) + `artifact_paths` (list[str]). Acceptance tools add `accepted: bool`. Phase review tools add `phase: str`.

## State Model

**PCG state (6 keys):**
- `messages` — user-facing I/O only (lifecycle bookends)
- `project_id` — root thread identifier
- `current_phase` — scoping|research|architecture|planning|development|acceptance
- `current_agent` — which role graph is active
- `handoff_log` — append-only audit trail (HandoffRecord objects)
- `pending_handoff` — active handoff cursor

**Child agents own their own state** via checkpoint namespaces. They never see PCG state beyond `messages` (enforced by `input_schema=_InputAgentState`).

## Middleware Stack

All 7 agents share the same `create_deep_agent()` shape. Universal baseline:
1. CollapseMiddleware — free context compression
2. ContextEditingMiddleware — clears stale tool results
3. SummarizationToolMiddleware — on-demand compaction
4. ModelCallLimitMiddleware — hard cost ceiling (per-role limits)
5. StagnationGuardMiddleware — progress-aware nudge/stop

Plus per-agent: phase gate middleware (PM, Developer, Architect), AskUserMiddleware (PM, Architect), ShellAllowListMiddleware (sandbox mode).

## Phase Gates

Middleware hooks on handoff tools, not PCG edges. Gate logic checks `handoff_log` (the authority), not `current_phase`. 2 transitions require user approval: scoping→research, architecture→planning. Autonomous mode auto-advances all.

## Backend Model

Dual-modality: local-first (FilesystemBackend + LocalShellBackend) or sandbox-backed. Each agent gets a CompositeBackend routing: `/` → role workspace, `/memories/` → episodic memory, `/skills/` → procedural memory, `/shared/` → team context.

## User Interface

Textual TUI adopted from Deep Agents CLI, extended with pipeline awareness (active agent indicator, phase progress, handoff visualization, approval gates, autonomous mode toggle). Launched via `langgraph dev`.
