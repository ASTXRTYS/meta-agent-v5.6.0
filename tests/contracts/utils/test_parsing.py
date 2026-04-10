# REPLACES: (no direct legacy equivalent — new canonical parser coverage)
# COVERS: utils.parsing
"""Contract tests for canonical JSON parsing utilities."""

from __future__ import annotations

import json
from typing import Any

import pytest
from hypothesis import assume, given, settings, strategies as st

from meta_agent.utils.parsing import ParseError, extract_json_block, parse_status_block

pytestmark = pytest.mark.contract


JSON_SERIALIZABLE_DICTS = st.from_type(dict).filter(lambda d: is_json_serializable(d))
JSON_SCALARS = st.none() | st.booleans() | st.integers() | st.floats(
    allow_nan=False,
    allow_infinity=False,
) | st.text()
JSON_VALUES = st.recursive(
    JSON_SCALARS,
    lambda children: st.lists(children, max_size=4) | st.dictionaries(st.text(), children, max_size=4),
    max_leaves=10,
)
JSON_DICTS = st.dictionaries(st.text(), JSON_VALUES, max_size=6)


def is_json_serializable(value: Any) -> bool:
    """True when value has a stable JSON round-trip."""
    if not isinstance(value, dict):
        return False
    try:
        return json.loads(json.dumps(value)) == value
    except (TypeError, ValueError, OverflowError):
        return False


# Feature: canonical-json-extraction, Property 1: Fenced round-trip
@given(JSON_SERIALIZABLE_DICTS)
@settings(max_examples=100)
def test_property_fenced_round_trip(data: dict[str, Any]) -> None:
    response = f"```json\n{json.dumps(data)}\n```"
    assert json.loads(extract_json_block(response)) == data


# Feature: canonical-json-extraction, Property 2: Bare-object round-trip
@given(JSON_SERIALIZABLE_DICTS)
@settings(max_examples=100)
def test_property_bare_object_round_trip(data: dict[str, Any]) -> None:
    assert json.loads(extract_json_block(json.dumps(data))) == data


# Feature: canonical-json-extraction, Property 3: ParseError invariants
@given(st.text())
@settings(max_examples=100)
def test_property_parse_error_invariants(text: str) -> None:
    try:
        extract_json_block(text)
    except ParseError as error:
        assert 0 <= error.char_offset <= len(text)
        assert len(error.reason) > 0


# Feature: canonical-json-extraction, Property 4: First-block selection
@given(JSON_DICTS, JSON_DICTS)
@settings(max_examples=100)
def test_property_first_block_selection(d1: dict[str, Any], d2: dict[str, Any]) -> None:
    assume(d1 != d2)
    response = (
        f"```json\n{json.dumps(d1)}\n```\n"
        "Some narrative text\n"
        f"```json\n{json.dumps(d2)}\n```"
    )
    assert json.loads(extract_json_block(response)) == d1


# Feature: canonical-json-extraction, Property 5: Block-selection scan
@given(
    d_example=JSON_DICTS,
    d_handshake=JSON_DICTS,
    status_value=st.text(min_size=1).filter(lambda s: bool(s.strip())),
)
@settings(max_examples=100)
def test_property_block_selection_scan(
    d_example: dict[str, Any],
    d_handshake: dict[str, Any],
    status_value: str,
) -> None:
    assume("status" not in d_example)
    handshake = dict(d_handshake)
    handshake["status"] = status_value

    response = (
        "Example configuration follows.\n"
        f"```json\n{json.dumps(d_example)}\n```\n"
        "Status handshake block:\n"
        f"```json\n{json.dumps(handshake)}\n```"
    )
    assert parse_status_block(response) == handshake


def test_extract_json_block_flat_object() -> None:
    payload = {"a": 1}
    response = f"```json\n{json.dumps(payload)}\n```"
    assert json.loads(extract_json_block(response)) == payload


def test_extract_json_block_two_level_nested_object() -> None:
    payload = {"a": {"b": 2}}
    response = f"```json\n{json.dumps(payload)}\n```"
    assert json.loads(extract_json_block(response)) == payload


def test_extract_json_block_three_level_nested_object() -> None:
    payload = {"a": {"b": {"c": 3}}}
    response = f"```json\n{json.dumps(payload)}\n```"
    assert json.loads(extract_json_block(response)) == payload


def test_extract_json_block_brace_inside_string() -> None:
    payload = {"key": "val}ue"}
    response = f"```json\n{json.dumps(payload)}\n```"
    assert json.loads(extract_json_block(response)) == payload


def test_extract_json_block_empty_input_error() -> None:
    with pytest.raises(ParseError) as exc_info:
        extract_json_block("")

    error = exc_info.value
    assert error.reason == "empty input"
    assert error.char_offset == 0


def test_extract_json_block_no_anchor_error() -> None:
    with pytest.raises(ParseError) as exc_info:
        extract_json_block("hello world")

    error = exc_info.value
    assert error.reason == "no JSON anchor found"
    assert error.char_offset == 0


def test_extract_json_block_unbalanced_brace_error() -> None:
    with pytest.raises(ParseError) as exc_info:
        extract_json_block("{unbalanced")

    error = exc_info.value
    assert error.reason == "unbalanced brace"
    assert error.char_offset == 0


def test_extract_json_block_json_decode_diagnostics() -> None:
    invalid_block = "{bad: json}"
    response = f"Prefix text\n```json\n{invalid_block}\n```"
    block_start = response.index("{")

    with pytest.raises(json.JSONDecodeError) as json_exc_info:
        json.loads(invalid_block)
    expected_decode_error = json_exc_info.value

    with pytest.raises(ParseError) as parse_exc_info:
        extract_json_block(response)
    error = parse_exc_info.value

    assert error.char_offset == block_start + expected_decode_error.pos
    assert error.msg == expected_decode_error.msg
    assert error.lineno == expected_decode_error.lineno
    assert error.colno == expected_decode_error.colno


def test_parse_status_block_returns_later_handshake_block() -> None:
    response = (
        "```json\n{\"example\": \"config\"}\n```\n"
        "Some explanation\n"
        "```json\n{\"status\": \"complete\"}\n```"
    )

    result = parse_status_block(response)
    assert result == {"status": "complete"}
    assert result != {"example": "config"}
