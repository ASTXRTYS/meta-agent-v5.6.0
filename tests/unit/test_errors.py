"""Unit tests for meta_agent.errors module."""

from __future__ import annotations

import pytest

from meta_agent.errors import (
    RetryPolicy,
    StructuredErrorContext,
    structured_error_context,
    classify_error,
    is_retryable,
    DEFAULT_RETRY_POLICY,
)


class TestRetryPolicy:
    def test_defaults(self):
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.initial_interval == 1.0
        assert policy.backoff_factor == 2.0
        assert policy.max_interval == 10.0

    def test_retry_on_types(self):
        policy = DEFAULT_RETRY_POLICY
        assert ConnectionError in policy.retry_on
        assert TimeoutError in policy.retry_on


class TestStructuredErrorContext:
    def test_from_exception(self):
        try:
            raise ValueError("test error")
        except ValueError as e:
            ctx = structured_error_context(
                error=e,
                current_stage="INTAKE",
                recovery_suggestion="Try again",
            )
            assert ctx.error_type == "ValueError"
            assert ctx.error_message == "test error"
            assert ctx.current_stage == "INTAKE"
            assert ctx.recovery_suggestion == "Try again"
            assert ctx.timestamp  # non-empty


class TestClassifyError:
    def test_retryable(self):
        assert classify_error(ConnectionError()) == "retry"
        assert classify_error(TimeoutError()) == "retry"

    def test_user_fixable(self):
        assert classify_error(FileNotFoundError()) == "user_fixable"
        assert classify_error(PermissionError()) == "user_fixable"

    def test_unexpected(self):
        assert classify_error(RuntimeError()) == "unexpected"


class TestIsRetryable:
    def test_connection_error(self):
        assert is_retryable(ConnectionError())

    def test_value_error(self):
        assert not is_retryable(ValueError())
