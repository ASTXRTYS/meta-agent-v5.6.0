from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, TypedDict

import yaml
from typing_extensions import NotRequired
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    PrivateStateAttr,
    ResponseT,
)
from langchain.tools import ToolRuntime
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from deepagents.backends.protocol import BACKEND_TYPES, BackendProtocol
from meta_agent.utils.artifact_validator import (
    ArtifactProtocol,
    ValidationResult,
    Violation,
    validate,
)

logger = logging.getLogger(__name__)

DEFAULT_PROTOCOLS_PATH = ".agents/protocols/artifacts.yaml"


class ArtifactProtocolState(AgentState):
    """State schema for ArtifactProtocolMiddleware.

    artifact_protocols is marked PrivateStateAttr so it is not propagated
    to parent agents — identical to how SkillsMiddleware marks skills_metadata.
    """
    artifact_protocols: NotRequired[
        Annotated[dict[str, ArtifactProtocol], PrivateStateAttr]
    ]


class ArtifactProtocolStateUpdate(TypedDict):
    artifact_protocols: dict[str, ArtifactProtocol]


class ValidateArtifactSchema(BaseModel):
    """Input schema for the validate_artifact tool."""
    artifact_path: str
    artifact_type: str


class ArtifactProtocolMiddleware(AgentMiddleware[ArtifactProtocolState, ContextT, ResponseT]):
    """Middleware that loads artifact protocols once per session and provides
    the validate_artifact tool, both bound to the same FilesystemBackend.

    Pattern: identical to FilesystemMiddleware for tool creation (close over
    self, resolve backend via _get_backend(runtime) at call time) and identical
    to MemoryMiddleware for state hydration (before_agent skip-if-present guard,
    download_files, cache in state).

    Usage:
        middleware = [
            ...,
            ArtifactProtocolMiddleware(backend=bare_fs),
            ...,
        ]
    """

    state_schema = ArtifactProtocolState

    def __init__(
        self,
        *,
        backend: BACKEND_TYPES,
        protocols_path: str = DEFAULT_PROTOCOLS_PATH,
    ) -> None:
        self._backend = backend
        self.protocols_path = protocols_path
        # Tool is created once at construction, closing over self.
        # Registered via self.tools so create_deep_agent() picks it up automatically.
        self.tools = [self._create_validate_artifact_tool()]

    def _get_backend(
        self,
        runtime: ToolRuntime[Any, ArtifactProtocolState],
    ) -> BackendProtocol:
        """Resolve backend from instance or factory — mirrors FilesystemMiddleware."""
        if callable(self._backend):
            return self._backend(runtime)
        return self._backend

    def _get_backend_from_agent(
        self,
        state: ArtifactProtocolState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> BackendProtocol:
        """Resolve backend in before_agent context — mirrors MemoryMiddleware."""
        if callable(self._backend):
            tool_runtime = ToolRuntime(
                state=state,
                context=runtime.context,
                stream_writer=runtime.stream_writer,
                store=runtime.store,
                config=config,
                tool_call_id=None,
            )
            return self._backend(tool_runtime)
        return self._backend

    def _parse_protocols(self, raw_yaml: str) -> dict[str, ArtifactProtocol]:
        data = yaml.safe_load(raw_yaml)
        if not isinstance(data, dict) or "protocols" not in data:
            raise ValueError(
                f"artifacts.yaml must have a top-level 'protocols' key; "
                f"got: {list(data.keys()) if isinstance(data, dict) else type(data)}"
            )
        return {
            artifact_type: ArtifactProtocol(**spec)
            for artifact_type, spec in data["protocols"].items()
        }

    def _create_validate_artifact_tool(self) -> BaseTool:
        """Create the validate_artifact tool, closing over self.

        Mirrors FilesystemMiddleware._create_read_file_tool(): the inner
        function receives a ToolRuntime, calls self._get_backend(runtime)
        to resolve the backend, and uses backend.read() for all file I/O.
        No raw Python filesystem access.
        """

        def sync_validate(
            artifact_path: str,
            artifact_type: str,
            runtime: ToolRuntime[Any, ArtifactProtocolState],
        ) -> str:
            backend = self._get_backend(runtime)
            protocols: dict[str, ArtifactProtocol] = (
                runtime.state.get("artifact_protocols") or {}
            )

            if artifact_type not in protocols:
                result = ValidationResult(
                    passed=False,
                    completeness_score=0.0,
                    violations=[Violation(
                        violation_type="unknown_protocol",
                        detail=(
                            f"No protocol registered for '{artifact_type}'. "
                            f"Available: {sorted(protocols.keys()) or 'none — ArtifactProtocolMiddleware may be missing'}"
                        ),
                    )],
                    artifact_type=artifact_type,
                )
                return _format_result(result)

            read_result = backend.read(artifact_path)
            if read_result.error:
                result = ValidationResult(
                    passed=False,
                    completeness_score=0.0,
                    violations=[Violation(
                        violation_type="file_not_found" if read_result.error == "file_not_found" else "file_read_error",
                        detail=f"{artifact_path}: {read_result.error}",
                    )],
                    artifact_type=artifact_type,
                )
                return _format_result(result)

            content = read_result.file_data["content"]
            protocol = protocols[artifact_type] # type: ignore
            result = validate(content, protocol)
            return _format_result(result)

        async def async_validate(
            artifact_path: str,
            artifact_type: str,
            runtime: ToolRuntime[Any, ArtifactProtocolState],
        ) -> str:
            backend = self._get_backend(runtime)
            protocols: dict[str, ArtifactProtocol] = (
                runtime.state.get("artifact_protocols") or {}
            )

            if artifact_type not in protocols:
                result = ValidationResult(
                    passed=False,
                    completeness_score=0.0,
                    violations=[Violation(
                        violation_type="unknown_protocol",
                        detail=(
                            f"No protocol registered for '{artifact_type}'. "
                            f"Available: {sorted(protocols.keys()) or 'none — ArtifactProtocolMiddleware may be missing'}"
                        ),
                    )],
                    artifact_type=artifact_type,
                )
                return _format_result(result)

            read_result = await backend.aread(artifact_path)
            if read_result.error:
                result = ValidationResult(
                    passed=False,
                    completeness_score=0.0,
                    violations=[Violation(
                        violation_type="file_not_found" if read_result.error == "file_not_found" else "file_read_error",
                        detail=f"{artifact_path}: {read_result.error}",
                    )],
                    artifact_type=artifact_type,
                )
                return _format_result(result)

            content = read_result.file_data["content"]
            protocol = protocols[artifact_type] # type: ignore
            result = validate(content, protocol)
            return _format_result(result)

        return StructuredTool.from_function(
            name="validate_artifact",
            description=(
                "Validate an artifact's structural completeness against its registered protocol. "
                "artifact_path: absolute path to the file. "
                "artifact_type: one of 'prd', 'technical-specification', 'eval-suite'."
            ),
            func=sync_validate,
            coroutine=async_validate,
            infer_schema=False,
            args_schema=ValidateArtifactSchema,
        )

    def before_agent(
        self,
        state: ArtifactProtocolState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> ArtifactProtocolStateUpdate | None:
        """Load protocols once per session (synchronous).

        Skips if artifact_protocols already present in state (checkpoint resume
        or subsequent turn). Raises FileNotFoundError if artifacts.yaml is absent.
        """
        if "artifact_protocols" in state:
            return None

        backend = self._get_backend_from_agent(state, runtime, config)
        responses = backend.download_files([self.protocols_path])
        response = responses[0]

        if response.error == "file_not_found":
            raise FileNotFoundError(
                f"ArtifactProtocolMiddleware: protocols file not found at "
                f"'{self.protocols_path}'. Ensure /.agents/protocols/artifacts.yaml exists."
            )
        if response.error:
            raise RuntimeError(
                f"ArtifactProtocolMiddleware: failed to load '{self.protocols_path}': {response.error}"
            )

        raw_yaml = response.content.decode("utf-8") # type: ignore
        protocols = self._parse_protocols(raw_yaml)
        logger.debug("ArtifactProtocolMiddleware: loaded %d protocols", len(protocols))
        return ArtifactProtocolStateUpdate(artifact_protocols=protocols)

    async def abefore_agent(
        self,
        state: ArtifactProtocolState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> ArtifactProtocolStateUpdate | None:
        """Load protocols once per session (async). Mirrors before_agent exactly."""
        if "artifact_protocols" in state:
            return None

        backend = self._get_backend_from_agent(state, runtime, config)
        responses = await backend.adownload_files([self.protocols_path])
        response = responses[0]

        if response.error == "file_not_found":
            raise FileNotFoundError(
                f"ArtifactProtocolMiddleware: protocols file not found at "
                f"'{self.protocols_path}'. Ensure /.agents/protocols/artifacts.yaml exists."
            )
        if response.error:
            raise RuntimeError(
                f"ArtifactProtocolMiddleware: failed to load '{self.protocols_path}': {response.error}"
            )

        raw_yaml = response.content.decode("utf-8") # type: ignore
        protocols = self._parse_protocols(raw_yaml)
        logger.debug("ArtifactProtocolMiddleware: loaded %d protocols (async)", len(protocols))
        return ArtifactProtocolStateUpdate(artifact_protocols=protocols)


def _format_result(result: ValidationResult) -> str:
    """Serialize a ValidationResult into a human-readable string.

    Returns str — the ToolNode wraps it in a ToolMessage automatically.
    Mirrors the return convention of FilesystemMiddleware tools (str | ToolMessage),
    not the Command pattern used by @tool-decorated functions in meta_agent/tools/.
    """
    if result.passed:
        summary = f"✓ Validation passed — completeness {result.completeness_score:.0%}"
        if result.omission_log:
            summary += f"\n  Optional sections absent: {', '.join(result.omission_log)}"
    else:
        violation_lines = "\n".join(
            f"  • [{v.violation_type}] {v.detail}" for v in result.violations
        )
        summary = (
            f"✗ Validation failed — completeness {result.completeness_score:.0%}\n"
            f"Violations:\n{violation_lines}"
        )
        if result.omission_log:
            summary += f"\n  Optional sections absent: {', '.join(result.omission_log)}"

    return summary
