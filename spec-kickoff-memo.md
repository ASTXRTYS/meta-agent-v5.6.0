# Spec Kickoff Memo

**To:** Design/Build Team
**From:** Jason
**Date:** 2026-04-13
**Subject:** AD is approved for spec — here's how to use it

---

## What you're getting

One document: **`AD.md`** /Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/AD.md (Architecture Decision Record). It is the single source of truth for every architectural decision in this project. All 14 questions are closed. Nothing is still being debated.

There is a companion file, **`DECISIONS.md`**, which contains the full rationale and design detail for each decision. Think of it as the appendix — you read it when you need to understand *why* a decision was made, not *what* was decided. The AD itself contains the locked constraints you must satisfy.

## How the AD is organized

| Section | What it contains | When you need it |
|---|---|---|
| §0–§3 | Header, decision snapshot, context, constraints, options considered | Read once upfront to understand the problem space |
| §4 | **The architecture.** This is the core — topology, PCG, handoff protocol, tool matrix, pipeline flow, repo structure, and agent primitive decisions (middleware, dispatch table, tool schemas, models, behavioral contracts, Anthropic middleware) | This is your primary reference for the entire spec effort |
| §5 | **Spec Handoff.** Dependency map (what to design first) and consolidated spec-owns list (what's already decided vs. what you own) | Read this first to plan your work |
| §6 | Observability & evaluation — required signals, success criteria, validation plan | Reference when designing observability and writing acceptance tests |
| §7 | Risks, tradeoffs, mitigations | Reference when you hit a design tension |
| §8 | Security/privacy/compliance (v1 scope) | Reference for data handling constraints |
| §9 | Decision index — maps every Q# to its AD section and DECISIONS.md entry | Use this as a lookup table when you need to find where a decision lives |

## What's already decided (you don't own this)

The AD locks these things. You must satisfy them; you don't get to change them:

- **Topology:** 7 peer Deep Agent child graphs mounted under a 2-node LangGraph PCG. No conditional edges. No routing intelligence in the PCG.
- **Handoff protocol:** 23 tools across 6 categories. Common parameter shape is `brief` + `artifact_paths`. Communication via `Command.PARENT`.
- **PCG state schema:** 5 keys (`messages`, `project_id`, `current_phase`, `current_agent`, `handoff_log`, `pending_handoff`). `messages` is user-facing I/O only — never written during pipeline execution.
- **Phase gates:** Middleware hooks on handoff tools, not PCG nodes. 2 user-approval gates (scoping→research, architecture→planning). Autonomous mode auto-advances both.
- **Middleware stack:** All 7 agents get the same `create_deep_agent()` call shape. Per-agent variation is in values, not presence. The exact middleware table is in §4 Agent Primitives (Q8).
- **Dispatch table:** 29 triples, 4 gate types. `handoff_log` is the gate authority, not `current_phase`.
- **Tool schemas:** 2 common params + acceptance tools get `accepted: bool` + phase review tools get `phase: str`.
- **Model selection:** Model-agnostic, per-agent, thread-scoped. Provider-specific tools injected by model profile.
- **Behavioral contracts:** Per-agent must-recognize / must-not-do / self-awareness triggers. System prompts live in external `.md` files next to each factory.
- **Anthropic middleware:** Adopt BashTool + Memory middleware via provider profile. Reject text editor + file search (overlap with FilesystemMiddleware).
- **Repo structure:** `agents/` for peer roles, root `graph.py` for PCG, `integrations/` for sandbox wiring.
- **User interface:** v1 ships a Textual TUI launched via `langgraph dev`. The Deep Agents CLI TUI is adopted as the base layer — same framework, same brand theme, same widget patterns. Extended for multi-agent pipeline awareness (active agent indicator, phase progress, handoff progress, approval gate status, autonomous mode toggle). AD locks what the TUI must surface; how it renders is spec territory. v2 evolves to LangGraph Platform + `pip install meta-harness`.

## What you own (the spec-owns list)

Everything the AD delegates to you is consolidated in §5 "Consolidated Spec-Owns List." The 16 items are:

1. Handoff record wire format (Pydantic/TypedDict types)
2. PCG state wire format (TypedDict, `input_schema` wiring)
3. Handoff log cap mechanism
4. Tool description text and `phase` identifier format
5. Acceptance rejection feedback flow
6. User approval tool schema and document rendering format
7. System prompt text (`.md` files — behavioral invariants are locked, text is yours)
8. Prompt loading mechanism (path resolution, caching, template vars)
9. Model routing (runtime resolution, provider adapter patterns)
10. Anthropic profile registration (`workspace_root`, `root_path` per deployment mode)
11. `MEMORY_SYSTEM_PROMPT` per-role override text
12. StagnationGuardMiddleware full implementation
13. Phase gate middleware implementation and `handoff_log` query patterns
14. Sandbox integration (`sandbox_factory.py`, `sandbox_provider.py`)
15. TUI pipeline awareness widgets (widget layout, animations, handoff progress visualization, approval gate rendering)
16. TUI adoption from CLI (fork vs. import decision, TUI module structure, welcome banner, non-interactive mode)

## What order to work in

§5 has a 5-layer dependency map. Here's the short version:

```
Layer 1 (Foundation):     PCG state schema, handoff record, repo structure
Layer 2 (Agent primitives): Middleware stack, tool schemas, model routing, Anthropic profile
Layer 3 (Behavioral):     System prompt .md files, MEMORY_SYSTEM_PROMPT overrides
Layer 4 (Integration):    Phase gate middleware, StagnationGuard, sandbox, observability
Layer 5 (Validation):     Validation plan scenarios
```

**Within each layer, you can work in parallel.** Between layers, the dependency is real — you cannot design tool schemas without the handoff record wire format, and you cannot author system prompts without knowing which tools and middleware each agent receives.

## Three things to know

1. **Run the Deep Agents CLI before designing the TUI.** The CLI (`pip install deepagents && deepagents`) is your reference implementation. Spend `N` minutes using it — the menu flow, the approval interaction, the theme switching, the `ask_user` widget. You'll get more signal from hands-on than from reading source code. Your job is to adopt this base layer and extend it for our 7-agent pipeline (active agent indicator, phase progress, handoff progress, approval gates, autonomous mode toggle).

2. **Three model slots are intentionally TBD.** Architect, Harness Engineer, and Developer models are marked for experimentation (Opus 4.6 vs GPT 5.4 variants). The AD locks the architecture (model-agnostic, per-agent, thread-scoped); the exact model choices will be determined by deployment-level experimentation. This is not a gap — it's a deliberate decision to defer until we have real benchmark data.

3. **System prompts are yours to write, but the behavioral contracts are not.** The AD defines what each agent must recognize, must not do, and what triggers self-awareness. The actual prompt text that fulfills those invariants is spec territory. Start from the invariants table in §4 Agent Primitives (Q12).

4. **Do not reimplement SDK capabilities.** The AD is explicit: leverage Deep Agents SDK as the primary harness. If the SDK already does it (FilesystemMiddleware, SummarizationMiddleware, SubAgentMiddleware, etc.), use it. If you think something is missing, check the SDK source at `.reference/libs/deepagents/deepagents/` before proposing a custom implementation.


---

Questions? The AD's §9 Decision Index tells you exactly where every decision lives. If the AD doesn't answer it, it's yours to decide.
