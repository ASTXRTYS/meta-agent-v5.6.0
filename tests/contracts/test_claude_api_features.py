# REPLACES: legacy Claude feature tests tied to model.py and global tool inventory
"""Contract tests for remaining Claude API integration behavior.

COVERS: tools.allowed_callers, research_agent.extract_api_citations
"""

import pytest

pytestmark = pytest.mark.contract


def test_safe_tools_have_allowed_callers():
    """Non-HITL tools should have allowed_callers for programmatic tool calling."""
    from meta_agent.tools import glob_search, grep_search

    for t in [glob_search, grep_search]:
        extras = getattr(t, 'extras', None) or {}
        assert 'allowed_callers' in extras, f'{t.name} missing allowed_callers'
        assert 'code_execution_20260120' in extras['allowed_callers']


def test_hitl_tools_do_not_have_allowed_callers():
    """HITL-gated tools must NOT have allowed_callers."""
    from meta_agent.tools import (
        create_eval_dataset_tool,
        execute_command_tool,
        langsmith_dataset_create_tool,
        langsmith_eval_run_tool,
        request_approval_tool,
        request_eval_approval_tool,
        transition_stage_tool,
    )

    hitl_tools = [
        execute_command_tool,
        request_approval_tool,
        request_eval_approval_tool,
        transition_stage_tool,
        langsmith_dataset_create_tool,
        langsmith_eval_run_tool,
        create_eval_dataset_tool,
    ]
    for t in hitl_tools:
        extras = getattr(t, 'extras', None) or {}
        assert 'allowed_callers' not in extras, (
            f'HITL tool {t.name} must NOT have allowed_callers'
        )


def test_extract_api_citations_empty_messages():
    """Returns empty list for messages with no citations."""
    from meta_agent.subagents.research_agent import extract_api_citations

    assert extract_api_citations([]) == []


def test_extract_api_citations_string_content():
    """Handles messages with string content (no citations possible)."""
    from meta_agent.subagents.research_agent import extract_api_citations

    msg = {'content': 'Hello world'}
    assert extract_api_citations([msg]) == []


def test_extract_api_citations_with_web_search_citations():
    """Extracts web_search_result_location citations from content blocks."""
    from meta_agent.subagents.research_agent import extract_api_citations

    msg = {'content': [
        {
            'type': 'text',
            'text': 'According to the docs...',
            'citations': [
                {
                    'type': 'web_search_result_location',
                    'url': 'https://example.com/docs',
                    'title': 'Example Docs',
                    'cited_text': 'The feature supports...',
                    'encrypted_index': 'abc123',
                }
            ],
        }
    ]}
    result = extract_api_citations([msg])
    assert len(result) == 1
    assert result[0]['type'] == 'web_search_result_location'
    assert result[0]['url'] == 'https://example.com/docs'
    assert result[0]['title'] == 'Example Docs'
    assert result[0]['cited_text'] == 'The feature supports...'
    assert result[0]['source'] == 'api'


def test_extract_api_citations_multiple_blocks_multiple_citations():
    """Handles multiple text blocks each with multiple citations."""
    from meta_agent.subagents.research_agent import extract_api_citations

    msg = {'content': [
        {'type': 'text', 'text': 'First...', 'citations': [
            {'type': 'web_search_result_location', 'url': 'https://a.com', 'title': 'A', 'cited_text': 'a'},
            {'type': 'web_search_result_location', 'url': 'https://b.com', 'title': 'B', 'cited_text': 'b'},
        ]},
        {'type': 'text', 'text': 'Second...', 'citations': [
            {'type': 'web_search_result_location', 'url': 'https://c.com', 'title': 'C', 'cited_text': 'c'},
        ]},
    ]}
    result = extract_api_citations([msg])
    assert len(result) == 3
    assert result[0]['block_index'] == 0
    assert result[2]['block_index'] == 1


def test_extract_api_citations_no_citations_field():
    """Handles content blocks without citations field."""
    from meta_agent.subagents.research_agent import extract_api_citations

    msg = {'content': [{'type': 'text', 'text': 'No citations here'}]}
    assert extract_api_citations([msg]) == []


def test_extract_api_citations_with_langchain_aimessage():
    """Works with LangChain AIMessage objects that have list content."""
    from meta_agent.subagents.research_agent import extract_api_citations

    class FakeAIMessage:
        def __init__(self, content):
            self.content = content

    msg = FakeAIMessage(content=[
        {'type': 'text', 'text': 'Cited text', 'citations': [
            {'type': 'web_search_result_location', 'url': 'https://x.com',
             'title': 'X', 'cited_text': 'x'},
        ]}
    ])
    result = extract_api_citations([msg])
    assert len(result) == 1
    assert result[0]['url'] == 'https://x.com'
