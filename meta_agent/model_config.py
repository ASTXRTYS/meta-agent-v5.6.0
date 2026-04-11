"""Centralized runtime model control plane."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from fnmatch import fnmatchcase
from types import MappingProxyType
from typing import Any, cast

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from meta_agent.anthropic_api import ANTHROPIC_NATIVE_FEATURES
from meta_agent.configuration import MetaAgentConfig
from meta_agent.openai_api import OPENAI_DEFAULTS

_VALID_EFFORTS: tuple[str | None, ...] = ('max', 'high', 'medium', 'low', None)
_SUPPORTED_PROVIDERS = frozenset({'anthropic', 'openai'})
_ANTHROPIC_ONLY_FIELDS = frozenset({'thinking', 'betas', 'mcp_servers'})
_OPENAI_ONLY_FIELDS = frozenset({'use_responses_api'})

_REQUEST_POLICY_DEFAULTS: dict[str, Any] = {
    'thinking': None,
    'streaming': True,
    'stream_usage': True,
    'timeout': None,
    'temperature': None,
    'top_p': None,
    'top_k': None,
    'stop_sequences': None,
    'betas': None,
    'mcp_servers': None,
    'context_management': None,
    'use_responses_api': None,
}

_EFFORT_MAX_TOKENS: dict[str | None, int] = {
    'max': 16000,
    'high': 12000,
    'medium': 8000,
    'low': 4096,
    None: 8000,
}

QUALITY_PROFILE: dict[str, Any] = {
    'effort': 'max',
    'temperature': None,
    'streaming': True,
    'stream_usage': True,
}
BALANCED_PROFILE: dict[str, Any] = {
    'effort': 'high',
    'temperature': None,
    'streaming': True,
    'stream_usage': True,
}
SPEED_PROFILE: dict[str, Any] = {
    'effort': 'high',
    'temperature': None,
    'streaming': True,
    'stream_usage': True,
}
COST_PROFILE: dict[str, Any] = {
    'effort': 'low',
    'temperature': None,
    'streaming': True,
    'stream_usage': True,
}


@dataclasses.dataclass(frozen=True)
class AgentModelConfig:
    model_spec: str | None = None
    effort: str | None = None
    server_tool_features: tuple[str, ...] = ()


AGENT_MODEL_REGISTRY: dict[str, AgentModelConfig] = {
    'orchestrator': AgentModelConfig(effort='high'),
    'research-agent': AgentModelConfig(
        effort='high',
        server_tool_features=('web_search_latest', 'web_fetch_latest'),
    ),
    'spec-writer': AgentModelConfig(effort='high'),
    'plan-writer': AgentModelConfig(effort='high'),
    'code-agent': AgentModelConfig(effort='high'),
    'verification-agent': AgentModelConfig(effort='high'),
    'evaluation-agent': AgentModelConfig(effort='high'),
    'document-renderer': AgentModelConfig(effort='low'),
}


@dataclasses.dataclass(frozen=True)
class RuntimeResolution:
    provider: str
    model_name: str
    model_spec: str
    effort: str | None
    max_tokens: int
    model: BaseChatModel
    thinking: Mapping[str, Any] | None
    streaming: bool
    stream_usage: bool
    timeout: float | None
    temperature: float | None
    top_p: float | None
    top_k: int | None
    stop_sequences: tuple[str, ...] | None
    betas: tuple[str, ...] | None
    mcp_servers: tuple[Mapping[str, Any], ...] | None
    context_management: Any | None
    use_responses_api: bool | None
    server_side_tools: tuple[Mapping[str, Any], ...]
    provenance: Mapping[str, str]


def _supports_feature_model(feature: Mapping[str, Any], model_name: str) -> bool:
    patterns = feature.get('supported_model_patterns', ())
    return any(fnmatchcase(model_name, pattern) for pattern in patterns)


def _validate_server_tool_support(feature_keys: tuple[str, ...], model_name: str) -> None:
    for key in feature_keys:
        feature = ANTHROPIC_NATIVE_FEATURES[key]
        if feature['kind'] != 'server_tool':
            continue
        if not _supports_feature_model(feature, model_name):
            tool_type = feature['tool']['type']
            raise ValueError(
                f"Anthropic feature {key!r} ({tool_type}) is not supported by model {model_name!r}. "
                f"Supported patterns: {feature.get('supported_model_patterns', ())}"
            )


def _freeze_json_like(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_json_like(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_like(v) for v in value)
    return value


def _freeze_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f'Expected mapping or None, got {type(value).__name__}')
    return cast(Mapping[str, Any], _freeze_json_like(value))


def _freeze_tuple_of_mappings(
    values: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(cast(Mapping[str, Any], _freeze_mapping(value)) for value in values)


def _thaw_json_like(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw_json_like(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_like(v) for v in value]
    return value


def runtime_resolution_to_dict(resolution: RuntimeResolution) -> dict[str, Any]:
    return {
        'provider': resolution.provider,
        'model_name': resolution.model_name,
        'model_spec': resolution.model_spec,
        'effort': resolution.effort,
        'thinking': _thaw_json_like(resolution.thinking),
        'max_tokens': resolution.max_tokens,
        'streaming': resolution.streaming,
        'stream_usage': resolution.stream_usage,
        'timeout': resolution.timeout,
        'temperature': resolution.temperature,
        'top_p': resolution.top_p,
        'top_k': resolution.top_k,
        'stop_sequences': _thaw_json_like(resolution.stop_sequences),
        'betas': _thaw_json_like(resolution.betas),
        'mcp_servers': _thaw_json_like(resolution.mcp_servers),
        'context_management': _thaw_json_like(resolution.context_management),
        'use_responses_api': resolution.use_responses_api,
        'server_side_tools': _thaw_json_like(resolution.server_side_tools),
        'provenance': _thaw_json_like(resolution.provenance),
    }


def _resolve_feature_set(feature_keys: list[str]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for key in feature_keys:
        if key in seen:
            continue
        if key not in ANTHROPIC_NATIVE_FEATURES:
            raise ValueError(
                f'Unknown feature key {key!r}. Valid keys: {sorted(ANTHROPIC_NATIVE_FEATURES)}'
            )
        seen.add(key)
        resolved.append(key)
    return resolved


def get_tool_policy(
    features: tuple[str, ...] | None = None,
) -> tuple[Mapping[str, Any], ...]:
    if not features:
        return ()

    result: list[Mapping[str, Any]] = []
    seen_tools: set[str] = set()
    for key in _resolve_feature_set(list(features)):
        feature = ANTHROPIC_NATIVE_FEATURES[key]
        if feature['kind'] != 'server_tool':
            continue
        tool = dict(feature['tool'])
        tool_name = str(tool['name'])
        if tool_name in seen_tools:
            continue
        seen_tools.add(tool_name)
        result.append(tool)
    return tuple(result)


def resolve_model(
    effort: str | None = None,
    max_tokens: int | None = None,
    model_spec: str | None = None,
    profile: Mapping[str, Any] | None = None,
    server_tool_features: tuple[str, ...] | None = None,
    **request_policy_overrides: Any,
) -> RuntimeResolution:
    if effort not in _VALID_EFFORTS:
        raise ValueError(f'effort must be one of {_VALID_EFFORTS}, got {effort!r}')

    cfg = MetaAgentConfig.from_env()
    resolved_model_spec = model_spec if model_spec is not None else cfg.model_spec
    model_spec_source = 'override' if model_spec is not None else 'env'

    if ':' not in resolved_model_spec:
        raise ValueError(
            f"model_spec must be in 'provider:model_name' format, got {resolved_model_spec!r}"
        )
    provider, resolved_model_name = resolved_model_spec.split(':', 1)
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider {provider!r}. Supported providers: {sorted(_SUPPORTED_PROVIDERS)}"
        )

    effective_policy = dict(_REQUEST_POLICY_DEFAULTS)
    provenance: dict[str, str] = {field: 'default' for field in effective_policy}
    effective_effort = effort
    profile_max_tokens: int | None = None

    if profile is not None:
        profile_dict = dict(profile)
        unknown_profile_fields = set(profile_dict) - (set(_REQUEST_POLICY_DEFAULTS) | {'effort', 'max_tokens'})
        if unknown_profile_fields:
            valid_fields = sorted(set(_REQUEST_POLICY_DEFAULTS) | {'effort', 'max_tokens'})
            raise ValueError(
                f'Unknown profile fields {sorted(unknown_profile_fields)}. Valid fields are {valid_fields}.'
            )
        if effective_effort is None and profile_dict.get('effort') is not None:
            effective_effort = profile_dict['effort']
        if max_tokens is None and profile_dict.get('max_tokens') is not None:
            profile_max_tokens = int(profile_dict['max_tokens'])
        for key, value in profile_dict.items():
            if key in {'effort', 'max_tokens'}:
                continue
            effective_policy[key] = value
            provenance[key] = 'default'

    unknown_override_fields = set(request_policy_overrides) - set(_REQUEST_POLICY_DEFAULTS)
    if unknown_override_fields:
        raise ValueError(
            f'Unknown request policy override fields {sorted(unknown_override_fields)}. '
            f'Valid fields are {sorted(_REQUEST_POLICY_DEFAULTS)}.'
        )
    for key, value in request_policy_overrides.items():
        effective_policy[key] = value
        provenance[key] = 'override'

    if effective_effort not in _VALID_EFFORTS:
        raise ValueError(f'effort must be one of {_VALID_EFFORTS}, got {effective_effort!r}')
    provenance['effort'] = 'override' if effort is not None else 'default'

    temperature = effective_policy.get('temperature')
    if temperature is not None and not (0.0 <= temperature <= 1.0):
        raise ValueError(f'temperature must be in [0.0, 1.0], got {temperature}')

    resolved_max_tokens = (
        max_tokens
        if max_tokens is not None
        else profile_max_tokens if profile_max_tokens is not None else _EFFORT_MAX_TOKENS[effective_effort]
    )
    if resolved_max_tokens <= 0:
        raise ValueError(f'max_tokens must be > 0, got {resolved_max_tokens}')
    provenance['max_tokens'] = 'override' if max_tokens is not None else 'default'

    if provider != 'anthropic':
        for field in _ANTHROPIC_ONLY_FIELDS:
            if provenance.get(field) == 'override':
                raise ValueError(
                    f"Field {field!r} is not supported by provider {provider!r}. "
                    f'Remove this override or switch to an Anthropic model spec.'
                )
            provenance[field] = 'unsupported_for_provider'
    if provider != 'openai':
        for field in _OPENAI_ONLY_FIELDS:
            if provenance.get(field) == 'override':
                raise ValueError(
                    f"Field {field!r} is not supported by provider {provider!r}. "
                    f'Remove this override or switch to an OpenAI model spec.'
                )
            provenance[field] = 'unsupported_for_provider'

    init_kwargs: dict[str, Any] = {'max_tokens': resolved_max_tokens}
    resolved_use_responses_api = False
    for field, value in effective_policy.items():
        if value is None or field == 'thinking':
            continue
        if provider != 'anthropic' and field in _ANTHROPIC_ONLY_FIELDS:
            continue
        if provider != 'openai' and field in _OPENAI_ONLY_FIELDS:
            continue
        init_kwargs[field] = value
    if provider == 'openai':
        init_kwargs.setdefault('use_responses_api', OPENAI_DEFAULTS['use_responses_api'])
        if provenance.get('use_responses_api') != 'override':
            provenance['use_responses_api'] = 'default'
        resolved_use_responses_api = bool(init_kwargs['use_responses_api'])

    openai_effort_map = {
        'max': 'high',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
    }
    if effective_effort is not None:
        if provider == 'anthropic':
            init_kwargs['effort'] = effective_effort
        elif provider == 'openai':
            openai_effort = openai_effort_map[effective_effort]
            if resolved_use_responses_api:
                init_kwargs['reasoning'] = {'effort': openai_effort}
            else:
                init_kwargs['reasoning_effort'] = openai_effort
        else:
            provenance['effort'] = 'unsupported_for_provider'

    thinking_value = effective_policy.get('thinking')
    if provider == 'anthropic':
        for feature in ANTHROPIC_NATIVE_FEATURES.values():
            if feature['kind'] != 'request_default' or not feature.get('default_enabled'):
                continue
            for patch_field, patch_value in feature['request_patch'].items():
                if provenance.get(patch_field) == 'override':
                    continue
                if patch_field == 'thinking':
                    thinking_value = patch_value
                init_kwargs[patch_field] = patch_value
                provenance[patch_field] = 'default'
        if thinking_value is not None:
            init_kwargs['thinking'] = thinking_value

    model = init_chat_model(resolved_model_spec, **init_kwargs)

    ls_params: dict[str, Any] = {}
    try:
        ls_params = model._get_ls_params() or {}
    except Exception:
        ls_params = {}
    confirmed_provider = ls_params.get('ls_provider', provider)

    if confirmed_provider == 'anthropic' and server_tool_features is not None:
        if server_tool_features:
            _validate_server_tool_support(server_tool_features, resolved_model_name)
        server_side_tools = get_tool_policy(features=server_tool_features)
    else:
        server_side_tools = ()

    raw_provenance = {
        **provenance,
        'provider': model_spec_source,
        'model_name': model_spec_source,
        'model_spec': model_spec_source,
        'server_side_tools': (
            'registry'
            if server_tool_features and confirmed_provider == 'anthropic'
            else 'none'
            if confirmed_provider == 'anthropic'
            else 'unsupported_for_provider'
        ),
    }

    return RuntimeResolution(
        provider=provider,
        model_name=resolved_model_name,
        model_spec=resolved_model_spec,
        effort=effective_effort,
        max_tokens=resolved_max_tokens,
        model=model,
        thinking=_freeze_mapping(thinking_value),
        streaming=bool(effective_policy.get('streaming', True)),
        stream_usage=bool(effective_policy.get('stream_usage', True)),
        timeout=effective_policy.get('timeout'),
        temperature=effective_policy.get('temperature'),
        top_p=effective_policy.get('top_p'),
        top_k=effective_policy.get('top_k'),
        stop_sequences=(
            tuple(str(item) for item in effective_policy['stop_sequences'])
            if effective_policy.get('stop_sequences') is not None
            else None
        ),
        betas=(
            tuple(str(item) for item in effective_policy['betas'])
            if effective_policy.get('betas') is not None
            else None
        ),
        mcp_servers=(
            _freeze_tuple_of_mappings(list(effective_policy['mcp_servers']))
            if effective_policy.get('mcp_servers') is not None
            else None
        ),
        context_management=_freeze_json_like(effective_policy.get('context_management')),
        use_responses_api=cast(bool | None, init_kwargs.get('use_responses_api')),
        server_side_tools=_freeze_tuple_of_mappings(list(server_side_tools)),
        provenance=cast(Mapping[str, str], _freeze_json_like(raw_provenance)),
    )


def resolve_agent_model(agent_name: str, **overrides: Any) -> RuntimeResolution:
    config = AGENT_MODEL_REGISTRY.get(agent_name, AgentModelConfig())
    kwargs: dict[str, Any] = {'server_tool_features': config.server_tool_features}
    if config.model_spec is not None:
        kwargs['model_spec'] = config.model_spec
    if config.effort is not None:
        kwargs['effort'] = config.effort
    kwargs.update(overrides)
    return resolve_model(**kwargs)


def _field_type(field: str) -> str:
    field_types = {
        'thinking': 'mapping',
        'streaming': 'boolean',
        'stream_usage': 'boolean',
        'timeout': 'number',
        'temperature': 'number',
        'top_p': 'number',
        'top_k': 'integer',
        'stop_sequences': 'sequence',
        'betas': 'sequence',
        'mcp_servers': 'sequence',
        'context_management': 'json',
        'use_responses_api': 'boolean',
    }
    return field_types.get(field, 'unknown')


def _field_constraints(field: str) -> dict[str, Any]:
    constraints: dict[str, dict[str, Any]] = {
        'thinking': {'allowed_values': [None, {'type': 'adaptive'}]},
        'temperature': {'minimum': 0.0, 'maximum': 1.0},
    }
    return constraints.get(field, {})


def get_policy_schema(model_spec: str) -> dict[str, Any]:
    if ':' not in model_spec:
        raise ValueError(
            f"model_spec must be in 'provider:model_name' format, got {model_spec!r}"
        )
    provider, model_name = model_spec.split(':', 1)
    is_anthropic = provider == 'anthropic'
    is_openai = provider == 'openai'

    fields: dict[str, dict[str, Any]] = {
        'thinking': {
            'supported': is_anthropic,
            'source_default': {'type': 'adaptive'} if is_anthropic else None,
            'type': 'mapping',
            'reason': None if is_anthropic else 'unsupported_for_provider',
            'allowed_values': [None, {'type': 'adaptive'}],
        },
        'effort': {
            'supported': is_anthropic or is_openai,
            'source_default': None,
            'type': 'string',
            'reason': None if (is_anthropic or is_openai) else 'unsupported_for_provider',
            'enum': ['max', 'high', 'medium', 'low', None],
            'provider_notes': (
                'Anthropic: passed as `effort` to ChatAnthropic. '
                'OpenAI: when Responses API mode is enabled, translated to '
                '`reasoning={\"effort\": ...}` with values `low`, `medium`, or `high`; '
                'if Responses API mode is disabled, translated to `reasoning_effort`. '
                'Internal `max` maps down to OpenAI `high`.'
            ),
        },
        'max_tokens': {
            'supported': True,
            'source_default': _EFFORT_MAX_TOKENS[None],
            'type': 'integer',
            'reason': None,
            'minimum': 1,
        },
    }
    for field, default in _REQUEST_POLICY_DEFAULTS.items():
        if field in fields:
            continue
        supported = True
        reason = None
        source_default = default
        if field in _ANTHROPIC_ONLY_FIELDS and not is_anthropic:
            supported = False
            reason = 'unsupported_for_provider'
            source_default = None
        elif field in _OPENAI_ONLY_FIELDS:
            supported = is_openai
            reason = None if is_openai else 'unsupported_for_provider'
            source_default = OPENAI_DEFAULTS['use_responses_api'] if is_openai else None
        fields[field] = {
            'supported': supported,
            'source_default': source_default,
            'type': _field_type(field),
            'reason': reason,
            **_field_constraints(field),
        }

    tools_schema: dict[str, dict[str, Any]] = {}
    for feature_key, feature in ANTHROPIC_NATIVE_FEATURES.items():
        if feature['kind'] != 'server_tool':
            continue
        tool = feature['tool']
        entry = {
            'name': tool['name'],
            'type_version': tool['type'],
            'default_enabled': feature.get('default_enabled', False),
            'supported_model_patterns': feature.get('supported_model_patterns', ()),
            'exposed_to_end_user': False,
        }
        if 'implicit_code_execution_for_dynamic_filtering' in feature:
            entry['implicit_code_execution_for_dynamic_filtering'] = feature[
                'implicit_code_execution_for_dynamic_filtering'
            ]
        if is_anthropic:
            if _supports_feature_model(feature, model_name):
                tools_schema[feature_key] = {**entry, 'supported': True}
            else:
                tools_schema[feature_key] = {
                    **entry,
                    'supported': False,
                    'reason': 'unsupported_model_version',
                }
        else:
            tools_schema[feature_key] = {
                **entry,
                'default_enabled': False,
                'supported': False,
                'reason': 'anthropic_only',
            }

    agents_schema = {
        agent_name: {
            'model_spec': agent_cfg.model_spec,
            'effort': agent_cfg.effort,
            'server_tool_features': agent_cfg.server_tool_features,
        }
        for agent_name, agent_cfg in AGENT_MODEL_REGISTRY.items()
    }

    return {
        'fields': fields,
        'profiles': {
            'quality': dict(QUALITY_PROFILE),
            'balanced': dict(BALANCED_PROFILE),
            'speed': dict(SPEED_PROFILE),
            'cost': dict(COST_PROFILE),
        },
        'provider_baselines': dict(OPENAI_DEFAULTS) if is_openai else {},
        'tools': tools_schema,
        'agents': agents_schema,
        'provider': provider,
        'model_spec': model_spec,
    }


__all__ = [
    'AGENT_MODEL_REGISTRY',
    'AgentModelConfig',
    'BALANCED_PROFILE',
    'COST_PROFILE',
    'QUALITY_PROFILE',
    'RuntimeResolution',
    'SPEED_PROFILE',
    'get_policy_schema',
    'get_tool_policy',
    'resolve_agent_model',
    'resolve_model',
    'runtime_resolution_to_dict',
]
