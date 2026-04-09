# Implementation Plan: Formalized Stage Interface

## Overview

Introduce `BaseStage` as an abstract base class in `meta_agent/stages/base.py`, then migrate all five existing stage classes to inherit from it. The migration uses the Template Method pattern: `check_entry_conditions` / `check_exit_conditions` become concrete on `BaseStage` and delegate to abstract `_check_entry_impl` / `_check_exit_impl` hooks that each stage implements. Centralized path resolution, revision tracking, and LangSmith telemetry are added to `BaseStage` and removed from the individual stages.

## Tasks

- [x] 1. Create `meta_agent/stages/base.py` with `ConditionResult` and `BaseStage`
  - Define `ConditionResult` as a `TypedDict` with required keys `met: bool` and `unmet: list[str]`
  - Define `BaseStage(abc.ABC)` with:
    - Class-level `STAGE_NAME: str` (enforced by `__init_subclass__`)
    - Class-level `MAX_REVISION_CYCLES: int = 5`
    - `__init__(self, project_dir: str, project_id: str)` — raises `ValueError` if `project_dir` is empty; sets `self.revision_count = 0`
    - `__init_subclass__` — raises `TypeError` at class-definition time if a concrete subclass is missing `STAGE_NAME`
    - Concrete template methods `check_entry_conditions` / `check_exit_conditions` (pipeline: normalize state → `sync_from_state` → impl hook → `setdefault("unmet", [])` → `_emit_span` → return)
    - Abstract hooks `_check_entry_impl` / `_check_exit_impl`
    - `resolve_path(self, *parts: str) -> str` using `os.path.join(self.project_dir, *parts)`
    - `_pass(self) -> ConditionResult` and `_fail(self, reasons: list[str]) -> ConditionResult` (raises `ValueError` on empty list)
    - `increment_revision_count(self) -> bool` and `at_revision_limit(self) -> bool`
    - `sync_from_state(self, state: dict) -> None` — no-op on base
    - `_emit_span(self, span_name: str, result: ConditionResult) -> None` — `_span_carrier` no-op pattern; early-return when `LANGSMITH_TRACING` is not `true`/`1`; catches `ImportError` silently
  - _Requirements: 1.1–1.10, 2.1–2.4, 3.1–3.4, 3.7–3.8, 3.10–3.11, 4.1–4.7, 5.1, 5.4, 7.6, 8.1–8.4_

  - [x] 1.1 Write property test for `resolve_path` equivalence
    - **Property 1: `resolve_path` is equivalent to `os.path.join`**
    - Generate arbitrary non-empty `project_dir` strings and arbitrary tuples of path parts; assert `stage.resolve_path(*parts) == os.path.join(project_dir, *parts)`
    - Tag: `# Feature: formalized-stage-interface, Property 1: resolve_path is equivalent to os.path.join`
    - **Validates: Requirements 2.1, 2.2**

  - [x] 1.2 Write property test for revision-count invariant
    - **Property 2: `increment_revision_count` / `at_revision_limit` invariant**
    - Generate `MAX_REVISION_CYCLES` values in range 1–20; assert return-value sequence is `[True] * (N-1) + [False]` and `at_revision_limit()` is `True` after N calls
    - Tag: `# Feature: formalized-stage-interface, Property 2: increment_revision_count/at_revision_limit invariant`
    - **Validates: Requirements 3.3, 3.4, 3.7, 8.2**

  - [x] 1.3 Write property test for `sync_from_state` overwrite
    - **Property 3: `sync_from_state` overwrites in-memory revision count**
    - Generate arbitrary prior `revision_count` values and arbitrary state dicts with integer revision values; assert `sync_from_state` sets `self.revision_count` to exactly the state value
    - Tag: `# Feature: formalized-stage-interface, Property 3: sync_from_state overwrites in-memory revision count`
    - **Validates: Requirements 3.8, 3.10**

  - [x] 1.4 Write property test for `_fail` correctness
    - **Property 4: `_fail` with non-empty reasons returns correct `ConditionResult`**
    - Generate arbitrary non-empty lists of reason strings; assert `_fail(reasons)` returns `met=False` and `unmet == reasons`
    - Tag: `# Feature: formalized-stage-interface, Property 4: _fail with non-empty reasons returns correct ConditionResult`
    - **Validates: Requirements 1.8**

  - [x] 1.5 Write unit tests for `BaseStage` error cases and helpers
    - Test `_fail([])` raises `ValueError`
    - Test `project_dir=""` raises `ValueError`
    - Test concrete subclass missing `STAGE_NAME` raises `TypeError` at class definition
    - Test `_pass()` returns `{"met": True, "unmet": []}`
    - Test `_emit_span` with `LANGSMITH_TRACING=false` — no external calls, result returned correctly
    - _Requirements: 1.7–1.9, 2.4, 4.5, 4.7_

- [x] 2. Migrate `IntakeStage` to `BaseStage`
  - Add `from meta_agent.stages.base import BaseStage` import
  - Declare `STAGE_NAME = WorkflowStage.INTAKE.value` (`"INTAKE"`)
  - Inherit from `BaseStage`; call `super().__init__(project_dir, project_id)` in `__init__`
  - Replace all `os.path.join(self.project_dir, ...)` and f-string path constructions in `__init__` with `self.resolve_path(...)`
  - Rename `check_entry_conditions` → `_check_entry_impl`; rename `check_exit_conditions` → `_check_exit_impl`
  - Replace raw `{"met": ..., "unmet": ...}` dict literals with `self._pass()` or `self._fail(reasons)`; preserve extra keys (e.g. `"reason"`) by merging: `{**self._pass(), "reason": "..."}`
  - Remove any local `MAX_REVISION_CYCLES` if present
  - _Requirements: 6.1, 6.6, 2.3, 3.5, 5.2, 5.4, 1.10_

- [x] 3. Migrate `PrdReviewStage` to `BaseStage`
  - Add `from meta_agent.stages.base import BaseStage` import
  - Declare `STAGE_NAME = WorkflowStage.PRD_REVIEW.value` (`"PRD_REVIEW"`)
  - Inherit from `BaseStage`; call `super().__init__(project_dir, project_id)` in `__init__`
  - Replace path constructions in `__init__` with `self.resolve_path(...)`
  - Rename `check_entry_conditions` → `_check_entry_impl`; rename `check_exit_conditions` → `_check_exit_impl`
  - Replace raw dict literals with `self._pass()` / `self._fail(reasons)`; preserve extra keys (`prd_approved`, `eval_approved`) via merge
  - Remove local `MAX_REVISION_CYCLES` constant and `increment_revision_count` / `at_revision_limit` methods (now inherited from `BaseStage`)
  - _Requirements: 6.2, 6.6, 2.3, 3.5, 5.3, 5.4, 1.10_

- [x] 4. Migrate `ResearchStage` to `BaseStage`
  - Add `from meta_agent.stages.base import BaseStage` import
  - Declare `STAGE_NAME = WorkflowStage.RESEARCH.value` (`"RESEARCH"`)
  - Inherit from `BaseStage`; call `super().__init__(project_dir, project_id)` in `__init__`
  - Replace path constructions in `__init__` with `self.resolve_path(...)`
  - Rename `check_entry_conditions` → `_check_entry_impl`; rename `check_exit_conditions` → `_check_exit_impl`
  - Replace raw dict literals with `self._pass()` / `self._fail(reasons)`
  - _Requirements: 6.3, 6.6, 2.3, 5.4, 1.10_

- [x] 5. Migrate `SpecGenerationStage` to `BaseStage`
  - Add `from meta_agent.stages.base import BaseStage` import
  - Declare `STAGE_NAME = WorkflowStage.SPEC_GENERATION.value` (`"SPEC_GENERATION"`)
  - Inherit from `BaseStage`; call `super().__init__(project_dir, project_id)` in `__init__`
  - Replace path constructions in `__init__` with `self.resolve_path(...)`
  - Rename `check_entry_conditions` → `_check_entry_impl`; rename `check_exit_conditions` → `_check_exit_impl`
  - Replace raw dict literals with `self._pass()` / `self._fail(reasons)`
  - Remove local `MAX_FEEDBACK_CYCLES` constant and `increment_feedback_cycle` method; replace callers with `self.increment_revision_count()` (inherited)
  - Override `sync_from_state(self, state: dict) -> None` to set `self.revision_count = int(state.get("spec_generation_feedback_cycles", 0))`
  - In `_check_exit_impl`, call `self.sync_from_state(state)` as the first line before the limit check
  - _Requirements: 6.4, 6.6, 2.3, 3.6, 3.8–3.10, 5.4, 1.10_

- [x] 6. Migrate `SpecReviewStage` to `BaseStage`
  - Add `from meta_agent.stages.base import BaseStage` import
  - Declare `STAGE_NAME = WorkflowStage.SPEC_REVIEW.value` (`"SPEC_REVIEW"`)
  - Inherit from `BaseStage`; call `super().__init__(project_dir, project_id)` in `__init__`
  - Replace path constructions in `__init__` with `self.resolve_path(...)`
  - Rename `check_entry_conditions` → `_check_entry_impl`; rename `check_exit_conditions` → `_check_exit_impl`
  - Replace raw dict literals with `self._pass()` / `self._fail(reasons)`; preserve extra keys (`spec_approved`, `eval_approved`) via merge
  - _Requirements: 6.5, 6.6, 2.3, 5.4, 1.10_

- [x] 7. Checkpoint — ensure all existing tests still pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update `meta_agent/stages/__init__.py` and write integration tests
  - Add `from .base import BaseStage, ConditionResult` to `__init__.py`
  - Add `"BaseStage"` and `"ConditionResult"` to `__all__`
  - Remove stale TODO comments that are now resolved by this migration (revision tracking, path construction, signature inconsistency)
  - _Requirements: 6.7, 7.1–7.4_

  - [x] 8.1 Write property tests for all five migrated stages
    - **Property 5: All condition checks return a valid `ConditionResult`**
    - Generate arbitrary state dicts; call `check_entry_conditions(state)` and `check_exit_conditions(state)` on all five stages; assert `met` (bool) and `unmet` (list) keys are always present without `KeyError`
    - Tag: `# Feature: formalized-stage-interface, Property 5: All condition checks return a valid ConditionResult`
    - **Validates: Requirements 5.5, 7.2, 7.3**

  - [x] 8.2 Write property tests for tracing-disabled equivalence
    - **Property 6: Condition checks work correctly when tracing is disabled**
    - Same as Property 5 but with `LANGSMITH_TRACING=false`; assert results are identical and no errors raised
    - Tag: `# Feature: formalized-stage-interface, Property 6: Condition checks work correctly when tracing is disabled`
    - **Validates: Requirements 4.5**

  - [x] 8.3 Write integration tests for `BaseStage` importability and stage instantiation
    - Verify `BaseStage` and `ConditionResult` are importable from `meta_agent.stages`
    - Instantiate each of the five migrated stages with a real `project_dir` temp directory
    - Verify `check_entry_conditions` / `check_exit_conditions` return dicts with `met` (bool) and `unmet` (list) keys
    - _Requirements: 6.7, 7.1–7.4, 8.1_

- [x] 9. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All property tests use `hypothesis` with minimum 100 iterations and the tag format `# Feature: formalized-stage-interface, Property {N}: {property_text}`
- The `_span_carrier` no-op pattern is the canonical approach for post-hoc LangSmith metadata injection — do not use `@traceable` on `_check_entry_impl` / `_check_exit_impl` directly
- `sync_from_state` is a no-op on `BaseStage`; only `SpecGenerationStage` overrides it
- Stages that return extra keys (e.g. `prd_approved`) should merge them: `{**self._fail(unmet), "prd_approved": prd_approved}`
- The `_get_field` helper in `common.py` is unchanged — it remains used by stage logic for polymorphic state field access
