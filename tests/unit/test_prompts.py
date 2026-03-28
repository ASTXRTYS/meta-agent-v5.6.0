"""Unit tests for prompt section assembly and composition."""

from __future__ import annotations

import pytest

from meta_agent.prompts.sections import (
    ROLE_SECTION,
    CORE_BEHAVIOR_SECTION,
    HITL_PROTOCOL_SECTION,
    COMMUNICATION_SECTION,
    DELEGATION_SECTION,
    MEMORY_SECTION,
    SECTION_MATRIX,
    STAGE_CONTEXTS,
    format_workspace_section,
    format_stage_context,
    format_agents_md_section,
)
from meta_agent.prompts.eval_mindset import EVAL_MINDSET_SECTION
from meta_agent.prompts.scoring_strategy import SCORING_STRATEGY_SECTION
from meta_agent.prompts.eval_approval_protocol import EVAL_APPROVAL_PROTOCOL
from meta_agent.prompts.orchestrator import construct_orchestrator_prompt
from meta_agent.state import WorkflowStage


class TestPromptSections:
    """Tests for individual prompt section constants."""

    def test_role_section_has_pm_identity(self):
        assert "Product Manager" in ROLE_SECTION
        assert "PM" in ROLE_SECTION

    def test_role_section_has_four_responsibilities(self):
        assert "Requirements Elicitation" in ROLE_SECTION
        assert "PRD Authoring" in ROLE_SECTION
        assert "Eval Definition" in ROLE_SECTION
        assert "Stakeholder Alignment" in ROLE_SECTION

    def test_eval_mindset_has_core_principle(self):
        assert "If you cannot evaluate it, you cannot ship it" in EVAL_MINDSET_SECTION

    def test_core_behavior_has_all_rules(self):
        assert "Persistence" in CORE_BEHAVIOR_SECTION
        assert "Accuracy" in CORE_BEHAVIOR_SECTION
        assert "Tool Discipline" in CORE_BEHAVIOR_SECTION
        assert "No Premature PRD Writing" in CORE_BEHAVIOR_SECTION
        assert "No Delegation of PM Work" in CORE_BEHAVIOR_SECTION
        assert "Explicit Reasoning" in CORE_BEHAVIOR_SECTION

    def test_core_behavior_has_pm_reasoning(self):
        assert "<pm_reasoning>" in CORE_BEHAVIOR_SECTION

    def test_scoring_strategy_has_binary_and_likert(self):
        assert "Binary Pass/Fail" in SCORING_STRATEGY_SECTION
        assert "Likert 1-5" in SCORING_STRATEGY_SECTION

    def test_eval_approval_has_seven_branches(self):
        assert "approved" in EVAL_APPROVAL_PROTOCOL
        assert "modify EVAL-XXX" in EVAL_APPROVAL_PROTOCOL
        assert "add an eval" in EVAL_APPROVAL_PROTOCOL
        assert "remove EVAL-XXX" in EVAL_APPROVAL_PROTOCOL
        assert "remove all evals" in EVAL_APPROVAL_PROTOCOL
        assert "unclear or off-topic" in EVAL_APPROVAL_PROTOCOL
        assert "change scoring strategy" in EVAL_APPROVAL_PROTOCOL

    def test_hitl_protocol_has_gated_ops(self):
        assert "write_file" in HITL_PROTOCOL_SECTION
        assert "transition_stage" in HITL_PROTOCOL_SECTION
        assert "execute_command" in HITL_PROTOCOL_SECTION


class TestFormatFunctions:
    """Tests for prompt formatting functions."""

    def test_format_workspace_section(self):
        result = format_workspace_section("/workspace/projects/test", "test")
        assert "/workspace/projects/test" in result
        assert "test" in result
        assert "artifacts/intake/prd.md" in result

    def test_format_stage_context_intake(self):
        result = format_stage_context("INTAKE", "test-project")
        assert "INTAKE" in result
        assert "requirements gathering" in result

    def test_format_stage_context_all_stages(self):
        for stage in WorkflowStage:
            result = format_stage_context(stage.value)
            assert stage.value in result

    def test_format_agents_md_section(self):
        result = format_agents_md_section("test memory content")
        assert "<agents_md>" in result
        assert "test memory content" in result


class TestSectionMatrix:
    """Tests for the SECTION_MATRIX constant."""

    def test_all_seven_agents_present(self):
        expected_agents = {
            "orchestrator", "research-agent", "spec-writer",
            "plan-writer", "code-agent", "test-agent", "verification-agent",
        }
        assert set(SECTION_MATRIX.keys()) == expected_agents

    def test_orchestrator_has_eval_mindset(self):
        assert "EVAL_MINDSET" in SECTION_MATRIX["orchestrator"]

    def test_non_orchestrators_lack_eval_mindset(self):
        for agent in ["research-agent", "spec-writer", "plan-writer",
                       "code-agent", "test-agent", "verification-agent"]:
            assert "EVAL_MINDSET" not in SECTION_MATRIX[agent]

    def test_all_agents_have_role(self):
        for agent, sections in SECTION_MATRIX.items():
            assert "ROLE" in sections, f"{agent} missing ROLE section"

    def test_all_agents_have_core_behavior(self):
        for agent, sections in SECTION_MATRIX.items():
            assert "CORE_BEHAVIOR" in sections, f"{agent} missing CORE_BEHAVIOR"


class TestStageContexts:
    """Tests for stage-specific context blocks."""

    def test_eight_stage_contexts_defined(self):
        # 8 defined in Section 7.3, plus EVALUATION and AUDIT
        assert len(STAGE_CONTEXTS) == 10

    def test_intake_context_has_protocol(self):
        assert "LISTEN" in STAGE_CONTEXTS["INTAKE"]
        assert "CLARIFY" in STAGE_CONTEXTS["INTAKE"]
        assert "CONFIRM" in STAGE_CONTEXTS["INTAKE"]
        assert "DRAFT PRD" in STAGE_CONTEXTS["INTAKE"]
        assert "PROPOSE EVALS" in STAGE_CONTEXTS["INTAKE"]

    def test_execution_context_has_phase_gate(self):
        assert "Phase Gate Protocol" in STAGE_CONTEXTS["EXECUTION"]


class TestConstructOrchestratorPrompt:
    """Tests for construct_orchestrator_prompt."""

    def test_always_includes_role(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test"
        )
        assert "Product Manager" in prompt

    def test_always_includes_eval_mindset(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test"
        )
        assert "Eval-First Mindset" in prompt

    def test_intake_includes_scoring_strategy(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test"
        )
        assert "Scoring Strategy Selection" in prompt

    def test_intake_includes_eval_approval(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test"
        )
        assert "Eval Approval Protocol" in prompt

    def test_research_includes_delegation(self):
        prompt = construct_orchestrator_prompt(
            "RESEARCH", "/workspace/projects/test", "test"
        )
        assert "Delegation Protocol" in prompt

    def test_research_excludes_scoring(self):
        prompt = construct_orchestrator_prompt(
            "RESEARCH", "/workspace/projects/test", "test"
        )
        assert "Scoring Strategy Selection" not in prompt

    def test_agents_md_included_when_present(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test",
            agents_md_content="Previous session notes",
        )
        assert "<agents_md>" in prompt
        assert "Previous session notes" in prompt

    def test_agents_md_excluded_when_empty(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test",
            agents_md_content="",
        )
        assert "<agents_md>" not in prompt

    def test_sections_joined_by_separator(self):
        prompt = construct_orchestrator_prompt(
            "INTAKE", "/workspace/projects/test", "test"
        )
        assert "\n\n---\n\n" in prompt
