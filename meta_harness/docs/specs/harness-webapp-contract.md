# Harness Web App Contract

> Migrated from `AD.md` §11–§12 on 2026-04-21. This document is the implementation specification for harness-side auth and deployment configuration required by the Meta Harness web app.
> Architecture decision: the web app uses LangGraph Platform custom auth with Supabase JWTs. This doc specifies *how* — handler schemas, `langgraph.json` requirements, CORS config.

---

## 1) Auth Contract — Harness-Side Requirements

### Context

The web app's `useStream` hook connects directly from the browser to the LangGraph Platform API. The platform provides an `Auth` object (`from langgraph_sdk import Auth`) with two decorator patterns:

1. `@auth.authenticate` — middleware that runs on every request, validates credentials, returns user identity
2. `@auth.on` — resource-level authorization handlers that stamp metadata on resources and return filters to restrict access

The web app sends Supabase JWTs in the `Authorization` header; the harness validates them and filters threads by `org_id`.

### What the Harness Must Implement

**File:** `src/security/auth.py` (new file in the harness repo)

**Registration:** Add to `langgraph.json`:
```json
{
  "auth": {
    "path": "src/security/auth.py:auth"
  }
}
```

**Required handlers:**

| Handler | Decorator | Responsibility |
|---|---|---|
| `get_current_user` | `@auth.authenticate` | Validate Supabase JWT (HS256, `audience="authenticated"`). Extract `sub`, `org_id`, `role` from claims. For agency users (`agency_owner`, `agency_member`), look up managed client org IDs from Supabase `agency_clients` table. Return `MinimalUserDict` with `identity`, `org_id`, `role`, `permissions`, `managed_org_ids`. |
| `on_thread_create` | `@auth.on.threads.create` | Stamp `metadata["org_id"] = ctx.user.org_id` on new threads. Return `{"org_id": ctx.user.org_id}` filter. |
| `on_thread_read` | `@auth.on.threads.read` | For client users: return `{"org_id": ctx.user.org_id}`. For agency users: return `{"org_id": {"$contains": [own_org_id, ...managed_client_org_ids]}}` using the `$contains` filter operator. |
| `on_run_create` | `@auth.on.threads.create_run` | Stamp `metadata["org_id"]` on runs. Inherit thread's org filter. |

**Key SDK details:**
- `Auth` is imported from `langgraph_sdk`, not `langgraph`
- `@auth.authenticate` can accept `authorization: str | None` as a named parameter — the platform extracts the `Authorization` header value automatically
- `@auth.on` handlers receive `ctx: Auth.types.AuthContext` (contains `ctx.user` with all fields from `MinimalUserDict`) and `value: dict` (the resource payload)
- Handlers return a filter dict that LangGraph Platform applies to all subsequent operations on that resource type
- Filter operators: `$eq` (exact match, default), `$contains` (list membership)
- The authenticated user's info is automatically available to the graph at `config["configuration"]["langgraph_auth_user"]` — no custom plumbing needed

**Agent-accessible user context:** After `@auth.authenticate` runs, the PCG can access the user's identity, role, and org_id via `config["configuration"]["langgraph_auth_user"]`. This enables the PM agent to adapt behavior based on the caller's role (e.g., restrict scope modifications for `qa_only` clients) without any custom middleware or state injection.

### Dependencies

- **Supabase project JWT secret** — needed to validate JWTs. Must be available as an environment variable (`SUPABASE_JWT_SECRET`).
- **Supabase client** — needed to look up `agency_clients` relationships for agency users. The auth handler needs read access to the `agency_clients` table.
- **`langgraph_sdk`** — the `Auth` object and types are in this package. Ensure it's in `pyproject.toml` dependencies.

### Why This Matters

Without these handlers:
- Any authenticated user can stream any thread on the platform (no tenant isolation)
- The web app's multi-tenant model (agency → client org hierarchy) has no enforcement at the agent streaming layer
- Client permission levels (`observe_only`, `qa_only`, `full`) are UI-only — a client with a valid JWT could bypass the frontend and create runs directly

With these handlers:
- Thread isolation is enforced at the LangGraph Platform layer before the PCG even sees the request
- Agency users get cross-org visibility via `$contains` metadata filters
- The PM agent can read the caller's role from `config["configuration"]["langgraph_auth_user"]` and adjust behavior accordingly

### Reference

- [LangGraph Platform Auth Conceptual Guide](https://docs.langchain.com/langgraph-platform/auth)
- [Tutorial Part 1: Set up custom authentication](https://docs.langchain.com/langsmith/set-up-custom-auth)
- [Tutorial Part 2: Make conversations private](https://docs.langchain.com/langsmith/resource-auth)
- [Auth API Reference](https://reference.langchain.com/python/langgraph-sdk/auth/Auth)
- [AD-WEBAPP.md §4 Architecture — LangGraph Platform Auth Coordination](../AD-WEBAPP.md)

### Local SDK References

The `Auth` class and all handler types live in the local venv. Droids should consult these for exact type signatures:

| What | Local Path |
|---|---|
| `Auth` class (decorators, handler registration, `on` property) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/__init__.py` |
| `MinimalUserDict` (return type for `@auth.authenticate`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/types.py:164` |
| `AuthContext` (first param of `@auth.on` handlers, contains `ctx.user`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/types.py:390` |
| `ThreadsCreate` value type (`@auth.on.threads.create`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/types.py:443` |
| `ThreadsRead` value type (`@auth.on.threads.read`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/types.py:470` |
| `RunsCreate` value type (`@auth.on.threads.create_run`) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/types.py:543` |
| `HTTPException` (for rejecting requests) | `.venv/lib/python3.11/site-packages/langgraph_sdk/auth/exceptions.py` |

Key detail from the source: `MinimalUserDict` is a `TypedDict(total=False)` with only `identity: Required[str]`. The `permissions`, `display_name`, and `is_authenticated` fields are optional. Any additional fields you return (like `org_id`, `role`, `managed_org_ids`) are stored on the user object and accessible via `ctx.user["org_id"]` or `ctx.user.org_id` in `@auth.on` handlers.

---

## 2) Web App Deployment Configuration — `langgraph.json`

### Context

The web app's `useStream` hook connects directly from the browser to the LangGraph Platform API. This means the browser makes cross-origin requests to the LangGraph Platform endpoint. Without proper CORS configuration, browsers will block these requests. Additionally, the sandbox file browsing feature (Developer IDE Tier 2 view) relies on custom FastAPI routes served via `http.app`, and these routes need auth protection.

### Required `langgraph.json` Configuration

```json
{
  "dependencies": ["."],
  "graphs": {
    "pcg": "./graph.py:graph"
  },
  "env": ".env",
  "auth": {
    "path": "src/security/auth.py:auth"
  },
  "http": {
    "cors": {
      "allow_origins": [
        "http://localhost:3000",
        "https://meta-harness.vercel.app"
      ],
      "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      "allow_headers": ["Authorization", "Content-Type"],
      "allow_credentials": true
    },
    "app": "src/api/routes.py:app",
    "enable_custom_route_auth": true,
    "configurable_headers": {
      "includes": ["x-organization-id", "x-permission-level"],
      "excludes": ["authorization"]
    },
    "middleware_order": "auth_first"
  }
}
```

### Configuration Breakdown

| Key | Purpose | Why It Matters |
|---|---|---|
| `auth.path` | Registers the `@auth.authenticate` and `@auth.on` handlers from §1 | Without this, no JWT validation or thread isolation |
| `http.cors.allow_origins` | Allows the web app (Vercel domain + localhost dev) to make cross-origin requests to the LangGraph Platform API | Without this, `useStream` connections from the browser are blocked by CORS. The web app connects directly — not through a proxy. |
| `http.cors.allow_credentials` | Allows the `Authorization` header to be sent cross-origin | Required for JWT-based auth from the browser |
| `http.app` | Mounts custom FastAPI routes alongside the Agent Server API | Used for sandbox file browsing in the Developer IDE Tier 2 view |
| `http.enable_custom_route_auth` | Extends `@auth.authenticate` to the custom routes mounted via `http.app` | Without this, the sandbox file browser is unauthenticated — anyone with the URL can browse project files |
| `http.configurable_headers` | Passes `x-organization-id` and `x-permission-level` headers into `config["configurable"]` | Gives graph nodes direct access to org context via `config["configurable"].get("x-organization-id")`. Supplements `langgraph_auth_user`. Excludes `authorization` to avoid leaking the JWT into graph config. |
| `http.middleware_order` | `"auth_first"` — run JWT validation before any custom middleware | Ensures all requests are authenticated before hitting custom logic |

### CORS Origins Management

The `allow_origins` list must be updated when:
- The Vercel deployment URL changes (e.g., custom domain)
- Additional frontend environments are added (staging, preview deploys)
- Local development port changes (default: `http://localhost:3000`)

For production, consider using `allow_origin_regex` for Vercel preview deploys:
```json
{
  "http": {
    "cors": {
      "allow_origin_regex": "^https://meta-harness.*\\.vercel\\.app$"
    }
  }
}
```

### Reference

- [Application Structure Guide](https://docs.langchain.com/langsmith/application-structure) — file layout, `langgraph.json` format, graph registration
- [Configuration File Reference](https://docs.langchain.com/langsmith/cli#configuration-file) — all supported `langgraph.json` keys including `http`, `auth`, `store`, `checkpointer`
- [Configurable Headers](https://docs.langchain.com/langsmith/configurable-headers) — `http.configurable_headers` usage, accessing headers in graph nodes
- [Agent Server Architecture](https://docs.langchain.com/langsmith/agent-server) — runtime model, persistence, task queue, deployment modes
- [Core Capabilities](https://docs.langchain.com/langsmith/core-capabilities) — durable execution, interrupt/resume, background runs, cron, retry
- [Platform Setup Comparison](https://docs.langchain.com/langsmith/platform-setup) — Cloud vs Hybrid vs Self-hosted feature matrix
