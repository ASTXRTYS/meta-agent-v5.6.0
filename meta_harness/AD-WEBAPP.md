# Architecture Decision Record — Web Application

> [!TIP]
> Keep this doc concise, factual, and testable. If a claim cannot be verified, add a validation step.

---

## 0) Header

| Field | Value |
|---|---|
| ADR ID | `ADR-002` |
| Title | `Meta Harness Web Application` |
| Status | `Draft` |
| Date | `2026-04-13` |
| Author(s) | `@Jason` |
| Reviewers | `@Jason` |
| Related PRs | `#NA` |
| Related Docs | `[AD.md](./AD.md)`, `[DECISIONS.md](./DECISIONS.md)`, `[AGENTS.md](../.agents/pm/AGENTS.md)` |

**One-liner:** `Multi-tenant SaaS web application for Meta Harness — project management, agent interaction, evaluation observability, and target harness configurability.`

---

## 1) Decision Snapshot

```txt
Meta Harness ships as a multi-tenant SaaS with a browser-based web application
as the primary user surface. The web app provides: mission-control project
overview (not kanban), real-time agent chat that follows the currently active
agent (observation mode during specialist work, interactive during PM phases),
pipeline observability (phase progress, handoff flow, evaluation cycles), a
client permission model (observe-only → Q&A-only → full access) configurable
by the agency owner per-project, CRM and communication hub integrations (Attio,
Slack, WhatsApp), developer optimization interrupts for system prompt changes,
and end-user target harness system prompt configuration with Harness Engineer
re-evaluation triggers. The CLI remains the power-user / local-dev surface.
The web app connects to the same PCG backend via LangGraph Platform APIs.
```

### Decision Badge

`Status: Draft` · `Risk: High` · `Impact: High`

---

## 2) Context

### Problem Statement

Meta Harness needs a hosted web application to serve three audiences:

1. **Jason's AI agency (immediate)** — Demo vehicle for go-to-market. Screen recordings of end-to-end project execution must look professional, not terminal recordings.
2. **Enterprises and SMBs (near-term)** — Teams that want project management AI without local setup. They need CRM/Slack integration, project isolation, and the ability to configure their deployed harnesses.
3. **Power users (ongoing)** — Developers who want a development hub where Meta Harness + LangChain ecosystem = exponential productivity.

The existing TUI (ADR-001, Q14) serves local dev and power users. The web app is the **product surface** — where most users will live.

### Constraints Inherited from ADR-001

- `thread_id = project_id` — project isolation is architecturally guaranteed by the PCG state model.
- PM is the primary user-facing agent — stakeholder interaction flows through PM. However, agents equipped with `AskUserMiddleware` (PM, Architect) can surface questions directly to the user, and the web app chat follows the currently active agent, rendering specialist work (tool calls, subagent spawning, reasoning) as observable activity. The chat is not PM-exclusive; it evolves to reflect whichever agent is working.
- Handoff tools return `Command.PARENT` — the web app does not bypass the PCG.
- Phase gates are middleware hooks — the web app surfaces gate status, does not enforce it.
- Agent state is private per checkpoint namespace — the web app cannot read child agent internals directly.
- LangGraph Platform provides managed checkpointer/store — the web app does not manage these.
- The PCG is a LangGraph graph — the web app is a **client** of the LangGraph server, not an extension of it.

### New Constraints

- Multi-tenant: user accounts, project isolation, subscription tiers.
- The web app must stream agent output in real time (not poll).
- CRM/communication integrations are PM context sources and invocation surfaces.
- Developer optimization interrupts (system prompt changes) must surface as user-actionable events.
- A display and or dedicated page for seeing datasets, (public and held out) should be treated as way to provide stakeholder trust, transparency and delight. 
- Target harness system prompt configurability must trigger Harness Engineer re-evaluation when business logic changes.(Feature leverage needs to be further designed)
- The web app must be exceptional — production-grade UX, not a demo shell.

### Non-Goals

- [ ] Replacing the CLI/TUI for local development
- [ ] Building a general-purpose chatbot platform
- [ ] Hosting arbitrary LangGraph graphs (we host our PCG only)
- [ ] Billing/subscription implementation in v1 of this AD (scope to a separate decision)
- [ ] Mobile-native app (responsive web is sufficient for v1)
- [ ] Custom agent topology editing by end users (v2+)

---

## 3) Options Considered

### WQ1: Frontend framework

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Next.js + `@langchain/react` + Tailwind + shadcn/ui | SDK provides `useStream` hook for React; Next.js gives SSR, routing, API routes; Tailwind/shadcn for polished UI | Locks to React ecosystem | `Selected` |
| B | Remix + `@langchain/react` | Same SDK support, different routing model | Smaller ecosystem than Next.js; no clear advantage for our use case | `Rejected` |
| C | SvelteKit + `@langchain/svelte` | Lighter runtime, SDK has Svelte adapter | Smaller ecosystem; fewer shadcn-compatible component libs | `Rejected` |
| D | Vue/Nuxt + `@langchain/vue` | SDK has Vue adapter | Smaller ecosystem; fewer reference implementations | `Rejected` |

**Rationale:** `@langchain/react` is the primary SDK frontend package with the most complete `useStream` implementation and reference examples (subagent streaming, todo list, sandbox, generative UI, HITL). Next.js provides SSR for the landing page, file-based routing for the dashboard, and API routes for our thin backend. Tailwind + shadcn/ui gives production-grade styling without heavy component libraries.

### WQ3: LangGraph Platform integration pattern

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | `useStream` directly to LangGraph Platform | SDK-native; zero custom streaming code; supports `streamSubgraphs`, `filterSubagentMessages`, state streaming | Requires LangGraph Platform deployment | `Selected` |
| B | Custom API backend that wraps LangGraph Platform | Can add business logic in the wrapper | Duplicates streaming that `useStream` already provides; adds latency | `Rejected` |
| C | Direct LangGraph SDK client calls (no `useStream`) | Maximum flexibility | Reimplements streaming, subagent filtering, state sync that `useStream` provides | `Rejected` |

**Rationale:** `useStream` is the SDK's designed integration point. It handles real-time streaming, subagent filtering, state access, and HITL resume — all the core functionality we need. Adding a custom wrapper would duplicate SDK capabilities.

### WQ2: Backend API layer

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | All-in on LangGraph Platform (`langgraph.json http.app`) | One deployment; shared auth; custom routes can access graph state directly | Python-only backend; can't natively handle webhook receivers (Slack/Attio); agency→client hierarchy is business logic that doesn't belong in graph config | `Rejected` |
| B | Separate thin Next.js API routes | TypeScript everywhere; webhook receivers natively; independent scaling; clean separation of business logic from agent graph | Two deployments; auth coordination between Next.js and LangGraph Platform | `Selected` |

**Rationale:** The agency→client→team hierarchy is business logic, not agent graph logic. CRM/Slack integrations require webhook receivers. Next.js API routes handle both naturally. LangGraph Platform's `@auth.authenticate` is designed to validate external IdP JWTs, so auth coordination is solved.

### WQ4: Authentication provider

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|
| A | Supabase Auth | Auth + DB + RLS in one service; JWTs include `org_id` and `role` claims that LangGraph `@auth` can validate; free tier covers early stage | Locks to Supabase for auth | `Selected` |
| B | Auth0 | Mature auth provider; supports agency→client hierarchy via organizations feature | Separate from DB; paid tier ($35/mo) for org features; two services to manage | `Rejected` |
| C | NextAuth (self-hosted) | Full control; no vendor lock-in | Must build org/role management ourselves; more code to maintain | `Rejected` |

**Rationale:** Supabase Auth + Postgres + RLS solves auth, database, and access control in one service. JWTs carry `org_id` and `role` claims that both Next.js (frontend routing) and LangGraph Platform (`@auth.authenticate`) can validate. Row Level Security handles the agency→client→team hierarchy without custom middleware.

### WQ5: Database for user/org/project metadata

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|
| A | Supabase Postgres | Same service as auth; RLS for org-scoped queries; real-time subscriptions for live updates; free tier | Locks to Supabase for DB | `Selected` |
| B | PlanetScale | Serverless MySQL; good developer experience | No auth; no RLS; separate IdP needed | `Rejected` |
| C | Neon | Serverless Postgres; branching | No auth; no RLS; separate IdP needed | `Rejected` |

**Rationale:** WQ4 and WQ5 are a package — Supabase solves both. RLS is the key differentiator: agency users can see across client orgs, client users cannot, all enforced at the database level. No custom middleware needed.

### WQ7: Deployment infrastructure

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Vercel (Next.js) + LangSmith Cloud (PCG) | Zero infra management; `langgraph deploy` one command; managed Postgres/Redis; built-in tracing; free dev deployment on Plus plan | Usage-based pricing for production; data on LangChain infra | `Selected` |
| B | Self-hosted (Docker on own servers) | Data stays in your VPC; no usage-based pricing | Must manage Postgres, Redis, API server, queue workers yourself | `Rejected` (v2+ concern) |
| C | Hybrid (runs in your cloud, managed by LangSmith) | Data in VPC + managed operations | Enterprise plan required; contact sales | `Rejected` (v2+ concern) |

**Rationale:** Start on LangSmith Cloud Plus plan with dev deployment. Covers launch scenario (Jason + 2 clients). Zero infra work — `langgraph deploy` and live. Upgrade to production deployment when traffic warrants. Self-hosted/hybrid are v2+ options for enterprise clients requiring data in their VPC or when usage-based pricing becomes expensive. Vercel for Next.js is the natural pairing — cheap, fast deploys, SSR for landing page.

### WQ21: Repository strategy and cross-repo architecture

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Separate repos: `meta-harness` (Python) + `meta-harness-web` (Next.js) | Clean separation of languages/runtimes/deployments; zero CI coupling; parallel development with Droids; clean API boundary via LangGraph Platform | Two repos to manage; cross-repo contract sync for PCG state schema | `Selected` |
| B | Monorepo with Turborepo (Python + Next.js in one repo) | Single repo; shared CI config; atomic cross-stack changes | CI complexity (path-based filtering); mixed language tooling; Vercel + LangGraph Cloud both watching same repo; no shared TypeScript/Python code to justify monorepo | `Rejected` |
| C | Web app as subdirectory inside `meta-harness` repo | Simplest initial setup | Deployment coupling; Droids' Python changes trigger Next.js CI; different deployment targets watching same repo; workspace pollution | `Rejected` |

**Rationale:** The harness is a Python project deploying to LangGraph Cloud Platform. The web app is a TypeScript/Next.js project deploying to Vercel. There is zero shared source code between them — they communicate exclusively over the LangGraph Platform API (HTTP/WebSocket). The only shared contracts are: (1) the LangGraph Platform API URL (an env var), (2) the PCG state schema (TypeScript interface mirrors Python TypedDict), and (3) the Supabase JWT format (validated by both Next.js middleware and LangGraph `@auth.authenticate`). Separate repos enable fully parallel development — the web app can be built against mocked LangGraph responses before the harness is deployed.

**Extraction plan:** The `meta_harness/` directory currently lives inside `meta-agent-v5.6.0/` alongside the v0.5 reference implementation. When the Droids finish development, `meta_harness/` is extracted into its own standalone `meta-harness` repo. The web app repo (`meta-harness-web`) is created independently and can begin development immediately.

### WQ6: Real-time streaming mechanism

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | `useStream` with `streamSubgraphs: true` | SDK-native; streams parent + child graph events; `filterSubagentMessages` separates coordinator from specialist output | Requires mapping our 7 PCG child graphs to `SubagentStreamInterface` | `Selected` |
| B | Custom SSE/WebSocket layer | Full control over event format | Reimplements what `useStream` provides; must handle reconnection, backpressure, etc. | `Rejected` |
| C | Polling against LangGraph Platform API | Simplest implementation | Latency; doesn't scale; poor UX for real-time agent output | `Rejected` |

**Rationale:** `useStream` with `streamSubgraphs: true` streams all PCG and child graph events in real time. Our 7 mounted child graphs appear as subagents in the stream. `filterSubagentMessages: true` keeps the chat clean (PM messages only), with specialist work accessible via `stream.subagents` and `stream.getSubagentsByMessage()`.

### WQ8: Mission control dashboard layout (Reopened → Closed)

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Kanban-style tabs with project cards | Familiar pattern; drag-and-drop | Feels vibe-coded; consumer, not enterprise; projects don't have "lanes" | `Rejected` |
| B | Card grid with project status | Visual; scannable | Cards waste space; less information density than a table; consumer feel | `Rejected` |
| C | Enterprise table with inline phase indicators | Maximum information density; one glance = full picture; enterprise feel; minimal chrome | Less visual flair than cards | `Selected` |

**Rationale:** Tables are enterprise. Cards are consumer. A project table with inline six-dot phase indicators, active agent name, one-line status, and relative timestamp gives maximum signal in minimum space. Agency owners add a Client column for cross-client visibility. Single-project clients skip the table entirely and land in the project chat view. Click any row → project view.

**Table schema:**

| Column | Content | Width |
|---|---|---|
| Client (agency only) | Client org name | Fixed |
| Project | Project name | Flexible |
| Phase | ●●●○○○ (six dots, filled/pulsing/hollow) | Fixed ~80px |
| Agent | Active agent name (e.g., "Researcher") | Fixed ~120px |
| Status | One sentence ("Exploring SDK docs...", "Awaiting your approval") | Flexible |
| Updated | Relative time ("2m ago", "Just now") | Fixed ~80px |

**Row drill-in (click to expand):** Clicking a project row can either navigate to the project chat view OR expand inline to show additional signal before navigating. Expanded detail includes:

| Metric | Source |
|---|---|
| Developer ↔ Evaluator cycle count | Count of `(Developer, Evaluator, submit)` records in `handoff_log` |
| Developer ↔ HE cycle count | Count of `(Developer, HE, submit)` records in `handoff_log` |
| Current phase progress | `stream.values.todos` completion percentage |
| Last handoff summary | Most recent `handoff_log` entry brief |
| Pending actions | Approval gates, `ask_user` questions awaiting response |

Minimal by default (the table row). Zoom-in on demand (expanded detail). Click through to project chat view for full interaction.

### WQ11: Developer optimization interrupt UX (Closed)

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Modal dialog with diff viewer | Prominent; hard to miss | Interrupts flow; feels heavy; blocks the chat | `Rejected` |
| B | Separate page/tab for pending approvals | Organized; batch review | User must navigate away from chat; easy to miss | `Rejected` |
| C | Inline review cycle with IDE-style diff comments | Flows naturally; collaborative; agency user can iterate with Developer before eval submission | More complex than binary approve/reject | `Selected` |

**Rationale:** This is an agency-only feature — never client-facing. It covers ALL optimization changes the Developer makes to the target harness, not just system prompts:

| Artifact Type | Example |
|---|---|
| System prompt | Rewriting the greeting handler prompt |
| Tool message | Changing a tool's description or response format |
| Tool schema | Adding/removing parameters, changing types |
| API integration | Swapping an endpoint, changing auth flow |
| Starting from scratch | Developer decides to rebuild a component entirely |

**Flow (toggle-controlled):**

1. Developer makes changes during a development phase
2. Before submitting to Evaluator/HE, Developer pauses (if the agency owner has the review toggle ON)
3. All diffs are presented IDE-style in the Developer's Tier 2 observation view — file-by-file, with before/after highlighting
4. Agency user can leave inline comments on specific lines of the diffs (code-review style)
5. Developer reads comments, revises, presents updated diffs
6. Agency user and Developer cycle back and forth until both agree
7. Agency user signals "ready" → Developer submits to Evaluator/HE for evaluation
8. If the review toggle is OFF, Developer submits directly to evaluators without pausing

**Key constraints:**
- **Agency-only.** Client stakeholders never see this. It's gated by role (`agency_owner` or `agency_member`) AND the review toggle being ON.
- **Toggle-controlled.** The agency owner can enable/disable per-project. Default: OFF (autonomous). When ON, Developer pauses before every eval submission.
- **Collaborative, not gatekeeping.** The agency user isn't approving/rejecting — they're collaborating with the Developer via inline comments. The Developer can push back, explain reasoning, or incorporate feedback.
- **Scope: all target harness artifacts.** Not limited to system prompts. Any file the Developer modifies that affects the target harness behavior.

### WQ13: Evaluation cycle visualization (Closed)

| Option | Summary | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Full eval dashboard in the web app (scores, rubrics, experiments) | Complete picture without leaving the app | Duplicates LangSmith; massive build effort; maintenance burden | `Rejected` |
| B | Signal-only in web app + deep-link to LangSmith for science | Minimal build; leverages existing LangSmith investment; clean separation of concerns | Requires LangSmith access for full detail | `Selected` |
| C | Embedded LangSmith iframe | Zero build for eval detail | Iframe UX is poor; auth complexity; not enterprise | `Rejected` |

**Rationale:** Don't duplicate LangSmith. The web app is the signal layer (pass/fail, who's blocking, what's next). LangSmith is the science layer (scores, rubrics, datasets, experiments, judge calibration). The web app shows a compact eval summary card in the pipeline panel: pass/fail per QA agent, one-line failure reason, "View in LangSmith →" deep-link to the relevant experiment run. Tier 2 observation (when HE is active and user clicks in) shows eval tool calls streaming in real time.

**Eval summary card format:**
```
Phase 2 Evaluation
├── Harness Engineer: ✓ Pass (3/3 criteria met)
└── Evaluator: ✗ Fail — spec alignment issue in auth module
    → Developer revising...
    [View in LangSmith →]
```

### Post-Delivery Handoff Flow (New Decision)

**Mechanism:** Permission elevation, not ownership transfer.

| Step | What Happens |
|---|---|
| 1. Agency owner clicks "Transfer to client" in project settings | Confirmation dialog: "This will give [Client Org] full access. They can interact with PM directly and configure system prompts. This action is reversible." |
| 2. Confirm | `project_client_permissions.permission_level` → `full` |
| 3. Client experience changes | Client dashboard shows project with full controls: PM chat (interactive), system prompt config, approval gates |
| 4. Agency retains read-only visibility | Project still appears in agency mission control; agency can observe but not interact |
| 5. Reversible | Agency owner can re-scope permissions back to `observe_only` or `qa_only` at any time |

**Why not ownership transfer:** The agency might need to re-engage later (client wants changes, new features, support). Keeping the agency as the system owner with read-only visibility preserves that option. The client gets full functional access without the agency losing the ability to monitor or re-engage.

---

## 4) Architecture

### Repository Strategy and Cross-Repo Architecture (WQ21)

**Two standalone repos, zero shared code:**

```
meta-harness/                    ← extracted from meta-agent-v5.6.0/meta_harness/
  agents/                        ← 7 Deep Agent factories (PM, HE, Researcher, Architect, Planner, Developer, Evaluator)
  tools/                         ← 23 handoff tools + agent-specific tools
  graph.py                       ← PCG factory (make_graph → CompiledStateGraph)
  langgraph.json                 ← LangGraph Platform entrypoint
  pyproject.toml
  .env
  tests/

meta-harness-web/                ← new repo
  src/
    app/
      (agency)/                  ← agency owner layout (route group)
      (client)/                  ← client layout (route group)
      api/                       ← Next.js API routes (auth, org/project CRUD, integrations, permissions)
    components/
      chat/                      ← PM chat, observation mode, agent transition animations
      pipeline/                  ← six-dot timeline, activity card, handoff log
      observation/               ← per-agent Tier 2 views (IDE, eval dashboard, subagent cards, etc.)
      dashboard/                 ← mission control overview
    lib/
      supabase/                  ← auth client, RLS queries, org/project helpers
      langgraph/                 ← useStream config, PCG state TypeScript types, stream helpers
  package.json
  tailwind.config.ts
  next.config.ts
  .env.local                     ← LANGGRAPH_API_URL, SUPABASE_URL, SUPABASE_ANON_KEY, etc.
```

**Connection architecture:**

```
meta-harness-web (Vercel)
  │
  ├── useStream ──→ LANGGRAPH_API_URL (LangSmith Cloud Platform)
  │                   └── PCG → 7 Deep Agent child graphs
  │                   └── Custom routes via http.app (sandbox file browsing)
  │
  ├── Next.js API Routes ──→ SUPABASE_URL
  │                           └── auth (JWT validation, session management)
  │                           └── org/project metadata (RLS-enforced queries)
  │                           └── client permissions (observe_only/qa_only/full)
  │                           └── target prompt versions
  │
  └── Next.js API Routes ──→ Integration webhooks (Attio, Slack)
```

The `useStream` hook talks directly to the LangGraph Platform API endpoint — it does NOT go through Next.js API routes. The Next.js API routes handle everything that is NOT agent streaming: user management, org/project CRUD, client permissions, integration webhooks, system prompt versioning.

**Shared contracts (not shared code):**

| Contract | Defined By | Consumed By | Sync Mechanism |
|---|---|---|---|
| LangGraph Platform API (threads, runs, streaming) | LangGraph SDK (not us) | `useStream` in web app | SDK version pinning |
| PCG state schema (`current_phase`, `current_agent`, `handoff_log`, `pending_handoff`) | `meta-harness` repo (`graph.py` → `ProjectCoordinationState`) | `stream.values.*` in web app (TypeScript interface) | AD-WEBAPP documents the contract; TypeScript interface mirrors Python TypedDict |
| `HandoffRecord` schema | `meta-harness` repo | Web app pipeline panel rendering | Same as above |
| Supabase JWT format (`org_id`, `role` claims) | Supabase Auth config | Both: Next.js middleware + LangGraph `@auth.authenticate` | Supabase project config (single source of truth) |
| Custom API routes (sandbox file browsing) | `meta-harness` repo (`langgraph.json` `http.app`) | Web app fetch calls for Developer IDE view | Documented in AD; route schemas in spec |

**Local development workflow:**

While building the web app, run the harness locally with `langgraph dev` (port 3100, as configured in `.factory/services.yaml`). The web app points `LANGGRAPH_API_URL=http://localhost:3100` during dev.

| Dev Phase | Harness Available? | Web App Strategy |
|---|---|---|
| Before Droids finish | No | Mock LangGraph Platform API responses; build UI components against static/fixture data |
| Droids finish, harness running locally | Yes (`langgraph dev` on port 3100) | `LANGGRAPH_API_URL=http://localhost:3100`; develop against live local backend |
| Harness deployed to LangSmith Cloud | Yes (production endpoint) | `LANGGRAPH_API_URL=https://meta-harness-xyz.langsmith.dev`; full integration |

**Extraction and deployment timeline:**

1. Droids finish the harness → extract `meta_harness/` from `meta-agent-v5.6.0/` into standalone `meta-harness` repo
2. Deploy `meta-harness` to LangSmith Cloud Platform (dev deployment via `langgraph deploy`)
3. Create `meta-harness-web` repo, scaffold Next.js + Supabase + `useStream` + Tailwind + shadcn/ui
4. Develop web app against deployed (or local) harness
5. Deploy web app to Vercel

Steps 3–4 can start NOW, in parallel with the Droids, using mocked LangGraph responses. The clean API boundary means zero dependency on harness completion for frontend development.

### Relationship to ADR-001 (Harness AD)

The web app is a **client** of the harness. It does not modify the PCG, agent topology, middleware stack, or handoff protocol. It consumes the LangGraph Platform API and adds:

1. **Presentation layer** — renders agent output, pipeline state, evaluation results
2. **Integration layer** — CRM, Slack, WhatsApp connectors that feed context to PM
3. **Configuration surface** — target harness system prompt editing with HE re-eval trigger
4. **Multi-tenancy layer** — auth, project isolation, user management

```
Browser
  → Next.js Frontend (@langchain/react useStream)
    → LangGraph Platform API (useStream connects directly)
      → PCG (ADR-001)
        → 7 Deep Agent child graphs (streamed via streamSubgraphs)
    → Next.js API Routes (thin backend)
      → User/Org DB (auth metadata, integration tokens, project config)
      → Integration Connectors (Attio, Slack, WhatsApp)
      → File Browser API (langgraph.json http.app for sandbox)
```

### SDK Coverage Analysis (Updated 2026-04-14)

The Deep Agents / LangChain frontend SDK provides significant out-of-the-box capability. This analysis maps SDK features to our requirements, informed by direct documentation review.

**SDK provides (zero custom code):**

| SDK Feature | Our Mapping | Reference |
|---|---|---|
| `useStream` hook (`@langchain/react`, also Vue/Svelte/Angular) | Real-time connection to PCG via LangGraph Platform. Single hook provides reactive state: messages, tool calls, interrupts, custom state values, subagent streaming. | [deepagents/frontend/overview](https://docs.langchain.com/oss/python/deepagents/frontend/overview) |
| `streamSubgraphs: true` (passed in `submit()` options) | Streams all 7 child graph events (PM, HE, Researcher, Architect, Planner, Developer, Evaluator). Must set recursion limit ≥100 for deep agent workflows. | [subagent-streaming](https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming) |
| `filterSubagentMessages: true` | Chat shows PM/coordinator messages only; specialist work accessible via `stream.subagents` and `stream.getSubagentsByMessage()`. Essential — without it, all agent tokens interleave into unreadable output. | Same |
| `SubagentStreamInterface` | `{ id, status: pending\|running\|complete\|error, messages, result, toolCall: { id, name, args: { description, subagent_type } }, startedAt, completedAt }` — maps 1:1 to our observation mode. Provides task description, specialist type, real-time message stream, timing, and status lifecycle per subagent. | Same |
| `stream.getSubagentsByMessage(msg.id)` | Links coordinator messages to the subagents they spawned — key API for rendering subagent cards inline with the message that triggered them. | Same |
| `stream.subagents` (Map) | Global access to all subagent instances — useful for the mission-control pipeline panel showing all active/completed specialist work. | Same |
| `stream.values.todos` | Agent todo progress (pending → in\_progress → completed) — maps to pipeline phase progress. Reactive updates, no polling. | [todo-list](https://docs.langchain.com/oss/python/deepagents/frontend/todo-list) |
| `stream.values.*` (any custom state key) | Exposes `handoff_log`, `current_phase`, `current_agent` from PCG state — maps to pipeline observability panel. TypeScript type safety via generic parameter. | Same |
| Sandbox three-panel pattern | File tree + diff viewer + chat for Developer agent workspace. Real-time file sync by watching `ToolMessage` instances for `write_file`/`edit_file`/`execute`. Thread-scoped sandboxes recommended for production. | [sandbox](https://docs.langchain.com/oss/python/deepagents/frontend/sandbox) |
| `langgraph.json` `http.app` | Custom FastAPI endpoints served alongside LangGraph API — used for file browsing, sandbox access, and any custom routes. | Same |
| `@auth.authenticate` + `@auth.on` | LangGraph Platform auth + authorization with metadata filtering for multi-tenant access | [langsmith/auth](https://docs.langchain.com/langsmith/auth) |
| `interrupt_on` + resume | HITL interrupts — maps to developer optimization interrupts and approval gates. First-class in the streaming API. | [langchain/frontend/overview](https://docs.langchain.com/oss/python/langchain/frontend/overview) |
| Generative UI patterns | Tool call rendering — maps to handoff cards, eval result cards. `useStream` is UI-agnostic, works with any component library. | Same |
| Synthesis phase detection | When all subagents are `complete` but `stream.isLoading` is still `true`, the coordinator is synthesizing. Maps to "PM is reviewing Researcher's findings..." indicator. | [subagent-streaming](https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming) |
| RemoteGraph | Deployed agents can call other deployed agents transparently (local/remote agnostic). Enables future distributed agent topology. | [langsmith/deployment](https://docs.langchain.com/langsmith/deployment) |
| Agent Server API | Threads, Thread Runs, Assistants, Store, A2A, MCP endpoints. Self-documenting at `/docs`. | [langsmith/server-api-ref](https://docs.langchain.com/langsmith/server-api-ref) |

**Observation Mode SDK Mapping (NEW):**

The "spectacle" experience — watching agents work — maps directly to SDK primitives:

| What User Sees | SDK Source | Rendering Strategy |
|---|---|---|
| Active agent identity + status | `stream.values.current_agent` + `stream.isLoading` | Agent avatar/name in chat header; pulse indicator when active |
| Agent's tool calls in real time | `stream.messages` (ToolMessage instances) | Visual cards: tool name, args summary, loading → result |
| Subagent spawning + progress | `stream.subagents` Map + `SubagentStreamInterface.status` | Collapsible subagent cards with status badges, task descriptions, timing |
| Subagent real-time output | `SubagentStreamInterface.messages` | Streaming text within each subagent card |
| Synthesis phase | All subagents `complete` + `stream.isLoading === true` | "Synthesizing results from N subagents..." indicator |
| Phase transitions / handoffs | `stream.values.current_phase` + `stream.values.handoff_log` | Pipeline panel updates; transition animation |
| `ask_user` interrupts | `interrupt` state from `useStream` | Input bar reactivates; interrupt card appears with question |
| Todo/plan progress | `stream.values.todos` | Progress bar + todo list in pipeline panel |

**We build (product-specific):**

| Feature | Why SDK Doesn't Cover It |
|---|---|
| Project dashboard / mission control | SDK is agent-scoped, not project-scoped; we need multi-project overview with phase/agent/status at a glance |
| Handoff/phase visualization (pipeline panel) | SDK streams the raw state (`stream.values.handoff_log`, `stream.values.current_phase`); we render the pipeline timeline and transition animations |
| Observation mode UX | SDK provides the data (`SubagentStreamInterface`, tool messages); we design the spectacle — how tool calls render as visual cards, how subagent spawning animates, how synthesis phases indicate |
| Client permission model | Agency owner toggles per-project: client read-only vs. restricted PM chat vs. full access. Not an SDK concern. |
| Context-dependent landing | Single project → chat view; multiple projects → mission control overview. Routing logic based on user role + project count. |
| CRM/Slack integration connectors | External API integrations, not LangGraph concerns |
| System prompt configuration surface | Product-specific feature; requires custom API + UI |
| Landing page / marketing | Static/SSR pages, not agent-related |
| User/org management beyond LangGraph auth | LangGraph `@auth` handles thread/run access; user profiles, org membership, subscription are separate |
| Subscription/billing | Business layer, not agent layer |

**Key insight:** The SDK solves the *data transport* problem (streaming, state sync, auth). We solve the *product surface* problem (what to show, how to organize, what actions to expose). The boundary is clean: `useStream` delivers the data; our React components render it.

### Agency Model (v1 Access Control)

The web app serves three user roles with different access patterns:

```
Agency (Jason / future AI agencies)
  ├── Client A (stakeholder, their own projects)
  │     └── Team members (seats)
  ├── Client B (stakeholder, their own projects)
  │     └── Team members (seats)
  └── Agency's own projects (internal)
```

**Role model:**

| Role | Sees | Dashboard | PM Interaction |
|---|---|---|---|
| Agency Owner | All clients' projects + own internal projects | Agency mission control: client list, cross-project status, seat management | Full — direct PM conversation, project changes, all controls |
| Agency Member | Assigned clients/projects only | Scoped agency dashboard | Full on assigned projects |
| Client Stakeholder (agency-managed phase) | Only their org's projects; read-only observation mode | Client observation view: pipeline progress, agent activity spectacle, restricted or no PM chat | Configurable by agency owner: disabled, Q&A-only (PM can answer questions, document open items, but cannot make project changes), or full |
| Client Stakeholder (post-delivery phase) | Only their org's projects; full access | Client dashboard: their projects, PM chat, system prompt config | Full — own credentials, full PM authority |
| Client Team Member | Only their org's projects (limited config) | Same as stakeholder, minus system prompt editing | Same as their stakeholder's permission level |

**Client permission model (agency-managed projects):**

The agency owner configures per-project client permissions via a toggle:

| Permission Level | Client Can See | Client Can Do | PM Behavior |
|---|---|---|---|
| `observe-only` | Pipeline progress, agent activity, artifacts | Nothing — pure spectator | PM ignores client messages (input disabled) |
| `qa-only` | Pipeline progress, agent activity, artifacts, PM chat | Ask questions, request features, flag concerns | PM answers questions, documents open items in project memory, but does NOT modify project scope, requirements, or trigger pipeline actions |
| `full` | Everything | Full PM interaction, system prompt config, approval gates | PM operates with full authority |

Default for new agency-managed projects: `observe-only`. Agency owner upgrades as trust/need dictates. Post-delivery handoff sets permission to `full` and transfers org ownership.

**Access control enforcement:**
- **Supabase RLS** — org-scoped queries; agency users can read across managed clients; client users cannot
- **LangGraph Platform `@auth.on`** — reads JWT `org_id` + `role` claims; filters threads by org; agency role gets expanded filter
- **Next.js middleware** — reads JWT role claim; routes to agency or client dashboard layout

**Same Next.js app, different layouts.** App Router route groups: `app/(agency)/` vs `app/(client)/`.

**Supabase schema sketch (v1):**

```sql
organizations (id, name, type: 'agency'|'client')
agency_clients (agency_id, client_id)
memberships (user_id, org_id, role: 'owner'|'member'|'stakeholder')
integration_tokens (org_id, provider, access_token_encrypted, refresh_token_encrypted)
target_prompt_versions (org_id, project_id, prompt_text, version, created_by, created_at)
project_client_permissions (project_id, client_org_id, permission_level: 'observe_only'|'qa_only'|'full', set_by, updated_at)
```

### Locked Decisions

| ID | Decision | Locked | Rationale |
|---|---|---|---|
| W1 | Web app is the primary product surface | Yes | Go-to-market requires professional demo; most users prefer browser over terminal |
| W2 | CLI is the power-user surface, not the primary surface | Yes | CLI for local dev and power users; web app for everyone else |
| W3 | Web app is a client of LangGraph Platform, not a custom server | Yes | Leverages managed checkpointer/store/auth; avoids reimplementing LangGraph Platform capabilities |
| W4 | `thread_id = project_id` guarantees project isolation | Yes | Inherited from ADR-001; no additional isolation layer needed in the web app |
| W5 | PM is the primary user-facing agent; chat follows the active agent | Yes | Inherited from ADR-001; PM is the conversational partner, but the chat visually evolves to show whichever agent is currently working. Agents with `AskUserMiddleware` (PM, Architect) can surface questions directly. |
| W6 | Multi-tenant SaaS with user accounts | Yes | Enterprise/SMB requirement; project isolation per user/org |
| W7 | Integrations feed PM context and enable PM invocation | Yes | PM needs CRM/Slack context; users invoke PM from Slack/WhatsApp |
| W8 | Developer optimization interrupts surface as user-actionable events | Yes | When Developer wants to change system prompt to meet eval criteria, user inspects and approves/rejects |
| W9 | Target harness system prompt is configurable by end users via web app | Yes | New business logic → user edits prompt → triggers Harness Engineer re-evaluation cycle |
| W10 | Landing page / marketing site is part of the web app | Yes | Users install CLI from the website; subscription signup; product info |
| W11 | PM chat is the central interaction surface of the entire app | Yes | Chat with PM is the primary CTA from every page; PM can pull context from CRM, filesystem, memory, and other projects |
| W12 | Chat follows the active agent (observation mode) | Yes | When a specialist is working, the chat becomes an observation surface showing tool calls, subagent activity, and synthesis. Input is disabled until PM regains control or `ask_user` fires. |
| W13 | Agency owner controls client interaction permissions per-project | Yes | Toggle whether client can chat with PM; if enabled, PM operates in restricted mode (Q&A only, no project changes) during agency-managed development phase |
| W14 | Two-phase client experience: observation (agency-managed) → full access (post-delivery) | Yes | During development, client observes. Post-delivery, client gets full PM interaction and system prompt configuration. |
| W15 | Dashboard is mission-control, not kanban | Yes | Enterprise feel; context-dependent landing (single project → chat view; multiple projects → overview with one-click into chat) |
| W16 | Observation mode uses two-tier progressive disclosure | Yes | Tier 1 (default): compact activity stream, identical for all agents. Tier 2 (click-to-expand): agent-specific spectacle (IDE for Developer, eval dashboard for HE, subagent cards for Researcher, etc.). Don't emit everything by default; let user drill in. |
| W17 | Pipeline timeline shows full journey, minimal chrome | Yes | Six dots on a horizontal line (filled/pulsing/hollow) + one current-activity card. Expandable for handoff log and todo detail. Maximum signal, minimum cognitive load. |
| W18 | Separate repos: `meta-harness` (Python) + `meta-harness-web` (Next.js) | Yes | Zero shared source code. Connected via LangGraph Platform API (`useStream` → `LANGGRAPH_API_URL`). Enables fully parallel development. Local dev: `langgraph dev` on port 3100. |
| W19 | Mission control is an enterprise table, not cards or kanban | Yes | Rows = projects. Columns: Project, Phase (six dots inline), Agent, Status (one sentence), Updated (relative time). Agency owner adds Client column. Click row → project chat view. |
| W20 | Developer optimization interrupts are agency-only with IDE-style collaborative review | Yes | Agency-only (never client-facing). Toggle-controlled per-project. Covers all target harness artifacts (system prompts, tool messages, tool schemas, APIs, rebuilds). IDE-style diffs with inline comments. Agency user and Developer cycle until both agree, then submit to evaluators. |
| W21 | Eval visualization: web app = signal layer, LangSmith = science layer | Yes | Compact pass/fail card in pipeline panel. Deep-link to LangSmith for full experiment detail. Don't duplicate LangSmith in the web app. |
| W22 | Post-delivery handoff is a permission elevation, not an ownership transfer | Yes | Agency owner clicks "Transfer to client" → `permission_level` set to `full`. Agency retains read-only visibility. Project history preserved. Reversible. |

### Open Questions

#### Round 0: Repository & Infrastructure

| Q# | Topic | Status | Depends On |
|---|---|---|---|
| WQ21 | Repository strategy (mono vs. separate) | **Closed** — Separate repos: `meta-harness` (Python, LangGraph Cloud) + `meta-harness-web` (Next.js, Vercel). Zero shared source code. Connected via LangGraph Platform API. | — |

#### Round 1: Foundation

| Q# | Topic | Status | Depends On |
|---|---|---|---|
| WQ1 | Frontend framework | **Closed** — Next.js + `@langchain/react` + Tailwind + shadcn/ui | — |
| WQ2 | Backend API layer | **Closed** — Next.js App Router API routes | WQ1 ✓, WQ3 ✓ |
| WQ3 | LangGraph Platform integration pattern | **Closed** — `useStream` direct to LangGraph Platform | — |
| WQ4 | Authentication provider | **Closed** — Supabase Auth (JWTs carry org_id + role) | — |
| WQ5 | Database for user/org/project metadata | **Closed** — Supabase Postgres with RLS | WQ4 ✓ |
| WQ6 | Real-time streaming mechanism | **Closed** — `useStream` with `streamSubgraphs: true` | WQ1 ✓, WQ3 ✓ |
| WQ7 | Deployment infrastructure | **Closed** — Vercel (Next.js) + LangSmith Cloud (PCG) | WQ2 ✓, WQ5 ✓ |

#### Round 2: Product Surface

| Q# | Topic | Status | Depends On |
|---|---|---|---|
| WQ8 | Project dashboard layout and navigation | **Closed** — Enterprise table view (not kanban, not cards). Each row = one project with inline six-dot phase indicator, active agent, one-line status, relative timestamp. Agency owner adds Client column. Single-project clients skip table, land in chat view. Click any row → project chat view. | WQ1 ✓ |
| WQ9 | PM chat UX | **Closed** — PM chat is the central surface; accessible from everywhere; primary CTA; PM pulls context from CRM/filesystem/memory/other projects | WQ1 ✓, WQ6 ✓ |
| WQ10 | Pipeline observability surface (phase, handoff, eval) | **Closed** — Phase diagram + handoff log + phase progress bars | WQ1 ✓, WQ6 ✓ |
| WQ11 | Developer optimization interrupt UX | **Closed** — Agency-only. Toggle-controlled IDE-style collaborative review cycle. Covers all target harness artifacts (system prompts, tool messages, tool schemas, APIs, rebuilds). Inline diff comments, Developer ↔ agency user iteration, then submit to evaluators. | WQ9 ✓ |
| WQ12 | Target harness system prompt configuration UX | **Closed** — Config tab: system prompt editor + version history + datasets view (optional) + "Trigger Re-evaluation" | WQ9 ✓ |
| WQ13 | Evaluation cycle visualization | **Closed** — Web app shows signal, not science. Compact eval summary card in pipeline panel: pass/fail per QA agent + one-line failure reason. "View in LangSmith →" deep-link for full experiment detail. Tier 2 observation shows eval tool calls in real time. LangSmith is the science layer; web app is the signal layer. | WQ10 ✓ |

**Prototype exploration posture:** Round 2 closures commit to *what surfaces exist*, not *how they're designed*. The prototype is a discovery tool — each iteration reveals what experience and user stories we want to provide. Design style, layout specifics, and interaction patterns remain fluid until we've iterated enough to have confidence.

**Prototype discoveries (2026-04-13, updated 2026-04-14):**

- **Dashboard (WQ8):** Kanban rejected — feels vibe-coded, not enterprise. Mission-control paradigm adopted instead. Recent Activity + Client Overview retained as high-value surfaces. The landing experience depends on context:
  - **Single active project:** Land directly in the project view (chat + live signal panel).
  - **Multiple projects (agency owner or multi-project client):** Land on mission-control overview showing all projects with phase/agent/status at a glance, one click into any project's chat view.
  - **Client in observation mode:** Read-only project view showing pipeline progress and agent activity as a spectacle.

- **Chat (WQ9):** PM chat is THE central interaction — but the chat is not PM-exclusive. The chat follows `current_agent` from PCG state. When PM hands off to Researcher, the chat visually transitions to show the Researcher's work: tool calls, subagent spawning, synthesis. The chat area becomes an observation surface during specialist work — input is disabled (observation mode) until the agent finishes or surfaces an `ask_user` question. PM's conversational input bar reactivates on handoff return. Subagent cards inline confirmed. Interrupt card interaction pattern still exploring.

- **Observation Mode (NEW):** When a specialist agent is active, the chat becomes a spectacle — the user watches the agent work. This is NOT narration; it's visual transparency of agent cognition:
  - **Two-tier progressive disclosure model:**
    - **Tier 1 (default, always visible):** Compact activity stream — identical for all agents. Single-line status indicator showing current action, updated in real time. Tool calls appear as compact one-line entries ("Reading LangChain docs...", "Writing architecture spec...", "Running eval harness..."). Minimal cognitive load.
    - **Tier 2 (click-to-expand, agent-specific):** The spectacle. Each agent gets its own observation experience, rendered only when the user clicks into it.
  - **Per-agent Tier 2 experiences:**
    - **PM:** No Tier 2 needed — PM IS the interactive chat surface.
    - **Researcher:** Subagent cards — see each sub-researcher's target, findings, sources. Collapsible cards per subagent with real-time streaming text. SDK: `stream.subagents`, `SubagentStreamInterface`, `getSubagentsByMessage()`.
    - **Architect:** Artifact preview — documents forming in real time, file diffs as specs/schemas/prompts are written. SDK: `ToolMessage` watching for `write_file`/`edit_file`.
    - **Planner:** Todo list formation — plan materializes as structured todo list with phases, tasks, eval breakpoints. SDK: `stream.values.todos`.
    - **Developer:** Full IDE view (richest mode) — three-panel sandbox (file tree, diff viewer, activity). Files created, code written, diffs in real time. SDK: sandbox pattern via `http.app` file browsing API + `ToolMessage` file sync.
    - **Harness Engineer:** Eval dashboard — experiment runs, dataset usage, scoring results, judge calibration, LangSmith trace links. SDK: `stream.values.*` for custom HE state + `ToolMessage` for eval tool calls.
    - **Evaluator:** Review feed — spec compliance checks, UI interaction recordings (if applicable), pass/fail verdicts per phase item. SDK: `stream.values.*` for custom Evaluator state + `ToolMessage`.
  - Input bar is dimmed/disabled during observation; reactivates when PM regains control or `ask_user` fires

- **Client Permission Model (NEW):** Two distinct client experiences based on project lifecycle:
  - **During development (agency-managed):** Client gets a read-only observation window. Agency owner configures whether client can chat with PM, and if so, PM operates in restricted mode (can answer questions, document open items/feature requests, but cannot make project changes).
  - **Post-delivery (client-owned):** Client gets full experience — own credentials, full PM interaction authority, system prompt configuration, the works.
  - Agency owner has a toggle per-project controlling client interaction permissions.

- **Pipeline (WQ10):** Phase diagram + handoff log + phase progress confirmed as high-value surfaces. Jason: "really, really likes" the pipeline visibility.
  - **Pipeline timeline design (decided):** Full pipeline always visible — all six phases (scoping → research → architecture → planning → development → acceptance) rendered as a single horizontal line with six dots. Completed = filled, current = pulsing, future = hollow. ~40px vertical, zero text unless hovered. Lives at the top of the right contextual panel.
  - **Current activity card:** Below the timeline, one card showing the current activity. One sentence, one status. "Researcher — exploring LangChain ecosystem" or "Developer — Phase 2 of 4" or "Awaiting your approval." Default right panel = six dots + one card.
  - **Expandable detail:** Handoff log and todo list unfold below on user expansion. Default is minimal; depth is available on demand.
  - Exact visual treatment still exploring.

- **Config (WQ12):** System prompt editor + version history + "Trigger Re-evaluation" confirmed. New discovery: datasets view for eval/experiment datasets alongside the system prompt — keeps the full picture in one place, with LangSmith as the deep-dive observability surface. Still exploring whether this is a tab, a section, or a separate page.

- **Open exploration items:**
  - Product naming ("Meta Harness" is a working title)
  - Observation mode visual design details (exact animations, color palette, typography for agent-specific Tier 2 views)
  - Client permission toggle UX (agency owner configuration surface — exact placement in project settings)

#### Round 3: Integrations

| Q# | Topic | Status | Depends On |
|---|---|---|---|
| WQ14 | CRM integration architecture (Attio-first) | Open | WQ2 |
| WQ15 | Communication hub integration (Slack, WhatsApp) | Open | WQ2 |
| WQ16 | Integration context injection into PM | Open | WQ14, WQ15 |
| WQ17 | PM invocation from external surfaces | Open | WQ14, WQ15 |

#### Round 4: Business

| Q# | Topic | Status | Depends On |
|---|---|---|---|
| WQ18 | Subscription tier model | Open | WQ4, WQ5 |
| WQ19 | API key management (user-provided vs hosted) | Open | WQ2 |
| WQ20 | Usage metering and limits | Open | WQ18, WQ19 |

---

## 5) Spec Handoff

### Dependency Map

```
Layer 0: Repository & Infrastructure (WQ21)
  → Layer 1: Foundation (WQ1–WQ7)
    → Layer 2: Product Surface (WQ8–WQ13)
      → Layer 3: Integrations (WQ14–WQ17)
        → Layer 4: Business (WQ18–WQ20)
```

### Spec-Owns List

| Topic | AD-Locked Constraint | Spec Owns |
|---|---|---|
| Repo structure | Separate repos; web app in `meta-harness-web` (W18) | Exact directory layout, module naming, shared contract TypeScript types |
| Frontend components | Must stream in real time; must surface pipeline state (W5, W10) | Component library, layout, animations, responsive breakpoints |
| API design | Must be client of LangGraph Platform (W3) | Endpoint design, request/response schemas, error codes |
| Auth flow | Must support multi-tenant (W6) | Login/signup UI, session management, org switching |
| Chat interface | PM is primary user-facing agent; chat follows active agent (W5, W12) | Message rendering, observation mode UX, tool call cards, subagent cards, synthesis indicators, input state management (active vs. disabled), agent transition animations |
| Pipeline visualization | Must surface phase, handoff, eval status | Widget design, animation, information density |
| Developer interrupts | Agency-only, toggle-controlled, covers all target harness artifacts (W20) | IDE-style diff viewer component, inline comment system, review cycle state management, toggle UX in project settings |
| System prompt config | Must trigger HE re-eval on business logic change (W9) | Editor UX, confirmation flow, version history |
| Client permissions | Agency owner controls client interaction per-project (W13, W14) | Permission toggle UX, PM restricted mode behavior, post-delivery handoff flow |
| Integrations | Must feed PM context and enable invocation (W7) | OAuth flow, connector config UI, context preview |
| Landing page | Must exist (W10) | Copy, design, SEO, analytics |

---

## 6) New Features Not in ADR-001

### 6.1 Developer Optimization Interrupts

When the Developer agent modifies any target harness artifact during an optimization cycle, this surfaces as a **collaborative review** in the web app (agency-only, toggle-controlled):

- **Scope:** All target harness artifacts — system prompts, tool messages, tool schemas, API integrations, or full component rebuilds. Not limited to system prompt changes.
- **Trigger:** Developer completes changes for a phase and is about to submit to Evaluator/HE. If the agency owner's review toggle is ON, Developer pauses and presents diffs.
- **Surface:** IDE-style diff view in the Developer's Tier 2 observation panel. File-by-file before/after with syntax highlighting. Agency user can leave inline comments on specific lines.
- **Flow:** Agency user reviews diffs → leaves inline comments → Developer revises → updated diffs presented → cycle until both agree → agency user signals "ready" → Developer submits to evaluators.
- **Toggle:** Per-project, agency-owner-controlled. Default OFF (Developer submits autonomously). When ON, Developer pauses before every eval submission.
- **Visibility:** Agency-only. Client stakeholders never see this surface regardless of their permission level.
- **Constraint:** This leverages the same `interrupt_on` mechanism from the SDK. The Developer's middleware detects the review toggle and either pauses (toggle ON) or proceeds (toggle OFF) before emitting the `Command.PARENT` for eval submission.

### 6.2 Target Harness System Prompt Configuration

End users (with appropriate permissions) can modify the system prompt of their deployed target harness:

- **When:** New product, new business logic, or any change that affects agent behavior
- **Flow:** User edits prompt → confirmation dialog → Harness Engineer re-evaluation triggered → new eval criteria generated → Developer optimization cycle begins
- **Constraint:** Prompt changes that affect business logic MUST trigger HE re-evaluation. Cosmetic changes (tone, style) MAY skip HE.
- **Scope:** Only target harness system prompts are configurable. Meta Harness agent prompts are NOT user-configurable.

*Exact trigger mechanism and "business logic vs cosmetic" classification is an open question.*

---

## 7) Risks, Tradeoffs, and Mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Web app scope expands to become its own product team | H | H | Strictly scope v1 to demo + basic SaaS; defer advanced features | @Jason |
| LangGraph Platform API limitations block real-time streaming | M | H | Verify streaming capabilities early; fallback to custom SSE layer | @Jason |
| CRM/Slack integrations become a distraction from core product | M | M | Ship Attio + Slack only; defer WhatsApp and others | @Jason |
| Developer interrupt UX confuses non-technical stakeholders | M | M | Design interrupt cards for non-technical audiences; hide diff details by default | @Jason |
| System prompt configurability leads to broken harnesses | H | H | HE re-evaluation is mandatory for business logic changes; version history with rollback | @Jason |
| Multi-tenancy adds complexity before product-market fit | M | M | Start with single-user; add org/team features incrementally | @Jason |

---

## 8) Security / Privacy / Compliance

- Multi-tenant data isolation: project data scoped by `project_id` (thread_id); user/org metadata in separate DB
- API keys: user-provided keys stored encrypted at rest; never logged; scoped to user's projects
- Integration OAuth tokens: stored encrypted; revocable; scoped to minimum permissions
- PII: agent prompts and tools must not log or transmit stakeholder PII beyond the LLM API call
- Access model: RBAC per org (admin, member, viewer) — exact roles are spec territory
- Retention: user-managed with org-level policies (v2)

---

## 9) Decision Index

*To be populated as decisions close.*

---

## 10) Changelog

| Date | Change | Author |
|---|---|---|
| 2026-04-13 | Initial draft — locked decisions W1–W10, open questions WQ1–WQ20 | @Jason + Cascade |
| 2026-04-14 | Corrected W5 (PM is primary, not sole; chat follows active agent). Reopened WQ8 (kanban rejected → mission-control). Added W12–W15 (observation mode, client permissions, two-phase client experience, mission-control dashboard). Added client permission model with `observe_only`/`qa_only`/`full` levels. Updated SDK Coverage Analysis with direct documentation research (subagent streaming, todo list, sandbox, HITL, synthesis detection). Added Observation Mode SDK Mapping table. Updated Spec-Owns list. | @Jason + Kiro |
| 2026-04-14 | Added W16–W17 (two-tier progressive disclosure for observation mode, pipeline timeline design). Defined per-agent Tier 2 observation experiences: Developer gets full IDE view, HE gets eval dashboard, Researcher gets subagent cards, Architect gets artifact preview, Planner gets todo formation, Evaluator gets review feed. Pipeline timeline: six dots + one card as default, expandable for detail. | @Jason + Kiro |
| 2026-04-14 | Added WQ21 (repo strategy) as Round 0. Locked W18: separate repos (`meta-harness` Python + `meta-harness-web` Next.js). Added full repo structure, connection architecture diagram, shared contracts table, local dev workflow (langgraph dev port 3100), extraction/deployment timeline. Updated dependency map and Spec-Owns list. | @Jason + Kiro |
| 2026-04-14 | Closed all Round 2 open questions. WQ8: enterprise table (W19). WQ11: inline chat card for interrupts (W20). WQ13: signal layer in web app, science layer in LangSmith (W21). Added post-delivery handoff flow as permission elevation (W22). All 22 locked decisions (W1–W22) and 21 questions (WQ1–WQ21) now closed. AD ready for spec transition. | @Jason + Kiro |
| 2026-04-14 | Refined WQ8: added row drill-in with cycle counts (Dev↔Evaluator, Dev↔HE), phase progress, pending actions. Refined WQ11: expanded from binary approve/reject to collaborative IDE-style review cycle. Scope broadened from system prompts to all target harness artifacts. Agency-only, toggle-controlled. Updated §6.1, W20, Spec-Owns. | @Jason + Kiro |
