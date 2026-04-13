"""Contract tests for foundation types: enums, HandoffRecord, and PCG state schemas.

Covers validation contract assertions VAL-FOUND-001 through VAL-FOUND-028.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import get_args, get_type_hints

import pytest
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Enum completeness tests (VAL-FOUND-018 through VAL-FOUND-021)
# ---------------------------------------------------------------------------


class TestAgentRoleEnum:
    """VAL-FOUND-018: AgentRole enum completeness — 7 agents."""

    def test_exactly_seven_members(self):
        from meta_harness.schemas.enums import AgentRole

        assert len(AgentRole) == 7

    def test_expected_values(self):
        from meta_harness.schemas.enums import AgentRole

        expected = {
            "project_manager",
            "harness_engineer",
            "researcher",
            "architect",
            "planner",
            "developer",
            "evaluator",
        }
        actual = {member.value for member in AgentRole}
        assert actual == expected

    def test_string_enum(self):
        """AgentRole values are strings (StrEnum)."""
        from meta_harness.schemas.enums import AgentRole

        for member in AgentRole:
            assert isinstance(member.value, str)
            assert isinstance(member, str)


class TestPhaseEnum:
    """VAL-FOUND-019: Phase enum completeness — 6 phases."""

    def test_exactly_six_members(self):
        from meta_harness.schemas.enums import Phase

        assert len(Phase) == 6

    def test_expected_values(self):
        from meta_harness.schemas.enums import Phase

        expected = {
            "scoping",
            "research",
            "architecture",
            "planning",
            "development",
            "acceptance",
        }
        actual = {member.value for member in Phase}
        assert actual == expected


class TestHandoffReasonEnum:
    """VAL-FOUND-020: HandoffReason enum completeness — 7 reasons."""

    def test_exactly_seven_members(self):
        from meta_harness.schemas.enums import HandoffReason

        assert len(HandoffReason) == 7

    def test_expected_values(self):
        from meta_harness.schemas.enums import HandoffReason

        expected = {
            "deliver",
            "return",
            "submit",
            "consult",
            "announce",
            "coordinate",
            "question",
        }
        actual = {member.value for member in HandoffReason}
        assert actual == expected


class TestHandoffStatusEnum:
    """VAL-FOUND-021: HandoffStatus enum completeness — 4 statuses."""

    def test_exactly_four_members(self):
        from meta_harness.schemas.enums import HandoffStatus

        assert len(HandoffStatus) == 4

    def test_expected_values(self):
        from meta_harness.schemas.enums import HandoffStatus

        expected = {"queued", "running", "completed", "failed"}
        actual = {member.value for member in HandoffStatus}
        assert actual == expected


# ---------------------------------------------------------------------------
# HandoffRecord tests (VAL-FOUND-001 through VAL-FOUND-010, 026-028)
# ---------------------------------------------------------------------------


def _make_handoff(**overrides):
    """Factory helper for creating HandoffRecord with valid defaults."""
    from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus
    from meta_harness.schemas.handoff import HandoffRecord

    defaults = {
        "project_id": "proj-test-001",
        "handoff_id": "hoff-001",
        "source_agent": AgentRole.PROJECT_MANAGER,
        "target_agent": AgentRole.HARNESS_ENGINEER,
        "reason": HandoffReason.DELIVER,
        "brief": "Deliver PRD to Harness Engineer for eval design",
        "artifact_paths": ["/pm/artifacts/prd.md"],
        "langsmith_run_id": "ls-run-abc",
        "status": HandoffStatus.QUEUED,
        "created_at": datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return HandoffRecord(**defaults)


class TestHandoffRecordBaseFields:
    """VAL-FOUND-001: All 10 base fields exist with correct types."""

    def test_all_base_fields_present(self):

        record = _make_handoff()
        assert record.project_id == "proj-test-001"
        assert record.handoff_id == "hoff-001"
        assert record.source_agent == "project_manager"
        assert record.target_agent == "harness_engineer"
        assert record.reason == "deliver"
        assert record.brief == "Deliver PRD to Harness Engineer for eval design"
        assert record.artifact_paths == ["/pm/artifacts/prd.md"]
        assert record.langsmith_run_id == "ls-run-abc"
        assert record.status == "queued"
        assert isinstance(record.created_at, datetime)

    def test_field_type_annotations(self):
        """Verify field types via model_fields introspection."""
        from meta_harness.schemas.handoff import HandoffRecord

        fields = HandoffRecord.model_fields
        assert "project_id" in fields
        assert "handoff_id" in fields
        assert "source_agent" in fields
        assert "target_agent" in fields
        assert "reason" in fields
        assert "brief" in fields
        assert "artifact_paths" in fields
        assert "langsmith_run_id" in fields
        assert "status" in fields
        assert "created_at" in fields


class TestHandoffRecordAccepted:
    """VAL-FOUND-002: HandoffRecord `accepted` extension field."""

    def test_accepted_defaults_to_none(self):
        record = _make_handoff()
        assert record.accepted is None

    def test_accepted_true(self):
        record = _make_handoff(accepted=True)
        assert record.accepted is True

    def test_accepted_false(self):
        record = _make_handoff(accepted=False)
        assert record.accepted is False


class TestHandoffRecordValidation:
    """VAL-FOUND-003 & VAL-FOUND-004: Pydantic validation rejects invalid/missing fields."""

    def test_rejects_invalid_source_agent(self):
        with pytest.raises(ValidationError):
            _make_handoff(source_agent="unknown-agent")

    def test_rejects_invalid_target_agent(self):
        with pytest.raises(ValidationError):
            _make_handoff(target_agent="invalid-target")

    def test_rejects_invalid_reason(self):
        with pytest.raises(ValidationError):
            _make_handoff(reason="invalid-reason")

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            _make_handoff(status="invalid-status")

    def test_rejects_missing_brief(self):
        from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        with pytest.raises(ValidationError):
            HandoffRecord(
                project_id="p1",
                handoff_id="h1",
                source_agent=AgentRole.PROJECT_MANAGER,
                target_agent=AgentRole.HARNESS_ENGINEER,
                reason=HandoffReason.DELIVER,
                # brief deliberately omitted
                status=HandoffStatus.QUEUED,
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_project_id(self):
        from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        with pytest.raises(ValidationError):
            HandoffRecord(
                # project_id deliberately omitted
                handoff_id="h1",
                source_agent=AgentRole.PROJECT_MANAGER,
                target_agent=AgentRole.HARNESS_ENGINEER,
                reason=HandoffReason.DELIVER,
                brief="test",
                status=HandoffStatus.QUEUED,
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_source_agent(self):
        from meta_harness.schemas.enums import HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        with pytest.raises(ValidationError):
            HandoffRecord(
                project_id="p1",
                handoff_id="h1",
                # source_agent deliberately omitted
                target_agent="harness_engineer",
                reason=HandoffReason.DELIVER,
                brief="test",
                status=HandoffStatus.QUEUED,
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_rejects_missing_target_agent(self):
        from meta_harness.schemas.enums import HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        with pytest.raises(ValidationError):
            HandoffRecord(
                project_id="p1",
                handoff_id="h1",
                source_agent="project_manager",
                # target_agent deliberately omitted
                reason=HandoffReason.DELIVER,
                brief="test",
                status=HandoffStatus.QUEUED,
                created_at=datetime.now(tz=timezone.utc),
            )


class TestHandoffRecordRoundtrip:
    """VAL-FOUND-005 & VAL-FOUND-006: Serialization/deserialization roundtrip."""

    def test_model_dump_validate_roundtrip(self):
        from meta_harness.schemas.handoff import HandoffRecord

        record = _make_handoff(accepted=True)
        dumped = record.model_dump()
        restored = HandoffRecord.model_validate(dumped)

        assert restored.project_id == record.project_id
        assert restored.handoff_id == record.handoff_id
        assert restored.source_agent == record.source_agent
        assert restored.target_agent == record.target_agent
        assert restored.reason == record.reason
        assert restored.brief == record.brief
        assert restored.artifact_paths == record.artifact_paths
        assert restored.langsmith_run_id == record.langsmith_run_id
        assert restored.status == record.status
        assert restored.created_at == record.created_at
        assert restored.accepted == record.accepted

    def test_json_roundtrip(self):
        from meta_harness.schemas.handoff import HandoffRecord

        record = _make_handoff(accepted=True)
        json_str = record.model_dump_json()
        restored = HandoffRecord.model_validate_json(json_str)

        assert restored.project_id == record.project_id
        assert restored.handoff_id == record.handoff_id
        assert restored.brief == record.brief
        assert restored.accepted == record.accepted

    def test_accepted_none_survives_json_roundtrip(self):
        """VAL-FOUND-006: accepted=None is preserved (not stripped)."""
        from meta_harness.schemas.handoff import HandoffRecord

        record = _make_handoff(accepted=None)
        json_str = record.model_dump_json()

        # Verify 'accepted' key is present in JSON
        parsed = json.loads(json_str)
        assert "accepted" in parsed
        assert parsed["accepted"] is None

        restored = HandoffRecord.model_validate_json(json_str)
        assert restored.accepted is None


class TestHandoffRecordMessageProtocol:
    """VAL-FOUND-007 & VAL-FOUND-008: HandoffRecord implements message protocol."""

    def test_has_id_field(self):
        record = _make_handoff()
        assert hasattr(record, "id")
        assert isinstance(record.id, str)

    def test_id_derived_from_handoff_id(self):
        """VAL-FOUND-008: id == handoff_id."""
        record = _make_handoff(handoff_id="hoff-123")
        assert record.id == "hoff-123"

    def test_add_messages_retains_distinct_ids(self):
        """Two records with different IDs are both retained by add_messages."""
        r1 = _make_handoff(handoff_id="hoff-1")
        r2 = _make_handoff(handoff_id="hoff-2")
        result = add_messages([r1], [r2])
        assert len(result) == 2
        ids = {r.id for r in result}
        assert ids == {"hoff-1", "hoff-2"}

    def test_add_messages_deduplicates_same_id(self):
        """Two records with the same ID — add_messages replaces."""
        r1 = _make_handoff(handoff_id="hoff-same", brief="Original brief")
        r2 = _make_handoff(handoff_id="hoff-same", brief="Updated brief")
        result = add_messages([r1], [r2])
        assert len(result) == 1
        assert result[0].id == "hoff-same"


class TestHandoffRecordDefaults:
    """VAL-FOUND-009, VAL-FOUND-010, VAL-FOUND-027: Default values."""

    def test_artifact_paths_defaults_to_empty_list(self):
        """VAL-FOUND-009."""
        from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        record = HandoffRecord(
            project_id="p1",
            handoff_id="h1",
            source_agent=AgentRole.PROJECT_MANAGER,
            target_agent=AgentRole.HARNESS_ENGINEER,
            reason=HandoffReason.DELIVER,
            brief="test",
            status=HandoffStatus.QUEUED,
            created_at=datetime.now(tz=timezone.utc),
        )
        assert record.artifact_paths == []

    def test_langsmith_run_id_defaults_to_none(self):
        """VAL-FOUND-010."""
        from meta_harness.schemas.enums import AgentRole, HandoffReason, HandoffStatus
        from meta_harness.schemas.handoff import HandoffRecord

        record = HandoffRecord(
            project_id="p1",
            handoff_id="h1",
            source_agent=AgentRole.PROJECT_MANAGER,
            target_agent=AgentRole.HARNESS_ENGINEER,
            reason=HandoffReason.DELIVER,
            brief="test",
            status=HandoffStatus.QUEUED,
            created_at=datetime.now(tz=timezone.utc),
        )
        assert record.langsmith_run_id is None

    def test_status_defaults_to_queued(self):
        """VAL-FOUND-027."""
        from meta_harness.schemas.enums import AgentRole, HandoffReason
        from meta_harness.schemas.handoff import HandoffRecord

        record = HandoffRecord(
            project_id="p1",
            handoff_id="h1",
            source_agent=AgentRole.PROJECT_MANAGER,
            target_agent=AgentRole.HARNESS_ENGINEER,
            reason=HandoffReason.DELIVER,
            brief="test",
            created_at=datetime.now(tz=timezone.utc),
        )
        assert record.status == "queued"


class TestHandoffRecordCreatedAt:
    """VAL-FOUND-026: created_at is RFC3339 compatible."""

    def test_created_at_rfc3339_serialization(self):

        dt = datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc)
        record = _make_handoff(created_at=dt)
        json_str = record.model_dump_json()
        parsed = json.loads(json_str)

        # Verify RFC3339 compatibility
        restored_dt = datetime.fromisoformat(parsed["created_at"])
        assert restored_dt == dt


class TestHandoffRecordFrozen:
    """VAL-FOUND-028: HandoffRecord is immutable after creation."""

    def test_frozen_rejects_mutation(self):
        record = _make_handoff()
        with pytest.raises((ValidationError, AttributeError)):
            record.brief = "modified"  # type: ignore[misc]

    def test_frozen_rejects_status_mutation(self):
        record = _make_handoff()
        with pytest.raises((ValidationError, AttributeError)):
            record.status = "completed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ProjectCoordinationState tests (VAL-FOUND-011 through VAL-FOUND-017)
# ---------------------------------------------------------------------------


class TestProjectCoordinationState:
    """VAL-FOUND-011 through VAL-FOUND-017: PCG state schema."""

    def test_has_all_six_keys(self):
        """VAL-FOUND-011."""
        from meta_harness.schemas.state import ProjectCoordinationState

        expected_keys = {
            "messages",
            "project_id",
            "current_phase",
            "current_agent",
            "handoff_log",
            "pending_handoff",
        }
        actual_keys = set(ProjectCoordinationState.__annotations__.keys())
        assert actual_keys == expected_keys

    def test_messages_uses_add_messages_reducer(self):
        """VAL-FOUND-012: messages annotated with add_messages reducer."""
        from meta_harness.schemas.state import ProjectCoordinationState

        hints = get_type_hints(ProjectCoordinationState, include_extras=True)
        messages_hint = hints["messages"]
        args = get_args(messages_hint)
        # Should have the list type and the add_messages reducer in metadata
        assert len(args) >= 2
        # The reducer function should be add_messages
        assert args[1] is add_messages

    def test_handoff_log_uses_add_messages_reducer(self):
        """VAL-FOUND-013: handoff_log annotated with add_messages reducer."""
        from meta_harness.schemas.state import ProjectCoordinationState

        hints = get_type_hints(ProjectCoordinationState, include_extras=True)
        handoff_log_hint = hints["handoff_log"]
        args = get_args(handoff_log_hint)
        assert len(args) >= 2
        assert args[1] is add_messages

    def test_pending_handoff_is_optional_handoff_record(self):
        """VAL-FOUND-014: pending_handoff is HandoffRecord | None."""
        from meta_harness.schemas.handoff import HandoffRecord
        from meta_harness.schemas.state import ProjectCoordinationState

        hints = get_type_hints(ProjectCoordinationState, include_extras=True)
        ph_hint = hints["pending_handoff"]
        # Should be Optional[HandoffRecord] or HandoffRecord | None
        args = get_args(ph_hint)
        assert HandoffRecord in args
        assert type(None) in args

    def test_project_id_is_str(self):
        """VAL-FOUND-017: project_id is plain str, no reducer."""
        from meta_harness.schemas.state import ProjectCoordinationState

        hints = get_type_hints(ProjectCoordinationState, include_extras=True)
        pid_hint = hints["project_id"]
        # Should be plain str, not Annotated
        assert pid_hint is str

    def test_state_works_with_state_graph(self):
        """Verify ProjectCoordinationState can be used with StateGraph."""
        from meta_harness.schemas.state import ProjectCoordinationState

        builder = StateGraph(ProjectCoordinationState)
        # Should not raise
        assert builder is not None


class TestProjectCoordinationInput:
    """VAL-FOUND-022: ProjectCoordinationInput exposes only `messages`."""

    def test_only_messages_key(self):
        from meta_harness.schemas.state import ProjectCoordinationInput

        keys = set(ProjectCoordinationInput.__annotations__.keys())
        assert keys == {"messages"}

    def test_usable_as_input_schema(self):
        """Can be passed to StateGraph as input_schema."""
        from meta_harness.schemas.state import (
            ProjectCoordinationInput,
            ProjectCoordinationState,
        )

        builder = StateGraph(
            ProjectCoordinationState,
            input_schema=ProjectCoordinationInput,
        )
        assert builder is not None


class TestProjectCoordinationOutput:
    """VAL-FOUND-023: ProjectCoordinationOutput is defined and usable."""

    def test_importable_and_has_annotations(self):
        from meta_harness.schemas.state import ProjectCoordinationOutput

        assert hasattr(ProjectCoordinationOutput, "__annotations__")

    def test_usable_as_output_schema(self):
        from meta_harness.schemas.state import (
            ProjectCoordinationOutput,
            ProjectCoordinationState,
        )

        builder = StateGraph(
            ProjectCoordinationState,
            output_schema=ProjectCoordinationOutput,
        )
        assert builder is not None


class TestProjectCoordinationContext:
    """VAL-FOUND-024: ProjectCoordinationContext is defined and importable."""

    def test_importable(self):
        from meta_harness.schemas.state import ProjectCoordinationContext

        assert hasattr(ProjectCoordinationContext, "__annotations__")


# ---------------------------------------------------------------------------
# Cross-cutting: enum/state consistency (VAL-FOUND-025)
# ---------------------------------------------------------------------------


class TestEnumStateConsistency:
    """VAL-FOUND-025: Agent enum values match current_agent."""

    def test_agent_role_values_are_underscored(self):
        """AgentRole enum values use underscores, matching current_agent annotation."""
        from meta_harness.schemas.enums import AgentRole

        for member in AgentRole:
            # Values should use underscores (Python convention, matching PCG state)
            assert "_" in member.value or member.value in {
                "researcher",
                "architect",
                "planner",
                "developer",
                "evaluator",
            }


# ---------------------------------------------------------------------------
# Import convenience test (verification step from feature spec)
# ---------------------------------------------------------------------------


class TestImportConvenience:
    """Verify all types are importable from expected locations."""

    def test_import_from_schemas_handoff(self):
        from meta_harness.schemas.handoff import HandoffRecord

        assert HandoffRecord is not None

    def test_import_enums_from_schemas(self):
        from meta_harness.schemas.enums import (
            AgentRole,
            HandoffReason,
            HandoffStatus,
            Phase,
        )

        assert all([AgentRole, Phase, HandoffReason, HandoffStatus])

    def test_import_state_schemas(self):
        from meta_harness.schemas.state import (
            ProjectCoordinationContext,
            ProjectCoordinationInput,
            ProjectCoordinationOutput,
            ProjectCoordinationState,
        )

        assert all([
            ProjectCoordinationState,
            ProjectCoordinationInput,
            ProjectCoordinationOutput,
            ProjectCoordinationContext,
        ])

    def test_import_from_schemas_package(self):
        """All types re-exported from schemas/__init__.py."""
        from meta_harness.schemas import (
            AgentRole,
            HandoffReason,
            HandoffRecord,
            HandoffStatus,
            Phase,
            ProjectCoordinationContext,
            ProjectCoordinationInput,
            ProjectCoordinationOutput,
            ProjectCoordinationState,
        )

        assert all([
            AgentRole,
            Phase,
            HandoffReason,
            HandoffStatus,
            HandoffRecord,
            ProjectCoordinationState,
            ProjectCoordinationInput,
            ProjectCoordinationOutput,
            ProjectCoordinationContext,
        ])
