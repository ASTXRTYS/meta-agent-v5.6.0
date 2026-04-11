# REPLACES: new contract coverage for the model control plane migration
"""Contract tests for runtime model resolution parity.

COVERS: configuration.MetaAgentConfig, model_config.resolve_model,
        model_config.resolve_agent_model, model_config.get_tool_policy,
        model_config.get_policy_schema, model_config.runtime_resolution_to_dict
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import Field

from langchain_core.language_models import BaseChatModel

import meta_agent.model_config as model_config
from meta_agent.anthropic_api import ANTHROPIC_NATIVE_FEATURES
from meta_agent.configuration import MetaAgentConfig
from meta_agent.model_config import (
    AGENT_MODEL_REGISTRY,
    AgentModelConfig,
    BALANCED_PROFILE,
    COST_PROFILE,
    QUALITY_PROFILE,
    SPEED_PROFILE,
    get_policy_schema,
    get_tool_policy,
    resolve_agent_model,
    resolve_model,
    runtime_resolution_to_dict,
)
from tests._support.fake_models import GenericFakeChatModel

pytestmark = pytest.mark.contract


class StubChatModel(GenericFakeChatModel):
    provider: str = 'anthropic'
    model_spec: str = 'anthropic:claude-opus-4-6'
    init_kwargs: dict[str, Any] = Field(default_factory=dict)

    def _get_ls_params(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {'ls_provider': self.provider}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('META_AGENT_MODEL', 'anthropic:claude-opus-4-6')
    monkeypatch.delenv('META_AGENT_MODEL_PROVIDER', raising=False)
    monkeypatch.delenv('META_AGENT_MODEL_NAME', raising=False)


@pytest.fixture
def init_model_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_init_chat_model(model_spec: str, **kwargs: Any) -> BaseChatModel:
        provider = model_spec.split(':', 1)[0]
        model = StubChatModel(
            messages=iter(['stub']),
            provider=provider,
            model_spec=model_spec,
            init_kwargs=dict(kwargs),
        )
        calls.append({'model_spec': model_spec, 'kwargs': dict(kwargs), 'model': model})
        return model

    monkeypatch.setattr(model_config, 'init_chat_model', fake_init_chat_model)
    return calls


def test_streaming_defaults_true(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model()
    assert resolution.streaming is True
    assert resolution.stream_usage is True
    assert init_model_calls[-1]['kwargs']['streaming'] is True
    assert init_model_calls[-1]['kwargs']['stream_usage'] is True


@pytest.mark.parametrize('effort', ['low', 'medium', 'high', 'max', None])
def test_thinking_defaults_adaptive(
    effort: str | None,
    init_model_calls: list[dict[str, Any]],
) -> None:
    resolution = resolve_model(effort=effort)
    assert resolution.thinking == {'type': 'adaptive'}
    assert init_model_calls[-1]['kwargs']['thinking'] == {'type': 'adaptive'}


@pytest.mark.parametrize(
    ('effort', 'expected_max_tokens'),
    [('max', 16000), ('high', 12000), ('medium', 8000), ('low', 4096), (None, 8000)],
)
def test_effort_max_tokens_mapping(
    effort: str | None,
    expected_max_tokens: int,
    init_model_calls: list[dict[str, Any]],
) -> None:
    resolution = resolve_model(effort=effort)
    assert resolution.max_tokens == expected_max_tokens
    assert init_model_calls[-1]['kwargs']['max_tokens'] == expected_max_tokens


def test_server_side_tools_empty_by_default(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model()
    assert resolution.server_side_tools == ()
    assert resolution.provenance['server_side_tools'] == 'none'
    assert init_model_calls[-1]['model_spec'] == 'anthropic:claude-opus-4-6'


def test_get_tool_policy_empty_by_default() -> None:
    assert get_tool_policy() == ()


def test_get_tool_policy_explicit_features() -> None:
    tools = get_tool_policy(('web_search_latest',))
    assert len(tools) == 1
    assert tools[0]['name'] == 'web_search'
    assert tools[0]['type'] == 'web_search_20260209'


def test_get_tool_policy_unknown_feature_raises() -> None:
    with pytest.raises(ValueError, match='Unknown feature key'):
        get_tool_policy(('missing',))


def test_tool_search_default_disabled() -> None:
    assert ANTHROPIC_NATIVE_FEATURES['tool_search_latest']['default_enabled'] is False


def test_code_execution_default_disabled() -> None:
    assert ANTHROPIC_NATIVE_FEATURES['code_execution_latest']['default_enabled'] is False


def test_server_tool_registry_entries_default_disabled() -> None:
    entries = [feature for feature in ANTHROPIC_NATIVE_FEATURES.values() if feature['kind'] == 'server_tool']
    assert entries
    assert all(feature['default_enabled'] is False for feature in entries)


def test_web_search_has_implicit_code_execution_annotation() -> None:
    assert ANTHROPIC_NATIVE_FEATURES['web_search_latest']['implicit_code_execution_for_dynamic_filtering'] is True


def test_web_fetch_has_implicit_code_execution_annotation() -> None:
    assert ANTHROPIC_NATIVE_FEATURES['web_fetch_latest']['implicit_code_execution_for_dynamic_filtering'] is True


def test_web_search_no_requires_field() -> None:
    assert 'requires' not in ANTHROPIC_NATIVE_FEATURES['web_search_latest']


def test_web_fetch_no_requires_field() -> None:
    assert 'requires' not in ANTHROPIC_NATIVE_FEATURES['web_fetch_latest']


def test_server_tool_features_validate_model_compatibility(
    init_model_calls: list[dict[str, Any]],
) -> None:
    with pytest.raises(ValueError, match='code_execution_latest'):
        resolve_model(
            model_spec='anthropic:claude-haiku-4-5',
            server_tool_features=('code_execution_latest',),
        )
    assert init_model_calls[-1]['model_spec'] == 'anthropic:claude-haiku-4-5'


def test_invalid_effort_raises() -> None:
    with pytest.raises(ValueError, match='effort'):
        resolve_model(effort='ultra')


def test_model_spec_without_colon_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('META_AGENT_MODEL', 'claude-opus-4-6')
    with pytest.raises(ValueError, match='META_AGENT_MODEL'):
        MetaAgentConfig.from_env()


def test_temperature_out_of_range_raises() -> None:
    with pytest.raises(ValueError, match='temperature'):
        resolve_model(temperature=2.0)


def test_max_tokens_zero_raises() -> None:
    with pytest.raises(ValueError, match='max_tokens'):
        resolve_model(max_tokens=0)


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match='Unsupported provider'):
        resolve_model(model_spec='bogus:model')


def test_anthropic_only_field_explicit_override_non_anthropic_raises(
    init_model_calls: list[dict[str, Any]],
) -> None:
    with pytest.raises(ValueError, match='thinking'):
        resolve_model(model_spec='openai:gpt-5', thinking={'type': 'adaptive'})
    assert init_model_calls == []


def test_betas_pass_through_untouched(init_model_calls: list[dict[str, Any]]) -> None:
    resolve_model(betas=('future-beta-2026-01-01',))
    assert init_model_calls[-1]['kwargs']['betas'] == ('future-beta-2026-01-01',)


def test_mcp_servers_do_not_auto_inject_beta(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(mcp_servers=({'name': 'demo'},))
    assert resolution.betas is None
    assert 'betas' not in init_model_calls[-1]['kwargs']


def test_deprecated_env_vars_emit_deprecation_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('META_AGENT_MODEL_PROVIDER', 'anthropic')
    with pytest.warns(DeprecationWarning, match='META_AGENT_MODEL_PROVIDER'):
        MetaAgentConfig.from_env()


def test_runtime_resolution_serializable_to_dict(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(server_tool_features=('web_search_latest',))
    payload = runtime_resolution_to_dict(resolution)
    assert 'model' not in payload
    json.dumps(payload)
    assert payload['server_side_tools'][0]['name'] == 'web_search'
    assert init_model_calls[-1]['kwargs']['thinking'] == {'type': 'adaptive'}


def test_runtime_resolution_deeply_immutable(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(server_tool_features=('web_search_latest',))
    assert isinstance(resolution.server_side_tools, tuple)
    with pytest.raises(TypeError):
        resolution.server_side_tools[0]['name'] = 'changed'


@pytest.mark.parametrize(
    'profile,expected_effort',
    [
        (QUALITY_PROFILE, 'max'),
        (BALANCED_PROFILE, 'high'),
        (SPEED_PROFILE, 'high'),
        (COST_PROFILE, 'low'),
    ],
)
def test_named_profiles_reflected_in_resolution(
    profile: dict[str, Any],
    expected_effort: str,
    init_model_calls: list[dict[str, Any]],
) -> None:
    resolution = resolve_model(profile=profile)
    assert resolution.effort == expected_effort
    assert resolution.streaming is True
    assert 'max_retries' not in init_model_calls[-1]['kwargs']


def test_explicit_override_beats_profile(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(profile=QUALITY_PROFILE, effort='low', temperature=0.2)
    assert resolution.effort == 'low'
    assert resolution.temperature == 0.2
    assert init_model_calls[-1]['kwargs']['temperature'] == 0.2


def test_policy_schema_anthropic_marks_thinking_supported() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert schema['fields']['thinking']['supported'] is True
    assert schema['fields']['thinking']['source_default'] == {'type': 'adaptive'}


def test_policy_schema_openai_marks_thinking_unsupported() -> None:
    schema = get_policy_schema('openai:gpt-5')
    assert schema['fields']['thinking']['supported'] is False
    assert schema['fields']['thinking']['reason'] == 'unsupported_for_provider'


def test_policy_schema_tools_contains_all_four_server_tool_features() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert set(schema['tools']) == {
        'web_search_latest',
        'web_fetch_latest',
        'code_execution_latest',
        'tool_search_latest',
    }


def test_policy_schema_tools_include_model_support_metadata() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    for entry in schema['tools'].values():
        assert 'supported_model_patterns' in entry
        assert 'requires' not in entry


def test_policy_schema_unsupported_model_version() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert schema['tools']['tool_search_latest']['supported'] is True
    unsupported = get_policy_schema('anthropic:claude-haiku-4-5')
    assert unsupported['tools']['code_execution_latest']['supported'] is False
    assert unsupported['tools']['code_execution_latest']['reason'] == 'unsupported_model_version'


def test_policy_schema_web_tools_include_implicit_code_execution_annotation() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert schema['tools']['web_search_latest']['implicit_code_execution_for_dynamic_filtering'] is True
    assert schema['tools']['web_fetch_latest']['implicit_code_execution_for_dynamic_filtering'] is True


def test_policy_schema_includes_agents_key() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert 'agents' in schema
    assert schema['agents']['research-agent']['server_tool_features'] == ('web_search_latest', 'web_fetch_latest')


def test_policy_schema_agents_effort_matches_registry() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    for agent_name, agent_cfg in AGENT_MODEL_REGISTRY.items():
        assert schema['agents'][agent_name]['effort'] == agent_cfg.effort


def test_policy_schema_tools_exposed_to_end_user_false() -> None:
    schema = get_policy_schema('anthropic:claude-opus-4-6')
    assert all(entry['exposed_to_end_user'] is False for entry in schema['tools'].values())


def test_openai_defaults_use_responses_api(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(model_spec='openai:gpt-5', effort='high')
    assert resolution.use_responses_api is True
    assert init_model_calls[-1]['kwargs']['use_responses_api'] is True
    assert init_model_calls[-1]['kwargs']['reasoning'] == {'effort': 'high'}
    assert 'reasoning_effort' not in init_model_calls[-1]['kwargs']


def test_openai_override_beats_responses_baseline(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model(model_spec='openai:gpt-5', effort='max', use_responses_api=False)
    assert resolution.use_responses_api is False
    assert init_model_calls[-1]['kwargs']['use_responses_api'] is False
    assert init_model_calls[-1]['kwargs']['reasoning_effort'] == 'high'
    assert 'reasoning' not in init_model_calls[-1]['kwargs']


@pytest.mark.parametrize(
    ('agent_name', 'expected_effort'),
    [
        ('orchestrator', 'high'),
        ('research-agent', 'high'),
        ('spec-writer', 'high'),
        ('plan-writer', 'high'),
        ('code-agent', 'high'),
        ('verification-agent', 'high'),
        ('evaluation-agent', 'high'),
        ('document-renderer', 'low'),
    ],
)
def test_resolve_agent_model_uses_registry_effort(
    agent_name: str,
    expected_effort: str,
    init_model_calls: list[dict[str, Any]],
) -> None:
    resolution = resolve_agent_model(agent_name)
    assert resolution.effort == expected_effort
    assert isinstance(resolution.model, BaseChatModel)
    assert init_model_calls[-1]['kwargs']['max_tokens'] == resolution.max_tokens


def test_resolve_agent_model_override_beats_registry(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_agent_model('code-agent', effort='low', max_tokens=2048)
    assert resolution.effort == 'low'
    assert resolution.max_tokens == 2048
    assert init_model_calls[-1]['kwargs']['max_tokens'] == 2048


def test_resolve_agent_model_unknown_agent_falls_back(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_agent_model('missing-agent')
    assert resolution.effort is None
    assert resolution.server_side_tools == ()
    assert init_model_calls[-1]['model_spec'] == 'anthropic:claude-opus-4-6'


def test_resolve_agent_model_explicit_model_spec(
    monkeypatch: pytest.MonkeyPatch,
    init_model_calls: list[dict[str, Any]],
) -> None:
    patched_registry = dict(AGENT_MODEL_REGISTRY)
    patched_registry['spec-writer'] = AgentModelConfig(model_spec='openai:gpt-5', effort='high')
    monkeypatch.setattr(model_config, 'AGENT_MODEL_REGISTRY', patched_registry)
    resolution = resolve_agent_model('spec-writer')
    assert resolution.model_spec == 'openai:gpt-5'
    assert init_model_calls[-1]['model_spec'] == 'openai:gpt-5'


def test_research_agent_server_side_tools_scoped(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_agent_model('research-agent')
    assert [tool['name'] for tool in resolution.server_side_tools] == ['web_search', 'web_fetch']
    assert all(tool['name'] != 'code_execution' for tool in resolution.server_side_tools)
    assert init_model_calls[-1]['kwargs']['thinking'] == {'type': 'adaptive'}


@pytest.mark.parametrize(
    'agent_name',
    ['spec-writer', 'code-agent', 'verification-agent', 'orchestrator'],
)
def test_selected_agents_have_no_server_side_tools(
    agent_name: str,
    init_model_calls: list[dict[str, Any]],
) -> None:
    resolution = resolve_agent_model(agent_name)
    assert resolution.server_side_tools == ()
    assert init_model_calls[-1]['kwargs']['thinking'] == {'type': 'adaptive'}


def test_server_side_tools_provenance_registry(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_agent_model('research-agent')
    assert resolution.provenance['server_side_tools'] == 'registry'
    assert init_model_calls[-1]['model_spec'] == 'anthropic:claude-opus-4-6'


def test_server_side_tools_provenance_none(init_model_calls: list[dict[str, Any]]) -> None:
    resolution = resolve_model()
    assert resolution.provenance['server_side_tools'] == 'none'
    assert init_model_calls[-1]['kwargs']['thinking'] == {'type': 'adaptive'}
