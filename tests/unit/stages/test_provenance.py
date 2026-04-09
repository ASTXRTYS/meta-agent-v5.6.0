import os
import tempfile
from typing import Any

from hypothesis import given, settings
import hypothesis.strategies as st

from meta_agent.state import ApprovalEntry
from meta_agent.stages.base import BaseStage
from meta_agent.stages.prd_review import PrdReviewStage
from meta_agent.stages.research import ResearchStage
from meta_agent.stages.spec_generation import SpecGenerationStage
from meta_agent.stages.spec_review import SpecReviewStage


class DummyStage(BaseStage):
    STAGE_NAME = "DUMMY"

    def _check_entry_impl(self, state: dict[str, Any]) -> dict[str, Any]:
        return self._pass()

    def _check_exit_impl(self, state: dict[str, Any]) -> dict[str, Any]:
        return self._pass()


@given(
    file_exists=st.booleans(),
    in_artifacts_written=st.booleans(),
    approved=st.booleans(),
    require_approval=st.booleans(),
)
@settings(max_examples=100)
def test_property_1_provenance_truth_table(
    file_exists: bool,
    in_artifacts_written: bool,
    approved: bool,
    require_approval: bool,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        stage = DummyStage(project_dir=temp_dir, project_id="test")
        artifact_path = os.path.join(temp_dir, "test.md")
        
        if file_exists:
            with open(artifact_path, "w") as f:
                f.write("content")
                
        state = {
            "artifacts_written": [artifact_path] if in_artifacts_written else [],
        }
        
        if not approved:
            state["approval_history"] = [
                {"stage": "test", "artifact": artifact_path, "action": "rejected", "reviewer": "test"}
            ]
        else:
            state["approval_history"] = [
                {"stage": "test", "artifact": artifact_path, "action": "approved", "reviewer": "test"}
            ]
            
        ok, reason = stage._artifact_is_proven(
            artifact_path, state, require_approval=require_approval
        )
        
        expected_ok = file_exists and in_artifacts_written and (not require_approval or approved)
        assert ok == expected_ok
        if ok:
            assert reason == ""
        else:
            assert reason != ""
            assert reason in {
                "not found on disk",
                "not recorded in artifacts_written",
                "not approved in current thread"
            }


@given(
    artifact_path=st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))).filter(lambda x: "\x00" not in x),
    require_approval=st.booleans()
)
@settings(max_examples=100)
def test_property_2_representation_independence(artifact_path: str, require_approval: bool):
    with tempfile.TemporaryDirectory() as temp_dir:
        stage = DummyStage(project_dir=temp_dir, project_id="test")
        temp_file = os.path.join(temp_dir, "test.md")
        with open(temp_file, "w") as f:
            f.write("content")
            
        dataclass_entry = ApprovalEntry.create(
            stage="test",
            artifact=artifact_path,
            action="approved",
            reviewer="test"
        )
        
        raw_dict_entry = {
            "stage": "test",
            "artifact": artifact_path,
            "action": "approved",
            "reviewer": "test"
        }
        
        state_dc = {
            "artifacts_written": [temp_file],
            "approval_history": [dataclass_entry]
        }
        
        state_dict = {
            "artifacts_written": [temp_file],
            "approval_history": [raw_dict_entry]
        }
        
        ok1, reason1 = stage._artifact_is_proven(temp_file, state_dc, require_approval=require_approval, approval_alias=artifact_path)
        ok2, reason2 = stage._artifact_is_proven(temp_file, state_dict, require_approval=require_approval, approval_alias=artifact_path)
        
        assert ok1 == ok2
        assert reason1 == reason2


@given(
    alias=st.sampled_from(["prd", "eval_suite", "research_clusters", "research_bundle",
                           "technical_specification", "eval_suite_architecture"]),
)
@settings(max_examples=100)
def test_property_3_alias_full_path_equivalence(alias: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        stage = DummyStage(project_dir=temp_dir, project_id="test")
        artifact_path = os.path.join(temp_dir, f"{alias}.md")
        
        with open(artifact_path, "w") as f:
            f.write("test")
            
        entry_with_path = {
            "stage": "test",
            "artifact": artifact_path,
            "action": "approved",
            "reviewer": "test"
        }
        
        entry_with_alias = {
            "stage": "test",
            "artifact": alias,
            "action": "approved",
            "reviewer": "test"
        }
        
        state_path = {
            "artifacts_written": [artifact_path],
            "approval_history": [entry_with_path]
        }
        
        state_alias = {
            "artifacts_written": [artifact_path],
            "approval_history": [entry_with_alias]
        }
        
        ok1, _ = stage._artifact_is_proven(artifact_path, state_path, require_approval=True, approval_alias=alias)
        ok2, _ = stage._artifact_is_proven(artifact_path, state_alias, require_approval=True, approval_alias=alias)
        
        assert ok1 is True
        assert ok2 is True


@given(
    failure_type=st.sampled_from(["disk", "written", "approved"]),
    stage_type=st.sampled_from([PrdReviewStage, ResearchStage, SpecGenerationStage, SpecReviewStage])
)
@settings(max_examples=100)
def test_property_4_diagnostic_messages(failure_type: str, stage_type: Any):
    with tempfile.TemporaryDirectory() as temp_dir:
        stage = stage_type(project_dir=temp_dir, project_id="test")
        
        if stage_type == PrdReviewStage:
            path = stage.prd_path
        elif stage_type == ResearchStage:
            path = stage.research_clusters_path
        elif stage_type == SpecGenerationStage:
            path = stage.spec_path
        elif stage_type == SpecReviewStage:
            path = stage.spec_path
            
        state = {
            "artifacts_written": [path],
            "approval_history": [{"artifact": path, "action": "approved"}]
        }
        
        if failure_type == "disk":
            pass # No file
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write("content")
                
            if failure_type == "written":
                state["artifacts_written"] = []
            elif failure_type == "approved":
                state["approval_history"] = []
                
        result = stage._check_exit_impl(state)
        unmet = result["unmet"]
        
        # Determine the expected reason fragment
        if failure_type == "disk":
            reason_fragment = "not found on disk"
        elif failure_type == "written":
            reason_fragment = "not recorded in artifacts_written"
        else:
            reason_fragment = "not approved in current thread"
            
        found = False
        for msg in unmet:
            if path in msg and reason_fragment in msg:
                found = True
                
        # SpecGenerationStage sets require_approval=False, so 'approved' won't fail provenance for spec_path.
        if stage_type == SpecGenerationStage and failure_type == "approved":
            found = True
            
        assert found


@given(
    file_exists=st.booleans(),
    in_artifacts_written=st.booleans(),
    approved=st.booleans(),
    require_approval=st.booleans(),
)
@settings(max_examples=100)
def test_property_5_reason_strings_allowed_set(
    file_exists: bool,
    in_artifacts_written: bool,
    approved: bool,
    require_approval: bool,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        stage = DummyStage(project_dir=temp_dir, project_id="test")
        artifact_path = os.path.join(temp_dir, "test.md")
        
        if file_exists:
            with open(artifact_path, "w") as f:
                f.write("content")
                
        state = {
            "artifacts_written": [artifact_path] if in_artifacts_written else [],
            "approval_history": [{"stage": "test", "artifact": artifact_path, "action": "approved" if approved else "rejected", "reviewer": "test"}]
        }
        
        ok, reason = stage._artifact_is_proven(artifact_path, state, require_approval=require_approval)
        
        if not ok:
            assert reason in {
                "not found on disk",
                "not recorded in artifacts_written",
                "not approved in current thread"
            }
