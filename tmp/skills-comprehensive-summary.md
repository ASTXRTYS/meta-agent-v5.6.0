# Comprehensive Skills System Summary

## Files Inventory (32 files read in full)

| # | File | Lines | Status |
|---|------|-------|--------|
| 1 | `/skills/anthropic/spec/agent-skills-spec.md` | 3 | Stub — points to agentskills.io |
| 2 | `/skills/anthropic/template/SKILL.md` | 6 | Minimal template |
| 3 | `/skills/anthropic/README.md` | 93 | Repository overview |
| 4 | `/skills/anthropic/skills/claude-api/SKILL.md` | 246 | **Master skill file** — routing, models, thinking, architecture |
| 5 | `/skills/anthropic/skills/claude-api/LICENSE.txt` | ~100 | Apache 2.0 |
| 6 | `shared/tool-use-concepts.md` | 305 | Tool use concepts (server-side, user-defined, structured outputs) |
| 7 | `shared/error-codes.md` | 206 | HTTP error reference + typed SDK exceptions |
| 8 | `shared/live-sources.md` | 115 | WebFetch URLs for live docs |
| 9 | `shared/models.md` | 119 | Model catalog + programmatic discovery |
| 10 | `python/claude-api/README.md` | ~400 | Python basics, vision, caching, thinking, compaction |
| 11 | `python/claude-api/tool-use.md` | 590 | Tool runner, MCP helpers, manual loop, code exec, memory, structured outputs |
| 12 | `python/claude-api/streaming.md` | 162 | Python streaming patterns |
| 13 | `python/claude-api/batches.md` | 185 | Batch API Python |
| 14 | `python/claude-api/files-api.md` | 165 | Files API Python |
| 15 | `python/agent-sdk/README.md` | 345 | Agent SDK Python — query(), ClaudeSDKClient, permissions, hooks |
| 16 | `python/agent-sdk/patterns.md` | 359 | Agent SDK patterns — custom tools, subagents, MCP, sessions |
| 17 | `typescript/claude-api/README.md` | ~320 | TypeScript basics, vision, caching, thinking, compaction |
| 18 | `typescript/claude-api/tool-use.md` | 527 | TS tool runner (Zod), manual loop, code exec, memory, structured outputs |
| 19 | `typescript/claude-api/streaming.md` | 178 | TypeScript streaming patterns |
| 20 | `typescript/claude-api/batches.md` | 106 | Batch API TypeScript |
| 21 | `typescript/claude-api/files-api.md` | 98 | Files API TypeScript |
| 22 | `typescript/agent-sdk/README.md` | 295 | Agent SDK TypeScript — query(), permissions, hooks |
| 23 | `typescript/agent-sdk/patterns.md` | 205 | Agent SDK TS patterns — subagents, MCP, sessions, mutations |
| 24 | `go/claude-api.md` | 404 | Go SDK — all features in one file |
| 25 | `java/claude-api.md` | 430 | Java SDK — all features in one file |
| 26 | `ruby/claude-api.md` | ~90 | Ruby SDK — basics + tool runner |
| 27 | `csharp/claude-api.md` | 400 | C# SDK — all features in one file |
| 28 | `php/claude-api.md` | 241 | PHP SDK — basics + manual tool loop |
| 29 | `curl/examples.md` | 193 | Raw HTTP/cURL examples |

---

# 1. KEY FINDINGS

---

## 1.1 Agent Skills Specification

**Status:** The spec at `/skills/anthropic/spec/agent-skills-spec.md` is a 3-line stub pointing to `https://agentskills.io/specification`. No substantive content is stored locally.

**What skills ARE:** Folders of instructions, scripts, and resources that Claude loads dynamically. Each skill has a `SKILL.md` file with YAML frontmatter (`name`, `description`) and markdown instructions below.

**Template structure** (from `/skills/anthropic/template/SKILL.md`):
```yaml
---
name: template-skill
description: Replace with description of the skill and when Claude should use it.
---
# Insert instructions below
```

**Skill activation:** Skills are triggered when conditions in their `description` field match. The claude-api skill, for example, triggers when `code imports anthropic/@anthropic-ai/sdk/claude_agent_sdk, or user asks to use Claude API`.

**Deployment surfaces:** Skills work across Claude Code (as plugins), Claude.ai (paid plans), and Claude API.

---

## 1.2 Architecture & Surface Selection (from SKILL.md)

**Single endpoint:** Everything goes through `POST /v1/messages`. Tools and output constraints are features of this endpoint, not separate APIs.

**Three tool categories:**
1. **User-defined tools** — You define JSON schemas; SDK tool runner or manual loop handles execution
2. **Server-side tools** — Run on Anthropic infrastructure (code execution, web search/fetch, computer use)
3. **Client-side tools** — You control storage (memory tool)

**Decision tree for surface selection:**
| Need | Surface |
|------|---------|
| Single LLM call (classification, Q&A, extraction) | Claude API |
| Multi-step workflow with your own tools | Claude API + tool use |
| Custom agent with your own tools | Claude API + tool use |
| Agent with built-in file/web/terminal access | Agent SDK |
| Built-in permissions and guardrails | Agent SDK |

**Four agent criteria:** Complexity, Value, Viability, Cost-of-error — if "no" to any, use simpler tier.

---

## 1.3 Current Models (cached 2026-02-17)

| Model | ID | Context | Max Output | Input $/1M | Output $/1M |
|-------|----|---------|------------|-----------|-------------|
| Claude Opus 4.6 | `claude-opus-4-6` | 200K (1M beta) | 128K | $5.00 | $25.00 |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 200K (1M beta) | 64K | $3.00 | $15.00 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | 64K | $1.00 | $5.00 |

**Rules:**
- ALWAYS use `claude-opus-4-6` unless user explicitly names a different model
- NEVER append date suffixes — use exact alias strings
- Use `client.models.retrieve(id)` / `client.models.list()` for live capability queries

**Legacy models still active:** Opus 4.5, Opus 4.1, Sonnet 4.5, Sonnet 4, Opus 4

---

## 1.4 Extended Thinking & Effort

### Adaptive Thinking (Opus 4.6 + Sonnet 4.6)
- **Recommended:** `thinking: {type: "adaptive"}` — Claude dynamically decides when/how much to think
- **`budget_tokens` is DEPRECATED** on Opus 4.6 and Sonnet 4.6 — must not be used
- Adaptive thinking automatically enables interleaved thinking (no beta header needed)

### Effort Parameter (GA)
- `output_config: {effort: "low"|"medium"|"high"|"max"}` — controls thinking depth
- Default: `high`; `max` is Opus 4.6 only
- Works on: Opus 4.5, Opus 4.6, Sonnet 4.6
- Errors on: Sonnet 4.5, Haiku 4.5
- Lives inside `output_config`, NOT top-level

### Older Models
- If user explicitly requests Sonnet 4.5 etc.: `thinking: {type: "enabled", budget_tokens: N}`
- `budget_tokens` must be < `max_tokens` (minimum 1024)

### Prefill Removed
- **Opus 4.6:** Assistant message prefills return 400 error. Use structured outputs or system prompt instead.

---

## 1.5 Tool Use Patterns

### Tool Runner (Recommended — Beta)
| Language | Decorator/API | Notes |
|----------|--------------|-------|
| Python | `@beta_tool` → `client.beta.messages.tool_runner()` | Type-safe, auto-schema from signatures |
| TypeScript | `betaZodTool` + Zod → `client.beta.messages.toolRunner()` | Type-safe via Zod schemas |
| Java | `@JsonClassDescription` + `Supplier<String>` → `BetaToolRunner` | Annotated classes |
| Go | `toolrunner.NewBetaToolFromJSONSchema` → `BetaToolRunner` | Struct tags for schema |
| Ruby | `BaseTool` subclass → `client.beta.messages.tool_runner()` | Model classes |

### Manual Agentic Loop
- Loop until `stop_reason == "end_turn"`
- Handle `stop_reason == "pause_turn"` (server-side tool iteration limit — re-send to continue, do NOT add "Continue." message)
- Always append full `response.content` (preserves tool_use blocks)
- Each `tool_result` must include matching `tool_use_id`
- Set `max_continuations` limit to prevent infinite loops

### Tool Choice Options
- `auto` (default), `any`, `tool` (forced specific), `none`
- Can include `disable_parallel_tool_use: true`

### MCP Tool Conversion (Python)
- `anthropic.lib.tools.mcp` provides: `async_mcp_tool`, `mcp_tool`, `mcp_message`, `mcp_resource_to_content`, `mcp_resource_to_file`
- Converts MCP tools/prompts/resources for use with the tool runner

---

## 1.6 Server-Side Tools (Native Tools)

### Code Execution
- **Type:** `code_execution_20260120`
- Sandboxed container: 1 CPU, 5 GiB RAM, 5 GiB disk, no internet
- Python 3.11 with data science libraries pre-installed
- Containers persist 30 days, reusable via `container_id`
- Claude gets `bash_code_execution` and `text_editor_code_execution`
- Cost: Free with web tools; otherwise $0.05/hr after 1,550 free hours/month

### Web Search & Web Fetch
- **Types:** `web_search_20260209`, `web_fetch_20260209`
- **Dynamic filtering** (Opus 4.6/Sonnet 4.6): Claude writes code to filter results before context window — activates automatically
- Previous version: `web_search_20250305` (without dynamic filtering)
- Do NOT combine standalone `code_execution` tool with `_20260209` web tools (creates confusing second environment)

### Programmatic Tool Calling
- Claude executes complex multi-tool workflows in code, keeping intermediates out of context
- Docs: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling`

### Tool Search
- Dynamic tool discovery from large libraries without loading all definitions
- Docs: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool`

### Computer Use
- Desktop interaction (screenshots, mouse, keyboard) — server-hosted or self-hosted
- Docs: `https://platform.claude.com/docs/en/agents-and-tools/computer-use/overview`

### Memory Tool
- **Type:** `memory_20250818`
- Client-side: you control storage
- Commands: view, create, str_replace, insert, delete, rename
- SDK helpers: Python `BetaAbstractMemoryTool`, TypeScript `betaMemoryTool`, Java `BetaMemoryToolHandler`

---

## 1.7 Structured Outputs

**Two features:**
1. **JSON outputs** (`output_config.format`): Controls response format via JSON schema
2. **Strict tool use** (`strict: true`): Guarantees valid tool parameter schemas

**Recommended:** `client.messages.parse()` — auto-validates against schema
- Python: Pydantic models → `output_format=MyModel`
- TypeScript: Zod schemas → `zodOutputFormat(schema)`
- Java: POJOs → `StructuredMessageCreateParams<T>`

**Key constraints:**
- Use `output_config: {format: {...}}` NOT deprecated `output_format` on `messages.create()`
- `additionalProperties: false` required for all objects
- No recursive schemas, no numerical constraints, no string length constraints
- Incompatible with: citations, message prefilling
- First request has schema compilation latency (24hr cache thereafter)

---

## 1.8 Streaming

**Default to streaming** for long input/output or high `max_tokens` — prevents HTTP timeouts.

**Patterns:**
- Python: `client.messages.stream()` → `stream.text_stream` → `stream.get_final_message()`
- TypeScript: `client.messages.stream()` → `for await (event of stream)` → `stream.finalMessage()`
- Go: `client.Messages.NewStreaming()` → `message.Accumulate(stream.Current())`

**128K output:** Opus 4.6 supports 128K `max_tokens` but requires streaming.

**`max_tokens` defaults:**
- Non-streaming: ~16000 (keeps under SDK HTTP timeouts)
- Streaming: ~64000 (timeouts aren't a concern)

---

## 1.9 Batches API

- `POST /v1/messages/batches` — 50% cost reduction
- Up to 100K requests or 256 MB per batch
- Most complete in 1 hour; max 24 hours
- Results available 29 days
- All Messages API features supported

---

## 1.10 Files API (Beta)

- Beta header: `files-api-2025-04-14`
- Max file: 500 MB; total storage: 100 GB/org
- Files persist until deleted
- Operations (upload/list/delete) free; content in messages billed as input tokens
- Not on Bedrock or Vertex AI
- Download only for code-execution-created files

---

## 1.11 Compaction (Beta)

- Beta header: `compact-2026-01-12`
- Opus 4.6 and Sonnet 4.6 only
- Server-side summarization when context approaches 150K tokens
- **CRITICAL:** Append `response.content` (not just text) — compaction blocks must be preserved
- Context management config: `context_management: {edits: [{type: "compact_20260112"}]}`

---

## 1.12 Prompt Caching

- **Automatic:** Top-level `cache_control: {type: "ephemeral"}` — auto-caches last cacheable block
- **Manual:** `cache_control` on specific content blocks
- TTL: Default 5 min; explicit `ttl: "1h"` supported
- Savings: up to 90%

---

## 1.13 Agent SDK (Python & TypeScript Only)

**Package:** `claude-agent-sdk` (Python) / `@anthropic-ai/claude-agent-sdk` (TypeScript)

**Two interfaces:**
1. `query()` — Simple one-shot usage, returns async iterator of messages
2. `ClaudeSDKClient` — Full lifecycle control, required for custom MCP tools

**Built-in tools:** Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, AskUserQuestion, Agent (subagents)

**Permission modes:** default, plan, acceptEdits, bypassPermissions (Python) / dontAsk (TypeScript)

**Key features:**
- MCP server integration (stdio/http servers or in-process via `create_sdk_mcp_server`)
- Hooks: PreToolUse, PostToolUse, PostToolUseFailure, Stop, SubagentStop, Notification, etc.
- Subagents via `AgentDefinition` + `Agent` tool
- Session resumption via `session_id`
- Session history (list, get messages, rename, tag, fork)
- Rate limit events
- Max budget (USD) and max turns controls
- Custom system prompts
- Task progress messages for subagent monitoring

---

## 1.14 Language-Specific SDK Coverage

| Feature | Python | TypeScript | Java | Go | Ruby | C# | PHP | cURL |
|---------|--------|-----------|------|-----|------|----|-----|------|
| Basic Messages | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tool Runner | ✅ (beta) | ✅ (beta) | ✅ (beta) | ✅ (beta) | ✅ (beta) | ❌ | ❌ | N/A |
| Agent SDK | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A |
| Adaptive Thinking | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Structured Outputs | ✅ | ✅ | ✅ | — | — | ✅ | — | — |
| Files API | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Compaction | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| Server-Side Tools | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — |
| MCP (API-level) | ✅ | ✅ | ✅ | — | — | — | ✅ | — |
| Memory Tool | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Bedrock/Vertex | — | — | — | — | — | — | ✅ | — |

---

## 1.15 Error Handling

| Code | Type | Retryable | SDK Exceptions |
|------|------|-----------|----------------|
| 400 | invalid_request_error | No | BadRequestError |
| 401 | authentication_error | No | AuthenticationError |
| 403 | permission_error | No | PermissionDeniedError |
| 404 | not_found_error | No | NotFoundError |
| 413 | request_too_large | No | — |
| 429 | rate_limit_error | Yes | RateLimitError |
| 500 | api_error | Yes | InternalServerError |
| 529 | overloaded_error | Yes | — |

**SDKs auto-retry** 429 and 5xx with exponential backoff (default `max_retries=2`).

---

## 1.16 Common Pitfalls (Critical Rules)

1. **Don't truncate inputs** — notify user if too long
2. **Opus 4.6 thinking:** Adaptive only — NO budget_tokens
3. **Opus 4.6 prefill:** Removed — returns 400
4. **Don't lowball max_tokens** — truncates mid-thought
5. **128K output requires streaming**
6. **Tool call JSON:** Always `json.loads()`/`JSON.parse()` — never raw string match
7. **Use `output_config.format`** not deprecated `output_format` on `create()`
8. **Don't reimplement SDK functionality** (use `finalMessage()`, typed exceptions, SDK types)
9. **Don't define custom types** for SDK data structures — use exports
10. **Sanitize filenames** with `os.path.basename()` for code execution outputs
11. **Compaction:** Append `response.content`, not just text
12. **`pause_turn` handling:** Don't add "Continue." — just re-send messages

---

# 2. GAPS — Questions That Remain Unanswered

| # | Gap | Where to find answers |
|---|-----|----------------------|
| 1 | **Agent Skills Specification** — Full spec is external at agentskills.io; no local content | WebFetch `https://agentskills.io/specification` |
| 2 | **Model capabilities beyond cache date** — Models table cached 2026-02-17; newer models may exist | `client.models.list()` or WebFetch models overview |
| 3 | **Programmatic Tool Calling details** — Only a WebFetch URL provided, no cached implementation examples | WebFetch the URL |
| 4 | **Tool Search implementation** — Only a WebFetch URL provided | WebFetch the URL |
| 5 | **Computer Use implementation** — Only a WebFetch URL; no code examples in skill files | WebFetch the URL |
| 6 | **Rate limit tiers** — Not documented in cached content | WebFetch `https://platform.claude.com/docs/en/api/rate-limits.md` |
| 7 | **1M context window beta** — Beta header `context-1m-2025-08-07` mentioned but no usage examples | WebFetch adaptive thinking docs |
| 8 | **Citations** — Mentioned as incompatible with structured outputs; no implementation detail | WebFetch citations URL |
| 9 | **Exact prompt caching pricing** — "Up to 90% savings" but no breakdowns | WebFetch pricing URL |
| 10 | **Ruby/PHP/C# advanced features** — Minimal coverage (no structured outputs, compaction, or files examples for Ruby/PHP) | SDK repo READMEs |
| 11 | **Agent SDK authentication/API keys** — How the Agent SDK authenticates (inherits from Claude Code CLI) | Agent SDK docs |
| 12 | **MCP server security model** — Permissions for MCP server tool calls not detailed | Agent SDK + MCP docs |
| 13 | **Foundry deployment** — Only PHP has Foundry client example; unclear for other SDKs | WebFetch platform docs |

---

# 3. ACTIONABLE BASELINE — What the Agent Now Knows for Certain

## 3.1 Hard Facts

1. **Default model:** Always `claude-opus-4-6` unless user says otherwise
2. **Default thinking:** Always `thinking: {type: "adaptive"}` for anything remotely complicated
3. **Default streaming:** For any request with long input/output or high `max_tokens`
4. **Use `.get_final_message()` / `.finalMessage()`** for streaming without event handling
5. **API endpoint:** Everything is `POST /v1/messages` — no separate APIs for tools/outputs
6. **API version header:** `anthropic-version: 2023-06-01`
7. **Effort parameter location:** `output_config: {effort: ...}` — NOT top-level
8. **`budget_tokens` is dead on 4.6 models** — will error or be ignored
9. **Assistant prefill is dead on Opus 4.6** — 400 error

## 3.2 SDK Installation

| Language | Package |
|----------|---------|
| Python | `pip install anthropic` |
| TypeScript | `npm install @anthropic-ai/sdk` |
| Java | `com.anthropic:anthropic-java:2.16.1` |
| Go | `go get github.com/anthropics/anthropic-sdk-go` |
| Ruby | `gem install anthropic` |
| C# | `dotnet add package Anthropic` |
| PHP | `composer require "anthropic-ai/sdk"` |
| Agent SDK (Py) | `pip install claude-agent-sdk` |
| Agent SDK (TS) | `npm install @anthropic-ai/claude-agent-sdk` |

## 3.3 Response Handling Rules

- `response.content` is a **list of content blocks** (TextBlock, ThinkingBlock, ToolUseBlock, etc.)
- **Always check `.type` before accessing `.text`** — first block may be ThinkingBlock
- **Tool results go in a `user` message** with `tool_result` blocks matching `tool_use_id`
- **Multiple tool calls in one response** — handle all, send all results in one user message
- **Stop reasons:** `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`

## 3.4 File Reference Map

**For any user task, read these files in order:**

| Task | Required Reading |
|------|-----------------|
| Basic API usage | `{lang}/claude-api/README.md` |
| Tool use / agents | + `shared/tool-use-concepts.md` + `{lang}/claude-api/tool-use.md` |
| Streaming / chat UI | + `{lang}/claude-api/streaming.md` |
| Batch processing | + `{lang}/claude-api/batches.md` |
| File uploads | + `{lang}/claude-api/files-api.md` |
| Agent SDK | `{lang}/agent-sdk/README.md` + `{lang}/agent-sdk/patterns.md` |
| Error debugging | `shared/error-codes.md` |
| Model lookup | `shared/models.md` |
| Latest docs | `shared/live-sources.md` → WebFetch |

## 3.5 Security Rules

1. Never store API keys, passwords, tokens in memory files
2. Sanitize filenames with `os.path.basename()` before writing code execution outputs
3. Validate tool inputs for side-effecting operations
4. Use manual agentic loop for human-in-the-loop approval on destructive tools
5. Be cautious with PII in memory tool (GDPR/CCPA considerations)
6. MCP conversion raises `UnsupportedMCPValueError` for unsupported content types

---

*Summary generated from 32 files across 9 language directories + 4 shared reference files.*
*Total skill content: approximately 6,000+ lines of documentation and code examples.*
