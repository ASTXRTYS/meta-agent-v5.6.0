"""Abstract base class and contract for meta-agent workflow stages.

Spec References:
- Sections 3.11 (Workflow Stages)
- Kiro Spec: formalized-stage-interface/requirements.md
- Antigravity Roadmap: docs/architecture/stage_evolution_roadmap.md
"""

from __future__ import annotations

import abc
import os
from typing import Any, TypedDict

from meta_agent.tracing import traceable as ls_traceable


class ConditionResult(TypedDict):
    """Structured result of a stage entry or exit condition check.

    Both keys are required. Extra keys (e.g. prd_approved, eval_approved) are
    valid at runtime due to Python's structural typing — a dict with additional
    keys is still a valid ConditionResult. The BaseStage template method
    normalizes missing 'unmet' keys to [] as a fail-soft guarantee.
    """

    met: bool
    unmet: list[str]


class BaseStage(abc.ABC):
    """Abstract base class for all workflow stages.

    Provides centralized boilerplate for path resolution, revision tracking,
    state synchronization, and telemetry.
    """

    STAGE_NAME: str
    """The WorkflowStage enum value associated with this stage."""

    MAX_REVISION_CYCLES: int = 5
    """Maximum number of iterations allowed for this stage's core artifact."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Enforce compile-time requirements for concrete subclasses."""
        super().__init_subclass__(**kwargs)
        # Only enforce on concrete classes (no remaining abstract methods)
        if not getattr(cls, "__abstractmethods__", None):
            if not hasattr(cls, "STAGE_NAME") or not isinstance(cls.STAGE_NAME, str):
                raise TypeError(
                    f"{cls.__name__} must define a class-level STAGE_NAME: str attribute"
                )

    def __init__(self, project_dir: str, project_id: str) -> None:
        """Initialize the stage with project context.

        Args:
            project_dir: Root directory of the project.
            project_id: Unique identifier for the project.

        Raises:
            ValueError: If project_dir is empty.
        """
        if not project_dir:
            raise ValueError("project_dir must not be empty")
        self.project_dir = project_dir
        self.project_id = project_id
        self.revision_count = 0

    # ── Template Methods (Public API) ────────────────────────────────────────

    def check_entry_conditions(self, state: dict[str, Any] | None = None) -> ConditionResult:
        """Execute the entry gate pipeline (normalization -> sync -> trace)."""
        state = state or {}
        self.sync_from_state(state)
        result = self._check_entry_impl(state)

        # Normalize: ensure unmet key exists
        result.setdefault("unmet", [])

        self._emit_span(f"{self.STAGE_NAME}.check_entry_conditions", result)
        return result

    def check_exit_conditions(self, state: dict[str, Any]) -> ConditionResult:
        """Execute the exit gate pipeline (normalization -> sync -> trace)."""
        self.sync_from_state(state)
        result = self._check_exit_impl(state)

        # Normalize: ensure unmet key exists
        result.setdefault("unmet", [])

        self._emit_span(f"{self.STAGE_NAME}.check_exit_conditions", result)
        return result

    # ── Abstract Implementation Hooks ────────────────────────────────────────

    @abc.abstractmethod
    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Subclasses implement the actual entry condition logic here."""
        pass

    @abc.abstractmethod
    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        """Subclasses implement the actual exit condition logic here."""
        pass

    # ── Shared Stage Utilities ──────────────────────────────────────────────

    def resolve_path(self, *parts: str) -> str:
        """Centralized path resolution using os.path.join and project_dir."""
        return os.path.join(self.project_dir, *parts)

    def _pass(self) -> ConditionResult:
        """Helper to return a passing ConditionResult."""
        return {"met": True, "unmet": []}

    def _fail(self, reasons: list[str]) -> ConditionResult:
        """Helper to return a failing ConditionResult with reasons.

        Raises:
            ValueError: If reasons list is empty.
        """
        if not reasons:
            raise ValueError("_fail requires at least one reason")
        return {"met": False, "unmet": reasons}

    # ── Revision Tracking ───────────────────────────────────────────────────

    def increment_revision_count(self) -> bool:
        """Increment the revision count and check against MAX_REVISION_CYCLES."""
        self.revision_count += 1
        return self.revision_count < self.MAX_REVISION_CYCLES

    def at_revision_limit(self) -> bool:
        """Return True if the revision limit has been reached."""
        return self.revision_count >= self.MAX_REVISION_CYCLES

    def sync_from_state(self, state: dict[str, Any]) -> None:
        """Hydrate in-memory state from the persistent MetaAgentState.

        Base implementation is a no-op; subclasses like SpecGenerationStage
        must override this to sync their specific counters.
        """
        pass

    # ── Telemetry ────────────────────────────────────────────────────────────

    def _emit_span(self, span_name: str, result: ConditionResult) -> None:
        """Emit a named LangSmith span with runtime metadata results.

        Uses the _span_carrier pattern for post-hoc metadata injection.
        No-op when LANGSMITH_TRACING is not enabled.
        """
        if os.environ.get("LANGSMITH_TRACING", "").lower() not in ("true", "1"):
            return

        def _span_carrier() -> None:
            """No-op carrier for the trace span."""
            pass

        try:
            # We use the ls_traceable wrapper from meta_agent.tracing
            # which handles the fallback to no-op if langsmith is missing.
            traced = ls_traceable(
                name=span_name,
                metadata={
                    "stage": self.STAGE_NAME,
                    "met": result.get("met"),
                    "unmet": result.get("unmet"),
                },
            )(_span_carrier)
            traced()
        except Exception:
            # Telemetry is non-critical; ensure errors don't corrupt main logic
            pass
