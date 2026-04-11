"""Canonical utilities for extracting JSON blocks from agent text responses."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterator, TypedDict

logger = logging.getLogger(__name__)

_JSON_FENCE_TOKEN = "```json"
_BARE_FENCE_TOKEN = "```"


class ParseError(Exception):
    """Raised when parsing a JSON block from text fails."""

    def __init__(
        self,
        reason: str,
        char_offset: int,
        msg: str | None = None,
        lineno: int | None = None,
        colno: int | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.char_offset = char_offset
        self.msg = msg
        self.lineno = lineno
        self.colno = colno

    def __str__(self) -> str:
        base = f"ParseError({self.reason}) at offset {self.char_offset}"
        if self.msg is not None:
            return f"{base} — {self.msg} (line {self.lineno}, col {self.colno})"
        return base


class _ScanRecord(TypedDict):
    start_offset: int
    raw_block: str | None
    kind: str


def _find_next_bare_fence(text: str, lowered: str, start: int) -> int:
    """Return the next bare ``` fence marker (without a language tag)."""
    idx = text.find(_BARE_FENCE_TOKEN, start)
    while idx != -1:
        if lowered.startswith(_JSON_FENCE_TOKEN, idx):
            idx = text.find(_BARE_FENCE_TOKEN, idx + len(_BARE_FENCE_TOKEN))
            continue

        suffix_pos = idx + len(_BARE_FENCE_TOKEN)
        if suffix_pos >= len(text):
            return idx

        next_char = text[suffix_pos]
        if next_char.isspace() or next_char == "{":
            return idx

        idx = text.find(_BARE_FENCE_TOKEN, idx + len(_BARE_FENCE_TOKEN))
    return -1


def _find_balanced_block_end(text: str, start_offset: int) -> int | None:
    """Return the matching closing brace index for a JSON object start."""
    if start_offset < 0 or start_offset >= len(text) or text[start_offset] != "{":
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start_offset, len(text)):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if in_string:
            if ch == "\\":
                escape_next = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                return i

    return None


def _scan_json_blocks_with_offsets(text: str) -> Iterator[_ScanRecord]:
    """Scan text and emit JSON block candidates in document order."""
    lowered = text.lower()
    scan_pos = 0

    while scan_pos < len(text):
        json_fence_pos = lowered.find(_JSON_FENCE_TOKEN, scan_pos)
        bare_fence_pos = _find_next_bare_fence(text, lowered, scan_pos)
        bare_brace_pos = text.find("{", scan_pos)

        anchor_kind = ""
        anchor_pos = -1

        for kind, pos in (
            ("json_fence", json_fence_pos),
            ("bare_fence", bare_fence_pos),
            ("bare_brace", bare_brace_pos),
        ):
            if pos == -1:
                continue
            if anchor_pos == -1 or pos < anchor_pos:
                anchor_kind = kind
                anchor_pos = pos
                continue
            if pos == anchor_pos:
                if anchor_kind == "bare_brace" and kind in {"json_fence", "bare_fence"}:
                    anchor_kind = kind
                    anchor_pos = pos
                    continue
                if anchor_kind == "bare_fence" and kind == "json_fence":
                    anchor_kind = kind
                    anchor_pos = pos

        if anchor_pos == -1:
            break

        if anchor_kind == "json_fence":
            brace_start = text.find("{", anchor_pos + len(_JSON_FENCE_TOKEN))
            if brace_start == -1:
                scan_pos = anchor_pos + len(_JSON_FENCE_TOKEN)
                continue
        elif anchor_kind == "bare_fence":
            brace_start = text.find("{", anchor_pos + len(_BARE_FENCE_TOKEN))
            if brace_start == -1:
                scan_pos = anchor_pos + len(_BARE_FENCE_TOKEN)
                continue
        else:
            brace_start = anchor_pos

        block_end = _find_balanced_block_end(text, brace_start)
        if block_end is None:
            yield {
                "start_offset": brace_start,
                "raw_block": None,
                "kind": "unbalanced",
            }
            scan_pos = brace_start + 1
            continue

        yield {
            "start_offset": brace_start,
            "raw_block": text[brace_start : block_end + 1],
            "kind": "balanced",
        }
        scan_pos = block_end + 1


def iter_json_blocks(text: str) -> Iterator[str]:
    """Yield syntactically balanced JSON object blocks in document order."""
    for record in _scan_json_blocks_with_offsets(text):
        if record["kind"] != "balanced":
            continue
        raw_block = record["raw_block"]
        if raw_block is not None:
            yield raw_block


def _parse_error_from_json_decode(
    error: json.JSONDecodeError,
    block_start: int,
) -> ParseError:
    return ParseError(
        reason=str(error),
        char_offset=block_start + error.pos,
        msg=error.msg,
        lineno=error.lineno,
        colno=error.colno,
    )


def extract_json_block(text: str) -> str:
    """Extract and validate the first JSON block from text."""
    if not text:
        raise ParseError(reason="empty input", char_offset=0)

    found_any_anchor = False
    last_decode_error: ParseError | None = None
    last_unbalanced_start: int | None = None

    for record in _scan_json_blocks_with_offsets(text):
        found_any_anchor = True
        if record["kind"] == "unbalanced":
            last_unbalanced_start = record["start_offset"]
            continue

        raw_block = record["raw_block"]
        if raw_block is None:
            continue

        block_start = record["start_offset"]
        try:
            json.loads(raw_block)
            return raw_block
        except json.JSONDecodeError as error:
            last_decode_error = _parse_error_from_json_decode(error, block_start)

    if not found_any_anchor:
        raise ParseError(reason="no JSON anchor found", char_offset=0)
    if last_decode_error is not None:
        raise last_decode_error
    if last_unbalanced_start is not None:
        raise ParseError(reason="unbalanced brace", char_offset=last_unbalanced_start)
    raise ParseError(reason="no JSON anchor found", char_offset=0)


def parse_status_block(text: str) -> dict[str, Any]:
    """Return the first parsed JSON object with a non-empty string status field."""
    found_any_block = False
    last_decode_error: ParseError | None = None

    for record in _scan_json_blocks_with_offsets(text):
        if record["kind"] != "balanced":
            continue

        raw_block = record["raw_block"]
        if raw_block is None:
            continue

        found_any_block = True
        block_start = record["start_offset"]
        try:
            parsed = json.loads(raw_block)
        except json.JSONDecodeError as error:
            last_decode_error = _parse_error_from_json_decode(error, block_start)
            continue

        if not isinstance(parsed, dict):
            continue
        status_value = parsed.get("status", "")
        if isinstance(status_value, str) and status_value.strip():
            return parsed

    if not found_any_block:
        raise ParseError(reason="no JSON blocks found in response", char_offset=0)
    if last_decode_error is not None:
        raise last_decode_error
    raise ParseError(reason="no_valid_handshake_block", char_offset=0)


__all__ = [
    "ParseError",
    "extract_json_block",
    "iter_json_blocks",
    "parse_status_block",
]
