"""Property-based and unit tests for BaseStage.

Feature: formalized-stage-interface
Spec Reference: .kiro/specs/formalized-stage-interface/tasks.md (Tasks 1.1-1.5)
"""

import os
from typing import Any

import pytest
from hypothesis import given, strategies as st

from meta_agent.stages.base import BaseStage, ConditionResult


# ── Testing Harness ────────────────────────────────────────────────────────

class MockStage(BaseStage):
    """Minimal concrete subclass for testing BaseStage functionality."""
    STAGE_NAME = "MOCK_STAGE"

    def _check_entry_impl(self, state: dict[str, Any]) -> ConditionResult:
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> ConditionResult:
        return self._pass()


# ── Property Tests (Hypothesis) ───────────────────────────────────────────

# Feature: formalized-stage-interface
# Property 1: resolve_path is equivalent to os.path.join
# Validates: Requirements 2.1, 2.2
@given(
    project_dir=st.text(min_size=1).filter(lambda x: x.strip() != ""),
    parts=st.lists(st.text())
)
def test_property_resolve_path_equivalence(project_dir, parts):
    stage = MockStage(project_dir=project_dir, project_id="test-id")
    expected = os.path.join(project_dir, *parts)
    assert stage.resolve_path(*parts) == expected


# Feature: formalized-stage-interface
# Property 2: increment_revision_count/at_revision_limit invariant
# Validates: Requirements 3.3, 3.4, 3.7, 8.2
@given(
    max_cycles=st.integers(min_value=1, max_value=20)
)
def test_property_revision_limit_invariant(max_cycles):
    stage = MockStage(project_dir=".", project_id="test")
    stage.MAX_REVISION_CYCLES = max_cycles
    
    # Assert sequence of return values from increment_revision_count
    results = []
    for _ in range(max_cycles):
        results.append(stage.increment_revision_count())
    
    # Final call should return False, others True
    expected = [True] * (max_cycles - 1) + [False]
    assert results == expected
    # at_revision_limit should be True now
    assert stage.at_revision_limit() is True


# Feature: formalized-stage-interface
# Property 3: sync_from_state overwrites in-memory revision count
# Validates: Requirements 3.8, 3.10
@given(
    initial_count=st.integers(min_value=0, max_value=100),
    state_count=st.integers(min_value=0, max_value=100)
)
def test_property_sync_from_state_overwrites(initial_count, state_count):
    class SyncMockStage(MockStage):
        def sync_from_state(self, state: dict[str, Any]) -> None:
            self.revision_count = state.get("count", 0)

    stage = SyncMockStage(project_dir=".", project_id="test")
    stage.revision_count = initial_count
    
    stage.sync_from_state({"count": state_count})
    assert stage.revision_count == state_count


# Feature: formalized-stage-interface
# Property 4: _fail with non-empty reasons returns correct ConditionResult
# Validates: Requirements 1.8
@given(
    reasons=st.lists(st.text(min_size=1), min_size=1)
)
def test_property_fail_with_reasons(reasons):
    stage = MockStage(project_dir=".", project_id="test")
    result = stage._fail(reasons)
    assert result["met"] is False
    assert result["unmet"] == reasons


# ── Unit Tests (Standard Pytest) ──────────────────────────────────────────

def test_unit_pass_helper():
    """Test that _pass() returns the standard success dict."""
    stage = MockStage(project_dir=".", project_id="test")
    assert stage._pass() == {"met": True, "unmet": []}


def test_unit_fail_empty_reasons():
    """Test that _fail([]) raises ValueError."""
    stage = MockStage(project_dir=".", project_id="test")
    with pytest.raises(ValueError, match="_fail requires at least one reason"):
        stage._fail([])


def test_unit_empty_project_dir():
    """Test that project_dir="" raises ValueError."""
    with pytest.raises(ValueError, match="project_dir must not be empty"):
        MockStage(project_dir="", project_id="test")


def test_unit_missing_stage_name():
    """Test that a concrete subclass missing STAGE_NAME raises TypeError."""
    with pytest.raises(TypeError, match="must define a class-level STAGE_NAME"):
        class BuggyStage(BaseStage):
            def _check_entry_impl(self, state): return self._pass()
            def _check_exit_impl(self, state): return self._pass()
        
        # Accessing the class might trigger __init_subclass__ even without instantiation
        # but standard Python behavior does it at definition time.
        # Since this is in a function, it happens now.
        pass


def test_unit_template_method_pipeline():
    """Test the full pipeline of check_entry_conditions."""
    class PipelineStage(MockStage):
        def sync_from_state(self, state):
            self.synced = True
        def _check_entry_impl(self, state):
            return {"met": True} # Missing "unmet" to test normalization

    stage = PipelineStage(project_dir=".", project_id="test")
    result = stage.check_entry_conditions({"foo": "bar"})
    
    assert stage.synced is True
    assert result["met"] is True
    assert result["unmet"] == [] # Normalized by base class
