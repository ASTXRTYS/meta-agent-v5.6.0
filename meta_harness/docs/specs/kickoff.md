# Meta Harness Spec Kickoff

> This document is the dependency map and delegated-items list for all implementation specs. The AD locks *what* and *why*; this doc tracks *how* and *in what order*.

---

## Spec Dependency Map

Design work must proceed in this order — each layer depends on the one above it:

```
Layer 1: Foundation (no dependencies)
  ├─ PCG state schema → TypedDict/Pydantic wire formats
  ├─ Handoff record → TypedDict/Pydantic wire formats
  └─ Repo structure → module layout, __init__.py contracts

Layer 2: Agent primitives (depends on Layer 1)
  ├─ Middleware stack → per-agent create_deep_agent() call shapes (Q12, Q8)
  ├─ Tool schemas → 23 handoff tool InputSchema definitions (Q10)
  ├─ Model routing → per-agent model resolution from project config (Q11)
  └─ Anthropic profile → provider profile registration (Q13)

Layer 3: Behavioral contracts (depends on Layer 2)
  ├─ System prompt .md files → per-agent prompt authoring (Q12 behavioral)
  └─ MEMORY_SYSTEM_PROMPT overrides → per-role memory tuning (Q13)

Layer 4: Integration (depends on Layers 1–3)
  ├─ Phase gate middleware → gate logic implementation (Q9 dispatch table)
  ├─ StagnationGuardMiddleware → full implementation (Q12 design vision)
  ├─ Sandbox integration → sandbox_factory + provider (Q8)
  └─ Observability wiring → LangSmith metadata, Studio config

Layer 5: Validation (depends on Layer 4)
  └─ Validation plan scenarios → §6 validation plan
```

**Parallelism:** Within each layer, items can be designed in parallel. Between layers, the dependency is real — you cannot design tool schemas without the handoff record wire format, and you cannot author system prompts without knowing which tools and middleware each agent receives.

---

## Delegated Spec Items (Consolidated Spec-Owns List)

| Topic | AD locks | Spec owns | Source |
|---|---|---|---|
| Handoff record wire format | Field set, enum values (Q6, Q10) | Exact Pydantic/TypedDict types, `HandoffRecord.id` protocol for `add_messages` | §4 Data Contracts |
| PCG state wire format | 5 keys + types + invariants (Q11) | Exact `ProjectCoordinationState` TypedDict, `input_schema` wiring | §4 PCG State Schema |
| Handoff log cap | Cap required, N is runtime constant (Q10) | Cap mechanism (summarize, migrate to Store, discard) | §4 PCG State Growth |
| Tool descriptions | 23 tool names, common + extra params (Q10) | Exact description text, `phase` identifier format, `artifact_paths` conventions | §4 Tool Use-Case Matrix |
| Acceptance rejection flow | `accepted=false` is audit record (Q10) | Rejection feedback flow — does agent retry? return to Developer? | §4 Acceptance |
| User approval tool | PM owns approval tool, prompt-driven (Q7) | Tool schema, document rendering format (docx/pdf/pptx) | §4 Phase Gates |
| System prompt text | Behavioral invariants per agent (Q12) | Exact prompt text in `.md` files | §4 + Q12 |
| Prompt loading mechanism | External `.md` files next to factory (Q12) | Path resolution, `Path.read_text()` vs backend, caching, template vars | Q12 |
| Model routing | Model-agnostic, per-agent, thread-scoped (Q11) | Runtime model resolution, provider adapter patterns | Q11 |
| Anthropic profile registration | Adopt BashTool + Memory + ServerSideTools middleware (Q13) | `workspace_root`, `root_path` values per deployment mode; `AnthropicServerSideToolsMiddleware` implementation and per-agent tool provisioning | Q13 |
| `MEMORY_SYSTEM_PROMPT` per-role tuning | Override belongs in prompt files (Q12, Q13) | Exact override text per role | Q12 + Q13 |
| StagnationGuardMiddleware | Two-tier nudge→stop, pluggable signals, graceful absence (Q12) | Full implementation, signal provider bodies, nudge templates, testing | Q12 |
| Phase gate middleware | Gate logic per triple (Q9), per-agent ownership (Q8) | Middleware implementation, `handoff_log` query patterns | Q8 + Q9 |
| Sandbox integration | Follows CLI `integrations/` convention (Q1, Q8) | `sandbox_factory.py`, `sandbox_provider.py` implementation | §4 Repo Structure |
| TUI pipeline awareness widgets | Information requirements locked (Q14) | Widget layout, animations, handoff progress visualization, approval gate rendering | §4 User Interface Surface (Q14) |
| TUI adoption from CLI | Adopt CLI TUI base layer (Q14) | Fork vs. import decision, TUI module structure, welcome banner, non-interactive mode | §4 User Interface Surface (Q14) |
| Web app auth & deployment | LangGraph Platform custom auth with Supabase JWTs (§10) | Handler schemas, `langgraph.json` requirements, CORS config, SDK reference paths | `harness-webapp-contract.md` |

---

## New Spec Docs Created

| Spec | Purpose | Created |
|---|---|---|
| `harness-webapp-contract.md` | Web app auth handlers, deployment `langgraph.json`, CORS, SDK references | 2026-04-21 |
| `kickoff.md` | This document — dependency map and delegated-items tracker | 2026-04-21 |



## Open Questions Blocking Spec Work

These open questions from `AD.md` §Open Questions may block or influence spec design:

- **OQ-H1:** PM visibility into executing projects — what does PM see in `pm_session`?
- **OQ-3:** Developer optimization visibility vs. information isolation — HE must emit a public evaluation dashboard artifact (sanitized trend/benchmark trail) while Developer stays blind to raw eval artifacts.
- **OQ-4:** HITL during development phases — Developer lacks `AskUserMiddleware`; who owns HITL? (PM relay vs. restricted-scope middleware addition.)

Resolution of these questions is deferred to a dedicated interview round. Spec authors should design for both options where possible or mark dependencies explicitly.
