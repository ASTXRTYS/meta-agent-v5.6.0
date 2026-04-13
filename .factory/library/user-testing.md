# User Testing

## Validation Surface

**Primary surface:** Python API (pytest) — most assertions test types, schemas, routing logic, middleware behavior.

**Secondary surface:** Terminal TUI (tuistory) — pipeline awareness widgets, theme, layout.

**Tertiary surface:** langgraph dev server (curl) — graph loading, health checks.

## Validation Concurrency

**pytest surface:** Max 4 concurrent test processes (8 cores / 2). Tests are CPU-light (mocked LLM, no real API calls). Memory overhead ~200MB per process.

**tuistory surface:** Max 2 concurrent validators. Each tuistory instance + Textual app ~400MB. On 8GB machine with ~4GB free: 2 instances = 800MB, fits within 70% headroom.

**langgraph dev surface:** Max 1 instance. Server uses port 3100. Single instance only.

## Testing Tools

- **pytest** — primary. Mocked LLM responses, schema validation, routing logic.
- **tuistory** — TUI snapshot testing. Widget layout, theme rendering, pipeline awareness.
- **curl** — langgraph dev health checks.

## Test Infrastructure

- Tests in `meta_harness/tests/` with subdirs: `contract/`, `integration/`, `tui/`
- Mocked LLM via pytest fixtures (no real API keys needed for automated tests)
- `langgraph dev` smoke tests at milestone boundaries (manual verification)
