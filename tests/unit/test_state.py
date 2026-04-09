import json
import operator
from typing import Any, get_type_hints

import pytest
from hypothesis import given, settings, strategies as st

from langchain.agents.middleware.types import AgentState
from langchain_core.runnables import RunnableConfig

from meta_agent.state import (
    MetaAgentState,
    StageContext,
    make_stage_context,
    create_initial_state,
)
from meta_agent.middleware.meta_state import (
    MetaAgentStateSchema,
    MetaAgentStateMiddleware,
)
from meta_agent.stages.base import BaseStage
from meta_agent.stages.spec_generation import SpecGenerationStage


# ---------------------------------------------------------------------------
# Task 1 & 6 Tests: StageContext & `make_stage_context`
# ---------------------------------------------------------------------------

@given(
    revision_count=st.integers(min_value=0, max_value=1000),
    extra=st.dictionaries(st.text(), st.text()),
)
@settings(max_examples=100)
def test_make_stage_context_roundtrip(revision_count: int, extra: dict):
    """Property 1: make_stage_context round-trip fidelity."""
    ctx = make_stage_context(revision_count=revision_count, extra=extra)
    assert ctx == {"revision_count": revision_count, "extra": extra}
    assert json.loads(json.dumps(ctx)) == ctx


@given(
    rev_a=st.integers(min_value=0, max_value=100),
    rev_b=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100)
def test_stage_metadata_merge_preserves_keys(rev_a: int, rev_b: int):
    """Property 2: stage_metadata merge preserves all stage keys."""
    ctx_a = make_stage_context(revision_count=rev_a)
    ctx_b = make_stage_context(revision_count=rev_b)

    dict_a = {"STAGE_A": ctx_a}
    dict_b = {"STAGE_B": ctx_b}

    merged = operator.or_(dict_a, dict_b)
    assert "STAGE_A" in merged
    assert "STAGE_B" in merged
    assert merged["STAGE_A"]["revision_count"] == rev_a
    assert merged["STAGE_B"]["revision_count"] == rev_b


def test_factory_smoke():
    """Factory smoke tests."""
    assert make_stage_context() == {"revision_count": 0, "extra": {}}
    assert make_stage_context(3, {"k": "v"}) == {"revision_count": 3, "extra": {"k": "v"}}


def test_create_initial_state_compliance():
    """create_initial_state smoke test."""
    state = create_initial_state("test")
    assert "stage_metadata" in state
    assert state["stage_metadata"] == {}
    assert "spec_generation_feedback_cycles" not in state
    assert "pending_research_gap_request" not in state


# ---------------------------------------------------------------------------
# Task 2 Tests: Middleware Migration
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=0, max_value=1000))
@settings(max_examples=100)
def test_before_agent_migration(n: int):
    """Property 5: before_agent migration of legacy field."""
    mw = MetaAgentStateMiddleware()
    # State with legacy field but no stage_metadata
    state = {"spec_generation_feedback_cycles": n}
    config = RunnableConfig()
    updates = mw.before_agent(state, None, config)
    
    assert updates is not None
    assert "stage_metadata" in updates
    assert "SPEC_GENERATION" in updates["stage_metadata"]
    assert updates["stage_metadata"]["SPEC_GENERATION"]["revision_count"] == n


def test_before_agent_example():
    """before_agent example: state without stage_metadata gets empty dict."""
    mw = MetaAgentStateMiddleware()
    state = {"current_stage": "INTAKE", "project_id": "test"}
    config = RunnableConfig()
    updates = mw.before_agent(state, None, config)
    assert updates is not None
    assert updates["stage_metadata"] == {}


# ---------------------------------------------------------------------------
# Task 3 Tests: BaseStage sync_from_state & Back-compat
# ---------------------------------------------------------------------------

class DummyStage(BaseStage):
    STAGE_NAME = "TEST_STAGE"
    
    def _check_entry_impl(self, state: dict[str, Any]):
        return self._pass()
        
    def _check_exit_impl(self, state: dict[str, Any]):
        return self._pass()


@given(n=st.integers(min_value=0, max_value=1000))
@settings(max_examples=100)
def test_sync_from_state_correctly_hydrates(n: int):
    """Property 3: sync_from_state correctly hydrates revision_count."""
    stage = DummyStage("/dummy", "proj")
    state = {"stage_metadata": {"TEST_STAGE": make_stage_context(revision_count=n)}}
    stage.sync_from_state(state)
    assert stage.revision_count == n


@given(n=st.integers(min_value=0, max_value=1000))
@settings(max_examples=100)
def test_sync_from_state_legacy_fallback(n: int):
    """Property 4: Legacy field backward-compat fallback."""
    stage = DummyStage("/dummy", "proj")
    state = {"spec_generation_feedback_cycles": n}
    
    with pytest.warns(DeprecationWarning, match="spec_generation_feedback_cycles is deprecated"):
        stage.sync_from_state(state)
        
    assert stage.revision_count == n


def test_sync_from_state_edge_case_empty():
    """sync_from_state edge-case: empty stage_metadata dict produces 0."""
    stage = DummyStage("/dummy", "proj")
    stage.sync_from_state({"stage_metadata": {}})
    assert stage.revision_count == 0


# ---------------------------------------------------------------------------
# Task 4 Tests: SpecGenerationStage
# ---------------------------------------------------------------------------

def test_spec_generation_uses_base_sync():
    """Assert SpecGenerationStage uses base sync_from_state."""
    assert "sync_from_state" not in SpecGenerationStage.__dict__
    
    stage = SpecGenerationStage("/dummy", "proj")
    
    # Verify _check_exit_impl reads correctly. (Set revision high to force failure)
    state = {
        "stage_metadata": {"SPEC_GENERATION": make_stage_context(revision_count=10)},
        "current_spec_path": stage.spec_path,
        "verification_results": {"technical_specification": {"status": "pass"}},
        "eval_suites": [stage.tier1_eval_suite_path, stage.arch_eval_suite_path],
    }
    
    # We mock out artifact_is_proven to bypass disk checks
    stage._artifact_is_proven = lambda path, st, require_approval=False, approval_alias=None: (True, "")
    
    result = stage._check_exit_impl(state)
    assert result["met"] is False
    assert any("exceeded maximum cycles" in reason for reason in result["unmet"])


# ---------------------------------------------------------------------------
# Task 6 Tests: Schema Drift Contract
# ---------------------------------------------------------------------------

def test_schema_drift_contract():
    """Property 6: Schema drift contract test."""
    state_hints = get_type_hints(MetaAgentState, include_extras=True)
    schema_hints = get_type_hints(MetaAgentStateSchema, include_extras=True)
    agent_state_hints = get_type_hints(AgentState, include_extras=True)

    # Subtract AgentState base fields from the schema side.
    # `messages` lives in AgentState so it is excluded from schema_keys after subtraction,
    # but it IS declared in MetaAgentState — exclude it from state_keys for the comparison.
    # `auto_approve_hitl` is a runtime-only injection flag in MetaAgentStateSchema with no
    # MetaAgentState counterpart by design; exclude it from schema_keys as well.
    SCHEMA_ONLY_FIELDS = {"auto_approve_hitl"}
    STATE_INHERITED_FIELDS = set(agent_state_hints.keys())  # e.g. "messages"

    state_keys = set(state_hints.keys()) - STATE_INHERITED_FIELDS
    schema_keys = set(schema_hints.keys()) - set(agent_state_hints.keys()) - SCHEMA_ONLY_FIELDS

    # Remove artifact_protocols from state_keys as it is internally typed as NotRequired
    state_keys.discard("artifact_protocols")
    schema_keys.discard("artifact_protocols")

    assert state_keys == schema_keys, f"Schema drift detected: {state_keys ^ schema_keys}"

    assert "stage_metadata" in state_keys
    assert "spec_generation_feedback_cycles" not in state_keys
    assert "pending_research_gap_request" not in state_keys

    # Check that stage_metadata carries operator.or_ in MetaAgentState
    meta_hint = state_hints["stage_metadata"]
    assert getattr(meta_hint, "__metadata__", None), "Missing Annotated metadata on MetaAgentState.stage_metadata"
    assert operator.or_ in meta_hint.__metadata__, "Missing operator.or_ reducer on MetaAgentState.stage_metadata"

    # Check that stage_metadata carries operator.or_ in MetaAgentStateSchema too.
    # The field is wrapped in NotRequired[Annotated[...]], so unwrap one level first.
    schema_meta_hint = schema_hints["stage_metadata"]
    inner = getattr(schema_meta_hint, "__args__", (schema_meta_hint,))[0]
    assert getattr(inner, "__metadata__", None), "Missing Annotated metadata on MetaAgentStateSchema.stage_metadata"
    assert operator.or_ in inner.__metadata__, "Missing operator.or_ reducer on MetaAgentStateSchema.stage_metadata"
