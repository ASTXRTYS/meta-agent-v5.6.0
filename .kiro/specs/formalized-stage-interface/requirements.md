# Requirements Document

## Introduction

The Formalized Stage Interface (FSI) introduces a `BaseStage` abstract base class that all workflow stage classes must inherit from. Currently, the five stage classes (`IntakeStage`, `PrdReviewStage`, `ResearchStage`, `SpecGenerationStage`, `SpecReviewStage`) are independent, duck-typed classes with no shared contract. This causes duplicated boilerplate (path construction, `_get_field` usage, revision cycle tracking), inconsistent method signatures, and no unified hook for telemetry.

FSI centralizes this boilerplate into `BaseStage`, enforces a shared interface via abstract methods, and provides a standardized LangSmith/LangChain telemetry hook so every stage entry, exit check, and condition evaluation is automatically traced as a named span. The result is a dramatically lower friction path for adding new stages and a unified performance auditing surface.

---

## Glossary

- **BaseStage**: The abstract base class defined in `meta_agent/stages/base.py` that all stage classes must subclass.
- **Stage**: A concrete subclass of `BaseStage` (e.g., `IntakeStage`, `PrdReviewStage`) that implements a single workflow phase.
- **Entry Condition**: A predicate evaluated before a stage begins, returning a structured result indicating whether the stage may be entered.
- **Exit Condition**: A predicate evaluated after stage work completes, returning a structured result indicating whether the stage may be exited.
- **Telemetry Hook**: A LangSmith `@traceable`-decorated wrapper that emits a named span for every entry/exit condition evaluation.
- **ConditionResult**: A typed `TypedDict` with keys `met: bool`, `unmet: list[str]`, and optional `metadata: dict[str, Any]` returned by all condition checks.
- **Provenance**: The audit trail of an artifact, verifying that a file not only exists but was explicitly produced and approved within the current thread context.
- **RevisionTracker**: A mixin or base-class mechanism that centralizes `revision_count`, `MAX_REVISION_CYCLES`, `increment_revision_count()`, and `at_revision_limit()`.
- **PathResolver**: A base-class utility method that constructs artifact paths using `os.path.join` consistently, replacing ad-hoc f-string concatenation.
- **WorkflowStage**: The existing `WorkflowStage` enum in `meta_agent/state.py` identifying each stage by name.
- **LangSmith**: The observability and evaluation platform used for tracing; tracing is enabled via `LANGSMITH_TRACING=true`.
- **`@traceable`**: The LangSmith decorator (wrapped in `meta_agent/tracing.py`) that emits a named span to LangSmith when tracing is active.

---

## Requirements

### Requirement 1: BaseStage Abstract Interface

**User Story:** As a developer adding a new workflow stage, I want a single base class to inherit from, so that I know exactly which methods I must implement and get common utilities for free.

#### Acceptance Criteria

1. THE `BaseStage` SHALL be defined as an abstract class in `meta_agent/stages/base.py`.
2. THE `BaseStage` SHALL declare `check_entry_conditions(self, state: dict[str, Any] | None = None) -> ConditionResult` as an abstract method.
3. THE `BaseStage` SHALL declare `check_exit_conditions(self, state: dict[str, Any]) -> ConditionResult` as an abstract method.
4. THE `BaseStage` SHALL require subclasses to accept `project_dir: str` and `project_id: str` as constructor parameters.
5. WHEN a developer attempts to instantiate a class that subclasses `BaseStage` without implementing all abstract methods, THE Python runtime SHALL raise `TypeError`.
6. THE `BaseStage` SHALL export `ConditionResult` as a `TypedDict` with required keys `met: bool` and `unmet: list[str]`.
7. THE `BaseStage` SHALL provide a protected `_pass(self) -> ConditionResult` method that returns `{"met": True, "unmet": []}`.
8. THE `BaseStage` SHALL provide a protected `_fail(self, reasons: list[str]) -> ConditionResult` method that returns `{"met": False, "unmet": reasons}`.
9. WHEN `_fail` is called with an empty list, THE `BaseStage` SHALL raise `ValueError` to prevent silent no-reason failures.
10. ALL five migrated stage classes SHALL use `self._pass()` or `self._fail(reasons)` as the sole return value of `check_entry_conditions` and `check_exit_conditions`, rather than constructing raw dicts inline.

---

### Requirement 2: Centralized Path Resolution

**User Story:** As a developer maintaining stage classes, I want path construction to be handled by a shared utility, so that I never have inconsistent path separators or duplicated `os.path.join` calls across stages.

#### Acceptance Criteria

1. THE `BaseStage` SHALL provide a `resolve_path(self, *parts: str) -> str` method that constructs paths using `os.path.join(self.project_dir, *parts)`.
2. WHEN `resolve_path` is called with one or more path parts, THE `BaseStage` SHALL return a path that is equivalent to calling `os.path.join(self.project_dir, *parts)` directly.
3. THE five existing stage classes (`IntakeStage`, `PrdReviewStage`, `ResearchStage`, `SpecGenerationStage`, `SpecReviewStage`) SHALL replace all direct `os.path.join(self.project_dir, ...)` and f-string path constructions in their `__init__` methods with calls to `self.resolve_path(...)`.
4. IF `project_dir` is an empty string, THEN THE `BaseStage` SHALL raise `ValueError` during construction.

---

### Requirement 3: Centralized Revision Cycle Tracking

**User Story:** As a developer reviewing stage logic, I want revision cycle tracking to live in one place, so that I don't have to synchronize duplicate `MAX_REVISION_CYCLES` constants and `increment_revision_count` methods across multiple files.

#### Acceptance Criteria

1. THE `BaseStage` SHALL define a class-level constant `MAX_REVISION_CYCLES: int = 5`.
2. THE `BaseStage` SHALL initialize `self.revision_count: int = 0` in its `__init__` method.
3. THE `BaseStage` SHALL provide `increment_revision_count(self) -> bool` that increments `self.revision_count` by 1 and returns `True` if `self.revision_count < self.MAX_REVISION_CYCLES`.
4. THE `BaseStage` SHALL provide `at_revision_limit(self) -> bool` that returns `True` when `self.revision_count >= self.MAX_REVISION_CYCLES`.
5. THE `PrdReviewStage` SHALL remove its local `MAX_REVISION_CYCLES` constant and `increment_revision_count` / `at_revision_limit` methods, delegating to the inherited `BaseStage` implementations.
6. THE `SpecGenerationStage` SHALL remove its local `MAX_FEEDBACK_CYCLES` constant and `increment_feedback_cycle` method, delegating to the inherited `BaseStage` implementations.
7. WHEN `increment_revision_count` is called exactly `MAX_REVISION_CYCLES` times, THE `BaseStage` SHALL return `False` on the final call and `at_revision_limit` SHALL return `True`.
8. THE `BaseStage` SHALL provide a `sync_from_state(self, state: dict[str, Any]) -> None` method that sets `self.revision_count` to the value retrieved from the appropriate field in the persistent `MetaAgentState`, not incremented.
9. THE `SpecGenerationStage` SHALL call `sync_from_state(state)` at the start of any condition check that depends on revision count, using `state.get("spec_generation_feedback_cycles", 0)` as the source field.
10. WHEN `sync_from_state` is called, `self.revision_count` SHALL be assigned the value from state directly, overwriting any in-memory value accumulated since the last graph resume.
11. THE `BaseStage` SHALL document that `sync_from_state` must be called at the start of any condition check that depends on revision count, to ensure the in-memory counter reflects persisted state across LangGraph graph resumes.

---

### Requirement 4: Standardized Telemetry via LangSmith Spans

**User Story:** As a platform engineer auditing system performance, I want every stage entry and exit condition check to emit a named LangSmith span automatically, so that I can measure stage gate latency and failure rates without instrumenting each stage individually.

#### Acceptance Criteria

1. THE `BaseStage` SHALL wrap `check_entry_conditions` in a `@traceable`-decorated method that emits a LangSmith span named `"{stage_name}.check_entry_conditions"` where `stage_name` is the `WorkflowStage` enum value associated with the stage.
2. THE `BaseStage` SHALL wrap `check_exit_conditions` in a `@traceable`-decorated method that emits a LangSmith span named `"{stage_name}.check_exit_conditions"`.
3. WHEN `LANGSMITH_TRACING=true` is set in the environment, THE telemetry wrapper SHALL inject the `ConditionResult` values into the LangSmith span metadata at runtime using `langsmith_extra={"metadata": {"stage": ..., "met": ..., "unmet": ...}}`, so that span metadata reflects the actual result of each condition check rather than static decorator-time values.
4. THE metadata keys `stage`, `met`, and `unmet` in the runtime-injected metadata SHALL be populated from the `ConditionResult` returned by the underlying condition method after it executes.
5. WHEN `LANGSMITH_TRACING` is not set or is `false`, THE telemetry wrapper SHALL invoke the underlying condition method and return its result without error.
6. THE `BaseStage` SHALL require subclasses to declare a class-level `STAGE_NAME: str` attribute whose value matches a `WorkflowStage` enum value, used to populate span names.
7. IF a subclass does not define `STAGE_NAME`, THEN THE `BaseStage` SHALL raise `TypeError` at class definition time.

---

### Requirement 5: Consistent `check_entry_conditions` Signature

**User Story:** As a developer calling stage condition checks, I want all stages to accept the same optional `state` parameter, so that I can call any stage's entry check uniformly without knowing which stages require state and which do not.

#### Acceptance Criteria

1. THE abstract `check_entry_conditions` method on `BaseStage` SHALL declare the signature `(self, state: dict[str, Any] | None = None) -> ConditionResult`.
2. THE `IntakeStage.check_entry_conditions` SHALL be updated to accept `state: dict[str, Any] | None = None` as a parameter, matching the base class signature.
3. THE `PrdReviewStage.check_entry_conditions` SHALL be updated to accept `state: dict[str, Any] | None = None` as a parameter, matching the base class signature.
4. WHEN `check_entry_conditions` is called with `state=None`, THE Stage SHALL treat it as an empty dict for any state lookups.
5. FOR ALL five existing stage classes, THE return value of `check_entry_conditions` SHALL conform to `ConditionResult` (i.e., contain `met: bool` and `unmet: list[str]`).

---

### Requirement 6: Migration of All Existing Stages to BaseStage

**User Story:** As a developer maintaining the codebase, I want all existing stage classes to inherit from `BaseStage`, so that the duck-typed pattern is fully eliminated and the shared contract is enforced everywhere.

#### Acceptance Criteria

1. THE `IntakeStage` SHALL inherit from `BaseStage` and declare `STAGE_NAME = WorkflowStage.INTAKE.value`.
2. THE `PrdReviewStage` SHALL inherit from `BaseStage` and declare `STAGE_NAME = WorkflowStage.PRD_REVIEW.value`.
3. THE `ResearchStage` SHALL inherit from `BaseStage` and declare `STAGE_NAME = WorkflowStage.RESEARCH.value`.
4. THE `SpecGenerationStage` SHALL inherit from `BaseStage` and declare `STAGE_NAME = WorkflowStage.SPEC_GENERATION.value`.
5. THE `SpecReviewStage` SHALL inherit from `BaseStage` and declare `STAGE_NAME = WorkflowStage.SPEC_REVIEW.value`.
6. WHEN any of the five migrated stage classes is instantiated, THE `BaseStage.__init__` SHALL be called with `project_dir` and `project_id`, initializing `self.revision_count = 0`.
7. THE `meta_agent/stages/__init__.py` SHALL export `BaseStage` in addition to the five existing stage classes.

---

### Requirement 7: Backward Compatibility

**User Story:** As a developer relying on existing stage instantiation patterns, I want the migration to `BaseStage` to be non-breaking, so that no call sites outside `meta_agent/stages/` need to change.

#### Acceptance Criteria

1. THE constructor signature of each migrated stage class SHALL remain `(self, project_dir: str, project_id: str)` with no additional required parameters.
2. THE return type of `check_entry_conditions` and `check_exit_conditions` on all migrated stages SHALL remain a `dict` (specifically a `ConditionResult` TypedDict, which is a subtype of `dict`).
3. WHEN existing code accesses `result["met"]` or `result["unmet"]` on the return value of any condition check, THE access SHALL succeed without `KeyError`.
4. THE `_get_field` helper in `meta_agent/stages/common.py` SHALL remain available and unchanged, as it is used by stage logic for polymorphic state field access.

---

### Requirement 8: Unit Testability of BaseStage

**User Story:** As a developer writing tests for new stages, I want `BaseStage` to be testable in isolation via a minimal concrete subclass, so that I can verify base-class behavior without depending on filesystem state.

#### Acceptance Criteria

1. THE `BaseStage` SHALL be instantiable via a minimal concrete subclass that implements only `check_entry_conditions` and `check_exit_conditions` and declares `STAGE_NAME`.
2. WHEN `increment_revision_count` is called on a `BaseStage` subclass instance, THE `revision_count` attribute SHALL reflect the incremented value.
3. WHEN `resolve_path` is called with `("artifacts", "intake", "prd.md")`, THE return value SHALL equal `os.path.join(project_dir, "artifacts", "intake", "prd.md")`.
4. THE telemetry wrapper SHALL be independently testable by setting `LANGSMITH_TRACING=false` in the test environment, ensuring no external calls are made.
