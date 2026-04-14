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

## Flow Validator Guidance: pytest

- **Isolation boundary:** run only Python/pytest commands from repo-local paths; do not edit application source files during validation.
- **Assigned scope:** validate only the assertion IDs assigned in your subagent prompt.
- **Execution mode:** use `meta_harness/.venv/bin/python -m pytest` with focused `-k` selectors and a unique cache dir per flow (`-o cache_dir=.pytest_cache_<flow-id>`).
- **Artifacts:** write only to your assigned flow report path and mission evidence directory.
- **Safety:** do not start extra services or use network-dependent test paths unless explicitly required by the assigned assertions.
