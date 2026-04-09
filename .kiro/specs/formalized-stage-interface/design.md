# Design Document: Formalized Stage Interface

## Overview

The Formalized Stage Interface (FSI) introduces `BaseStage` — an abstract base class in `meta_agent/stages/base.py` that all five existing workflow stage classes must inherit from. Today those classes are independent, duck-typed objects with no shared contract. FSI eliminates that by:

1. Enforcing a common abstract interface (`check_entry_conditions`, `check_exit_conditions`) via Python's `abc.ABC`.
2. Centralizing path construction, revision cycle tracking, and `ConditionResult` helpers into the base class.
3. Wrapping both condition-check methods in a LangSmith telemetry layer that emits a named span per call, with runtime metadata injected via `langsmith_extra={"metadata": {...}}` after the underlying method returns.
4. Requiring each subclass to declare a `STAGE_NAME` class attribute (validated at class-definition time via `__init_subclass__`) so span names are always correct.

The migration is purely additive from the perspective of call sites: constructor signatures, return types, and the `_get_field` helper in `common.py` are all preserved unchanged.

---

## Architecture

```
meta_agent/stages/
├── base.py              ← NEW: BaseStage, ConditionResult
├── common.py            ← unchanged (_get_field)
├── intake.py            ← migrated: inherits BaseStage
├── prd_review.py        ← migrated: inherits BaseStage
├── research.py          ← migrated: inherits BaseStage
├── spec_generation.py   ← migrated: inherits BaseStage
├── spec_review.py       ← migrated: inherits BaseStage
└── __init__.py          ← updated: exports BaseStage
```

### Call flow for a condition check

```
caller
  │
  ▼
stage.check_entry_conditions(state)          ← concrete method on BaseStage (Template Method)
  │  1. state = state or {}
  │  2. self.sync_from_state(state)
  │  3. result = self._check_entry_impl(state)   ← abstract; subclass implements
  │  4. result.setdefault("unmet", [])            ← normalize: ensure "unmet" key exists
  │  5. self._emit_span(f"{STAGE_NAME}.check_entry_conditions", result)
  │  6. return result
  ▼
ConditionResult
```

The Template Method pattern guarantees that `_emit_span` is always called by `BaseStage` — subclasses cannot accidentally omit it. Subclasses implement only `_check_entry_impl` / `_check_exit_impl` and never call `_emit_span` directly. The telemetry wrapper does **not** wrap the implementation function itself with `@traceable` at decoration time (which would bake in static metadata). Instead it calls the implementation first, then emits a zero-argument traced span carrying the live result as `langsmith_extra` metadata. This is the only pattern that satisfies Requirement 4.3 — runtime metadata injection using the `langsmith_extra={"metadata": {...}}` mechanism confirmed in the LangSmith SDK (`LangSmithExtra` TypedDict, `run_helpers.py`).

---

## Components and Interfaces

### `ConditionResult` (TypedDict)

```python
from typing import TypedDict

class ConditionResult(TypedDict):
    met: bool          # required
    unmet: list[str]   # required
    # stages may add extra keys (e.g. prd_approved, eval_approved) at runtime —
    # Python TypedDicts are structurally typed, so a dict with extra keys is still
    # a valid ConditionResult. No total=False needed.
```

`met` and `unmet` are both required. Additional keys (e.g. `prd_approved`) that existing stages return are still valid at runtime because Python's structural typing allows extra keys in a `TypedDict`-typed dict. The template method normalizes the result from `_check_entry_impl` / `_check_exit_impl` by defaulting `unmet` to `[]` if missing (step 4 in the pipeline), providing a fail-soft guarantee without requiring `total=False`.

### `BaseStage` (abstract class)

```python
import abc
import os
from typing import Any
from meta_agent.stages.base import ConditionResult

class BaseStage(abc.ABC):
    STAGE_NAME: str                    # must be declared by every subclass
    MAX_REVISION_CYCLES: int = 5

    def __init_subclass__(cls, **kwargs: Any) -> None: ...
    # raises TypeError if STAGE_NAME is missing on a concrete (non-abstract) subclass

    def __init__(self, project_dir: str, project_id: str) -> None: ...
    # raises ValueError if project_dir is empty string
    # sets self.revision_count = 0

    # ── Template Methods (concrete) ─────────────────────────────────────────
    def check_entry_conditions(self, state: dict[str, Any] | None = None) -> ConditionResult:
        # 1. state = state or {}
        # 2. self.sync_from_state(state)
        # 3. result = self._check_entry_impl(state)
        # 4. result.setdefault("unmet", [])
        # 5. self._emit_span(f"{self.STAGE_NAME}.check_entry_conditions", result)
        # 6. return result
        ...

    def check_exit_conditions(self, state: dict[str, Any]) -> ConditionResult:
        # same pipeline via _check_exit_impl
        ...

    # ── Abstract implementation hooks (subclasses implement these) ──────────
    @abc.abstractmethod
    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult: ...

    @abc.abstractmethod
    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult: ...

    # ── Path resolution ─────────────────────────────────────────────────────
    def resolve_path(self, *parts: str) -> str:
        return os.path.join(self.project_dir, *parts)

    # ── Condition result helpers ─────────────────────────────────────────────
    def _pass(self) -> ConditionResult:
        return {"met": True, "unmet": []}

    def _fail(self, reasons: list[str]) -> ConditionResult:
        # raises ValueError if reasons is empty
        return {"met": False, "unmet": reasons}

    # ── Revision tracking ────────────────────────────────────────────────────
    def increment_revision_count(self) -> bool:
        self.revision_count += 1
        return self.revision_count < self.MAX_REVISION_CYCLES

    def at_revision_limit(self) -> bool:
        return self.revision_count >= self.MAX_REVISION_CYCLES

    def sync_from_state(self, state: dict[str, Any]) -> None:
        # subclass overrides to pull the right state field
        # base implementation is a no-op; SpecGenerationStage overrides
        pass

    # ── Telemetry ────────────────────────────────────────────────────────────
    def _emit_span(self, span_name: str, result: ConditionResult) -> None:
        # emits a named LangSmith span with runtime metadata
        # no-op when langsmith is not installed or LANGSMITH_TRACING != true
        ...
```

### `__init_subclass__` enforcement

`STAGE_NAME` enforcement happens at **class definition time** via `__init_subclass__`. Abstract subclasses (those that still have unimplemented abstract methods) are exempt; only concrete classes are checked. This means intermediate abstract subclasses are allowed, but any class that can be instantiated must declare `STAGE_NAME`.

```python
def __init_subclass__(cls, **kwargs: Any) -> None:
    super().__init_subclass__(**kwargs)
    # Only enforce on concrete classes (no remaining abstract methods)
    if not getattr(cls, "__abstractmethods__", None):
        if not hasattr(cls, "STAGE_NAME") or not isinstance(cls.STAGE_NAME, str):
            raise TypeError(
                f"{cls.__name__} must define a class-level STAGE_NAME: str attribute"
            )
```

### Telemetry wrapper design

The LangSmith SDK's `traceable` decorator supports runtime metadata injection via the `langsmith_extra` keyword argument (confirmed in `LangSmithExtra` TypedDict in `.venv/lib/python3.11/site-packages/langsmith/run_helpers.py`). The `metadata` key in `langsmith_extra` is merged into the span's metadata at invocation time, not at decoration time.

The wrapper pattern:

```python
def _emit_span(self, span_name: str, result: ConditionResult) -> None:
    try:
        from langsmith import traceable as ls_traceable
        import os
        if os.environ.get("LANGSMITH_TRACING", "").lower() not in ("true", "1"):
            return
        # Define a no-op function to carry the span
        def _span_carrier() -> None:
            pass
        traced = ls_traceable(name=span_name)(_span_carrier)
        traced(
            langsmith_extra={
                "metadata": {
                    "stage": self.STAGE_NAME,
                    "met": result["met"],
                    "unmet": result["unmet"],
                }
            }
        )
    except ImportError:
        pass
```

The `BaseStage` template methods (`check_entry_conditions` / `check_exit_conditions`) call `self._emit_span(...)` after the implementation hook returns and the result is normalized. Subclasses never call `_emit_span` directly — the base class owns the full pipeline, guaranteeing telemetry is never silently lost.

The span-carrier pattern is the canonical approach for post-hoc metadata injection in LangSmith — it is preferred over context variable manipulation.

Span naming convention:
- `"{STAGE_NAME}.check_entry_conditions"` — e.g. `"INTAKE.check_entry_conditions"`
- `"{STAGE_NAME}.check_exit_conditions"` — e.g. `"SPEC_GENERATION.check_exit_conditions"`

---

## Data Models

### `ConditionResult`

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `met` | `bool` | yes | `True` iff all conditions satisfied |
| `unmet` | `list[str]` | yes | Human-readable failure reasons; empty when `met=True` |
| *(extra keys)* | `Any` | no | Stages may add keys (e.g. `prd_approved`) for caller convenience; valid at runtime due to Python's structural typing |

### `BaseStage` instance state

| Attribute | Type | Set by | Notes |
|-----------|------|--------|-------|
| `project_dir` | `str` | `__init__` | Validated non-empty |
| `project_id` | `str` | `__init__` | Passed through |
| `revision_count` | `int` | `__init__` / `sync_from_state` | Starts at 0; overwritten by `sync_from_state` |
| `STAGE_NAME` | `str` (class-level) | subclass declaration | Validated by `__init_subclass__` |
| `MAX_REVISION_CYCLES` | `int` (class-level) | `BaseStage` default = 5 | Subclasses may override |

### `sync_from_state` mapping per stage

Each stage that depends on revision count must override `sync_from_state` to pull from the correct `MetaAgentState` field:

| Stage | `MetaAgentState` field | Notes |
|-------|------------------------|-------|
| `SpecGenerationStage` | `spec_generation_feedback_cycles` | Only stage currently using revision tracking from persistent state |
| All others | *(no override needed)* | `revision_count` is purely in-memory for these stages |

`SpecGenerationStage.check_exit_conditions` calls `self.sync_from_state(state)` as its first line, ensuring `self.revision_count` reflects the persisted value before the limit check runs.

### Migration summary per stage

| Stage | `STAGE_NAME` | Path changes | Revision tracking changes | Signature changes |
|-------|-------------|--------------|--------------------------|-------------------|
| `IntakeStage` | `"INTAKE"` | `resolve_path(...)` replaces `os.path.join(self.project_dir, ...)` | none | `check_entry_conditions` → `_check_entry_impl`; `check_exit_conditions` → `_check_exit_impl`; gains `state=None` default via base template |
| `PrdReviewStage` | `"PRD_REVIEW"` | `resolve_path(...)` | removes local `MAX_REVISION_CYCLES`, `increment_revision_count`, `at_revision_limit` | `check_entry_conditions` → `_check_entry_impl`; `check_exit_conditions` → `_check_exit_impl`; gains `state=None` default via base template |
| `ResearchStage` | `"RESEARCH"` | `resolve_path(...)` | none | `check_entry_conditions` → `_check_entry_impl`; `check_exit_conditions` → `_check_exit_impl` |
| `SpecGenerationStage` | `"SPEC_GENERATION"` | `resolve_path(...)` | removes `MAX_FEEDBACK_CYCLES`, `increment_feedback_cycle`; adds `sync_from_state` override | `check_entry_conditions` → `_check_entry_impl`; `check_exit_conditions` → `_check_exit_impl` |
| `SpecReviewStage` | `"SPEC_REVIEW"` | `resolve_path(...)` | none | `check_entry_conditions` → `_check_entry_impl`; `check_exit_conditions` → `_check_exit_impl` |

All five stages replace raw `{"met": ..., "unmet": ...}` dict literals with `self._pass()` or `self._fail(reasons)`. Stages that return extra keys (e.g. `prd_approved`) continue to do so by merging: `{**self._fail(unmet), "prd_approved": prd_approved, ...}`.

### `meta_agent/stages/__init__.py` changes

```python
from .base import BaseStage, ConditionResult
from .intake import IntakeStage
from .prd_review import PrdReviewStage
from .research import ResearchStage
from .spec_generation import SpecGenerationStage
from .spec_review import SpecReviewStage

__all__ = [
    "BaseStage",
    "ConditionResult",
    "IntakeStage",
    "PrdReviewStage",
    "ResearchStage",
    "SpecGenerationStage",
    "SpecReviewStage",
]
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: `resolve_path` is equivalent to `os.path.join`

*For any* non-empty `project_dir` string and any sequence of path part strings, `stage.resolve_path(*parts)` SHALL return a value equal to `os.path.join(project_dir, *parts)`.

**Validates: Requirements 2.1, 2.2**

---

### Property 2: `increment_revision_count` / `at_revision_limit` invariant

*For any* `BaseStage` subclass instance with `MAX_REVISION_CYCLES = N` (where N ≥ 1), calling `increment_revision_count()` exactly `N` times SHALL produce a return-value sequence of `[True] * (N-1) + [False]`, and `at_revision_limit()` SHALL return `True` immediately after the `N`-th call.

**Validates: Requirements 3.3, 3.4, 3.7, 8.2**

---

### Property 3: `sync_from_state` overwrites in-memory revision count

*For any* `BaseStage` subclass instance that has had `increment_revision_count()` called an arbitrary number of times, calling `sync_from_state(state)` with a state dict containing a revision count value `v` SHALL set `self.revision_count` to exactly `v`, regardless of the prior in-memory value.

**Validates: Requirements 3.8, 3.10**

---

### Property 4: `_fail` with non-empty reasons returns correct `ConditionResult`

*For any* non-empty list of reason strings, `_fail(reasons)` SHALL return a dict with `met=False` and `unmet` equal to the provided list.

**Validates: Requirements 1.8**

---

### Property 5: All condition checks return a valid `ConditionResult`

*For any* of the five migrated stage classes and any state dict, calling `check_entry_conditions(state)` or `check_exit_conditions(state)` SHALL return a dict containing a `met` key of type `bool` and an `unmet` key of type `list`, accessible without `KeyError`.

**Validates: Requirements 5.5, 7.2, 7.3**

---

### Property 6: Condition checks work correctly when tracing is disabled

*For any* of the five migrated stage classes and any state dict, when `LANGSMITH_TRACING` is not set or is `false`, calling `check_entry_conditions(state)` or `check_exit_conditions(state)` SHALL return the same `ConditionResult` as when tracing is enabled, with no errors raised.

**Validates: Requirements 4.5**

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `_fail([])` called | `ValueError("_fail requires at least one reason")` |
| `project_dir=""` at construction | `ValueError("project_dir must not be empty")` |
| Concrete subclass missing `STAGE_NAME` | `TypeError` raised by `__init_subclass__` at class definition |
| `langsmith` not installed | `_emit_span` catches `ImportError` silently; condition check returns normally |
| `LANGSMITH_TRACING` not set or `false` | `_emit_span` returns early without making any LangSmith calls |
| `sync_from_state` called with missing key | Defaults to `0` via `state.get("spec_generation_feedback_cycles", 0)` |
| `_check_entry_impl` / `_check_exit_impl` returns dict missing `"unmet"` key | `BaseStage` template method normalizes to `[]` via `result.setdefault("unmet", [])` |

---

## Testing Strategy

### Unit tests

- Instantiate a minimal concrete `BaseStage` subclass (implements both abstract hooks `_check_entry_impl` and `_check_exit_impl`, declares `STAGE_NAME`) to test base-class behavior in isolation.
- Test `_pass()`, `_fail(reasons)`, `_fail([])`, `resolve_path`, `increment_revision_count`, `at_revision_limit`, `sync_from_state` directly.
- Test the template method pipeline: call the public `check_entry_conditions` / `check_exit_conditions` and verify `sync_from_state`, the impl hook, result normalization, and `_emit_span` are all exercised in order.
- Test `__init_subclass__` enforcement by defining a class without `STAGE_NAME` inside a test and asserting `TypeError`.
- Test `project_dir=""` raises `ValueError`.
- Test telemetry wrapper with `LANGSMITH_TRACING=false` — no external calls, result returned correctly.
- Test each migrated stage still passes its existing condition-check tests after migration (now calling the public template method, which delegates to `_check_entry_impl` / `_check_exit_impl`).

### Property-based tests

Use `hypothesis` (already available in the project's dev dependencies) with minimum 100 iterations per property.

Tag format: `# Feature: formalized-stage-interface, Property {N}: {property_text}`

- **Property 1** — generate arbitrary non-empty `project_dir` strings and arbitrary tuples of path parts; assert `resolve_path` equals `os.path.join`.
- **Property 2** — generate `MAX_REVISION_CYCLES` values in range 1–20; assert the return-value sequence from `increment_revision_count` is `[True] * (N-1) + [False]` and `at_revision_limit()` is `True` after.
- **Property 3** — generate arbitrary prior `revision_count` values and arbitrary state dicts with integer revision values; assert `sync_from_state` overwrites correctly.
- **Property 4** — generate arbitrary non-empty lists of reason strings; assert `_fail(reasons)` returns `met=False` and `unmet==reasons`.
- **Property 5** — generate arbitrary state dicts; call both public template methods (`check_entry_conditions` / `check_exit_conditions`) on all five stages; assert `met` (bool) and `unmet` (list) keys are always present.
- **Property 6** — same as Property 5 but with `LANGSMITH_TRACING=false`; assert results are identical and no errors raised.
- Edge cases (`_fail([])`, `project_dir=""`, missing `STAGE_NAME`) are example-based single-execution tests, not property tests.

### Integration tests

- Instantiate each of the five migrated stages with a real `project_dir` temp directory and verify `check_entry_conditions` / `check_exit_conditions` return `ConditionResult`-shaped dicts with `met` and `unmet` keys.
- Verify `BaseStage` is importable from `meta_agent.stages` after `__init__.py` update.
