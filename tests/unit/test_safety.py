"""Unit tests for meta_agent.safety module."""

from __future__ import annotations

import pytest

from meta_agent.safety import (
    RECURSION_LIMITS,
    TOKEN_BUDGET_LIMITS,
    get_token_budget,
    validate_path,
    validate_command,
    is_eval_immutable,
    validate_eval_write,
)


class TestRecursionLimits:
    def test_all_agents_have_limits(self):
        expected = {
            "orchestrator", "code-agent", "research-agent",
            "spec-writer", "plan-writer", "verification-agent",
            "test-agent", "document-renderer", "observation-agent",
            "evaluation-agent", "audit-agent",
        }
        assert set(RECURSION_LIMITS.keys()) == expected

    def test_orchestrator_highest(self):
        assert RECURSION_LIMITS["orchestrator"] == 200
        for agent, limit in RECURSION_LIMITS.items():
            assert limit <= 200


class TestTokenBudget:
    def test_default_budget(self):
        assert get_token_budget("unknown-agent") == 100_000

    def test_research_agent_budget(self):
        assert get_token_budget("research-agent") == 1_000_000

    def test_spec_writer_budget(self):
        assert get_token_budget("spec-writer") == 200_000


class TestValidatePath:
    def test_allows_normal_path(self):
        assert validate_path("projects/test/prd.md")

    def test_blocks_path_traversal(self):
        assert not validate_path("../../../etc/passwd")

    def test_blocks_embedded_traversal(self):
        assert not validate_path("projects/../../etc/passwd")


class TestValidateCommand:
    def test_hitl_always_required(self):
        result = validate_command("ls -la")
        assert result["hitl_required"] is True

    def test_timeout(self):
        result = validate_command("sleep 10")
        assert result["timeout"] == 300


class TestEvalImmutability:
    def test_immutable_during_execution(self):
        assert is_eval_immutable("EXECUTION")

    def test_not_immutable_during_intake(self):
        assert not is_eval_immutable("INTAKE")

    def test_eval_write_allowed_outside_execution(self):
        assert validate_eval_write("INTAKE", "/evals/test.yaml")

    def test_eval_write_blocked_during_execution(self):
        assert not validate_eval_write("EXECUTION", "/evals/test.yaml")

    def test_eval_write_allowed_with_hitl(self):
        assert validate_eval_write("EXECUTION", "/evals/test.yaml", is_hitl=True)
