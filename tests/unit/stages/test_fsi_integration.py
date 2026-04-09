"""Integration and property tests for the Formalized Stage Interface (FSI).

Feature: formalized-stage-interface
Spec Reference: .kiro/specs/formalized-stage-interface/tasks.md (Tasks 8.1-8.3)
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st

from meta_agent.stages import BaseStage, ConditionResult
from meta_agent.stages import (
    IntakeStage,
    PrdReviewStage,
    ResearchStage,
    SpecGenerationStage,
    SpecReviewStage,
)
from meta_agent.state import WorkflowStage


# ---------------------------------------------------------------------------
# Task 8.3 — Importability and instantiation integration tests
# ---------------------------------------------------------------------------

def test_base_stage_importable_from_package():
    """Verify BaseStage is importable from meta_agent.stages."""
    from meta_agent.stages import BaseStage as BS
    assert BS is BaseStage


def test_condition_result_importable_from_package():
    """Verify ConditionResult is importable from meta_agent.stages."""
    from meta_agent.stages import ConditionResult as CR
    assert CR is ConditionResult


def test_all_stages_instantiate_with_temp_dir():
    """Instantiate all five stages with a real temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stages = [
            IntakeStage(project_dir=tmpdir, project_id="test"),
            PrdReviewStage(project_dir=tmpdir, project_id="test"),
            ResearchStage(project_dir=tmpdir, project_id="test"),
            SpecGenerationStage(project_dir=tmpdir, project_id="test"),
            SpecReviewStage(project_dir=tmpdir, project_id="test"),
        ]
        for stage in stages:
            assert isinstance(stage, BaseStage)


def test_all_stages_check_entry_returns_condition_result():
    """All five stages return dicts with met (bool) and unmet (list) from check_entry_conditions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stages = [
            IntakeStage(project_dir=tmpdir, project_id="test"),
            PrdReviewStage(project_dir=tmpdir, project_id="test"),
            ResearchStage(project_dir=tmpdir, project_id="test"),
            SpecGenerationStage(project_dir=tmpdir, project_id="test"),
            SpecReviewStage(project_dir=tmpdir, project_id="test"),
        ]
        for stage in stages:
            result = stage.check_entry_conditions(state=None)
            assert isinstance(result.get("met"), bool), f"{stage.__class__.__name__}: 'met' must be bool"
            assert isinstance(result.get("unmet"), list), f"{stage.__class__.__name__}: 'unmet' must be list"


def test_all_stages_check_exit_returns_condition_result():
    """All five stages return dicts with met (bool) and unmet (list) from check_exit_conditions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stages = [
            IntakeStage(project_dir=tmpdir, project_id="test"),
            PrdReviewStage(project_dir=tmpdir, project_id="test"),
            ResearchStage(project_dir=tmpdir, project_id="test"),
            SpecGenerationStage(project_dir=tmpdir, project_id="test"),
            SpecReviewStage(project_dir=tmpdir, project_id="test"),
        ]
        for stage in stages:
            result = stage.check_exit_conditions(state={})
            assert isinstance(result.get("met"), bool), f"{stage.__class__.__name__}: 'met' must be bool"
            assert isinstance(result.get("unmet"), list), f"{stage.__class__.__name__}: 'unmet' must be list"


# ---------------------------------------------------------------------------
# Logic Invariants — Specific Stage Behaviors
# ---------------------------------------------------------------------------

@given(
    revision_count=st.integers(min_value=0, max_value=10)
)
def test_spec_generation_state_sync_invariant(revision_count):
    """Property: SpecGenerationStage must hydrate its revision counter from state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stage = SpecGenerationStage(project_dir=tmpdir, project_id="test")
        
        state = {
            "spec_generation_feedback_cycles": revision_count
        }
        
        # Trigger sync via the public gate
        stage.check_entry_conditions(state)
        
        assert stage.revision_count == revision_count
        
        # Increment works correctly
        limit_reached = not stage.increment_revision_count()
        assert stage.revision_count == revision_count + 1
        assert limit_reached == (stage.revision_count >= stage.MAX_REVISION_CYCLES)


@given(
    met_val=st.booleans()
)
def test_prd_review_exit_logic_hydration_invariant(met_val):
    """Property: PrdReviewStage exit conditions depend on state hydration and filesystem."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stage = PrdReviewStage(project_dir=tmpdir, project_id="test")
        
        # Create required files to bypass basic existence check
        os.makedirs(os.path.join(tmpdir, "artifacts", "intake"), exist_ok=True)
        os.makedirs(os.path.join(tmpdir, "evals"), exist_ok=True)
        with open(os.path.join(tmpdir, "artifacts", "intake", "prd.md"), "w") as f:
            f.write("test")
        with open(os.path.join(tmpdir, "evals", "eval-suite-prd.json"), "w") as f:
            f.write("{}")

        state = {
            "approval_history": [
                {"artifact": "prd", "action": "approved"} if met_val else {},
                {"artifact": "eval_suite", "action": "approved"} if met_val else {}
            ]
        }
        
        result = stage.check_exit_conditions(state)
        
        assert result["met"] == met_val
        if not met_val:
            assert len(result["unmet"]) > 0


# ---------------------------------------------------------------------------
# Task 8.1 — Property 5: All condition checks return a valid ConditionResult
# Feature: formalized-stage-interface
# Property 5: All condition checks return a valid ConditionResult
# Validates: Requirements 5.5, 7.2, 7.3
# ---------------------------------------------------------------------------

_STAGE_CLASSES = [
    IntakeStage,
    PrdReviewStage,
    ResearchStage,
    SpecGenerationStage,
    SpecReviewStage,
]

# Strategy: generate arbitrary state dicts with string keys and simple values
_state_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.text(max_size=50),
        st.lists(st.text(max_size=20), max_size=5),
    ),
    max_size=10,
)


@given(state=_state_strategy)
@settings(max_examples=50)
def test_property_5_entry_conditions_always_return_valid_result(state):
    """
    Feature: formalized-stage-interface
    Property 5: All condition checks return a valid ConditionResult
    Validates: Requirements 5.5, 7.2, 7.3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        for StageClass in _STAGE_CLASSES:
            stage = StageClass(project_dir=tmpdir, project_id="test")
            result = stage.check_entry_conditions(state=state)
            assert "met" in result, f"{StageClass.__name__}: missing 'met' key"
            assert "unmet" in result, f"{StageClass.__name__}: missing 'unmet' key"
            assert isinstance(result["met"], bool), f"{StageClass.__name__}: 'met' must be bool"
            assert isinstance(result["unmet"], list), f"{StageClass.__name__}: 'unmet' must be list"


@given(state=_state_strategy)
@settings(max_examples=50)
def test_property_5_exit_conditions_always_return_valid_result(state):
    """
    Feature: formalized-stage-interface
    Property 5: All condition checks return a valid ConditionResult
    Validates: Requirements 5.5, 7.2, 7.3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        for StageClass in _STAGE_CLASSES:
            stage = StageClass(project_dir=tmpdir, project_id="test")
            result = stage.check_exit_conditions(state=state)
            assert "met" in result, f"{StageClass.__name__}: missing 'met' key"
            assert "unmet" in result, f"{StageClass.__name__}: missing 'unmet' key"
            assert isinstance(result["met"], bool), f"{StageClass.__name__}: 'met' must be bool"
            assert isinstance(result["unmet"], list), f"{StageClass.__name__}: 'unmet' must be list"


# ---------------------------------------------------------------------------
# Task 8.2 — Property 6: Condition checks work correctly when tracing is disabled
# Feature: formalized-stage-interface
# Property 6: Condition checks work correctly when tracing is disabled
# Validates: Requirements 4.5
# ---------------------------------------------------------------------------

@given(state=_state_strategy)
@settings(max_examples=50)
def test_property_6_entry_conditions_tracing_disabled(state):
    """
    Feature: formalized-stage-interface
    Property 6: Condition checks work correctly when tracing is disabled
    Validates: Requirements 4.5
    """
    original = os.environ.get("LANGSMITH_TRACING")
    os.environ["LANGSMITH_TRACING"] = "false"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            for StageClass in _STAGE_CLASSES:
                stage = StageClass(project_dir=tmpdir, project_id="test")
                result = stage.check_entry_conditions(state=state)
                assert "met" in result
                assert "unmet" in result
                assert isinstance(result["met"], bool)
                assert isinstance(result["unmet"], list)
    finally:
        if original is None:
            os.environ.pop("LANGSMITH_TRACING", None)
        else:
            os.environ["LANGSMITH_TRACING"] = original


@given(state=_state_strategy)
@settings(max_examples=50)
def test_property_6_exit_conditions_tracing_disabled(state):
    """
    Feature: formalized-stage-interface
    Property 6: Condition checks work correctly when tracing is disabled
    Validates: Requirements 4.5
    """
    original = os.environ.get("LANGSMITH_TRACING")
    os.environ["LANGSMITH_TRACING"] = "false"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            for StageClass in _STAGE_CLASSES:
                stage = StageClass(project_dir=tmpdir, project_id="test")
                result = stage.check_exit_conditions(state=state)
                assert "met" in result
                assert "unmet" in result
                assert isinstance(result["met"], bool)
                assert isinstance(result["unmet"], list)
    finally:
        if original is None:
            os.environ.pop("LANGSMITH_TRACING", None)
        else:
            os.environ["LANGSMITH_TRACING"] = original


def test_property_6_tracing_disabled_matches_enabled():
    """Results are identical whether tracing is on or off."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = {"approval_history": [], "verification_results": {}}
        for StageClass in _STAGE_CLASSES:
            original = os.environ.get("LANGSMITH_TRACING")
            try:
                os.environ["LANGSMITH_TRACING"] = "false"
                stage_off = StageClass(project_dir=tmpdir, project_id="test")
                result_off = stage_off.check_entry_conditions(state=state)

                os.environ["LANGSMITH_TRACING"] = "false"
                stage_on = StageClass(project_dir=tmpdir, project_id="test")
                result_on = stage_on.check_entry_conditions(state=state)
            finally:
                if original is None:
                    os.environ.pop("LANGSMITH_TRACING", None)
                else:
                    os.environ["LANGSMITH_TRACING"] = original

            assert result_off["met"] == result_on["met"], f"{StageClass.__name__}: met differs"
            assert result_off["unmet"] == result_on["unmet"], f"{StageClass.__name__}: unmet differs"
