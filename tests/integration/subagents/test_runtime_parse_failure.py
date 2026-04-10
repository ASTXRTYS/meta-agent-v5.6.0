# REPLACES: (no direct legacy equivalent — runtime parse-error normalization coverage)
# COVERS: subagents.parse_failure_normalization
"""Integration tests for runtime parse-failure and schema-violation normalization."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest

from meta_agent.subagents.code_agent_runtime import normalize_code_agent_outputs
from meta_agent.subagents.evaluation_agent_runtime import normalize_evaluation_agent_outputs
from meta_agent.subagents.plan_writer_runtime import normalize_plan_writer_outputs
from meta_agent.subagents.spec_writer_agent import normalize_spec_writer_outputs
from meta_agent.utils.parsing import ParseError

pytestmark = pytest.mark.integration


NormalizeFn = Callable[..., dict[str, Any]]


def _raw_result(assistant_text: str) -> dict[str, Any]:
    return {"messages": [{"type": "ai", "content": assistant_text}]}


RUNTIME_CASES = [
    (
        "meta_agent.subagents.spec_writer_agent.parse_status_block",
        normalize_spec_writer_outputs,
        {
            "needs_additional_research": False,
            "additional_research_request": "",
        },
        "complete",
    ),
    (
        "meta_agent.subagents.code_agent_runtime.parse_status_block",
        normalize_code_agent_outputs,
        {
            "tasks_completed": [],
            "artifacts_written": [],
        },
        "blocked",
    ),
    (
        "meta_agent.subagents.plan_writer_runtime.parse_status_block",
        normalize_plan_writer_outputs,
        {
            "plan_path": "",
            "revision_notes": "",
        },
        None,
    ),
    (
        "meta_agent.subagents.evaluation_agent_runtime.parse_status_block",
        normalize_evaluation_agent_outputs,
        {
            "eval_summary": "",
            "eval_results": {},
        },
        None,
    ),
]


@pytest.mark.parametrize(
    ("patch_target", "normalize_fn", "expected_defaults", "forbidden_status"),
    RUNTIME_CASES,
)
def test_parse_error_sets_parse_error_status_for_all_runtimes(
    tmp_path: pytest.TempPathFactory,
    patch_target: str,
    normalize_fn: NormalizeFn,
    expected_defaults: dict[str, Any],
    forbidden_status: str | None,
) -> None:
    with patch(
        patch_target,
        side_effect=ParseError(reason="test error", char_offset=5),
    ):
        result = normalize_fn(
            _raw_result("assistant output"),
            project_dir=str(tmp_path),
            project_id="project-1",
        )

    assert result["status"] == "parse_error"
    if forbidden_status is not None:
        assert result["status"] != forbidden_status

    for key, expected in expected_defaults.items():
        assert result[key] == expected


@pytest.mark.parametrize(
    ("normalize_fn", "expected_defaults"),
    [
        (
            normalize_spec_writer_outputs,
            {
                "needs_additional_research": False,
                "additional_research_request": "",
            },
        ),
        (
            normalize_code_agent_outputs,
            {
                "tasks_completed": [],
                "artifacts_written": [],
            },
        ),
        (
            normalize_plan_writer_outputs,
            {
                "plan_path": "",
                "revision_notes": "",
            },
        ),
        (
            normalize_evaluation_agent_outputs,
            {
                "eval_summary": "",
                "eval_results": {},
            },
        ),
    ],
)
def test_schema_violation_sets_parse_error_for_all_runtimes(
    tmp_path: pytest.TempPathFactory,
    normalize_fn: NormalizeFn,
    expected_defaults: dict[str, Any],
) -> None:
    raw_result = _raw_result("```json\n{\"status\": \"nonsense\"}\n```")

    result = normalize_fn(
        raw_result,
        project_dir=str(tmp_path),
        project_id="project-1",
    )

    assert result["status"] == "parse_error"
    assert result["status"] != "nonsense"
    for key, expected in expected_defaults.items():
        assert result[key] == expected


def test_parse_error_logging_contains_decode_details(
    tmp_path: pytest.TempPathFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    parse_error = ParseError(
        reason="decode failure",
        char_offset=12,
        msg="Expecting property name enclosed in double quotes",
        lineno=1,
        colno=2,
    )

    with patch(
        "meta_agent.subagents.code_agent_runtime.parse_status_block",
        side_effect=parse_error,
    ):
        with caplog.at_level(logging.WARNING):
            normalize_code_agent_outputs(
                _raw_result("assistant output"),
                project_dir=str(tmp_path),
                project_id="project-1",
            )

    records = [
        record
        for record in caplog.records
        if "ParseError extracting status block" in record.getMessage()
    ]
    assert records

    record = records[-1]
    assert "reason=decode failure" in record.getMessage()
    assert "char_offset=12" in record.getMessage()
    assert "msg='Expecting property name enclosed in double quotes'" in record.getMessage()
    assert getattr(record, "parse_error_reason") == "decode failure"
    assert getattr(record, "parse_error_char_offset") == 12
    assert getattr(record, "parse_error_msg") == "Expecting property name enclosed in double quotes"
    assert getattr(record, "parse_error_lineno") == 1
    assert getattr(record, "parse_error_colno") == 2


def test_schema_violation_logging_contains_reason_and_bad_value(
    tmp_path: pytest.TempPathFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        normalize_plan_writer_outputs(
            _raw_result("```json\n{\"status\": \"nonsense\"}\n```"),
            project_dir=str(tmp_path),
            project_id="project-1",
        )

    records = [
        record
        for record in caplog.records
        if "schema_violation" in record.getMessage()
    ]
    assert records

    record = records[-1]
    assert "nonsense" in record.getMessage()
    assert getattr(record, "reason") == "schema_violation"
    assert getattr(record, "actual_status") == "nonsense"
