# Deviation Record

## Context

- Date: 2026-03-23
- Project: `meta-agent-v5.6.0`
- Spec source of truth: `/Users/Jason/2026/V3/technical-specification-v5.6.0-final (3).md`
- Trigger: runtime failures observed in LangGraph Studio and `/runs/wait` path

## Deviation 1: Dynamic prompt middleware execution model

- File: `meta_agent/middleware/dynamic_system_prompt.py`
- Spec sections: `22.4`, `22.14`

### Spec baseline

Spec text describes `DynamicSystemPromptMiddleware` as primarily a `before_model` hook that recomposes and injects/replaces the system message in `messages` each call.

### Implemented behavior

- `before_model` now sanitizes state history by stripping existing system messages.
- `wrap_model_call` / `awrap_model_call` apply the stage-aware prompt at request level.
- Request override is version-compatible across runtime shapes:
  - `system_message` (newer LangChain)
  - `system_prompt` (older LangChain)
  - fallback to `messages` replacement if needed

### Why

This was required to fix two real runtime failures:

1. `TypeError: ModelRequest.__init__() got an unexpected keyword argument 'system_message'` (older runtime shape)
2. `ValueError: Received multiple non-consecutive system messages` (duplicate system prompt injection path)

### Evidence

- Failure reproduced through Studio and direct API `runs/wait`.
- After change, `runs/wait` returns successful agent responses.
- Targeted tests pass (`tests/unit/test_dynamic_prompt.py`).

### Reversibility

Reversible by moving all prompt injection back into `before_model` once runtime compatibility and provider semantics are strictly pinned and validated.

---

## Deviation 2: Runtime dependency fail-fast guard

- File: `meta_agent/server.py`
- Spec section: `22.6` (server factory)

### Spec baseline

Spec describes dynamic graph factory behavior but does not require runtime package validation.

### Implemented behavior

- Added `REQUIRED_RUNTIME_VERSIONS` and `_validate_runtime_dependencies()`.
- `get_agent()` now fails fast on incompatible/missing runtime versions.

### Why

Prevent silent runtime drift (global CLI/runtime mismatch) from causing opaque middleware/model failures at execution time.

### Reversibility

Can be removed, but not recommended. This guard enforces architecture assumptions explicitly.

---

## Deviation 3: Filesystem backend root path

- File: `meta_agent/graph.py`
- Related spec/docs area: graph backend configuration in Section `22.4` ecosystem docs

### Implemented behavior

- Backend root uses absolute repo root path resolved from module location.

### Why

Avoided runtime blocking issues tied to cwd resolution in dev runtime.

### Reversibility

Can revert to `root_dir="."` after validating runtime blocking behavior across local/dev server modes.

---

## Impact Assessment

- Functional intent is preserved: stage-aware dynamic prompt recomposition remains active and ordered first.
- Reliability improved: startup now detects incompatible runtimes early.
- Architectural risk reduced: fewer runtime-shape assumptions in hot execution path.

## Follow-up

- Keep this record synced with spec updates.
- If spec is revised to this implementation, mark these deviations as absorbed and close this record.
