"""Anthropic-native model features and server-side tool inventory."""

from __future__ import annotations

from typing import Any

ANTHROPIC_NATIVE_FEATURES: dict[str, dict[str, Any]] = {
    'adaptive_thinking': {
        'kind': 'request_default',
        'request_patch': {'thinking': {'type': 'adaptive'}},
        'default_enabled': True,
    },
    'web_search_latest': {
        'kind': 'server_tool',
        'tool': {'type': 'web_search_20260209', 'name': 'web_search'},
        'implicit_code_execution_for_dynamic_filtering': True,
        'supported_model_patterns': (
            'claude-opus-4-6',
            'claude-sonnet-4-6',
            'claude-mythos-*',
        ),
        'default_enabled': False,
    },
    'web_fetch_latest': {
        'kind': 'server_tool',
        'tool': {'type': 'web_fetch_20260209', 'name': 'web_fetch'},
        'implicit_code_execution_for_dynamic_filtering': True,
        'supported_model_patterns': (
            'claude-opus-4-6',
            'claude-sonnet-4-6',
            'claude-mythos-*',
        ),
        'default_enabled': False,
    },
    'code_execution_latest': {
        'kind': 'server_tool',
        'tool': {'type': 'code_execution_20260120', 'name': 'code_execution'},
        'supported_model_patterns': (
            'claude-opus-4-6',
            'claude-sonnet-4-6',
            'claude-opus-4-5-*',
            'claude-sonnet-4-5-*',
        ),
        'default_enabled': False,
    },
    'tool_search_latest': {
        'kind': 'server_tool',
        'tool': {'type': 'tool_search_tool_regex_20251119', 'name': 'tool_search'},
        'supported_model_patterns': (
            'claude-mythos-*',
            'claude-opus-4*',
            'claude-sonnet-4*',
        ),
        'default_enabled': False,
    },
}
